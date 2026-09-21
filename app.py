# COPIA ISOLADA PARA TESTE EM NUVEM. Consulte README.md.
import streamlit as st
import psycopg
import cloud_db
import hashlib
from cloud_db import get_conn, read_sql_query
import pandas as pd
import streamlit.components.v1 as components
from datetime import datetime, timedelta
from html import escape
import time, io, base64, os, re, bcrypt, json, shutil, zipfile
from pathlib import Path
from urllib.parse import quote
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

st.set_page_config(
    page_title="TESTE — Controle de Estoque",
    layout="wide",
    initial_sidebar_state="auto"
)

# ═══════════════════════════════════════════════════════════════════════════════
# CSS GLOBAL — seletores reais do Streamlit/BaseWeb, sem hacks
# ═══════════════════════════════════════════════════════════════════════════════
def localizar_imagem_fundo(base_dir):
    # Fundo oficial da tela. Nao usar busca generica: ela podia selecionar
    # imagens antigas, comprimidas ou com o brasao incorreto.
    nome = "fundofinal.png"
    return nome if os.path.isfile(os.path.join(base_dir, nome)) else ""


def inject_css():
    bg_css = ""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    nome_imagem = localizar_imagem_fundo(base_dir)
    if nome_imagem:
        bg_path = os.path.join(base_dir, nome_imagem)
        with open(bg_path, "rb") as f:
            enc = base64.b64encode(f.read()).decode()
        ext = os.path.splitext(nome_imagem)[1].lower().lstrip(".").replace("jpg", "jpeg")
        bg_css = f'background-image:url("data:image/{ext};base64,{enc}");background-size:cover;background-position:right top;background-repeat:no-repeat;background-attachment:fixed;'

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* ── BASE ─────────────────────────────────────────────── */
    :root {{
        --bg: #0f172a;
        --surface: rgba(15, 23, 42, 0.88);
        --surface-field: #111827;
        --surface-field-focus: #172554;
        --surface-soft: rgba(30, 41, 59, 0.70);
        --surface-strong: rgba(15, 23, 42, 0.74);
        --border: rgba(226, 232, 240, 0.20);
        --text: #ffffff;
        --text-muted: #e2e8f0;
        --text-subtle: #cbd5e1;
        --text-faint: #94a3b8;
        --title-blue: #dbeafe;
        --primary: #2563eb;
        --primary-dark: #1d4ed8;
        --success: #10b981;
        color-scheme: dark;
    }}
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif !important; }}
    .stApp {{
        {bg_css}
        background-color: rgba(2, 6, 23, 0.48);
        background-blend-mode: multiply;
        color: var(--text);
    }}
    header[data-testid="stHeader"] {{
        display: block !important;
        visibility: visible !important;
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
    }}
    header[data-testid="stHeader"]::before,
    header[data-testid="stHeader"]::after,
    header[data-testid="stHeader"] *,
    div[data-testid="stToolbar"],
    div[data-testid="stDecoration"],
    div[data-testid="stStatusWidget"] {{
        background: transparent !important;
        background-color: transparent !important;
    }}

    /* ── CONTAINER PRINCIPAL ──────────────────────────────── */
    .main .block-container {{
        background: var(--surface-strong) !important;
        backdrop-filter: blur(5px);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 20px 24px 32px !important;
        max-width: 1380px !important;
    }}

    /* ── TÍTULOS ──────────────────────────────────────────── */
    h1  {{ color: var(--title-blue) !important; font-size: 1.4rem !important; font-weight: 700 !important; margin-bottom: 16px !important; }}
    h2  {{ color: #bfdbfe !important; font-size: 1.15rem !important; font-weight: 600 !important; }}
    h3  {{ color: #e0f2fe !important; font-size: 0.97rem !important; font-weight: 600 !important; }}
    p, li, span, label {{ color: var(--text-muted) !important; }}
    p, li {{ font-size: 0.83rem !important; }}

    /* ── LABELS (todos os widgets) ────────────────────────── */
    div[data-testid="stTextInput"]    > label,
    div[data-testid="stNumberInput"]  > label,
    div[data-testid="stTextArea"]     > label,
    div[data-testid="stSelectbox"]    > label,
    div[data-testid="stMultiSelect"]  > label {{
        color: #f8fafc !important;
        font-size: 0.72rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.03em !important;
        text-transform: uppercase !important;
        margin-bottom: 2px !important;
    }}

    /* ── INPUT TEXT ───────────────────────────────────────── */
    /* wrapper externo */
    div[data-baseweb="input"] {{
        background: var(--surface-field) !important;
        background-color: var(--surface-field) !important;
        border: 1.5px solid rgba(148, 163, 184, 0.55) !important;
        border-radius: 7px !important;
        height: 36px !important;
        min-height: 36px !important;
        transition: border-color .18s, box-shadow .18s !important;
    }}
    div[data-baseweb="input"] > div {{
        background: transparent !important;
        background-color: transparent !important;
    }}
    div[data-baseweb="input"]:focus-within {{
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(59,130,246,0.15) !important;
        background: var(--surface-field-focus) !important;
        background-color: var(--surface-field-focus) !important;
    }}
    /* o <input> nativo */
    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input,
    div[data-baseweb="input"] input {{
        background: var(--surface-field) !important;
        background-color: var(--surface-field) !important;
        color: var(--text) !important;
        -webkit-text-fill-color: var(--text) !important;
        font-size: 0.83rem !important;
        height: 34px !important;
        padding: 0 10px !important;
        border: none !important;
        box-shadow: none !important;
        caret-color: #3b82f6 !important;
    }}
    div[data-testid="stTextInput"] input::placeholder,
    div[data-testid="stNumberInput"] input::placeholder,
    div[data-baseweb="input"] input::placeholder {{
        color: #cbd5e1 !important;
        -webkit-text-fill-color: #cbd5e1 !important;
        opacity: 1 !important;
    }}
    div[data-baseweb="input"] input:-webkit-autofill {{
        box-shadow: 0 0 0 1000px var(--surface-field) inset !important;
        -webkit-text-fill-color: var(--text) !important;
        caret-color: #3b82f6 !important;
    }}

    /* ── NUMBER INPUT ─────────────────────────────────────── */
    div[data-testid="stNumberInput"] div[data-baseweb="input"] {{
        height: 36px !important;
        min-height: 36px !important;
    }}
    div[data-testid="stNumberInput"] button {{
        background: transparent !important;
        border: none !important;
        color: #ffffff !important;
    }}

    /* ── TEXTAREA ─────────────────────────────────────────── */
    div[data-baseweb="textarea"] {{
        background: var(--surface-field) !important;
        background-color: var(--surface-field) !important;
        border: 1.5px solid rgba(148, 163, 184, 0.55) !important;
        border-radius: 7px !important;
        transition: border-color .18s, box-shadow .18s !important;
    }}
    div[data-baseweb="textarea"] > div {{
        background: transparent !important;
        background-color: transparent !important;
    }}
    div[data-baseweb="textarea"]:focus-within {{
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59,130,246,0.15) !important;
        background: var(--surface-field-focus) !important;
        background-color: var(--surface-field-focus) !important;
    }}
    div[data-testid="stTextArea"] textarea,
    div[data-baseweb="textarea"] textarea {{
        background: var(--surface-field) !important;
        background-color: var(--surface-field) !important;
        color: var(--text) !important;
        -webkit-text-fill-color: var(--text) !important;
        font-size: 0.83rem !important;
        min-height: 58px !important;
        max-height: 80px !important;
        height: 58px !important;
        resize: none !important;
        border: none !important;
        box-shadow: none !important;
        padding: 7px 10px !important;
        line-height: 1.45 !important;
        caret-color: #3b82f6 !important;
    }}
    div[data-testid="stTextArea"] textarea::placeholder,
    div[data-baseweb="textarea"] textarea::placeholder {{
        color: #cbd5e1 !important;
        -webkit-text-fill-color: #cbd5e1 !important;
        opacity: 1 !important;
    }}

    /* ── SELECTBOX ────────────────────────────────────────── */
    div[data-baseweb="select"] > div:first-child {{
        background: var(--surface-field) !important;
        background-color: var(--surface-field) !important;
        border: 1.5px solid rgba(148, 163, 184, 0.55) !important;
        border-radius: 7px !important;
        min-height: 36px !important;
        height: 36px !important;
        transition: border-color .18s, box-shadow .18s !important;
    }}
    div[data-baseweb="select"] > div:first-child:focus-within,
    div[data-baseweb="select"] > div:first-child:hover {{
        background: var(--surface-field-focus) !important;
        background-color: var(--surface-field-focus) !important;
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59,130,246,0.15) !important;
    }}
    div[data-baseweb="select"] [class*="ValueContainer"] span,
    div[data-baseweb="select"] [class*="singleValue"],
    div[data-baseweb="select"] input,
    div[data-baseweb="select"] [role="combobox"] {{
        color: var(--text) !important;
        -webkit-text-fill-color: var(--text) !important;
        font-size: 0.83rem !important;
    }}
    div[data-baseweb="select"] > div,
    div[data-baseweb="select"] [class*="ValueContainer"] {{
        background: var(--surface-field) !important;
        background-color: var(--surface-field) !important;
    }}
    div[data-baseweb="select"]:focus-within > div:first-child,
    div[data-baseweb="select"] [class*="ControlContainer"],
    div[data-baseweb="select"] [class*="InputContainer"] {{
        background: #0f172a !important;
        background-color: #0f172a !important;
        color: #e2e8f0 !important;
        -webkit-text-fill-color: #e2e8f0 !important;
    }}
    div[data-baseweb="select"] [class*="placeholder"] {{
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-size: 0.83rem !important;
    }}
    /* dropdown list */
    ul[data-baseweb="menu"] {{
        background: #0f172a !important;
        background-color: #0f172a !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        padding: 4px !important;
        box-shadow: 0 8px 24px rgba(0,0,0,0.4) !important;
    }}
    ul[data-baseweb="menu"] li {{
        background: #0f172a !important;
        background-color: #0f172a !important;
        color: var(--text) !important;
        -webkit-text-fill-color: var(--text) !important;
        font-size: 0.82rem !important;
        border-radius: 5px !important;
        padding: 7px 10px !important;
    }}
    ul[data-baseweb="menu"] li *,
    div[role="listbox"] *,
    div[data-baseweb="popover"] * {{
        color: #f1f5f9 !important;
        -webkit-text-fill-color: #f1f5f9 !important;
    }}
    ul[data-baseweb="menu"] li:hover,
    ul[data-baseweb="menu"] li[aria-selected="true"] {{
        background: #1d4ed8 !important;
        background-color: #1d4ed8 !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }}
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] > div,
    div[data-baseweb="popover"] div,
    div[data-baseweb="popover"] [role="listbox"],
    div[role="listbox"],
    div[role="listbox"] > div,
    div[role="listbox"] div,
    div[role="option"],
    div[data-baseweb="menu"],
    div[data-baseweb="menu"] div,
    ul[data-baseweb="menu"] {{
        background: #0f172a !important;
        background-color: #0f172a !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }}
    div[data-baseweb="popover"] div[style*="overflow"],
    div[data-baseweb="popover"] div[style*="height"],
    div[data-baseweb="popover"] div[style*="position: relative"],
    div[role="listbox"] div[style*="overflow"],
    div[role="listbox"] div[style*="height"],
    div[role="listbox"] div[style*="position: relative"] {{
        background: #0f172a !important;
        background-color: #0f172a !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }}
    div[role="option"]:hover,
    div[role="option"][aria-selected="true"] {{
        background: #1d4ed8 !important;
        background-color: #1d4ed8 !important;
    }}

    /* ── BOTÕES ───────────────────────────────────────────── */
    .stButton > button {{
        background: linear-gradient(135deg, var(--primary-dark), var(--primary)) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 7px !important;
        padding: 0 14px !important;
        height: 32px !important;
        min-height: 32px !important;
        width: auto !important;
        font-size: 0.81rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.01em !important;
        cursor: pointer !important;
        transition: transform .12s ease, box-shadow .18s ease, background .15s ease !important;
        box-shadow: 0 2px 8px rgba(37,99,235,0.30) !important;
        white-space: nowrap !important;
    }}
    .stButton > button:hover {{
        background: linear-gradient(135deg, #1e40af, #1d4ed8) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 5px 14px rgba(37,99,235,0.42) !important;
    }}
    .stButton > button:active {{
        transform: scale(0.97) !important;
        box-shadow: 0 1px 4px rgba(37,99,235,0.2) !important;
    }}
    /* form submit = verde */
    div[data-testid="stFormSubmitButton"] > button {{
        background: linear-gradient(135deg, #059669, var(--success)) !important;
        box-shadow: 0 2px 8px rgba(16,185,129,0.30) !important;
        height: 32px !important;
        min-height: 32px !important;
        width: auto !important;
        min-width: 128px !important;
        padding: 0 16px !important;
        font-size: 0.80rem !important;
    }}
    div[data-testid="stFormSubmitButton"] > button:hover {{
        background: linear-gradient(135deg, #047857, #059669) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 5px 14px rgba(16,185,129,0.42) !important;
    }}

    /* ── CHECKBOX ─────────────────────────────────────────── */
    div[data-testid="stCheckbox"] label span {{ color: #94a3b8 !important; font-size: 0.82rem !important; }}

    /* ── SIDEBAR ──────────────────────────────────────────── */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #1e3a5f 0%, #0f2340 100%) !important;
        border-right: 1px solid rgba(255,255,255,0.06) !important;
    }}
    section[data-testid="stSidebar"] > div {{ padding: 0 8px 8px !important; }}
    section[data-testid="stSidebar"] * {{ color: #e2e8f0 !important; }}
    section[data-testid="stSidebar"] .stButton > button {{
        background: rgba(255,255,255,0.05) !important;
        color: #cbd5e1 !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 7px !important;
        font-size: 0.77rem !important;
        padding: 0 10px !important;
        height: 34px !important;
        width: 100% !important;
        box-shadow: none !important;
        text-align: left !important;
        transition: background .14s, border-color .14s, transform .1s !important;
        margin-bottom: 2px !important;
    }}
    section[data-testid="stSidebar"] .stButton > button:hover {{
        background: rgba(59,130,246,0.20) !important;
        border-color: rgba(59,130,246,0.5) !important;
        transform: translateX(3px) !important;
        box-shadow: none !important;
    }}

    /* ── MÉTRICAS ─────────────────────────────────────────── */
    [data-testid="metric-container"] {{
        background: rgba(239,246,255,0.96) !important;
        border: 1px solid rgba(15,47,95,0.22) !important;
        border-radius: 10px !important;
        padding: 12px 14px !important;
    }}
    [data-testid="metric-container"] label        {{ color: #0f2f5f !important; -webkit-text-fill-color: #0f2f5f !important; font-size: 0.84rem !important; text-transform: uppercase !important; letter-spacing:.04em !important; }}
    [data-testid="stMetricValue"]                  {{ color: #0f2f5f !important; font-size: 1.5rem !important; font-weight: 700 !important; }}
    [data-testid="stMetricDelta"] span             {{ font-size: 0.72rem !important; }}

    /* ── TABS ─────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {{ background: rgba(30,41,59,0.55) !important; border-radius: 8px !important; padding: 3px !important; gap: 2px !important; }}
    .stTabs [data-baseweb="tab"]      {{ color: #dbeafe !important; border-radius: 6px !important; padding: 6px 14px !important; font-size: 0.78rem !important; font-weight:600 !important; }}
    .stTabs [data-baseweb="tab"] > div {{ color: #dbeafe !important; -webkit-text-fill-color: #dbeafe !important; }}
    .stTabs [aria-selected="true"]    {{ background: #1d4ed8 !important; color: #fff !important; }}
    .stTabs [aria-selected="true"] > div {{ color: #fff !important; -webkit-text-fill-color: #fff !important; }}
    /* Conteudo dentro das tabs — reseta cor para padrao do tema */
    .stTabs [data-baseweb="tab-panel"] span,
    .stTabs [data-baseweb="tab-panel"] label {{ color: var(--text-muted) !important; -webkit-text-fill-color: var(--text-muted) !important; }}

    /* ── EXPANDERS ────────────────────────────────────────── */
    div[data-testid="stExpander"] summary {{
        background: rgba(30,41,59,0.65) !important;
        border-radius: 7px !important;
        padding: 8px 12px !important;
        color: #e2e8f0 !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
    }}
    div[data-testid="stExpander"] summary:hover {{ background: rgba(30,41,59,0.90) !important; }}

    /* ── DATAFRAME ────────────────────────────────────────── */
    /* ── ALERTAS ──────────────────────────────────────────── */
    div[data-testid="stAlert"]  {{
        background: rgba(15, 23, 42, 0.94) !important;
        border: 1px solid rgba(226, 232, 240, 0.18) !important;
        border-radius: 8px !important;
        color: #f8fafc !important;
        font-size: 0.82rem !important;
    }}
    div[data-testid="stAlert"] * {{
        color: #f8fafc !important;
        -webkit-text-fill-color: #f8fafc !important;
    }}
    div[data-testid="stSuccess"] {{ border-left: 3px solid #10b981 !important; }}
    div[data-testid="stError"]   {{ border-left: 3px solid #ef4444 !important; }}
    div[data-testid="stInfo"]    {{ border-left: 3px solid #3b82f6 !important; }}
    div[data-testid="stWarning"] {{ border-left: 3px solid #f59e0b !important; }}

    /* ── HR ───────────────────────────────────────────────── */
    hr {{ border-color: rgba(255,255,255,0.07) !important; margin: 16px 0 !important; }}

    /* ── CAPTION ──────────────────────────────────────────── */
    small, .stCaption {{ color: var(--text-subtle) !important; font-size: 0.70rem !important; }}

    /* ── DOWNLOAD BUTTON ──────────────────────────────────── */
    .stDownloadButton > button {{
        background: rgba(30,41,59,0.80) !important;
        color: #93c5fd !important;
        border: 1px solid rgba(59,130,246,0.35) !important;
        border-radius: 7px !important;
        font-size: 0.80rem !important;
        height: 34px !important;
        padding: 0 14px !important;
    }}
    .stDownloadButton > button:hover {{
        background: rgba(59,130,246,0.15) !important;
        border-color: #3b82f6 !important;
        transform: translateY(-1px) !important;
    }}

    /* ── TABELAS HTML (st.table) ─────────────────────────── */
    [data-testid="stTable"],
    [data-testid="stTable"] *,
    .stTable *,
    table, thead, tbody, tr, th, td {{
        color: #e2e8f0 !important;
        -webkit-text-fill-color: #e2e8f0 !important;
        background-color: #0f172a !important;
        border-color: rgba(148,163,184,0.20) !important;
    }}
    th {{
        color: #93c5fd !important;
        -webkit-text-fill-color: #93c5fd !important;
        background-color: #1e3a5f !important;
        font-weight: 700 !important;
        font-size: 0.78rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.04em !important;
    }}
    tr:hover td {{
        background-color: rgba(59,130,246,0.10) !important;
    }}
    .search-results-table {{
        width: 100%;
        max-height: 420px;
        overflow: auto;
        border: 1px solid rgba(148,163,184,0.28);
        border-radius: 8px;
        background: #0f172a;
    }}
    .search-results-table table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 0.78rem;
    }}
    .search-results-table th,
    .search-results-table td {{
        padding: 8px 10px;
        white-space: nowrap;
        color: #e2e8f0 !important;
        -webkit-text-fill-color: #e2e8f0 !important;
    }}
    .search-results-table th {{
        position: sticky;
        top: 0;
        z-index: 1;
        color: #bfdbfe !important;
        -webkit-text-fill-color: #bfdbfe !important;
        background: #1e3a5f !important;
    }}
    .search-results-table a.receipt-link {{
        color: #60a5fa !important;
        -webkit-text-fill-color: #60a5fa !important;
        font-weight: 700;
        text-decoration: underline;
        text-underline-offset: 2px;
    }}
    /* ── DATAFRAME (canvas/glide-data-grid) ─────────────── */
    /* ── HTML CUSTOMIZADO ─────────────────────────────────── */
    .login-spacer {{ height: 32px; }}
    .login-card {{
        background: rgba(15, 23, 42, 0.96);
        border: 1px solid rgba(255, 255, 255, 0.10);
        border-radius: 14px;
        padding: 26px 24px 24px;
        box-shadow: 0 24px 60px rgba(0, 0, 0, 0.60);
    }}
    .login-brand {{
        align-items: center;
        display: flex;
        flex-direction: column;
        justify-content: center;
        margin-bottom: 14px;
        text-align: center;
        width: 100%;
    }}
    .login-brand__icon {{
        align-items: center;
        display: flex;
        justify-content: center;
        min-height: 78px;
        text-align: center;
        width: 100%;
    }}
    .login-brand__logo {{
        border-radius: 8px;
        display: block;
        height: 154px;
        margin: 0 auto;
        max-width: 132px;
        object-fit: contain;
        width: auto;
    }}
    .login-brand__fallback {{ font-size: 2.6rem; line-height: 1; }}
    .login-brand__title {{
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-size: 1.45rem !important;
        font-weight: 700 !important;
        margin: 8px 0 2px !important;
        text-align: center !important;
        width: 100%;
    }}
    .login-brand__subtitle {{ color: #cbd5e1 !important; font-size: 0.78rem !important; margin: 0 !important; }}
    .login-label {{
        color: #f8fafc !important;
        font-size: 0.72rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.04em !important;
        text-transform: uppercase !important;
        margin: 12px 0 4px !important;
    }}
    .login-field-gap {{ height: 8px; }}
    .login-version {{
        bottom: 18px;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        left: 0;
        margin: 0 !important;
        position: fixed;
        right: 0;
        text-align: center;
        width: 100%;
    }}
    .sidebar-brand {{
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        margin-bottom: 8px;
        padding: 16px 4px 10px;
        text-align: center;
    }}
    .sidebar-brand__icon {{
        align-items: center;
        display: flex;
        justify-content: center;
        min-height: 75px;
    }}
    .sidebar-brand__logo {{
        border-radius: 6px;
        display: block;
        height: 75px;
        max-width: 120px;
        object-fit: contain;
        width: auto;
    }}
    .sidebar-brand__fallback {{ font-size: 1.6rem; line-height: 1; }}
    .sidebar-brand__title {{ color: var(--text) !important; font-size: 1rem !important; font-weight: 700 !important; margin: 5px 0 2px; }}
    .sidebar-brand__subtitle {{ color: #cbd5e1 !important; font-size: 0.68rem !important; }}
    .sidebar-brand__user {{ color: #e2e8f0 !important; font-size: 0.65rem !important; margin-top: 6px; }}
    .receipt-frame {{
        background: #fff;
        border: 1px solid #334155;
        border-radius: 8px;
        min-height: 620px;
        width: 100%;
    }}

    /* ── OVERRIDE FINAL: CORES POR FUNÇÃO ─────────────────── */
    h1, h2, h3,
    [data-testid="stHeading"],
    [data-testid="stHeading"] * {{
        color: var(--title-blue) !important;
        -webkit-text-fill-color: var(--title-blue) !important;
    }}
    .login-brand__title {{
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        display: block !important;
        margin-left: auto !important;
        margin-right: auto !important;
        text-align: center !important;
        width: 100% !important;
    }}
    [data-testid="stMarkdownContainer"],
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] span,
    [data-testid="stMarkdownContainer"] strong,
    [data-testid="stMarkdownContainer"] em {{
        color: var(--text-muted) !important;
        -webkit-text-fill-color: var(--text-muted) !important;
    }}
    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input,
    div[data-testid="stTextArea"] textarea,
    div[data-baseweb="input"] input,
    div[data-baseweb="textarea"] textarea,
    div[data-baseweb="select"] input,
    div[data-baseweb="select"] [role="combobox"],
    div[data-baseweb="select"] [class*="singleValue"],
    div[data-baseweb="select"] [class*="ValueContainer"] span,
    ul[data-baseweb="menu"] li,
    ul[data-baseweb="menu"] li *,
    ul[data-baseweb="menu"] div,
    div[data-baseweb="menu"] *,
    div[data-baseweb="popover"] *,
    div[role="listbox"],
    div[role="listbox"] *,
    div[role="option"],
    div[role="option"] * {{
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }}
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] *,
    div[data-baseweb="menu"],
    div[data-baseweb="menu"] *,
    ul[data-baseweb="menu"],
    ul[data-baseweb="menu"] *,
    div[role="listbox"],
    div[role="listbox"] *,
    div[role="option"],
    div[role="option"] * {{
        background-color: #0f172a !important;
    }}
    div[role="option"]:hover,
    div[role="option"][aria-selected="true"],
    ul[data-baseweb="menu"] li:hover,
    ul[data-baseweb="menu"] li[aria-selected="true"] {{
        background-color: #1d4ed8 !important;
    }}
    div[data-testid="stTextInput"] input::placeholder,
    div[data-testid="stNumberInput"] input::placeholder,
    div[data-testid="stTextArea"] textarea::placeholder,
    div[data-baseweb="input"] input::placeholder,
    div[data-baseweb="textarea"] textarea::placeholder {{
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        opacity: 1 !important;
    }}
    svg,
    svg * {{
        -webkit-text-fill-color: initial !important;
    }}
    [data-testid="metric-container"] {{
        background: linear-gradient(180deg, rgba(239, 246, 255, 0.98), rgba(219, 234, 254, 0.96)) !important;
        border: 1px solid rgba(15, 47, 95, 0.22) !important;
        border-radius: 10px !important;
        box-shadow: 0 10px 28px rgba(15, 47, 95, 0.18) !important;
        min-height: 92px !important;
        padding: 14px 16px !important;
    }}
    [data-testid="metric-container"] *,
    [data-testid="metric-container"] label,
    [data-testid="stMetricValue"],
    [data-testid="stMetricValue"] *,
    [data-testid="stMetricDelta"],
    [data-testid="stMetricDelta"] * {{
        color: #0f2f5f !important;
        -webkit-text-fill-color: #0f2f5f !important;
    }}
    [data-testid="stMetricValue"] {{
        font-size: 1.65rem !important;
        font-weight: 800 !important;
        line-height: 1.1 !important;
    }}
    [data-testid="metric-container"] label {{
        color: #0f2f5f !important;
        -webkit-text-fill-color: #0f2f5f !important;
        font-size: 0.86rem !important;
        font-weight: 800 !important;
        opacity: 1 !important;
    }}
    [data-testid="stVegaLiteChart"],
    [data-testid="stArrowVegaLiteChart"],
    [data-testid="stPlotlyChart"] {{
        background: rgba(15, 23, 42, 0.92) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 10px !important;
        padding: 8px !important;
    }}
    .dash-metric-card {{
        background: linear-gradient(180deg, rgba(239, 246, 255, 0.98), rgba(219, 234, 254, 0.96));
        border: 1px solid rgba(15, 47, 95, 0.22);
        border-radius: 10px;
        box-shadow: 0 10px 28px rgba(15, 47, 95, 0.18);
        min-height: 96px;
        padding: 14px 12px;
    }}
    .dash-metric-label {{
        color: #0f2f5f !important;
        -webkit-text-fill-color: #0f2f5f !important;
        font-size: 1.02rem !important;
        font-weight: 900 !important;
        line-height: 1.18;
        margin: 0 0 10px !important;
    }}
    .dash-metric-value {{
        color: #0f2f5f !important;
        -webkit-text-fill-color: #0f2f5f !important;
        font-size: 1.85rem !important;
        font-weight: 900 !important;
        line-height: 1;
        margin: 0 !important;
    }}
    .dash-metric-delta {{
        color: #0f2f5f !important;
        -webkit-text-fill-color: #0f2f5f !important;
        font-size: 0.95rem !important;
        font-weight: 800 !important;
        margin: 8px 0 0 !important;
    }}
    [data-testid="stMarkdownContainer"] .dash-metric-card,
    [data-testid="stMarkdownContainer"] .dash-metric-card *,
    [data-testid="stMarkdownContainer"] .dash-metric-label,
    [data-testid="stMarkdownContainer"] .dash-metric-value,
    [data-testid="stMarkdownContainer"] .dash-metric-delta {{
        color: #0f2f5f !important;
        -webkit-text-fill-color: #0f2f5f !important;
    }}
    .dash-bars {{
        display: grid;
        gap: 10px;
        background: rgba(15, 23, 42, 0.78);
        border: 1px solid rgba(191, 219, 254, 0.18);
        border-radius: 10px;
        padding: 14px;
    }}
    .dash-bar-row {{
        display: grid;
        grid-template-columns: minmax(160px, 260px) 1fr 54px;
        align-items: center;
        gap: 12px;
    }}
    .dash-bar-label {{
        color: #f8fafc !important;
        -webkit-text-fill-color: #f8fafc !important;
        font-size: 0.78rem !important;
        font-weight: 800 !important;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }}
    .dash-bar-track {{
        height: 13px;
        background: rgba(226, 232, 240, 0.16);
        border-radius: 999px;
        overflow: hidden;
        border: 1px solid rgba(226, 232, 240, 0.12);
    }}
    .dash-bar-fill {{
        height: 100%;
        border-radius: 999px;
        background: linear-gradient(90deg, #38bdf8, #2563eb);
    }}
    .dash-bar-value {{
        color: #bfdbfe !important;
        -webkit-text-fill-color: #bfdbfe !important;
        font-size: 0.82rem !important;
        font-weight: 900 !important;
        text-align: right;
    }}
    @media (max-width: 900px) {{
        .dash-bar-row {{
            grid-template-columns: 1fr 44px;
            gap: 8px;
        }}
        .dash-bar-label {{
            grid-column: 1 / -1;
        }}
    }}

    /* Multiselect tags (filtros de busca) */
    div[data-baseweb="tag"] {{
        background: rgba(37,99,235,0.35) !important;
        border: 1px solid rgba(59,130,246,0.50) !important;
        border-radius: 5px !important;
    }}
    div[data-baseweb="tag"] span {{
        color: #bfdbfe !important;
        -webkit-text-fill-color: #bfdbfe !important;
        font-size: 0.78rem !important;
    }}
    div[data-baseweb="tag"] button svg {{
        fill: #93c5fd !important;
    }}

    /* FINAL FORM FIELD CONTRAST OVERRIDE */
    div[data-baseweb="input"],
    div[data-baseweb="textarea"],
    div[data-baseweb="select"] > div:first-child {{
        background: #f8fafc !important;
        background-color: #f8fafc !important;
        border: 1.5px solid #94a3b8 !important;
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        color-scheme: light !important;
        opacity: 1 !important;
    }}
    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="textarea"]:focus-within,
    div[data-baseweb="select"] > div:first-child:focus-within,
    div[data-baseweb="select"] > div:first-child:hover {{
        background: #ffffff !important;
        background-color: #ffffff !important;
        border-color: #2563eb !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.20) !important;
    }}
    div[data-baseweb="input"] *,
    div[data-baseweb="textarea"] *,
    div[data-baseweb="select"] > div:first-child *,
    div[data-baseweb="select"] [class*="ValueContainer"],
    div[data-baseweb="select"] [class*="ControlContainer"],
    div[data-baseweb="select"] [class*="InputContainer"] {{
        background-color: transparent !important;
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        opacity: 1 !important;
    }}
    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input,
    div[data-testid="stTextArea"] textarea,
    div[data-baseweb="input"] input,
    div[data-baseweb="textarea"] textarea,
    div[data-baseweb="select"] input,
    div[data-baseweb="select"] [role="combobox"],
    div[data-baseweb="select"] [class*="singleValue"],
    div[data-baseweb="select"] [class*="SingleValue"],
    div[data-baseweb="select"] [class*="ValueContainer"] span {{
        background: transparent !important;
        background-color: transparent !important;
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        opacity: 1 !important;
    }}
    div[data-testid="stTextInput"] input::placeholder,
    div[data-testid="stNumberInput"] input::placeholder,
    div[data-testid="stTextArea"] textarea::placeholder,
    div[data-baseweb="input"] input::placeholder,
    div[data-baseweb="textarea"] textarea::placeholder {{
        color: #475569 !important;
        -webkit-text-fill-color: #475569 !important;
        opacity: 1 !important;
    }}
    div[data-baseweb="select"] [class*="placeholder"],
    div[data-baseweb="select"] [class*="Placeholder"] {{
        color: #475569 !important;
        -webkit-text-fill-color: #475569 !important;
        opacity: 1 !important;
    }}
    div[data-baseweb="select"] [aria-disabled="true"],
    div[data-baseweb="input"] [aria-disabled="true"],
    div[data-baseweb="textarea"] [aria-disabled="true"],
    input:disabled,
    textarea:disabled {{
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        opacity: 1 !important;
    }}
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] > div,
    div[data-baseweb="menu"],
    ul[data-baseweb="menu"],
    div[role="listbox"] {{
        background: #f8fafc !important;
        background-color: #f8fafc !important;
        border-color: #94a3b8 !important;
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        color-scheme: light !important;
    }}
    ul[data-baseweb="menu"] li,
    div[role="option"] {{
        background: #f8fafc !important;
        background-color: #f8fafc !important;
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        opacity: 1 !important;
    }}
    ul[data-baseweb="menu"] li *,
    div[role="option"] * {{
        background: transparent !important;
        background-color: transparent !important;
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        opacity: 1 !important;
    }}
    ul[data-baseweb="menu"] li:hover,
    ul[data-baseweb="menu"] li[aria-selected="true"],
    div[role="option"]:hover,
    div[role="option"][aria-selected="true"] {{
        background: #2563eb !important;
        background-color: #2563eb !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }}
    ul[data-baseweb="menu"] li:hover *,
    ul[data-baseweb="menu"] li[aria-selected="true"] *,
    div[role="option"]:hover *,
    div[role="option"][aria-selected="true"] * {{
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }}
    div[data-baseweb="tag"] {{
        background: #dbeafe !important;
        border-color: #93c5fd !important;
    }}
    div[data-baseweb="tag"] span {{
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
    }}

    @media (max-width: 900px) {{
        .main .block-container {{
            border-radius: 0;
            padding: 16px 14px 24px !important;
        }}
        h1 {{ font-size: 1.22rem !important; }}
        .stTabs [data-baseweb="tab-list"] {{ overflow-x: auto !important; }}
        .login-card {{ padding: 24px 20px 22px; }}
    }}
    </style>
    """, unsafe_allow_html=True)

inject_css()

# Layout de celular sem depender das larguras calculadas pelo Streamlit no desktop.
st.markdown("""
<style>
.st-key-login_panel { width: 100%; max-width: 480px; margin-inline: auto; }
[data-testid="stColumn"], [data-testid="stVerticalBlock"] { min-width: 0; }
.search-results-table { max-width: 100%; overscroll-behavior-x: contain; }
@media (max-width: 768px) {
    [data-testid="stMainBlockContainer"], .main .block-container {
        padding: 3.5rem 0.75rem 1.5rem !important;
        max-width: 100% !important;
        box-sizing: border-box;
        backdrop-filter: none !important;
    }
    [data-testid="stAppViewContainer"] {
        background-attachment: scroll !important;
    }
    [data-testid="stHorizontalBlock"] {
        flex-direction: column !important;
        gap: 0.75rem !important;
    }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        width: 100% !important;
        min-width: 0 !important;
        flex: 1 1 auto !important;
    }
    [data-testid="stSidebar"] {
        min-width: 0 !important;
        max-width: 88vw !important;
    }
    [data-testid="stSidebarCollapsedControl"] button,
    [data-testid="stSidebarCollapseButton"] button {
        min-height: 44px !important;
        min-width: 44px !important;
    }
    input, textarea, [data-baseweb="select"] input {
        font-size: 16px !important;
    }
    [data-testid="stButton"] button,
    [data-testid="stFormSubmitButton"] button,
    [data-testid="stDownloadButton"] button {
        min-height: 44px !important;
        min-width: 0 !important;
        width: 100% !important;
        white-space: normal !important;
    }
    h1 { font-size: 1.25rem !important; overflow-wrap: anywhere; }
    h2, h3 { overflow-wrap: anywhere; }
    .login-spacer { height: 0.5rem !important; min-height: 0 !important; }
    .st-key-login_panel { max-width: 100%; }
    .search-results-table {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
    }
    .search-results-table th, .search-results-table td {
        padding: 10px 8px;
        font-size: 0.8rem;
    }
    .stTabs [data-baseweb="tab-list"] { overflow-x: auto !important; }
    .stTabs [data-baseweb="tab"] { flex-shrink: 0; min-height: 44px; }
    .dash-bar-row { grid-template-columns: minmax(0, 1fr) 44px; }
    .receipt-frame { max-width: 100%; height: 70vh; min-height: 400px; }
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# BANCO DE DADOS
# ═══════════════════════════════════════════════════════════════════════════════
APP_DIR = Path(__file__).resolve().parent
RECIBO_SEQ_BASE = 2002

def inicializar_banco():
    if not cloud_db.setting("TEST_DATABASE_URL"):
        st.info("Cópia de teste preparada. Configure o banco de teste nos Secrets para começar.")
        st.stop()
    try:
        cloud_db.initialize()
    except Exception as exc:
        st.error(cloud_db.initialization_diagnostic(exc))
        st.stop()

def proximo_recibo(conn=None):
    fechar_conn = conn is None
    if fechar_conn:
        conn = get_conn()
    seq = conn.execute(
        "UPDATE seq_recibo SET valor=CASE WHEN valor<? THEN ? ELSE valor END + 1 WHERE id=1 RETURNING valor",
        (RECIBO_SEQ_BASE, RECIBO_SEQ_BASE),
    ).fetchone()[0]
    if fechar_conn:
        conn.commit(); conn.close()
    return seq

def formatar_num_recibo(seq: int) -> str:
    return f"{seq:03d}/07/{datetime.now().year}"

def registrar_log(usuario, acao):
    conn = get_conn()
    conn.execute("INSERT INTO logs_sistema(usuario,acao,data) VALUES(?,?,?)",
                 (usuario, acao, datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
    conn.commit(); conn.close()

inicializar_banco()

# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
LOGIN_MAX_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 300
SESSION_TIMEOUT_SECONDS = 15 * 60
USERNAME_RE = re.compile(r"^[A-Za-z0-9_.@-]{3,32}$")

def is_admin():
    return st.session_state.get("perfil") == "Administrador"

def usuario_valido(usuario):
    return bool(USERNAME_RE.fullmatch((usuario or "").strip()))

def senha_forte(senha):
    senha = senha or ""
    return (
        len(senha) >= 8
        and any(ch.isalpha() for ch in senha)
        and any(ch.isdigit() for ch in senha)
    )

def verificar_senha_bcrypt(senha, hash_senha):
    try:
        return bool(hash_senha) and bcrypt.checkpw(senha.encode(), hash_senha.encode())
    except (TypeError, ValueError):
        return False

def segundos_bloqueio_login():
    return max(0, int(st.session_state.get("login_lock_until", 0) - time.time()))

def registrar_falha_login(usuario=""):
    st.session_state["login_failed_attempts"] = st.session_state.get("login_failed_attempts", 0) + 1
    if st.session_state["login_failed_attempts"] >= LOGIN_MAX_ATTEMPTS:
        st.session_state["login_lock_until"] = time.time() + LOGIN_LOCKOUT_SECONDS
        registrar_log(usuario or "login", "Bloqueio temporario por tentativas invalidas")

def limpar_falhas_login():
    st.session_state["login_failed_attempts"] = 0
    st.session_state["login_lock_until"] = 0

def encerrar_sessao(motivo=""):
    usuario = st.session_state.get("usuario") or "sistema"
    if motivo:
        registrar_log(usuario, motivo)
    st.session_state["autenticado"] = False
    st.session_state["usuario"] = ""
    st.session_state["perfil"] = ""
    st.session_state["carrinho"] = []
    st.session_state["entradas_temp"] = []
    st.session_state["ultimo_recibo_html"] = ""
    st.session_state["ultimo_recibo_num"] = ""
    st.session_state["last_activity_at"] = 0

def verificar_expiracao_sessao():
    if not st.session_state.get("autenticado"):
        return
    agora = time.time()
    ultimo = st.session_state.get("last_activity_at") or agora
    if agora - ultimo > SESSION_TIMEOUT_SECONDS:
        st.session_state["sessao_expirada"] = True
        encerrar_sessao("Sessao expirada por inatividade")
        st.rerun()
    st.session_state["last_activity_at"] = agora

def injetar_timer_inatividade():
    timeout_ms = SESSION_TIMEOUT_SECONDS * 1000
    components.html(
        f"""
        <script>
        (function() {{
          const timeout = {timeout_ms};
          let timer;
          function reloadParent() {{
            try {{ window.parent.location.reload(); }}
            catch (e) {{ window.location.reload(); }}
          }}
          function resetTimer() {{
            clearTimeout(timer);
            timer = setTimeout(reloadParent, timeout + 1000);
          }}
          try {{
            ['click','keydown','mousemove','scroll','touchstart'].forEach(function(evt) {{
              window.parent.document.addEventListener(evt, resetTimer, true);
            }});
          }} catch (e) {{}}
          resetTimer();
        }})();
        </script>
        """,
        height=0,
        width=0,
    )

def possui_movimentacao_entidade(nome):
    conn = get_conn()
    total = conn.execute(
        "SELECT COUNT(*) FROM historico WHERE entidade=?",
        ((nome or "").strip().upper(),),
    ).fetchone()[0]
    conn.close()
    return total > 0

def listar_orgaos():
    conn = get_conn()
    rows = conn.execute("SELECT nome FROM orgaos ORDER BY nome").fetchall()
    conn.close()
    return [r[0] for r in rows]

def material_identificador_duplicado(campo, valor, ignorar_id=None):
    colunas = {
        "patrimonio": ("patrimonio", "Patrimônio"),
        "num_serie": ("num_serie", "Nº Série"),
        "imei": ("imei", "IMEI"),
        "numero_linha": ("numero_linha", "Número da linha"),
        "imei_chip": ("imei_chip", "IMEI do chip"),
    }
    valor = (valor or "").strip().upper()
    if not valor or campo not in colunas:
        return None
    coluna, rotulo = colunas[campo]
    params = [valor]
    filtro_id = ""
    if ignorar_id is not None:
        filtro_id = " AND id<>?"
        params.append(ignorar_id)
    conn = get_conn()
    row = conn.execute(
        f"SELECT id,nome FROM materiais WHERE UPPER({coluna})=? AND TRIM(COALESCE({coluna},''))<>''{filtro_id} LIMIT 1",
        params,
    ).fetchone()
    conn.close()
    if row:
        return f"⚠️ {rotulo} **{valor}** já cadastrado — Material: **{row[1]}** (ID {row[0]})."
    return None

def validar_identificadores_material(dados, ignorar_id=None):
    for campo in ("patrimonio", "num_serie", "imei", "numero_linha", "imei_chip"):
        erro = material_identificador_duplicado(campo, dados.get(campo), ignorar_id)
        if erro:
            return erro
    return None

def material_tem_identificador_unico(dados):
    return any((dados.get(campo) or "").strip() for campo in ("patri", "serial", "imei", "numero_linha", "imei_chip"))

def localizar_material_generico_entrada(conn, item):
    return conn.execute(
        """
        SELECT id
          FROM materiais
         WHERE UPPER(TRIM(COALESCE(nome,'')))=?
           AND UPPER(TRIM(COALESCE(marca,'')))=?
           AND UPPER(TRIM(COALESCE(modelo,'')))=?
           AND TRIM(COALESCE(patrimonio,''))=''
           AND TRIM(COALESCE(num_serie,''))=''
           AND TRIM(COALESCE(imei,''))=''
           AND TRIM(COALESCE(numero_linha,''))=''
           AND TRIM(COALESCE(imei_chip,''))=''
         ORDER BY COALESCE(entrada_registrada,0) DESC, quantidade DESC, id
         LIMIT 1
        """,
        (
            (item.get("nome") or "").strip().upper(),
            (item.get("marca") or "").strip().upper(),
            (item.get("modelo") or "").strip().upper(),
        ),
    ).fetchone()

def patrimonio_serie_para_exibicao(patrimonio, serie, identificacao="", material_ref=None):
    patrimonio = (patrimonio or "").strip()
    serie = (serie or "").strip()
    ident = (identificacao or "").strip()
    if material_ref:
        patrimonio = patrimonio or (material_ref[2] or "").strip()
        serie = serie or (material_ref[3] or "").strip()

    genericos = {"", "-", "—", "â€”", "MARCA/MODELO", "LOTE"}
    ident_util = ident if ident.upper() not in genericos else ""
    if ident_util and not patrimonio:
        ids_material = set()
        if material_ref:
            ids_material = {
                (material_ref[idx] or "").strip().upper()
                for idx in (2, 3, 4, 6, 7)
                if len(material_ref) > idx and (material_ref[idx] or "").strip()
            }
        if ident_util.upper() not in ids_material:
            patrimonio = ident_util
    return patrimonio, serie

def localizar_material_historico(conn, material_id, material, marca, modelo, identificacao):
    if material_id:
        row = conn.execute(
            "SELECT id,nome,patrimonio,num_serie,imei,prefixo_viatura,numero_linha,imei_chip FROM materiais WHERE id=?",
            (material_id,),
        ).fetchone()
        if row:
            return row

    ident = (identificacao or "").strip().upper()
    genericos = {"", "-", "—", "MARCA/MODELO", "LOTE"}
    if ident not in genericos:
        row = conn.execute(
            "SELECT id,nome,patrimonio,num_serie,imei,prefixo_viatura,numero_linha,imei_chip FROM materiais "
            "WHERE UPPER(COALESCE(patrimonio,''))=? "
            "OR UPPER(COALESCE(num_serie,''))=? "
            "OR UPPER(COALESCE(imei,''))=? "
            "OR UPPER(COALESCE(prefixo_viatura,''))=? "
            "OR UPPER(COALESCE(numero_linha,''))=? "
            "OR UPPER(COALESCE(imei_chip,''))=? "
            "ORDER BY COALESCE(entrada_registrada,0) DESC, id LIMIT 1",
            (ident, ident, ident, ident, ident, ident),
        ).fetchone()
        if row:
            return row

    return conn.execute(
        "SELECT id,nome,patrimonio,num_serie,imei,prefixo_viatura,numero_linha,imei_chip FROM materiais "
        "WHERE UPPER(COALESCE(nome,''))=? "
        "AND UPPER(COALESCE(marca,''))=? "
        "AND UPPER(COALESCE(modelo,''))=? "
        "ORDER BY CASE WHEN quantidade=0 THEN 0 ELSE 1 END, id LIMIT 1",
        ((material or "").strip().upper(), (marca or "").strip().upper(), (modelo or "").strip().upper()),
    ).fetchone()

def rotulo_material_identificado(row, quantidade=None):
    if not row:
        return ""
    partes = [row[1] or ""]
    detalhes = []
    if len(row) > 2 and row[2]:
        detalhes.append(f"Patrimonio: {row[2]}")
    if len(row) > 3 and row[3]:
        detalhes.append(f"Serie: {row[3]}")
    if len(row) > 4 and row[4]:
        detalhes.append(f"IMEI: {row[4]}")
    if len(row) > 5 and row[5]:
        detalhes.append(f"Cod barras: {row[5]}")
    if detalhes:
        partes.append(" | ".join(detalhes))
    if quantidade is not None:
        partes.append(f"Qtd: {quantidade}")
    return " | ".join(partes)

def gerar_html_recibo_saida(num_recibo):
    conn = get_conn()
    rows = conn.execute(
        "SELECT h.material,h.marca,h.modelo,h.quantidade,h.identificacao,h.observacoes,h.entidade,"
        "h.material_id,m.patrimonio,m.num_serie "
        "FROM historico h LEFT JOIN materiais m ON m.id=h.material_id "
        "WHERE h.tipo='SAÍDA (CLIENTE)' AND h.num_recibo=? ORDER BY h.id",
        (num_recibo,),
    ).fetchall()
    if not rows:
        conn.close()
        return ""

    itens = []
    genericos = {"", "-", "—", "â€”", "MARCA/MODELO", "LOTE"}
    for r in rows:
        ident = (r[4] or "").strip()
        ident_util = ident if ident.upper() not in genericos else ""
        material_ref = localizar_material_historico(conn, r[7], r[0], r[1], r[2], ident_util)
        patrimonio, serie = patrimonio_serie_para_exibicao(r[8], r[9], ident_util, material_ref)
        itens.append({
            "nome": r[0],
            "marca": r[1] or "",
            "modelo": r[2] or "",
            "quantidade": r[3],
            "patrimonio": patrimonio,
            "num_serie": serie,
        })
    conn.close()
    return html_recibo(itens, rows[0][6], "SAÍDA (CLIENTE)", num_recibo, rows[0][5] or "")

def limpar_dados_cadastro(opcoes):
    tabelas = {
        "Materiais": "materiais",
        "Clientes": "clientes",
        "Fornecedores": "fornecedores",
    }
    selecionadas = list(dict.fromkeys(tabelas[o] for o in opcoes if o in tabelas))
    limpar_todas_movimentacoes = "Movimentações" in opcoes
    tipos_movimentacao = []
    if "Entradas" in opcoes:
        tipos_movimentacao.append("ENTRADA (FORNECEDOR)")
    if "Saídas" in opcoes:
        tipos_movimentacao.append("SAÍDA (CLIENTE)")

    if not selecionadas and not limpar_todas_movimentacoes and not tipos_movimentacao:
        return 0

    conn = get_conn()
    total = 0
    try:
        for tabela in selecionadas:
            total += conn.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]
            conn.execute(f"DELETE FROM {tabela}")
        if limpar_todas_movimentacoes:
            total += conn.execute("SELECT COUNT(*) FROM historico").fetchone()[0]
            conn.execute("DELETE FROM historico")
            conn.execute("UPDATE seq_recibo SET valor=? WHERE id=1", (RECIBO_SEQ_BASE,))
        elif tipos_movimentacao:
            placeholders = ",".join("?" for _ in tipos_movimentacao)
            total += conn.execute(
                f"SELECT COUNT(*) FROM historico WHERE tipo IN ({placeholders})",
                tipos_movimentacao,
            ).fetchone()[0]
            conn.execute(
                f"DELETE FROM historico WHERE tipo IN ({placeholders})",
                tipos_movimentacao,
            )
            if "SAÍDA (CLIENTE)" in tipos_movimentacao:
                seq_atual = conn.execute(
                    "SELECT COALESCE(MAX(seq_recibo),0) FROM historico WHERE tipo='SAÍDA (CLIENTE)'"
                ).fetchone()[0]
                seq_atual = max(seq_atual, RECIBO_SEQ_BASE)
                conn.execute("UPDATE seq_recibo SET valor=? WHERE id=1", (seq_atual,))
        conn.commit()
        return total
    finally:
        conn.close()

def solicitar_cadastro_usuario(usuario, senha):
    usuario = (usuario or "").strip()
    if not usuario or not senha:
        return False, "Preencha usuario e senha."
    if not usuario_valido(usuario):
        return False, "Usuario deve ter 3 a 32 caracteres e usar apenas letras, numeros, ponto, hifen, sublinhado ou @."
    if not senha_forte(senha):
        return False, "Senha deve ter no minimo 8 caracteres, incluindo letras e numeros."

    h = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
    conn = get_conn()
    try:
        existe = conn.execute("SELECT 1 FROM usuarios WHERE usuario=?", (usuario,)).fetchone()
        if existe:
            return False, "Este usuario ja existe."
        conn.execute(
            "INSERT INTO solicitacoes_usuarios(usuario,senha,data) VALUES(?,?,?)",
            (usuario, h, datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
        )
        conn.commit()
        return True, "Solicitacao enviada. Aguarde validacao do administrador."
    except psycopg.IntegrityError:
        return False, "Ja existe uma solicitacao pendente para este usuario."
    finally:
        conn.close()


def solicitar_redefinicao_senha(usuario, senha):
    usuario = (usuario or "").strip()
    if not usuario or not senha:
        return False, "Preencha usuario e nova senha."
    if not usuario_valido(usuario):
        return False, "Usuario deve ter 3 a 32 caracteres e usar apenas letras, numeros, ponto, hifen, sublinhado ou @."
    if not senha_forte(senha):
        return False, "Senha deve ter no minimo 8 caracteres, incluindo letras e numeros."

    h = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
    conn = get_conn()
    try:
        existe = conn.execute("SELECT 1 FROM usuarios WHERE usuario=?", (usuario,)).fetchone()
        if not existe:
            return False, "Usuario nao encontrado. Verifique o nome de usuario ou solicite novo acesso."
        conn.execute(
            """
            INSERT INTO solicitacoes_senha(usuario,senha,data) VALUES(?,?,?)
            ON CONFLICT(usuario) DO UPDATE SET senha=excluded.senha, data=excluded.data
            """,
            (usuario, h, datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
        )
        conn.commit()
        return True, "Pedido de redefinicao enviado. Aguarde um administrador aprovar."
    finally:
        conn.close()

def gerar_excel(df):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        df.to_excel(w, index=False)
    return out.getvalue()

def texto_pdf(valor):
    if pd.isna(valor):
        return ""
    return str(valor).encode("latin-1", "replace").decode("latin-1")

def gerar_pdf_relatorio(df, titulo="Relatorio"):
    out = io.BytesIO()
    doc = SimpleDocTemplate(
        out,
        pagesize=landscape(A4),
        leftMargin=0.8 * cm,
        rightMargin=0.8 * cm,
        topMargin=0.8 * cm,
        bottomMargin=0.8 * cm,
    )
    styles = getSampleStyleSheet()
    elems = [
        Paragraph(texto_pdf(titulo), styles["Title"]),
        Paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles["Normal"]),
        Spacer(1, 0.25 * cm),
    ]

    df_pdf = df.copy().fillna("")
    max_cols = max(1, len(df_pdf.columns))
    data = [[texto_pdf(c) for c in df_pdf.columns]]
    for _, row in df_pdf.iterrows():
        data.append([texto_pdf(v)[:120] for v in row.tolist()])

    page_width = landscape(A4)[0] - (1.6 * cm)
    col_widths = [page_width / max_cols] * max_cols
    tabela = Table(data, repeatRows=1, colWidths=col_widths)
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a6b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]))
    elems.append(tabela)
    doc.build(elems)
    return out.getvalue()

def imagem_para_data_url(uploaded_file):
    mime = uploaded_file.type or "image/png"
    enc = base64.b64encode(uploaded_file.getvalue()).decode()
    return f"data:{mime};base64,{enc}"

def imagem_local_para_data_url(nome_arquivo):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, nome_arquivo)
    if not os.path.exists(path):
        return ""
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext or 'png'}"
    with open(path, "rb") as f:
        enc = base64.b64encode(f.read()).decode()
    return f"data:{mime};base64,{enc}"

def salvar_brasao_recibo(uploaded_file):
    content = uploaded_file.getvalue()
    digest = hashlib.sha256(content).hexdigest()
    if st.session_state.get("brasao_upload_digest") == digest:
        return "imagem do ambiente de teste"
    mime = uploaded_file.type or "image/png"
    data_url = "data:" + mime + ";base64," + base64.b64encode(content).decode()
    cloud_db.save_setting("brasao_recibo", data_url)
    st.session_state["brasao_upload_digest"] = digest
    st.session_state["brasao_recibo"] = data_url
    return "imagem do ambiente de teste"

def brasao_recibo_data_url():
    saved = cloud_db.load_setting("brasao_recibo")
    if saved is not None:
        return saved or BRASAO_URL
    for nome in ("brasao_recibo.png", "brasao_recibo.jpg"):
        data_url = imagem_local_para_data_url(nome)
        if data_url:
            return data_url
    return BRASAO_URL

def remover_brasao_recibo():
    cloud_db.save_setting("brasao_recibo", "")
    st.session_state["brasao_recibo"] = ""

# helper: campo de busca padronizado [input 4fr | botão 1fr]
def search_row(label, key, btn_key, session_key, placeholder="Buscar...", buscar_apenas_ao_clicar=False):
    """Retorna o termo atual do campo de busca."""
    if session_key not in st.session_state:
        st.session_state[session_key] = ""
    if key not in st.session_state:
        st.session_state[key] = st.session_state.get(session_key, "")

    def limpar_busca():
        st.session_state[session_key] = ""
        st.session_state[key] = ""

    c1, c2, c3 = st.columns([5, 1, 1])
    val = c1.text_input(label, placeholder=placeholder, key=key, label_visibility="collapsed")
    buscar = c2.button("🔍 Buscar", key=btn_key, use_container_width=True)
    c3.button("Limpar", key=f"{btn_key}_limpar", use_container_width=True, on_click=limpar_busca)
    termo = val.strip()
    if buscar or (not buscar_apenas_ao_clicar and termo != st.session_state.get(session_key, "")):
        st.session_state[session_key] = termo
    return st.session_state.get(session_key, termo)

def tabela_visivel(df, empty_msg="Nenhum registro encontrado."):
    if df.empty:
        st.info(empty_msg)
        return
    df = df.fillna("")
    st.markdown(
        f"<div class='search-results-table'>{df.to_html(index=False, escape=True)}</div>",
        unsafe_allow_html=True,
    )

def grafico_barras_horizontal(df, label_col, value_col, empty_msg="Sem dados."):
    if df.empty:
        st.info(empty_msg)
        return
    max_val = int(df[value_col].fillna(0).max()) or 1
    linhas = []
    for _, row in df.iterrows():
        valor = int(row[value_col]) if pd.notna(row[value_col]) else 0
        pct = max(4, min(100, (valor / max_val) * 100)) if valor > 0 else 0
        rotulo = escape(str(row[label_col]))
        linhas.append(
            f'<div class="dash-bar-row">'
            f'<div class="dash-bar-label" title="{rotulo}">{rotulo}</div>'
            f'<div class="dash-bar-track"><div class="dash-bar-fill" style="width:{pct:.1f}%"></div></div>'
            f'<div class="dash-bar-value">{valor}</div>'
            f'</div>'
        )
    html = f'<div class="dash-bars">{"".join(linhas)}</div>'
    st.markdown(html, unsafe_allow_html=True)

def saldo_agrupado_materiais(conn):
    df = read_sql_query("""
        SELECT
            MIN(COALESCE(NULLIF(TRIM(nome),''),'SEM NOME')) AS Material,
            MIN(COALESCE(TRIM(marca),'')) AS Marca,
            MIN(COALESCE(TRIM(modelo),'')) AS Modelo,
            SUM(CASE WHEN COALESCE(entrada_registrada,0)=1 THEN COALESCE(quantidade,0) ELSE 0 END) AS QtdAtual,
            MAX(COALESCE(minimo,0)) AS Minimo,
            SUM(CASE WHEN COALESCE(entrada_registrada,0)=1 THEN 1 ELSE 0 END) AS EntradasRegistradas,
            COUNT(*) AS Cadastros
        FROM materiais
        GROUP BY UPPER(TRIM(nome)), UPPER(TRIM(marca)), UPPER(TRIM(modelo))
        ORDER BY Material, Marca, Modelo
    """, conn)
    if df.empty:
        return df
    df[["QtdAtual", "Minimo", "EntradasRegistradas", "Cadastros"]] = df[["QtdAtual", "Minimo", "EntradasRegistradas", "Cadastros"]].fillna(0).astype(int)

    def status_grupo(row):
        if row["EntradasRegistradas"] <= 0:
            return "AGUARDANDO ENTRADA"
        if row["QtdAtual"] == 0:
            return "ZERADO"
        if row["Minimo"] > 0 and row["QtdAtual"] <= row["Minimo"]:
            return "CRITICO"
        return "OK"

    df["Status"] = df.apply(status_grupo, axis=1)
    df["Deficit"] = (df["Minimo"] - df["QtdAtual"]).clip(lower=0)
    return df

def editor_recibo_saida(recibo_padrao=""):
    with st.expander("✏️ Editar recibo / devolver item ao estoque", expanded=bool(recibo_padrao)):
        b_rec = search_row(
            "Recibo para editar",
            "inp_rec_saida_edit",
            "btn_rec_saida_edit",
            "busca_rec_saida_edit",
            "Nº recibo, cliente, material ou patrimônio...",
        )

        conn = get_conn()
        termo = (b_rec or "").strip().upper()
        if termo:
            recibos = conn.execute(
                """
                SELECT num_recibo,seq_recibo,entidade,MAX(data_hora) data_hora
                  FROM historico
                 WHERE tipo='SAÍDA (CLIENTE)'
                   AND num_recibo IS NOT NULL
                   AND (UPPER(COALESCE(num_recibo,'')) LIKE ?
                        OR UPPER(COALESCE(entidade,'')) LIKE ?
                        OR UPPER(COALESCE(material,'')) LIKE ?
                        OR UPPER(COALESCE(identificacao,'')) LIKE ?)
                 GROUP BY num_recibo, seq_recibo, entidade
                 ORDER BY seq_recibo DESC
                """,
                (f"%{termo}%",) * 4,
            ).fetchall()
        elif recibo_padrao:
            recibos = conn.execute(
                """
                SELECT num_recibo,seq_recibo,entidade,MAX(data_hora) data_hora
                  FROM historico
                 WHERE tipo='SAÍDA (CLIENTE)' AND num_recibo IS NOT NULL
                 GROUP BY num_recibo, seq_recibo, entidade
                 ORDER BY CASE WHEN num_recibo=? THEN 0 ELSE 1 END, seq_recibo DESC
                 LIMIT 30
                """,
                (recibo_padrao,),
            ).fetchall()
        else:
            recibos = conn.execute(
                """
                SELECT num_recibo,seq_recibo,entidade,MAX(data_hora) data_hora
                  FROM historico
                 WHERE tipo='SAÍDA (CLIENTE)' AND num_recibo IS NOT NULL
                 GROUP BY num_recibo, seq_recibo, entidade
                 ORDER BY seq_recibo DESC
                 LIMIT 30
                """
            ).fetchall()
        conn.close()

        if not recibos:
            st.info("Nenhum recibo de saída encontrado.")
            return

        mapa_recibos = {f"Recibo {r[0]} | {r[3]} | {r[2]}": r for r in recibos}
        recibo_label = st.selectbox("Recibo:", list(mapa_recibos.keys()), key="sel_rec_saida_edit")
        recibo_info = mapa_recibos[recibo_label]
        num_recibo = recibo_info[0]
        seq_recibo = recibo_info[1]

        conn = get_conn()
        itens = conn.execute(
            "SELECT h.id,h.material_id,h.material,h.marca,h.modelo,h.quantidade,h.identificacao,h.observacoes,h.entidade,"
            "COALESCE(m.patrimonio,''),COALESCE(m.num_serie,'') "
            "FROM historico h LEFT JOIN materiais m ON m.id=h.material_id "
            "WHERE h.tipo='SAÍDA (CLIENTE)' AND h.num_recibo=? ORDER BY h.id",
            (num_recibo,),
        ).fetchall()
        conn.close()

        if not itens:
            st.info("Esse recibo não possui itens ativos.")
            return

        conn = get_conn()
        materiais_itens = {
            r[0]: localizar_material_historico(conn, r[1], r[2], r[3], r[4], r[6])
            for r in itens
        }
        conn.close()

        df_itens = pd.DataFrame(
            itens,
            columns=["ID", "MaterialID", "Material", "Marca", "Modelo", "Qtd", "Identificacao", "Obs", "Cliente", "PatrimonioDB", "SerieDB"],
        )
        genericos_ident = {"", "-", "—", "MARCA/MODELO", "LOTE"}
        df_itens[["Patrimonio", "Serie"]] = df_itens.apply(
            lambda row: pd.Series(
                patrimonio_serie_para_exibicao(
                    row["PatrimonioDB"],
                    row["SerieDB"],
                    row["Identificacao"] if str(row["Identificacao"] or "").strip().upper() not in genericos_ident else "",
                    materiais_itens.get(row["ID"]),
                )
            ),
            axis=1,
        )
        tabela_visivel(df_itens[["Material", "Marca", "Modelo", "Qtd", "Patrimonio", "Serie"]])

        st.markdown("##### 📝 Observações do recibo")
        obs_edit_recibo = st.text_area(
            "Observações",
            value=itens[0][7] or "",
            key=f"obs_rec_saida_{num_recibo}",
        )
        if st.button("💾 Salvar observações", key=f"btn_salvar_obs_rec_saida_{num_recibo}", use_container_width=True):
            conn = get_conn()
            conn.execute(
                "UPDATE historico SET observacoes=? WHERE tipo='SAÍDA (CLIENTE)' AND num_recibo=?",
                (obs_edit_recibo, num_recibo),
            )
            conn.commit(); conn.close()
            st.session_state["ultimo_recibo_html"] = gerar_html_recibo_saida(num_recibo)
            st.session_state["ultimo_recibo_num"] = num_recibo
            registrar_log(st.session_state["usuario"], f"Editou observações do recibo {num_recibo}")
            confirmar_e_atualizar("Observações do recibo atualizadas.")

        st.markdown("##### ↩️ Remover item do recibo")
        opcoes = {}
        for r in itens:
            material_ref_r = materiais_itens.get(r[0])
            patrimonio_r = r[9] or (material_ref_r[2] if material_ref_r else "") or (r[6] if (r[6] or "").strip().upper() not in genericos_ident else "")
            serie_r = r[10] or (material_ref_r[3] if material_ref_r else "")
            rotulo = f"{r[2]} | {r[3] or ''} {r[4] or ''} | Qtd:{r[5]} | Patrimonio: {patrimonio_r or '-'} | Serie: {serie_r or '-'}"
            opcoes[rotulo] = r
        item_label = st.selectbox("Item para remover do recibo:", list(opcoes.keys()), key="sel_item_rec_saida_edit")
        item = opcoes[item_label]

        conn = get_conn()
        material_destino = localizar_material_historico(conn, item[1], item[2], item[3], item[4], item[6])
        conn.close()

        if material_destino:
            st.info(f"Será devolvido ao estoque: {rotulo_material_identificado(material_destino, item[5])}")
        else:
            st.warning("Não consegui localizar automaticamente o material no estoque. Verifique patrimônio/série antes de remover.")

        confirmar = st.checkbox(
            "Confirmo remover este item do recibo e devolver ao estoque",
            key=f"conf_remove_item_rec_saida_{item[0]}",
        )
        if st.button("↩️ Remover do recibo e devolver ao estoque", key="btn_remove_item_rec_saida", use_container_width=True):
            if not confirmar:
                st.error("Marque a confirmação antes de remover.")
                return
            if not material_destino:
                st.error("Não foi possível devolver ao estoque porque o material não foi localizado.")
                return

            conn = get_conn()
            try:
                conn.execute(
                    "UPDATE materiais SET quantidade=quantidade+?, entrada_registrada=1 WHERE id=?",
                    (item[5], material_destino[0]),
                )
                conn.execute("DELETE FROM historico WHERE id=? AND tipo='SAÍDA (CLIENTE)'", (item[0],))
                conn.commit()
            finally:
                conn.close()

            novo_recibo_html = gerar_html_recibo_saida(num_recibo)
            st.session_state["ultimo_recibo_html"] = novo_recibo_html
            st.session_state["ultimo_recibo_num"] = num_recibo if novo_recibo_html else ""

            registrar_log(
                st.session_state["usuario"],
                f"Removeu item {item[0]} do recibo {num_recibo} e devolveu ao estoque ID {material_destino[0]}",
            )
            confirmar_e_atualizar("Item removido do recibo e devolvido ao estoque.")

        st.markdown("---")
        st.markdown("##### ➕ Adicionar item ao recibo")
        b_add = search_row(
            "Item para adicionar ao recibo",
            "inp_add_item_rec_saida",
            "btn_add_item_rec_saida",
            "busca_add_item_rec_saida",
            "Nome, marca, modelo, patrimônio, série, IMEI, linha, chip...",
            buscar_apenas_ao_clicar=True,
        )
        termo_add = (b_add or "").strip().upper()
        conn = get_conn()
        campos_add = ("nome", "marca", "modelo", "patrimonio", "num_serie", "prefixo_viatura", "imei", "numero_linha", "imei_chip", "lcm", "orgao")
        filtro_add = " OR ".join([f"UPPER(COALESCE({campo},'')) LIKE ?" for campo in campos_add])
        if termo_add:
            itens_add = conn.execute(
                "SELECT id,nome,quantidade,patrimonio,num_serie,marca,modelo,imei,lcm,orgao,prefixo_viatura,numero_linha,imei_chip "
                f"FROM materiais WHERE entrada_registrada=1 AND quantidade>0 AND ({filtro_add}) "
                "ORDER BY nome,marca,modelo,patrimonio,num_serie,imei,numero_linha,imei_chip,id",
                (f"%{termo_add}%",) * len(campos_add),
            ).fetchall()
        else:
            itens_add = []
        conn.close()

        if not termo_add:
            # Mantém o campo vazio até que o usuário clique em Buscar.
            ca1, ca2, ca3 = st.columns([5, 1, 1])
            ca1.selectbox(
                "Item disponível:",
                [""],
                key="sel_add_item_rec_saida_vazio",
                label_visibility="collapsed",
                disabled=True,
            )
            ca2.number_input(
                "Qtd adicionar",
                min_value=1,
                value=1,
                key="qtd_add_item_rec_saida_vazio",
                label_visibility="collapsed",
                disabled=True,
            )
            ca3.button("+", key="btn_confirm_add_item_rec_saida_vazio", use_container_width=True, disabled=True)
        elif not itens_add:
            st.info("Nenhum item disponível em estoque para adicionar.")
        else:
            ids_no_recibo = {r[1] for r in itens if r[1]}
            ident_no_recibo = {(r[6] or "").strip().upper() for r in itens if (r[6] or "").strip()}

            def rotulo_add_recibo(idx):
                r = itens_add[idx]
                partes = [r[1]]
                if r[0] in ids_no_recibo or (r[3] or r[4] or r[7] or r[10] or r[11] or r[12] or "").strip().upper() in ident_no_recibo:
                    partes.insert(0, "[JA NO RECIBO]")
                marca_modelo = " ".join(parte for parte in (r[5], r[6]) if parte)
                if marca_modelo:
                    partes.append(marca_modelo)
                detalhes = []
                if r[3]:
                    detalhes.append(f"Patrimonio: {r[3]}")
                if r[4]:
                    detalhes.append(f"Serie: {r[4]}")
                if r[7]:
                    detalhes.append(f"IMEI: {r[7]}")
                if r[11]:
                    detalhes.append(f"Número da linha: {r[11]}")
                if r[12]:
                    detalhes.append(f"IMEI do chip: {r[12]}")
                if r[8]:
                    detalhes.append(f"LCM: {r[8]}")
                if r[9]:
                    detalhes.append(f"Orgao: {r[9]}")
                if detalhes:
                    partes.append(" | ".join(detalhes))
                partes.append(f"Qtd disponivel: {r[2]}")
                return " | ".join(partes)

            ca1, ca2, ca3 = st.columns([5, 1, 1])
            idx_add = ca1.selectbox(
                "Item disponível:",
                range(len(itens_add)),
                key="sel_add_item_rec_saida",
                label_visibility="collapsed",
                format_func=rotulo_add_recibo,
            )
            item_add = itens_add[idx_add]
            qtd_add = ca2.number_input(
                "Qtd adicionar",
                min_value=1,
                max_value=max(1, item_add[2]),
                value=1,
                step=1,
                key="qtd_add_item_rec_saida",
                label_visibility="collapsed",
            )
            if ca3.button("➕", key="btn_confirm_add_item_rec_saida", use_container_width=True):
                ident_add = item_add[3] or item_add[4] or item_add[7] or item_add[11] or item_add[12] or item_add[10] or "Marca/Modelo"
                obs_rec = itens[0][7] or ""
                entidade_rec = itens[0][8] or recibo_info[2]
                dt_add = datetime.now().strftime("%d/%m/%Y %H:%M")
                conn = get_conn()
                try:
                    cur = conn.execute(
                        "UPDATE materiais SET quantidade=quantidade-? WHERE id=? AND quantidade>=?",
                        (qtd_add, item_add[0], qtd_add),
                    )
                    if cur.rowcount == 0:
                        conn.rollback()
                        st.error("Estoque insuficiente para adicionar esse item ao recibo.")
                        return
                    conn.execute(
                        "INSERT INTO historico(material_id,tipo,material,quantidade,entidade,identificacao,marca,modelo,observacoes,data_hora,num_recibo,seq_recibo) "
                        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                        (item_add[0], "SAÍDA (CLIENTE)", item_add[1], qtd_add, entidade_rec,
                         ident_add, item_add[5], item_add[6], obs_rec, dt_add, num_recibo, seq_recibo),
                    )
                    conn.commit()
                finally:
                    conn.close()

                novo_recibo_html = gerar_html_recibo_saida(num_recibo)
                st.session_state["ultimo_recibo_html"] = novo_recibo_html
                st.session_state["ultimo_recibo_num"] = num_recibo if novo_recibo_html else ""
                registrar_log(
                    st.session_state["usuario"],
                    f"Adicionou material ID {item_add[0]} ao recibo {num_recibo}",
                )
                confirmar_e_atualizar("Item adicionado ao recibo e baixado do estoque.")

# ═══════════════════════════════════════════════════════════════════════════════
# RECIBO HTML
# ═══════════════════════════════════════════════════════════════════════════════
BRASAO_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f7/Bras%C3%A3o_da_Pol%C3%ADcia_Militar_do_Estado_de_S%C3%A3o_Paulo.svg/120px-Bras%C3%A3o_da_Pol%C3%ADcia_Militar_do_Estado_de_S%C3%A3o_Paulo.svg.png"

def html_recibo(itens, cliente, operacao, num_recibo_fmt, obs=""):
    def esc(value):
        return escape(str(value), quote=True)

    cliente_html = esc(cliente)
    operacao_html = esc(operacao)
    recibo_html = esc(num_recibo_fmt)
    obs_html = esc(obs) if obs else "&nbsp;"
    brasao_src = esc(brasao_recibo_data_url())
    rows = ""
    for i, it in enumerate(itens, 1):
        marca = it.get("marca") or "—"
        modelo = it.get("modelo") or "—"
        patrimonio = it.get("patrimonio") or "—"
        serie = it.get("num_serie") or "—"
        rows += f"""<tr>
          <td class="text-center">{i}</td>
          <td>{esc(it.get('nome', ''))}</td>
          <td>{esc(marca)}</td>
          <td>{esc(modelo)}</td>
          <td class="text-center">{esc(it.get('quantidade', ''))}</td>
          <td>{esc(patrimonio)}</td>
          <td>{esc(serie)}</td>
        </tr>"""
    dt = datetime.now().strftime("%d/%m/%Y %H:%M")
    return f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Recibo {recibo_html}</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:#f8fafc;color:#111827;font-family:Arial,Helvetica,sans-serif;font-size:12px;line-height:1.35}}
.page{{background:#fff;margin:0 auto;max-width:900px;min-height:100vh;padding:24px}}
.print-actions{{padding:14px 24px;text-align:center}}
.btn{{background:#1a3a6b;border:0;border-radius:6px;color:#fff;cursor:pointer;font-size:13px;font-weight:700;padding:10px 32px}}
.btn:hover{{background:#274fa8}}
.header{{align-items:center;border-bottom:3px double #1a3a6b;display:grid;gap:16px;grid-template-columns:112px 1fr 112px;margin-bottom:14px;padding-bottom:12px}}
.header-center{{text-align:center}}
.header-logo{{align-items:center;display:flex;justify-content:center}}
.header img{{height:100px;object-fit:contain;width:100px}}
h3,p{{margin:2px 0}}
.org-title{{font-size:12px;font-weight:700;letter-spacing:.02em}}
.org-subtitle{{color:#555;font-size:10px}}
.rec-num{{font-size:14px;font-weight:700;margin:12px 0;text-align:center}}
.info{{border:1px solid #d1d5db;border-radius:6px;display:grid;gap:0;grid-template-columns:1fr 1fr;margin:10px 0;overflow:hidden}}
.info span{{border-bottom:1px solid #e5e7eb;font-size:12px;padding:7px 9px}}
.info span:nth-child(odd){{border-right:1px solid #e5e7eb}}
.info span:nth-last-child(-n+2){{border-bottom:0}}
table{{border-collapse:collapse;margin-top:12px;width:100%}}
th{{background:#1a3a6b;color:#fff;font-size:11px;padding:7px 8px;text-align:left}}
td{{border-bottom:1px solid #ddd;font-size:11px;padding:6px 8px;vertical-align:top}}
tr:nth-child(even){{background:#f7f7f7}}
.col-index{{width:32px}}
.col-qtd{{width:48px}}
.text-center{{text-align:center}}
.section-label{{font-weight:700;margin-top:12px}}
.obs{{border:1px solid #cbd5e1;border-radius:5px;font-size:11px;margin-top:6px;min-height:52px;padding:8px;white-space:pre-wrap}}
.assin{{font-size:12px;line-height:2;margin-top:76px}}
.ass-linha{{margin-top:18px;white-space:nowrap}}
.ass-linha:first-child{{margin-top:0}}
.footer{{color:#777;font-size:9px;margin-top:28px;text-align:center}}
@media print{{@page{{size:A4;margin:1.5cm}}body{{background:#fff}}.no-print{{display:none!important}}.page{{max-width:none;min-height:auto;padding:0}}}}
@media (max-width:640px){{.page{{padding:16px}}.header{{gap:10px;grid-template-columns:68px 1fr 68px}}.header img{{height:64px;width:64px}}.info{{grid-template-columns:1fr}}.info span,.info span:nth-child(odd){{border-right:0}}.info span:nth-last-child(2){{border-bottom:1px solid #e5e7eb}}.ass-linha{{white-space:normal}}}}
</style>
</head>
<body>
<div class="print-actions no-print">
<button class="btn no-print" onclick="window.print()">🖨️ Imprimir / Salvar como PDF</button>
</div>
<main class="page">
<div class="header">
  <div class="header-logo"><img src="{brasao_src}" alt="Brasão da seção" onerror="this.style.display='none'"></div>
  <div class="header-center">
    <h3 class="org-title">SECRETARIA DA SEGURANÇA PÚBLICA</h3>
    <h3 class="org-title">POLÍCIA MILITAR DO ESTADO DE SÃO PAULO</h3>
    <h3 class="org-title">1º BATALHÃO DE POLÍCIA RODOVIÁRIA</h3>
    <p class="org-subtitle">Controle de Materiais de Telemática — Seção 07</p>
  </div>
  <div class="header-logo"><img src="{brasao_src}" alt="Brasão da seção" onerror="this.style.display='none'"></div>
</div>
<p class="rec-num">RECIBO DE MOVIMENTAÇÃO — Nº {recibo_html}</p>
<div class="info">
  <span><b>Operação:</b> {operacao_html}</span>
  <span><b>Data/Hora:</b> {dt}</span>
  <span><b>Envolvido:</b> {cliente_html}</span>
  <span><b>Nº Recibo:</b> {recibo_html}</span>
</div>
<table><thead><tr>
  <th class="col-index">#</th><th>Material</th><th>Marca</th>
  <th>Modelo</th><th class="col-qtd">Qtd</th>
  <th>Nº Patrimônio</th><th>Nº Série</th>
</tr></thead><tbody>{rows}</tbody></table>
<p class="section-label">Observações:</p>
<div class="obs">{obs_html}</div>
<div class="assin">
  <div class="ass-linha">Entregue por: ________________________________</div>
  <div class="ass-linha">Recebedor: NOME LEGÍVEL: ______________________________ RE/RG: ______________ DATA: ______________ ASSINATURA: ____________________</div>
</div>
<p class="footer">
  Documento gerado em {dt} — 1º BPRv
</p>
</main>
</body>
</html>"""

def mostrar_recibo_iframe(html_str, key_prefix=""):
    enc = base64.b64encode(html_str.encode()).decode()
    st.markdown(
        f'<iframe src="data:text/html;base64,{enc}" width="100%" height="620" '
        f'class="receipt-frame"></iframe>',
        unsafe_allow_html=True)
    st.download_button(
        "📥 Baixar HTML do Recibo (abrir → Ctrl+P → salvar PDF)",
        html_str.encode(),
        file_name=f"recibo_{key_prefix}_{datetime.now().strftime('%d%m%Y_%H%M')}.html",
        mime="text/html",
        key=f"dl_{key_prefix}_{int(time.time())}")

def query_param_valor(nome):
    try:
        valor = st.query_params.get(nome, "")
    except Exception:
        try:
            valor = st.experimental_get_query_params().get(nome, [""])[0]
        except Exception:
            valor = ""
    if isinstance(valor, list):
        valor = valor[0] if valor else ""
    return valor or ""

def limpar_query_param(nome):
    try:
        if nome in st.query_params:
            del st.query_params[nome]
            return
    except Exception:
        pass
    try:
        params = st.experimental_get_query_params()
        params.pop(nome, None)
        st.experimental_set_query_params(**params)
    except Exception:
        pass

def recibos_para_texto_html(valor):
    recibos = [r.strip() for r in str(valor or "").split(",") if r and r.strip()]
    itens = []
    for recibo in recibos:
        recibo_html = escape(recibo)
        itens.append(f'<span class="receipt-link">{recibo_html}</span>')
    return ", ".join(itens)

# ═══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════════════════════
_defaults = {
    "autenticado": False, "usuario": "", "perfil": "", "carrinho": [],
    "pagina": "Dashboard", "ultimo_recibo_html": "", "ultimo_recibo_num": "",
    "brasao_recibo": "",
    "multi_saida_seq": 0,
    "busca_prod": "", "busca_cli": "", "busca_forn": "",
    "busca_orgao": "",
    "busca_mat_entrada": "", "busca_forn_entrada": "",
    "busca_cli_saida": "", "busca_mat_saida": "",
    "busca_rec_saida_edit": "",
    "busca_add_item_rec_saida": "",
    "recibo_busca_aberto": "",
    "entradas_temp": [],
    "login_failed_attempts": 0,
    "login_lock_until": 0,
    "last_activity_at": 0,
    "sessao_expirada": False,
    "confirmar_limpeza_dados": False,
    "backup_auto_status": None,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

app_logo = ""
for logo_nome in ("Brasão 18ago23 alta resolução.png", "polrv.png", "polrv.webp", "polrv.jpg", "polrv.jpeg"):
    app_logo = imagem_local_para_data_url(logo_nome)
    if app_logo:
        break
login_logo_html = (
    f'<img class="login-brand__logo" src="{app_logo}" alt="Logo da empresa">'
    if app_logo
    else '<span class="login-brand__fallback">🛡️</span>'
)
sidebar_logo_html = (
    f'<img class="sidebar-brand__logo" src="{app_logo}" alt="Logo da empresa">'
    if app_logo
    else '<span class="sidebar-brand__fallback">🛡️</span>'
)

# ═══════════════════════════════════════════════════════════════════════════════
# LOGIN  — sem form, sem div wrapper fantasma
# ═══════════════════════════════════════════════════════════════════════════════
if not st.session_state["autenticado"]:
    st.markdown("""
    <style>
    section[data-testid="stSidebar"], header[data-testid="stHeader"], footer { display:none !important; }
    .main .block-container {
        background: transparent !important;
        border: none !important; box-shadow: none !important;
        backdrop-filter: none !important;
        padding: 0 !important; max-width: 100% !important;
    }
    /* botão de login — tamanho fixo sem depender de padding */
    .login-area .stButton > button {
        width: 100% !important;
        height: 46px !important;
        min-height: 46px !important;
        font-size: 0.92rem !important;
        border-radius: 8px !important;
        background: linear-gradient(135deg,#1d4ed8,#3b82f6) !important;
        box-shadow: 0 4px 16px rgba(59,130,246,0.40) !important;
    }
    .login-area .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 7px 22px rgba(59,130,246,0.50) !important;
    }
    .login-area div[data-testid="stButton"] {
        margin-top: 2px !important;
        margin-bottom: 0 !important;
    }
    .login-area div[data-testid="stCheckbox"] {
        margin-top: 0 !important;
        margin-bottom: 2px !important;
    }
    .login-area div[data-testid="stCheckbox"] label {
        align-items: center !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Container central com largura limitada no desktop e fluida no celular.
    with st.container(key="login_panel"):
        st.markdown("<div class='login-spacer'></div>", unsafe_allow_html=True)

        # ── cartão visual ─────────────────────────────────────────
        st.markdown("""
        <div class="login-card">
          <div class="login-brand">
            <div class="login-brand__icon">""" + login_logo_html + """</div>
            <h2 class="login-brand__title">1º BPRv</h2>
            <p style="font-size: 80px;">Controle de Materiais de Telemática</p>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── campos — largura controlada pela coluna pai ───────────
        st.markdown("<div class='login-area'>", unsafe_allow_html=True)
        if st.session_state.get("sessao_expirada"):
            st.warning("Sessão expirada por inatividade. Informe a senha novamente.")

        # label manual + campo com label oculto
        st.markdown("<p class='login-label'>Usuário</p>", unsafe_allow_html=True)
        usuario_val = st.text_input("u", placeholder="Digite seu usuário",
                                    label_visibility="collapsed", key="login_u")

        st.markdown("<p class='login-label'>Senha</p>", unsafe_allow_html=True)
        senha_val = st.text_input("s", placeholder="Digite sua senha",
                                  type="password", label_visibility="collapsed", key="login_s")

        st.markdown("<div class='login-field-gap'></div>", unsafe_allow_html=True)
        try:
            login_qp = st.query_params.get("login", "")
        except Exception:
            login_qp = ""
        if isinstance(login_qp, list):
            login_qp = login_qp[0] if login_qp else ""
        if login_qp in ("reset", "acesso"):
            st.session_state["login_help_panel"] = login_qp

        aux_left, aux_right = st.columns([1, 1])
        with aux_left:
            st.checkbox("Lembrar-me", key="login_lembrar", label_visibility="visible")
        with aux_right:
            st.markdown(
                "<div style='text-align:right;margin-top:4px;padding-right:2px;'><a href='?login=reset' style='color:#e2e8f0;text-decoration:none;font-weight:600;font-size:0.82rem;'>Esqueci minha senha</a></div>",
                unsafe_allow_html=True,
            )
        entrar = st.button("🔐  Entrar", use_container_width=True, key="login_btn")
        st.markdown(
            "<div style='text-align:center;margin-top:10px;'><a href='?login=acesso' style='color:#e2e8f0;text-decoration:none;font-weight:600;font-size:0.84rem;'>Solicitar novo acesso</a></div>",
            unsafe_allow_html=True,
        )

        st.markdown("</div>", unsafe_allow_html=True)

        if entrar:
            u = usuario_val.strip()
            p = senha_val
            bloqueio = segundos_bloqueio_login()
            if bloqueio > 0:
                st.error(f"Muitas tentativas incorretas. Aguarde {bloqueio // 60 + 1} minuto(s) e tente novamente.")
            elif not u or not p:
                st.error("Preencha usuário e senha.")
            elif not usuario_valido(u):
                registrar_falha_login(u[:32])
                st.error("Usuário ou senha incorretos.")
            else:
                conn = get_conn()
                row = conn.execute(
                    "SELECT senha, perfil FROM usuarios WHERE usuario=?", (u,)
                ).fetchone()
                conn.close()
                if row and verificar_senha_bcrypt(p, row[0]):
                    limpar_falhas_login()
                    st.session_state.update(autenticado=True, usuario=u,
                                            perfil=row[1], carrinho=[],
                                            last_activity_at=time.time(),
                                            sessao_expirada=False,
                                            login_help_panel="")
                    registrar_log(u, "Login realizado")
                    st.rerun()
                else:
                    registrar_falha_login(u[:32])
                    st.error("Usuário ou senha incorretos.")

        painel_login = st.session_state.get("login_help_panel", "")
        if painel_login == "reset":
            st.markdown("##### Redefinir senha")
            c_reset_u, c_reset_s, c_reset_c = st.columns([1.2, 1, 1])
            reset_usuario = c_reset_u.text_input(
                "Usuario cadastrado",
                placeholder="Digite seu usuario",
                label_visibility="collapsed",
                key="reset_u",
            )
            reset_senha = c_reset_s.text_input(
                "Nova senha",
                placeholder="Nova senha",
                type="password",
                label_visibility="collapsed",
                key="reset_s",
            )
            reset_confirma = c_reset_c.text_input(
                "Confirmar nova senha",
                placeholder="Confirmar senha",
                type="password",
                label_visibility="collapsed",
                key="reset_sc",
            )
            if st.button("Solicitar redefinição", use_container_width=True, key="btn_solicitar_redef_senha"):
                if reset_senha != reset_confirma:
                    st.error("Senhas nao coincidem.")
                else:
                    ok_reset, msg_reset = solicitar_redefinicao_senha(reset_usuario, reset_senha)
                    if ok_reset:
                        registrar_log(reset_usuario.strip()[:32], "Solicitou redefinicao de senha")
                        st.success(msg_reset)
                    else:
                        st.error(msg_reset)
            st.markdown("<div style='text-align:center;margin-top:6px;'><a href='?' style='color:#e2e8f0;text-decoration:none;font-size:0.78rem;'>Voltar ao login</a></div>", unsafe_allow_html=True)

        elif painel_login == "acesso":
            st.markdown("##### Solicitar novo acesso")
            c_cad_u, c_cad_s, c_cad_c = st.columns([1.2, 1, 1])
            novo_usuario = c_cad_u.text_input(
                "Novo usuario",
                placeholder="Escolha seu usuario",
                label_visibility="collapsed",
                key="cadastro_u",
            )
            nova_senha = c_cad_s.text_input(
                "Senha",
                placeholder="Senha",
                type="password",
                label_visibility="collapsed",
                key="cadastro_s",
            )
            confirma_senha = c_cad_c.text_input(
                "Confirmar senha",
                placeholder="Confirmar senha",
                type="password",
                label_visibility="collapsed",
                key="cadastro_sc",
            )
            if st.button("Solicitar validação", use_container_width=True, key="btn_solicitar_acesso"):
                if nova_senha != confirma_senha:
                    st.error("Senhas nao coincidem.")
                else:
                    ok_solic, msg_solic = solicitar_cadastro_usuario(novo_usuario, nova_senha)
                    if ok_solic:
                        registrar_log(novo_usuario.strip()[:32], "Solicitou cadastro de usuario")
                        st.success(msg_solic)
                    else:
                        st.error(msg_solic)
            st.markdown("<div style='text-align:center;margin-top:6px;'><a href='?' style='color:#e2e8f0;text-decoration:none;font-size:0.78rem;'>Voltar ao login</a></div>", unsafe_allow_html=True)

        st.markdown(
            "<p class='login-version'>Desenvolvido por Cb PM Baldinetti - 1º BPRv</p>",
            unsafe_allow_html=True)

    st.stop()

verificar_expiracao_sessao()
injetar_timer_inatividade()


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR / MENU
# ═══════════════════════════════════════════════════════════════════════════════
MENU_GRUPOS = [
    ("", [
        ("📊", "Dashboard"),
        ("🔍", "Busca e Gerenciamento"),
    ]),
    ("Cadastros", [
        ("🏭", "Cadastrar Fornecedor"),
        ("👤", "Cadastrar Cliente"),
        ("📦", "Cadastrar Material"),
        ("🏢", "Cadastrar Órgão"),
    ]),
    ("Movimentação", [
        ("📥", "Registrar Entrada"),
        ("📤", "Registrar Saída"),
    ]),
    ("Documentação", [
        ("📋", "Histórico e Recibos"),
        ("📑", "Central de Relatórios"),
    ]),
]
if is_admin():
    MENU_GRUPOS += [("Administração", [("👥", "Gerenciar Usuários"), ("💾", "Backup Automático"), ("🧹", "Limpeza de Dados"), ("🛡️", "Auditoria")])]

def navegar_para(pagina):
    st.session_state["pagina"] = pagina


def confirmar_e_atualizar(mensagem):
    st.session_state["confirmacao_pendente"] = mensagem
    st.rerun()


with st.sidebar:
    st.markdown(f"""
    <div class="sidebar-brand">
      <div class="sidebar-brand__icon">{sidebar_logo_html}</div>
      <div class="sidebar-brand__title">1º BPRv</div>
      <div class="sidebar-brand__subtitle">Controle de Estoque</div>
      <div class="sidebar-brand__user">
        👤 {escape(st.session_state['usuario'])} · {escape(st.session_state['perfil'])}
      </div>
    </div>
    """, unsafe_allow_html=True)

    if is_admin():
        with st.expander("🖼️ Brasão do Recibo"):
            brasao_file = st.file_uploader(
                "Enviar imagem",
                type=["png", "jpg", "jpeg", "webp"],
                key="upload_brasao_recibo",
                label_visibility="collapsed",
            )
            if brasao_file is not None:
                salvar_brasao_recibo(brasao_file)
                st.session_state["brasao_recibo"] = imagem_para_data_url(brasao_file)
                st.success("Imagem carregada para os recibos.")
            else:
                st.session_state.pop("brasao_upload_digest", None)
            brasao_atual = brasao_recibo_data_url()
            if brasao_atual and brasao_atual != BRASAO_URL:
                st.image(brasao_atual, width=92)
                if st.button("Remover imagem", key="btn_remover_brasao"):
                    remover_brasao_recibo()
                    st.rerun()

    for grupo, itens in MENU_GRUPOS:
        if grupo:
            st.markdown(f"<small>{escape(grupo).upper()}</small>", unsafe_allow_html=True)
        for icon, label in itens:
            ativo = st.session_state["pagina"] == label
            extra = "background:rgba(59,130,246,0.20)!important;border-color:rgba(59,130,246,0.45)!important;color:#93c5fd!important;" if ativo else ""
            if extra:
                st.markdown(f"<style>div[data-testid='element-container']:has(button[key='nav_{label}']) button{{ {extra} }}</style>", unsafe_allow_html=True)
            st.button(f"{icon}  {label}", key=f"nav_{label}", use_container_width=True,
                      on_click=navegar_para, args=(label,))
        st.markdown("<hr>", unsafe_allow_html=True)

    if st.button("🚪  Sair", use_container_width=True, key="btn_logout"):
        encerrar_sessao("Logout")
        st.rerun()

opcao = st.session_state["pagina"]
confirmacao = st.session_state.pop("confirmacao_pendente", None)
if confirmacao:
    st.success(confirmacao)

# ═══════════════════════════════════════════════════════════════════════════════
# GERENCIAR USUÁRIOS
# ═══════════════════════════════════════════════════════════════════════════════
if opcao == "Gerenciar Usuários":
    if not is_admin(): st.warning("⛔ Acesso restrito."); st.stop()
    st.title("👥 Gerenciar Usuários")
    t1, t2, t3, t4, t5 = st.tabs(["➕ Criar", "🗑️ Remover", "🔑 Alterar Senha", "✅ Validar Solicitações", "♻️ Redefinir Senhas"])

    with t1:
        with st.form("form_criar_user"):
            c1, c2 = st.columns(2)
            nu = c1.text_input("Nome de Usuário")
            ns = c2.text_input("Senha", type="password")
            c3, c4 = st.columns(2)
            nc = c3.text_input("Confirmar Senha", type="password")
            np = c4.selectbox("Perfil", ["Padrão", "Administrador"])
            ok = st.form_submit_button("Criar Usuário", use_container_width=True)
        if ok:
            nu = nu.strip()
            if not nu or not ns: st.error("Preencha todos os campos.")
            elif not usuario_valido(nu): st.error("Usuário deve ter 3 a 32 caracteres e usar apenas letras, números, ponto, hífen, sublinhado ou @.")
            elif ns != nc: st.error("Senhas não coincidem.")
            elif not senha_forte(ns): st.error("Senha deve ter no mínimo 8 caracteres, incluindo letras e números.")
            else:
                try:
                    h = bcrypt.hashpw(ns.encode(), bcrypt.gensalt()).decode()
                    conn = get_conn()
                    conn.execute("INSERT INTO usuarios(usuario,senha,perfil) VALUES(?,?,?)", (nu, h, np))
                    conn.execute("DELETE FROM solicitacoes_usuarios WHERE usuario=?", (nu,))
                    conn.commit(); conn.close()
                    registrar_log(st.session_state["usuario"], f"Criou usuário: {nu}")
                    st.success(f"Usuário '{nu}' criado!")
                except psycopg.IntegrityError: st.error("Usuário já existe.")

    with t2:
        conn = get_conn()
        lu = [r[0] for r in conn.execute("SELECT usuario FROM usuarios WHERE usuario!=?",
                                          (st.session_state["usuario"],)).fetchall()]
        conn.close()
        if not lu: st.info("Sem outros usuários.")
        else:
            with st.form("form_rem_user"):
                ud = st.selectbox("Usuário a remover:", lu)
                ok = st.form_submit_button("Excluir", use_container_width=True)
            if ok:
                conn = get_conn(); conn.execute("DELETE FROM usuarios WHERE usuario=?", (ud,)); conn.commit(); conn.close()
                registrar_log(st.session_state["usuario"], f"Excluiu: {ud}")
                confirmar_e_atualizar("Removido!")

    with t3:
        conn = get_conn()
        tu = [r[0] for r in conn.execute("SELECT usuario FROM usuarios").fetchall()]
        conn.close()
        with st.form("form_alt_senha"):
            c1, c2, c3 = st.columns(3)
            ua = c1.selectbox("Usuário:", tu)
            ns2 = c2.text_input("Nova Senha", type="password")
            nc2 = c3.text_input("Confirmar", type="password")
            ok = st.form_submit_button("Alterar", use_container_width=True)
        if ok:
            if not ns2 or ns2 != nc2: st.error("Senhas não coincidem.")
            elif not senha_forte(ns2): st.error("Senha deve ter no mínimo 8 caracteres, incluindo letras e números.")
            else:
                h = bcrypt.hashpw(ns2.encode(), bcrypt.gensalt()).decode()
                conn = get_conn(); conn.execute("UPDATE usuarios SET senha=? WHERE usuario=?", (h, ua)); conn.commit(); conn.close()
                registrar_log(st.session_state["usuario"], f"Alterou senha: {ua}")
                st.success("Senha alterada!")

    with t4:
        conn = get_conn()
        solicitacoes = conn.execute(
            "SELECT id,usuario,data FROM solicitacoes_usuarios ORDER BY id DESC"
        ).fetchall()
        conn.close()

        if not solicitacoes:
            st.info("Nenhuma solicitacao pendente.")
        else:
            mapa_solic = {f"{r[1]} | solicitado em {r[2]}": {"id": r[0], "usuario": r[1], "data": r[2]} for r in solicitacoes}
            escolha = st.selectbox("Solicitacao pendente:", list(mapa_solic.keys()), key="sel_solic_usuario")
            solicitacao = mapa_solic[escolha]
            perfil_aprovado = st.selectbox("Perfil ao aprovar:", ["Padrão", "Administrador"], key="perfil_solic_usuario")
            c_aprovar, c_rejeitar = st.columns(2)

            if c_aprovar.button("Aprovar usuario", use_container_width=True, key="btn_aprovar_usuario"):
                conn = get_conn()
                row = conn.execute(
                    "SELECT usuario,senha FROM solicitacoes_usuarios WHERE id=?",
                    (solicitacao["id"],),
                ).fetchone()
                if row:
                    try:
                        conn.execute(
                            "INSERT INTO usuarios(usuario,senha,perfil) VALUES(?,?,?)",
                            (row[0], row[1], perfil_aprovado),
                        )
                        conn.execute("DELETE FROM solicitacoes_usuarios WHERE id=?", (solicitacao["id"],))
                        conn.commit()
                        registrar_log(st.session_state["usuario"], f"Aprovou usuario: {row[0]} como {perfil_aprovado}")
                        confirmar_e_atualizar("Usuario aprovado.")
                    except psycopg.IntegrityError:
                        conn.execute("DELETE FROM solicitacoes_usuarios WHERE id=?", (solicitacao["id"],))
                        conn.commit()
                        st.error("Usuario ja existe. Solicitacao removida.")
                conn.close()

            if c_rejeitar.button("Rejeitar solicitacao", use_container_width=True, key="btn_rejeitar_usuario"):
                conn = get_conn()
                conn.execute("DELETE FROM solicitacoes_usuarios WHERE id=?", (solicitacao["id"],))
                conn.commit(); conn.close()
                registrar_log(st.session_state["usuario"], f"Rejeitou solicitacao de usuario: {solicitacao['usuario']}")
                confirmar_e_atualizar("Solicitacao rejeitada.")

    with t5:
        conn = get_conn()
        solicitacoes_senha = conn.execute(
            "SELECT id,usuario,data FROM solicitacoes_senha ORDER BY id DESC"
        ).fetchall()
        conn.close()

        if not solicitacoes_senha:
            st.info("Nenhuma redefinicao de senha pendente.")
        else:
            mapa_reset = {f"{r[1]} | solicitado em {r[2]}": {"id": r[0], "usuario": r[1], "data": r[2]} for r in solicitacoes_senha}
            escolha_reset = st.selectbox("Pedido pendente:", list(mapa_reset.keys()), key="sel_redef_senha")
            pedido_reset = mapa_reset[escolha_reset]
            c_aprovar_reset, c_rejeitar_reset = st.columns(2)

            if c_aprovar_reset.button("Aprovar redefinicao", use_container_width=True, key="btn_aprovar_redef_senha"):
                conn = get_conn()
                row = conn.execute(
                    "SELECT usuario,senha FROM solicitacoes_senha WHERE id=?",
                    (pedido_reset["id"],),
                ).fetchone()
                if row:
                    cur = conn.execute("UPDATE usuarios SET senha=? WHERE usuario=?", (row[1], row[0]))
                    conn.execute("DELETE FROM solicitacoes_senha WHERE id=?", (pedido_reset["id"],))
                    conn.commit()
                    if cur.rowcount:
                        registrar_log(st.session_state["usuario"], f"Aprovou redefinicao de senha: {row[0]}")
                        st.success("Senha redefinida.")
                    else:
                        st.error("Usuario nao encontrado. Pedido removido.")
                    st.rerun()
                conn.close()

            if c_rejeitar_reset.button("Rejeitar redefinicao", use_container_width=True, key="btn_rejeitar_redef_senha"):
                conn = get_conn()
                conn.execute("DELETE FROM solicitacoes_senha WHERE id=?", (pedido_reset["id"],))
                conn.commit(); conn.close()
                registrar_log(st.session_state["usuario"], f"Rejeitou redefinicao de senha: {pedido_reset['usuario']}")
                confirmar_e_atualizar("Pedido rejeitado.")

# ═══════════════════════════════════════════════════════════════════════════════
# BACKUP AUTOMÁTICO
# ═══════════════════════════════════════════════════════════════════════════════
elif opcao == "Backup Automático":
    if not is_admin(): st.warning("Acesso restrito."); st.stop()
    st.title("Backup do ambiente de teste")
    st.info("O teste usa um banco separado na nuvem. Backups devem ser exportados do PostgreSQL; pastas deste computador não estão disponíveis na hospedagem.")
    st.caption("Consulte o guia desta cópia para exportar com pg_dump. O backup automático ainda não está configurado neste piloto.")

elif opcao == "Limpeza de Dados":
    if not is_admin(): st.warning("⛔ Acesso restrito."); st.stop()
    st.title("🧹 Limpeza de Dados")
    st.warning("Esta ação apaga definitivamente dados do banco. Usuários e auditoria não serão apagados nesta tela.")

    opcoes_limpeza = st.multiselect(
        "Dados que serão apagados:",
        ["Materiais", "Clientes", "Fornecedores", "Movimentações", "Entradas", "Saídas"],
        default=["Materiais", "Clientes", "Fornecedores"],
        key="limpeza_opcoes",
    )

    if st.button("Apagar dados selecionados", type="primary", use_container_width=True, key="btn_preparar_limpeza"):
        if not opcoes_limpeza:
            st.error("Selecione pelo menos uma categoria para apagar.")
        else:
            st.session_state["confirmar_limpeza_dados"] = True

    if st.session_state.get("confirmar_limpeza_dados"):
        st.error("Confirmação necessária: os dados selecionados serão apagados e não poderão ser recuperados pelo sistema.")
        frase = st.text_input(
            "Digite APAGAR para confirmar:",
            key="txt_confirmar_limpeza",
        )
        c_conf, c_cancel = st.columns(2)
        if c_conf.button("Confirmar apagamento definitivo", use_container_width=True, key="btn_confirmar_limpeza"):
            if frase.strip().upper() != "APAGAR":
                st.error("Confirmação inválida. Digite APAGAR exatamente.")
            elif not opcoes_limpeza:
                st.error("Selecione pelo menos uma categoria para apagar.")
            else:
                total = limpar_dados_cadastro(opcoes_limpeza)
                registrar_log(st.session_state["usuario"], f"Limpou dados de cadastro: {', '.join(opcoes_limpeza)} ({total} registro(s))")
                st.session_state["confirmar_limpeza_dados"] = False
                confirmar_e_atualizar(f"Limpeza concluída. {total} registro(s) apagado(s).")
        if c_cancel.button("Cancelar", use_container_width=True, key="btn_cancelar_limpeza"):
            st.session_state["confirmar_limpeza_dados"] = False
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# AUDITORIA
# ═══════════════════════════════════════════════════════════════════════════════
elif opcao == "Auditoria":
    if not is_admin(): st.warning("⛔ Acesso restrito."); st.stop()
    st.title("🛡️ Auditoria do Sistema")
    conn = get_conn()
    df = read_sql_query("SELECT id,usuario,acao,data FROM logs_sistema ORDER BY id DESC", conn)
    conn.close()
    tabela_visivel(df)
    if not df.empty:
        st.download_button("📥 Exportar Excel", gerar_excel(df),
                           f"auditoria_{datetime.now().strftime('%d%m%Y_%H%M')}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ═══════════════════════════════════════════════════════════════════════════════
# BUSCA E GERENCIAMENTO
# ═══════════════════════════════════════════════════════════════════════════════
elif opcao == "Busca e Gerenciamento":
    st.title("🔍 Busca e Gerenciamento")
    tp, tc, tf, to = st.tabs(["📦 Produtos", "👤 Clientes", "🏭 Fornecedores", "🏢 Órgãos"])

    # ── Produtos ──────────────────────────────────────────────────────────────
    with tp:
        st.subheader("Localizar Produtos")
        # busca + status na mesma linha
        if "inp_bp" not in st.session_state:
            st.session_state["inp_bp"] = st.session_state.get("busca_prod", "")

        def limpar_busca_prod():
            st.session_state["busca_prod"] = ""
            st.session_state["inp_bp"] = ""

        c_busca, c_status, c_btn, c_limpar = st.columns([4, 2, 1, 1])
        termo_p = c_busca.text_input("Busca produto", placeholder="Nome, Patrimônio, Série, Marca, Prefixo da Viatura...",
                                     key="inp_bp", label_visibility="collapsed")
        fs = c_status.selectbox("Status", ["Todos", "Em estoque", "Críticos", "Zerados", "Aguardando entrada"],
                                 label_visibility="collapsed", key="sel_status_p")
        if c_btn.button("🔍", key="btn_bp", use_container_width=True):
            st.session_state["busca_prod"] = termo_p.strip(); st.rerun()

        c_limpar.button("Limpar", key="clr_bp", use_container_width=True, on_click=limpar_busca_prod)
        if termo_p.strip() != st.session_state.get("busca_prod", ""):
            st.session_state["busca_prod"] = termo_p.strip()
        b = st.session_state["busca_prod"].upper()
        conn = get_conn()
        q = ("""
             SELECT m.id, m.nome 'Material', m.quantidade 'Qtd', m.minimo 'Minimo',
                    m.patrimonio 'Patrimonio', m.num_serie 'Serie', m.imei 'IMEI',
                    m.numero_linha 'Numero da Linha', m.imei_chip 'IMEI do Chip',
                    m.lcm 'LCM', m.orgao 'Orgao', COALESCE(saidas.recibos,'') 'Nº Recibo',
                    COALESCE(saidas.clientes,'') 'Cliente Pago', m.marca 'Marca',
                    m.modelo 'Modelo', m.tipo_transceptor 'Tipo de Transceptor', m.entrada_registrada
             FROM materiais m
             LEFT JOIN (
                 SELECT material_id,
                        GROUP_CONCAT(DISTINCT num_recibo) recibos,
                        GROUP_CONCAT(DISTINCT entidade) clientes
                 FROM historico
                 WHERE tipo LIKE 'SA%'
                   AND tipo LIKE '%CLIENTE%'
                   AND material_id IS NOT NULL
                   AND COALESCE(num_recibo,'')<>''
                 GROUP BY material_id
             ) saidas ON saidas.material_id=m.id
             WHERE 1=1""")
        p = []
        campos_busca_prod = ("nome", "patrimonio", "num_serie", "marca", "modelo", "prefixo_viatura", "imei", "numero_linha", "imei_chip", "lcm", "orgao", "tipo_transceptor")
        filtro_busca_prod = " OR ".join([f"UPPER(COALESCE({campo},'')) LIKE ?" for campo in campos_busca_prod])
        filtro_busca_prod_m = " OR ".join([f"UPPER(COALESCE(m.{campo},'')) LIKE ?" for campo in campos_busca_prod])
        params_busca_prod = [f"%{b}%"] * len(campos_busca_prod)
        if b:
            q += f" AND ({filtro_busca_prod_m})"
            p += params_busca_prod
        if fs == "Em estoque": q += " AND m.quantidade>0"
        elif fs == "Críticos": q += " AND m.entrada_registrada=1 AND m.quantidade<=m.minimo AND m.minimo>0"
        elif fs == "Zerados":  q += " AND m.entrada_registrada=1 AND m.quantidade=0"
        elif fs == "Aguardando entrada": q += " AND COALESCE(m.entrada_registrada,0)=0"
        df_p = read_sql_query(q, conn, params=p); conn.close()
        df_p.columns = ["id", "Material", "Qtd", "Minimo", "Patrimonio", "Serie", "IMEI", "Numero da Linha", "IMEI do Chip", "LCM", "Orgao", "Nº Recibo", "Cliente Pago", "Marca", "Modelo", "Tipo de Transceptor", "EntradaRegistrada"]

        if df_p.empty:
            st.info("Nenhum produto encontrado.")
        else:
            df_vis = df_p.copy()
            df_vis.insert(
                1,
                "Situacao",
                df_vis.apply(
                    lambda row: "AGUARDANDO ENTRADA" if not row["EntradaRegistrada"] else ("ZERADO" if row["Qtd"] == 0 else ("ABAIXO DO MINIMO" if row["Minimo"] > 0 and row["Qtd"] <= row["Minimo"] else "OK")),
                    axis=1,
                ),
            )
            df_vis = df_vis.drop(columns=["id", "EntradaRegistrada"], errors="ignore")
            ordem_colunas_produtos = [
                "Situacao", "Material", "Qtd", "Minimo", "Patrimonio", "Serie", "IMEI",
                "Numero da Linha", "Nº Recibo", "IMEI do Chip", "LCM", "Orgao",
                "Cliente Pago", "Marca", "Modelo", "Tipo de Transceptor"
            ]
            df_vis = df_vis[[col for col in ordem_colunas_produtos if col in df_vis.columns]]
            df_vis = df_vis.fillna("")
            st.caption(f"{len(df_vis)} produto(s) encontrado(s).")
            for col in df_vis.columns:
                if col != "Nº Recibo":
                    df_vis[col] = df_vis[col].map(lambda v: escape(str(v)) if v != "" else "")
            recibos_encontrados = sorted({
                recibo.strip()
                for valor in df_vis["Nº Recibo"].tolist()
                for recibo in str(valor or "").split(",")
                if recibo and recibo.strip()
            })
            df_vis["Nº Recibo"] = df_vis["Nº Recibo"].map(recibos_para_texto_html)
            st.markdown(
                f"<div class='search-results-table'>{df_vis.to_html(index=False, escape=False)}</div>",
                unsafe_allow_html=True,
            )
            st.caption("AGUARDANDO ENTRADA = material base ainda sem entrada | ZERADO = item que ja teve entrada e esta com quantidade 0 | ABAIXO DO MINIMO = quantidade menor ou igual ao minimo | OK = estoque normal")
            recibo_aberto = st.session_state.get("recibo_busca_aberto", "")
            if recibos_encontrados:
                c_rec_sel, c_rec_btn, c_rec_busca, c_rec_busca_btn, c_rec_fechar = st.columns([2, 1, 2, 1, 1])
                recibo_sel = c_rec_sel.selectbox(
                    "Abrir recibo pela lista",
                    recibos_encontrados,
                    key="sel_recibo_busca_produtos",
                )
                if c_rec_btn.button("Abrir lista", key="btn_abrir_recibo_busca", use_container_width=True):
                    st.session_state["recibo_busca_aberto"] = recibo_sel
                    st.rerun()
                recibo_digitado = c_rec_busca.text_input(
                    "Buscar recibo por numero",
                    placeholder="Ex.: 2011/07/2026",
                    key="inp_recibo_busca_produtos",
                ).strip()
                if c_rec_busca_btn.button("Buscar", key="btn_buscar_recibo_digitado", use_container_width=True):
                    st.session_state["recibo_busca_aberto"] = re.sub(
                        r"^\s*recibo\s*",
                        "",
                        recibo_digitado,
                        flags=re.IGNORECASE,
                    ).strip()
                    st.rerun()
                if recibo_aberto and c_rec_fechar.button("Fechar", key="btn_fechar_recibo_busca_topo", use_container_width=True):
                    st.session_state["recibo_busca_aberto"] = ""
                    st.rerun()
                recibo_aberto = st.session_state.get("recibo_busca_aberto", "")
            if recibo_aberto:
                st.markdown("---")
                st.subheader(f"Recibo {recibo_aberto}")
                html_recibo_aberto = gerar_html_recibo_saida(recibo_aberto)
                if html_recibo_aberto:
                    mostrar_recibo_iframe(html_recibo_aberto, f"busca_{re.sub(r'[^A-Za-z0-9]+', '_', recibo_aberto)}")
                    if st.button("Fechar Recibo", key="fechar_recibo_busca"):
                        st.session_state["recibo_busca_aberto"] = ""
                        st.rerun()
                else:
                    st.warning("Recibo nao encontrado.")

        if is_admin():
            with st.expander("🛠️ Editar Material"):
                conn = get_conn()
                sql_lm = "SELECT id,nome,marca,modelo,patrimonio,num_serie,imei,numero_linha,imei_chip FROM materiais"
                params_lm = []
                if b:
                    sql_lm += f" WHERE {filtro_busca_prod}"
                    params_lm = params_busca_prod
                sql_lm += " ORDER BY nome,id"
                lm = conn.execute(sql_lm, params_lm).fetchall()
                conn.close()
                if lm:
                    mp = {f"ID {r[0]} | {r[1]} | {r[2] or ''} {r[3] or ''} | PAT:{r[4] or '-'} SER:{r[5] or '-'} IMEI:{r[6] or '-'} LINHA:{r[7] or '-'} CHIP:{r[8] or '-'}": r[0] for r in lm}
                    sel = st.selectbox("Selecione:", list(mp.keys()), key="ed_m")
                    conn = get_conn(); d = conn.execute("SELECT * FROM materiais WHERE id=?", (mp[sel],)).fetchone(); conn.close()
                    opcoes_tipo_transceptor = ["", "MOVEL", "FIXO", "PORTATIL", "REPETIDOR"]
                    tipo_transceptor_atual = (d[9] or "").strip().upper() if len(d) > 9 else ""
                    indice_tipo_transceptor = (
                        opcoes_tipo_transceptor.index(tipo_transceptor_atual)
                        if tipo_transceptor_atual in opcoes_tipo_transceptor
                        else 0
                    )
                    with st.form("form_edm"):
                        a, b_, c_ = st.columns(3)
                        nn  = a.text_input("Nome",     value=d[1])
                        nm  = b_.text_input("Marca",   value=d[6] or "")
                        nmo = c_.text_input("Modelo",  value=d[7] or "")
                        d_, e_, f_ = st.columns(3)
                        nq  = d_.number_input("Quantidade", value=d[2], min_value=0, step=1)
                        nmi = e_.number_input("Mínimo",     value=d[3], min_value=0, step=1)
                        nlo = f_.selectbox(
                            "Tipo de Transceptor",
                            opcoes_tipo_transceptor,
                            index=indice_tipo_transceptor,
                            format_func=lambda valor: valor if valor else "Escolha um tipo",
                        )
                        g_, h_, i_ = st.columns(3)
                        npatr = g_.text_input("Nº Patrimônio", value=d[4] or "")
                        nser  = h_.text_input("Nº Série", value=d[5] or "")
                        ncod = i_.text_input("Prefixo da Viatura", value=d[10] or "" if len(d) > 10 else "")
                        j_, k_, l_ = st.columns(3)
                        nimei = j_.text_input("IMEI", value=d[11] or "" if len(d) > 11 else "")
                        nlcm  = k_.text_input("LCM", value=d[12] or "" if len(d) > 12 else "")
                        norg  = l_.text_input("Órgão", value=d[13] or "" if len(d) > 13 else "")
                        m_, n_ = st.columns(2)
                        nlinha = m_.text_input("Número da linha", value=d[15] or "" if len(d) > 15 else "")
                        nimei_chip = n_.text_input("IMEI do chip", value=d[16] or "" if len(d) > 16 else "")
                        no  = st.text_area("Observações",   value=d[8] or "")
                        if st.form_submit_button("Atualizar", use_container_width=True):
                            dados_ids = {
                                "patrimonio": npatr,
                                "num_serie": nser,
                                "imei": nimei,
                                "numero_linha": nlinha,
                                "imei_chip": nimei_chip,
                            }
                            if not nn.strip():
                                st.error("Nome é obrigatório.")
                            elif (npatr.strip() or nser.strip() or nimei.strip() or nlinha.strip() or nimei_chip.strip()) and nq > 1:
                                st.error("Item com Patrimônio/Série/IMEI/Número da linha/IMEI do chip deve ter Quantidade = 0 ou 1.")
                            else:
                                erro_dup = validar_identificadores_material(dados_ids, ignorar_id=mp[sel])
                                if erro_dup:
                                    st.error(erro_dup)
                                else:
                                    conn = None
                                    try:
                                        conn = get_conn()
                                        conn.execute(
                                            "UPDATE materiais SET nome=?,patrimonio=?,num_serie=?,marca=?,modelo=?,quantidade=?,minimo=?,tipo_transceptor=?,prefixo_viatura=?,imei=?,lcm=?,orgao=?,observacoes=?,numero_linha=?,imei_chip=? WHERE id=?",
                                            (nn.strip().upper(), npatr.strip().upper(), nser.strip().upper(),
                                             nm.strip().upper(), nmo.strip().upper(), nq, nmi, nlo.strip().upper(),
                                             ncod.strip(), nimei.strip().upper(), nlcm.strip().upper(),
                                             norg.strip().upper(), no, nlinha.strip().upper(), nimei_chip.strip().upper(), mp[sel]))
                                        conn.commit(); conn.close(); conn = None
                                        registrar_log(st.session_state["usuario"], f"Editou material ID {mp[sel]}")
                                        confirmar_e_atualizar("Atualizado!")
                                    except psycopg.IntegrityError:
                                        st.error("Não foi possível atualizar: patrimônio, série, IMEI, número da linha ou IMEI do chip já existe em outro material.")
                                    finally:
                                        if conn:
                                            conn.close()

            with st.expander("🗑️ Excluir Material"):
                conn = get_conn()
                sql_ld = "SELECT id,nome FROM materiais"
                params_ld = []
                if b:
                    sql_ld += f" WHERE {filtro_busca_prod}"
                    params_ld = params_busca_prod
                sql_ld += " ORDER BY nome,id"
                ld = conn.execute(sql_ld, params_ld).fetchall(); conn.close()
                if ld:
                    md = {f"ID {r[0]} - {r[1]}": r[0] for r in ld}
                    sd = st.selectbox("Material:", list(md.keys()), key="del_ms")
                    cf = st.checkbox("Confirmo exclusão permanente", key="cf_del")
                    if st.button("🗑️ Excluir", key="btn_del_m") and cf:
                        conn = get_conn()
                        usado = conn.execute("SELECT COUNT(*) FROM historico WHERE material_id=?", (md[sd],)).fetchone()[0]
                        if usado:
                            conn.close()
                            st.error("Este material possui movimentações/recibos no histórico e não pode ser excluído. Zere ou edite o cadastro, mas preserve a rastreabilidade.")
                        else:
                            conn.execute("DELETE FROM materiais WHERE id=?", (md[sd],)); conn.commit(); conn.close()
                            registrar_log(st.session_state["usuario"], f"Excluiu: {sd}")
                            confirmar_e_atualizar("Excluído!")

        if b:
            st.markdown("---")
            st.subheader(f"Rastreio de saídas: {b}")
            conn = get_conn()
            dr = read_sql_query(
                "SELECT data_hora,entidade,quantidade,identificacao FROM historico "
                "WHERE tipo='SAÍDA (CLIENTE)' AND (material LIKE ? OR identificacao LIKE ?) ORDER BY id DESC",
                conn, params=(f"%{b}%",) * 2)
            conn.close()
            if dr.empty: st.info("Nenhuma saída encontrada.")
            else: tabela_visivel(dr)

    # ── Clientes ──────────────────────────────────────────────────────────────
    with tc:
        st.subheader("Localizar e Editar Clientes")
        b_cli = search_row("Cliente", "inp_bc", "btn_bc", "busca_cli", "Nome do cliente...")

        conn = get_conn()
        q2 = "SELECT id,nome,doc_fiscal,campo_re,telefone,email FROM clientes"
        p2 = []
        if b_cli: q2 += " WHERE nome LIKE ?"; p2.append(f"%{b_cli.upper()}%")
        lc = conn.execute(q2, p2).fetchall(); conn.close()

        if not lc: st.info("Nenhum cliente encontrado.")
        else:
            cd = {r[1]: {"id":r[0],"nome":r[1],"doc":r[2],"re":r[3],"tel":r[4],"email":r[5]} for r in lc}
            cs = st.selectbox("Selecione para editar:", list(cd.keys()), key="sel_c")
            dc = cd[cs]
            with st.form("form_ed_cli"):
                a, b_ = st.columns(2)
                nn = a.text_input("Nome",     value=dc["nome"]).strip().upper()
                nd = b_.text_input("CNPJ/CPF", value=dc["doc"] or "")
                c_, d_ = st.columns(2)
                nr = c_.text_input("RE",       value=dc["re"] or "")
                nt = d_.text_input("Telefone", value=dc["tel"] or "")
                ne = st.text_input("E-mail",   value=dc["email"] or "")
                if st.form_submit_button("Salvar", use_container_width=True):
                    conn = get_conn()
                    conn.execute("UPDATE clientes SET nome=?,doc_fiscal=?,campo_re=?,telefone=?,email=? WHERE id=?",
                                 (nn, nd, nr, nt, ne, dc["id"]))
                    conn.commit(); conn.close(); confirmar_e_atualizar("Atualizado!")
            if is_admin() and st.button("🗑️ Excluir Cliente", key="del_c"):
                if possui_movimentacao_entidade(dc["nome"]):
                    st.error("Cliente possui movimentação no histórico e não pode ser excluído.")
                else:
                    conn = get_conn(); conn.execute("DELETE FROM clientes WHERE id=?", (dc["id"],)); conn.commit(); conn.close()
                    registrar_log(st.session_state["usuario"], f"Excluiu cliente: {dc['nome']}")
                    confirmar_e_atualizar("Excluído!")

    # ── Fornecedores ──────────────────────────────────────────────────────────
    with tf:
        st.subheader("Localizar e Editar Fornecedores")
        b_forn = search_row("Fornecedor", "inp_bf", "btn_bf", "busca_forn", "Nome do fornecedor...")

        conn = get_conn()
        qf = "SELECT id,nome,telefone,cnpj,endereco,ramo,email FROM fornecedores"
        pf = []
        if b_forn: qf += " WHERE nome LIKE ?"; pf.append(f"%{b_forn.upper()}%")
        lf = conn.execute(qf, pf).fetchall(); conn.close()

        if not lf: st.info("Nenhum fornecedor encontrado.")
        else:
            fd = {r[1]: {"id":r[0],"nome":r[1],"tel":r[2],"cnpj":r[3],"end":r[4],"ramo":r[5],"email":r[6]} for r in lf}
            fs2 = st.selectbox("Selecione para editar:", list(fd.keys()), key="sel_f")
            df2 = fd[fs2]
            with st.form("form_ed_forn"):
                fa, fb = st.columns(2)
                nf  = fa.text_input("Nome",     value=df2["nome"]).strip().upper()
                tf2 = fb.text_input("Telefone", value=df2["tel"] or "")
                fc, fd_ = st.columns(2)
                nc  = fc.text_input("CNPJ",             value=df2["cnpj"] or "")
                ra  = fd_.text_input("Ramo de Atividade", value=df2["ramo"] or "")
                em  = st.text_input("E-mail",            value=df2["email"] or "")
                en  = st.text_input("Endereço",          value=df2["end"] or "")
                if st.form_submit_button("Salvar", use_container_width=True):
                    conn = get_conn()
                    conn.execute("UPDATE fornecedores SET nome=?,telefone=?,cnpj=?,endereco=?,ramo=?,email=? WHERE id=?",
                                 (nf, tf2, nc, en, ra, em, df2["id"]))
                    conn.commit(); conn.close(); confirmar_e_atualizar("Atualizado!")
            if is_admin() and st.button("🗑️ Excluir Fornecedor", key="del_f"):
                if possui_movimentacao_entidade(df2["nome"]):
                    st.error("Fornecedor possui movimentação no histórico e não pode ser excluído.")
                else:
                    conn = get_conn(); conn.execute("DELETE FROM fornecedores WHERE id=?", (df2["id"],)); conn.commit(); conn.close()
                    registrar_log(st.session_state["usuario"], f"Excluiu fornecedor: {df2['nome']}")
                    confirmar_e_atualizar("Excluído!")

    # ── Órgãos ───────────────────────────────────────────────────────────────
    with to:
        st.subheader("Localizar e Editar Órgãos")
        b_orgao = search_row("Órgão", "inp_bo", "btn_bo", "busca_orgao", "Nome do órgão...")

        conn = get_conn()
        qo = "SELECT id,nome FROM orgaos"
        po = []
        if b_orgao:
            qo += " WHERE UPPER(COALESCE(nome,'')) LIKE ?"
            po.append(f"%{b_orgao.upper()}%")
        qo += " ORDER BY nome"
        lo = conn.execute(qo, po).fetchall()
        conn.close()

        if not lo:
            st.info("Nenhum órgão encontrado.")
        else:
            df_org = pd.DataFrame(lo, columns=["id", "Nome"])
            st.caption(f"{len(df_org)} órgão(s) encontrado(s).")
            tabela_visivel(df_org.drop(columns=["id"]))

            od = {r[1]: {"id": r[0], "nome": r[1]} for r in lo}
            osel = st.selectbox("Selecione para editar:", list(od.keys()), key="sel_orgao")
            org = od[osel]
            with st.form("form_ed_orgao"):
                nome_orgao = st.text_input("Nome", value=org["nome"]).strip().upper()
                if st.form_submit_button("Salvar", use_container_width=True):
                    if not nome_orgao:
                        st.error("Nome é obrigatório.")
                    else:
                        conn = None
                        try:
                            conn = get_conn()
                            conn.execute("UPDATE orgaos SET nome=? WHERE id=?", (nome_orgao, org["id"]))
                            conn.execute(
                                "UPDATE materiais SET orgao=? WHERE UPPER(COALESCE(orgao,''))=?",
                                (nome_orgao, org["nome"].upper()),
                            )
                            conn.commit(); conn.close(); conn = None
                            registrar_log(st.session_state["usuario"], f"Editou órgão: {org['nome']} -> {nome_orgao}")
                            confirmar_e_atualizar("Órgão atualizado!")
                        except psycopg.IntegrityError:
                            st.error("Já existe um órgão cadastrado com esse nome.")
                        finally:
                            if conn:
                                conn.close()

# ═══════════════════════════════════════════════════════════════════════════════
# CADASTRAR MATERIAL
# ═══════════════════════════════════════════════════════════════════════════════
elif opcao == "Cadastrar Material":
    st.title("📦 Cadastrar Novo Material")
    st.caption("Cadastre aqui apenas os dados comuns do material. Patrimônio, série, IMEI e tipo de transceptor entram na tela Registrar Entrada.")
    with st.form("form_cad_mat", clear_on_submit=True):
        nome = st.text_input("Nome do Material *", placeholder="Ex: Notebook Dell Latitude")
        c1, c2 = st.columns(2)
        marca = c1.text_input("Marca", placeholder="Ex: Dell")
        modelo = c2.text_input("Modelo", placeholder="Ex: Latitude 5420")
        c3, c4 = st.columns(2)
        c3.metric("Estoque Inicial", 0)
        qtd = 0
        minimo = c4.number_input("Quantidade Minima", min_value=0, step=1, value=0)
        ok = st.form_submit_button("Cadastrar Material", use_container_width=True)

    if ok:
        nome = nome.strip().upper()
        marca = marca.strip().upper()
        modelo = modelo.strip().upper()
        if not nome:
            st.error("Nome e obrigatorio.")
        else:
            conn = None
            try:
                conn = get_conn()
                existente = conn.execute(
                    """
                    SELECT id, quantidade
                      FROM materiais
                     WHERE UPPER(TRIM(COALESCE(nome,'')))=?
                       AND UPPER(TRIM(COALESCE(marca,'')))=?
                       AND UPPER(TRIM(COALESCE(modelo,'')))=?
                       AND TRIM(COALESCE(patrimonio,''))=''
                       AND TRIM(COALESCE(num_serie,''))=''
                       AND TRIM(COALESCE(imei,''))=''
                       AND TRIM(COALESCE(numero_linha,''))=''
                       AND TRIM(COALESCE(imei_chip,''))=''
                     LIMIT 1
                    """,
                    (nome, marca, modelo),
                ).fetchone()
                if existente:
                    st.warning(f"Material base ja cadastrado para {nome} {marca} {modelo}. Use Registrar Entrada para somar quantidade.")
                    conn.close(); conn = None
                    st.stop()
                conn.execute(
                    "INSERT INTO materiais(nome,quantidade,minimo,patrimonio,num_serie,marca,modelo,observacoes,tipo_transceptor,prefixo_viatura,imei,lcm,orgao) "
                    "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (nome, qtd, minimo, "", "", marca, modelo, "", "", "", "", "", "")
                )
                conn.commit(); conn.close(); conn = None
                registrar_log(st.session_state["usuario"], f"Cadastrou material base: {nome}")
                st.success(f"Material base {nome} cadastrado com sucesso.")
            except psycopg.IntegrityError:
                st.error("Nao foi possivel cadastrar o material.")
            finally:
                if conn:
                    conn.close()

# ═══════════════════════════════════════════════════════════════════════════════
# CADASTRAR ORGAO
# ═══════════════════════════════════════════════════════════════════════════════
elif opcao == "Cadastrar Órgão":
    st.title("🏢 Cadastrar Novo Órgão")
    with st.form("form_cad_orgao", clear_on_submit=True):
        nome_orgao = st.text_input("Nome *", placeholder="Ex: 4ª CIA - TELEMÁTICA")
        ok = st.form_submit_button("Salvar Órgão", use_container_width=True)

    if ok:
        nome_orgao = nome_orgao.strip().upper()
        if not nome_orgao:
            st.error("Nome é obrigatório.")
        else:
            conn = None
            try:
                conn = get_conn()
                conn.execute("INSERT INTO orgaos(nome) VALUES(?)", (nome_orgao,))
                conn.commit(); conn.close(); conn = None
                registrar_log(st.session_state["usuario"], f"Cadastrou órgão: {nome_orgao}")
                st.success(f"Órgão '{nome_orgao}' cadastrado!")
            except psycopg.IntegrityError:
                st.error("Órgão já cadastrado.")
            finally:
                if conn:
                    conn.close()

# ════════════════════════════════════════════════════════════════════════════════
# REGISTRAR ENTRADA
# ════════════════════════════════════════════════════════════════════════════════
elif opcao == "Registrar Entrada":
    st.title("📥 Registrar Entrada de Fornecedor")

    # ── 1. Fornecedor ─────────────────────────────────────────────────────────
    st.subheader("1️⃣ Fornecedor")
    b_forn_e = search_row("Fornecedor", "inp_bfe", "btn_bfe", "busca_forn_entrada", "Buscar fornecedor...")

    conn = get_conn()
    bfe = b_forn_e.upper()
    lf_e = (conn.execute("SELECT nome FROM fornecedores WHERE nome LIKE ?", (f"%{bfe}%",)).fetchall()
            if bfe else conn.execute("SELECT nome FROM fornecedores").fetchall())
    conn.close()

    if not lf_e:
        st.info("Nenhum fornecedor encontrado. Cadastre primeiro.")
    else:
        opcoes_fornecedor_entrada = [None] + [r[0] for r in lf_e]
        if "forn_ent_placeholder_v2" not in st.session_state:
            st.session_state["forn_ent_sel"] = None
            st.session_state["forn_ent_placeholder_v2"] = True
        if st.session_state.get("forn_ent_sel") not in opcoes_fornecedor_entrada:
            st.session_state["forn_ent_sel"] = None
        forn_sel = st.selectbox(
            "Fornecedor *:",
            opcoes_fornecedor_entrada,
            key="forn_ent_sel",
            label_visibility="collapsed",
            format_func=lambda valor: valor if valor else "Selecione uma opção",
        )

        # ── 2. Material ───────────────────────────────────────────────────────
        st.subheader("2️⃣ Adicionar Itens")
        b_mat_e = search_row("Material entrada", "inp_bme", "btn_bme",
                              "busca_mat_entrada", "Buscar por nome, marca, modelo, serial, patrimônio, linha, chip...")

        bme = b_mat_e.strip()
        conn = get_conn()
        mats_e = (conn.execute(
            "SELECT id,nome,marca,modelo,patrimonio,num_serie,imei,lcm,orgao,minimo,tipo_transceptor,prefixo_viatura,observacoes,quantidade,entrada_registrada,numero_linha,imei_chip FROM materiais "
            "WHERE UPPER(COALESCE(nome,'')) LIKE UPPER(?) "
            "OR UPPER(COALESCE(marca,'')) LIKE UPPER(?) "
            "OR UPPER(COALESCE(modelo,'')) LIKE UPPER(?) "
            "OR UPPER(COALESCE(num_serie,'')) LIKE UPPER(?) "
            "OR UPPER(COALESCE(patrimonio,'')) LIKE UPPER(?) "
            "OR UPPER(COALESCE(prefixo_viatura,'')) LIKE UPPER(?) "
            "OR UPPER(COALESCE(imei,'')) LIKE UPPER(?) "
            "OR UPPER(COALESCE(lcm,'')) LIKE UPPER(?) "
            "OR UPPER(COALESCE(orgao,'')) LIKE UPPER(?) "
            "OR UPPER(COALESCE(numero_linha,'')) LIKE UPPER(?) "
            "OR UPPER(COALESCE(imei_chip,'')) LIKE UPPER(?) "
            "ORDER BY nome, marca, modelo, patrimonio, num_serie, imei, numero_linha, imei_chip, id",
            (f"%{bme}%",) * 11).fetchall()
            if bme else conn.execute("SELECT id,nome,marca,modelo,patrimonio,num_serie,imei,lcm,orgao,minimo,tipo_transceptor,prefixo_viatura,observacoes,quantidade,entrada_registrada,numero_linha,imei_chip FROM materiais ORDER BY nome, marca, modelo, patrimonio, num_serie, imei, numero_linha, imei_chip, id").fetchall())
        conn.close()

        if mats_e:
            def rotulo_material_entrada(row):
                partes = [row[1]]
                marca_modelo = " ".join(parte for parte in (row[2], row[3]) if parte)
                if marca_modelo:
                    partes.append(marca_modelo)
                detalhes = []
                if row[4]:
                    detalhes.append(f"Patrimonio: {row[4]}")
                if row[5]:
                    detalhes.append(f"Serie: {row[5]}")
                if row[6]:
                    detalhes.append(f"IMEI: {row[6]}")
                if row[7]:
                    detalhes.append(f"LCM: {row[7]}")
                if row[8]:
                    detalhes.append(f"Orgao: {row[8]}")
                if row[10]:
                    detalhes.append(f"Local: {row[10]}")
                if row[11]:
                    detalhes.append(f"Cod barras: {row[11]}")
                if len(row) > 15 and row[15]:
                    detalhes.append(f"Número da linha: {row[15]}")
                if len(row) > 16 and row[16]:
                    detalhes.append(f"IMEI do chip: {row[16]}")
                if detalhes:
                    partes.append(" | ".join(detalhes))
                elif not row[14]:
                    partes.append("Cadastro base sem entrada")
                partes.append(f"Qtd atual: {row[13]}")
                return " | ".join(partes)

            indices_mat_entrada = list(range(len(mats_e)))
            opcoes_mat_entrada = [None] + indices_mat_entrada
            busca_mat_entrada_auto = f"{b_mat_e.strip().upper()}|{len(mats_e)}|{mats_e[0][0] if mats_e else ''}"
            if st.session_state.get("mat_ent_auto_key") != busca_mat_entrada_auto:
                st.session_state["mat_ent_sel"] = indices_mat_entrada[0] if b_mat_e.strip() and indices_mat_entrada else None
                st.session_state["mat_ent_auto_key"] = busca_mat_entrada_auto
            if st.session_state.get("mat_ent_sel") not in opcoes_mat_entrada:
                st.session_state["mat_ent_sel"] = None

            idx_mat_e = st.selectbox(
                "Material cadastrado:",
                opcoes_mat_entrada,
                key="mat_ent_sel",
                format_func=lambda idx: "Selecione um item" if idx is None else rotulo_material_entrada(mats_e[idx]),
            )
            md = mats_e[idx_mat_e] if idx_mat_e is not None else None
            md_identificado = bool(
                md and any((md[idx] or "").strip() for idx in (4, 5, 6, 15, 16))
            )
            orgaos_entrada = listar_orgaos()
            if not orgaos_entrada:
                st.warning("Cadastre um órgão antes de adicionar itens na entrada.")

            reset_entrada = st.session_state.get("reset_form_entrada_item", 0)
            chave_form_entrada = f"{reset_entrada}_{md[0] if md else 'sem_material'}"
            orgao_atual = (md[8] or "").strip().upper() if md else ""
            opcoes_orgao_entrada = [""] + orgaos_entrada
            indice_orgao_entrada = (
                opcoes_orgao_entrada.index(orgao_atual)
                if orgao_atual in opcoes_orgao_entrada
                else 0
            )
            if md_identificado:
                st.info(
                    "Reentrada de item já cadastrado: os dados foram carregados do "
                    "estoque e a confirmação atualizará o mesmo cadastro."
                )
            opcoes_tipo_transceptor = ["", "MOVEL", "FIXO", "PORTATIL", "REPETIDOR"]
            tipo_transceptor_atual = (md[10] or "").strip().upper() if md else ""
            indice_tipo_transceptor = (
                opcoes_tipo_transceptor.index(tipo_transceptor_atual)
                if tipo_transceptor_atual in opcoes_tipo_transceptor
                else 0
            )
            with st.form("form_add_entrada_item"):
                c1, c2, c3 = st.columns(3)
                qtd_e = c1.number_input("Qtd entrada", min_value=1, step=1, value=1, disabled=md_identificado, key=f"entrada_qtd_{chave_form_entrada}")
                patri_e = c2.text_input("No Patrimonio", value=(md[4] or "") if md else "", disabled=md_identificado, key=f"entrada_patrimonio_{chave_form_entrada}")
                serial_e = c3.text_input("No serie", value=(md[5] or "") if md else "", disabled=md_identificado, key=f"entrada_serie_{chave_form_entrada}")
                c4, c5, c6 = st.columns(3)
                loc_e = c4.selectbox(
                    "Tipo de Transceptor",
                    opcoes_tipo_transceptor,
                    index=indice_tipo_transceptor,
                    format_func=lambda valor: valor if valor else "Escolha um tipo",
                    key=f"entrada_tipo_transceptor_{chave_form_entrada}",
                )
                cod_e = c5.text_input("Prefixo da Viatura", value=(md[11] or "") if md else "", key=f"entrada_prefixo_viatura_{chave_form_entrada}")
                imei_e = c6.text_input("IMEI", value=(md[6] or "") if md else "", disabled=md_identificado, key=f"entrada_imei_{chave_form_entrada}")
                c7, c8, c9 = st.columns(3)
                lcm_e = c7.text_input("LCM", value=(md[7] or "") if md else "", key=f"entrada_lcm_{chave_form_entrada}")
                numero_linha_e = c8.text_input("Número da linha", value=(md[15] or "") if md else "", disabled=md_identificado, key=f"entrada_numero_linha_{chave_form_entrada}")
                imei_chip_e = c9.text_input("IMEI do chip", value=(md[16] or "") if md else "", disabled=md_identificado, key=f"entrada_imei_chip_{chave_form_entrada}")
                orgao_e = st.selectbox(
                    "Órgão *",
                    opcoes_orgao_entrada,
                    index=indice_orgao_entrada,
                    format_func=lambda valor: valor if valor else "Selecione o órgão",
                    disabled=not orgaos_entrada,
                    key=f"entrada_orgao_{chave_form_entrada}",
                )
                obs_e = st.text_area("Observacoes", value=(md[12] or "") if md else "", key=f"entrada_obs_{chave_form_entrada}")
                add_item = st.form_submit_button("Adicionar item a entrada", use_container_width=True)

            if add_item:
                patri_e = patri_e.strip().upper()
                serial_e = serial_e.strip().upper()
                imei_e = imei_e.strip().upper()
                numero_linha_e = numero_linha_e.strip().upper()
                imei_chip_e = imei_chip_e.strip().upper()
                orgao_e = (orgao_e or "").strip().upper()
                dados_ids = {
                    "patrimonio": patri_e,
                    "num_serie": serial_e,
                    "imei": imei_e,
                    "numero_linha": numero_linha_e,
                    "imei_chip": imei_chip_e,
                }
                if not forn_sel:
                    st.error("Fornecedor é campo obrigatório para registrar entrada.")
                elif md is None:
                    st.error("Selecione um item cadastrado.")
                elif not orgao_e:
                    st.error("Órgão é campo obrigatório para registrar entrada.")
                elif (patri_e or serial_e or imei_e or numero_linha_e or imei_chip_e) and qtd_e > 1:
                    st.error("Item com Patrimonio/Serie/IMEI/Número da linha/IMEI do chip deve ser unitario.")
                elif md_identificado and int(md[13] or 0) > 0:
                    st.error("Este item identificado já consta em estoque. A reentrada só pode ser registrada quando a quantidade atual for zero.")
                else:
                    erro_dup = validar_identificadores_material(
                        dados_ids,
                        ignorar_id=md[0] if md_identificado else None,
                    )
                    if erro_dup:
                        st.error(erro_dup)
                    elif any(
                        (patri_e and item.get("patri") == patri_e) or
                        (serial_e and item.get("serial") == serial_e) or
                        (imei_e and item.get("imei") == imei_e) or
                        (numero_linha_e and item.get("numero_linha") == numero_linha_e) or
                        (imei_chip_e and item.get("imei_chip") == imei_chip_e)
                        for item in st.session_state["entradas_temp"]
                    ):
                        st.error("Patrimonio, serie, IMEI, número da linha ou IMEI do chip ja foi adicionado nesta entrada.")
                    else:
                        novo_item = {
                            "id": md[0], "nome": md[1], "marca": md[2] or "", "modelo": md[3] or "",
                            "minimo": md[9] or 0, "quantidade": qtd_e,
                            "reentrada_existente": md_identificado,
                            "patri": patri_e, "serial": serial_e, "tipo_transceptor": loc_e.strip().upper(),
                            "prefixo_viatura": cod_e.strip(), "imei": imei_e, "lcm": lcm_e.strip().upper(),
                            "orgao": orgao_e, "numero_linha": numero_linha_e,
                            "imei_chip": imei_chip_e, "obs": obs_e.strip()
                        }
                        if material_tem_identificador_unico(novo_item):
                            st.session_state["entradas_temp"].append(novo_item)
                        else:
                            existente = next(
                                (
                                    item for item in st.session_state["entradas_temp"]
                                    if not material_tem_identificador_unico(item)
                                    and item.get("nome") == novo_item["nome"]
                                    and item.get("marca", "") == novo_item["marca"]
                                    and item.get("modelo", "") == novo_item["modelo"]
                                ),
                                None,
                            )
                            if existente:
                                existente["quantidade"] += novo_item["quantidade"]
                                for campo in ("tipo_transceptor", "prefixo_viatura", "lcm", "orgao", "obs"):
                                    if novo_item.get(campo) and not existente.get(campo):
                                        existente[campo] = novo_item[campo]
                            else:
                                st.session_state["entradas_temp"].append(novo_item)
                        st.session_state["reset_form_entrada_item"] = reset_entrada + 1
                        confirmar_e_atualizar(f"{md[1]} adicionado!")

        else:
            st.info("Nenhum material encontrado. Cadastre o material base primeiro.")

        st.subheader("3️⃣ Itens a Dar Entrada")
        if not st.session_state["entradas_temp"]:
            st.info("Nenhum item adicionado.")
        else:
            for item_temp in st.session_state["entradas_temp"]:
                for campo in ("minimo", "tipo_transceptor", "prefixo_viatura", "imei", "lcm", "orgao", "numero_linha", "imei_chip", "obs"):
                    item_temp.setdefault(campo, "" if campo != "minimo" else 0)
            df_ent = pd.DataFrame(st.session_state["entradas_temp"])[["nome","marca","modelo","quantidade","patri","serial","tipo_transceptor","prefixo_viatura","imei","numero_linha","imei_chip","lcm","orgao","obs"]]
            df_ent.columns = ["Material","Marca","Modelo","Qtd","Patrimonio","Serie","Tipo de Transceptor","Prefixo da Viatura","IMEI","Numero da Linha","IMEI do Chip","LCM","Orgao","Obs"]
            tabela_visivel(df_ent)

            def rotulo_item_entrada(idx, item):
                ident = item.get("patri") or item.get("serial") or item.get("imei") or item.get("numero_linha") or item.get("imei_chip") or item.get("prefixo_viatura") or "SEM IDENTIFICADOR"
                marca_modelo = " ".join(parte for parte in (item.get("marca"), item.get("modelo")) if parte)
                detalhe = f" | {marca_modelo}" if marca_modelo else ""
                return f"{idx + 1}. {item['nome']}{detalhe} | Qtd:{item['quantidade']} | {ident}"

            nms = [rotulo_item_entrada(i, c) for i, c in enumerate(st.session_state["entradas_temp"])]
            ri1, ri2 = st.columns(2)
            ir = ri1.selectbox("Remover item:", range(len(nms)), key="rem_ent", label_visibility="collapsed",
                               format_func=lambda idx: nms[idx])
            if ri1.button("🗑️ Remover item", key="btn_rem_ent", use_container_width=True):
                st.session_state["entradas_temp"].pop(ir); st.rerun()
            if ri2.button("🧹 Limpar todos", key="btn_lim_ent", use_container_width=True):
                st.session_state["entradas_temp"] = []; st.rerun()

            if st.button("✅ Confirmar Entradas", type="primary", use_container_width=True):
                if not forn_sel:
                    st.error("Fornecedor é campo obrigatório para confirmar a entrada.")
                    st.stop()
                dt = datetime.now().strftime("%d/%m/%Y %H:%M")
                conn = get_conn()
                for it in st.session_state["entradas_temp"]:
                    ident = it["patri"] or it["serial"] or it["imei"] or it["numero_linha"] or it["imei_chip"] or it["prefixo_viatura"] or "Lote"
                    tem_identificador_unico = material_tem_identificador_unico(it)
                    material_id_hist = it["id"]
                    if it.get("reentrada_existente"):
                        cur_mat = conn.execute(
                            """
                            UPDATE materiais
                               SET quantidade=quantidade+?,
                                   entrada_registrada=1,
                                   tipo_transceptor=?,
                                   prefixo_viatura=?,
                                   lcm=?,
                                   orgao=?,
                                   observacoes=?
                             WHERE id=? AND quantidade=0
                            """,
                            (
                                it["quantidade"], it["tipo_transceptor"], it["prefixo_viatura"],
                                it["lcm"], it["orgao"], it["obs"], material_id_hist,
                            ),
                        )
                        if cur_mat.rowcount != 1:
                            conn.rollback()
                            conn.close()
                            st.error(
                                f"Não foi possível dar reentrada em {it['nome']}: "
                                "o item já consta em estoque ou foi alterado por outro usuário."
                            )
                            st.stop()
                    elif tem_identificador_unico:
                        cur_mat = conn.execute(
                            "INSERT INTO materiais(nome,quantidade,minimo,patrimonio,num_serie,marca,modelo,observacoes,tipo_transceptor,prefixo_viatura,imei,lcm,orgao,entrada_registrada,numero_linha,imei_chip) "
                            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,1,?,?)",
                            (it["nome"], it["quantidade"], it["minimo"], it["patri"], it["serial"],
                             it["marca"], it["modelo"], it["obs"], it["tipo_transceptor"], it["prefixo_viatura"],
                             it["imei"], it["lcm"], it["orgao"], it["numero_linha"], it["imei_chip"])
                        )
                        material_id_hist = cur_mat.lastrowid
                    else:
                        row_generico = localizar_material_generico_entrada(conn, it)
                        material_id_hist = row_generico[0] if row_generico else it["id"]
                        conn.execute(
                            """
                            UPDATE materiais
                               SET quantidade=quantidade+?,
                                   minimo=MAX(COALESCE(minimo,0), ?),
                                   entrada_registrada=1,
                                   tipo_transceptor=CASE WHEN TRIM(COALESCE(tipo_transceptor,''))='' THEN ? ELSE tipo_transceptor END,
                                   prefixo_viatura=CASE WHEN TRIM(COALESCE(prefixo_viatura,''))='' THEN ? ELSE prefixo_viatura END,
                                   lcm=CASE WHEN TRIM(COALESCE(lcm,''))='' THEN ? ELSE lcm END,
                                   orgao=CASE WHEN TRIM(COALESCE(orgao,''))='' THEN ? ELSE orgao END,
                                   observacoes=CASE WHEN TRIM(COALESCE(observacoes,''))='' THEN ? ELSE observacoes END
                             WHERE id=?
                            """,
                            (
                                it["quantidade"], it["minimo"], it["tipo_transceptor"],
                                it["prefixo_viatura"], it["lcm"], it["orgao"], it["obs"],
                                material_id_hist,
                            ),
                        )
                    conn.execute(
                        "INSERT INTO historico(material_id,tipo,material,quantidade,entidade,identificacao,marca,modelo,observacoes,data_hora) VALUES(?,?,?,?,?,?,?,?,?,?)",
                        (material_id_hist,
                         "REENTRADA (DEVOLUÇÃO)" if it.get("reentrada_existente") else "ENTRADA (FORNECEDOR)",
                         it["nome"], it["quantidade"],
                         forn_sel, ident, it["marca"], it["modelo"], it["obs"], dt)
                    )
                conn.commit(); conn.close()
                registrar_log(st.session_state["usuario"],
                              f"Entrada de {len(st.session_state['entradas_temp'])} item(ns) de {forn_sel}")
                st.session_state["entradas_temp"] = []
                st.session_state["busca_mat_entrada"] = ""
                confirmar_e_atualizar("✅ Entradas registradas!")

# ═══════════════════════════════════════════════════════════════════════════════
# REGISTRAR SAÍDA
# ═══════════════════════════════════════════════════════════════════════════════
elif opcao == "Registrar Saída":
    st.title("📤 Registrar Saída para Cliente")
    if not isinstance(st.session_state["carrinho"], list):
        st.session_state["carrinho"] = []

    saida_form_seq = st.session_state.get("saida_form_seq", 0)

    # ── 1. Cliente ────────────────────────────────────────────────────────────
    st.subheader("1️⃣ Cliente")
    b_cli_s = search_row(
        "Cliente saída",
        f"inp_bcs_{saida_form_seq}",
        f"btn_bcs_{saida_form_seq}",
        f"busca_cli_saida_{saida_form_seq}",
        "Buscar cliente...",
    )

    conn = get_conn()
    bcs = b_cli_s.upper()
    clientes_s = (conn.execute("SELECT nome FROM clientes WHERE nome LIKE ?", (f"%{bcs}%",)).fetchall()
                  if bcs else conn.execute("SELECT nome FROM clientes").fetchall())
    conn.close()

    if not clientes_s:
        st.info("Nenhum cliente encontrado. Cadastre primeiro."); st.stop()
    opcoes_clientes_saida = [r[0] for r in clientes_s]
    chave_cliente_saida = f"cli_saida_sel_{saida_form_seq}"

    # Quando a busca encontra somente um cliente, já o seleciona. Antes, o
    # resultado ficava escondido no selectbox e exigia abrir a lista.
    if bcs and len(opcoes_clientes_saida) == 1:
        st.session_state[chave_cliente_saida] = opcoes_clientes_saida[0]
    elif st.session_state.get(chave_cliente_saida, "") not in opcoes_clientes_saida:
        st.session_state[chave_cliente_saida] = ""

    cli_sel_s = st.selectbox(
        "Cliente:",
        [""] + opcoes_clientes_saida,
        key=chave_cliente_saida,
        label_visibility="collapsed",
        format_func=lambda valor: valor if valor else "Escolha as opções",
    )

    # ── 2. Material ───────────────────────────────────────────────────────────
    st.subheader("2️⃣ Adicionar Itens")
    b_mat_s = search_row(
        "Material saída",
        f"inp_bms_{saida_form_seq}",
        f"btn_bms_{saida_form_seq}",
        f"busca_mat_saida_{saida_form_seq}",
        "Buscar por nome, marca, modelo, serial, patrimônio, linha, chip...",
    )

    bms = b_mat_s.upper()
    conn = get_conn()
    banco = (conn.execute(
        "SELECT id,nome,quantidade,patrimonio,num_serie,marca,modelo,imei,lcm,orgao,numero_linha,imei_chip FROM materiais "
        "WHERE entrada_registrada=1 AND quantidade>0 AND (nome LIKE ? OR marca LIKE ? OR modelo LIKE ? OR num_serie LIKE ? OR patrimonio LIKE ? OR prefixo_viatura LIKE ? OR imei LIKE ? OR lcm LIKE ? OR orgao LIKE ? OR numero_linha LIKE ? OR imei_chip LIKE ?)",
        (f"%{bms}%",) * 11).fetchall()
        if bms else conn.execute("SELECT id,nome,quantidade,patrimonio,num_serie,marca,modelo,imei,lcm,orgao,numero_linha,imei_chip FROM materiais WHERE entrada_registrada=1 AND quantidade>0").fetchall())
    conn.close()

    if banco:
        itens_saida = []
        for r in banco:
            id_, n, q, p, s, m, mo, imei, lcm, orgao, numero_linha, imei_chip = r
            itens_saida.append({
                "id": id_, "nome": n, "qtd_max": q, "patri": p or "", "serial": s or "",
                "marca": m or "", "modelo": mo or "", "imei": imei or "", "lcm": lcm or "",
                "orgao": orgao or "", "numero_linha": numero_linha or "", "imei_chip": imei_chip or "",
            })

        def rotulo_material_saida(idx):
            item = itens_saida[idx]
            qtd_no_carrinho = sum(c["quantidade"] for c in st.session_state["carrinho"] if c["id"] == item["id"])
            restante = max(0, item["qtd_max"] - qtd_no_carrinho)
            partes = [item["nome"]]
            if qtd_no_carrinho:
                partes.insert(0, f"[NO CARRINHO: {qtd_no_carrinho}]")
            marca_modelo = " ".join(parte for parte in (item["marca"], item["modelo"]) if parte)
            if marca_modelo:
                partes.append(marca_modelo)
            identificadores = []
            if item["patri"]:
                identificadores.append(f"Patrimonio: {item['patri']}")
            if item["serial"]:
                identificadores.append(f"Serie: {item['serial']}")
            if item["imei"]:
                identificadores.append(f"IMEI: {item['imei']}")
            if item["numero_linha"]:
                identificadores.append(f"Número da linha: {item['numero_linha']}")
            if item["imei_chip"]:
                identificadores.append(f"IMEI do chip: {item['imei_chip']}")
            if item["lcm"]:
                identificadores.append(f"LCM: {item['lcm']}")
            if item["orgao"]:
                identificadores.append(f"Orgao: {item['orgao']}")
            if identificadores:
                partes.append(" | ".join(identificadores))
            if qtd_no_carrinho:
                partes.append(f"Restante: {restante}")
            else:
                partes.append(f"Qtd disponivel: {item['qtd_max']}")
            return " | ".join(partes)

        def adicionar_item_carrinho(item, quantidade=1):
            no_cart = sum(c["quantidade"] for c in st.session_state["carrinho"] if c["id"] == item["id"])
            disp = max(0, item["qtd_max"] - no_cart)
            if disp <= 0:
                return False
            qtd_add = min(quantidade, disp)
            ex = next((c for c in st.session_state["carrinho"] if c["id"] == item["id"]), None)
            if ex:
                ex["quantidade"] = min(ex["quantidade"] + qtd_add, item["qtd_max"])
            else:
                st.session_state["carrinho"].append({
                    "id": item["id"], "nome": item["nome"], "quantidade": qtd_add,
                    "patri": item["patri"], "serial": item["serial"],
                    "marca": item["marca"], "modelo": item["modelo"], "imei": item["imei"],
                    "lcm": item["lcm"], "orgao": item["orgao"], "numero_linha": item["numero_linha"],
                    "imei_chip": item["imei_chip"], "qtd_max": item["qtd_max"],
                })
            return True

        opcoes_item_saida = list(range(len(itens_saida)))
        busca_item_auto = f"{b_mat_s.strip().upper()}|{len(itens_saida)}|{itens_saida[0]['id'] if itens_saida else ''}"
        item_saida_key = f"item_s_{saida_form_seq}"
        item_saida_auto_key = f"item_s_auto_key_{saida_form_seq}"
        if st.session_state.get(item_saida_auto_key) != busca_item_auto:
            st.session_state[item_saida_key] = opcoes_item_saida[0] if b_mat_s.strip() and opcoes_item_saida else None
            st.session_state[item_saida_auto_key] = busca_item_auto
        if st.session_state.get(item_saida_key) not in opcoes_item_saida:
            st.session_state[item_saida_key] = None

        si1, si2, si3 = st.columns([5, 1, 1])
        idx_sel = si1.selectbox(
            "Item:",
            opcoes_item_saida,
            key=item_saida_key,
            index=None,
            placeholder="Escolha o produto",
            label_visibility="collapsed",
            format_func=rotulo_material_saida,
        )
        d_it = itens_saida[idx_sel] if idx_sel is not None else None
        no_cart = sum(c["quantidade"] for c in st.session_state["carrinho"] if d_it and c["id"] == d_it["id"])
        disp = max(0, d_it["qtd_max"] - no_cart) if d_it else 0
        qtd_s = si2.number_input("Qtd", min_value=1, max_value=max(1, disp), step=1,
                                  key=f"qtd_s_{saida_form_seq}", label_visibility="collapsed", disabled=d_it is None)
        if si3.button("➕", key=f"add_s_{saida_form_seq}", use_container_width=True):
            if d_it is None:
                st.warning("Escolha o produto antes de adicionar.")
            elif disp <= 0:
                st.warning("Este item já está no carrinho aguardando confirmação.")
            else:
                adicionar_item_carrinho(d_it, qtd_s)
                confirmar_e_atualizar(f"'{d_it['nome']}' adicionado/atualizado no carrinho.")

        st.caption("Seleção múltipla: marque vários itens abaixo e envie todos para o carrinho de uma vez.")
        multi_saida_key = f"itens_saida_multi_{saida_form_seq}_{st.session_state.get('multi_saida_seq', 0)}"
        sel_mult = st.multiselect(
            "Selecionar vários itens:",
            range(len(itens_saida)),
            key=multi_saida_key,
            label_visibility="collapsed",
            format_func=rotulo_material_saida,
            placeholder="Escolha as opções",
        )
        if st.button("➕ Adicionar itens selecionados ao carrinho", key=f"add_mult_s_{saida_form_seq}", use_container_width=True):
            if not sel_mult:
                st.warning("Selecione pelo menos um item.")
            else:
                adicionados = 0
                ignorados = 0
                for idx_multi in sel_mult:
                    if adicionar_item_carrinho(itens_saida[idx_multi], 1):
                        adicionados += 1
                    else:
                        ignorados += 1
                st.session_state["multi_saida_seq"] = st.session_state.get("multi_saida_seq", 0) + 1
                if adicionados:
                    st.success(f"{adicionados} item(ns) adicionado(s) ao carrinho.")
                if ignorados:
                    st.warning(f"{ignorados} item(ns) ignorado(s), pois já estavam no carrinho ou sem saldo restante.")
                st.rerun()

    # ── 3. Carrinho ───────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("3️⃣ Carrinho")
    if not st.session_state["carrinho"]:
        st.info("Nenhum item adicionado ao carrinho.")
    else:
        for c in st.session_state["carrinho"]:
            c.setdefault("imei", "")
            c.setdefault("lcm", "")
            c.setdefault("orgao", "")
            c.setdefault("numero_linha", "")
            c.setdefault("imei_chip", "")
        df_c = pd.DataFrame(st.session_state["carrinho"])[["nome","marca","modelo","quantidade","patri","serial","imei","numero_linha","imei_chip","lcm","orgao"]]
        df_c.columns = ["Material","Marca","Modelo","Qtd","Patrimônio","Nº Série","IMEI","Número da Linha","IMEI do Chip","LCM","Órgão"]
        tabela_visivel(df_c)

        cr1, cr2 = st.columns(2)
        def rotulo_item_saida(idx, item):
            ids = []
            if item.get("patri"):
                ids.append(f"Patrimonio: {item['patri']}")
            if item.get("serial"):
                ids.append(f"Serie: {item['serial']}")
            if item.get("imei"):
                ids.append(f"IMEI: {item['imei']}")
            if item.get("numero_linha"):
                ids.append(f"Número da linha: {item['numero_linha']}")
            if item.get("imei_chip"):
                ids.append(f"IMEI do chip: {item['imei_chip']}")
            ident = " | ".join(ids) if ids else "SEM IDENTIFICADOR"
            marca_modelo = " ".join(parte for parte in (item.get("marca"), item.get("modelo")) if parte)
            detalhe = f" | {marca_modelo}" if marca_modelo else ""
            return f"{idx + 1}. {item['nome']}{detalhe} | Qtd:{item['quantidade']} | {ident}"

        nms_c = [rotulo_item_saida(i, c) for i, c in enumerate(st.session_state["carrinho"])]
        ir_c = cr1.selectbox("Remover:", range(len(nms_c)), key=f"rem_c_{saida_form_seq}", label_visibility="collapsed",
                             format_func=lambda idx: nms_c[idx])
        if cr1.button("🗑️ Remover item",   key=f"btn_rem_c_{saida_form_seq}", use_container_width=True):
            st.session_state["carrinho"].pop(ir_c); st.rerun()
        if cr2.button("🧹 Limpar carrinho", key=f"btn_lim_c_{saida_form_seq}", use_container_width=True):
            st.session_state["carrinho"] = []; st.rerun()

        obs_s = st.text_area("Observações (aparecerá no recibo):", key=f"obs_saida_{saida_form_seq}",
                              placeholder="Informações adicionais sobre esta saída...")
        st.markdown("---")
        if st.button("✅ Confirmar Saída e Gerar Recibo", type="primary", use_container_width=True):
            if not cli_sel_s:
                st.error("Selecione um cliente antes de confirmar a saída.")
                st.stop()
            dt = datetime.now().strftime("%d/%m/%Y %H:%M")
            conn = get_conn()
            erro_estoque = None
            try:
                conn.execute("BEGIN IMMEDIATE")
                seq = proximo_recibo(conn)
                nr = formatar_num_recibo(seq)
                for it in st.session_state["carrinho"]:
                    ident = it["patri"] or it["serial"] or it.get("imei") or it.get("numero_linha") or it.get("imei_chip") or "Marca/Modelo"
                    cur = conn.execute(
                        "UPDATE materiais SET quantidade=quantidade-? WHERE id=? AND quantidade>=?",
                        (it["quantidade"], it["id"], it["quantidade"]),
                    )
                    if cur.rowcount == 0:
                        erro_estoque = f"Estoque insuficiente ou item indisponível: {it['nome']} {it.get('marca','')} {it.get('modelo','')}"
                        break
                    conn.execute(
                        "INSERT INTO historico(material_id,tipo,material,quantidade,entidade,identificacao,marca,modelo,observacoes,data_hora,num_recibo,seq_recibo) "
                        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                        (it["id"], "SAÍDA (CLIENTE)", it["nome"], it["quantidade"], cli_sel_s,
                         ident, it["marca"], it["modelo"], obs_s, dt, nr, seq))
                if erro_estoque:
                    conn.rollback()
                else:
                    conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
            if erro_estoque:
                st.error(erro_estoque)
                st.stop()
            registrar_log(st.session_state["usuario"], f"Saída recibo {nr} para {cli_sel_s}")
            itens_rec = [{"nome":c["nome"],"marca":c["marca"],"modelo":c["modelo"],
                          "quantidade":c["quantidade"],"patrimonio":c["patri"],"num_serie":c["serial"],
                          "imei":c.get("imei",""),"numero_linha":c.get("numero_linha",""),"imei_chip":c.get("imei_chip","")}
                         for c in st.session_state["carrinho"]]
            st.session_state["ultimo_recibo_html"] = html_recibo(itens_rec, cli_sel_s, "SAÍDA (CLIENTE)", nr, obs_s)
            st.session_state["ultimo_recibo_num"] = nr
            st.session_state["carrinho"] = []
            st.session_state["saida_form_seq"] = saida_form_seq + 1
            st.session_state["multi_saida_seq"] = st.session_state.get("multi_saida_seq", 0) + 1
            confirmar_e_atualizar(f"✅ Saída registrada! Recibo Nº {nr}")

    if st.session_state.get("ultimo_recibo_html"):
        st.markdown("---"); st.subheader("🖨️ Recibo Gerado")
        mostrar_recibo_iframe(st.session_state["ultimo_recibo_html"], "saida")
        if st.button("❌ Fechar Recibo"):
            st.session_state["ultimo_recibo_html"] = ""
            st.session_state["ultimo_recibo_num"] = ""
            st.rerun()

    st.markdown("---")
    editor_recibo_saida("")

# ═══════════════════════════════════════════════════════════════════════════════
# CADASTRAR CLIENTE
# ═══════════════════════════════════════════════════════════════════════════════
elif opcao == "Cadastrar Cliente":
    st.title("👤 Cadastrar Novo Cliente")
    with st.form("form_cad_cli", clear_on_submit=True):
        nome = st.text_input("Nome *", placeholder="Nome completo ou razão social")
        c1, c2 = st.columns(2)
        doc  = c1.text_input("CNPJ ou CPF")
        re   = c2.text_input("RE")
        c3, c4 = st.columns(2)
        tel   = c3.text_input("Telefone")
        email = c4.text_input("E-mail")
        ok = st.form_submit_button("✅ Salvar Cliente", use_container_width=True)
    if ok:
        if not nome.strip(): st.error("Nome é obrigatório.")
        else:
            try:
                conn = get_conn()
                conn.execute("INSERT INTO clientes(nome,doc_fiscal,campo_re,telefone,email) VALUES(?,?,?,?,?)",
                             (nome.strip().upper(), doc, re, tel, email))
                conn.commit(); conn.close()
                registrar_log(st.session_state["usuario"], f"Cadastrou cliente: {nome}")
                st.success(f"Cliente '{nome.upper()}' cadastrado!")
            except psycopg.IntegrityError: st.error("Cliente já cadastrado.")

# ═══════════════════════════════════════════════════════════════════════════════
# CADASTRAR FORNECEDOR
# ═══════════════════════════════════════════════════════════════════════════════
elif opcao == "Cadastrar Fornecedor":
    st.title("🏭 Cadastrar Novo Fornecedor")
    with st.form("form_cad_forn", clear_on_submit=True):
        c1, c2 = st.columns(2)
        nome = c1.text_input("Nome *",    placeholder="Razão social")
        tel  = c2.text_input("Telefone",  placeholder="(11) 99999-9999")
        c3, c4 = st.columns(2)
        cnpj = c3.text_input("CNPJ",      placeholder="00.000.000/0001-00")
        email = st.text_input("E-mail", placeholder="contato@fornecedor.com")
        ramo = c4.text_input("Ramo de Atividade", placeholder="Ex: Informática")
        end  = st.text_input("Endereço Completo",  placeholder="Rua, número, cidade...")
        ok = st.form_submit_button("✅ Salvar Fornecedor", use_container_width=True)
    if ok:
        if not nome.strip(): st.error("Nome é obrigatório.")
        else:
            try:
                conn = get_conn()
                conn.execute("INSERT INTO fornecedores(nome,telefone,cnpj,endereco,ramo,email) VALUES(?,?,?,?,?,?)",
                             (nome.strip().upper(), tel, cnpj, end, ramo, email))
                conn.commit(); conn.close()
                registrar_log(st.session_state["usuario"], f"Cadastrou fornecedor: {nome}")
                st.success(f"Fornecedor '{nome.upper()}' cadastrado!")
            except psycopg.IntegrityError: st.error("Fornecedor já cadastrado.")

# ═══════════════════════════════════════════════════════════════════════════════
# HISTÓRICO E RECIBOS
# ═══════════════════════════════════════════════════════════════════════════════
elif opcao == "Histórico e Recibos":
    st.title("📋 Histórico e Recibos")
    conn = get_conn()
    dh = read_sql_query(
        "SELECT id 'ID',data_hora 'Data/Hora',tipo 'Tipo',material 'Material',identificacao 'Pat/Ser',"
        "quantidade 'Qtd',entidade 'Origem/Destino',num_recibo 'Nº Recibo' "
        "FROM historico ORDER BY id DESC", conn)
    conn.close()

    if dh.empty:
        st.info("Sem registros.")
    else:
        tf_h = st.selectbox("Filtrar:", ["Todos","ENTRADA (FORNECEDOR)","SAÍDA (CLIENTE)"])
        df_fh = dh if tf_h == "Todos" else dh[dh["Tipo"] == tf_h]
        tabela_visivel(df_fh)

        if is_admin():
            with st.expander("🗑️ Excluir entradas ou saídas"):
                st.warning("A exclusão remove os registros do histórico/recibos. O saldo atual do estoque não é recalculado automaticamente.")
                tipo_del = st.selectbox(
                    "Tipo de movimentação:",
                    ["ENTRADA (FORNECEDOR)", "SAÍDA (CLIENTE)"],
                    key="tipo_excluir_mov",
                )
                df_del = dh[dh["Tipo"] == tipo_del].copy()
                if df_del.empty:
                    st.info("Nenhum registro encontrado para este tipo.")
                else:
                    opcoes_del = {
                        f"ID {int(r['ID'])} | {r['Data/Hora']} | {r['Material']} | Qtd:{r['Qtd']} | {r['Origem/Destino']} | Recibo:{r['Nº Recibo'] or '-'}": int(r["ID"])
                        for _, r in df_del.iterrows()
                    }
                    itens_del = st.multiselect(
                        "Selecione os registros para excluir:",
                        list(opcoes_del.keys()),
                        key="movs_para_excluir",
                    )
                    confirmar_del = st.checkbox(
                        "Confirmo a exclusão definitiva das movimentações selecionadas",
                        key="confirmar_exclusao_mov",
                    )
                    if st.button("🗑️ Excluir selecionados", use_container_width=True, key="btn_excluir_movs"):
                        if not itens_del:
                            st.error("Selecione pelo menos uma movimentação.")
                        elif not confirmar_del:
                            st.error("Marque a confirmação antes de excluir.")
                        else:
                            ids_del = [opcoes_del[item] for item in itens_del]
                            placeholders = ",".join("?" for _ in ids_del)
                            conn = get_conn()
                            total = conn.execute(
                                f"SELECT COUNT(*) FROM historico WHERE id IN ({placeholders})",
                                ids_del,
                            ).fetchone()[0]
                            conn.execute(f"DELETE FROM historico WHERE id IN ({placeholders})", ids_del)
                            if tipo_del == "SAÍDA (CLIENTE)":
                                seq_atual = conn.execute(
                                    "SELECT COALESCE(MAX(seq_recibo),0) FROM historico WHERE tipo='SAÍDA (CLIENTE)'"
                                ).fetchone()[0]
                                seq_atual = max(seq_atual, RECIBO_SEQ_BASE)
                                conn.execute("UPDATE seq_recibo SET valor=? WHERE id=1", (seq_atual,))
                            conn.commit(); conn.close()
                            registrar_log(st.session_state["usuario"], f"Excluiu {total} movimentacao(oes) do tipo {tipo_del}")
                            confirmar_e_atualizar(f"{total} movimentação(ões) excluída(s).")

    st.markdown("---")
    st.subheader("🖨️ Buscar e Reemitir Recibo")
    b_rec = search_row("Busca recibo","inp_brec","btn_brec","busca_rec_in",
                        "Nº recibo, cliente, data, material ou patrimônio...")

    conn = get_conn()
    br = b_rec.upper()
    if br:
        recibos_q = conn.execute("""
            SELECT DISTINCT num_recibo,seq_recibo,entidade,MAX(data_hora) data_hora
            FROM historico WHERE tipo='SAÍDA (CLIENTE)' AND num_recibo IS NOT NULL
            AND (num_recibo LIKE ? OR entidade LIKE ? OR material LIKE ? OR identificacao LIKE ? OR data_hora LIKE ?)
            GROUP BY num_recibo, seq_recibo, entidade ORDER BY seq_recibo DESC
        """, (f"%{br}%",) * 5).fetchall()
    else:
        recibos_q = conn.execute("""
            SELECT DISTINCT num_recibo,seq_recibo,entidade,MAX(data_hora) data_hora
            FROM historico WHERE tipo='SAÍDA (CLIENTE)' AND num_recibo IS NOT NULL
            GROUP BY num_recibo, seq_recibo, entidade ORDER BY seq_recibo DESC LIMIT 30
        """).fetchall()
    conn.close()

    if not recibos_q:
        st.info("Nenhum recibo encontrado.")
    else:
        mapa_r = {f"Recibo {r[0]} | {r[3]} | {r[2]}": r[0] for r in recibos_q}
        sel_r = st.selectbox("Selecione o recibo:", list(mapa_r.keys()), key="sel_rec")
        nr_sel = mapa_r[sel_r]

        conn = get_conn()
        itens_h = conn.execute(
            "SELECT h.id,h.material_id,h.material,h.marca,h.modelo,h.quantidade,h.identificacao,h.observacoes,h.entidade,"
            "COALESCE(m.patrimonio,''),COALESCE(m.num_serie,'') "
            "FROM historico h LEFT JOIN materiais m ON m.id=h.material_id "
            "WHERE h.tipo='SAÍDA (CLIENTE)' AND h.num_recibo=? ORDER BY h.id",
            (nr_sel,),
        ).fetchall()
        conn.close()

        if itens_h:
            st.markdown("##### 📦 Itens do recibo")
            conn = get_conn()
            materiais_h = {
                row[0]: localizar_material_historico(conn, row[1], row[2], row[3], row[4], row[6])
                for row in itens_h
            }
            conn.close()
            df_hist_rec = pd.DataFrame(
                itens_h,
                columns=["ID", "MaterialID", "Material", "Marca", "Modelo", "Qtd", "Identificacao", "Obs", "Cliente", "PatrimonioDB", "SerieDB"],
            )
            genericos_ident = {"", "-", "—", "MARCA/MODELO", "LOTE"}
            df_hist_rec[["Patrimonio", "Serie"]] = df_hist_rec.apply(
                lambda row: pd.Series(
                    patrimonio_serie_para_exibicao(
                        row["PatrimonioDB"],
                        row["SerieDB"],
                        row["Identificacao"] if str(row["Identificacao"] or "").strip().upper() not in genericos_ident else "",
                        materiais_h.get(row["ID"]),
                    )
                ),
                axis=1,
            )
            tabela_visivel(df_hist_rec[["Material", "Marca", "Modelo", "Qtd", "Patrimonio", "Serie"]])

            obs_edit = st.text_area("Observações", value=itens_h[0][7] or "", key="obs_edit_rec")
            if st.button("💾 Salvar observações", key="salvar_ed_rec"):
                conn = get_conn()
                conn.execute(
                    "UPDATE historico SET observacoes=? WHERE tipo='SAÍDA (CLIENTE)' AND num_recibo=?",
                    (obs_edit, nr_sel),
                )
                conn.commit(); conn.close()
                registrar_log(st.session_state["usuario"], f"Editou observações do recibo {nr_sel}")
                confirmar_e_atualizar("Observações atualizadas!")

            html_r = gerar_html_recibo_saida(nr_sel)
            if html_r:
                mostrar_recibo_iframe(html_r, f"rec_{nr_sel}")

# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
elif opcao == "Dashboard":
    st.title("📊 Dashboard Operacional — 1º BPRv")
    conn = get_conn()
    df_grupos = saldo_agrupado_materiais(conn)
    ti, ts, to, te = cloud_db.dashboard_totals(conn)
    cr = int((df_grupos["Status"] == "CRITICO").sum()) if not df_grupos.empty else 0
    ze = int((df_grupos["Status"] == "ZERADO").sum()) if not df_grupos.empty else 0

    def dash_metric(col, label, value, delta=None):
        delta_html = f"<p class='dash-metric-delta'>{escape(str(delta))}</p>" if delta else ""
        col.markdown(
            f"""
            <div class="dash-metric-card">
              <p class="dash-metric-label">{escape(label)}</p>
              <p class="dash-metric-value">{escape(str(value))}</p>
              {delta_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

    k1,k2,k3,k4,k5,k6 = st.columns(6)
    dash_metric(k1, "Itens em Estoque", ti)
    dash_metric(k2, "Itens Cadastrados", ts)
    dash_metric(k3, "Itens Críticos", cr)
    dash_metric(k4, "Itens Zerados", ze)
    dash_metric(k5, "Total Saídas", to)
    dash_metric(k6, "Total Entradas", te)
    st.markdown("---")

    st.subheader("🗃️ Saldo por Item — Rastreabilidade")
    if df_grupos.empty:
        st.info("Nenhum item cadastrado.")
    else:
        ordem_status = {"ZERADO": 0, "CRITICO": 1, "OK": 2, "AGUARDANDO ENTRADA": 3}
        df_sku = df_grupos.copy()
        df_sku["Ordem"] = df_sku["Status"].map(ordem_status).fillna(9)
        df_sku = df_sku.sort_values(["Ordem", "Material", "Marca", "Modelo"]).drop(columns=["Ordem"])
        tabela_visivel(
            df_sku[["Material", "Marca", "Modelo", "QtdAtual", "Minimo", "Status", "Deficit", "Cadastros"]].rename(
                columns={"QtdAtual": "Qtd Atual", "Minimo": "Minimo"}
            ),
            "Nenhum item cadastrado.",
        )
    st.markdown("---")

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("📊 Distribuição por Quantidade")
        filtro_dist = st.selectbox(
            "Exibir produtos:",
            ["Todos", "Em estoque", "Zerados", "Críticos", "Aguardando entrada"],
            key="filtro_dist_qtd",
        )
        df_bar = df_grupos.copy() if not df_grupos.empty else pd.DataFrame()
        if not df_bar.empty:
            if filtro_dist == "Em estoque":
                df_bar = df_bar[df_bar["QtdAtual"] > 0]
            elif filtro_dist == "Zerados":
                df_bar = df_bar[df_bar["Status"] == "ZERADO"]
            elif filtro_dist == "Críticos":
                df_bar = df_bar[df_bar["Status"] == "CRITICO"]
            elif filtro_dist == "Aguardando entrada":
                df_bar = df_bar[df_bar["Status"] == "AGUARDANDO ENTRADA"]
        if not df_bar.empty:
            df_bar["Item"] = df_bar.apply(lambda r: " | ".join([v for v in (r["Material"], r["Marca"], r["Modelo"]) if v]), axis=1)
            df_bar = df_bar.sort_values(["QtdAtual", "Material", "Marca", "Modelo"], ascending=[False, True, True, True])
            grafico_barras_horizontal(df_bar, "Item", "QtdAtual")
        else: st.info("Sem dados.")
    with col_b:
        st.subheader("🚨 Alertas de Segurança")
        df_cr = df_grupos[df_grupos["Status"].isin(["ZERADO", "CRITICO"])].copy() if not df_grupos.empty else pd.DataFrame()
        if not df_cr.empty:
            df_cr = df_cr[["Material", "Marca", "Modelo", "QtdAtual", "Minimo", "Deficit", "Status"]].rename(columns={"QtdAtual": "Qtd Atual"})
        if not df_cr.empty: tabela_visivel(df_cr)
        else: st.success("✅ Todos os itens dentro do nível de segurança.")
    st.markdown("---")

    st.subheader("📈 Tendência de Movimentações")
    periodo = st.selectbox("Período:", ["Últimos 7 dias","Últimos 30 dias","Tudo"], key="per_dash")
    df_ht = read_sql_query("SELECT data_hora,tipo FROM historico", conn)
    if not df_ht.empty:
        df_ht["data_hora"] = pd.to_datetime(df_ht["data_hora"], dayfirst=True, errors="coerce")
        df_ht = df_ht.dropna(subset=["data_hora"])
        hj = pd.Timestamp.now()
        if periodo == "Últimos 7 dias":  df_ht = df_ht[df_ht["data_hora"] >= hj - pd.Timedelta(days=7)]
        elif periodo == "Últimos 30 dias": df_ht = df_ht[df_ht["data_hora"] >= hj - pd.Timedelta(days=30)]
        if df_ht.empty: st.info("Sem movimentações no período.")
        else:
            dc = df_ht.groupby([df_ht["data_hora"].dt.date, "tipo"]).size().reset_index(name="Qtd")
            dc.columns = ["Data", "Tipo", "Qtd"]
            dc["Data"] = dc["Data"].astype(str)
            tabela_visivel(dc)
    else: st.info("Sem movimentações.")
    st.markdown("---")

    col_c, col_d = st.columns(2)
    with col_c:
        st.subheader("🏆 Top 10 Mais Movimentados")
        df_top = read_sql_query("SELECT material 'Material',SUM(quantidade) 'Total',COUNT(*) 'Operações' FROM historico GROUP BY material ORDER BY 2 DESC LIMIT 10", conn)
        df_top.columns = ["Material", "Total", "Operacoes"]
        tabela_visivel(df_top, "Sem movimentacoes.")
    with col_d:
        st.subheader("🕐 Últimas 10 Saídas")
        df_ul = read_sql_query("SELECT data_hora,entidade,material,quantidade,num_recibo FROM historico WHERE tipo='SAÍDA (CLIENTE)' ORDER BY id DESC LIMIT 10", conn)
        df_ul.columns = ["Data", "Entidade", "Material", "Qtd", "Recibo"]
        tabela_visivel(df_ul, "Sem saidas registradas.")

    st.markdown("---")
    st.subheader("👤 Relação Cliente x Produto")
    df_cliente_produto = read_sql_query("""
        SELECT
            MIN(COALESCE(NULLIF(TRIM(h.entidade),''),'SEM CLIENTE')) AS Cliente,
            MIN(COALESCE(NULLIF(TRIM(h.material),''),'SEM MATERIAL')) AS Produto,
            MIN(COALESCE(TRIM(h.marca),'')) AS Marca,
            MIN(COALESCE(TRIM(h.modelo),'')) AS Modelo,
            SUM(COALESCE(h.quantidade,0)) AS Qtd,
            COUNT(*) AS Movimentacoes,
            COALESCE(GROUP_CONCAT(DISTINCT NULLIF(TRIM(COALESCE(
                NULLIF(m.patrimonio,''),
                NULLIF(m.num_serie,''),
                NULLIF(m.imei,''),
                NULLIF(m.numero_linha,''),
                NULLIF(m.imei_chip,''),
                CASE
                    WHEN UPPER(TRIM(COALESCE(h.identificacao,''))) NOT IN ('', '-', 'MARCA/MODELO', 'LOTE')
                    THEN h.identificacao
                    ELSE ''
                END
            )),'')),'') AS Identificadores,
            COALESCE(GROUP_CONCAT(DISTINCT NULLIF(TRIM(h.num_recibo),'')),'') AS Recibos,
            MAX(h.data_hora) AS UltimaSaida
        FROM historico h
        LEFT JOIN materiais m ON m.id = h.material_id
        WHERE h.tipo LIKE 'SA%CLIENTE%'
        GROUP BY
            UPPER(TRIM(h.entidade)),
            UPPER(TRIM(h.material)),
            UPPER(TRIM(h.marca)),
            UPPER(TRIM(h.modelo))
        ORDER BY Cliente, Produto, Marca, Modelo
    """, conn)
    if not df_cliente_produto.empty:
        df_cliente_produto.columns = [
            "Cliente", "Produto", "Marca", "Modelo", "Qtd", "Movimentacoes",
            "Identificadores", "Recibos", "Ultima Saida"
        ]
        df_cliente_produto["Qtd"] = df_cliente_produto["Qtd"].fillna(0).astype(int)
        df_cliente_produto["Movimentacoes"] = df_cliente_produto["Movimentacoes"].fillna(0).astype(int)
    tabela_visivel(df_cliente_produto, "Sem saidas registradas para relacionar cliente e produto.")

    st.markdown("---")
    st.subheader("🔖 Rastreabilidade Individual")
    df_rt = read_sql_query("""
        SELECT nome 'Material',marca 'Marca',modelo 'Modelo',patrimonio 'Patrimônio',
               num_serie 'Nº Série',imei 'IMEI',numero_linha 'Número da Linha',imei_chip 'IMEI do Chip',lcm 'LCM',orgao 'Órgão',tipo_transceptor 'Tipo de Transceptor',
               CASE WHEN quantidade>0 THEN '✅ Disponível' ELSE '❌ Sem estoque' END 'Situação'
        FROM materiais WHERE (patrimonio IS NOT NULL AND patrimonio!='')
                          OR (num_serie IS NOT NULL AND num_serie!='')
                          OR (imei IS NOT NULL AND imei!='')
                          OR (numero_linha IS NOT NULL AND numero_linha!='')
                          OR (imei_chip IS NOT NULL AND imei_chip!='')
                          OR (lcm IS NOT NULL AND lcm!='') ORDER BY nome
    """, conn)
    conn.close()
    df_rt.columns = ["Material", "Marca", "Modelo", "Patrimonio", "Serie", "IMEI", "Numero da Linha", "IMEI do Chip", "LCM", "Orgao", "Tipo de Transceptor", "Situacao"]
    df_rt["Situacao"] = df_rt["Situacao"].apply(lambda valor: "Disponivel" if "Dispon" in str(valor) else "Sem estoque")
    if not df_rt.empty: tabela_visivel(df_rt)
    else: st.info("Nenhum item com patrimônio/série cadastrado.")

# ═══════════════════════════════════════════════════════════════════════════════
# CENTRAL DE RELATÓRIOS
# ═══════════════════════════════════════════════════════════════════════════════
elif opcao == "Central de Relatórios":
    st.title("📑 Central de Relatórios")
    tipo_rel = st.selectbox("Tipo de relatório:", [
        "Estoque Atual Completo","Retiradas por Cliente","Entradas por Fornecedor",
        "Materiais Críticos / Zerados","Rastreabilidade Nº Série / Patrimônio","Busca por Produto",
    ])
    conn = get_conn(); df_rel = pd.DataFrame()

    if tipo_rel == "Estoque Atual Completo":
        df_rel = read_sql_query("SELECT nome 'Material',quantidade 'Qtd',minimo 'Mínimo',marca 'Marca',modelo 'Modelo',patrimonio 'Patrimônio',num_serie 'Nº Série',imei 'IMEI',numero_linha 'Número da Linha',imei_chip 'IMEI do Chip',lcm 'LCM',orgao 'Órgão',tipo_transceptor 'Tipo de Transceptor',prefixo_viatura 'Prefixo da Viatura',observacoes 'Obs' FROM materiais ORDER BY nome", conn)

    elif tipo_rel == "Retiradas por Cliente":
        b_rc = search_row("Cliente relatório","inp_rel_cli","btn_rel_cli","rel_busca_cli","Nome do cliente...")
        if b_rc:
            df_rel = read_sql_query("SELECT data_hora,entidade,material,marca,modelo,identificacao,quantidade,num_recibo FROM historico WHERE tipo='SAÍDA (CLIENTE)' AND entidade LIKE ? ORDER BY id DESC",
                                       conn, params=(f"%{b_rc.upper()}%",))

    elif tipo_rel == "Entradas por Fornecedor":
        b_rf = search_row("Fornecedor relatório","inp_rel_forn","btn_rel_forn","rel_busca_forn","Nome do fornecedor...")
        if b_rf:
            df_rel = read_sql_query("SELECT data_hora,entidade,material,marca,modelo,identificacao,quantidade FROM historico WHERE tipo='ENTRADA (FORNECEDOR)' AND entidade LIKE ? ORDER BY id DESC",
                                       conn, params=(f"%{b_rf.upper()}%",))

    elif tipo_rel == "Materiais Críticos / Zerados":
        df_rel = saldo_agrupado_materiais(conn)
        if not df_rel.empty:
            df_rel = df_rel[df_rel["Status"].isin(["ZERADO", "CRITICO"])][
                ["Material", "Marca", "Modelo", "QtdAtual", "Minimo", "Deficit", "Status", "Cadastros"]
            ].rename(columns={"QtdAtual": "Qtd Atual"})

    elif tipo_rel == "Rastreabilidade Nº Série / Patrimônio":
        b_rr = search_row("Rastreabilidade","inp_rel_rastr","btn_rel_rastr","rel_busca_rastr","Patrimônio, Nº Série, linha, chip ou Nome...")
        brt = b_rr.upper() if b_rr else ""
        if brt:
            df_rel = read_sql_query("SELECT nome,marca,modelo,patrimonio,num_serie,imei,numero_linha,imei_chip,lcm,orgao,quantidade,tipo_transceptor FROM materiais WHERE (patrimonio LIKE ? OR num_serie LIKE ? OR imei LIKE ? OR numero_linha LIKE ? OR imei_chip LIKE ? OR lcm LIKE ? OR orgao LIKE ? OR nome LIKE ?) AND ((patrimonio IS NOT NULL AND patrimonio!='') OR (num_serie IS NOT NULL AND num_serie!='') OR (imei IS NOT NULL AND imei!='') OR (numero_linha IS NOT NULL AND numero_linha!='') OR (imei_chip IS NOT NULL AND imei_chip!='') OR (lcm IS NOT NULL AND lcm!=''))",
                                       conn, params=(f"%{brt}%",)*8)
        else:
            df_rel = read_sql_query("SELECT nome,marca,modelo,patrimonio,num_serie,imei,numero_linha,imei_chip,lcm,orgao,quantidade,tipo_transceptor FROM materiais WHERE (patrimonio IS NOT NULL AND patrimonio!='') OR (num_serie IS NOT NULL AND num_serie!='') OR (imei IS NOT NULL AND imei!='') OR (numero_linha IS NOT NULL AND numero_linha!='') OR (imei_chip IS NOT NULL AND imei_chip!='') OR (lcm IS NOT NULL AND lcm!='') ORDER BY nome", conn)

    elif tipo_rel == "Busca por Produto":
        b_rp = search_row("Produto relatório","inp_rel_prod","btn_rel_prod","rel_busca_prod","Nome, marca, modelo, patrimônio, série, código, IMEI, linha, chip...")
        if b_rp:
            bpt = b_rp.upper()
            campos_prod = ("nome", "marca", "modelo", "patrimonio", "num_serie", "prefixo_viatura", "imei", "numero_linha", "imei_chip", "lcm", "orgao", "tipo_transceptor")
            filtro_prod = " OR ".join([f"UPPER(COALESCE({campo},'')) LIKE ?" for campo in campos_prod])
            df_prod = read_sql_query(
                "SELECT nome 'Material',marca 'Marca',modelo 'Modelo',quantidade 'Qtd Atual',minimo 'Minimo',"
                "patrimonio 'Patrimonio',num_serie 'Serie',prefixo_viatura 'Prefixo da Viatura',imei 'IMEI',numero_linha 'Numero da Linha',imei_chip 'IMEI do Chip',lcm 'LCM',"
                "orgao 'Orgao',tipo_transceptor 'Tipo de Transceptor',observacoes 'Obs' "
                f"FROM materiais WHERE {filtro_prod} "
                "ORDER BY nome,marca,modelo,patrimonio,num_serie,imei,numero_linha,imei_chip,id",
                conn,
                params=(f"%{bpt}%",) * len(campos_prod),
            )
            st.subheader("📦 Dados do Produto")
            if not df_prod.empty:
                tabela_visivel(df_prod)
            else:
                st.info("Nenhum produto encontrado para essa busca.")
            campos_uso = ("material", "marca", "modelo", "identificacao", "entidade", "num_recibo", "observacoes")
            filtro_uso = " OR ".join([f"UPPER(COALESCE({campo},'')) LIKE ?" for campo in campos_uso])
            df_uso = read_sql_query(
                "SELECT data_hora 'Data/Hora',tipo 'Tipo',entidade 'Origem/Destino',material 'Material',"
                "marca 'Marca',modelo 'Modelo',identificacao 'Identificacao',quantidade 'Qtd',"
                "num_recibo 'Recibo',observacoes 'Obs' "
                f"FROM historico WHERE {filtro_uso} ORDER BY id DESC",
                conn,
                params=(f"%{bpt}%",) * len(campos_uso),
            )
            st.subheader("📋 Histórico de Uso")
            if not df_uso.empty:
                tabela_visivel(df_uso)
            else:
                st.info("Nenhum histórico encontrado para essa busca.")
            partes = []
            if not df_prod.empty:
                d1 = df_prod.copy()
                d1.insert(0, "Seção", "Dados do Produto")
                partes.append(d1)
            if not df_uso.empty:
                d2 = df_uso.copy()
                d2.insert(0, "Seção", "Histórico de Uso")
                partes.append(d2)
            if partes:
                df_rel = pd.concat(partes, ignore_index=True, sort=False).fillna("")

    conn.close()

    if not df_rel.empty:
        df_rel = df_rel.fillna("")
        if tipo_rel != "Busca por Produto":
            tabela_visivel(df_rel)
        c1, c2 = st.columns(2)
        nome_base = f"relatorio_{datetime.now().strftime('%d%m%Y_%H%M')}"
        c1.download_button("📥 Exportar Excel", gerar_excel(df_rel),
                           f"{nome_base}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        c2.download_button("📄 Exportar PDF", gerar_pdf_relatorio(df_rel, tipo_rel),
                           f"{nome_base}.pdf",
                           mime="application/pdf")
    elif tipo_rel not in ("Retiradas por Cliente","Entradas por Fornecedor",
                          "Rastreabilidade Nº Série / Patrimônio","Busca por Produto"):
        st.info("Nenhum dado encontrado.")

    st.markdown("---")
    st.subheader("Backup do banco de teste")
    st.info("Exporte o PostgreSQL conforme o guia da cópia de teste. Os relatórios acima não substituem um backup completo.")
