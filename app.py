import streamlit as st
import pandas as pd
import asyncio
import time
import requests
import json
import os
from deriv_api import DerivAPI

# --- 1. UI STYLING ---
st.set_page_config(page_title="Slimmy Pro V17.6", layout="centered") 
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

# --- 2. PERMANENT DATABASE (EMAIL-BASED) ---
DB_FILE = "slimmy_members.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_member(email, data):
    db = load_db()
    db[email] = data
    with open(DB_FILE, "w") as f:
        json.dump(db, f)

# --- 3. STATE & TELEGRAM ---
if "trades" not in st.session_state: st.session_state.trades = []
if "running" not in st.session_state: st.session_state.running = False
if "wins" not in st.session_state: st.session_state.wins = 0
if "losses" not in st.session_state: st.session_state.losses = 0
if "live_bal" not in st.session_state: st.session_state.live_bal = 0.0
if "user_session" not in st.session_state: st.session_state.user_session = None

def send_tele(msg, token, cid):
    if token and cid:
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={cid}&text={msg}"
            requests.get(url)
        except: pass

# --- 4. HEADER ---
st.markdown("<div class='bank-header'><h2 style='color:white; margin:0;'>SLIMMY PRO</h2><p style='color:#8cc63f; margin:0; font-size:12px;'>V17.6 EMAIL ACCESS</p></div>", unsafe_allow_html=True)

# Math calculations
total_pl = sum([t['Profit'] for t in st.session_state.trades])
total_t = st.session_state.wins + st.session_state.losses
win_rate = (st.session_state.wins / total_t * 100) if total_t > 0 else 0

st.metric("💳 DERIV BALANCE", f"${st.session_state.live_bal:,.2f}")
st.metric("💰 SESSION P/L", f"${total_pl:.2f}")
st.metric("🎯 ACCURACY", f"{win_rate:.0f}%")
st.metric("✅ WINS", st.session_state.wins)
st.metric("❌ LOSSES", st.session_state.losses)

st.markdown("---")
status_area = st.empty()
chart_area = st.empty()

# --- 5. USER CENTER ---
st.sidebar.title("👥 User Center")
choice = st.sidebar.selectbox("Access Mode", ["Login", "Register", "Forgot Password"])

db = load_db()

if choice == "Register":
    st.sidebar.subheader("Join Slimmy Pro")
    r_email = st.sidebar.text_input("Email Address")
    r_user = st.sidebar.text_input("Username (Display Name)")
    r_pass = st.sidebar.text_input("Password", type="password")
    r_bot = st.sidebar.text_input("Telegram Bot Token")
    r_cid = st.sidebar.text_input("Telegram Chat ID")
    r_deriv = st.sidebar.text_input("Deriv API Token")
    
    if st.sidebar.button("✨ Create Account"):
        if r_email in db:
            st.sidebar.error("❌ Email already registered!")
        elif r_email and r_pass:
            user_data = {"name": r_user, "pass": r_pass, "bot": r_bot, "cid": r_cid, "deriv": r_deriv}
            save_member(r_email, user_data)
            st.sidebar.success("✅ Registered! Switch to 'Login' now.")
        else:
            st.sidebar.error("❌ Email and Password are required!")

elif choice == "Login":
    st.sidebar.subheader("Member Login")
    l_email = st.sidebar.text_input("Email")
    l_pass = st.sidebar.text_input("Password", type="password")
    
    if st.sidebar.button("🔓 Login Now"):
        if l_email in db and db[l_email]["pass"] == l_pass:
            st.session_state.user_session = db[l_email]
            st.sidebar.success(f"✅ Welcome back, {db[l_email]['name']}!")
        else:
            st.sidebar.error("❌ Incorrect Email or Password")

