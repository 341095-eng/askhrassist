"""Environment and Streamlit secrets configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None  # type: ignore

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
HANDBOOK_DIR = DATA_DIR / "handbook"
EMPLOYEE_FILE = DATA_DIR / "employees.csv"


def _streamlit_secret(name: str) -> Any | None:
    try:
        import streamlit as st
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        if get_script_run_ctx(suppress_warning=True) is None:
            return None
        return st.secrets.get(name)
    except (FileNotFoundError, KeyError, RuntimeError):
        return None


def _value(name: str, default: str) -> str:
    secret = _streamlit_secret(name)
    return str(secret if secret is not None else os.getenv(name, default))


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    provider: str
    api_key: str
    model: str
    temperature: float
    timeout_seconds: float
    rag_top_k: int
    rag_min_score: float
    simulate_api_failure: bool

    @property
    def has_api_key(self) -> bool:
        return bool(self.api_key and "replace-with" not in self.api_key.lower())


def load_settings() -> Settings:
    """Load settings, preferring Streamlit secrets over environment variables."""
    if load_dotenv is not None:
        load_dotenv(ROOT_DIR / ".env")
    return Settings(
        provider=_value("LLM_PROVIDER", "openai").strip().lower(),
        api_key=_value("OPENAI_API_KEY", "").strip(),
        model=_value("OPENAI_MODEL", "gpt-4o-mini").strip(),
        temperature=float(_value("LLM_TEMPERATURE", "0.1")),
        timeout_seconds=float(_value("LLM_TIMEOUT_SECONDS", "20")),
        rag_top_k=max(1, int(_value("RAG_TOP_K", "3"))),
        rag_min_score=max(0.0, float(_value("RAG_MIN_SCORE", "1.5"))),
        simulate_api_failure=_as_bool(_value("SIMULATE_API_FAILURE", "false")),
    )
