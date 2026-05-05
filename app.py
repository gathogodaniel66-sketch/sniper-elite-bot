import streamlit as st
import pandas as pd
import time
import requests
import json
import os
import asyncio
from deriv_api import DerivAPI

# --- 1. ARCHITECTURE & THEME ---
st.set_page_config(page_title="KihatoGathogo Pro V21.0", layout="wide") 

st.markdown("""
    <style>
    .stApp { background-color: #020d08; color: #8cc63f; }
    .main-box { max-width: 500px; margin: auto; padding: 40px; text-align: center; margin-top: 30px; }
    .brand-title { font-family: 'Arial Black', sans-serif; font-size: 32px; letter-spacing: 2px; }
    .kihato { color: #ffffff; }
    .gathogo { color: #8cc63f; }
    .pro-tag { color: #ffffff; font-size: 28px; }
    .version-text { color: #4e805d; font-size: 14px; letter-spacing: 3px; margin-bottom: 20px; }
    .stTextInput input { background-color: #05140d !important; border: 1px solid #1a3a2a !important; color: #8cc63f !important; }
    .stButton>button { background-color: #8cc63f !important; color: #020d08 !important; font-weight: bold !important; width: 100% !important; padding: 12px !important; border-radius: 4px !important; }
    .top-nav { display: flex; justify-content: space-between; align-items: center; padding: 10px 20px; background-color: #05140d; border-bottom: 1px solid #1a3a2a; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE REAL LOGIN & CREATION ENGINE ---
DB_FILE = "slimmy_vault_v18.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f)

# Telegram Alert System
def send_telegram_msg(msg):
    if st.session_state.user_session:
        token = st.session_state.user_session.get('tele_token')
        chat_id = st.session_state.user_session.get('tele_id')
        if token and chat_id:
            try:
                url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={msg}"
                requests.get(url)
            except: pass

# --- 3. SESSION INITIALIZATION ---
if "db" not in st.session_state: st.session_state.db = load_db()
if "uplink_established" not in st.session_state: st.session_state.uplink_established = False
if "user_session" not in st.session_state: st.session_state.user_session = None
if "live_bal" not in st.session_state: st.session_state.live_bal = 0.0

async def sync_balance():
    user = st.session_state.user_session
    if user and user.get("deriv"):
        try:
            api = DerivAPI(app_id=1089)
            await api.authorize(user["deriv"])
            bal_data = await api.balance() 
            st.session_state.live_bal = float(bal_data['balance']['balance'])
            await api.clear()
        except: pass

# --- 4. AUTH INTERFACE (image_e7a593.png) ---
if not st.session_state.uplink_established:
    st.markdown("""
        <div class="main-box">
            <div style="font-size: 50px; color: #8cc63f;">🎯</div>
            <div class="brand-title"><span class="kihato">KIHATO</span><span class="gathogo">GATHOGO</span> <span class="pro-tag">PRO</span></div>
            <div class="version-text">V21.0 GLOBAL PRECISION ARCHITECTURE</div>
        </div>
    """, unsafe_allow_html=True)
    
    auth_mode = st.radio("", ["AUTH_LOGIN", "INIT_SYSTEM"], horizontal=True, label_visibility="collapsed")
    
    if auth_mode == "AUTH_LOGIN":
        op_id = st.text_input("OPERATOR_ID (EMAIL)", placeholder="Enter your email")
        sec_key = st.text_input("SECURITY_KEY (PASSWORD)", type="password")
        
        if st.button("💾 ESTABLISH UPLINK"):
            if op_id in st.session_state.db and st.session_state.db[op_id]["pass"] == sec_key:
                st.session_state.user_session = st.session_state.db[op_id]
                st.session_state.user_session['email'] = op_id # Keep track of who is logged in
                with st.spinner("SYNCHRONIZING TERMINAL..."):
                    asyncio.run(sync_balance())
                    send_telegram_msg("🚀 Uplink Established. System Online.")
                    st.session_state.uplink_established = True
                    st.rerun()
            else:
                st.error("UPLINK FAILED: IDENTITY NOT RECOGNIZED")

    else:
        # --- NEW REAL ACCOUNT CREATION ENGINE ---
        st.info("ENTER SYSTEM CREDENTIALS")
        r_email = st.text_input("OPERATOR_EMAIL (Unique ID)")
        r_pass = st.text_input("SECURITY_KEY (Password)", type="password")
        r_token = st.text_input("DERIV_API_TOKEN")
        r_tele_bot = st.text_input("TELEGRAM_BOT_TOKEN")
        r_tele_id = st.text_input("TELEGRAM_CHAT_ID")
        
        if st.button("💾 INITIALIZE PROFILE"):
            if r_email and r_pass and r_token:
                # The Identity Object
                st.session_state.db[r_email] = {
                    "pass": r_pass,
                    "deriv": r_token,
                    "tele_token": r_tele_bot,
                    "tele_id": r_tele_id,
                    "type": "deriv"
                }
                save_db(st.session_state.db)
                st.success("PROFILE ENCRYPTED. YOU CAN NOW LOGIN.")
            else:
                st.warning("All primary fields (Email, Pass, Token) required.")

# --- 5. THE DASHBOARD (REVEALED AFTER UPLINK) ---
else:
    # Header
    st.markdown(f"""
        <div class="top-nav">
            <div style="font-weight:bold; letter-spacing:2px; color:#8cc63f;">SLIMMY <span style="color:white;">PRO V21.0</span></div>
            <div style="display: flex; gap: 20px; font-size: 13px; color: #4e805d;">
                <span>📉 TERMINAL</span> <span>🔄 LEDGER</span> <span>📖 SETUP GUIDE</span>
            </div>
            <div style="font-size: 12px; color: #8cc63f;">
                ● {st.session_state.user_session['email']} | <span style="color:white;">UPLINK: ACTIVE</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("BALANCE", f"${st.session_state.live_bal:,.2f}")
    m2.metric("SESSION P/L", "$0.00")
    m3.metric("WIN RATE", "0.0%")
    m4.metric("WIN STREAK", "0W / 0L")

    # Layout
    col_l, col_r = st.columns([3, 1])
    with col_l:
        st.components.v1.html('<iframe src="https://tradingview.binary.com/v1.3.10/main.html?symbol=1HZ100V&theme=black" height="500" width="100%"></iframe>', height=500)
    with col_r:
        st.markdown("### ⚙️ ENGINE_CONTROL")
        if st.button("DISCONNECT"):
            st.session_state.uplink_established = False
            st.rerun()
        
        st.number_input("STAKE", value=10)
        st.button("▶️ START SNIPER")
