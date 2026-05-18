"""
Sales Intelligence Chat — Main Entry Point
==========================================
Run with:  streamlit run app.py
"""

import streamlit as st
from app.ui import render_sidebar, render_chat_interface
from app.config import AppConfig

# Single shared config instance
_cfg = AppConfig()

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title=_cfg.APP_TITLE,
    page_icon=_cfg.APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inject global CSS ──────────────────────────────────────────────────────────
with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
render_sidebar()

# ── Main chat interface ────────────────────────────────────────────────────────
render_chat_interface()
