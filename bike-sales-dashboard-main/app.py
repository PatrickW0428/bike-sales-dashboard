from __future__ import annotations

import base64
import mimetypes
from datetime import timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
import streamlit.components.v1 as components
from plotly.subplots import make_subplots

from data_prep import clean_sales_orders, load_sales_orders


def _resolve_default_data_path() -> str:
    """
    Prefer repo-local dataset (Streamlit Cloud friendly), but fall back to the
    original Desktop location for local dev convenience.
    """
    here = Path(__file__).resolve().parent
    candidates = [
        here / "Global Bike Sales Data (1).xlsx",
        here.parent / "Global Bike Sales Data (1).xlsx",
        Path.home() / "Desktop" / "Data wrangling" / "Global Bike Sales Data (1).xlsx",
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    # Default to the first (Cloud) path to make the error message predictable
    return str(candidates[0])


DEFAULT_PATH = _resolve_default_data_path()


def _resolve_office_background_uri() -> str:
    """Embed a user-provided office background as a data URI for Streamlit CSS."""
    here = Path(__file__).resolve().parent
    candidates = [
        here / "assets" / "office-bg.png",
        here / "assets" / "office-bg.jpg",
        Path(
            r"C:\Users\28172\.cursor\projects\c-Users-28172-Desktop-bike-sales-dashboard-main-bike-sales-dashboard-main\assets\c__Users_28172_AppData_Roaming_Cursor_User_workspaceStorage_fd405c5d745cdbce913603f6bb3c5a37_images_Gemini_Generated_Image_ycuy5xycuy5xycuy-26ba2454-b994-488d-9a17-6e8050bd9345.png"
        ),
    ]
    for path in candidates:
        if path.exists():
            mime = mimetypes.guess_type(path.name)[0] or "image/png"
            data = base64.b64encode(path.read_bytes()).decode("ascii")
            return f"data:{mime};base64,{data}"
    return ""


OFFICE_BG_URI = _resolve_office_background_uri()

APPLE_GLOBAL_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');
  @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@600;700;800;900&display=swap');
  @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&display=swap');
  :root{
    --bg: #172334;
    --text: #111827;
    --muted: rgba(17,24,39,0.60);
    --office-ink: #102338;
    --office-muted: rgba(16,35,56,0.62);
    --office-blue: #2F5870;
    --office-aqua: #2E6F73;
    --office-mint: #4F7569;
    --office-sun: #A7774B;
    --apple-blue: #FF7A33;
    --apple-indigo: #3DD1A8;
    --apple-purple: #FF6491;
    --apple-pink: #FFBC2E;
    --apple-orange: #FF5A5A;
    --glass-bg: rgba(255, 255, 255, 0.15);
    --glass-border: 1px solid rgba(255,255,255,0.34);
    --glass-shadow: 0 18px 48px rgba(15,23,42,0.22);
  }

  html, body, .stApp, [data-testid="stAppViewContainer"]{
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: Inter, -apple-system, Segoe UI, sans-serif !important;
    font-weight: 400 !important;
  }

  /* High-rise office backdrop: real uploaded office image + subtle glass tint. */
  .stApp,
  [data-testid="stAppViewContainer"],
  [data-testid="stAppViewContainer"] section.main{
    background-color: var(--bg) !important;
    background-image:
      radial-gradient(ellipse 56% 42% at 78% 12%, rgba(196,238,255,0.20), rgba(196,238,255,0.00) 66%),
      radial-gradient(ellipse 52% 38% at 18% 72%, rgba(68,170,170,0.10), rgba(68,170,170,0.00) 70%),
      linear-gradient(180deg, rgba(236,248,255,0.10), rgba(15,31,48,0.16)),
      __OFFICE_BG_LAYER__ !important;
    background-size: auto, auto, auto, cover !important;
    background-attachment: fixed !important;
    background-repeat: no-repeat !important;
    background-position: center !important;
  }

  /* Remove Streamlit chrome (keep sidebar toggle available) */
  #MainMenu { visibility: hidden; }
  footer { visibility: hidden; height: 0px; }

  /* Keep header/toolbar so the sidebar expand button remains accessible */
  header { visibility: visible; height: auto; background: transparent !important; }
  [data-testid="stToolbar"] { visibility: visible; height: auto; position: relative; }
  [data-testid="stHeader"] { background: transparent !important; }

  /* Deploy area decor: a tiny standing person + hint banner (non-interactive) */
  [data-testid="stToolbar"]::before{
    content: "🧍";
    position: absolute;
    right: 110px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 18px;
    line-height: 1;
    opacity: 0.92;
    pointer-events: none;
    filter: saturate(0.95);
    text-shadow:
      0 0 0.6px rgba(255,255,255,0.65),
      0 10px 24px rgba(0,0,0,0.10);
  }

  /* Top-left hint banner (fixed overlay; does NOT affect layout) */
  [data-testid="stAppViewContainer"]::before{
    content: "Click to open the filter";
    position: fixed;
    left: 56px; /* avoid the built-in sidebar toggle */
    top: 12px;
    padding: 7px 12px;
    border-radius: 999px;
    background: rgba(255,255,255,0.78);
    border: 1px solid rgba(17,24,39,0.10);
    box-shadow: 0 10px 24px rgba(17,24,39,0.10);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    font-family: Inter, -apple-system, Segoe UI, sans-serif;
    font-weight: 800;
    font-size: 12px;
    letter-spacing: 0.01em;
    color: rgba(17,24,39,0.66);
    pointer-events: none;
    white-space: nowrap;
    opacity: 0.96;
    z-index: 1000;
  }

  /* Links: avoid default red/purple */
  a, a:visited { color: var(--apple-blue) !important; }
  a:hover { color: rgba(255,140,66,0.80) !important; }

  /* Custom signature footer (website-like) */
  .patrick-footer{
    position: fixed;
    left: 50%;
    bottom: 10px;
    transform: translateX(-50%);
    padding: 8px 14px;
    border-radius: 999px;
    background: rgba(255,255,255,0.26);
    border: 1px solid rgba(255,255,255,0.38);
    box-shadow:
      0 10px 28px rgba(15,23,42,0.12),
      inset 0 1px 0 rgba(255,255,255,0.52);
    backdrop-filter: blur(12px) saturate(1.05);
    -webkit-backdrop-filter: blur(12px) saturate(1.05);
    font-family: Inter, -apple-system, Segoe UI, sans-serif;
    font-weight: 700;
    font-size: 12px;
    letter-spacing: 0.01em;
    color: rgba(17,24,39,0.55);
    pointer-events: none;
    z-index: 999;
    white-space: nowrap;
  }

  /* Tight grid rhythm */
  .block-container{
    padding-top: 2rem;
    padding-bottom: 1.5rem;
    padding-left: 16px;
    padding-right: 16px;
    max-width: 1240px;
  }
  div[data-testid="stHorizontalBlock"]{ gap: 1rem !important; }

  /* Sidebar: same cool frosted-glass language as the dashboard cards. */
  section[data-testid="stSidebar"]{
    background: rgba(255,255,255,0.18) !important;
    border-right: 1px solid rgba(255,255,255,0.28) !important;
    box-shadow:
      inset 0 1px 0 rgba(255,255,255,0.42),
      18px 0 42px rgba(15,23,42,0.18) !important;
    backdrop-filter: blur(16px) saturate(1.04);
    -webkit-backdrop-filter: blur(16px) saturate(1.04);
    position: relative;
    overflow: hidden;
    background-image:
      radial-gradient(ellipse 90% 36% at 55% 7%, rgba(255,255,255,0.34), rgba(255,255,255,0.00) 70%),
      linear-gradient(180deg, rgba(255,255,255,0.18), rgba(255,255,255,0.06));
  }

  /* Glass edge highlight, aligned with the main dashboard language. */
  section[data-testid="stSidebar"]::before{
    content: "";
    position: absolute;
    left: 14px;
    right: 14px;
    top: 0;
    width: auto;
    height: 1px;
    border-radius: 999px;
    background: linear-gradient(90deg, rgba(255,255,255,0.00), rgba(255,255,255,0.70) 32%, rgba(255,255,255,0.22) 72%, rgba(255,255,255,0.00));
    opacity: 1;
    pointer-events: none;
  }
  section[data-testid="stSidebar"]::after{
    content: "";
    position: absolute;
    inset: 0;
    background:
      linear-gradient(100deg, rgba(255,255,255,0.18), rgba(255,255,255,0.00) 38%),
      radial-gradient(ellipse 62% 30% at 70% 18%, rgba(255,220,170,0.20), rgba(255,220,170,0.00) 72%);
    opacity: 1;
    pointer-events: none;
  }
  section[data-testid="stSidebar"] .block-container{ padding-top: 1.25rem; }

  /* Controls: synced with the translucent dashboard cards. */
  section[data-testid="stSidebar"] [data-baseweb="select"] > div,
  section[data-testid="stSidebar"] [data-baseweb="input"] > div{
    background: rgba(255,255,255,0.46) !important;
    border: 1px solid rgba(255,255,255,0.46) !important;
    border-radius: 16px !important;
    box-shadow:
      0 8px 22px rgba(15,23,42,0.08),
      inset 0 1px 0 rgba(255,255,255,0.50) !important;
    backdrop-filter: blur(10px) saturate(1.04);
    -webkit-backdrop-filter: blur(10px) saturate(1.04);
    font-family: Nunito, Inter, -apple-system, Segoe UI, sans-serif !important;
    font-weight: 800 !important;
    letter-spacing: 0.005em !important;
    color: var(--office-ink) !important;
  }
  section[data-testid="stSidebar"] input,
  section[data-testid="stSidebar"] [data-baseweb="input"] input{
    font-family: Nunito, Inter, -apple-system, Segoe UI, sans-serif !important;
    font-weight: 800 !important;
    color: var(--office-ink) !important;
    letter-spacing: 0.005em !important;
  }
  section[data-testid="stSidebar"] input::placeholder{
    font-family: Nunito, Inter, -apple-system, Segoe UI, sans-serif !important;
    font-weight: 700 !important;
    color: rgba(16,35,56,0.42) !important;
  }
  section[data-testid="stSidebar"] label,
  section[data-testid="stSidebar"] p{
    color: rgba(16,35,56,0.72) !important;
  }
  section[data-testid="stSidebar"] [data-baseweb="tag"]{
    background: rgba(255,255,255,0.34) !important;
    border: 1px solid rgba(255,255,255,0.42) !important;
    color: rgba(17,24,39,0.80) !important;
    border-radius: 999px !important;
    font-family: Nunito, Inter, -apple-system, Segoe UI, sans-serif !important;
    font-weight: 800 !important;
    letter-spacing: 0.005em !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.38) !important;
  }
  section[data-testid="stSidebar"] [data-baseweb="select"] > div:focus-within,
  section[data-testid="stSidebar"] [data-baseweb="input"] > div:focus-within{
    box-shadow: 0 0 0 4px rgba(255,140,66,0.12) !important;
  }

  /* Apple card spec */
  .apple-card{
    background: var(--glass-bg);
    border-radius: 24px;
    border: var(--glass-border);
    box-shadow:
      var(--glass-shadow),
      inset 0 1px 0 rgba(255,255,255,0.48),
      inset 0 -1px 0 rgba(255,255,255,0.10);
    padding: 24px;
    backdrop-filter: blur(13px) saturate(1.06);
    -webkit-backdrop-filter: blur(13px) saturate(1.06);
    position: relative;
    overflow: hidden;
  }
  .apple-card::after{
    content:"";
    position:absolute;
    inset:0;
    pointer-events:none;
    background:
      linear-gradient(112deg, rgba(255,255,255,0.40), rgba(255,255,255,0.06) 17%, rgba(255,255,255,0.00) 38%),
      linear-gradient(180deg, rgba(255,255,255,0.22), rgba(255,255,255,0.00) 42%);
    mix-blend-mode: screen;
    opacity: 0.62;
  }

  /* Card containers via st.container(key=...) */
  div[class*="st-key-card_"]{
    /* Ultra-thin frosted glass: transparent enough for the office skyline to show through. */
    background: rgba(255,255,255,0.13);
    background-image:
      radial-gradient(ellipse 70% 34% at 24% 0%, rgba(255,255,255,0.34), rgba(255,255,255,0.00) 68%),
      radial-gradient(ellipse 54% 38% at 86% 18%, rgba(255,255,255,0.16), rgba(255,255,255,0.00) 66%),
      linear-gradient(180deg, rgba(255,255,255,0.13), rgba(255,255,255,0.04) 58%);
    background-size: auto;
    background-repeat: no-repeat;
    border-radius: 22px;
    border: 1px solid rgba(255,255,255,0.34);
    box-shadow:
      0 18px 46px rgba(15,23,42,0.18),
      inset 0 1px 0 rgba(255,255,255,0.50),
      inset 0 -1px 0 rgba(255,255,255,0.10);
    padding: 28px;
    backdrop-filter: blur(13px) saturate(1.06);
    -webkit-backdrop-filter: blur(13px) saturate(1.06);
    overflow: hidden;
    position: relative;
  }

  /* Top glass-edge highlight */
  div[class*="st-key-card_"]::before{
    content: "";
    position: absolute;
    top: 0;
    left: 24px;
    right: 24px;
    height: 1px;
    background: linear-gradient(90deg, rgba(255,255,255,0.00), rgba(255,255,255,0.86) 25%, rgba(255,255,255,0.32) 58%, rgba(255,255,255,0.00) 82%);
    border-radius: 0 0 999px 999px;
    pointer-events: none;
  }
  /* Directional office-light reflection across the glass surface. */
  div[class*="st-key-card_"]::after{
    content:"";
    position:absolute;
    inset:0;
    pointer-events:none;
    background:
      linear-gradient(112deg, rgba(255,255,255,0.34), rgba(255,255,255,0.05) 18%, rgba(255,255,255,0.00) 38%),
      linear-gradient(180deg, rgba(255,255,255,0.18), rgba(255,255,255,0.00) 45%);
    mix-blend-mode: screen;
    opacity: 0.58;
  }

  div[class*="st-key-card_"] > div{
    padding: 0 !important;
  }

  /* Chart content area: nearly invisible so glass card shows through */
  div[data-testid="stVerticalBlock"][class*="_plotwrap"],
  .share-plot-wrap{
    background: rgba(255,255,255,0.055);
    border: 1px solid rgba(255,255,255,0.18);
    border-radius: 16px;
    padding: 16px;
    box-shadow:
      inset 0 1px 0 rgba(255,255,255,0.28),
      inset 0 -1px 0 rgba(255,255,255,0.08);
    overflow: hidden;
  }
  div[data-testid="stVerticalBlock"][class*="_plotwrap"] > div{ padding: 0 !important; }

  /* Categories treemap: glassmorphism, aligned with other large cards */
  div.st-key-card_mix{
    box-shadow:
      0 18px 46px rgba(15,23,42,0.18),
      inset 0 1px 0 rgba(255,255,255,0.50) !important;
    border: 1px solid rgba(255,255,255,0.34) !important;
    border-radius: 22px !important;
    background: rgba(255, 255, 255, 0.13) !important;
    backdrop-filter: blur(13px) saturate(1.06) !important;
    -webkit-backdrop-filter: blur(13px) saturate(1.06) !important;
    overflow: hidden !important;
    position: relative !important;
    /* inner glow + soft gradient for "jelly" */
    background-image:
      radial-gradient(ellipse 70% 34% at 24% 0%, rgba(255,255,255,0.34), rgba(255,255,255,0.00) 68%),
      linear-gradient(180deg, rgba(255,255,255,0.13), rgba(255,255,255,0.04)) !important;
  }

  /* Row 2 alignment: Trend + Share */
  div.st-key-card_trend,
  div.st-key-card_share {
    min-height: 520px;
  }

  /* Row 3 alignment: Categories + Customers */
  div.st-key-card_mix,
  div.st-key-card_topcust {
    min-height: 600px;
  }

  /* Customers map card: prevent map from overlapping the Top 3 list */
  div.st-key-card_topcust [data-testid="stPlotlyChart"]{
    overflow: hidden !important;
    border-radius: 18px !important;
  }
  /* Share donut: pixel-level nudge (guaranteed visible) */
  div.st-key-card_share [data-testid="stPlotlyChart"]{
    overflow: visible !important;
  }
  /* Plotly root is .js-plotly-plot; target it directly (robust) */
  div.st-key-card_share [data-testid="stPlotlyChart"] .js-plotly-plot{
    transform: translate(36px, -10px) scale(1.02) !important; /* big nudge for verification */
    transform-origin: top left !important;
    will-change: transform;
  }
  /* Fallback: sometimes Streamlit wraps plotly in extra divs */
  div.st-key-card_share [data-testid="stPlotlyChart"] .js-plotly-plot + div{
    transform: translate(36px, -10px) scale(1.02) !important;
    transform-origin: top left !important;
  }
  div.st-key-cust_map_left{
    position: relative !important;
    z-index: 1 !important;
    overflow: hidden !important;
  }
  div.st-key-cust_map_right{
    position: relative !important;
    z-index: 5 !important;
  }
  div.st-key-card_mix [data-testid="stPlotlyChart"]{
    box-shadow: none !important;
    border: none !important;
    background: transparent !important;
  }
  /* Jelly feel on treemap tiles (SVG) */
  div.st-key-card_mix [data-testid="stPlotlyChart"] svg .slice path{
    stroke: rgba(255,255,255,0.00) !important;
    stroke-width: 0px !important;
    filter: saturate(1.05) brightness(1.02);
  }

  .apple-title{
    font-size: 1.18rem;
    font-family: Inter, -apple-system, Segoe UI, sans-serif;
    font-weight: 800;
    letter-spacing: 0.01em;
    margin: 0 0 10px 0;
    color: var(--office-ink);
    /* Tiny neon edge (Apple subtle) */
    text-shadow:
      0 0 0.6px rgba(255,255,255,0.55),
      0 0 10px rgba(255,140,66,0.10),
      0 0 16px rgba(255,140,66,0.08);
  }
  .apple-subtitle{
    margin: -2px 0 0 0;
    font-size: 0.85rem;
    color: var(--office-muted);
    font-family: Nunito, Inter, -apple-system, Segoe UI, sans-serif;
    font-weight: 700;
  }

  /* KPI text */
  .kpi-title{
    font-size: 0.80rem;
    color: rgba(17,24,39,0.55);
    font-weight: 600;
    letter-spacing: 0.02em;
  }
  .kpi-value{
    margin-top: 10px;
    font-size: 2.25rem;
    font-weight: 900;
    color: #111827;
    line-height: 1.05;
  }
  .kpi-badge{
    margin-top: 12px;
    display: inline-flex;
    align-items: center;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 0.80rem;
    font-weight: 750;
  }
  .badge-pos{
    background: rgba(61,209,168,0.16);
    color: rgba(61,209,168,0.95);
  }
  .badge-neg{
    background: rgba(255,100,140,0.14);
    color: rgba(255,100,140,0.95);
  }

  .kpi-icon{
    width: 44px;
    height: 44px;
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(0,0,0,0.04);
    border: 1px solid rgba(0,0,0,0.05);
    box-shadow: 0 6px 18px rgba(0,0,0,0.04);
    font-size: 1.25rem;
    flex: 0 0 auto;
  }

  /* Financial KPI card: crisp print on ultra-thin frosted glass. */
  .fin-kpi{
    height: 140px;
    position: relative;
    overflow: hidden;
    border-radius: 22px;
    background: rgba(255,255,255,0.15);
    background-image:
      linear-gradient(112deg, rgba(255,255,255,0.34), rgba(255,255,255,0.06) 18%, rgba(255,255,255,0.00) 40%),
      radial-gradient(ellipse 70% 34% at 22% 0%, rgba(255,255,255,0.30), rgba(255,255,255,0.00) 68%),
      linear-gradient(180deg, rgba(255,255,255,0.13), rgba(255,255,255,0.04));
    border: 1px solid rgba(255,255,255,0.34);
    box-shadow:
      0 16px 42px rgba(15,23,42,0.18),
      inset 0 1px 0 rgba(255,255,255,0.52),
      inset 0 -1px 0 rgba(255,255,255,0.10);
    backdrop-filter: blur(13px) saturate(1.06);
    -webkit-backdrop-filter: blur(13px) saturate(1.06);
    padding: 18px 18px 14px 18px;
  }
  .fin-kpi .spark{
    position: absolute;
    left: 0;
    bottom: 0;
    width: 100%;
    height: 40%;
    opacity: 0.45;
    pointer-events: none;
  }
  .fin-kpi .title{
    font-size: 0.80rem;
    font-weight: 600;
    color: rgba(17,24,39,0.55);
    letter-spacing: 0.02em;
  }
  .fin-kpi .icon{
    width: 34px;
    height: 34px;
    border-radius: 14px;
    display:flex;
    align-items:center;
    justify-content:center;
    background: rgba(255,255,255,0.24);
    border: 1px solid rgba(255,255,255,0.32);
    box-shadow:
      0 6px 18px rgba(15,23,42,0.08),
      inset 0 1px 0 rgba(255,255,255,0.42);
    font-size: 1.05rem;
    flex: 0 0 auto;
  }
  .fin-kpi .title-row{
    display:flex;
    align-items:center;
    gap: 10px;
  }
  .fin-kpi .value{
    margin-top: 14px;
    font-size: 2.15rem;
    font-weight: 900;
    color: rgba(17,24,39,0.92);
    line-height: 1.05;
  }
  .fin-kpi .trend{
    position: absolute;
    top: 16px;
    right: 16px;
    font-size: 0.90rem;
    font-weight: 800;
    padding: 4px 10px;
    border-radius: 999px;
    border: 1px solid rgba(255,255,255,0.36);
    background: rgba(255,255,255,0.24);
    color: rgba(17,24,39,0.65);
  }
  .fin-kpi .trend.up{
    background: rgba(61,209,168,0.16);
    color: rgba(61,209,168,0.95);
    border-color: rgba(61,209,168,0.14);
  }
  .fin-kpi .trend.down{
    background: rgba(255,100,140,0.14);
    color: rgba(255,100,140,0.95);
    border-color: rgba(255,100,140,0.14);
  }

  /* Card header row with micro icon */
  .card-header{
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap: 12px;
    margin-bottom: 8px;
  }

  /* (Removed) overlay-based card banner: replaced by card background-image */
  .micro-icon{
    width: 28px;
    height: 28px;
    border-radius: 999px;
    border: 1px solid rgba(255,255,255,0.34);
    background: rgba(255,255,255,0.22);
    color: rgba(17,24,39,0.65);
    display:flex;
    align-items:center;
    justify-content:center;
    font-weight: 850;
    font-size: 0.90rem;
    user-select:none;
  }

  /* Share card icon row (below donut) */
  .share-icons{
    display: flex;
    gap: 10px;
    justify-content: center;
    align-items: center;
    margin-top: 8px;
    padding-top: 10px;
    border-top: 1px solid rgba(0,0,0,0.06);
  }
  .share-icon,
  div.st-key-share_icon_row button{
    width: 38px;
    height: 38px;
    border-radius: 14px;
    border: 1px solid rgba(255,255,255,0.38);
    background: rgba(255,255,255,0.22);
    box-shadow:
      0 8px 18px rgba(15,23,42,0.12),
      inset 0 1px 0 rgba(255,255,255,0.46);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    line-height: 1;
    user-select: none;
    backdrop-filter: blur(12px) saturate(1.05);
    -webkit-backdrop-filter: blur(12px) saturate(1.05);
    opacity: 0.96;
  }
  div.st-key-share_icon_row{
    margin-top: 6px;
    padding-top: 10px;
    border-top: 1px solid rgba(0,0,0,0.06);
  }
  div.st-key-share_icon_row [data-testid="stHorizontalBlock"]{ gap: 10px !important; }
  div.st-key-share_icon_row button{
    padding: 0 !important;
    min-height: 38px !important;
  }
  div.st-key-share_icon_row button:hover{
    box-shadow: 0 10px 22px rgba(0,0,0,0.07);
    transform: translateY(-1px);
  }
  div.st-key-share_icon_row button:focus{
    outline: none !important;
    box-shadow: 0 0 0 4px rgba(255,140,66,0.14), 0 10px 22px rgba(0,0,0,0.07);
  }

  /* Top 3 list (Customers card) — keep native layout, add iOS styling */
  .top3-title{
    font-weight: 600;
    color: rgba(17,24,39,0.62);
    font-size: 0.86rem;
    margin-top: 6px;
  }
  .top3-badge{
    width: 24px;
    height: 24px;
    border-radius: 999px;
    background: rgba(255,45,85,0.12);
    color: rgba(255,45,85,0.95);
    border: 1px solid rgba(255,45,85,0.14);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 0.85rem;
    line-height: 1;
  }
  .top3-city{
    font-weight: 600;
    color: rgba(17,24,39,0.84);
    font-size: 0.95rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    display: block;
  }
  .top3-value{
    font-weight: 700;
    color: rgba(17,24,39,0.72);
    font-size: 0.95rem;
    text-align: right;
    white-space: nowrap;
    display: block;
  }

  /* Categories list style (like reference) */
  .cat-row{
    display:grid;
    grid-template-columns: 170px 84px 1fr 64px;
    align-items:center;
    gap: 12px;
    padding: 8px 0;
    font-family: Nunito, Inter, -apple-system, Segoe UI, sans-serif;
  }
  .cat-name{
    font-weight: 800;
    color: rgba(228,246,255,0.92);
    font-size: 0.95rem;
    text-shadow:
      0 0 8px rgba(98,168,190,0.26),
      0 1px 0 rgba(255,255,255,0.20);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .cat-delta{
    font-family: Nunito, Inter, -apple-system, Segoe UI, sans-serif;
    font-weight: 900;
    font-size: 0.90rem;
    text-align: right;
    color: rgba(218,240,249,0.82);
    text-shadow: 0 0 8px rgba(98,168,190,0.22);
  }
  .cat-delta.pos{
    color: rgba(120,236,216,0.98);
    text-shadow: 0 0 10px rgba(72,196,176,0.36);
  }
  .cat-delta.neg{
    color: rgba(255,165,174,0.96);
    text-shadow: 0 0 10px rgba(210,92,106,0.30);
  }
  .cat-dot{
    width: 14px;
    height: 14px;
    border-radius: 999px;
    background: rgba(68,170,170,0.38);
    border: 1px solid rgba(255,255,255,0.42);
    box-shadow: 0 6px 18px rgba(68,170,170,0.22), inset 0 1px 0 rgba(255,255,255,0.38);
    margin-right: 8px;
    flex: 0 0 auto;
  }
  .bar-wrap{
    position: relative;
    height: 12px;
    border-radius: 999px;
    background: rgba(16,35,56,0.10);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.34);
    overflow: hidden;
  }
  .bar-fill{
    position:absolute;
    left:0; top:0; bottom:0;
    border-radius: 999px;
    background: linear-gradient(90deg, rgba(70,126,154,0.68), rgba(68,170,170,0.78));
    box-shadow: 0 6px 16px rgba(68,170,170,0.20);
  }
  .bar-target{
    position:absolute;
    top:-4px;
    width: 2px;
    height: 20px;
    border-radius: 2px;
    background: rgba(214,154,92,0.84);
    box-shadow: 0 6px 16px rgba(214,154,92,0.24);
  }
  .pct-ring{
    width: 40px;
    height: 40px;
    border-radius: 999px;
    background:
      conic-gradient(rgba(122,201,88,0.66) var(--p), rgba(16,35,56,0.08) 0);
    display:flex;
    align-items:center;
    justify-content:center;
    position: relative;
    box-shadow:
      0 8px 18px rgba(122,201,88,0.16),
      inset 0 2px 4px rgba(255,255,255,0.32),
      inset 0 -4px 8px rgba(16,35,56,0.08);
  }
  .pct-ring::before{
    content:"";
    width: 30px;
    height: 30px;
    border-radius: 999px;
    background: rgba(255,255,255,0.26);
    border: 1px solid rgba(255,255,255,0.34);
    position:absolute;
    box-shadow:
      inset 0 1px 0 rgba(255,255,255,0.36),
      inset 0 -3px 8px rgba(16,35,56,0.06);
  }
  .pct-ring::after{
    content:"";
    position:absolute;
    left: 9px;
    top: 7px;
    width: 18px;
    height: 10px;
    border-radius: 999px;
    background: linear-gradient(180deg, rgba(255,255,255,0.36), rgba(255,255,255,0.00));
    transform: rotate(-18deg);
    pointer-events:none;
  }
  .pct-text{
    position: relative;
    font-weight: 700;
    font-size: 0.86rem;
    color: rgba(232,248,255,0.90);
    font-family: Nunito, Inter, -apple-system, Segoe UI, sans-serif;
    text-shadow: 0 0 8px rgba(98,168,190,0.28);
  }

  /* Mini table (segment summary) */
  .mini-table{
    margin-top: 14px;
    border-top: 1px solid rgba(255,255,255,0.22);
    padding-top: 10px;
  }
  .mini-head, .mini-row{
    display:grid;
    grid-template-columns: 1.1fr 0.7fr 0.9fr 0.8fr;
    gap: 10px;
    align-items:center;
  }
  .mini-head{
    font-size: 0.78rem;
    font-weight: 600;
    color: rgba(217,239,249,0.72);
    font-family: Nunito, Inter, -apple-system, Segoe UI, sans-serif;
    text-shadow: 0 0 8px rgba(98,168,190,0.18);
    padding: 4px 0 8px 0;
  }
  .mini-row{
    padding: 8px 0;
    border-top: 1px solid rgba(255,255,255,0.18);
  }
  .seg-pill{
    display:inline-flex;
    align-items:center;
    gap: 8px;
    font-weight: 650;
    color: rgba(228,246,255,0.88);
    font-family: Nunito, Inter, -apple-system, Segoe UI, sans-serif;
    text-shadow: 0 0 8px rgba(98,168,190,0.22);
    font-size: 0.90rem;
  }
  .seg-dot{
    width: 8px; height: 8px; border-radius: 999px;
    background: rgba(68,170,170,0.82);
    box-shadow: 0 0 0 4px rgba(68,170,170,0.16);
  }
  .seg-dot.steady{ background: rgba(70,126,154,0.80); box-shadow: 0 0 0 4px rgba(70,126,154,0.16); }
  .seg-dot.low{ background: rgba(214,154,92,0.80); box-shadow: 0 0 0 4px rgba(214,154,92,0.18); }

  /* Responsive: keep it stable */
  @media (max-width: 900px){
    .block-container{ padding-left: 12px; padding-right: 12px; }
    div[data-testid="stHorizontalBlock"]{ gap: 1rem !important; }
  }
