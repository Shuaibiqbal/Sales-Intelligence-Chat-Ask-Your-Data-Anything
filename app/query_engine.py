"""
query_engine.py — AI-powered query layer
"""

from __future__ import annotations

import traceback
import warnings
from typing import TYPE_CHECKING, Any, Optional

import pandas as pd
import streamlit as st

warnings.filterwarnings("ignore", category=FutureWarning)

if TYPE_CHECKING:
    from langchain.agents.agent import AgentExecutor

from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_openai import ChatOpenAI


_MEMORY_KEY = "lc_memory"

_MONTH_NAME = {
    1:"January", 2:"February", 3:"March", 4:"April",
    5:"May", 6:"June", 7:"July", 8:"August",
    9:"September", 10:"October", 11:"November", 12:"December",
}


def _enrich_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add helper columns so the LLM can filter reliably without dtype surprises.

    New columns added (only if source cols exist):
      - month_int   : int version of month (always plain int64, never category)
      - year_int    : int version of year  (always plain int64)
      - month_name  : human-readable month name string  e.g. "August"
      - period      : "Aug-2024" style label — unambiguous filter key
      - period_int  : YYYYMM integer  e.g. 202408  — easy range queries
    """
    df = df.copy()

    if "month" in df.columns:
        df["month_int"]  = pd.to_numeric(df["month"], errors="coerce").astype("Int64")
        df["month_name"] = df["month_int"].map(_MONTH_NAME).fillna("Unknown")

    if "year" in df.columns:
        df["year_int"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    if "month_int" in df.columns and "year_int" in df.columns:
        df["period"]     = df["month_name"] + "-" + df["year_int"].astype(str)
        df["period_int"] = df["year_int"] * 100 + df["month_int"]   # e.g. 202408

    return df


def _build_dynamic_system_prefix(df: pd.DataFrame) -> str:
    """Build a fully dynamic, data-driven system prompt."""

    # ── 1. Column schema ───────────────────────────────────────────────────────
    col_lines = []
    for col in df.columns:
        dtype    = str(df[col].dtype)
        n_unique = df[col].nunique()
        if dtype == "bool":
            t  = int((df[col] == True).sum())   # noqa: E712
            f_ = int((df[col] == False).sum())  # noqa: E712
            col_lines.append(f"  {col:<24} BOOLEAN    True={t:,}  False={f_:,}")
        elif dtype == "category":
            samples = df[col].astype(str).dropna().unique()[:6].tolist()
            col_lines.append(f"  {col:<24} category   unique={n_unique}  samples={samples}")
        elif dtype == "object" and n_unique <= 60:
            samples = df[col].dropna().unique()[:6].tolist()
            col_lines.append(f"  {col:<24} string     unique={n_unique}  samples={samples}")
        elif dtype.startswith(("int","float","Int")):
            mn = df[col].min(); mx = df[col].max()
            col_lines.append(f"  {col:<24} {dtype:<10} min={mn}  max={mx}")
        else:
            col_lines.append(f"  {col:<24} {dtype:<10} unique={n_unique}")
    schema_block = "\n".join(col_lines)

    # ── 2. VERIFIED period → row count table ───────────────────────────────────
    period_lines = []
    if "period" in df.columns and "period_int" in df.columns:
        grp = (
            df.groupby(["year_int", "month_int", "month_name", "period", "period_int"],
                       observed=True)
            .size()
            .reset_index(name="row_count")
            .sort_values("period_int")
        )
        for _, r in grp.iterrows():
            period_lines.append(
                f"  year_int={int(r.year_int)}  month_int={int(r.month_int)}"
                f"  month_name='{r.month_name}'  period='{r.period}'  rows={int(r.row_count):,}"
            )
    periods_block = "\n".join(period_lines) if period_lines else "  (not available)"

    # ── 3. Stockout column info ────────────────────────────────────────────────
    stockout_note = ""
    if "stockout" in df.columns:
        sc_dtype   = str(df["stockout"].dtype)
        sc_nonzero = int((pd.to_numeric(df["stockout"], errors="coerce") > 0).sum())
        sc_samples = sorted(pd.to_numeric(df["stockout"], errors="coerce").dropna().unique().tolist())[:8]
        stockout_note = f"""
STOCKOUT COLUMN INFO:
  dtype={sc_dtype}, sample_values={sc_samples}, non_zero_rows={sc_nonzero:,}

  Correct pattern to count stockout brands in a month:
    month_df     = df[df['month_int'] == 4]            # April = 4
    stockout_df  = month_df[pd.to_numeric(month_df['stockout'], errors='coerce') > 0]
    brand_count  = stockout_df['brand'].astype(str).nunique()
"""

    # ── 4. Productivity ────────────────────────────────────────────────────────
    prod_note = ""
    if "productivity" in df.columns:
        ptype = str(df["productivity"].dtype)
        if ptype == "bool" or set(df["productivity"].dropna().unique()) <= {True, False}:
            t  = int((df["productivity"] == True).sum())   # noqa: E712
            f_ = int((df["productivity"] == False).sum())  # noqa: E712
            prod_note = f"""
PRODUCTIVITY COLUMN:
  BOOLEAN — True={t:,} (productive outlets), False={f_:,} (unproductive).
  Rate % = (df['productivity']==True).sum() / len(df) * 100
  Filter productive rows: df[df['productivity']==True]
  DO NOT use .sum() or .mean() directly on this column as a number.
"""

    # ── 5. CSV export pattern ─────────────────────────────────────────────────
    csv_note = """
CSV EXPORT:
  When user asks to save/export/download results as CSV:
    result_df.to_csv('output.csv', index=False)
    print("Saved to output.csv")
