import streamlit as st
import pandas as pd
import asyncio
import time
from deriv_api import DerivAPI

# --- 1. STYLING ---
st.set_page_config(page_title="Sniper Elite V3 - Live", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1f2937; border: 1px solid #3b82f6; border-radius: 15px; padding: 15px; }
    h1 { color: #3b82f6; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MEMORY ---
if "trades" not in st.session_state: st.session_state.trades = []
if "running" not in st.session_state: st.session_state.running = False
if "wins" not in st.session_state: st.session_state.wins = 0
if "losses" not in st.session_state: st.session_state.losses = 0

# --- 3. SIDEBAR ---
st.sidebar.title("🎮 Sniper Controller")
token = st.sidebar.text_input("Deriv Token", type="password")
stake = st.sidebar.number_input("Stake ($)", value=10.0)

# NEW: The switch that makes it trade for real
live_trade = st.sidebar.toggle("🟢 ENABLE REAL TRADING", value=False)

if st.sidebar.button("▶ LAUNCH BOT"):
    st.session_state.running = True
if st.sidebar.button("⛔ STOP"):
    st.session_state.running = False

# --- 4. DASHBOARD ---
st.title("🎯 SNIPER ELITE V3 - EXECUTION MODE")
m_col1, m_col2, m_col3, m_col4 = st.columns(4)
price_box = m_col1.empty()
signal_box = m_col2.empty()
profit_box = m_col3.empty()
winrate_box = m_col4.empty()
chart_area = st.empty()

async def run_sniper():
    api = DerivAPI(app_id=1089)
    await api.authorize(token)
    
    while st.session_state.running:
        ticks = await api.ticks_history({"ticks_history": "1HZ100V", "count": 50, "end": "latest"})
        prices = [float(p) for p in ticks["history"]["prices"]]
        last_p, sma = prices[-1], sum(prices[-15:]) / 15
        momentum = prices[-1] - prices[-5]
        
        sig, color = "⌛ SCANNING...", "#AAAAAA"
        
        # --- LOGIC & EXECUTION ---
        # 100% Confirmation: Price > Average AND Strong Momentum
        if last_p > sma and momentum > 0.5:
            sig, color = "🔥 BUY SIGNAL", "#00FF00"
            if live_trade:
                # THIS PART SENDS THE REAL TRADE TO DERIV
                try:
                    contract = await api.buy({"buy": 1, "subscribe": 1, "price": stake, 
                                            "parameters": {"amount": stake, "basis": "stake", 
                                            "contract_type": "CALL", "currency": "USD", 
                                            "duration": 5, "duration_unit": "t", "symbol": "1HZ100V"}})
                    st.session_state.trades.append({"Time": time.strftime("%H:%M:%S"), "Type": "BUY", "Result": "EXECUTED", "Profit": 0})
                except Exception as e:
                    st.error(f"Trade Error: {e}")

        elif last_p < sma and momentum < -0.5:
            sig, color = "❄️ SELL SIGNAL", "#FF4B4B"
            if live_trade:
                try:
                    await api.buy({"buy": 1, "subscribe": 1, "price": stake, 
                                   "parameters": {"amount": stake, "basis": "stake", 
                                   "contract_type": "PUT", "currency": "USD", 
                                   "duration": 5, "duration_unit": "t", "symbol": "1HZ100V"}})
                    st.session_state.trades.append({"Time": time.strftime("%H:%M:%S"), "Type": "SELL", "Result": "EXECUTED", "Profit": 0})
                except Exception as e:
                    st.error(f"Trade Error: {e}")

        # Update UI
        price_box.metric("Price", f"{last_p:.2f}")
        signal_box.markdown(f"<h3 style='color:{color}; text-align:center;'>{sig}</h3>", unsafe_allow_html=True)
        chart_area.line_chart(prices)
        await asyncio.sleep(1)

if st.session_state.running:
    asyncio.run(run_sniper())
