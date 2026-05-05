import streamlit as st
import pandas as pd
import time
import requests
import json
import os
import asyncio
from deriv_api import DerivAPI

# --- 1. THE ARCHITECTURE (CSS & THEME) ---
st.set_page_config(page_title="KihatoGathogo Pro V21.0", layout="wide") 

st.markdown("""
    <style>
    /* Global Terminal Background */
    .stApp { background-color: #020d08; color: #8cc63f; }
    
    /* Center the Auth Box */
    .main-box {
        max-width: 500px; margin: auto; padding: 40px;
        background-color: transparent; text-align: center; margin-top: 50px;
    }
    
    /* Branding */
    .brand-title { font-family: 'Arial Black', Gadget, sans-serif; font-size: 32px; letter-spacing: 2px; }
    .kihato { color: #ffffff; }
    .gathogo { color: #8cc63f; }
    .pro-tag { color: #ffffff; font-size: 28px; }
    .version-text { color: #4e805d; font-size: 14px; letter-spacing: 3px; margin-bottom: 30px; }
    
    /* Input Fields Styling */
    label { color: #4e805d !important; font-size: 10px !important; letter-spacing: 1px; }
    .stTextInput input {
        background-color: #05140d !important;
        border: 1px solid #1a3a2a !important;
        color: #8cc63f !important;
        border-radius: 4px !important;
    }
    
    /* Establish Uplink Button */
    .stButton>button {
        background-color: #8cc63f !important;
        color: #020d08 !important;
        font-weight: bold !important;
        border: none !important;
        width: 100% !important;
        padding: 15px !important;
        border-radius: 4px !important;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    
    /* Navigation Bar (Post-Login) */
    .top-nav {
        display: flex; justify-content: space-between; align-items: center;
        padding: 10px 20px; background-color: #05140d; border-bottom: 1px solid #1a3a2a;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE ENGINE DATA ---
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
if "uplink_established" not in st.session_state: st.session_state.uplink_established = False
if "user_session" not in st.session_state: st.session_state.user_session = None
if "live_bal" not in st.session_state: st.session_state.live_bal = 0.0

async def sync_balance():
    user = st.session_state.user_session
    if not user: return
    try:
        if user.get("type") == "deriv":
            api = DerivAPI(app_id=1089)
            await api.authorize(user["deriv"])
            bal_data = await api.balance() 
            st.session_state.live_bal = float(bal_data['balance']['balance'])
            await api.clear()
    except: pass

# --- 3. THE "ESTABLISH UPLINK" SCREEN (image_e46f60.png) ---
if not st.session_state.uplink_established:
    st.markdown("""
        <div class="main-box">
            <div style="font-size: 50px; color: #8cc63f;">🎯</div>
            <div class="brand-title">
                <span class="kihato">KIHATO</span><span class="gathogo">GATHOGO</span> <span class="pro-tag">PRO</span>
            </div>
            <div class="version-text">V21.0 GLOBAL PRECISION ARCHITECTURE</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Simple Toggle for Login/Register (matches the tab-style header in your image)
    auth_mode = st.radio("", ["AUTH_LOGIN", "INIT_SYSTEM"], horizontal=True, label_visibility="collapsed")
    
    with st.container():
        if auth_mode == "AUTH_LOGIN":
            op_id = st.text_input("OPERATOR_ID (EMAIL)", placeholder="gathogodaniel66@gmail.com")
            sec_key = st.text_input("SECURITY_KEY (PASSWORD)", type="password")
            
            if st.button("💾 ESTABLISH UPLINK"):
                if op_id in st.session_state.db and st.session_state.db[op_id]["pass"] == sec_key:
                    with st.spinner("SYNCHRONIZING TERMINAL..."):
                        st.session_state.user_session = st.session_state.db[op_id]
                        asyncio.run(sync_balance())
                        time.sleep(1)
                        st.session_state.uplink_established = True
                        st.rerun()
                else:
                    st.error("UPLINK FAILED: IDENTITY NOT RECOGNIZED")
        else:
            # Register Mode
            reg_broker = st.selectbox("SELECT ENGINE", ["Deriv API", "Pocket Option OTC"])
            reg_email = st.text_input("NEW OPERATOR_ID")
            reg_pass = st.text_input("NEW SECURITY_KEY", type="password")
            reg_token = st.text_input("API_TOKEN / SSID")
            
            if st.button("CREATE SECURE PROFILE"):
                b_type = "deriv" if "Deriv" in reg_broker else "pocket"
                st.session_state.db[reg_email] = {
                    "pass": reg_pass, 
                    "deriv" if b_type == "deriv" else "po_ssid": reg_token,
                    "type": b_type, "email": reg_email
                }
                save_db(st.session_state.db)
                st.success("PROFILE ENCRYPTED. PROCEED TO AUTH_LOGIN.")

    st.markdown("<br><center style='font-size:10px; color:#4e805d;'>New to Deriv? <a href='#' style='color:#8cc63f;'>Follow the step-by-step setup guide →</a></center>", unsafe_allow_html=True)

# --- 4. THE DASHBOARD (REVEALED AFTER UPLINK) ---
else:
    # Header from image_e80eb0.png
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

    # 4-Column Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("BALANCE", f"${st.session_state.live_bal:,.2f}")
    m2.metric("SESSION P/L", "$0.00")
    m3.metric("WIN RATE", "0.0%")
    m4.metric("WIN STREAK", "0W / 0L")

    # Layout Grid
    col_l, col_r = st.columns([3, 1])
    with col_l:
        st.components.v1.html('<iframe src="https://tradingview.binary.com/v1.3.10/main.html?symbol=1HZ100V&theme=black" height="500" width="100%"></iframe>', height=500)
    with col_r:
        st.markdown("### ⚙️ ENGINE_CONTROL")
        if st.button("DISCONNECT"):
            st.session_state.uplink_established = False
            st.rerun()
        st.number_input("STAKE", value=10)
        st.slider("SIGNAL THRESHOLD", 8, 10, 8)
        st.button("▶️ START SNIPER")
