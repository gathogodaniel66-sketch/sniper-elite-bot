import streamlit as st
import pandas as pd
import asyncio
import time
import requests
import json
import os
from deriv_api import DerivAPI

# --- 1. UI STYLING (PERMANENT) ---
st.set_page_config(page_title="Slimmy Pro V21.0", layout="wide") 
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

# --- 2. DATA VAULT LOGIC ---
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
if "live_bal" not in st.session_state: st.session_state.live_bal = 0.0 
if "user_session" not in st.session_state: st.session_state.user_session = None
if "session_profit" not in st.session_state: st.session_state.session_profit = 0.0

# --- 3. HEADER & METRICS ---
st.markdown("<div class='bank-header'><h2 style='color:white; margin:0;'>SLIMMY PRO V21.0</h2><p style='color:#8cc63f; margin:0;'>GLOBAL PRECISION ARCHITECTURE</p></div>", unsafe_allow_html=True)

m1, m2, m3 = st.columns(3)
with m1: st.metric("💳 BALANCE", f"${st.session_state.live_bal:,.2f}")
with m2: st.metric("💰 SESSION P/L", f"${round(st.session_state.session_profit, 2)}")
with m3: st.metric("📉 STATUS", "RUNNING" if st.session_state.running else "IDLE")

st.markdown("---")

# --- 4. MARKET VISUALS ---
col_main_1, col_main_2 = st.columns(2)
with col_main_1:
    st.write("**Gold Market**")
    st.components.v1.html('<iframe src="https://s.tradingview.com/widgetembed/?symbol=OANDA%3AXAUUSD&interval=1&theme=dark" height="350" width="100%"></iframe>', height=350)
with col_main_2:
    st.write("**Volatility / OTC Market**")
    st.components.v1.html('<iframe src="https://tradingview.binary.com/v1.3.10/main.html?symbol=1HZ100V&theme=black" height="350" width="100%"></iframe>', height=350)

# --- 5. SIDEBAR: SEPARATED USER CENTER ---
st.sidebar.title("👥 User Center")
broker_engine = st.sidebar.radio("Select Trading Engine", ["Deriv API", "Pocket Option OTC"])

action = st.sidebar.selectbox("Action", ["Login", "Register", "Secure Gateway", "Password Recovery"])

if action == "Register":
    st.sidebar.subheader(f"📝 {broker_engine} Registration")
    r_email = st.sidebar.text_input("New Email")
    r_pass = st.sidebar.text_input("New Password", type="password")
    
    if broker_engine == "Deriv API":
        r_token = st.sidebar.text_input("Deriv API Token")
        if st.sidebar.button("Create Account"):
            st.session_state.db[r_email] = {"pass": r_pass, "deriv": r_token, "type": "deriv"}
            save_db(st.session_state.db)
            st.sidebar.success("✅ Deriv Account Created!")
    else:
        r_ssid = st.sidebar.text_input("Pocket Option SSID")
        if st.sidebar.button("Create Account"):
            st.session_state.db[r_email] = {"pass": r_pass, "po_ssid": r_ssid, "type": "pocket"}
            save_db(st.session_state.db)
            st.sidebar.success("✅ Pocket Account Created!")

elif action == "Login":
    l_email = st.sidebar.text_input("Email")
    l_pass = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Unlock Dashboard"):
        if l_email in st.session_state.db and st.session_state.db[l_email]["pass"] == l_pass:
            st.session_state.user_session = st.session_state.db[l_email]
            # FIXED: Added .get() to prevent KeyError
            u_type = st.session_state.user_session.get("type", "Standard")
            st.sidebar.success(f"✅ Logged in as {u_type.upper()}")
            time.sleep(1)
            st.rerun()
        else: st.sidebar.error("❌ Access Denied")

elif action == "Password Recovery":
    st.sidebar.subheader("🔑 Recovery")
    rec_email = st.sidebar.text_input("Email")
    if st.sidebar.button("Get Hint"):
        if rec_email in st.session_state.db:
            st.sidebar.info(f"Your password starts with: {st.session_state.db[rec_email]['pass'][:2]}***")
        else: st.sidebar.error("Email not found")

# --- 6. SNIPER COMMAND CENTER ---
st.markdown("### 🎮 Sniper Command Center")
with st.container():
    c1, c2, c3 = st.columns(3)
    with c1:
        stake = st.number_input("Stake ($)", value=1.0, min_value=0.35)
        m_mult = st.number_input("Martingale", value=2.1)
    with c2:
        tp_val = st.number_input("Take Profit ($)", value=2.0)
        sl_val = st.number_input("Stop Loss ($)", value=10.0)
    with c3:
        if not st.session_state.running:
            if st.button("▶️ START SNIPER", use_container_width=True):
                if st.session_state.user_session:
                    st.session_state.running = True
                    st.rerun()
                else: st.warning("Login First!")
        else:
            if st.button("🛑 STOP SNIPER", use_container_width=True):
                st.session_state.running = False
                st.rerun()

# --- 7. AUTO-STOP LOGIC ---
if st.session_state.running:
    if st.session_state.session_profit >= tp_val:
        st.success("🎯 Take Profit Hit!")
        st.session_state.running = False
    elif st.session_state.session_profit <= -abs(sl_val):
        st.error("🛑 Stop Loss Hit!")
        st.session_state.running = False
