import streamlit as st
import pandas as pd
import time
import requests
import json
import os
import asyncio
from deriv_api import DerivAPI

# --- 1. PRO TERMINAL STYLING ---
st.set_page_config(page_title="KihatoGathogo Pro V21.0", layout="wide") 

st.markdown("""
    <style>
    .stApp { background-color: #020d08; color: #8cc63f; }
    .top-nav { display: flex; justify-content: space-between; padding: 10px 20px; background: #05140d; border-bottom: 1px solid #1a3a2a; }
    div[data-testid="stMetric"] { background: #05140d; border: 1px solid #1a3a2a; padding: 15px; border-radius: 5px; }
    .stButton>button { background-color: #8cc63f !important; color: #020d08 !important; font-weight: bold !important; width: 100%; border-radius: 4px; }
    .stop-btn>div>button { background-color: #ff4b4b !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. PERSISTENT ENGINE & ACCOUNTING ---
DB_FILE = "slimmy_vault_v18.json"
def load_db():
    if os.path.exists(DB_FILE):
        try: return json.load(open(DB_FILE, "r"))
        except: return {}
    return {}

if "db" not in st.session_state: st.session_state.db = load_db()
if "uplink_established" not in st.session_state: st.session_state.uplink_established = False
if "current_page" not in st.session_state: st.session_state.current_page = "TERMINAL"
if "running" not in st.session_state: st.session_state.running = False

# Accounting States
if "live_bal" not in st.session_state: st.session_state.live_bal = 0.0
if "total_profit" not in st.session_state: st.session_state.total_profit = 0.0
if "total_loss" not in st.session_state: st.session_state.total_loss = 0.0
if "wins" not in st.session_state: st.session_state.wins = 0
if "losses" not in st.session_state: st.session_state.losses = 0
if "trade_count" not in st.session_state: st.session_state.trade_count = 0

# --- 3. CORE FUNCTIONS ---
async def sync_account_data():
    """Fetches Real Balance from Deriv"""
    user = st.session_state.user_session
    if user and user.get("deriv"):
        try:
            api = DerivAPI(app_id=1089)
            await api.authorize(user["deriv"])
            bal_data = await api.balance()
            st.session_state.live_bal = float(bal_data['balance']['balance'])
            await api.clear()
        except: pass

def get_win_rate():
    total = st.session_state.wins + st.session_state.losses
    return (st.session_state.wins / total * 100) if total > 0 else 0.0

# --- 4. AUTH GATE ---
if not st.session_state.uplink_established:
    st.title("KIHATOGATHOGO PRO: UPLINK REQUIRED")
    op_id = st.text_input("OPERATOR_ID")
    sec_key = st.text_input("SECURITY_KEY", type="password")
    if st.button("ESTABLISH UPLINK"):
        if op_id in st.session_state.db and st.session_state.db[op_id]["pass"] == sec_key:
            st.session_state.user_session = st.session_state.db[op_id]
            st.session_state.user_session['email'] = op_id
            asyncio.run(sync_account_data())
            st.session_state.uplink_established = True
            st.rerun()
else:
    # --- 5. DASHBOARD LAYOUT ---
    # Top Nav Switcher
    cols = st.columns([2, 4, 2])
    with cols[1]:
        c1, c2, c3 = st.columns(3)
        if c1.button("📉 TERMINAL"): st.session_state.current_page = "TERMINAL"; st.rerun()
        if c2.button("🔄 LEDGER"): st.session_state.current_page = "LEDGER"; st.rerun()
        if c3.button("📖 SETUP GUIDE"): st.session_state.current_page = "GUIDE"; st.rerun()

    if st.session_state.current_page == "TERMINAL":
        # REAL-TIME METRICS
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("REAL BALANCE", f"${st.session_state.live_bal:,.2f}")
        m2.metric("PROFIT", f"${st.session_state.total_profit:,.2f}", delta_color="normal")
        m3.metric("LOSS", f"${st.session_state.total_loss:,.2f}", delta_color="inverse")
        m4.metric("WIN RATE", f"{get_win_rate():.1f}%")
        m5.metric("TRADES", f"{st.session_state.trade_count}")

        col_l, col_r = st.columns([3, 1])
        
        with col_l:
            st.components.v1.html('<iframe src="https://tradingview.binary.com/v1.3.10/main.html?symbol=1HZ100V&theme=black" height="450" width="100%"></iframe>', height=450)
            st.markdown("### 📡 MARKET SIGNAL SCANNER")
            st.write("Bot Status: " + ("🟢 RUNNING" if st.session_state.running else "🔴 STOPPED"))

        with col_r:
            st.markdown("### ⚙️ ENGINE_CONTROL")
            
            # Control Inputs
            stake_amt = st.number_input("STAKE AMOUNT ($)", value=10.0, min_value=0.35)
            stop_loss_limit = st.number_input("STOP LOSS ($)", value=50.0)
            max_trades_limit = st.number_input("MAX NUMBER OF TRADES", value=10, min_value=1)
            
            st.markdown("---")
            
            # START / STOP BUTTONS
            if not st.session_state.running:
                if st.button("▶️ START BOT", use_container_width=True):
                    st.session_state.running = True
                    st.rerun()
            else:
                st.markdown('<div class="stop-btn">', unsafe_allow_html=True)
                if st.button("🛑 STOP BOT", use_container_width=True):
                    st.session_state.running = False
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Automation Safety Checks
            if st.session_state.running:
                if st.session_state.total_loss >= stop_loss_limit:
                    st.error("STOP LOSS REACHED")
                    st.session_state.running = False
                if st.session_state.trade_count >= max_trades_limit:
                    st.warning("MAX TRADES COMPLETED")
                    st.session_state.running = False

    elif st.session_state.current_page == "LEDGER":
        st.header("🔄 Performance Ledger")
        st.write(f"Total Wins: {st.session_state.wins} | Total Losses: {st.session_state.losses}")

    elif st.session_state.current_page == "GUIDE":
        st.header("📖 Bot Instructions")
        st.write("Set your Stake and Stop Loss before pressing START. The bot will auto-stop when Max Trades are hit.")
