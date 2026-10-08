"""Transparent, deterministic request routing."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from hr_assistant.guardrails import (
    is_prompt_injection,
    is_sensitive_hr_topic,
    off_topic_category,
)


class Route(str, Enum):
    INJECTION_REFUSAL = "refusal: prompt injection"
    SCOPE_REFUSAL = "refusal: out of scope"
    HUMAN_HANDOFF = "human handoff"
    LEAVE_TOOL = "leave tool"
    CLARIFY = "clarifying question"
    RAG = "RAG"


@dataclass(frozen=True)
class RouteDecision:
    route: Route
    reason: str
    detail: str | None = None


HANDOFF_PHRASES = (
    "talk to a human",
    "speak to a human",
    "human agent",
    "contact hr",
    "raise a ticket",
    "create a ticket",
    "open a ticket",
)

BALANCE_PHRASES = (
    "leave balance",
    "balance",
    "remaining",
    "left",
    "used",
    "entitled",
    "how many days",
    "days do i have",
)

LEAVE_TERMS = (
    "annual leave", "sick leave", "casual leave", "vacation", "pto", "paid time off"
)

VAGUE_INPUTS = {
    "help",
    "hr",
    "policy",
    "policies",
    "leave",
    "benefits",
    "expense",
    "expenses",
    "work",
    "problem",
    "i have a problem",
    "i have a question",
    "tell me more",
}


def route_message(text: str, last_route: str | None = None) -> RouteDecision:
    normalized = " ".join(text.lower().strip().split())

    if is_prompt_injection(normalized):
        return RouteDecision(Route.INJECTION_REFUSAL, "Matched an injection pattern")

    category = off_topic_category(normalized)
    if category:
        return RouteDecision(
            Route.SCOPE_REFUSAL, "Matched an out-of-scope topic", category
        )

    if any(phrase in normalized for phrase in HANDOFF_PHRASES):
        return RouteDecision(Route.HUMAN_HANDOFF, "User explicitly requested HR")

    mentions_leave = any(term in normalized for term in LEAVE_TERMS)
    asks_for_balance = any(
        re.search(rf"\b{re.escape(phrase)}\b", normalized)
        for phrase in BALANCE_PHRASES
    )
    follows_leave_lookup = last_route == Route.LEAVE_TOOL.value and mentions_leave
    if (asks_for_balance and mentions_leave) or follows_leave_lookup:
        return RouteDecision(
            Route.LEAVE_TOOL,
            "Balance wording or follow-up to a leave lookup",
        )

    if normalized in VAGUE_INPUTS or len(normalized.split()) < 2:
        return RouteDecision(Route.CLARIFY, "Input is too broad to answer safely")

    detail = "sensitive" if is_sensitive_hr_topic(normalized) else None
    return RouteDecision(Route.RAG, "Potential handbook question", detail)


def clarification_for(text: str) -> str:
    topic = text.strip().lower()
    if topic in {"leave", "benefits", "expense", "expenses", "policy", "policies"}:
        return (
            f"What would you like to know about {topic}—the general policy, "
            "eligibility, a deadline, or your leave balance?"
        )
    return (
        "Could you briefly say which HR topic you need help with—for example leave, "
        "hybrid work, expenses, benefits, performance reviews, or leaving the company?"
    )
