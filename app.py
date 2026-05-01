import streamlit as st
import pandas as pd
import asyncio
import time
import requests
import json
import os
from deriv_api import DerivAPI

# --- 1. UI STYLING ---
st.set_page_config(page_title="KihatoGathogo Pro V21.0", layout="wide") 
st.markdown("""
    <style>
    .main { background-color: #041a12; }
    .bank-header {
        background: linear-gradient(135deg, #072b1d 0%, #155e46 100%);
        padding: 25px; border-radius: 20px;
        text-align: center; border-bottom: 3px solid #8cc63f;
        margin-bottom: 20px;
    }
    div[data-testid="stMetric"] {
        background: rgba(140, 198, 63, 0.1);
        border: 1px solid #8cc63f;
        border-radius: 15px; padding: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. STATE INITIALIZATION ---
DB_FILE = "slimmy_vault_v18.json"

if "trades" not in st.session_state: st.session_state.trades = []
if "running" not in st.session_state: st.session_state.running = False
if "wins" not in st.session_state: st.session_state.wins = 0
if "losses" not in st.session_state: st.session_state.losses = 0
if "live_bal" not in st.session_state: st.session_state.live_bal = 36.0 # Set to your current balance
if "user_session" not in st.session_state: st.session_state.user_session = None

# --- 3. HEADER & METRICS ---
st.markdown("<div class='bank-header'><h2 style='color:white; margin:0;'>SLIMMY PRO V21.0</h2><p style='color:#8cc63f; margin:0;'>GLOBAL PRECISION ARCHITECTURE</p></div>", unsafe_allow_html=True)

total_pl = round(sum([t['Profit'] for t in st.session_state.trades]), 2)
total_t = st.session_state.wins + st.session_state.losses
win_rate = (st.session_state.wins / total_t * 100) if total_t > 0 else 0

m1, m2, m3 = st.columns(3)
with m1: st.metric("💳 BALANCE", f"${st.session_state.live_bal:,.2f}")
with m2: st.metric("💰 SESSION P/L", f"${total_pl:.2f}")
with m3: st.metric("🎯 WIN RATE", f"{win_rate:.0f}%")

# --- 4. SIDEBAR CONTROLS ---
st.sidebar.title("🎮 Sniper Control")
# Use 1.0 stake for your $36 balance (Safe 2.7% risk)
base_stake = st.sidebar.number_input("Stake Amount ($)", value=1.0, min_value=0.35)
max_loss = st.sidebar.number_input("Hard Stop Loss ($)", value=10.0)
live_trade = st.sidebar.toggle("🟢 LIVE TRADING ACTIVE")

# Ensure you paste your token in the Login/Register section first!
if st.sidebar.button("🚀 DEPLOY SNIPER", use_container_width=True):
    st.session_state.running = True

if st.sidebar.button("🛑 KILL SWITCH", use_container_width=True):
    st.session_state.running = False

# --- 5. THE ENGINE ---
async def worker():
    # Use the session token
    token = st.session_state.user_session["deriv"] if st.session_state.user_session else None
    if not token:
        st.error("No API Token found. Please Login.")
        return

    api = DerivAPI(app_id=1089) # Changed to standard DTrader ID
    status_area = st.empty()
    chart_area = st.empty()
    
    try:
        await api.authorize(token)
        status_area.success("🟢 SOVEREIGN ENGINE ACTIVE")
        
        while st.session_state.running:
            # 1. Fetch High-Res Data
            ticks = await api.ticks_history({"ticks_history": "1HZ100V", "count": 100, "end": "latest"})
            prices = [float(p) for p in ticks["history"]["prices"]]
            chart_area.line_chart(prices[-50:])

            # 2. Precision Scoring Logic
            ma200 = sum(prices[-100:]) / 100
            ma50 = sum(prices[-50:]) / 50
            
            # RSI Calculation
            deltas = pd.Series(prices).diff()
            gain = deltas.where(deltas > 0, 0).rolling(14).mean().iloc[-1]
            loss = (-deltas.where(deltas < 0, 0)).rolling(14).mean().iloc[-1]
            rsi = 100 - (100 / (1 + (gain/loss))) if loss != 0 else 50

            # Scoring System
            score = 0
            is_bull = prices[-1] > ma50 > ma200
            is_bear = prices[-1] < ma50 < ma200
            
            if is_bull or is_bear: score += 4
            if (is_bull and 55 <= rsi <= 70) or (is_bear and 30 <= rsi <= 45): score += 3
            if (prices[-1] > prices[-2]) == is_bull: score += 3 # Momentum match

            if score >= 9:
                direction = "CALL" if is_bull else "PUT"
                status_area.warning(f"💎 ELITE SIGNAL: {direction} (Score {score}/10)")
                
                if live_trade:
                    # Execution
                    buy = await api.buy({"buy": 1, "price": base_stake, "parameters": {
                        "amount": base_stake, "basis": "stake", "contract_type": direction,
                        "currency": "USD", "duration": 5, "duration_unit": "t", "symbol": "1HZ100V"
                    }})
                    
                    # Result Tracking
                    await asyncio.sleep(10)
                    history = await api.profit_table({"profit_table": 1, "limit": 1})
                    res = history['profit_table']['transactions'][0]
                    p_val = round(float(res['sell_price']) - float(res['buy_price']), 2)
                    
                    if p_val > 0: st.session_state.wins += 1
                    else: st.session_state.losses += 1
                    
                    # Update State
                    bal_upd = await api.balance()
                    st.session_state.live_bal = bal_upd['balance']['balance']
                    st.session_state.trades.append({"Time": time.strftime("%H:%M:%S"), "Type": direction, "Profit": p_val})
                    
                    st.rerun() # Refresh metrics
                    await asyncio.sleep(60) # Cooldown
            
            await asyncio.sleep(1) # Scan frequency

    except Exception as e:
        st.error(f"Engine Alert: {e}")

# --- 6. EXECUTION ---
if st.session_state.running:
    asyncio.run(worker())
