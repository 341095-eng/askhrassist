"""Streamlit entry point for the AsterPeak HR Helpdesk Assistant."""

from __future__ import annotations

import streamlit as st

from hr_assistant.config import EMPLOYEE_FILE, HANDBOOK_DIR, load_settings
from hr_assistant.conversation import AssistantEngine
from hr_assistant.leave_tool import EmployeeDirectory
from hr_assistant.retrieval import HandbookRetriever
from hr_assistant.tickets import (
    Ticket,
    create_ticket,
    summarize_conversation,
    tickets_to_csv,
)

st.set_page_config(
    page_title="AsterPeak HR Helpdesk",
    page_icon="💬",
    layout="centered",
)


@st.cache_resource
def load_resources() -> tuple[EmployeeDirectory, HandbookRetriever]:
    return EmployeeDirectory(EMPLOYEE_FILE), HandbookRetriever(HANDBOOK_DIR)


def initialize_state() -> None:
    defaults = {
        "messages": [
            {
                "role": "assistant",
                "content": (
                    "Hello! I’m AsterPeak’s AI HR Helpdesk Assistant. I can explain "
                    "handbook policies, show a fictional employee’s leave balance, or "
                    "create a demo HR ticket. How can I help?"
                ),
            }
        ],
        "tickets": [],
        "last_route": None,
        "last_debug": {},
        "pending_ticket": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def add_assistant_message(
    text: str, *, route: str, debug: dict[str, object] | None = None
) -> None:
    st.session_state.messages.append(
        {"role": "assistant", "content": text, "route": route}
    )
    st.session_state.last_route = route
    st.session_state.last_debug = debug or {"route": route}


def make_handoff_ticket(employee_id: str | None) -> Ticket:
    ticket = create_ticket(
        st.session_state.tickets,
        employee_id=employee_id,
        category="Human handoff",
        description="Employee requested assistance from a human HR representative.",
        conversation_summary=summarize_conversation(st.session_state.messages),
    )
    st.session_state.tickets.append(ticket)
    return ticket


def process_ticket_reply(prompt: str, employee_id: str | None) -> bool:
    pending = st.session_state.pending_ticket
    if not pending:
        return False

    normalized = prompt.strip().lower()
    if pending["stage"] == "confirmation":
        if normalized in {"yes", "y", "sure", "okay", "ok", "please do"}:
            pending["stage"] = "description"
            add_assistant_message(
                "Please give a short, non-sensitive description of what HR should "
                "help with.",
                route="ticket: collect description",
            )
        elif normalized in {"no", "n", "cancel", "never mind", "nevermind"}:
            st.session_state.pending_ticket = None
            add_assistant_message(
                "No ticket was created. You can ask another HR question at any time.",
                route="ticket: cancelled",
            )
        else:
            add_assistant_message(
                "Please reply **yes** to raise a ticket or **no** to cancel.",
                route="ticket: confirmation",
            )
        return True

    ticket = create_ticket(
        st.session_state.tickets,
        employee_id=employee_id,
        category=pending.get("category", "Policy question"),
        description=prompt,
        conversation_summary=summarize_conversation(st.session_state.messages),
    )
    st.session_state.tickets.append(ticket)
    st.session_state.pending_ticket = None
    add_assistant_message(
        f"Created demo ticket **{ticket.ticket_id}**. It exists only in this browser "
        "session; download the CSV from the sidebar if you need to keep it.",
        route="ticket: created",
        debug={"route": "ticket: created", "ticket_id": ticket.ticket_id},
    )
    return True


settings = load_settings()
directory, retriever = load_resources()
engine = AssistantEngine(settings, retriever)
initialize_state()

st.title("AsterPeak HR Helpdesk Assistant")
st.warning(
    "You’re chatting with an AI assistant, not a human. Messages are sent to a "
    "third-party LLM API. Don’t enter sensitive personal information.",
    icon="⚠️",
)
st.caption(
    "Educational demo using entirely fictional company, handbook, employee, and "
    "ticket data. Responses are general guidance—not binding HR decisions."
)

with st.sidebar:
    st.header("Demo identity")
    st.info(
        "**AI disclosure:** This is not a human. Policy questions may be sent to "
        "OpenAI with only retrieved handbook excerpts. Do not enter sensitive data."
    )

    employees = directory.all()
    labels = ["No employee selected"] + [employee.display_name for employee in employees]
    selected_label = st.selectbox(
        "Select a fictional employee",
        labels,
        help="Demo identity selection only—this is not real authentication.",
    )
    manual_id = st.text_input(
        "Or enter employee ID",
        placeholder="e.g. AP1001",
        help="A valid manual ID takes priority over the dropdown.",
    ).strip()

    selected_employee = None
    if manual_id:
        selected_employee = directory.get(manual_id)
        if selected_employee is None:
            st.error("Employee ID not found in the fictional demo data.")
    elif selected_label != labels[0]:
        selected_id = selected_label.rsplit("(", 1)[-1].rstrip(")")
        selected_employee = directory.get(selected_id)

    if selected_employee:
        st.success(
            f"Demo user: {selected_employee.name}\n\n"
            f"{selected_employee.department} · Manager: {selected_employee.manager}"
        )
    st.caption("Identity selection is for demonstration only and provides no security.")

    if not settings.has_api_key:
        st.warning("OpenAI API key is not configured. Deterministic features still work.")
    elif settings.simulate_api_failure:
        st.error("SIMULATE_API_FAILURE is ON. Policy API calls will fail for demo.")
    else:
        st.caption(f"LLM configured: `{settings.model}`")

    if st.button("👤 Talk to a human", use_container_width=True):
        ticket = make_handoff_ticket(
            selected_employee.employee_id if selected_employee else None
        )
        add_assistant_message(
            f"I created demo handoff ticket **{ticket.ticket_id}** with a short local "
            "conversation summary. Download it below if you need to keep it.",
            route="human handoff",
            debug={"route": "human handoff", "ticket_id": ticket.ticket_id},
        )
        st.rerun()

    st.divider()
    st.subheader("Tickets")
    tickets: list[Ticket] = st.session_state.tickets
    st.write(f"Session tickets: **{len(tickets)}**")
    if tickets:
        st.download_button(
            "Download ticket log (CSV)",
            data=tickets_to_csv(tickets),
            file_name="asterpeak_hr_tickets.csv",
            mime="text/csv",
            use_container_width=True,
        )
    st.caption(
        "Tickets are session-only on the free host and disappear when the session "
        "resets. This demo does not send tickets to a real HR system."
    )

    st.divider()
    show_debug = st.toggle("Debug / Transparency", value=False)
    if show_debug:
        st.caption("Latest request trace. Secrets and full employee records are hidden.")
        if st.session_state.last_debug:
            st.json(st.session_state.last_debug, expanded=False)
        else:
            st.write("Ask a question to create a trace.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Ask an HR question…")
if prompt:
    clean_prompt = prompt.strip()[:2000]
    st.session_state.messages.append({"role": "user", "content": clean_prompt})
    with st.chat_message("user"):
        st.markdown(clean_prompt)

    employee_id = selected_employee.employee_id if selected_employee else None
    if not process_ticket_reply(clean_prompt, employee_id):
        prior_history = st.session_state.messages[:-1]
        response = engine.answer(
            clean_prompt,
            employee=selected_employee,
            history=prior_history,
            last_route=st.session_state.last_route,
        )
        add_assistant_message(
            response.text,
            route=response.route,
            debug=response.debug,
        )
        if response.ticket_offer:
            st.session_state.pending_ticket = {
                "stage": "confirmation",
                "category": "Unanswered HR question",
            }
        if response.create_handoff_ticket:
            ticket = make_handoff_ticket(employee_id)
            st.session_state.messages[-1]["content"] += (
                f"\n\nCreated demo ticket **{ticket.ticket_id}**. It is session-only "
                "and available for CSV download in the sidebar."
            )

    with st.chat_message("assistant"):
        st.markdown(st.session_state.messages[-1]["content"])
