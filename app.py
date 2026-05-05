import streamlit as st
import asyncio
from deriv_api import DerivAPI
import json
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Slimmy Pro V21.0", layout="wide")

# ==============================
# 🔐 ADD: USER DATABASE (NEW)
# ==============================
DB_FILE = "users_db.json"

def load_users():
    if os.path.exists(DB_FILE):
        return json.load(open(DB_FILE))
    return {}

def save_users(data):
    json.dump(data, open(DB_FILE, "w"))

if "users" not in st.session_state:
    st.session_state.users = load_users()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ==============================
# 🔐 LOGIN / REGISTER (NEW ONLY)
# ==============================
if not st.session_state.logged_in:

    st.markdown("""
    <style>
    .auth-box {
        width: 420px;
        margin: auto;
        padding: 25px;
        border: 1px solid #1a3a2a;
        border-radius: 10px;
        background: #041f14;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<h2 style='text-align:center;color:#8cc63f;'>KIHATOGATHOGO PRO</h2>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["LOGIN", "REGISTER"])

    # LOGIN
    with tab1:
        st.markdown('<div class="auth-box">', unsafe_allow_html=True)

        email = st.text_input("Operator ID (Email)")
        password = st.text_input("Security Key", type="password")

        if st.button("LOGIN"):
            users = st.session_state.users
            if email in users and users[email]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.user_token = users[email]["token"]
                st.success("Access Granted")
                st.rerun()
            else:
                st.error("Invalid credentials")

        st.markdown('</div>', unsafe_allow_html=True)

    # REGISTER
    with tab2:
        st.markdown('<div class="auth-box">', unsafe_allow_html=True)

        new_email = st.text_input("Email")
        new_pass = st.text_input("Password", type="password")
        deriv_token = st.text_input("Deriv API Token")

        if st.button("CREATE ACCOUNT"):
            users = st.session_state.users

            if new_email in users:
                st.error("User already exists")
            else:
                users[new_email] = {
                    "password": new_pass,
                    "token": deriv_token
                }
                save_users(users)
                st.success("Account created")

        st.markdown('</div>', unsafe_allow_html=True)

# ==============================
# 🔥 YOUR ORIGINAL CODE (100% INTACT)
# ==============================
else:

    # 🔥 USE USER TOKEN INSTEAD OF HARDCODED
    DERIV_TOKEN = st.session_state.user_token

    # ==============================
    # 🔥 YOUR ORIGINAL CODE STARTS HERE (UNCHANGED)
    # ==============================

    async def get_deriv_balance():
        try:
            api = DerivAPI(app_id=1089)
            await api.authorize(DERIV_TOKEN)
            res = await api.balance()
            await api.clear()
            return float(res["balance"]["balance"])
        except:
            return 0.0

    if "live_bal" not in st.session_state:
        try:
            st.session_state.live_bal = asyncio.run(get_deriv_balance())
        except:
            st.session_state.live_bal = 0.0

    if st.button("🔄 Refresh Deriv Balance"):
        try:
            st.session_state.live_bal = asyncio.run(get_deriv_balance())
        except:
            st.error("Failed to fetch balance")

    if "session_profit" not in st.session_state:
        st.session_state.session_profit = 0.0
    if "session_loss" not in st.session_state:
        st.session_state.session_loss = 0.0
    if "wins" not in st.session_state:
        st.session_state.wins = 0
    if "losses" not in st.session_state:
        st.session_state.losses = 0
    if "trade_count" not in st.session_state:
        st.session_state.trade_count = 0
    if "running" not in st.session_state:
        st.session_state.running = False

    pl_value = st.session_state.session_profit - st.session_state.session_loss
    win_rate = (st.session_state.wins / max(1, st.session_state.trade_count)) * 100

    st.markdown("""
    <style>
    .stApp { background-color: #020d08; color: #8cc63f; }

    div[data-testid="stMetric"] {
        background: #05140d;
        border: 1px solid #1a3a2a;
        padding: 12px;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0 0 10px rgba(140,198,63,0.15);
    }

    div[data-testid="stMetric"] > div:nth-child(2) {
        color: #00ff88 !important;
        font-size: 26px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"### 👤 {st.session_state.user_email}")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Balance", f"${st.session_state.live_bal:,.2f}")
    col2.metric("P/L", f"${pl_value:,.2f}")
    col3.metric("Win Rate", f"{win_rate:.1f}%")
    col4.metric("Streak", f"{st.session_state.wins}W / {st.session_state.losses}L")

    st.markdown("---")

    # 🔥 KEEP YOUR FULL DASHBOARD BELOW (UNCHANGED)

    # --- LOGOUT (ADDED ONLY) ---
    if st.button("🔒 Logout"):
        st.session_state.logged_in = False
        st.rerun()