</style>
"""

APPLE_PALETTE = ["#2F5870", "#2E6F73", "#4F7569", "#A7774B", "#8F4952"]
COLOR_BLUE = "#2E6F73"
COLOR_INDIGO = "#2F5870"
COLOR_PURPLE = "#8F4952"
COLOR_ORANGE = "#A7774B"
COLOR_MINT = "#4F7569"

# Warm-only palette (orange family) for cohesive glassmorphism
WARM_TINTS = [
    "rgba(47,88,112,0.92)",
    "rgba(46,111,115,0.86)",
    "rgba(79,117,105,0.78)",
    "rgba(167,119,75,0.76)",
    "rgba(88,108,124,0.70)",
    "rgba(143,73,82,0.64)",
]

# Deprecated alias for backwards compatibility
BLUE_TINTS = WARM_TINTS

# Brighter jelly-glass palette for the Share donut only.
SHARE_JELLY_TINTS = [
    "rgba(98,156,190,0.92)",
    "rgba(88,190,184,0.90)",
    "rgba(126,210,170,0.86)",
    "rgba(232,174,96,0.88)",
    "rgba(190,126,142,0.82)",
    "rgba(168,186,202,0.78)",
]

TREND_FRUIT_GREEN_BAR = "rgba(122,201,88,0.34)"
TREND_FRUIT_GREEN_LINE = "#8FD35F"

PLOTLY_LAYOUT_BASE: dict = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"family": "Nunito, Inter, -apple-system, Segoe UI, sans-serif", "color": "#102338"},
    "margin": {"l": 10, "r": 10, "t": 10, "b": 10},
    "showlegend": False,
    "hoverlabel": {
        "bgcolor": "rgba(255,255,255,0.72)",
        "bordercolor": "rgba(255,255,255,0.00)",
        "font": {"family": "Nunito, Inter, -apple-system, Segoe UI, sans-serif", "color": "#102338", "size": 12},
    },
}


@st.cache_data(show_spinner=False)
def get_clean_data(path: str) -> pd.DataFrame:
    raw = load_sales_orders(path)
    return clean_sales_orders(raw)


def render_kpi_card(label: str, value: str, *, sub: str | None = None, accent: str = "blue") -> None:
    # Deprecated: replaced by richer KPI cards with trend + sparkline.
    st.markdown(f"<div><strong>{label}</strong>: {value}</div>", unsafe_allow_html=True)


def _fmt_money(x: float) -> str:
    return f"${x:,.2f}"


def _fmt_money_short(x: float) -> str:
    x = float(x)
    ax = abs(x)
    if ax >= 1_000_000_000:
        return f"${x/1_000_000_000:.1f}B"
    if ax >= 1_000_000:
        return f"${x/1_000_000:.1f}M"
    if ax >= 1_000:
        return f"${x/1_000:.1f}K"
    return f"${x:,.2f}"


def _fmt_pct(x: float) -> str:
    if pd.isna(x):
        return "—"
    return f"{float(x):.2%}"


def _catmull_rom_to_bezier(points: list[tuple[float, float]]) -> str:
    if len(points) < 2:
        return ""

    def p(i: int) -> tuple[float, float]:
        i = max(0, min(i, len(points) - 1))
        return points[i]

    d = [f"M {points[0][0]:.2f} {points[0][1]:.2f}"]
    for i in range(len(points) - 1):
        p0 = p(i - 1)
        p1 = p(i)
        p2 = p(i + 1)
        p3 = p(i + 2)
        c1x = p1[0] + (p2[0] - p0[0]) / 6.0
        c1y = p1[1] + (p2[1] - p0[1]) / 6.0
        c2x = p2[0] - (p3[0] - p1[0]) / 6.0
        c2y = p2[1] - (p3[1] - p1[1]) / 6.0
        d.append(f"C {c1x:.2f} {c1y:.2f}, {c2x:.2f} {c2y:.2f}, {p2[0]:.2f} {p2[1]:.2f}")
    return " ".join(d)


def sparkline_svg(values: list[float], *, stroke: str = "rgba(0, 122, 255, 0.15)") -> str:
    vals = [float(v) for v in values if pd.notna(v)]
    if len(vals) < 2:
        return ""

    w, h = 100.0, 40.0
    vmin, vmax = min(vals), max(vals)
    span = (vmax - vmin) if vmax != vmin else 1.0

    pts: list[tuple[float, float]] = []
    for i, v in enumerate(vals):
        x = (i / (len(vals) - 1)) * w
        y = h - ((v - vmin) / span) * h
        pts.append((x, y))

    d = _catmull_rom_to_bezier(pts)
    if not d:
        return ""

    return f"""
    <svg viewBox="0 0 100 40" preserveAspectRatio="none" aria-hidden="true">
      <path d="{d}"
            fill="none"
            stroke="{stroke}"
            stroke-width="3.0"
            stroke-linecap="round"
            stroke-linejoin="round" />
    </svg>
    """.strip()


def _safe_div(n: float, d: float) -> float:
    return float(n) / float(d) if d else float("nan")


def monthly_fin_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a monthly table with:
      - gross_margin_pct
      - discount_rate_pct
      - aov_usd
      - profit_per_unit_usd
    """
    if df.empty:
        return pd.DataFrame()

    tmp = df.copy()
    tmp["Month"] = tmp["Date"].dt.to_period("M").dt.to_timestamp()

    # Basic monthly aggregates
    g = tmp.groupby("Month", as_index=False).agg(
        revenue_usd=("Revenue USD", "sum"),
        costs_usd=("Costs in USD", "sum"),
        discount_usd=("Discount USD", "sum"),
        profit_usd=("Profit", "sum"),
        sales_qty=("SalesQuantity", "sum"),
        orders=("OrderNumber", "nunique"),
    )

    g["gross_margin_pct"] = (g["revenue_usd"] - g["costs_usd"]).where(g["revenue_usd"] != 0) / g["revenue_usd"].where(
        g["revenue_usd"] != 0
    )
    denom = (g["revenue_usd"] + g["discount_usd"])
    g["discount_rate_pct"] = g["discount_usd"].where(denom != 0) / denom.where(denom != 0)
    g["aov_usd"] = g["revenue_usd"].where(g["orders"] != 0) / g["orders"].where(g["orders"] != 0)
    g["profit_per_unit_usd"] = g["profit_usd"].where(g["sales_qty"] != 0) / g["sales_qty"].where(g["sales_qty"] != 0)

    return g.sort_values("Month", ascending=True)


