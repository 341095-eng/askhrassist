"""Deterministic employee lookup and leave-balance formatting."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

LEAVE_TYPES = ("annual", "sick", "casual")


@dataclass(frozen=True)
class Employee:
    employee_id: str
    name: str
    department: str
    manager: str
    balances: dict[str, dict[str, int]]

    @property
    def display_name(self) -> str:
        return f"{self.name} ({self.employee_id})"


class EmployeeDirectory:
    def __init__(self, csv_path: Path):
        frame = pd.read_csv(csv_path, dtype={"employee_id": str})
        required = {"employee_id", "name", "department", "manager"}
        required.update(
            f"{leave_type}_{field}"
            for leave_type in LEAVE_TYPES
            for field in ("entitled", "used", "remaining")
        )
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"Employee CSV is missing columns: {sorted(missing)}")

        self._employees: dict[str, Employee] = {}
        for _, row in frame.iterrows():
            balances: dict[str, dict[str, int]] = {}
            for leave_type in LEAVE_TYPES:
                entitled = int(row[f"{leave_type}_entitled"])
                used = int(row[f"{leave_type}_used"])
                remaining = int(row[f"{leave_type}_remaining"])
                if entitled - used != remaining:
                    raise ValueError(
                        f"Invalid {leave_type} balance for {row['employee_id']}"
                    )
                balances[leave_type] = {
                    "entitled": entitled,
                    "used": used,
                    "remaining": remaining,
                }
            employee = Employee(
                employee_id=str(row["employee_id"]).strip().upper(),
                name=str(row["name"]),
                department=str(row["department"]),
                manager=str(row["manager"]),
                balances=balances,
            )
            self._employees[employee.employee_id] = employee

    def all(self) -> list[Employee]:
        return sorted(self._employees.values(), key=lambda item: item.employee_id)

    def get(self, employee_id: str | None) -> Employee | None:
        if not employee_id:
            return None
        return self._employees.get(employee_id.strip().upper())


def requested_leave_types(query: str) -> list[str]:
    query_lower = query.lower()
    aliases = {
        "annual": ("annual", "vacation", "pto", "paid time off"),
        "sick": ("sick", "medical"),
        "casual": ("casual",),
    }
    selected = [
        leave_type
        for leave_type, words in aliases.items()
        if any(word in query_lower for word in words)
    ]
    return selected or list(LEAVE_TYPES)


def format_leave_balance(employee: Employee, query: str) -> str:
    """Format values directly from CSV; no model is involved."""
    leave_types = requested_leave_types(query)
    lines = [
        f"Here is the demo leave balance for **{employee.name} "
        f"({employee.employee_id})**:"
    ]
    for leave_type in leave_types:
        balance = employee.balances[leave_type]
        lines.append(
            f"- **{leave_type.title()} leave:** {balance['remaining']} remaining "
            f"({balance['used']} used of {balance['entitled']})"
        )
    lines.extend(
        [
            "",
            "These figures come directly from the fictional employee record. "
            "They are not a leave approval.",
        ]
    )
    return "\n".join(lines)
