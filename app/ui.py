"""
ui.py — All Streamlit rendering logic
"""
from __future__ import annotations

import re
from datetime import datetime

import pandas as pd
import streamlit as st

from app.config import AppConfig
from app.chat_history import (
    add_message, clear_history, export_history_json,
    get_history, init_history,
)
from app.data_loader import get_dataframe_summary, load_data, auto_load_data
from app.query_engine import build_engine, run_query, reset_memory

# Single shared config instance
_cfg = AppConfig()

_DF_KEY      = "dataframe"
_ENGINE_KEY  = "query_engine"
_API_KEY     = "openai_api_key"
_MODEL_KEY   = "selected_model"
_PREV_MODEL  = "prev_model"
_AUTO_LOADED = "auto_loaded"


# ── Sidebar ────────────────────────────────────────────────────────────────────

def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            f"""
            <div class="sidebar-header">
                <span class="sidebar-icon">📊</span>
                <div>
                    <div class="sidebar-title">{_cfg.APP_TITLE}</div>
                    <div class="sidebar-version">v{_cfg.APP_VERSION}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()

        # ── API key ────────────────────────────────────────────────────────────
        if _cfg.OPENAI_API_KEY:
            st.session_state[_API_KEY] = _cfg.OPENAI_API_KEY
            st.success("🔑 API key loaded from .env")
        else:
            st.error("⚠️ OPENAI_API_KEY not found in .env file")

        # ── Model selector ─────────────────────────────────────────────────────
        st.markdown("#### 🤖 Model")
        selected_model = st.selectbox(
            "Model",
            _cfg.AVAILABLE_MODELS,
            label_visibility="collapsed",
            key=_MODEL_KEY,
        )

        prev_model = st.session_state.get(_PREV_MODEL)
        if prev_model is not None and selected_model != prev_model:
            st.session_state[_ENGINE_KEY] = None
            reset_memory()
            st.info(f"Model changed to **{selected_model}** — engine restarted.")
        st.session_state[_PREV_MODEL] = selected_model

        st.divider()

        # ── Auto-load dataset ──────────────────────────────────────────────────
        if not st.session_state.get(_AUTO_LOADED):
            df = auto_load_data()
            if df is not None:
                st.session_state[_DF_KEY] = df
                st.session_state[_ENGINE_KEY] = None
                st.session_state[_AUTO_LOADED] = True

        df = st.session_state.get(_DF_KEY)
        if df is not None:
            st.markdown("#### 📊 Dataset")
            _render_data_summary(df)
        else:
            st.markdown("#### 📁 Upload Dataset")
            st.caption("Or place file in `data/` folder for auto-load")
            uploaded = st.file_uploader(
                "Upload",
                type=["csv", "xlsx", "xls", "parquet"],
                label_visibility="collapsed",
                help=f"Max {_cfg.MAX_UPLOAD_MB} MB",
            )
            if uploaded:
                with st.spinner("Loading data…"):
                    df = load_data(uploaded)
                if df is not None:
                    st.session_state[_DF_KEY] = df
                    st.session_state[_ENGINE_KEY] = None
                    st.session_state[_AUTO_LOADED] = True
                    st.success(f"✅ Loaded **{uploaded.name}**")
                    st.rerun()

        st.divider()

        # ── Sample questions ───────────────────────────────────────────────────
        st.markdown("#### 💡 Sample Questions")
        for q in _cfg.SAMPLE_QUESTIONS:
            if st.button(q, use_container_width=True, key=f"sample_{q}"):
                _submit_question(q)

        st.divider()

        # ── Utility buttons ────────────────────────────────────────────────────
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                clear_history()
                st.rerun()
        with col2:
            st.download_button(
                "⬇️ Export",
                data=export_history_json(),
                file_name="chat_history.json",
                mime="application/json",
                use_container_width=True,
            )


# ── Data summary ───────────────────────────────────────────────────────────────

def _render_data_summary(df: pd.DataFrame) -> None:
    summary = get_dataframe_summary(df)
    st.markdown(
        f"""
        <div class="data-summary">
            <div class="summary-item"><span class="s-label">Rows</span>
                <span class="s-value">{summary['rows']}</span></div>
            <div class="summary-item"><span class="s-label">Columns</span>
                <span class="s-value">{summary['columns']}</span></div>
            <div class="summary-item"><span class="s-label">Memory</span>
                <span class="s-value">{summary['memory']}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("Column names"):
        st.write(summary["column_names"])


