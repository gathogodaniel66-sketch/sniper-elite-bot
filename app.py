import streamlit as st
import pandas as pd
import asyncio
import time
from deriv_api import DerivAPI

# --- 1. BENTO BOX GRID STYLING ---
st.set_page_config(page_title="Slimmy Bento V15", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    
    /* The Banking Header */
    .bank-header {
        background: linear-gradient(135deg, #041a12 0%, #155e46 100%);
        padding: 25px; border-radius: 0 0 30px 30px;
        text-align: center; border-bottom: 3px solid #8cc63f;
        margin-bottom: 20px;
    }

    /* CSS Grid Container (The Bento Logic) */
    .bento-grid {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr 1fr;
        grid-template-rows: auto auto auto;
        gap: 15px;
        padding: 10px;
    }

    /* Common Card Style */
    .bento-card {
        background: white;
        border-radius: 15px;
        padding: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }

    /* Specific Spans (Matching your image) */
    .chart-box { grid-row: span 3; grid-column: span 1; background: #ffffff; border-left: 5px solid #8cc63f; }
    .wide-metric { grid-column: span 2; background: #e8f5e9; }
    .small-metric { grid-column: span 1; }

    /* Icons */
    .icon-circle {
        background: #f1f3f4; width: 50px; height: 50px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 24px; margin-bottom: 5px;
    }
    .label { font-size: 12px; font-weight: bold; color: #333; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. STATE ---
if "trades" not in st.session_state: st.session_state.trades = []
if "running" not in st.session_state: st.session_state.running = False
if "wins" not in st.session_state: st.session_state.wins = 0
if "losses" not in st.session_state: st.session_state.losses = 0

# --- 3. HEADER ---
st.markdown("<div class='bank-header'><h2 style='color:white; margin:0;'>SLIMMY BENTO V15</h2><p style='color:#8cc63f; margin:0;'>ELITE TRADING TERMINAL</p></div>", unsafe_allow_html=True)

# Math
total_pl = sum([t['Profit'] for t in st.session_state.trades])
win_rate = (st.session_state.wins / (st.session_state.wins + st.session_state.losses) * 100) if (st.session_state.wins + st.session_state.losses) > 0 else 0

# --- 4. THE BENTO MAPPING ---
# We use HTML to define the layout since Streamlit's native columns don't support uneven spans like your image
st.markdown(f"""
<div class="bento-grid">
    <div class="bento-card chart-box">
        <div class="label">LIVE MARKET FEED</div>
        <p style="font-size:10px; color:#666;">1HZ100V Index</p>
    </div>

    <div class="bento-card wide-metric">
        <div class="icon-circle">💰</div>
        <div class="label">TOTAL NET PROFIT</div>
        <h3 style="margin:0; color:#2e7d32;">${total_pl:.2f}</h3>
    </div>

    <div class="bento-card small-metric" style="background:#fff3e0;">
        <div class="icon-circle">🎯</div>
        <div class="label">ACCURACY</div>
        <h4 style="margin:0;">{win_rate:.1f}%</h4>
    </div>

    <div class="bento-card small-metric">
        <div class="icon-circle">✅</div>
        <div class="label">WINS</div>
        <h4 style="margin:0;">{st.session_state.wins}</h4>
    </div>
    <div class="bento-card small-metric" style="background:#ffebee;">
        <div class="icon-circle">❌</div>
        <div class="label">LOSSES</div>
        <h4 style="margin:0; color:#c62828;">{st.session_state.losses}</h4>
    </div>

    <div class="bento-card chart-box" style="grid-column: 4; grid-row: 2 / span 2;">
        <div class="icon-circle">⚙️</div>
        <div class="label">SETTINGS</div>
        <p style="font-size:10px; text-align:center;">Selective Logic Active<br>Stake: $2.00</p>
    </div>

    <div class="bento-card wide-metric" style="background:#e3f2fd;">
        <div class="icon-circle">📰</div>
        <div class="label">MARKET SUMMARY</div>
        <p style="font-size:11px; margin:0;">V12 Protocol Scanning...</p>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 5. CONTROL & LIVE CHART (Standard Streamlit under the Grid) ---
st.sidebar.title("🏦 Wallet Console")
token = st.sidebar.text_input("Deriv Token", type="password")
live_trade = st.sidebar.toggle("Activate Live Trading")

if st.sidebar.button("🚀 DEPLOY SYSTEM", use_container_width=True): st.session_state.running = True
if st.sidebar.button("🛑 KILL SYSTEM", use_container_width=True): st.session_state.running = False

# We place the real chart here so it updates live
chart_container = st.empty()
status_container = st.empty()

async def worker():
    api = DerivAPI(app_id=36544)
    try:
        await api.authorize(token)
        while st.session_state.running:
            ticks = await api.ticks_history({"ticks_history": "1HZ100V", "count": 30, "end": "latest"})
            prices = [float(p) for p in ticks["history"]["prices"]]
            
            # This injects the live chart into your dashboard area
            chart_container.line_chart(prices)
            status_container.markdown(f"<div class='bento-card' style='background:#fff;'>📡 Analyzing momentum: {prices[-1] - prices[-5]:.2f}</div>", unsafe_allow_html=True)
            
            await asyncio.sleep(2)
    except Exception as e:
        st.error(f"Error: {e}")

if st.session_state.running:
    asyncio.run(worker())