"""

    return f"""You are an expert sales data analyst with direct access to `df`.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DATASET: {len(df):,} rows × {len(df.columns)} columns
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ALL COLUMNS AND THEIR TYPES:
{schema_block}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VERIFIED PERIODS (pre-computed, guaranteed accurate):
{periods_block}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HELPER COLUMNS ADDED FOR YOU (always use these, never the originals for filtering):
  month_int   → plain integer month (1–12). Use this for all month filters.
  year_int    → plain integer year. Use this for all year filters.
  month_name  → string like "August", "January". Useful for display.
  period      → string like "August-2024". Unique label per month/year.
  period_int  → integer like 202408 (YYYYMM). Best for range/sort queries.

FILTERING RULES — MANDATORY:
  ✅ ALWAYS filter months with:   df[df['month_int'] == 8]    # August
  ✅ ALWAYS filter years with:    df[df['year_int'] == 2024]
  ✅ ALWAYS filter by period:     df[df['period'] == 'August-2024']
  ❌ NEVER filter with:           df[df['month'] == 8]         # 'month' may be category dtype
  ❌ NEVER filter with:           df[df['month'] == 'August']  # month is NOT a string

  Month integer reference:
  January=1, February=2, March=3, April=4, May=5, June=6,
  July=7, August=8, September=9, October=10, November=11, December=12

GROUPBY RULES — MANDATORY:
  ✅ ALWAYS pass observed=True:   df.groupby('brand', observed=True)['sales'].sum()
  ✅ Use .agg() not .apply():     df.groupby('city', observed=True).agg({{'sales':'sum'}})
  ❌ NEVER use .apply(lambda x: x['col']...) on a groupby — causes FutureWarning and wrong results.

CATEGORY DTYPE RULES:
  Columns with category dtype must use .astype(str) before any .str. operation.
  e.g. df['brand'].astype(str).str.lower()
{stockout_note}
{prod_note}
{csv_note}
OUTPUT RULES:
  - Return DataFrames directly as tables — do not convert to string.
  - Always show which period filter was applied (e.g. "Filtered: August-2024, 1,234,567 rows").
  - If user asks for CSV/export, save with .to_csv('output.csv', index=False) and confirm filename.
  - Format all numbers with comma separators.
  - Never show Python code unless user explicitly says "show code".
  - If a period has 0 rows, show the VERIFIED PERIODS table to the user so they can pick a valid one.
""".strip()


# ── Engine builder ─────────────────────────────────────────────────────────────

def build_engine(
    df: pd.DataFrame,
    api_key: str,
    model: str,
) -> Optional[Any]:
    try:
        # Enrich df with helper columns and store enriched version
        enriched_df = _enrich_dataframe(df)
        st.session_state["dataframe_enriched"] = enriched_df

        llm = ChatOpenAI(
            model=model,
            temperature=0.0,
            openai_api_key=api_key,
        )

        system_prefix = _build_dynamic_system_prefix(enriched_df)
        st.session_state["_system_prefix"] = system_prefix

        agent = create_pandas_dataframe_agent(
            llm=llm,
            df=enriched_df,          # use enriched df with helper columns
            agent_type="openai-tools",
            verbose=False,
            allow_dangerous_code=True,
            prefix=system_prefix,
            extra_tools=[],
            max_iterations=20,
            max_execution_time=180,
            handle_parsing_errors=True,
        )

        if _MEMORY_KEY not in st.session_state:
            st.session_state[_MEMORY_KEY] = []

        return agent

    except Exception as exc:
        st.error(f"Failed to initialise AI engine: {exc}")
        traceback.print_exc()
        return None


# ── Query runner ───────────────────────────────────────────────────────────────

def run_query(engine: Any, question: str) -> "QueryResult":
    try:
        history_text = _format_memory()
        full_input = (
            f"{history_text}\nUser: {question}" if history_text else question
        )

        raw    = engine.invoke({"input": full_input})
        answer = raw.get("output", raw) if isinstance(raw, dict) else raw

        _update_memory("user", question)
        _update_memory("assistant", str(answer))

        return QueryResult(success=True, data=answer)

    except Exception as exc:
        _log_error(exc)
        return QueryResult(success=False, error=f"{type(exc).__name__}: {exc}")


# ── Memory helpers ─────────────────────────────────────────────────────────────

def reset_memory() -> None:
    st.session_state[_MEMORY_KEY] = []


def _format_memory() -> str:
    history: list[dict] = st.session_state.get(_MEMORY_KEY, [])
    if not history:
        return ""
    lines = ["Previous conversation:"]
    for turn in history:
        role = "User" if turn["role"] == "user" else "Assistant"
        lines.append(f"  {role}: {turn['content']}")
    return "\n".join(lines)


def _update_memory(role: str, content: str) -> None:
    if _MEMORY_KEY not in st.session_state:
        st.session_state[_MEMORY_KEY] = []
    st.session_state[_MEMORY_KEY].append({"role": role, "content": content})


def _log_error(exc: Exception) -> None:
    traceback.print_exc()


# ── Result wrapper ─────────────────────────────────────────────────────────────

class QueryResult:
    def __init__(self, success: bool, data: Any = None, error: str = "") -> None:
        self.success   = success
        self.data      = data
        self.error     = error
        self.is_table  = isinstance(data, pd.DataFrame)
        self.is_number = isinstance(data, (int, float)) and not isinstance(data, bool)
        self.is_text   = isinstance(data, str)

    def __repr__(self) -> str:
        if self.success:
            return f"QueryResult(success=True, type={type(self.data).__name__})"
        return f"QueryResult(success=False, error={self.error!r})"