# ── Main chat interface ────────────────────────────────────────────────────────

def render_chat_interface() -> None:
    init_history()

    st.markdown(
        """
        <div class="hero">
            <h1 class="hero-title">Sales Intelligence Chat</h1>
            <p class="hero-subtitle">
                Ask anything about your sales data — in plain English.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df      = st.session_state.get(_DF_KEY)
    api_key = st.session_state.get(_API_KEY, "")

    if df is None or not api_key:
        _render_empty_state(df, api_key)
        return

    engine = st.session_state.get(_ENGINE_KEY)
    if engine is None:
        with st.spinner("Initialising AI engine…"):
            engine = build_engine(
                df,
                api_key,
                st.session_state.get(_MODEL_KEY, _cfg.DEFAULT_MODEL),
            )
        if engine is None:
            return
        st.session_state[_ENGINE_KEY] = engine

    _render_history()

    if question := st.chat_input("Ask a question about your data…"):
        _submit_question(question, engine=engine, df=df)


# ── Question handler ───────────────────────────────────────────────────────────

def _submit_question(question: str, engine=None, df=None) -> None:
    if engine is None:
        engine = st.session_state.get(_ENGINE_KEY)
    if df is None:
        df = st.session_state.get(_DF_KEY)

    if engine is None or df is None:
        st.warning("Dataset not loaded yet. Please wait or upload manually.")
        return

    add_message("user", question)

    with st.spinner("Thinking…"):
        result = run_query(engine, question)

    if result.success:
        if result.is_table:
            fname = _safe_filename(question)
            add_message(
                "assistant",
                f"Here are the results for: *{question}*",
                table=result.data,
                csv_filename=fname,
            )
        elif result.is_number:
            add_message("assistant", f"**{result.data:,.2f}**")
        else:
            # Check if the text answer mentions a CSV was saved — offer download
            answer_text = str(result.data)
            csv_data, csv_name = _extract_csv_from_answer(answer_text, question)
            add_message(
                "assistant",
                answer_text,
                csv_data=csv_data,
                csv_filename=csv_name,
            )
    else:
        add_message(
            "assistant",
            f"⚠️ I couldn't answer that query.\n\n**Error:** `{result.error}`\n\n"
            "Try rephrasing or check if the relevant columns exist in your dataset.",
        )

    st.rerun()


# ── History renderer ───────────────────────────────────────────────────────────

def _render_history() -> None:
    for idx, msg in enumerate(get_history()):
        with st.chat_message(msg.role):
            st.markdown(msg.content)

            # Render table if present
            if msg.has_table and msg.table_json:
                try:
                    tbl = pd.read_json(msg.table_json, orient="split")
                    st.dataframe(tbl, use_container_width=True, hide_index=True)
                except Exception:
                    pass

            # ── CSV download button ────────────────────────────────────────────
            if msg.has_csv and msg.csv_data and msg.role == "assistant":
                st.download_button(
                    label="⬇️ Download CSV",
                    data=msg.csv_data,
                    file_name=msg.csv_filename or "result.csv",
                    mime="text/csv",
                    key=f"csv_dl_{idx}",
                    use_container_width=False,
                )

            st.caption(msg.timestamp)


# ── Empty state ────────────────────────────────────────────────────────────────

def _render_empty_state(df, api_key: str) -> None:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            """
            <div class="empty-state">
                <div class="empty-icon">🚀</div>
                <h3>Get started</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if not api_key:
            st.info("**1.** Add your OpenAI API key to the `.env` file")
        if df is None:
            st.info("**2.** Place your dataset in the `data/` folder")


# ── Helpers ────────────────────────────────────────────────────────────────────

def _safe_filename(question: str) -> str:
    """Turn a question string into a safe CSV filename."""
    slug = re.sub(r"[^\w\s-]", "", question.lower())
    slug = re.sub(r"[\s]+", "_", slug).strip("_")[:50]
    ts   = datetime.now().strftime("%H%M%S")
    return f"{slug}_{ts}.csv"


def _extract_csv_from_answer(answer: str, question: str) -> tuple[str, str]:
    """
    When the agent saves a CSV to disk (e.g. 'Saved to output.csv'),
    we cannot access that file — instead we return empty strings so the
    UI won't show a broken download button.  Tables come through
    result.is_table and are handled separately with auto-CSV generation.
    """
    return "", ""