elif choice == "Forgot Password":
    st.sidebar.subheader("Reset Access")
    f_email = st.sidebar.text_input("Enter Registered Email")
    if st.sidebar.button("🔑 Send Password"):
        if f_email in db:
            u = db[f_email]
            send_tele(f"🔐 Password Recovery: Your password is {u['pass']}", u['bot'], u['cid'])
            st.sidebar.success("✅ Sent! Check your Telegram.")
        else:
            st.sidebar.error("❌ Email not found.")

# --- 6. AUTO-LOAD & TRADING ENGINE ---
u = st.session_state.user_session
v_bot = u["bot"] if u else ""
v_cid = u["cid"] if u else ""
v_deriv = u["deriv"] if u else ""

st.sidebar.markdown("---")
st.sidebar.title("📲 Connection Details")
tele_token = st.sidebar.text_input("Bot Token", value=v_bot, type="password")
tele_id = st.sidebar.text_input("Chat ID", value=v_cid)
deriv_token = st.sidebar.text_input("Deriv Token", value=v_deriv, type="password")

st.sidebar.markdown("---")
st.sidebar.title("🏦 Risk & Trade")
stake = st.sidebar.number_input("Stake ($)", value=2.0)
max_loss = st.sidebar.number_input("Stop Loss ($)", value=50.0)
live_trade = st.sidebar.toggle("🟢 ACTIVATE LIVE TRADING")

if st.sidebar.button("🚀 DEPLOY (START FRESH)", use_container_width=True):
    if deriv_token: 
        st.session_state.trades = []
        st.session_state.wins = 0; st.session_state.losses = 0
        st.session_state.running = True
    else: st.sidebar.error("❌ Please login first!")

if st.sidebar.button("🛑 STOP SESSION", use_container_width=True):
    st.session_state.running = False

async def worker():
    api = DerivAPI(app_id=36544)
    try:
        await api.authorize(deriv_token)
        status_area.success("🟢 CONNECTED")
        bal_res = await api.balance()
        st.session_state.live_bal = bal_res['balance']['balance']
        send_tele(f"🏁 NEW ROUND STARTED\nBalance: ${st.session_state.live_bal}", tele_token, tele_id)
        while st.session_state.running:
            if total_pl <= -max_loss:
                send_tele("⚠️ Stop Loss Hit!", tele_token, tele_id); st.session_state.running = False; break
            ticks = await api.ticks_history({"ticks_history": "1HZ100V", "count": 30, "end": "latest"})
            prices = [float(p) for p in ticks["history"]["prices"]]
            chart_area.line_chart(prices)
            ma_short = sum(prices[-10:])/10; momentum = prices[-1] - prices[-5]
            if (prices[-1] > ma_short and momentum > 0.4) or (prices[-1] < ma_short and momentum < -0.4):
                trade_type = "CALL" if prices[-1] > ma_short else "PUT"
                status_area.warning(f"🎯 SIGNAL: {trade_type}")
                await asyncio.sleep(2)
                if live_trade: await api.buy({"buy": 1, "price": stake, "parameters": {"amount": stake, "basis": "stake", "contract_type": trade_type, "currency": "USD", "duration": 5, "duration_unit": "t", "symbol": "1HZ100V"}})
                await asyncio.sleep(8)
                history = await api.profit_table({"profit_table": 1, "limit": 1})
                last_trade = history['profit_table']['transactions'][0]
                p_val = float(last_trade['sell_price']) - float(last_trade['buy_price'])
                if p_val > 0: st.session_state.wins += 1
                else: st.session_state.losses += 1
                bal_upd = await api.balance(); st.session_state.live_bal = bal_upd['balance']['balance']
                st.session_state.trades.append({"Time": time.strftime("%H:%M"), "Type": trade_type, "Profit": p_val})
                send_tele(f"💰 Result: {'WIN' if p_val > 0 else 'LOSS'} (${p_val:.2f})\n💳 Balance: ${st.session_state.live_bal}", tele_token, tele_id)
                await asyncio.sleep(50)
            await asyncio.sleep(1)
    except Exception as e: st.error(f"Error: {e}")

if st.session_state.running: asyncio.run(worker())