def _trend_dir(this_val: float, prev_val: float) -> tuple[str, str]:
    if pd.isna(prev_val) or prev_val == 0 or pd.isna(this_val):
        return "—", ""
    if this_val >= prev_val:
        return "↑", "up"
    return "↓", "down"


def render_fin_kpi_card(
    *,
    icon: str,
    title: str,
    value: str,
    arrow: str,
    arrow_cls: str,
    spark_values: list[float],
) -> None:
    svg = sparkline_svg(spark_values)
    arrow_html = f"<div class='trend {arrow_cls}'>{arrow}</div>" if arrow else "<div class='trend'>—</div>"
    st.markdown(
        f"""
        <div class="fin-kpi">
          <div class="spark">{svg}</div>
          {arrow_html}
          <div class="title-row">
            <div class="icon">{icon}</div>
            <div class="title">{title}</div>
          </div>
          <div class="value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_kpi_card_apple(*, icon: str, title: str, value: str, trend_pct: float | None) -> None:
    badge = "<span class='kpi-badge'>—</span>"
    if trend_pct is not None and pd.notna(trend_pct):
        cls = "badge-pos" if trend_pct >= 0 else "badge-neg"
        badge = f"<span class='kpi-badge {cls}'>{trend_pct:+.0%}</span>"

    st.markdown(
        f"""
        <div class="apple-card" style="height: 132px; display:flex; align-items:center; gap: 14px;">
          <div class="kpi-icon">{icon}</div>
          <div style="display:flex; flex-direction:column; justify-content:space-between; height: 100%; padding: 2px 0;">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
            <div>{badge}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_apple_style(fig: go.Figure) -> go.Figure:
    fig.update_layout(**PLOTLY_LAYOUT_BASE)
    # Absolute minimalist: no axis lines, no grids, no backgrounds
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        showline=False,
        ticks="",
        mirror=False,
        tickfont={"family": "Nunito, Inter, sans-serif", "size": 11, "color": "rgba(16,35,56,0.62)"},
    )
    fig.update_yaxes(
        showgrid=False,
        zeroline=False,
        showline=False,
        ticks="",
        mirror=False,
        tickfont={"family": "Nunito, Inter, sans-serif", "size": 11, "color": "rgba(16,35,56,0.62)"},
    )
    fig.update_layout(showlegend=False, legend={"bgcolor": "rgba(0,0,0,0)"}, bargap=0.70)

    # Smooth lines + unify stroke widths
    for tr in fig.data:
        if getattr(tr, "type", None) in {"scatter"}:
            # spline + thicker stroke per spec
            tr.update(line={"width": 4, "shape": "spline"})
        if getattr(tr, "type", None) in {"bar"}:
            # Rounded bars via layout + no border
            tr.update(marker={"line": {"width": 0}})

    # Rounded bars (supported in modern plotly)
    fig.update_layout(barcornerradius=12)
    return fig


