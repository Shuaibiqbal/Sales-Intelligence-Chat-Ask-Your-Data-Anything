"""
chat_history.py — Session-scoped conversation history
======================================================
All state lives in st.session_state so it survives reruns
but resets on page refresh (stateless prototype behaviour).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List

import streamlit as st


# ── Message model ──────────────────────────────────────────────────────────────

@dataclass
class Message:
    role: str                        # "user" | "assistant"
    content: str                     # display text
    timestamp: str = field(
        default_factory=lambda: datetime.now().strftime("%H:%M:%S")
    )
    has_table: bool = False
    table_json: str = ""             # serialised DataFrame for re-display
    has_csv: bool = False
    csv_data: str = ""               # CSV string ready for download
    csv_filename: str = ""           # suggested filename


# ── History manager ────────────────────────────────────────────────────────────

HISTORY_KEY  = "chat_history"
MEMORY_KEY   = "lc_memory"
ENGINE_KEY   = "query_engine"


def init_history() -> None:
    """Ensure the history list exists in session state."""
    if HISTORY_KEY not in st.session_state:
        st.session_state[HISTORY_KEY] = []


def add_message(
    role: str,
    content: str,
    table=None,
    csv_data: str = "",
    csv_filename: str = "",
) -> None:
    """Append a message to the session history."""
    init_history()
    msg = Message(role=role, content=content)

    if table is not None:
        msg.has_table = True
        msg.table_json = table.to_json(orient="split")
        # Auto-generate CSV from table if no explicit csv_data provided
        if not csv_data:
            msg.has_csv   = True
            msg.csv_data  = table.to_csv(index=False)
            msg.csv_filename = csv_filename or "result.csv"

    if csv_data:
        msg.has_csv      = True
        msg.csv_data     = csv_data
        msg.csv_filename = csv_filename or "result.csv"

    st.session_state[HISTORY_KEY].append(msg)


def get_history() -> List[Message]:
    init_history()
    return st.session_state[HISTORY_KEY]


def clear_history() -> None:
    """
    Wipe UI chat history, LangChain memory, and the cached engine
    so all three stay in sync.
    """
    st.session_state[HISTORY_KEY] = []

    mem = st.session_state.get(MEMORY_KEY)
    if mem is not None:
        try:
            mem.clear()
        except Exception:
            pass

    st.session_state[ENGINE_KEY] = None


def export_history_json() -> str:
    """Serialise full history to JSON string for download."""
    return json.dumps(
        [asdict(m) for m in get_history()],
        indent=2,
        ensure_ascii=False,
    )
