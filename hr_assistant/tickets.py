"""Session-only HR ticket creation and CSV export."""

from __future__ import annotations

import csv
import io
from dataclasses import asdict, dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class Ticket:
    ticket_id: str
    created_at_utc: str
    employee_id: str
    category: str
    description: str
    conversation_summary: str
    status: str = "Open (demo)"


def summarize_conversation(messages: list[dict[str, str]], limit: int = 600) -> str:
    """Create a local, deterministic summary without another API call."""
    relevant = messages[-6:]
    parts = []
    for message in relevant:
        role = "Employee" if message.get("role") == "user" else "Assistant"
        content = " ".join(message.get("content", "").split())
        if content:
            parts.append(f"{role}: {content[:180]}")
    summary = " | ".join(parts)
    return summary[:limit] or "No prior conversation available."


def create_ticket(
    existing_tickets: list[Ticket],
    *,
    employee_id: str | None,
    category: str,
    description: str,
    conversation_summary: str,
    now: datetime | None = None,
) -> Ticket:
    current_time = now or datetime.now(timezone.utc)
    sequence = len(existing_tickets) + 1
    ticket_id = f"HR-{current_time.year}-{sequence:04d}"
    return Ticket(
        ticket_id=ticket_id,
        created_at_utc=current_time.isoformat(timespec="seconds"),
        employee_id=employee_id or "Not selected",
        category=category,
        description=" ".join(description.split())[:1000],
        conversation_summary=conversation_summary,
    )


def tickets_to_csv(tickets: list[Ticket]) -> str:
    output = io.StringIO()
    fieldnames = list(Ticket.__dataclass_fields__.keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for ticket in tickets:
        writer.writerow(asdict(ticket))
    return output.getvalue()
