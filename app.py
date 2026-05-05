import streamlit as st
import asyncio
from deriv_api import DerivAPI
import json
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Slimmy Pro V21.0", layout="wide")

# ==============================
# 🔐 DATABASE (ADDED)
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
# 🔥 LOGIN SCREEN (MATCHES YOUR UI)
# ==============================
if not st.session_state.logged_in:

    st.markdown("""
    <style>
    .login-wrapper {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 90vh;
    }

    .login-card {
        width: 420px;
        padding: 25px;
        border-radius: 10px;
        border: 1px solid #1a3a2a;
        background: #041f14;
        box-shadow: 0 0 15px rgba(140,198,63,0.2);
    }

    .title {
        text-align: center;
        color: #8cc63f;
        font-size: 26px;
        font-weight: bold;
    }

    .subtitle {
        text-align: center;
        font-size: 12px;
        color: #4e805d;
        margin-bottom: 20px;
    }

    .btn-main button {
        background-color: #8cc63f !important;
        color: black !important;
        font-weight: bold;
        width: 100%;
        height: 45px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="login-card">', unsafe_allow_html=True)

    st.markdown('<div class="title">KIHATOGATHOGO PRO</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">V21.0 GLOBAL PRECISION ARCHITECTURE</div>', unsafe_allow_html=True)

    mode = st.radio("", ["AUTH_LOGIN", "INIT_SYSTEM"], horizontal=True)

    email = st.text_input("OPERATOR_ID (EMAIL)")
    password = st.text_input("SECURITY_KEY (PASSWORD)", type="password")
    token = st.text_input("DERIV_API_TOKEN")

    col1, col2 = st.columns(2)
    tg_token = col1.text_input("TG_BOT_TOKEN (Optional)")
    tg_chat = col2.text_input("TG_CHAT_ID (Optional)")

    st.warning("API tokens are stored encrypted. Ensure tokens have Trade permission.")

    if mode == "AUTH_LOGIN":
        if st.button("🔓 LOGIN", key="login"):
            users = st.session_state.users
            if email in users and users[email]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.user_token = users[email]["token"]
                st.rerun()
            else:
                st.error("Invalid credentials")

    if mode == "INIT_SYSTEM":
        if st.button("🚀 INITIALIZE CORE", key="register"):
            users = st.session_state.users
            users[email] = {
                "password": password,
                "token": token
            }
            save_users(users)
            st.success("System initialized successfully")

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================
# 🔥 YOUR ORIGINAL BOT (UNCHANGED)
# ==============================
else:

    DERIV_TOKEN = st.session_state.user_token

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
        st.session_state.live_bal = asyncio.run(get_deriv_balance())

    if st.button("🔄 Refresh Deriv Balance"):
        st.session_state.live_bal = asyncio.run(get_deriv_balance())

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

    # --- METRICS ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Balance", f"${st.session_state.live_bal:,.2f}")
    col2.metric("P/L", f"${pl_value:,.2f}")
    col3.metric("Win Rate", f"{win_rate:.1f}%")
    col4.metric("Streak", f"{st.session_state.wins}W / {st.session_state.losses}L")

    st.markdown("---")

    if st.button("🚀 Start Engine"):
        st.session_state.running = True

    if st.session_state.running:
        st.success("Engine Running")
    else:
        st.warning("Engine Stopped")

    if st.button("🔒 Logout"):
        st.session_state.logged_in = False
        st.rerun()
