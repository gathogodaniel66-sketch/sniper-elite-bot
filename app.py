import streamlit as st
import pandas as pd
import asyncio
import time
from deriv_api import DerivAPI

# --- 1. COMPACT VERTICAL STYLING ---
# Changed to centered for a slim, mobile-friendly look
st.set_page_config(page_title="Slimmy Sniper Pro", layout="centered") 

st.markdown("""
    <style>
    /* Dark Banking Background */
    .main { background-color: #041a12; }
    
    /* Slim Curved Header */
    .bank-header {
        background: linear-gradient(135deg, #0a3d2e 0%, #155e46 100%);
        padding: 15px; border-radius: 0 0 20px 20px;
        text-align: center; border-bottom: 2px solid #8cc63f;
        margin-bottom: 10px;
    }

    /* Tighten Vertical Spacing */
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
    
    /* Compact Metric Cards (Vertical Stack) */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(140, 198, 63, 0.2);
        border-radius: 12px;
        padding: 10px;
        margin-bottom: -10px; /* Reduces space between metrics */
    }
    div[data-testid="stMetricValue"] { color: #8cc63f !important; font-size: 24px !important; }
    div[data-testid="stMetricLabel"] { font-size: 14px !important; color: #ffffff !important; }
    
    /* Hide Streamlit Footer/Menu for cleaner look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. STATE MANAGEMENT ---
if "trades" not in st.session_state: st.session_state.trades = []
if "running" not in st.session_state: st.session_state.running = False
if "wins" not in st.session_state: st.session_state.wins = 0
if "losses" not in st.session_state: st.session_state.losses = 0

# --- 3. MOBILE HEADER ---
st.markdown("<div class='bank-header'><h2 style='color:white; margin:0;'>SLIMMY PRO</h2><p style='color:#8cc63f; margin:0; font-size:12px;'>V16 VERTICAL DASHBOARD</p></div>", unsafe_allow_html=True)

# Math
total_pl = sum([t['Profit'] for t in st.session_state.trades])
total_t = st.session_state.wins + st.session_state.losses
win_rate = (st.session_state.wins / total_t * 100) if total_t > 0 else 0

# --- 4. VERTICAL METRIC STACK (No Columns) ---
st.metric("💰 NET PROFIT", f"${total_pl:.2f}")
st.metric("🎯 ACCURACY", f"{win_rate:.1f}%")
st.metric("✅ TOTAL WINS", st.session_state.wins)
st.metric("❌ TOTAL LOSSES", st.session_state.losses)

# --- 5. MONITORING AREA ---
st.markdown("---")
status_area = st.empty()
chart_area = st.empty()

# --- 6. CONTROL CONSOLE (Sidebar) ---
st.sidebar.title("🏦 Wallet Console")
token = st.sidebar.text_input("Deriv Token", type="password")
stake = st.sidebar.number_input("Stake Amount", value=2.0)
live_trade = st.sidebar.toggle("🟢 Activate Live Logic")

if st.sidebar.button("🚀 DEPLOY SYSTEM", use_container_width=True): st.session_state.running = True
if st.sidebar.button("🛑 KILL SYSTEM", use_container_width=True): st.session_state.running = False

# --- 7. BACKGROUND WORKER ---
async def worker():
    api = DerivAPI(app_id=36544)
    try:
        await api.authorize(token)
        while st.session_state.running:
            ticks = await api.ticks_history({"ticks_history": "1HZ100V", "count": 25, "end": "latest"})
            prices = [float(p) for p in ticks["history"]["prices"]]
            
            # Chart and Status stay vertical
            chart_area.line_chart(prices)
            status_area.markdown(f"<div style='text-align:center; color:#8cc63f;'>📡 SCANNING... Price: {prices[-1]}</div>", unsafe_allow_html=True)
            
            await asyncio.sleep(2)
    except Exception as e:
        st.error(f"Error: {e}")

if st.session_state.running:
    asyncio.run(worker())
