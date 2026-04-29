import streamlit as st
import pandas as pd
import asyncio
import time
import requests
from deriv_api import DerivAPI

# --- 1. UI STYLING ---
st.set_page_config(page_title="Slimmy Pro V16.2", layout="centered") 
st.markdown("""
    <style>
    .main { background-color: #041a12; }
    .bank-header {
        background: linear-gradient(135deg, #0a3d2e 0%, #155e46 100%);
        padding: 20px; border-radius: 0 0 25px 25px;
        text-align: center; border-bottom: 2px solid #8cc63f;
        margin-bottom: 15px;
    }
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(140, 198, 63, 0.2);
        border-radius: 12px; padding: 12px; margin-bottom: -15px;
    }
    div[data-testid="stMetricValue"] { color: #8cc63f !important; font-size: 24px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. TELEGRAM FUNCTION ---
def send_tele(msg, token, cid):
    if token and cid:
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={cid}&text={msg}"
            requests.get(url)
        except: pass

# --- 3. STATE ---
if "trades" not in st.session_state: st.session_state.trades = []
if "running" not in st.session_state: st.session_state.running = False
if "wins" not in st.session_state: st.session_state.wins = 0
if "losses" not in st.session_state: st.session_state.losses = 0

# --- 4. HEADER ---
st.markdown("<div class='bank-header'><h2 style='color:white; margin:0;'>SLIMMY PRO</h2><p style='color:#8cc63f; margin:0; font-size:12px;'>V16.2 CONTROL CENTER</p></div>", unsafe_allow_html=True)

# Math
total_pl = sum([t['Profit'] for t in st.session_state.trades])
total_t = st.session_state.wins + st.session_state.losses
win_rate = (st.session_state.wins / total_t * 100) if total_t > 0 else 0

# --- 5. VERTICAL DASHBOARD ---
st.metric("💰 NET PROFIT", f"${total_pl:.2f}")
st.metric("🎯 ACCURACY", f"{win_rate:.0f}%")
st.metric("✅ WINS", st.session_state.wins)
st.metric("❌ LOSSES", st.session_state.losses)

st.markdown("---")
status_area = st.empty()
chart_area = st.empty()

# --- 6. SIDEBAR CONTROLS (Find these by tapping >>) ---
st.sidebar.title("📲 Telegram Alerts")
tele_token = st.sidebar.text_input("Bot Token", type="password")
tele_id = st.sidebar.text_input("Chat ID")

st.sidebar.markdown("---")
st.sidebar.title("🏦 Wallet & Risk")
deriv_token = st.sidebar.text_input("Deriv Token", type="password")
stake = st.sidebar.number_input("Stake Amount ($)", value=2.0)
max_loss = st.sidebar.number_input("Stop Loss Limit ($)", value=50.0)
live_trade = st.sidebar.toggle("🟢 ACTIVATE LIVE TRADING")

if st.sidebar.button("🚀 DEPLOY SYSTEM", use_container_width=True):
    if deriv_token: st.session_state.running = True
    else: st.sidebar.error("Enter Deriv Token!")

if st.sidebar.button("🛑 STOP SYSTEM", use_container_width=True):
    st.session_state.running = False

# --- 7. THE ENGINE ---
async def worker():
    api = DerivAPI(app_id=36544)
    try:
        await api.authorize(deriv_token)
        status_area.success("🟢 CONNECTED")
        send_tele("🚀 Slimmy, the V16.2 Engine is now LIVE.", tele_token, tele_id)
        
        while st.session_state.running:
            # Safety Check: Stop Loss
            if total_pl <= -max_loss:
                status_area.error(f"🛑 STOP LOSS HIT: ${max_loss}")
                send_tele(f"⚠️ STOP LOSS HIT: Your session lost ${max_loss}. System Halted.", tele_token, tele_id)
                st.session_state.running = False
                break

            ticks = await api.ticks_history({"ticks_history": "1HZ100V", "count": 30, "end": "latest"})
            prices = [float(p) for p in ticks["history"]["prices"]]
            chart_area.line_chart(prices)
            
            # Logic: Using the High-Probability V12 Setup
            ma_short = sum(prices[-10:])/10
            momentum = prices[-1] - prices[-5]
            
            if (prices[-1] > ma_short and momentum > 0.4) or (prices[-1] < ma_short and momentum < -0.4):
                trade_type = "CALL" if prices[-1] > ma_short else "PUT"
                status_area.warning(f"🎯 SIGNAL: {trade_type}. Delaying 2s...")
                await asyncio.sleep(2)
                
                if live_trade:
                    await api.buy({"buy": 1, "price": stake, "parameters": {"amount": stake, "basis": "stake", "contract_type": trade_type, "currency": "USD", "duration": 5, "duration_unit": "t", "symbol": "1HZ100V"}})
                
                entry_p = prices[-1]
                await asyncio.sleep(7)
                
                res = await api.ticks_history({"ticks_history": "1HZ100V", "count": 1, "end": "latest"})
                exit_p = float(res["history"]["prices"][0])
                won = (trade_type == "CALL" and exit_p > entry_p) or (trade_type == "PUT" and exit_p < entry_p)
                
                p_val = (stake * 0.95) if won else -stake
                if won: 
                    st.session_state.wins += 1
                    send_tele(f"✅ WIN! Profit: ${p_val:.2f}", tele_token, tele_id)
                else: 
                    st.session_state.losses += 1
                    send_tele(f"❌ LOSS! -${stake}", tele_token, tele_id)
                
                st.session_state.trades.append({"Profit": p_val})
                await asyncio.sleep(50)
            
            await asyncio.sleep(1)
    except Exception as e:
        st.error(f"Error: {e}")

if st.session_state.running:
    asyncio.run(worker())
