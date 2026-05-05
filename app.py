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
    .log-text { font-family: monospace; font-size: 10px; color: #4e805d; background: #05140d; padding: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE EXECUTION ENGINE (THE MISSING PIECE) ---
async def execute_deriv_trade(symbol, stake, contract_type):
    """Handles the Proposal and Buy steps required by Deriv API"""
    user = st.session_state.user_session
    try:
        api = DerivAPI(app_id=1089)
        await api.authorize(user["deriv"])
        
        # STEP 1: Request Contract Proposal
        proposal = await api.proposal({
            "proposal": 1,
            "amount": float(stake),
            "basis": "stake",
            "contract_type": "CALL" if contract_type == "RISE" else "PUT",
            "currency": "USD",
            "duration": 1,
            "duration_unit": "m",
            "symbol": symbol
        })
        
        # STEP 2: Execute Purchase if Proposal is Valid
        if "proposal" in proposal:
            p_id = proposal["proposal"]["id"]
            buy = await api.buy({"buy": p_id, "price": float(stake)})
            
            if "buy" in buy:
                st.session_state.trade_count += 1
                st.session_state.last_log = f"✅ SUCCESS: {contract_type} on {symbol}"
                return True
        else:
            error_msg = proposal.get('error', {}).get('message', 'Unknown Error')
            st.session_state.last_log = f"❌ REJECTED: {error_msg}"
        
        await api.clear()
    except Exception as e:
        st.session_state.last_log = f"⚠️ SYSTEM ERROR: {str(e)}"
    return False

# --- 3. DATA VAULT ---
DB_FILE = "slimmy_vault_v18.json"
def load_db():
    if os.path.exists(DB_FILE):
        try: return json.load(open(DB_FILE, "r"))
        except: return {}
    return {}

# --- 4. SESSION INITIALIZATION ---
if "db" not in st.session_state: st.session_state.db = load_db()
if "uplink_established" not in st.session_state: st.session_state.uplink_established = False
if "running" not in st.session_state: st.session_state.running = False
if "last_log" not in st.session_state: st.session_state.last_log = "Waiting for Uplink..."
# Accounting Stats
stats = ["live_bal", "session_profit", "session_loss", "wins", "losses", "trade_count"]
for stat in stats:
    if stat not in st.session_state: st.session_state[stat] = 0.0

# --- 5. AUTH GATE & DASHBOARD ---
if not st.session_state.uplink_established:
    # (Simplified login for code focus)
    st.title("KIHATOGATHOGO PRO: UPLINK")
    op_id = st.text_input("OPERATOR_ID")
    sec_key = st.text_input("SECURITY_KEY", type="password")
    if st.button("ESTABLISH UPLINK"):
        if op_id in st.session_state.db and st.session_state.db[op_id]["pass"] == sec_key:
            st.session_state.user_session = st.session_state.db[op_id]
            st.session_state.user_session['email'] = op_id
            st.session_state.uplink_established = True
            st.rerun()
else:
    # Top Nav
    st.markdown(f'<div class="top-nav"><b style="color:#8cc63f;">SLIMMY PRO V21.0</b><span>● {st.session_state.user_session["email"]}</span></div>', unsafe_allow_html=True)

    # Metrics
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("REAL BALANCE", f"${st.session_state.live_bal:,.2f}")
    m2.metric("PROFIT", f"${st.session_state.session_profit:,.2f}")
    m3.metric("LOSS", f"${st.session_state.session_loss:,.2f}")
    m4.metric("TRADES", f"{int(st.session_state.trade_count)}")
    m5.metric("STATUS", "ACTIVE" if st.session_state.running else "IDLE")

    col_main, col_ctrl = st.columns([3, 1])

    with col_main:
        st.components.v1.html('<iframe src="https://tradingview.binary.com/v1.3.10/main.html?symbol=1HZ100V&theme=black" height="500" width="100%"></iframe>', height=500)

    with col_ctrl:
        st.markdown("### ⚙️ ENGINE_CONTROL")
        
        # Required Inputs
        asset_choice = st.selectbox("SELECT ASSET", ["1HZ100V", "1HZ75V", "1HZ50V", "1HZ25V", "R_100", "R_50"])
        stake_amt = st.number_input("STAKE ($)", value=10.0, min_value=0.35)
        max_t = st.number_input("MAX TRADES", value=10)
        sl_limit = st.number_input("STOP LOSS ($)", value=50.0)
        
        st.markdown("---")
        
        # Manual Override Buttons (For testing the Buy Logic)
        col_a, col_b = st.columns(2)
        if col_a.button("🚀 CALL"):
            asyncio.run(execute_deriv_trade(asset_choice, stake_amt, "RISE"))
        if col_b.button("📉 PUT"):
            asyncio.run(execute_deriv_trade(asset_choice, stake_amt, "PUT"))

        # START/STOP Toggle
        if not st.session_state.running:
            if st.button("▶️ START AUTO-BOT"):
                st.session_state.running = True; st.rerun()
        else:
            st.markdown('<div class="stop-btn">', unsafe_allow_html=True)
            if st.button("🛑 STOP AUTO-BOT"):
                st.session_state.running = False; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # 📟 DEBUG LOG WINDOW
        st.markdown("**SYSTEM LOGS**")
        st.markdown(f'<div class="log-text">{st.session_state.last_log}</div>', unsafe_allow_html=True)

    # 🛑 AUTO-SAFETY CHECKS
    if st.session_state.running:
        if st.session_state.trade_count >= max_t or st.session_state.session_loss >= sl_limit:
            st.session_state.running = False
            st.rerun()
