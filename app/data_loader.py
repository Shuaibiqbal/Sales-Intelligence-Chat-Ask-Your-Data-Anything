"""
data_loader.py — Data ingestion & validation layer
Supports .gz directly + optimised loading for large files.
"""
from __future__ import annotations

import io
import warnings
import pandas as pd
import streamlit as st
from pathlib import Path
from typing import Optional

# Suppress pandas FutureWarning about observed parameter in groupby with categoricals.
# LangChain-experimental's generated pandas code triggers this with categorical columns.
warnings.filterwarnings(
    "ignore",
    message="The default value of observed=False is deprecated",
    category=FutureWarning,
)

from app.config import AppConfig
_cfg = AppConfig()


def auto_load_data() -> Optional[pd.DataFrame]:
    """Auto-load the first supported file found in the data/ folder."""
    data_dir = Path("data")
    if not data_dir.exists():
        return None

    # Supported extensions including .gz
    supported = [".csv", ".xlsx", ".xls", ".parquet", ".gz"]
    found_files = []
    for ext in supported:
        found_files.extend(data_dir.glob(f"*{ext}"))

    if not found_files:
        return None

    file_path = found_files[0]

    try:
        with st.spinner(f"📂 Loading `{file_path.name}` — please wait…"):
            df = _read_file_from_path(file_path)
            if df is not None:
                df = _normalise_columns(df)
                st.sidebar.success(f"✅ Loaded **{file_path.name}**")
        return df
    except Exception as exc:
        st.error(f"Failed to auto-load `{file_path.name}`: {exc}")
        return None


def load_data(uploaded_file) -> Optional[pd.DataFrame]:
    """Parse an uploaded Streamlit file object into a DataFrame."""
    try:
        suffix = Path(uploaded_file.name).suffix.lower()
        raw = uploaded_file.read()

        if suffix == ".gz":
            df = pd.read_csv(io.BytesIO(raw), compression="gzip")
        elif suffix == ".csv":
            df = pd.read_csv(io.BytesIO(raw))
        elif suffix in (".xlsx", ".xls"):
            df = pd.read_excel(io.BytesIO(raw))
        elif suffix == ".parquet":
            df = pd.read_parquet(io.BytesIO(raw))
        else:
            st.error(f"Unsupported file type: `{suffix}`")
            return None

        return _normalise_columns(df)

    except Exception as exc:
        st.error(f"Failed to load file: {exc}")
        return None


def get_dataframe_summary(df: pd.DataFrame) -> dict:
    return {
        "rows": f"{len(df):,}",
        "columns": len(df.columns),
        "memory": f"{df.memory_usage(deep=True).sum() / 1024**2:.1f} MB",
        "column_names": list(df.columns),
    }


def _read_file_from_path(file_path: Path) -> Optional[pd.DataFrame]:
    """
    Read file from disk with optimised settings for large files.
    Supports .csv, .csv.gz, .gz, .xlsx, .parquet
    """
    name   = file_path.name.lower()
    suffix = file_path.suffix.lower()

    # ── CSV / GZ ───────────────────────────────────────────────────────────────
    if suffix == ".gz" or name.endswith(".csv.gz"):
        return _read_large_csv(file_path, compression="gzip")

    elif suffix == ".csv":
        return _read_large_csv(file_path, compression=None)

    # ── Excel ──────────────────────────────────────────────────────────────────
    elif suffix in (".xlsx", ".xls"):
        return pd.read_excel(file_path)

    # ── Parquet (already fast & compressed) ───────────────────────────────────
    elif suffix == ".parquet":
        return pd.read_parquet(file_path)

    return None


def _read_large_csv(file_path: Path, compression) -> pd.DataFrame:
    """
    Memory-optimised CSV reader.
    - Uses categorical dtype for low-cardinality string columns
    - Downcasts numerics to save RAM
    """
    # First pass: read with optimised dtypes
    df = pd.read_csv(
        file_path,
        compression=compression,
        low_memory=False,
        dtype={
            # Categorical for known string columns → huge RAM saving
            "month":       "category",
            "year":        "int16",
            "region":      "category",
            "city":        "category",
            "area":        "category",
            "territory":   "category",
            "distributor": "category",
            "route":       "category",
            "customer":    "category",
            "brand":       "category",
            "variant":     "category",
            "packtype":    "category",
            "sku":         "category",
        },
    )

    # Downcast numeric columns to save RAM
    float_cols = df.select_dtypes(include=["float64"]).columns
    int_cols   = df.select_dtypes(include=["int64"]).columns
    df[float_cols] = df[float_cols].astype("float32")
    df[int_cols]   = df[int_cols].astype("int32")

    return df


def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip().lower() for c in df.columns]
    return df