def compute_mom_growth_pct(df: pd.DataFrame, value_col: str) -> tuple[float | None, pd.Period | None]:
    """
    Month-over-month growth percentage for `value_col`, using the latest month in df as "this month".
    Returns (growth_pct, this_month_period).
    """
    if df.empty or "Date" not in df.columns or value_col not in df.columns:
        return None, None

    dmax = pd.to_datetime(df["Date"]).max()
    if pd.isna(dmax):
        return None, None

    this_m = pd.Period(dmax, freq="M")
    prev_m = this_m - 1

    this_mask = df["Date"].dt.to_period("M") == this_m
    prev_mask = df["Date"].dt.to_period("M") == prev_m

    this_val = float(df.loc[this_mask, value_col].sum())
    prev_val = float(df.loc[prev_mask, value_col].sum())
    if prev_val == 0:
        return None, this_m
    return (this_val - prev_val) / prev_val, this_m


def classify_products_by_margin(
    df: pd.DataFrame,
    *,
    product_col_candidates: tuple[str, ...] = ("ProdDescr", "Product"),
    high_threshold: float = 0.35,
    low_threshold: float = 0.15,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Classify products into: 高毛利 / 稳健 / 低利 based on Profit Margin.

    Returns:
    - product_level: per-product aggregates + segment label
    - segment_agg: per-segment aggregates (count, revenue, profit, avg margin)
    """
    product_col = next((c for c in product_col_candidates if c in df.columns), None)
    if product_col is None or df.empty:
        product_level = pd.DataFrame(columns=["segment", "revenue_usd", "profit_usd", "margin"])
        segment_agg = pd.DataFrame(columns=["segment", "product_count", "revenue_usd", "profit_usd", "avg_margin"])
        return product_level, segment_agg

    g = (
        df.groupby(product_col, as_index=False)
        .agg(revenue_usd=("Revenue USD", "sum"), profit_usd=("Profit", "sum"))
        .copy()
    )
    g["margin"] = g["profit_usd"].where(g["revenue_usd"] != 0) / g["revenue_usd"].where(g["revenue_usd"] != 0)

    def _seg(m: float) -> str:
        if pd.isna(m):
            return "稳健"
        if m >= high_threshold:
            return "高毛利"
        if m < low_threshold:
            return "低利"
        return "稳健"

    g["segment"] = g["margin"].apply(_seg)

    seg = (
        g.groupby("segment", as_index=False)
        .agg(
            product_count=(product_col, "count"),
            revenue_usd=("revenue_usd", "sum"),
            profit_usd=("profit_usd", "sum"),
            avg_margin=("margin", "mean"),
        )
        .sort_values("revenue_usd", ascending=False)
    )

    return g, seg


def _fmt_int(x: int) -> str:
    return f"{x:,}"


def fig_time_trend(monthly: pd.DataFrame) -> go.Figure:
    """
    Dual-axis trend:
    - Revenue USD: bar (left axis)
    - Profit: line (right axis)
    """
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(
            x=monthly["Month"],
            y=monthly["Revenue USD"],
            name="Revenue",
            marker={"color": TREND_FRUIT_GREEN_BAR, "opacity": 0.78, "line": {"width": 0}},
            width=18 * 24 * 60 * 60 * 1000,  # ~18 days in ms => narrower month bars
            hovertemplate="Month: %{x|%Y-%m}<br>Revenue: $%{y:,.2f}<extra></extra>",
        ),
        secondary_y=False,
    )

    # Profit: gradient (or translucent) fill + spline line
    x = monthly["Month"]
    y = monthly["Profit"]
    try:
        profit_fill = go.Scatter(
            x=x,
            y=y,
            mode="lines",
            line={"color": "rgba(0,0,0,0)", "width": 0},
            fill="tozeroy",
            fillgradient={
                "type": "vertical",
                "colorscale": [
                    [0.0, "rgba(143,211,95,0.30)"],
                    [0.6, "rgba(143,211,95,0.13)"],
                    [1.0, "rgba(143,211,95,0.00)"],
                ],
            },
            hoverinfo="skip",
            name="Profit (fill)",
        )
    except Exception:
        # Fallback for Plotly versions without fillgradient support
        profit_fill = go.Scatter(
            x=x,
            y=y,
            mode="lines",
            line={"color": "rgba(0,0,0,0)", "width": 0},
            fill="tozeroy",
            fillcolor="rgba(143,211,95,0.16)",
            hoverinfo="skip",
            name="Profit (fill)",
        )
    fig.add_trace(profit_fill, secondary_y=True)

    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            name="Profit",
            mode="lines",
            line={"color": TREND_FRUIT_GREEN_LINE, "width": 4, "shape": "spline"},
            hovertemplate="Month: %{x|%Y-%m}<br>Profit: $%{y:,.2f}<extra></extra>",
        ),
        secondary_y=True,
    )

    fig.update_layout(autosize=True)
    return apply_apple_style(fig)


def fig_bubble_map(df: pd.DataFrame, *, location_level: str = "country") -> go.Figure:
    """
    Bubble map:
    - bubble size: Revenue USD
    - bubble color: Profit Margin

    Preferred: Scatter Mapbox when lat/lon exist.
    Fallback: Scatter Geo using Country/City names to keep it working without geocoding.
    """
    level = location_level.lower()
    loc_col = "Country" if level == "country" else "City"
    if loc_col not in df.columns:
        loc_col = "Country" if "Country" in df.columns else ("City" if "City" in df.columns else None)
    if loc_col is None:
        fig = go.Figure()
        fig.update_layout(**PLOTLY_LAYOUT_BASE)
        return fig

    agg = (
        df.groupby(loc_col, as_index=False)
        .agg(
            revenue_usd=("Revenue USD", "sum"),
            profit_usd=("Profit", "sum"),
            margin=("Profit Margin", "mean"),
        )
        .sort_values("revenue_usd", ascending=False)
    )

    # if we have coordinates, use Mapbox
    lat_col = next((c for c in ["Latitude", "Lat", "latitude", "lat"] if c in df.columns), None)
    lon_col = next((c for c in ["Longitude", "Lon", "longitude", "lon", "Lng", "lng"] if c in df.columns), None)
    if lat_col and lon_col:
        coords = df[[loc_col, lat_col, lon_col]].dropna().drop_duplicates(subset=[loc_col])
        agg = agg.merge(coords, on=loc_col, how="left").dropna(subset=[lat_col, lon_col])
        fig = px.scatter_mapbox(
            agg,
            lat=lat_col,
            lon=lon_col,
            size="revenue_usd",
            color="margin",
            size_max=40,
            hover_name=loc_col,
            hover_data={"revenue_usd": ":,.2f", "profit_usd": ":,.2f", "margin": ":.2%"},
            color_continuous_scale=[(0.0, "#FFF3E0"), (0.5, "#FFCC80"), (1.0, "#FF8C42")],
            zoom=1,
        )
        fig.update_layout(
            **PLOTLY_LAYOUT_BASE,
            mapbox_style="carto-positron",
            autosize=True,
        )
        fig.update_traces(
            hovertemplate=(
                f"{loc_col}: %{{hovertext}}<br>"
                "Revenue: $%{customdata[0]:,.2f}<br>"
                "Profit: $%{customdata[1]:,.2f}<br>"
                "Profit margin: %{customdata[2]:.2%}<extra></extra>"
            ),
            customdata=agg[["revenue_usd", "profit_usd", "margin"]].to_numpy(),
        )
        fig.update_layout(coloraxis_colorbar={"title": "Profit Margin"})
        fig.update_layout(
            coloraxis_colorbar={
                "title": "",
                "tickfont": {"size": 11},
                "outlinewidth": 0,
                "bgcolor": "rgba(255,255,255,0)",
            }
        )
        return fig

    # fallback: geo scatter by name (no lat/lon required)
    fig = px.scatter_geo(
        agg.head(60),
        locations=loc_col,
        locationmode="country names" if loc_col == "Country" else None,
        size="revenue_usd",
        color="margin",
        size_max=40,
        hover_name=loc_col,
        hover_data={"revenue_usd": ":,.2f", "profit_usd": ":,.2f", "margin": ":.2%"},
        color_continuous_scale=[(0.0, "#FFF3E0"), (0.5, "#FFCC80"), (1.0, "#FF8C42")],
    )
    fig.update_layout(**PLOTLY_LAYOUT_BASE, autosize=True)
    fig.update_geos(
        showcountries=True,
        showcoastlines=False,
        showland=True,
        landcolor="rgba(225,245,254,0.45)",
        bgcolor="rgba(0,0,0,0)",
    )
    fig.update_traces(
        hovertemplate=(
            f"{loc_col}: %{{hovertext}}<br>"
            "Revenue: $%{customdata[0]:,.2f}<br>"
            "Profit: $%{customdata[1]:,.2f}<br>"
            "Profit margin: %{customdata[2]:.2%}<extra></extra>"
        ),
        customdata=agg.head(60)[["revenue_usd", "profit_usd", "margin"]].to_numpy(),
    )
    fig.update_layout(
        coloraxis_colorbar={
            "title": "",
            "tickfont": {"size": 11},
            "outlinewidth": 0,
            "bgcolor": "rgba(255,255,255,0)",
        }
    )
    return fig


def fig_category_mix(df: pd.DataFrame, category_col: str) -> go.Figure:
    """
    Horizontal bars for category performance, sorted by Profit (desc).
    """
    cat = (
        df.groupby(category_col, as_index=False)
        .agg(revenue_usd=("Revenue USD", "sum"), profit_usd=("Profit", "sum"), margin=("Profit Margin", "mean"))
        .sort_values("profit_usd", ascending=False)
        .head(12)
    )

    fig = px.bar(
        cat,
        x="profit_usd",
        y=category_col,
        orientation="h",
        color="profit_usd",
        color_continuous_scale=[(0.0, "rgba(255,140,66,0.20)"), (1.0, "rgba(255,140,66,0.95)")],
        hover_data={"revenue_usd": ":,.2f", "profit_usd": ":,.2f", "margin": ":.2%"},
    )
    fig.update_layout(autosize=True)
    fig = apply_apple_style(fig)
    fig.update_traces(
        hovertemplate=(
            f"Category: %{{y}}<br>"
            "Revenue: $%{customdata[0]:,.2f}<br>"
            "Profit: $%{x:,.2f}<br>"
            "Profit margin: %{customdata[1]:.2%}<extra></extra>"
        ),
        customdata=cat[["revenue_usd", "margin"]].to_numpy(),
        marker_line_width=0,
    )
    # Keep it clean: no visible colorbar, just subtle shade differences
    fig.update_layout(coloraxis_showscale=False)
    return fig


def fig_category_treemap(df: pd.DataFrame, category_col: str) -> go.Figure:
    """
    Treemap for categories:
    - size: Revenue USD
    - color: Profit (blue-only shades)
    """
    if df.empty:
        fig = go.Figure()
        fig.update_layout(**PLOTLY_LAYOUT_BASE)
        return fig

    cat_col = "CatDescr" if "CatDescr" in df.columns else category_col
    prod_col = "ProdDescr" if "ProdDescr" in df.columns else ("Product" if "Product" in df.columns else None)
    if prod_col is None:
        # Fallback to single-level treemap
        prod_col = cat_col

    tmp = df[[cat_col, prod_col, "Revenue USD", "Profit Margin"]].copy()
    tmp[cat_col] = tmp[cat_col].astype("string").fillna("Unknown")
    tmp[prod_col] = tmp[prod_col].astype("string").fillna("Unknown")

    agg = (
        tmp.groupby([cat_col, prod_col], as_index=False)
        .agg(revenue_usd=("Revenue USD", "sum"), margin=("Profit Margin", "mean"))
        .sort_values("revenue_usd", ascending=False)
    )

    # Keep top products for readability while preserving hierarchy
    agg = agg.head(120)

    fig = px.treemap(
        agg,
        path=[cat_col, prod_col],
        values="revenue_usd",
        color="margin",
        color_continuous_scale=["#FFF3E0", "#FF8C42"],
        range_color=(0.0, float(max(0.01, agg["margin"].max()))),
    )

    fig.update_traces(
        # Only show labels where there's enough area
        textinfo="label",
        textfont={"size": 13, "color": "rgba(17,24,39,0.75)", "family": "Inter, SF Pro Display, sans-serif"},
        textposition="middle center",
        marker={"line": {"width": 0}},
        opacity=0.85,
        pathbar={"visible": False},
        root_color="rgba(0,0,0,0)",
        tiling={"pad": 8},
        hovertemplate=(
            "Product: %{label}<br>"
            "Revenue: $%{value:,.2f}<br>"
            "Profit margin: %{color:.2%}<extra></extra>"
        ),
    )

    fig.update_layout(
        autosize=True,
        margin={"t": 0, "l": 0, "r": 0, "b": 0},
        uniformtext_minsize=12,
        uniformtext_mode="hide",
        coloraxis_showscale=False,
    )
    # apply minimalist/typography defaults without reintroducing margins
    fig = apply_apple_style(fig)
    fig.update_layout(margin={"t": 0, "l": 0, "r": 0, "b": 0}, coloraxis_showscale=False)
    return fig


def render_categories_target_list(*, key: str, df: pd.DataFrame, margin_segments: pd.DataFrame | None = None) -> None:
    """
    Replace treemap with a compact 'Top 5 Categories | Sales vs Targets' list.
    - Current: latest month revenue per category
    - Target: previous month revenue per category
    - Delta: current - target
    - Right ring: current share of total revenue (latest month)
    """
    cat_col = "CatDescr" if "CatDescr" in df.columns else ("ProdCat" if "ProdCat" in df.columns else None)
    if cat_col is None or df.empty:
        render_chart_card(
            key=key,
            title="Top 5 Categories",
            subtitle="Sales vs Targets",
            fig=go.Figure().update_layout(**PLOTLY_LAYOUT_BASE),
        )
        return

    dmax = pd.to_datetime(df["Date"]).max()
    if pd.isna(dmax):
        return
    this_m = pd.Period(dmax, freq="M")
    prev_m = this_m - 1

    dfm = df.copy()
    dfm["Month"] = dfm["Date"].dt.to_period("M")

    cur = dfm.loc[dfm["Month"] == this_m].groupby(cat_col, as_index=False)["Revenue USD"].sum().rename(columns={"Revenue USD": "cur"})
    prev = dfm.loc[dfm["Month"] == prev_m].groupby(cat_col, as_index=False)["Revenue USD"].sum().rename(columns={"Revenue USD": "prev"})
    merged = cur.merge(prev, on=cat_col, how="left").fillna({"prev": 0.0})
    merged["delta"] = merged["cur"] - merged["prev"]

    total = float(merged["cur"].sum()) if len(merged) else 0.0
    merged["share"] = merged["cur"].apply(lambda x: (float(x) / total) if total else 0.0)

    top = merged.sort_values("cur", ascending=False).head(5).reset_index(drop=True)
    max_cur = float(top["cur"].max()) if len(top) else 1.0
    max_target = float(max(top["prev"].max(), max_cur, 1.0))

    with st.container(key=key):
        st.markdown(
            """
            <div class="card-header" style="position:relative; z-index:1;">
              <div>
                <div class="apple-title" style="margin:0;">Top 5 Categories</div>
                <div class="apple-subtitle">Sales vs Targets</div>
              </div>
              <div class="micro-icon">i</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        rows_html: list[str] = []
        for _, r in top.iterrows():
            name = str(r[cat_col])
            cur_v = float(r["cur"])
            prev_v = float(r["prev"])
            delta = float(r["delta"])
            share = float(r["share"])

            fill_w = 100.0 * (cur_v / max_cur) if max_cur else 0.0
            target_x = 100.0 * (prev_v / max_target) if max_target else 0.0

            delta_cls = "pos" if delta >= 0 else "neg"
            # Always show delta in $K for consistency (fixes cases like Accessoire missing K)
            sign = "+" if delta >= 0 else "−"
            delta_txt = f"{sign}${abs(delta)/1000:.1f}K"

            rows_html.append(
                f"""
                <div class="cat-row">
                  <div style="display:flex; align-items:center; gap:10px; min-width:0;">
                    <span class="cat-dot"></span>
                    <span class="cat-name">{name}</span>
                  </div>
                  <div class="cat-delta {delta_cls}">{delta_txt}</div>
                  <div class="bar-wrap">
                    <div class="bar-fill" style="width:{fill_w:.1f}%;"></div>
                    <div class="bar-target" style="left:{min(max(target_x,2.0),98.0):.1}%;"></div>
                  </div>
                  <div class="pct-ring" style="--p:{share*100:.1f}%;">
                    <span class="pct-text">{share*100:.1f}%</span>
                  </div>
                </div>
                """
            )

        st.markdown("".join(rows_html), unsafe_allow_html=True)

        # Use the leftover space for a compact segment summary table
        if margin_segments is not None:
            # Always show 3 segments; render in English
            seg_map = {
                "高毛利": "High margin",
                "稳健": "Steady",
                "低利": "Low margin",
                "High margin": "High margin",
                "Steady": "Steady",
                "Low margin": "Low margin",
            }
            order = ["High margin", "Steady", "Low margin"]

            ms = margin_segments.copy() if not margin_segments.empty else pd.DataFrame(columns=["segment", "product_count", "revenue_usd", "avg_margin", "profit_usd"])
            if "segment" in ms.columns:
                ms["segment"] = ms["segment"].astype("string").map(lambda x: seg_map.get(str(x), str(x)))

            # Fill missing segments with zeros
            full = pd.DataFrame({"segment": order})
            ms = full.merge(ms, on="segment", how="left")
            for col, default in [
                ("product_count", 0),
                ("revenue_usd", 0.0),
                ("profit_usd", 0.0),
                ("avg_margin", float("nan")),
            ]:
                if col not in ms.columns:
                    ms[col] = default
                else:
                    ms[col] = ms[col].fillna(default)

            def _dot(seg: str) -> str:
                if seg == "High margin":
                    return "seg-dot"
                if seg == "Low margin":
                    return "seg-dot low"
                return "seg-dot steady"

            seg_rows: list[str] = []
            for _, r in ms.iterrows():
                seg = str(r.get("segment", "—"))
                cnt = int(r.get("product_count", 0))
                rev = float(r.get("revenue_usd", 0.0))
                am = float(r.get("avg_margin", float("nan")))
                seg_rows.append(
                    (
                        f"<div class=\"mini-row\">"
                        f"<div><span class=\"seg-pill\"><span class=\"{_dot(seg)}\"></span>{seg}</span></div>"
                        f"<div style=\"text-align:right; font-weight:750; color:rgba(228,246,255,0.86); text-shadow:0 0 8px rgba(98,168,190,0.22);\">{cnt:,}</div>"
                        f"<div style=\"text-align:right; font-weight:750; color:rgba(228,246,255,0.86); text-shadow:0 0 8px rgba(98,168,190,0.22);\">{_fmt_money_short(rev)}</div>"
                        f"<div style=\"text-align:right; font-weight:750; color:rgba(228,246,255,0.86); text-shadow:0 0 8px rgba(98,168,190,0.22);\">{_fmt_pct(am)}</div>"
                        f"</div>"
                    )
                )

            st.markdown(
                (
                    "<div class=\"mini-table\">"
                    "<div class=\"mini-head\">"
                    "<div>Segment</div>"
                    "<div style=\"text-align:right;\">Products</div>"
                    "<div style=\"text-align:right;\">Revenue</div>"
                    "<div style=\"text-align:right;\">Avg Margin</div>"
                    "</div>"
                    + "".join(seg_rows)
                    + "</div>"
                ),
                unsafe_allow_html=True,
            )


def fig_share_donut(df: pd.DataFrame, *, dim: str | None = None) -> go.Figure:
    if dim is None:
        dim = "SalesOrg" if "SalesOrg" in df.columns else ("Country" if "Country" in df.columns else None)
    if dim is None or df.empty:
        fig = go.Figure()
        fig.update_layout(**PLOTLY_LAYOUT_BASE)
        return fig

    agg = (
        df.groupby(dim, as_index=False)["Revenue USD"]
        .sum()
        .sort_values("Revenue USD", ascending=False)
        .head(6)
    )
    fig = px.pie(
        agg,
        values="Revenue USD",
        names=dim,
        hole=0.70,
        color_discrete_sequence=SHARE_JELLY_TINTS,
    )
    fig.update_traces(
        textinfo="label",
        textposition="inside",
        insidetextorientation="tangential",
        textfont={
            "family": "Nunito, Inter, -apple-system, Segoe UI, sans-serif",
            "size": 13,
            "color": "rgba(13,31,49,0.86)",
        },
        texttemplate="<b>%{label}</b>",
        hovertemplate=f"{dim}: %{{label}}<br>Revenue: $%{{value:,.2f}}<br>Share: %{{percent}}<extra></extra>",
        marker={"line": {"width": 2, "color": "rgba(255,255,255,0.34)"}},
        opacity=0.80,
        pull=[0.012, 0.008, 0.006, 0.004, 0.002, 0.0][: len(agg)],
    )
    # Strong, visible nudge: shrink domain and shift up-left, then re-apply after styling
    nudge_domain = {"x": [0.00, 0.72], "y": [0.22, 0.96]}
    fig.update_layout(autosize=True, margin={"t": 0, "l": 0, "r": 0, "b": 0})
    fig.update_traces(selector=dict(type="pie"), domain=nudge_domain)

    fig = apply_apple_style(fig)
    fig.update_layout(margin={"t": 0, "l": 0, "r": 0, "b": 0})
    fig.update_traces(selector=dict(type="pie"), domain=nudge_domain)
    return fig


def fig_top_customers(df: pd.DataFrame, *, top_n: int = 8) -> go.Figure:
    cust_col = "CustDescr" if "CustDescr" in df.columns else ("Customer" if "Customer" in df.columns else None)
    if cust_col is None or df.empty:
        fig = go.Figure()
        fig.update_layout(**PLOTLY_LAYOUT_BASE)
        return fig

    top_customers = (
        df.groupby(cust_col, as_index=False)["Revenue USD"]
        .sum()
        .sort_values("Revenue USD", ascending=False)
        .head(top_n)
    )
    fig = px.bar(
        top_customers,
        x="Revenue USD",
        y=cust_col,
        orientation="h",
        color="Revenue USD",
        color_continuous_scale=[(0.0, "rgba(255,140,66,0.25)"), (1.0, "rgba(255,140,66,0.95)")],
    )
    fig.update_traces(
        hovertemplate=("Customer: %{y}<br>Revenue: $%{x:,.2f}<extra></extra>"),
        marker={"line": {"width": 0}},
    )
    fig.update_layout(autosize=True)
    fig = apply_apple_style(fig)
    fig.update_layout(coloraxis_showscale=False)
    return fig


def fig_customer_hotspots(df: pd.DataFrame) -> go.Figure:
    """
    Customer hotspots map (works without geocoding):
    - Aggregates revenue by Country (fallback), bubbles represent revenue.
    - Hover shows top customer in that country and total customers.
    If lat/lon columns exist, will use mapbox scatter; otherwise scatter_geo.
    """
    if df.empty:
        fig = go.Figure()
        fig.update_layout(**PLOTLY_LAYOUT_BASE)
        return fig

    country_col = "Country" if "Country" in df.columns else None
    cust_col = "CustDescr" if "CustDescr" in df.columns else ("Customer" if "Customer" in df.columns else None)
    if country_col is None or cust_col is None:
        fig = go.Figure()
        fig.update_layout(**PLOTLY_LAYOUT_BASE)
        return fig

    tmp = df[[country_col, cust_col, "Revenue USD"]].copy()
    tmp[country_col] = tmp[country_col].astype("string").fillna("Unknown")
    tmp[cust_col] = tmp[cust_col].astype("string").fillna("Unknown")

    by_cc = tmp.groupby([country_col, cust_col], as_index=False)["Revenue USD"].sum()
    top_cust = by_cc.sort_values("Revenue USD", ascending=False).groupby(country_col, as_index=False).head(1)
    top_cust = top_cust.rename(columns={cust_col: "top_customer", "Revenue USD": "top_customer_revenue"})

    agg = (
        tmp.groupby(country_col, as_index=False)
        .agg(revenue_usd=("Revenue USD", "sum"), customer_count=(cust_col, "nunique"))
        .merge(top_cust[[country_col, "top_customer", "top_customer_revenue"]], on=country_col, how="left")
        .sort_values("revenue_usd", ascending=False)
    )

    # Prefer mapbox only when coordinates exist
    lat_col = next((c for c in ["Latitude", "Lat", "latitude", "lat"] if c in df.columns), None)
    lon_col = next((c for c in ["Longitude", "Lon", "longitude", "lon", "Lng", "lng"] if c in df.columns), None)
    if lat_col and lon_col:
        coords = df[[country_col, lat_col, lon_col]].dropna().drop_duplicates(subset=[country_col])
        agg = agg.merge(coords, on=country_col, how="left").dropna(subset=[lat_col, lon_col])
        fig = px.scatter_mapbox(
            agg,
            lat=lat_col,
            lon=lon_col,
            size="revenue_usd",
            color="revenue_usd",
            size_max=36,
            zoom=1,
            color_continuous_scale=[(0.0, "rgba(255,140,66,0.25)"), (1.0, "rgba(255,140,66,0.95)")],
        )
        fig.update_traces(
            hovertemplate=(
                "Country: %{customdata[0]}<br>"
                "Revenue: $%{customdata[1]:,.2f}<br>"
                "Customers: %{customdata[2]:,.0f}<br>"
                "Top customer: %{customdata[3]}<extra></extra>"
            ),
            customdata=agg[[country_col, "revenue_usd", "customer_count", "top_customer"]].to_numpy(),
            marker={"line": {"width": 0}},
            opacity=0.85,
        )
        fig.update_layout(mapbox_style="carto-positron", autosize=True)
        fig.update_layout(coloraxis_showscale=False)
        return apply_apple_style(fig)

    # No coords: scatter_geo by country names
    fig = px.scatter_geo(
        agg.head(60),
        locations=country_col,
        locationmode="country names",
        size="revenue_usd",
        color="revenue_usd",
        size_max=36,
        color_continuous_scale=[(0.0, "rgba(255,140,66,0.25)"), (1.0, "rgba(255,140,66,0.95)")],
    )
    fig.update_traces(
        hovertemplate=(
            "Country: %{customdata[0]}<br>"
            "Revenue: $%{customdata[1]:,.2f}<br>"
            "Customers: %{customdata[2]:,.0f}<br>"
            "Top customer: %{customdata[3]}<extra></extra>"
        ),
        customdata=agg.head(60)[[country_col, "revenue_usd", "customer_count", "top_customer"]].to_numpy(),
        marker={"line": {"width": 0}},
        opacity=0.85,
    )
    fig.update_layout(autosize=True, coloraxis_showscale=False)
    fig.update_geos(
        showcountries=True,
        showcoastlines=False,
        showland=True,
        landcolor="rgba(225,245,254,0.35)",
        bgcolor="rgba(0,0,0,0)",
    )
    return apply_apple_style(fig)


CITY_COORDS: dict[tuple[str, str], tuple[float, float]] = {
    # Germany (DE)
    ("DE", "München"): (48.1351, 11.5820),
    ("DE", "Munchen"): (48.1351, 11.5820),
    ("DE", "Hamburg"): (53.5511, 9.9937),
    ("DE", "Stuttgart"): (48.7758, 9.1829),
    ("DE", "Berlin"): (52.5200, 13.4050),
    ("DE", "Heidelberg"): (49.3988, 8.6724),
    ("DE", "Frankfurt"): (50.1109, 8.6821),
    ("DE", "Frankfurt am Main"): (50.1109, 8.6821),
    ("DE", "Hannover"): (52.3759, 9.7320),
    ("DE", "Bochum"): (51.4818, 7.2162),
    ("DE", "Leipzig"): (51.3397, 12.3731),
    ("DE", "Magdeburg"): (52.1205, 11.6276),
    ("DE", "Anklam"): (53.8560, 13.6890),
    # United States (US)
    ("US", "Boston"): (42.3601, -71.0589),
    ("US", "Palo Alto"): (37.4419, -122.1430),
    ("US", "Denver"): (39.7392, -104.9903),
    ("US", "New York City"): (40.7128, -74.0060),
    ("US", "Seattle"): (47.6062, -122.3321),
    ("US", "Chicago"): (41.8781, -87.6298),
    ("US", "Detroit"): (42.3314, -83.0458),
    ("US", "Irvine"): (33.6846, -117.8265),
    ("US", "Washington DC"): (38.9072, -77.0369),
    ("US", "Philadelphia"): (39.9526, -75.1652),
    ("US", "Atlanta"): (33.7490, -84.3880),
    ("US", "Grand Rapids"): (42.9634, -85.6681),
}


def fig_customer_heatmap(df: pd.DataFrame, *, focus_country: str = "US") -> go.Figure:
    """
    Density heatmap (Mapbox) of customer revenue hotspots.
    Uses a static (Country, City) -> (lat, lon) lookup for top cities.
    Falls back to scatter_geo if coordinates missing.
    """
    if df.empty or "Country" not in df.columns or "City" not in df.columns:
        fig = go.Figure()
        fig.update_layout(**PLOTLY_LAYOUT_BASE)
        return fig

    focus_country = str(focus_country).strip().upper()

    tmp = df[["Country", "City", "Revenue USD"]].copy()
    tmp["Country"] = tmp["Country"].astype("string").fillna("Unknown").str.strip().str.upper()
    tmp["City"] = tmp["City"].astype("string").fillna("Unknown").str.strip()

    if focus_country in {"US", "DE"}:
        tmp = tmp.loc[tmp["Country"] == focus_country].copy()

    agg = (
        tmp.groupby(["Country", "City"], as_index=False)["Revenue USD"]
        .sum()
        .sort_values("Revenue USD", ascending=False)
        .head(200)
    )

    # Map coords
    lats: list[float] = []
    lons: list[float] = []
    for c, city in zip(agg["Country"].tolist(), agg["City"].tolist()):
        latlon = CITY_COORDS.get((str(c), str(city)))
        if latlon is None:
            lats.append(float("nan"))
            lons.append(float("nan"))
        else:
            lats.append(latlon[0])
            lons.append(latlon[1])
    agg["lat"] = lats
    agg["lon"] = lons
    agg = agg.dropna(subset=["lat", "lon"])

    if agg.empty:
        # fallback: country-only bubble map
        return fig_customer_hotspots(df)

    # Emphasize hotspots by compressing the upper range (better contrast)
    zmax = float(agg["Revenue USD"].quantile(0.92)) if len(agg) >= 10 else float(agg["Revenue USD"].max())
    zmax = max(zmax, 1.0)

    if focus_country == "DE":
        center = {"lat": 51.1657, "lon": 10.4515}
        zoom = 5.0
    else:
        center = {"lat": 39.5, "lon": -98.35}
        zoom = 3.2

    fig = px.density_mapbox(
        agg,
        lat="lat",
        lon="lon",
        z="Revenue USD",
        radius=22,
        center=center,
        zoom=zoom,
        mapbox_style="carto-positron",
        range_color=(0.0, zmax),
        # Deeper purple hotspot ramp (Apple indigo) with stronger opacity
        color_continuous_scale=[
            (0.0, "rgba(255,45,85,0.00)"),
            (0.25, "rgba(255,45,85,0.18)"),
            (0.55, "rgba(255,45,85,0.45)"),
            (0.80, "rgba(255,45,85,0.70)"),
            (1.0, "rgba(255,45,85,0.95)"),
        ],
        hover_name="City",
        hover_data={"Country": True, "Revenue USD": ":,.2f", "lat": False, "lon": False},
    )
    fig.update_layout(autosize=True, coloraxis_showscale=False)
    fig = apply_apple_style(fig)
    fig.update_layout(coloraxis_showscale=False)
    # Overlay key cities as "pins" to make major cities pop
    top = agg.sort_values("Revenue USD", ascending=False).head(12)
    fig.add_trace(
        go.Scattermapbox(
            lat=top["lat"],
            lon=top["lon"],
            mode="markers",
            marker={
                "size": 18,
                "color": "rgba(255,45,85,0.22)",  # halo
                "opacity": 1.0,
            },
            text=top["City"],
            customdata=top[["Country", "Revenue USD"]].to_numpy(),
            hovertemplate="City: %{text}<br>Country: %{customdata[0]}<br>Revenue: $%{customdata[1]:,.2f}<extra></extra>",
            name="Top cities",
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scattermapbox(
            lat=top["lat"],
            lon=top["lon"],
            mode="markers",
            marker={
                "size": 10,
                "color": "rgba(255,255,255,0.78)",  # faux stroke base
                "opacity": 1.0,
            },
            text=top["City"],
            customdata=top[["Country", "Revenue USD"]].to_numpy(),
            hovertemplate="City: %{text}<br>Country: %{customdata[0]}<br>Revenue: $%{customdata[1]:,.2f}<extra></extra>",
            name="Top cities (stroke)",
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scattermapbox(
            lat=top["lat"],
            lon=top["lon"],
            mode="markers",
            marker={
                "size": 8,
                "color": "rgba(255,45,85,0.95)",  # core
                "opacity": 1.0,
            },
            text=top["City"],
            customdata=top[["Country", "Revenue USD"]].to_numpy(),
            hovertemplate="City: %{text}<br>Country: %{customdata[0]}<br>Revenue: $%{customdata[1]:,.2f}<extra></extra>",
            name="Top cities (core)",
            showlegend=False,
        )
    )

    fig.update_traces(
        selector=dict(type="densitymapbox"),
        hovertemplate="City: %{hovertext}<br>Country: %{customdata[0]}<br>Revenue: $%{customdata[1]:,.2f}<extra></extra>",
    )
    return fig


def top_cities_list(df: pd.DataFrame, *, focus_country: str, n: int = 3) -> list[tuple[str, float]]:
    if df.empty or "Country" not in df.columns or "City" not in df.columns:
        return []
    focus_country = str(focus_country).strip().upper()
    tmp = df.copy()
    tmp["Country"] = tmp["Country"].astype("string").fillna("Unknown").str.strip().str.upper()
    tmp["City"] = tmp["City"].astype("string").fillna("Unknown").str.strip()
    tmp = tmp.loc[tmp["Country"] == focus_country].copy()
    if tmp.empty:
        return []
    top = (
        tmp.groupby("City", as_index=False)["Revenue USD"]
        .sum()
        .sort_values("Revenue USD", ascending=False)
        .head(n)
    )
    return [(str(r["City"]), float(r["Revenue USD"])) for _, r in top.iterrows()]


def render_customers_map_card(*, key: str, df: pd.DataFrame) -> None:
    with st.container(key=key):
        st.markdown(
            """
            <div class="card-header" style="position:relative; z-index:1;">
              <div>
                <div class="apple-title" style="margin:0;">Customers</div>
                <div class="apple-subtitle">Heatmap hotspots + Top cities</div>
              </div>
              <div class="micro-icon">i</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        focus_country = st.radio(
            "Country focus",
            options=["US", "DE"],
            horizontal=True,
            label_visibility="collapsed",
        )

        left, right = st.columns([3.0, 1.0], gap="small")
        with left:
            with st.container(key="cust_map_left"):
                fig = fig_customer_heatmap(df, focus_country=focus_country)
                fig.update_layout(height=420, margin={"t": 0, "l": 0, "r": 0, "b": 0})
                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    config={"displayModeBar": False, "responsive": True},
                )
        with right:
            with st.container(key="cust_map_right"):
                items = top_cities_list(df, focus_country=focus_country, n=3)
                if not items:
                    st.markdown("<div style='color: rgba(17,24,39,0.55); font-weight:600;'>No cities found.</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='top3-title'>Top 3 cities</div>", unsafe_allow_html=True)
                    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                    st.markdown("<div style='border-top: 1px solid rgba(0,0,0,0.06)'></div>", unsafe_allow_html=True)
                    for i, (city, rev) in enumerate(items, start=1):
                        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                        c1, c2, c3 = st.columns([0.20, 0.50, 0.30], gap="small")
                        with c1:
                            st.markdown(f"<span class='top3-badge'>{i}</span>", unsafe_allow_html=True)
                        with c2:
                            st.markdown(f"<span class='top3-city'>{city}</span>", unsafe_allow_html=True)
                        with c3:
                            st.markdown(f"<span class='top3-value'>{_fmt_money_short(rev)}</span>", unsafe_allow_html=True)


def render_chart_card(*, key: str, title: str, subtitle: str, fig: go.Figure) -> None:
    with st.container(key=key):
        st.markdown(
            f"""
            <div class="card-header" style="position:relative; z-index:1;">
              <div>
                <div class="apple-title" style="margin:0;">{title}</div>
                <div class="apple-subtitle">{subtitle}</div>
              </div>
              <div class="micro-icon">i</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        # For Share donut, render via HTML wrapper so we can precisely nudge position.
        if key == "card_share":
            with st.container(key=f"{key}_plotwrap"):
                html = pio.to_html(
                    fig,
                    include_plotlyjs="cdn",
                    full_html=False,
                    config={"displayModeBar": False, "responsive": True},
                )
                components.html(
                    f"""
                    <div class="share-plot-wrap">
                      <div style="transform: translate(36px, -10px) scale(1.02); transform-origin: top left;">
                        {html}
                      </div>
                    </div>
                    """,
                    height=360,
                )
            # Linked controls: icons switch the donut grouping dimension
            with st.container(key="share_icon_row"):
                c1, c2, c3, c4 = st.columns(4, gap="small")
                with c1:
                    if st.button("🏢", key="share_btn_salesorg", help="Group by SalesOrg", use_container_width=True):
                        st.session_state["share_dim"] = "SalesOrg"
                with c2:
                    if st.button("🌍", key="share_btn_country", help="Group by Country", use_container_width=True):
                        st.session_state["share_dim"] = "Country"
                with c3:
                    if st.button("🏷️", key="share_btn_category", help="Group by Category", use_container_width=True):
                        st.session_state["share_dim"] = "CatDescr"
                with c4:
                    if st.button("👤", key="share_btn_customer", help="Group by Customer", use_container_width=True):
                        st.session_state["share_dim"] = "CustDescr"
        else:
            with st.container(key=f"{key}_plotwrap"):
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})


def main() -> None:
    st.set_page_config(page_title="Global Bike Sales Dashboard", layout="wide", initial_sidebar_state="expanded")

    office_bg_layer = (
        f"url('{OFFICE_BG_URI}')"
        if OFFICE_BG_URI
        else "linear-gradient(120deg, #e6eff7 0%, #bfd0df 34%, #8298ad 61%, #27394f 100%)"
    )
    st.markdown(APPLE_GLOBAL_CSS.replace("__OFFICE_BG_LAYER__", office_bg_layer), unsafe_allow_html=True)
    st.markdown(
        """
        <div style="display:flex; align-items:baseline; gap:12px; margin-bottom: 14px;">
          <div style="
              font-size: 1.85rem;
              font-weight: 950;
              color: rgba(17,24,39,0.94);
              letter-spacing: -0.015em;
              text-shadow: 0 0 0.6px rgba(255,255,255,0.55), 0 10px 28px rgba(0,0,0,0.06);
            ">
            Executive Sales Overview
          </div>
          <div style="font-size: 1.05rem; font-weight: 850; color: rgba(17,24,39,0.50); letter-spacing: -0.01em;">
            Global Bike
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown(
            """
            <div style="padding: 10px 12px; border: 1px solid rgba(255,255,255,0.42); border-radius: 16px;
                        background: rgba(255,255,255,0.32); box-shadow: 0 12px 28px rgba(15,23,42,0.10), inset 0 1px 0 rgba(255,255,255,0.44);
                        backdrop-filter: blur(12px) saturate(1.04); -webkit-backdrop-filter: blur(12px) saturate(1.04);">
              <div style="font-size: 0.78rem; font-weight: 800; color: rgba(17,24,39,0.55); letter-spacing: 0.02em;">
                Developer
              </div>
              <div style="font-size: 1.05rem; font-weight: 900; color: #111827; margin-top: 2px;">
                Patrick.W
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Data source is fixed by default (no file-path control in sidebar)
        data_path = Path(DEFAULT_PATH)
        if not data_path.exists():
            st.error(
                "Data file not found.\n\n"
                "Please copy `Global Bike Sales Data (1).xlsx` into the same folder as `app.py` "
                "(the `bike_dashboard` project root), then redeploy/restart."
            )
            st.stop()

        df = get_clean_data(str(data_path))

        st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)
        st.subheader("Filters")
        dmin = df["Date"].min().date()
        dmax = df["Date"].max().date()
        date_range = st.date_input("Date range", value=(dmin, dmax), min_value=dmin, max_value=dmax)

        search = st.text_input("Search (Customer / Product)", value="", placeholder="e.g. Contoso / Road-150")

        # Use Date + Search to scope available dimension options (better UX)
        if isinstance(date_range, tuple) and len(date_range) == 2:
            _start, _end = date_range
        else:
            _start, _end = dmin, dmax

        seed = df.loc[(df["Date"].dt.date >= _start) & (df["Date"].dt.date <= _end)].copy()
        q = search.strip().lower()
        if q:
            search_cols = [c for c in ["CustDescr", "Customer", "ProdDescr", "Product"] if c in seed.columns]
            if search_cols:
                hay = seed[search_cols].astype("string").fillna("")
                m = False
                for c in search_cols:
                    m = m | hay[c].str.lower().str.contains(q, na=False)
                seed = seed.loc[m].copy()

        def _options(col: str) -> list[str]:
            if col not in seed.columns:
                return []
            return sorted(seed[col].astype("string").fillna("Unknown").unique().tolist())

        country_opts = _options("Country")
        prodcat_opts = _options("ProdCat")
        salesorg_opts = _options("SalesOrg")
        catdescr_opts = _options("CatDescr")

        selected_countries = st.multiselect("Country", options=country_opts, default=country_opts)
        selected_prodcats = st.multiselect("ProdCat", options=prodcat_opts, default=prodcat_opts)
        selected_salesorg = st.multiselect("SalesOrg", options=salesorg_opts, default=salesorg_opts)
        selected_catdescr = st.multiselect("CatDescr", options=catdescr_opts, default=catdescr_opts)

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = date_range
    else:
        start, end = dmin, dmax

    mask = (df["Date"].dt.date >= start) & (df["Date"].dt.date <= end)
    if search.strip():
        q = search.strip().lower()
        search_cols = [c for c in ["CustDescr", "Customer", "ProdDescr", "Product"] if c in df.columns]
        if search_cols:
            hay = df[search_cols].astype("string").fillna("")
            m = False
            for c in search_cols:
                m = m | hay[c].str.lower().str.contains(q, na=False)
            mask &= m

    if selected_countries and "Country" in df.columns:
        mask &= df["Country"].astype("string").fillna("Unknown").isin(selected_countries)
    if selected_prodcats and "ProdCat" in df.columns:
        mask &= df["ProdCat"].astype("string").fillna("Unknown").isin(selected_prodcats)
    if selected_salesorg and "SalesOrg" in df.columns:
        mask &= df["SalesOrg"].astype("string").fillna("Unknown").isin(selected_salesorg)
    if selected_catdescr and "CatDescr" in df.columns:
        mask &= df["CatDescr"].astype("string").fillna("Unknown").isin(selected_catdescr)

    view = df.loc[mask].copy()

    # Build a non-date mask (dimension + search filters only).
    mask_non_date = pd.Series(True, index=df.index)
    if search.strip():
        q = search.strip().lower()
        search_cols = [c for c in ["CustDescr", "Customer", "ProdDescr", "Product"] if c in df.columns]
        if search_cols:
            hay = df[search_cols].astype("string").fillna("")
            m = False
            for c in search_cols:
                m = m | hay[c].str.lower().str.contains(q, na=False)
            mask_non_date &= m

    if selected_countries and "Country" in df.columns:
        mask_non_date &= df["Country"].astype("string").fillna("Unknown").isin(selected_countries)
    if selected_prodcats and "ProdCat" in df.columns:
        mask_non_date &= df["ProdCat"].astype("string").fillna("Unknown").isin(selected_prodcats)
    if selected_salesorg and "SalesOrg" in df.columns:
        mask_non_date &= df["SalesOrg"].astype("string").fillna("Unknown").isin(selected_salesorg)
    if selected_catdescr and "CatDescr" in df.columns:
        mask_non_date &= df["CatDescr"].astype("string").fillna("Unknown").isin(selected_catdescr)

    base_df = df.loc[mask_non_date].copy()

    # Month-over-month KPI growth (this month vs last month)
    rev_mom, mom_month = compute_mom_growth_pct(base_df, "Revenue USD")
    prof_mom, _ = compute_mom_growth_pct(base_df, "Profit")
    # Margin is a rate, compute MoM on avg margin for month slices
    if mom_month is not None:
        this_m = mom_month
        prev_m = mom_month - 1
        this_avg_m = float(base_df.loc[base_df["Date"].dt.to_period("M") == this_m, "Profit Margin"].mean())
        prev_avg_m = float(base_df.loc[base_df["Date"].dt.to_period("M") == prev_m, "Profit Margin"].mean())
        margin_mom = None if (pd.isna(prev_avg_m) or prev_avg_m == 0) else (this_avg_m - prev_avg_m) / prev_avg_m
        orders_this = int(base_df.loc[base_df["Date"].dt.to_period("M") == this_m].shape[0])
        orders_prev = int(base_df.loc[base_df["Date"].dt.to_period("M") == prev_m].shape[0])
        orders_mom = None if orders_prev == 0 else (orders_this - orders_prev) / orders_prev
    else:
        margin_mom = None
        orders_mom = None

    # Product segmentation by Profit Margin (prepared aggregation data)
    product_level, margin_segments = classify_products_by_margin(base_df)

    # Financial KPI row (4 cards, tight)
    fin_monthly = monthly_fin_kpis(view).tail(12)
    if fin_monthly.empty:
        k1, k2, k3, k4 = st.columns([1, 1, 1, 1], gap="small")
        with k1:
            render_fin_kpi_card(icon="％", title="Gross Margin", value="—", arrow="—", arrow_cls="", spark_values=[])
        with k2:
            render_fin_kpi_card(icon="🏷️", title="Discount Rate", value="—", arrow="—", arrow_cls="", spark_values=[])
        with k3:
            render_fin_kpi_card(icon="💳", title="Average Order Value", value="—", arrow="—", arrow_cls="", spark_values=[])
        with k4:
            render_fin_kpi_card(icon="💹", title="Profit / Unit", value="—", arrow="—", arrow_cls="", spark_values=[])
    else:
        # Current (latest month) KPI values and arrows vs previous month
        this_row = fin_monthly.iloc[-1]
        prev_row = fin_monthly.iloc[-2] if len(fin_monthly) >= 2 else None

        gm = float(this_row["gross_margin_pct"])
        dr = float(this_row["discount_rate_pct"])
        aov = float(this_row["aov_usd"])
        ppu = float(this_row["profit_per_unit_usd"])

        gm_arrow, gm_cls = _trend_dir(gm, float(prev_row["gross_margin_pct"])) if prev_row is not None else ("—", "")
        dr_arrow, dr_cls = _trend_dir(dr, float(prev_row["discount_rate_pct"])) if prev_row is not None else ("—", "")
        aov_arrow, aov_cls = _trend_dir(aov, float(prev_row["aov_usd"])) if prev_row is not None else ("—", "")
        ppu_arrow, ppu_cls = _trend_dir(ppu, float(prev_row["profit_per_unit_usd"])) if prev_row is not None else ("—", "")

        k1, k2, k3, k4 = st.columns([1, 1, 1, 1], gap="small")
        with k1:
            render_fin_kpi_card(
                icon="％",
                title="Gross Margin",
                value=_fmt_pct(gm),
                arrow=gm_arrow,
                arrow_cls=gm_cls,
                spark_values=fin_monthly["gross_margin_pct"].fillna(0).tolist(),
            )
        with k2:
            render_fin_kpi_card(
                icon="🏷️",
                title="Discount Rate",
                value=_fmt_pct(dr),
                arrow=dr_arrow,
                arrow_cls=dr_cls,
                spark_values=fin_monthly["discount_rate_pct"].fillna(0).tolist(),
            )
        with k3:
            render_fin_kpi_card(
                icon="💳",
                title="Average Order Value",
                value=_fmt_money_short(aov),
                arrow=aov_arrow,
                arrow_cls=aov_cls,
                spark_values=fin_monthly["aov_usd"].fillna(0).tolist(),
            )
        with k4:
            render_fin_kpi_card(
                icon="💹",
                title="Profit / Unit",
                value=_fmt_money_short(ppu),
                arrow=ppu_arrow,
                arrow_cls=ppu_cls,
                spark_values=fin_monthly["profit_per_unit_usd"].fillna(0).tolist(),
            )

    st.markdown("<div style='height: 14px'></div>", unsafe_allow_html=True)

    view["Month"] = view["Date"].dt.to_period("M").dt.to_timestamp()
    monthly = (
        view.groupby("Month", as_index=False)[["Revenue USD", "Profit"]]
        .sum()
        .sort_values("Month", ascending=True)
    )

    # Bento row 2 (2/3 + 1/3): main trend + share donut
    left, right = st.columns([2, 1], gap="small")
    with left:
        with st.spinner("Loading…"):
            render_chart_card(
                key="card_trend",
                title="Trend",
                subtitle="Revenue (bar) + Profit (spline)",
                fig=fig_time_trend(monthly),
            )
    with right:
        with st.spinner("Loading…"):
            # Share dimension (driven by icon buttons under the donut)
            if "share_dim" not in st.session_state:
                st.session_state["share_dim"] = "CustDescr" if "CustDescr" in view.columns else "SalesOrg"
            dim = str(st.session_state.get("share_dim") or "SalesOrg")
            if dim not in view.columns:
                # graceful fallback based on availability
                dim = "CustDescr" if "CustDescr" in view.columns else ("SalesOrg" if "SalesOrg" in view.columns else ("Country" if "Country" in view.columns else dim))
                st.session_state["share_dim"] = dim

            render_chart_card(
                key="card_share",
                title="Share",
                subtitle=f"Revenue share by {dim}",
                fig=fig_share_donut(view, dim=dim),
            )

    st.markdown("<div style='height: 14px'></div>", unsafe_allow_html=True)

    # Bento row 3: two side-by-side category analysis cards
    bleft, bright = st.columns([1, 1], gap="small")
    with bleft:
        with st.spinner("Loading…"):
            render_categories_target_list(key="card_mix", df=view, margin_segments=margin_segments)
    with bright:
        with st.spinner("Loading…"):
            render_customers_map_card(key="card_topcust", df=view)

    # Website-like signature footer
    st.markdown(
        "<div class='patrick-footer'>© Patrick.W — Dashboard design & build</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()

