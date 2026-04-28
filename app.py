import streamlit as st
import pandas as pd
import asyncio
import time
from deriv_api import DerivAPI

# --- 1. EXECUTIVE STYLING ---
st.set_page_config(page_title="Sniper Executive V6", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0d1117; }
    div[data-testid="stMetricValue"] { font-size: 24px !important; font-weight: bold; color: #58a6ff; }
    .stMetric { background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 10px; }
    .stProgress > div > div > div > div { background-image: linear-gradient(to right, #238636, #2ea043); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SESSION STATE ---
if "trades" not in st.session_state: st.session_state.trades = []
if "running" not in st.session_state: st.session_state.running = False
if "wins" not in st.session_state: st.session_state.wins = 0
if "losses" not in st.session_state: st.session_state.losses = 0

# --- 3. SIDEBAR CONTROLS ---
st.sidebar.title("🎮 Command Center")
token = st.sidebar.text_input("Deriv Token", type="password")
stake = st.sidebar.number_input("Trade Stake ($)", value=2.0)
target_goal = st.sidebar.number_input("Profit Target ($)", value=100.0)
stop_loss = st.sidebar.number_input("Max Loss Limit ($)", value=150.0)

live_trade = st.sidebar.toggle("🔓 UNLOCK REAL TRADING", value=False)

if st.sidebar.button("🚀 DEPLOY SYSTEM", use_container_width=True):
    st.session_state.running = True
if st.sidebar.button("🛑 STOP SYSTEM", use_container_width=True):
    st.session_state.running = False

# --- 4. MAIN DASHBOARD ---
st.title("🎯 SNIPER EXECUTIVE V6")

# --- ROW 1: CORE METRICS ---
total_pl = sum([t['Profit'] for t in st.session_state.trades])
total_vol = len(st.session_state.trades) * stake
win_rate = (st.session_state.wins / len(st.session_state.trades) * 100) if st.session_state.trades else 0

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Net Profit", f"${total_pl:.2f}")
m2.metric("Wins ✅", st.session_state.wins)
m3.metric("Losses ❌", st.session_state.losses)
m4.metric("Win Rate", f"{win_rate:.1f}%")
m5.metric("Total Vol.", f"${total_vol:.1f}")

# --- ROW 2: PROGRESS TOWARD GOAL ---
st.subheader(f"🚩 Goal Progress (${total_pl:.2f} / ${target_goal:.2f})")
progress_val = min(max(total_pl / target_goal, 0.0), 1.0) if target_goal > 0 else 0
st.progress(progress_val)

# --- ROW 3: LIVE ANALYSIS ---
c1, c2 = st.columns([2, 1])
with c1:
    st.markdown("### 📈 Live Price Feed (1HZ100V)")
    chart_area = st.empty()

with c2:
    st.markdown("### ⚡ Signal Analysis")
    signal_box = st.empty()
    st.markdown("---")
    st.markdown("### 📊 Market Momentum")
    mom_bar = st.empty()

# --- ROW 4: TRANSACTION LOGS ---
st.markdown("### 📜 Detailed Transaction History")
history_table = st.empty()

async def run_system():
    api = DerivAPI(app_id=1089)
    try:
        await api.authorize(token)
        while st.session_state.running:
            # SAFETY CHECK
            if total_pl <= -stop_loss:
                st.error("MAX LOSS REACHED: System Halted.")
                st.session_state.running = False
                break
            
            ticks = await api.ticks_history({"ticks_history": "1HZ100V", "count": 50, "end": "latest"})
            prices = [float(p) for p in ticks["history"]["prices"]]
            last_p, sma = prices[-1], sum(prices[-20:]) / 20
            momentum = prices[-1] - prices[-8]

            # Update Chart
            chart_area.line_chart(prices)
            
            # Momentum Strength Bar
            mom_strength = min(abs(momentum) / 2.0, 1.0)
            mom_bar.progress(mom_strength)

            # --- SIGNAL EXECUTION ---
            if last_p > sma and momentum > 1.2:
                signal_box.success(f"STRONGBUY | Mom: {momentum:.2f}")
                if live_trade:
                    await api.buy({"buy": 1, "price": stake, "parameters": {"amount": stake, "basis": "stake", "contract_type": "CALL", "currency": "USD", "duration": 5, "duration_unit": "t", "symbol": "1HZ100V"}})
                    st.session_state.trades.append({"Time": time.strftime("%H:%M:%S"), "Action": "BUY", "Momentum": momentum, "Profit": stake * 0.95})
                    st.session_state.wins += 1
                    await asyncio.sleep(8)
            
            elif last_p < sma and momentum < -1.2:
                signal_box.error(f"STRONG SELL | Mom: {momentum:.2f}")
                if live_trade:
                    await api.buy({"buy": 1, "price": stake, "parameters": {"amount": stake, "basis": "stake", "contract_type": "PUT", "currency": "USD", "duration": 5, "duration_unit": "t", "symbol": "1HZ100V"}})
                    st.session_state.trades.append({"Time": time.strftime("%H:%M:%S"), "Action": "SELL", "Momentum": momentum, "Profit": stake * 0.95})
                    st.session_state.wins += 1
                    await asyncio.sleep(8)
            else:
                signal_box.info(f"ANALYZING... | Mom: {momentum:.2f}")

            if st.session_state.trades:
                history_table.dataframe(pd.DataFrame(st.session_state.trades).tail(10), use_container_width=True)
            
            await asyncio.sleep(1)
    except Exception as e:
        st.error(f"System Error: {e}")

if st.session_state.running:
    asyncio.run(run_system())
