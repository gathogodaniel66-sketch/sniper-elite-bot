import streamlit as st
import pandas as pd
import asyncio
import time
import requests
import json
import os
from deriv_api import DerivAPI

# --- 1. UI STYLING ---
st.set_page_config(page_title="KihatoGathogo Pro V22.3", layout="wide") 
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

# --- 2. DATA PERSISTENCE ---
DB_FILE = "slimmy_vault_v18.json"
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}
def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f)

if "db" not in st.session_state: st.session_state.db = load_db()
if "trades" not in st.session_state: st.session_state.trades = []
if "running" not in st.session_state: st.session_state.running = False
if "wins" not in st.session_state: st.session_state.wins = 0
if "losses" not in st.session_state: st.session_state.losses = 0
if "live_bal" not in st.session_state: st.session_state.live_bal = 0.0
if "user_session" not in st.session_state: st.session_state.user_session = None
if "is_paid" not in st.session_state: st.session_state.is_paid = False

# --- 3. THE MASTER BYPASS CHECK (CRITICAL FIX) ---
# We check this BEFORE the sidebar logic starts
is_admin = False
if st.session_state.user_session and st.session_state.user_session.get("email") == "gathogodaniel66@gmail.com":
    is_admin = True

# --- 4. SIDEBAR ACCESS CONTROL ---
st.sidebar.title("🔐 Access Center")

# If NOT Admin and NOT Paid, show the lock
if not is_admin and not st.session_state.is_paid:
    st.sidebar.info("💳 Pay 1,300 KES to: 0711934973")
    txn_id = st.sidebar.text_input("M-Pesa Transaction ID").strip().upper()
    
    if st.sidebar.button("Unlock with M-Pesa"):
        if len(txn_id) >= 10:
            if "used_ids" not in st.session_state.db: st.session_state.db["used_ids"] = []
            if txn_id not in st.session_state.db["used_ids"]:
                st.session_state.db["used_ids"].append(txn_id)
                save_db(st.session_state.db)
                st.session_state.is_paid = True
                st.rerun()
    
    st.sidebar.markdown("---")
    choice = st.sidebar.selectbox("Admin/User Portal", ["Login", "Register"])
    
    if choice == "Login":
        l_email = st.sidebar.text_input("Email")
        l_pass = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("System Unlock"):
            if l_email in st.session_state.db and st.session_state.db[l_email]["pass"] == l_pass:
                st.session_state.user_session = st.session_state.db[l_email]
                st.rerun() # This will now trigger is_admin = True at the top
            else:
                st.sidebar.error("Invalid Credentials")
                
    elif choice == "Register":
        r_email = st.sidebar.text_input("New Email")
        r_pass = st.sidebar.text_input("New Password", type="password")
        r_bot = st.sidebar.text_input("Telegram Bot Token")
        r_cid = st.sidebar.text_input("Telegram Chat ID")
        r_deriv = st.sidebar.text_input("Deriv API Token")
        if st.sidebar.button("Register Account"):
            st.session_state.db[r_email] = {"pass": r_pass, "bot": r_bot, "cid": r_cid, "deriv": r_deriv}
            save_db(st.session_state.db)
            st.sidebar.success("✅ Registered! Switch to Login.")

    st.stop() # This only hits if you aren't logged in as Admin or Paid

# --- 5. THE MAIN DASHBOARD (Only visible after bypass) ---
st.markdown("<div class='bank-header'><h2 style='color:white; margin:0;'>SLIMMY PRO V22.3</h2><p style='color:#8cc63f; margin:0;'>GLOBAL PRECISION ARCHITECTURE</p></div>", unsafe_allow_html=True)

u = st.session_state.user_session
v_bot, v_cid, v_deriv = (u["bot"], u["cid"], u["deriv"]) if u else ("", "", "")

# Metrics
total_pl = round(sum([t['Profit'] for t in st.session_state.trades]), 2)
m1, m2, m3 = st.columns(3)
with m1: st.metric("💳 BALANCE", f"${round(st.session_state.live_bal, 2):,.2f}")
with m2: st.metric("💰 SESSION P/L", f"${total_pl:.2f}")
with m3: st.metric("🎯 STATUS", "AUTHORIZED" if is_admin else "PAID USER")

# Charts
st.markdown("### 📈 Live Market Dashboard")
c1, c2 = st.columns(2)
with c1: st.components.v1.html('<iframe src="https://s.tradingview.com/widgetembed/?symbol=OANDA%3AXAUUSD&interval=1&theme=dark" height="350" width="100%"></iframe>', height=350)
with c2: st.components.v1.html('<iframe src="https://tradingview.binary.com/v1.3.10/main.html?symbol=1HZ100V&theme=black" height="350" width="100%"></iframe>', height=350)

# Trade Logic/Deployment
st.sidebar.markdown("---")
base_stake = st.sidebar.number_input("Fixed Stake ($)", value=5.0)
max_loss = st.sidebar.number_input("Hard Stop Loss ($)", value=100.0)
live_trade = st.sidebar.toggle("🟢 LIVE TRADING ACTIVE")

if st.sidebar.button("🚀 DEPLOY SNIPER", use_container_width=True):
    if v_deriv: st.session_state.running = True
    else: st.sidebar.error("Check API Token.")

if st.sidebar.button("🛑 KILL SWITCH", use_container_width=True): st.session_state.running = False

status_area = st.empty()
chart_area = st.empty()

# --- 6. SOVEREIGN ENGINE ---
async def worker():
    api = DerivAPI(app_id=36544)
    try:
        await api.authorize(v_deriv)
        status_area.success("🟢 SOVEREIGN ENGINE ACTIVE")
        while st.session_state.running:
            ticks = await api.ticks_history({"ticks_history": "1HZ100V", "count": 100, "end": "latest"})
            prices = [float(p) for p in ticks["history"]["prices"]]
            chart_area.line_chart(prices[-50:])
            
            # Simplified Logic check for Score 9
            ma200, ma50 = sum(prices[-100:])/100, sum(prices[-50:])/50
            if (prices[-1] > ma50 > ma200) or (prices[-1] < ma50 < ma200):
                direction = "CALL" if prices[-1] > ma50 else "PUT"
                status_area.warning(f"💎 SIGNAL DETECTED: {direction}")
                if live_trade:
                    await api.buy({"buy": 1, "price": base_stake, "parameters": {"amount": base_stake, "basis": "stake", "contract_type": direction, "currency": "USD", "duration": 5, "duration_unit": "t", "symbol": "1HZ100V"}})
                await asyncio.sleep(90)
            await asyncio.sleep(2)
    except Exception as e: st.error(f"Engine Error: {e}")

if st.session_state.running: asyncio.run(worker())
