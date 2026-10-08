"""Conversation orchestration independent of the Streamlit UI."""

from __future__ import annotations

from dataclasses import dataclass, field

from hr_assistant.config import Settings
from hr_assistant.guardrails import (
    SENSITIVE_GUIDANCE,
    injection_refusal,
    scope_refusal,
)
from hr_assistant.leave_tool import Employee, format_leave_balance
from hr_assistant.llm import LLMServiceError, generate_grounded_answer
from hr_assistant.retrieval import HandbookRetriever
from hr_assistant.routing import Route, clarification_for, route_message


@dataclass
class AssistantResponse:
    text: str
    route: str
    ticket_offer: bool = False
    create_handoff_ticket: bool = False
    debug: dict[str, object] = field(default_factory=dict)


def _contextualized_query(
    question: str, history: list[dict[str, str]]
) -> str:
    lowered = question.lower().strip()
    follow_up_markers = (
        "and ",
        "what about",
        "how about",
        "does that",
        "is that",
        "for contractors",
        "for interns",
    )
    if len(question.split()) <= 10 and lowered.startswith(follow_up_markers):
        for message in reversed(history):
            if message.get("role") == "user":
                previous = message.get("content", "")
                return f"{previous} {question}"
    return question


class AssistantEngine:
    def __init__(self, settings: Settings, retriever: HandbookRetriever):
        self.settings = settings
        self.retriever = retriever

    def answer(
        self,
        question: str,
        *,
        employee: Employee | None,
        history: list[dict[str, str]],
        last_route: str | None,
    ) -> AssistantResponse:
        decision = route_message(question, last_route)
        debug: dict[str, object] = {
            "route": decision.route.value,
            "route_reason": decision.reason,
        }

        if decision.route == Route.INJECTION_REFUSAL:
            return AssistantResponse(injection_refusal(), decision.route.value, debug=debug)

        if decision.route == Route.SCOPE_REFUSAL:
            return AssistantResponse(
                scope_refusal(decision.detail or "that topic"),
                decision.route.value,
                debug=debug,
            )

        if decision.route == Route.HUMAN_HANDOFF:
            return AssistantResponse(
                "I’ll create a demo HR ticket with a short summary of this conversation. "
                "Please avoid adding sensitive personal information.",
                decision.route.value,
                create_handoff_ticket=True,
                debug=debug,
            )

        if decision.route == Route.CLARIFY:
            return AssistantResponse(
                clarification_for(question), decision.route.value, debug=debug
            )

        if decision.route == Route.LEAVE_TOOL:
            if employee is None:
                return AssistantResponse(
                    "Please select or enter a valid demo employee ID in the sidebar so "
                    "I can look up the leave balance. I won’t guess leave numbers.",
                    decision.route.value,
                    debug=debug,
                )
            debug["employee_data_sent_to_llm"] = False
            debug["employee_row_used"] = employee.employee_id
            return AssistantResponse(
                format_leave_balance(employee, question),
                decision.route.value,
                debug=debug,
            )

        retrieval_query = _contextualized_query(question, history)
        retrieval = self.retriever.retrieve(
            retrieval_query,
            top_k=self.settings.rag_top_k,
            min_score=self.settings.rag_min_score,
        )
        debug.update(
            {
                "retrieval_query": retrieval_query,
                "normalized_query": retrieval.normalized_query,
                "retrieval_confident": retrieval.confident,
                "confidence_reason": retrieval.reason,
                "retrieved_chunks": [
                    result.as_debug_dict() for result in retrieval.results
                ],
                "employee_data_sent_to_llm": False,
            }
        )
        if not retrieval.confident:
            return AssistantResponse(
                "I couldn’t find reliable support for that in the AsterPeak handbook, "
                "so I don’t want to guess. Would you like me to raise an HR ticket? "
                "Reply **yes** to continue or **no** to cancel.",
                "fallback",
                ticket_offer=True,
                debug=debug,
            )

        try:
            answer = generate_grounded_answer(
                self.settings,
                question=question,
                results=retrieval.results,
                history=history,
            )
            debug.update(
                {
                    "llm_model": answer.model,
                    "llm_attempts": answer.attempts,
                }
            )
            text = answer.text
            if decision.detail == "sensitive":
                text = f"{SENSITIVE_GUIDANCE}\n\n{text}"
            return AssistantResponse(text, decision.route.value, debug=debug)
        except LLMServiceError as exc:
            debug.update(
                {
                    "llm_attempts": exc.attempts,
                    "llm_error": str(exc)[:500],
                }
            )
            return AssistantResponse(
                "I’m sorry—the AI service is unavailable or returned an unusable "
                "answer. I tried once more and still couldn’t produce a reliable "
                "response. Would you like me to raise an HR ticket? Reply **yes** to "
                "continue or **no** to cancel.",
                "fallback: API failure",
                ticket_offer=True,
                debug=debug,
            )
