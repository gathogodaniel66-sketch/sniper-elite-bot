import streamlit as st
import asyncio
from deriv_api import DerivAPI
import json
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Slimmy Pro V21.0", layout="wide")

# ==============================
# 🔐 DATABASE
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
# 🔥 DERIV VALIDATION
# ==============================
async def validate_deriv(token):
    try:
        api = DerivAPI(app_id=1089)
        auth = await api.authorize(token)
        balance = await api.balance()
        await api.clear()

        return {
            "valid": True,
            "loginid": auth["authorize"]["loginid"],
            "currency": balance["balance"]["currency"]
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}

# ==============================
# 🔐 LOGIN SCREEN
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
    }
    .title {
        text-align: center;
        color: #8cc63f;
        font-size: 26px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="login-card">', unsafe_allow_html=True)

    st.markdown('<div class="title">KIHATOGATHOGO PRO</div>', unsafe_allow_html=True)

    mode = st.radio("", ["AUTH_LOGIN", "INIT_SYSTEM"], horizontal=True)

    # LOGIN
    if mode == "AUTH_LOGIN":
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("🔓 ESTABLISH UPLINK"):
            users = st.session_state.users

            if email in users and users[email]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.user_token = users[email]["token"]
                st.session_state.user = users[email]
                st.rerun()
            else:
                st.error("Invalid credentials")

    # REGISTER
    if mode == "INIT_SYSTEM":
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        token = st.text_input("Deriv API Token")

        if st.button("🚀 INITIALIZE CORE"):
            result = asyncio.run(validate_deriv(token))

            if not result["valid"]:
                st.error(result["error"])
            else:
                users = st.session_state.users
                users[email] = {
                    "password": password,
                    "token": token,
                    "loginid": result["loginid"],
                    "currency": result["currency"]
                }
                save_users(users)
                st.success("Account Created")

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================
# 🔥 DASHBOARD (UPGRADED)
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

    pl = st.session_state.session_profit - st.session_state.session_loss
    win_rate = (st.session_state.wins / max(1, st.session_state.trade_count)) * 100

    def color(v):
        return "lime" if v >= 0 else "red"

    # ===== TOP METRICS =====
    c1, c2, c3, c4 = st.columns(4)

    c1.markdown(f"### Balance\n<h2 style='color:lime;'>${st.session_state.live_bal:,.2f}</h2>", unsafe_allow_html=True)
    c2.markdown(f"### P/L\n<h2 style='color:{color(pl)};'>${pl:,.2f}</h2>", unsafe_allow_html=True)
    c3.markdown(f"### Win Rate\n<h2>{win_rate:.1f}%</h2>", unsafe_allow_html=True)
    c4.markdown(f"### Streak\n<h2>{st.session_state.wins}W / {st.session_state.losses}L</h2>", unsafe_allow_html=True)

    # ===== EXTRA METRICS =====
    c5, c6, c7, c8, c9, c10 = st.columns(6)

    c5.metric("Signal Strength", "0 / 10")
    c6.metric("Drawdown", "$0.00")
    c7.metric("Exec Speed", "0 ms")
    c8.metric("API Status", "Connected")
    c9.metric("Avg Trade", "$0.00")
    c10.metric("Risk/Trade", "0%")

    st.markdown("---")

    # ===== MAIN LAYOUT =====
    left, right = st.columns([3,1])

    with left:
        st.markdown("## MARKET SIGNAL SCANNER")

        assets = ["Vol 100", "Vol 75", "Vol 25", "Gold", "BTC", "GBPJPY"]

        for a in assets:
            st.write(f"{a} — waiting...")

        if st.button("▶️ Start Engine"):
            st.session_state.running = True

    with right:
        st.markdown("## ENGINE CONTROL")

        st.number_input("Stake", value=10.0)
        st.number_input("Stop Loss", value=50.0)

        if st.session_state.running:
            st.success("Engine Running")
        else:
            st.warning("Engine Stopped")

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
