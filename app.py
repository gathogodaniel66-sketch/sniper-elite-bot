
import streamlit as st
import pandas as pd
import asyncio
import time
import requests
import json
import os
from deriv_api import DerivAPI

# --- 1. UI STYLING (UNTOUCHED) ---
st.set_page_config(page_title="Slimmy Pro V19.5", layout="centered") 
st.markdown("""
    <style>
    .main { background-color: #041a12; }
    .bank-header {
        background: linear-gradient(135deg, #072b1d 0%, #155e46 100%);
        padding: 25px; border-radius: 0 0 30px 30px;
        text-align: center; border-bottom: 3px solid #8cc63f;
        margin-bottom: 20px;
    }
    div[data-testid="stMetric"] {
        background: rgba(140, 198, 63, 0.1);
        border: 1px solid #8cc63f;
        border-radius: 15px; padding: 15px;
    }
    .stDownloadButton button {
        width: 100%;
        background-color: #8cc63f !important;
        color: #041a12 !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. PERMANENT DATA & STATE (UNTOUCHED) ---
DB_FILE = "slimmy_vault_v18.json"
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}
def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f)

if "db" not in st.session_state:
    st.session_state.db = load_db()

if "trades" not in st.session_state: st.session_state.trades = []
if "running" not in st.session_state: st.session_state.running = False
if "wins" not in st.session_state: st.session_state.wins = 0
if "losses" not in st.session_state: st.session_state.losses = 0
if "live_bal" not in st.session_state: st.session_state.live_bal = 0.0
if "user_session" not in st.session_state: st.session_state.user_session = None

def send_tele(msg, token, cid):
    if token and cid:
        try: requests.get(f"https://api.telegram.org/bot{token}/sendMessage?chat_id={cid}&text={msg}")
        except: pass

# --- 3. HEADER (UNTOUCHED) ---
st.markdown("<div class='bank-header'><h2 style='color:white; margin:0;'>SLIMMY PRO V19.5</h2><p style='color:#8cc63f; margin:0;'>HIGH-PRECISION SCORING ACTIVE</p></div>", unsafe_allow_html=True)

total_pl = sum([t['Profit'] for t in st.session_state.trades])
total_t = st.session_state.wins + st.session_state.losses
win_rate = (st.session_state.wins / total_t * 100) if total_t > 0 else 0

c1, c2, c3 = st.columns(3)
with c1: st.metric("💳 BALANCE", f"${st.session_state.live_bal:,.2f}")
with c2: st.metric("💰 SESSION P/L", f"${total_pl:.2f}")
with c3: st.metric("🎯 WIN RATE", f"{win_rate:.0f}%")

st.markdown("---")

# --- 4. SIDEBAR & USER CENTER (UNTOUCHED) ---
st.sidebar.title("👥 User Center")
choice = st.sidebar.selectbox("Action", ["Login", "Register", "Recovery"])

if choice == "Register":
    r_email = st.sidebar.text_input("Email")
    r_pass = st.sidebar.text_input("Password", type="password")
    r_bot = st.sidebar.text_input("Bot Token")
    r_cid = st.sidebar.text_input("Chat ID")
    r_deriv = st.sidebar.text_input("Deriv Token")
    if st.sidebar.button("Create Pro Account"):
        st.session_state.db[r_email] = {"pass": r_pass, "bot": r_bot, "cid": r_cid, "deriv": r_deriv}
        save_db(st.session_state.db)
        st.sidebar.success("✅ Registered Successfully!")

elif choice == "Login":
    l_email = st.sidebar.text_input("Email")
    l_pass = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Unlock Dashboard"):
        if l_email in st.session_state.db and st.session_state.db[l_email]["pass"] == l_pass:
            st.session_state.user_session = st.session_state.db[l_email]
            st.sidebar.success("✅ Access Granted")
        else: st.sidebar.error("❌ Invalid Credentials")

# --- 5. RISK & ENGINE (FIXED STAKE) ---
u = st.session_state.user_session
v_bot, v_cid, v_deriv = (u["bot"], u["cid"], u["deriv"]) if u else ("", "", "")

st.sidebar.markdown("---")
base_stake = st.sidebar.number_input("Fixed Stake Amount ($)", value=5.0)
max_loss = st.sidebar.number_input("Hard Stop Loss ($)", value=100.0)
live_trade = st.sidebar.toggle("🟢 LIVE TRADING ACTIVE")

if st.sidebar.button("🚀 DEPLOY SNIPER", use_container_width=True):
    if v_deriv:
        st.session_state.trades = []; st.session_state.wins = 0; st.session_state.losses = 0
        st.session_state.running = True
    else: st.sidebar.error("Login first!")

if st.sidebar.button("🛑 KILL SWITCH", use_container_width=True): st.session_state.running = False

status_area = st.empty()
chart_area = st.empty()

# --- 6. THE HIGH-PRECISION ENGINE (IMPROVED LOGIC) ---
async def worker():
    api = DerivAPI(app_id=36544)
    try:
        await api.authorize(v_deriv)
        status_area.success("🟢 SOVEREIGN ENGINE ACTIVE")
        
        while st.session_state.running:
            # 10. Risk Discipline: Stop trading if max loss reached
            if total_pl <= -max_loss:
                status_area.error("🛑 SESSION STOP LOSS REACHED")
                send_tele("🛑 Bot stopped: Max loss hit.", v_bot, v_cid)
                st.session_state.running = False; break

            # 9. Pull optimized tick count (100 ticks instead of 200)
            ticks = await api.ticks_history({"ticks_history": "1HZ100V", "count": 100, "end": "latest"})
            prices = [float(p) for p in ticks["history"]["prices"]]
            chart_area.line_chart(prices[-50:])
            
            # --- 🧠 PRECISION SCORING ENGINE ---
            score = 0
            
            # 3. Strengthen Trend Detection (Full Alignment)
            ma200 = sum(prices[-100:]) / 100
            ma50 = sum(prices[-50:]) / 50
            is_bull_trend = (prices[-1] > ma50 > ma200)
            is_bear_trend = (prices[-1] < ma50 < ma200)
            if is_bull_trend or is_bear_trend: score += 4
            
            # 4. Tighten RSI Conditions
            deltas = pd.Series(prices).diff()
            gain = deltas.where(deltas > 0, 0).rolling(14).mean()
            loss = (-deltas.where(deltas < 0, 0)).rolling(14).mean()
            rsi_s = 100 - (100 / (1 + (gain/loss)))
            rsi = rsi_s.iloc[-1]
            if is_bull_trend and (55 <= rsi <= 65): score += 2
            if is_bear_trend and (35 <= rsi <= 45): score += 2
            
            # 5. Candle Confirmation (Rising/Falling sequence)
            is_rising = prices[-1] > prices[-2] > prices[-3]
            is_falling = prices[-1] < prices[-2] < prices[-3]
            if (is_bull_trend and is_rising) or (is_bear_trend and is_falling): score += 2
            
            # 6. Volatility Filter (Eliminate sideways/dead markets)
            vol = pd.Series(prices[-20:]).std()
            if 0.12 < vol < 0.50: score += 2 # healthy range, skip if flat (<0.12) or chaotic (>0.50)

            # --- ⚡ EXECUTION GATE (1. SCORE >= 9) ---
            if score >= 9:
                direction = "CALL" if is_bull_trend else "PUT"
                status_area.warning(f"💎 ELITE SIGNAL ({score}/10): {direction}")
                
                if live_trade:
                    await api.buy({"buy": 1, "price": base_stake, "parameters": {"amount": base_stake, "basis": "stake", "contract_type": direction, "currency": "USD", "duration": 5, "duration_unit": "t", "symbol": "1HZ100V"}})
                
                await asyncio.sleep(8)
                
                # 8. Correct Profit Calculation (Using broker provided profit)
                history = await api.profit_table({"profit_table": 1, "limit": 1})
                res = history['profit_table']['transactions'][0]
                p_val = float(res['sell_price']) - float(res['buy_price'])
                
                if p_val > 0: st.session_state.wins += 1
                else: st.session_state.losses += 1
                
                bal_upd = await api.balance(); st.session_state.live_bal = bal_upd['balance']['balance']
                st.session_state.trades.append({"Time": time.strftime("%H:%M:%S"), "Type": direction, "Profit": p_val, "Score": f"{score}/10"})
                send_tele(f"📊 {direction} {score}/10 | Profit: {p_val}", v_bot, v_cid)
                
                # 7. Add Cooldown (90 seconds)
                await asyncio.sleep(90) 
            
            # 9. Increase sleep interval slightly
            await asyncio.sleep(2)
    except Exception as e: st.error(f"Engine Error: {e}")

if st.session_state.running: asyncio.run(worker())
           
                
