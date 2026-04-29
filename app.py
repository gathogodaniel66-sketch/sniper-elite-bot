import streamlit as st
import pandas as pd
import asyncio
import time
from deriv_api import DerivAPI

# --- 1. UI STYLING ---
st.set_page_config(page_title="Slimmy Bento V15.1", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .bank-header {
        background: linear-gradient(135deg, #041a12 0%, #155e46 100%);
        padding: 20px; border-radius: 0 0 30px 30px;
        text-align: center; border-bottom: 3px solid #8cc63f;
        margin-bottom: 20px;
    }
    /* Simple Box Styling */
    [data-testid="stVerticalBlock"] > div:has(div.stMarkdown) {
        background: white;
        border-radius: 15px;
        padding: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border: 1px solid #eee;
    }
    .icon-text { font-size: 24px; margin-bottom: 5px; text-align: center; }
    .label-text { font-size: 12px; font-weight: bold; color: #555; text-align: center; display: block; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. STATE ---
if "trades" not in st.session_state: st.session_state.trades = []
if "running" not in st.session_state: st.session_state.running = False
if "wins" not in st.session_state: st.session_state.wins = 0
if "losses" not in st.session_state: st.session_state.losses = 0

# --- 3. HEADER ---
st.markdown("<div class='bank-header'><h2 style='color:white; margin:0;'>SLIMMY BENTO V15.1</h2><p style='color:#8cc63f; margin:0;'>STABLE GRID INTERFACE</p></div>", unsafe_allow_html=True)

# Math
total_pl = sum([t['Profit'] for t in st.session_state.trades])
total_t = st.session_state.wins + st.session_state.losses
win_rate = (st.session_state.wins / total_t * 100) if total_t > 0 else 0

# --- 4. THE BENTO GRID (Using Native Columns) ---
# Column 1: The Tall Sidebar (Chart)
# Column 2-3: The Metrics
main_col1, main_col2 = st.columns([1, 2])

with main_col1:
    st.markdown("<div class='icon-text'>📈</div><span class='label-text'>LIVE MARKET</span>", unsafe_allow_html=True)
    chart_area = st.empty()
    st.markdown("<small style='color:gray;'>1HZ100V Index</small>", unsafe_allow_html=True)

with main_col2:
    # Row 1: Profit
    st.markdown(f"<div class='icon-text'>💰</div><span class='label-text'>NET PROFIT</span><h3 style='text-align:center; color:#2e7d32; margin:0;'>${total_pl:.2f}</h3>", unsafe_allow_html=True)
    
    # Row 2: Stats
    sub_col1, sub_col2 = st.columns(2)
    with sub_col1:
        st.markdown(f"<div class='icon-text'>🎯</div><span class='label-text'>ACCURACY</span><h4 style='text-align:center; margin:0;'>{win_rate:.0f}%</h4>", unsafe_allow_html=True)
    with sub_col2:
        st.markdown(f"<div class='icon-text'>❌</div><span class='label-text'>LOSSES</span><h4 style='text-align:center; color:#c62828; margin:0;'>{st.session_state.losses}</h4>", unsafe_allow_html=True)
    
    # Row 3: Wins & Settings
    sub_col3, sub_col4 = st.columns(2)
    with sub_col3:
        st.markdown(f"<div class='icon-text'>✅</div><span class='label-text'>WINS</span><h4 style='text-align:center; margin:0;'>{st.session_state.wins}</h4>", unsafe_allow_html=True)
    with sub_col4:
        st.markdown("<div class='icon-text'>⚙️</div><span class='label-text'>SETTINGS</span><p style='font-size:10px; text-align:center; margin:0;'>V12 Protocol Active</p>", unsafe_allow_html=True)

# --- 5. CONTROLS ---
st.sidebar.title("🏦 Wallet Console")
token = st.sidebar.text_input("Deriv Token", type="password")
live_trade = st.sidebar.toggle("Activate Live Trading")

if st.sidebar.button("🚀 DEPLOY SYSTEM", use_container_width=True): st.session_state.running = True
if st.sidebar.button("🛑 KILL SYSTEM", use_container_width=True): st.session_state.running = False

status_area = st.empty()

async def worker():
    api = DerivAPI(app_id=36544)
    try:
        await api.authorize(token)
        while st.session_state.running:
            ticks = await api.ticks_history({"ticks_history": "1HZ100V", "count": 25, "end": "latest"})
            prices = [float(p) for p in ticks["history"]["prices"]]
            chart_area.line_chart(prices)
            status_area.info(f"📡 Scanning... Price: {prices[-1]}")
            await asyncio.sleep(2)
    except Exception as e:
        st.error(f"Error: {e}")

if st.session_state.running:
    asyncio.run(worker())
