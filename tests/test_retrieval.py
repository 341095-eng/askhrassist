from pathlib import Path

from hr_assistant.config import EMPLOYEE_FILE, HANDBOOK_DIR
from hr_assistant.leave_tool import EmployeeDirectory, format_leave_balance
from hr_assistant.retrieval import HandbookRetriever, normalize_query


def test_handbook_is_chunked_by_sections() -> None:
    retriever = HandbookRetriever(HANDBOOK_DIR)
    assert len(retriever.chunks) >= 25
    assert all(chunk.section and chunk.file_name.endswith(".md") for chunk in retriever.chunks)


def test_vacation_alias_retrieves_annual_leave() -> None:
    retriever = HandbookRetriever(HANDBOOK_DIR)
    result = retriever.retrieve("Can I carry over unused vacation days?", min_score=1.0)
    assert result.confident
    assert result.results[0].chunk.file_name == "leave_policy.md"
    assert "Annual leave" in result.results[0].chunk.section


def test_planted_mileage_gap_is_retrievable() -> None:
    retriever = HandbookRetriever(HANDBOOK_DIR)
    result = retriever.retrieve("What is the personal vehicle mileage rate?", min_score=1.0)
    assert result.confident
    assert any("mileage rate" in item.chunk.text for item in result.results)


def test_unrelated_question_has_low_confidence() -> None:
    retriever = HandbookRetriever(HANDBOOK_DIR)
    result = retriever.retrieve("Give me a recipe for sourdough bread", min_score=1.5)
    assert not result.confident


def test_query_normalization_expands_wfh() -> None:
    assert "remote work" in normalize_query("What is the WFH policy?")


def test_employee_balances_are_valid_and_deterministic() -> None:
    directory = EmployeeDirectory(EMPLOYEE_FILE)
    assert len(directory.all()) == 15
    employee = directory.get("ap1001")
    assert employee is not None
    assert employee.balances["annual"]["remaining"] == 13
    answer = format_leave_balance(employee, "How much annual leave is left?")
    assert "13 remaining" in answer
    assert "Sick leave" not in answer
