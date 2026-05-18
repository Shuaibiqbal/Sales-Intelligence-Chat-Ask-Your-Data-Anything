"""
config.py — Central configuration for Sales Intelligence Chat
=============================================================
Extend this file to add new models, themes, or feature flags.
"""

import os
from dataclasses import dataclass, field
from typing import List
from dotenv import load_dotenv

load_dotenv()  # loads .env file automatically


@dataclass(frozen=True)
class AppConfig:
    # ── Branding ───────────────────────────────────────────────────────────────
    APP_TITLE: str = "Sales Intelligence Chat"
    APP_ICON: str = "📊"
    APP_VERSION: str = "1.0.0"

    # ── API Key (loaded from .env) ─────────────────────────────────────────────
    OPENAI_API_KEY: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))

    # ── LLM settings ──────────────────────────────────────────────────────────
    # Using real, current OpenAI models that support tool-calling (OPENAI_TOOLS).
    # Removed fake "gpt-5.4-mini" — this model does not exist.
    DEFAULT_MODEL: str = "gpt-4.1-mini"
    AVAILABLE_MODELS: List[str] = field(default_factory=lambda: [
        "gpt-4.1-mini",       # Best value — fast, cheap, supports tool-calling
        "gpt-4.1",            # Most capable GPT-4.1
        "gpt-4o",             # GPT-4o — powerful multimodal
        "gpt-4o-mini",        # GPT-4o-mini — fast & affordable
        "gpt-4-turbo",        # Legacy GPT-4 Turbo
    ])
    MAX_TOKENS: int = 2048
    TEMPERATURE: float = 0.0          # 0 = deterministic → better for analytics

    # ── Data settings ─────────────────────────────────────────────────────────
    SUPPORTED_EXTENSIONS: List[str] = field(default_factory=lambda: [
        ".csv", ".xlsx", ".xls", ".parquet",
    ])
    MAX_UPLOAD_MB: int = 50

    # ── Expected columns in the sales dataframe ────────────────────────────────
    EXPECTED_COLUMNS: List[str] = field(default_factory=lambda: [
        "month", "year", "region", "city", "area", "territory",
        "distributor", "route", "customer", "brand", "variant",
        "packtype", "sku", "sales", "primary sales", "target",
        "productivity", "mro", "unproductive_mro", "unassorted_mro",
        "stockout_mro", "stockout", "assortment", "mto",
    ])

    # ── Sample questions shown in the sidebar ─────────────────────────────────
    SAMPLE_QUESTIONS: List[str] = field(default_factory=lambda: [
        "Total stockout brands in April",
        "Which region has the highest sales?",
        "Top 5 SKUs by primary sales",
        "Monthly sales trend by brand",
        "Unproductive MRO by territory",
        "Compare target vs actual sales by city",
        "Which distributor has the lowest productivity?",
        "Assortment score by area",
    ])
