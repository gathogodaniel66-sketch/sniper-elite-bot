import streamlit as st
import pandas as pd
import asyncio
import time
import requests
import json
import os
import nest_asyncio
from deriv_api import DerivAPI

# Required for Streamlit to handle background async tasks
nest_asyncio.apply()

# --- 1. UI STYLING ---
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

# --- 2. DATA & BALANCE SYNC ENGINE ---
DB_FILE = "slimmy_vault_v18.json"
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f)

async def fetch_real_balance():
    """Retrieves live account balance from the active broker."""
    if st.session_state.user_session:
        user = st.session_state.user_session
        try:
            if user.get("type") == "deriv" and user.get("deriv"):
                api = DerivAPI(app_id=1089)
                authorize = await api.authorize(user["deriv"])
                bal_resp = await api.balance()
                st.session_state.live_bal = float(bal_resp['balance']['balance'])
                await api.clear()
            elif user.get("type") == "pocket" and user.get("po_ssid"):
                # Use a request-based sync for Pocket Option balance via SSID
                headers = {"Cookie": f"ssid={user['po_ssid']}"}
                response = requests.get("https://pocketoption.com/en/cabinet/", headers=headers, timeout=5)
                # Logic would parse the real balance from the cabinet HTML here
                # st.session_state.live_bal = parsed_value
                pass 
        except Exception:
            pass

if "db" not in st.session_state: st.session_state.db = load_db()
if "live_bal" not in st.session_state: st.session_state.live_bal = 0.0
if "user_session" not in st.session_state: st.session_state.user_session = None
if "running" not in st.session_state: st.session_state.running = False

# --- 3. HEADER & METRICS ---
st.markdown("<div class='bank-header'><h2 style='color:white; margin:0;'>SLIMMY PRO V21.0</h2><p style='color:#8cc63f; margin:0;'>GLOBAL PRECISION ARCHITECTURE</p></div>", unsafe_allow_html=True)

m1, m2, m3 = st.columns(3)
with m1: st.metric("💳 REAL BALANCE", f"${st.session_state.live_bal:,.2f}")
with m2: st.metric("💰 SESSION P/L", "$0.00")
with m3: st.metric("📉 ENGINE", "ACTIVE" if st.session_state.running else "OFFLINE")

# --- 4. SIDEBAR: DIFFERENTIATED USER CENTER ---
st.sidebar.title("👥 User Center")
broker_choice = st.sidebar.radio("Select Trading Engine", ["Deriv API", "Pocket Option OTC"])
action = st.sidebar.selectbox("Action", ["Login", "Register", "Password Recovery"])

if action == "Register":
    st.sidebar.subheader(f"📝 {broker_choice} Register")
    r_email = st.sidebar.text_input("Email", key="reg_email")
    r_pass = st.sidebar.text_input("Password", type="password", key="reg_pass")
    
    if broker_choice == "Deriv API":
        r_token = st.sidebar.text_input("Deriv API Token")
        if st.sidebar.button("Register Deriv"):
            st.session_state.db[r_email] = {"pass": r_pass, "deriv": r_token, "type": "deriv"}
            save_db(st.session_state.db); st.sidebar.success("Deriv Registered!")
    else:
        r_ssid = st.sidebar.text_input("Pocket SSID")
        if st.sidebar.button("Register Pocket"):
            st.session_state.db[r_email] = {"pass": r_pass, "po_ssid": r_ssid, "type": "pocket"}
            save_db(st.session_state.db); st.sidebar.success("Pocket Registered!")

elif action == "Login":
    st.sidebar.subheader(f"🔑 {broker_choice} Login")
    l_email = st.sidebar.text_input("Email", key="log_email")
    l_pass = st.sidebar.text_input("Password", type="password", key="log_pass")
    
    if st.sidebar.button("Unlock Dashboard"):
        if l_email in st.session_state.db and st.session_state.db[l_email]["pass"] == l_pass:
            user_data = st.session_state.db[l_email]
            db_type = user_data.get("type", "deriv")
            
            # Differentiate Login Warning
            if db_type != broker_choice.lower().split()[0]:
                st.sidebar.warning(f"⚠️ Account type mismatch ({db_type.upper()})")
            
            st.session_state.user_session = user_data
            asyncio.run(fetch_real_balance())
            st.sidebar.success("✅ Access Accepted")
            time.sleep(1); st.rerun()
        else:
            st.sidebar.error("❌ Access Denied")

# --- 5. MARKET DASHBOARD ---
c1, c2 = st.columns(2)
with c1: st.components.v1.html('<iframe src="https://s.tradingview.com/widgetembed/?symbol=OANDA%3AXAUUSD&interval=1&theme=dark" height="350" width="100%"></iframe>', height=350)
with c2: st.components.v1.html('<iframe src="https://tradingview.binary.com/v1.3.10/main.html?symbol=1HZ100V&theme=black" height="350" width="100%"></iframe>', height=350)

# --- 6. SNIPER COMMAND CENTER ---
st.markdown("### 🎮 Sniper Command Center")
with st.container():
    col1, col2, col3 = st.columns(3)
    with col1:
        stake = st.number_input("Stake", value=1.0, min_value=0.35)
        mart = st.number_input("Martingale", value=2.1)
    with col2:
        tp = st.number_input("Take Profit", value=2.0)
        sl = st.number_input("Stop Loss", value=10.0)
    with col3:
        if not st.session_state.running:
            if st.button("▶️ START SNIPER", use_container_width=True):
                if st.session_state.user_session:
                    st.session_state.running = True; st.rerun()
                else: st.warning("Login First!")
        else:
            if st.button("🛑 STOP SNIPER", use_container_width=True):
                st.session_state.running = False; st.rerun()

# --- 7. LIVE ENGINE ---
if st.session_state.running:
    asyncio.run(fetch_real_balance())
