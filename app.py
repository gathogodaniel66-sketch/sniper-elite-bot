import streamlit as st
import pandas as pd
import asyncio
import time
import requests
import json
import os
from deriv_api import DerivAPI

# --- 1. UI STYLING ---
st.set_page_config(page_title="Slimmy Pro V17.4", layout="centered") 
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

# --- 2. PERMANENT MEMORY (JSON DATABASE) ---
DB_FILE = "user_vault.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: return json.load(f)
    return {}

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f)

# --- 3. TELEGRAM FUNCTION ---
def send_tele(msg, token, cid):
    if token and cid:
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={cid}&text={msg}"
            requests.get(url)
        except: pass

# --- 4. STATE ---
if "trades" not in st.session_state: st.session_state.trades = []
if "running" not in st.session_state: st.session_state.running = False
if "wins" not in st.session_state: st.session_state.wins = 0
if "losses" not in st.session_state: st.session_state.losses = 0
if "live_bal" not in st.session_state: st.session_state.live_bal = 0.0
if "active_user" not in st.session_state: st.session_state.active_user = None

# --- 5. HEADER ---
st.markdown("<div class='bank-header'><h2 style='color:white; margin:0;'>SLIMMY PRO</h2><p style='color:#8cc63f; margin:0; font-size:12px;'>V17.4 PERMANENT MEMORY</p></div>", unsafe_allow_html=True)

# Math calculations
total_pl = sum([t['Profit'] for t in st.session_state.trades])
total_t = st.session_state.wins + st.session_state.losses
win_rate = (st.session_state.wins / total_t * 100) if total_t > 0 else 0

# Metrics Display
st.metric("💳 DERIV BALANCE", f"${st.session_state.live_bal:,.2f}")
st.metric("💰 SESSION P/L", f"${total_pl:.2f}")
st.metric("🎯 ACCURACY", f"{win_rate:.0f}%")
st.metric("✅ WINS", st.session_state.wins)
st.metric("❌ LOSSES", st.session_state.losses)

st.markdown("---")
status_area = st.empty()
chart_area = st.empty()

# --- 6. SIDEBAR & USER CENTER (SENSES ERRORS) ---
st.sidebar.title("👥 User Center")
menu = st.sidebar.radio("Select Action", ["Login", "Register", "Forgot Password"])

db = load_db()

if menu == "Register":
    st.sidebar.subheader("Create Account")
    new_user = st.sidebar.text_input("Username")
    new_email = st.sidebar.text_input("Email")
    new_pass = st.sidebar.text_input("Password", type="password")
    reg_bot = st.sidebar.text_input("Bot Token")
    reg_cid = st.sidebar.text_input("Chat ID")
    reg_deriv = st.sidebar.text_input("Deriv Token")
    
    if st.sidebar.button("💾 Register Account"):
        if not new_user or not new_pass:
            st.sidebar.error("❌ Username and Password cannot be empty!")
        elif new_user in db:
            st.sidebar.error("❌ Username already exists! Try another one.")
        else:
            db[new_user] = {"email": new_email, "pass": new_pass, "bot": reg_bot, "cid": reg_cid, "deriv": reg_deriv}
            save_db(db)
            st.sidebar.success("✅ Account saved forever! Go to Login.")

elif menu == "Login":
    st.sidebar.subheader("Account Login")
    u_name = st.sidebar.text_input("Username")
    u_pass = st.sidebar.text_input("Password", type="password")
    
    if st.sidebar.button("🔓 Login Now"):
        if u_name not in db:
            st.sidebar.error("❌ User not found. Please Register first.")
        elif db[u_name]["pass"] != u_pass:
            st.sidebar.error("❌ Incorrect Password!")
        else:
            st.session_state.active_user = db[u_name]
            st.sidebar.success(f"✅ Welcome {u_name}! All details loaded.")

elif menu == "Forgot Password":
    st.sidebar.subheader("Recovery")
    rec_u = st.sidebar.text_input("Username")
    rec_e = st.sidebar.text_input("Email")
    if st.sidebar.button("🔑 Send to Telegram"):
        if rec_u in db and db[rec_u]["email"] == rec_e:
            send_tele(f"🔐 Recovery: Your password is: {db[rec_u]['pass']}", db[rec_u]['bot'], db[rec_u]['cid'])
            st.sidebar.success("✅ Sent to your Telegram!")
        else: st.sidebar.error("❌ Username or Email is wrong.")

# --- AUTO-LOAD LOADED DATA ---
v_bot = st.session_state.active_user["bot"] if st.session_state.active_user else ""
v_cid = st.session_state.active_user["cid"] if st.session_state.active_user else ""
v_deriv = st.session_state.active_user["deriv"] if st.session_state.active_user else ""

st.sidebar.markdown("---")
st.sidebar.title("📲 Connection Details")
tele_token = st.sidebar.text_input("Bot Token", value=v_bot, type="password")
tele_id = st.sidebar.text_input("Chat ID", value=v_cid)
deriv_token = st.sidebar.text_input("Deriv Token", value=v_deriv, type="password")

st.sidebar.markdown("---")
st.sidebar.title("🏦 Wallet & Risk")
stake = st.sidebar.number_input("Stake Amount ($)", value=2.0)
max_loss = st.sidebar.number_input("Stop Loss Limit ($)", value=50.0)
live_trade = st.sidebar.toggle("🟢 ACTIVATE LIVE TRADING")

if st.sidebar.button("🚀 DEPLOY (START FRESH)", use_container_width=True):
    if deriv_token: 
        st.session_state.trades = []
        st.session_state.wins = 0
        st.session_state.losses = 0
        st.session_state.running = True
    else: st.sidebar.error("❌ Please Login first!")

if st.sidebar.button("🛑 STOP SESSION", use_container_width=True):
    st.session_state.running = False

# --- 7. ENGINE (Same Logic) ---
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
