"""Deterministic pre-LLM safety checks."""

from __future__ import annotations

import re

INJECTION_PATTERNS = (
    r"\bignore (all |any |the )?(previous|prior|system|developer) instructions?\b",
    r"\b(reveal|show|print|repeat|leak).{0,30}\b(system prompt|hidden prompt|instructions)\b",
    r"\bact as (an? )?(unrestricted|unfiltered|jailbroken)\b",
    r"\bdeveloper mode\b",
    r"\bprompt injection\b",
    r"\bdo anything now\b",
)

OFF_TOPIC_GROUPS = {
    "coding": (
        "write code", "debug my code", "python script", "javascript", "sql query",
        "coding homework", "build a website",
    ),
    "politics": (
        "election", "political party", "president", "prime minister", "who should i vote",
    ),
    "medical advice": (
        "diagnose me", "what medicine", "medical diagnosis", "treat my", "dosage",
    ),
    "legal advice": (
        "legal advice", "sue", "lawsuit", "is this legal", "my lawyer",
    ),
}

SENSITIVE_TERMS = (
    "harass", "bully", "discriminat", "retaliat", "grievance", "terminated",
    "termination", "fired", "misconduct", "assault", "threat",
)

SENSITIVE_GUIDANCE = (
    "This may be a sensitive workplace matter. Please avoid sharing names, medical "
    "details, allegations, or confidential documents here. For confidential help, "
    "contact an HR business partner or **ethics@asterpeak.example**. If anyone is in "
    "immediate danger, contact local emergency services and site security."
)


def is_prompt_injection(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in INJECTION_PATTERNS)


def off_topic_category(text: str) -> str | None:
    lowered = text.lower()
    for category, phrases in OFF_TOPIC_GROUPS.items():
        if any(phrase in lowered for phrase in phrases):
            return category
    return None


def is_sensitive_hr_topic(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in SENSITIVE_TERMS)


def injection_refusal() -> str:
    return (
        "I can’t follow requests to ignore my safeguards or reveal hidden "
        "instructions. I can still help with AsterPeak HR policies, your demo leave "
        "balance, or raising an HR ticket."
    )


def scope_refusal(category: str) -> str:
    return (
        f"I can’t help with {category}. I’m limited to AsterPeak workplace policies, "
        "demo leave balances, and HR ticket handoff. What HR topic can I help with?"
    )
