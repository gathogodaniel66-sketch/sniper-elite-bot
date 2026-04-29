import streamlit as st
import pandas as pd
import asyncio
import time
import requests
from deriv_api import DerivAPI

# --- UI STYLING ---
st.set_page_config(page_title="Slimmy Pulse V10.1", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #041a12; }
    .bank-header { background: linear-gradient(135deg, #0a3d2e 0%, #155e46 100%); padding: 15px; border-radius: 0 0 20px 20px; text-align: center; border-bottom: 2px solid #8cc63f; }
    .icon-circle { background: #ffffff; width: 45px; height: 45px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-bottom: 5px; font-size: 20px; }
    div[data-testid="stMetric"] { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(140, 198, 63, 0.2); border-radius: 12px; padding: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- TELEGRAM ---
def notify_slimmy(msg, bot_token, chat_id):
    if bot_token and chat_id:
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            requests.post(url, data={"chat_id": chat_id, "text": msg})
        except: pass

# --- STATE ---
if "trades" not in st.session_state: st.session_state.trades = []
if "running" not in st.session_state: st.session_state.running = False
if "wins" not in st.session_state: st.session_state.wins = 0
if "losses" not in st.session_state: st.session_state.losses = 0

# --- SIDEBAR ---
st.sidebar.title("📲 Telegram Alerts")
tele_token = st.sidebar.text_input("Bot Token", type="password")
tele_id = st.sidebar.text_input("Chat ID")
st.sidebar.markdown("---")
st.sidebar.title("🏦 Wallet")
deriv_token = st.sidebar.text_input("Deriv Token", type="password")
stake = st.sidebar.number_input("Stake ($)", value=2.0)
live_trade = st.sidebar.toggle("🟢 ACTIVATE HIGH-FREQ")

if st.sidebar.button("🚀 START PULSE LOOP", use_container_width=True): st.session_state.running = True
if st.sidebar.button("🛑 STOP", use_container_width=True): st.session_state.running = False

# --- HEADER ---
st.markdown("<div class='bank-header'><h2 style='color:white; margin:0;'>SLIMMY PULSE V10.1</h2><p style='color:#8cc63f; margin:0;'>HIGH-FREQUENCY AUTO-TRADER</p></div>", unsafe_allow_html=True)

total_pl = sum([t['Profit'] for t in st.session_state.trades])
c1, c2, c3 = st.columns(3)
c1.metric("PROFIT", f"${total_pl:.2f}")
c2.metric("WINS", st.session_state.wins)
c3.metric("LOSSES", st.session_state.losses)

status_area = st.empty()
chart_area = st.empty()

async def pulse_worker():
    api = DerivAPI(app_id=36544)
    try:
        await api.authorize(deriv_token)
        notify_slimmy("🔥 High-Frequency Pulse is active. Striking every minute if trend holds.", tele_token, tele_id)
        
        while st.session_state.running:
            ticks = await api.ticks_history({"ticks_history": "1HZ100V", "count": 20, "end": "latest"})
            prices = [float(p) for p in ticks["history"]["prices"]]
            last_p, sma = prices[-1], sum(prices[-10:]) / 10
            momentum = prices[-1] - prices[-5] # Quicker lookback for faster trades
            
            chart_area.line_chart(prices)
            
            # FASTER LOGIC: Strike if trend is even slightly confirmed
            if (last_p > sma and momentum > 0.5) or (last_p < sma and momentum < -0.5):
                trade_type = "CALL" if last_p > sma else "PUT"
                entry_p = last_p
                
                if live_trade:
                    await api.buy({"buy": 1, "price": stake, "parameters": {"amount": stake, "basis": "stake", "contract_type": trade_type, "currency": "USD", "duration": 5, "duration_unit": "t", "symbol": "1HZ100V"}})
                
                status_area.success(f"⚡ Pulse Strike: {trade_type}")
                await asyncio.sleep(7) # Trade duration
                
                res = await api.ticks_history({"ticks_history": "1HZ100V", "count": 1, "end": "latest"})
                exit_p = float(res["history"]["prices"][0])
                won = (trade_type == "CALL" and exit_p > entry_p) or (trade_type == "PUT" and exit_p < entry_p)
                
                if won:
                    st.session_state.wins += 1
                    p_val = stake * 0.95
                    notify_slimmy(f"✅ WIN! +${p_val:.2f}", tele_token, tele_id)
                else:
                    st.session_state.losses += 1
                    p_val = -stake
                    notify_slimmy(f"❌ LOSS. -${stake}", tele_token, tele_id)
                
                st.session_state.trades.append({"Profit": p_val})
                await asyncio.sleep(2) # Minimal pause to catch the next minute cycle
            
            await asyncio.sleep(1)
    except Exception as e:
        st.error(f"Error: {e}")
        st.session_state.running = False

if st.session_state.running:
    asyncio.run(pulse_worker())
