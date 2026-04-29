import streamlit as st
import pandas as pd
import asyncio
import time
import requests
from deriv_api import DerivAPI

# --- 1. EXACT FINTECH UI STYLING ---
st.set_page_config(page_title="Slimmy Sniper Pro", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; } 
    .bank-header {
        background: linear-gradient(135deg, #041a12 0%, #155e46 100%);
        padding: 30px 20px 50px 20px;
        border-radius: 0 0 35px 35px;
        text-align: center;
        border-bottom: 3px solid #8cc63f;
    }
    .icon-container { display: flex; flex-direction: column; align-items: center; margin-bottom: 20px; }
    .icon-circle {
        background: #ffffff; width: 60px; height: 60px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08); font-size: 24px; border: 1px solid #eee;
    }
    .icon-label { color: #444; font-size: 11px; font-weight: 600; margin-top: 6px; text-align: center; }
    .status-card {
        background: #112b21; color: #8cc63f; border-radius: 15px;
        padding: 15px; text-align: center; margin: 10px 20px; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIC STATE ---
if "trades" not in st.session_state: st.session_state.trades = []
if "running" not in st.session_state: st.session_state.running = False
if "wins" not in st.session_state: st.session_state.wins = 0
if "losses" not in st.session_state: st.session_state.losses = 0
if "streak_loss" not in st.session_state: st.session_state.streak_loss = 0

# --- 3. HEADER ---
st.markdown("<div class='bank-header'><p style='color:#8cc63f; margin:0;'>FINTECH ELITE V14</p><h2 style='color:white; margin:0;'>Hello, Slimmy 👋</h2></div>", unsafe_allow_html=True)

# Math
total_pl = sum([t['Profit'] for t in st.session_state.trades])
total_t = st.session_state.wins + st.session_state.losses
win_rate = (st.session_state.wins / total_t * 100) if total_t > 0 else 0

# --- 4. ICON GRID (Fintech Format) ---
c1, c2, c3, c4 = st.columns(4)
with c1: st.markdown(f"<div class='icon-container'><div class='icon-circle'>💰</div><div class='icon-label'>Profit<br>${total_pl:.2f}</div></div>", unsafe_allow_html=True)
with c2: st.markdown(f"<div class='icon-container'><div class='icon-circle'>❌</div><div class='icon-label'>Losses<br>{st.session_state.losses}</div></div>", unsafe_allow_html=True)
with c3: st.markdown(f"<div class='icon-container'><div class='icon-circle'>🎯</div><div class='icon-label'>Accuracy<br>{win_rate:.0f}%</div></div>", unsafe_allow_html=True)
with c4: st.markdown(f"<div class='icon-container'><div class='icon-circle'>🔥</div><div class='icon-label'>Streak Loss<br>{st.session_state.streak_loss}</div></div>", unsafe_allow_html=True)

c5, c6, c7, c8 = st.columns(4)
with c5: st.markdown("<div class='icon-container'><div class='icon-circle'>⚙️</div><div class='icon-label'>Settings</div></div>", unsafe_allow_html=True)
with c6: st.markdown("<div class='icon-container'><div class='icon-circle'>📋</div><div class='icon-label'>Summary</div></div>", unsafe_allow_html=True)
with c7: st.markdown("<div class='icon-container'><div class='icon-circle'>📄</div><div class='icon-label'>Reports</div></div>", unsafe_allow_html=True)
with c8: st.markdown("<div class='icon-container'><div class='icon-circle'>📰</div><div class='icon-label'>News</div></div>", unsafe_allow_html=True)

# --- 5. CONTROL PANEL ---
st.sidebar.title("🏦 Account Console")
token = st.sidebar.text_input("Deriv Token", type="password")
stake = st.sidebar.number_input("Stake Amount", value=2.0)
live_trade = st.sidebar.toggle("🟢 Activate Selective Logic")

if st.sidebar.button("🚀 DEPLOY SYSTEM", use_container_width=True): st.session_state.running = True
if st.sidebar.button("🛑 KILL SYSTEM", use_container_width=True): st.session_state.running = False

# --- 6. EXECUTION AREA ---
status_area = st.empty()
chart_area = st.empty()

async def worker():
    api = DerivAPI(app_id=36544)
    try:
        await api.authorize(token)
        while st.session_state.running:
            # A. LOSS PROTECTION
            if st.session_state.streak_loss >= 3:
                status_area.markdown("<div class='status-card' style='color:#ff4b4b;'>🛑 STREAK PROTECTION ACTIVE (5m Pause)</div>", unsafe_allow_html=True)
                await asyncio.sleep(300)
                st.session_state.streak_loss = 0
                continue

            # B. DATA ANALYSIS
            ticks = await api.ticks_history({"ticks_history": "1HZ100V", "count": 50, "end": "latest"})
            prices = [float(p) for p in ticks["history"]["prices"]]
            ma_short = sum(prices[-10:]) / 10
            ma_long = sum(prices[-30:]) / 30
            momentum = prices[-1] - prices[-5]
            volatility = max(prices[-10:]) - min(prices[-10:])
            
            chart_area.line_chart(prices)

            # C. SELECTIVE FILTERS (Your Requirements)
            trend_up = (prices[-1] > ma_short > ma_long) and (momentum > 0.3)
            trend_down = (prices[-1] < ma_short < ma_long) and (momentum < -0.3)
            high_vol = volatility > 0.2

            if (trend_up or trend_down) and high_vol:
                trade_type = "CALL" if trend_up else "PUT"
                status_area.markdown(f"<div class='status-card' style='color:#ffc107;'>⏳ SIGNAL DETECTED: 2s Delaying...</div>", unsafe_allow_html=True)
                
                await asyncio.sleep(2) # ENTRY DELAY
                
                if live_trade:
                    await api.buy({"buy": 1, "price": stake, "parameters": {"amount": stake, "basis": "stake", "contract_type": trade_type, "currency": "USD", "duration": 5, "duration_unit": "t", "symbol": "1HZ100V"}})
                
                entry_p = prices[-1]
                await asyncio.sleep(7)
                
                res = await api.ticks_history({"ticks_history": "1HZ100V", "count": 1, "end": "latest"})
                exit_p = float(res["history"]["prices"][0])
                won = (trade_type == "CALL" and exit_p > entry_p) or (trade_type == "PUT" and exit_p < entry_p)
                
                if won:
                    st.session_state.wins += 1
                    st.session_state.streak_loss = 0
                    p_val = stake * 0.95
                    status_area.markdown("<div class='status-card'>✅ HIGH-PROBABILITY WIN</div>", unsafe_allow_html=True)
                else:
                    st.session_state.losses += 1
                    st.session_state.streak_loss += 1
                    p_val = -stake
                    status_area.markdown("<div class='status-card' style='color:#ff4b4b;'>❌ TRADE FAILED</div>", unsafe_allow_html=True)
                
                st.session_state.trades.append({"Profit": p_val})
            else:
                status_area.markdown("<div class='status-card' style='color:#58a6ff;'>📡 SCANNING: No High-Probability setup.</div>", unsafe_allow_html=True)

            await asyncio.sleep(60) # STRICT MINUTE CYCLE CHECK

    except Exception as e:
        st.error(f"Error: {e}")

if st.session_state.running:
    asyncio.run(worker())
