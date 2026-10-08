from datetime import datetime, timezone

from hr_assistant.config import HANDBOOK_DIR, Settings
from hr_assistant.conversation import AssistantEngine
from hr_assistant.retrieval import HandbookRetriever
from hr_assistant.tickets import create_ticket, tickets_to_csv


def settings(*, simulate_failure: bool = False) -> Settings:
    return Settings(
        provider="openai",
        api_key="test-key-not-sent",
        model="gpt-4o-mini",
        temperature=0.1,
        timeout_seconds=1,
        rag_top_k=3,
        rag_min_score=1.0,
        simulate_api_failure=simulate_failure,
    )


def test_simulated_api_failure_retries_then_offers_ticket() -> None:
    engine = AssistantEngine(
        settings(simulate_failure=True), HandbookRetriever(HANDBOOK_DIR)
    )
    response = engine.answer(
        "Can I carry over annual leave?",
        employee=None,
        history=[],
        last_route=None,
    )
    assert response.route == "fallback: API failure"
    assert response.ticket_offer
    assert response.debug["llm_attempts"] == 2


def test_low_confidence_question_offers_ticket_without_llm() -> None:
    engine = AssistantEngine(settings(), HandbookRetriever(HANDBOOK_DIR))
    response = engine.answer(
        "What is the office cafeteria menu tomorrow?",
        employee=None,
        history=[],
        last_route=None,
    )
    assert response.route == "fallback"
    assert response.ticket_offer
    assert "llm_attempts" not in response.debug


def test_ticket_id_and_csv_export() -> None:
    ticket = create_ticket(
        [],
        employee_id="AP1001",
        category="Policy question",
        description="Clarify the mileage rate.",
        conversation_summary="Employee asked about mileage.",
        now=datetime(2026, 10, 8, tzinfo=timezone.utc),
    )
    assert ticket.ticket_id == "HR-2026-0001"
    exported = tickets_to_csv([ticket])
    assert "HR-2026-0001" in exported
    assert "AP1001" in exported
