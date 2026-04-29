import streamlit as st
import pandas as pd
import asyncio
import time
import requests
from deriv_api import DerivAPI

# --- UI STYLING ---
st.set_page_config(page_title="Slimmy Minute-Must V11", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #041a12; }
    .bank-header { background: linear-gradient(135deg, #0a3d2e 0%, #155e46 100%); padding: 15px; border-radius: 0 0 20px 20px; text-align: center; border-bottom: 3px solid #8cc63f; }
    div[data-testid="stMetric"] { background: rgba(255, 255, 255, 0.05); border: 1px solid #8cc63f; border-radius: 12px; }
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
st.sidebar.title("🏦 Wallet")
deriv_token = st.sidebar.text_input("Deriv Token", type="password")
stake = st.sidebar.number_input("Stake ($)", value=2.0)
live_trade = st.sidebar.toggle("🟢 ACTIVATE FORCED MINUTE TRADING")

if st.sidebar.button("🚀 START MINUTE-MUST LOOP", use_container_width=True): st.session_state.running = True
if st.sidebar.button("🛑 STOP", use_container_width=True): st.session_state.running = False

# --- HEADER ---
st.markdown("<div class='bank-header'><h2 style='color:white; margin:0;'>SLIMMY MINUTE-MUST V11</h2><p style='color:#8cc63f; margin:0;'>STRICT 60-SECOND CYCLE ENABLED</p></div>", unsafe_allow_html=True)

total_pl = sum([t['Profit'] for t in st.session_state.trades])
c1, c2, c3 = st.columns(3)
c1.metric("PROFIT", f"${total_pl:.2f}")
c2.metric("WINS", st.session_state.wins)
c3.metric("LOSSES", st.session_state.losses)

status_area = st.empty()
chart_area = st.empty()

async def minute_must_worker():
    api = DerivAPI(app_id=36544)
    try:
        await api.authorize(deriv_token)
        notify_slimmy("🚀 Minute-Must Cycle Started. One trade every 60 seconds. Let's get it.", tele_token, tele_id)
        
        while st.session_state.running:
            start_time = time.time()
            
            # 1. Analyze for the first 5 seconds of the minute
            status_area.info("🧐 Analyzing Micro-Trend for this minute...")
            ticks = await api.ticks_history({"ticks_history": "1HZ100V", "count": 15, "end": "latest"})
            prices = [float(p) for p in ticks["history"]["prices"]]
            
            # Simple Directional Logic: Is it generally up or down?
            direction = "CALL" if prices[-1] > prices[0] else "PUT"
            entry_p = prices[-1]
            
            # 2. EXECUTE IMMEDIATELY (FORCED)
            if live_trade:
                await api.buy({"buy": 1, "price": stake, "parameters": {"amount": stake, "basis": "stake", "contract_type": direction, "currency": "USD", "duration": 5, "duration_unit": "t", "symbol": "1HZ100V"}})
            
            status_area.warning(f"⚡ FORCED {direction} EXECUTED. Waiting for result...")
            await asyncio.sleep(7) # Duration of trade
            
            # 3. VERIFY
            res = await api.ticks_history({"ticks_history": "1HZ100V", "count": 1, "end": "latest"})
            exit_p = float(res["history"]["prices"][0])
            won = (direction == "CALL" and exit_p > entry_p) or (direction == "PUT" and exit_p < entry_p)
            
            if won:
                st.session_state.wins += 1
                p_val = stake * 0.95
                notify_slimmy(f"✅ MINUTE WIN! +${p_val:.2f}", tele_token, tele_id)
            else:
                st.session_state.losses += 1
                p_val = -stake
                notify_slimmy(f"❌ MINUTE LOSS. -${stake}", tele_token, tele_id)
            
            st.session_state.trades.append({"Profit": p_val})
            
            # 4. WAIT UNTIL THE FULL MINUTE IS UP
            elapsed = time.time() - start_time
            wait_time = max(0, 60 - elapsed)
            status_area.success(f"⌛ Trade Complete. Next cycle in {int(wait_time)}s")
            await asyncio.sleep(wait_time) 

    except Exception as e:
        st.error(f"Error: {e}")
        st.session_state.running = False

if st.session_state.running:
    asyncio.run(minute_must_worker())
