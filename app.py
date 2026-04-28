import streamlit as st
import pandas as pd
import asyncio
import time
from deriv_api import DerivAPI

# --- 1. PRO STYLING ---
st.set_page_config(page_title="Sniper Safe-Guard V5", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0b0e14; }
    div[data-testid="stMetricValue"] { font-size: 32px; font-weight: bold; }
    .stMetric { background-color: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIC MEMORY ---
if "trades" not in st.session_state: st.session_state.trades = []
if "running" not in st.session_state: st.session_state.running = False
if "wins" not in st.session_state: st.session_state.wins = 0
if "losses" not in st.session_state: st.session_state.losses = 0

# --- 3. SIDEBAR (The Safety Controls) ---
st.sidebar.title("🛡️ Safety Controls")
token = st.sidebar.text_input("Deriv Token", type="password")
stake = st.sidebar.number_input("Stake ($)", value=2.0) # Resetting to $2 for safety
target_profit = st.sidebar.number_input("Take Profit Target ($)", value=50.0)
max_loss_limit = st.sidebar.number_input("Max Loss Limit ($)", value=100.0)

if st.sidebar.button("🚀 START SAFE-MODE", use_container_width=True):
    st.session_state.running = True
if st.sidebar.button("🛑 STOP BOT", use_container_width=True):
    st.session_state.running = False

# --- 4. MAIN SCOREBOARD ---
st.title("🎯 SNIPER SAFE-GUARD V5")

total_pl = sum([t['Profit'] for t in st.session_state.trades])
col1, col2, col3, col4 = st.columns(4)

# Dynamic color for profit
p_color = "normal" if total_pl >= 0 else "inverse"

col1.metric("Current Session P/L", f"${total_pl:.2f}", delta=f"{total_pl:.2f}", delta_color=p_color)
col2.metric("Wins ✅", st.session_state.wins)
col3.metric("Losses ❌", st.session_state.losses)
col4.metric("Daily Target", f"${target_profit}")

# --- 5. LIVE MONITORING ---
chart_area = st.empty()
status_area = st.empty()

async def run_safe_bot():
    api = DerivAPI(app_id=1089)
    try:
        await api.authorize(token)
        while st.session_state.running:
            # Check Safety Limits First
            if total_pl <= -max_loss_limit:
                st.error(f"❌ Max Loss of ${max_loss_limit} reached. Shutting down for safety.")
                st.session_state.running = False
                break
            
            if total_pl >= target_profit:
                st.balloons()
                st.success(f"🎯 Target of ${target_profit} reached! Great job.")
                st.session_state.running = False
                break

            ticks = await api.ticks_history({"ticks_history": "1HZ100V", "count": 50, "end": "latest"})
            prices = [float(p) for p in ticks["history"]["prices"]]
            last_p = prices[-1]
            sma = sum(prices[-20:]) / 20
            momentum = prices[-1] - prices[-8] # Looking back further for stability

            # UI Update
            chart_area.line_chart(prices)
            
            # --- ULTRA-STRICT LOGIC ---
            if last_p > sma and momentum > 1.2:
                status_area.success(f"🔥 STRONG BUY DETECTED (Momentum: {momentum:.2f})")
                # Execution would go here
            elif last_p < sma and momentum < -1.2:
                status_area.error(f"❄️ STRONG SELL DETECTED (Momentum: {momentum:.2f})")
                # Execution would go here
            else:
                status_area.info(f"📡 Waiting for High Momentum... (Current: {momentum:.2f})")

            await asyncio.sleep(1)
            
    except Exception as e:
        st.error(f"Connection Error: {e}")

if st.session_state.running:
    asyncio.run(run_safe_bot())
