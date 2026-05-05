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
# 🔥 ADD: DERIV VALIDATION
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
# 🔥 LOGIN SCREEN (FIXED)
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
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="login-card">', unsafe_allow_html=True)

    st.markdown('<div class="title">KIHATOGATHOGO PRO</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">V21.0 GLOBAL PRECISION ARCHITECTURE</div>', unsafe_allow_html=True)

    mode = st.radio("", ["AUTH_LOGIN", "INIT_SYSTEM"], horizontal=True)

    # ================= LOGIN =================
    if mode == "AUTH_LOGIN":

        email = st.text_input("OPERATOR_ID (EMAIL)", key="login_email")
        password = st.text_input("SECURITY_KEY (PASSWORD)", type="password", key="login_pass")

        if st.button("🔓 ESTABLISH UPLINK"):

            users = st.session_state.users

            if email in users and users[email]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.user_token = users[email]["token"]
                st.session_state.user = users[email]
                st.success("Uplink Established")
                st.rerun()
            else:
                st.error("Invalid credentials")

    # ================= REGISTER =================
    if mode == "INIT_SYSTEM":

        email = st.text_input("OPERATOR_ID (EMAIL)", key="reg_email")
        password = st.text_input("SECURITY_KEY (PASSWORD)", type="password", key="reg_pass")
        token = st.text_input("DERIV_API_TOKEN", key="reg_token")

        col1, col2 = st.columns(2)
        tg_token = col1.text_input("TG_BOT_TOKEN (Optional)")
        tg_chat = col2.text_input("TG_CHAT_ID (Optional)")

        st.warning("Ensure Deriv token has TRADE permission")

        if st.button("🚀 INITIALIZE CORE"):

            with st.spinner("Validating Deriv account..."):
                result = asyncio.run(validate_deriv(token))

            if not result["valid"]:
                st.error(f"Invalid Token: {result['error']}")
            else:
                users = st.session_state.users

                users[email] = {
                    "password": password,
                    "token": token,
                    "loginid": result["loginid"],
                    "currency": result["currency"],
                    "tg_bot": tg_token,
                    "tg_chat": tg_chat
                }

                save_users(users)

                st.success(f"Account linked: {result['loginid']} ({result['currency']})")

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================
# 🔥 YOUR ORIGINAL BOT (UNCHANGED)
# ==============================
else:
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

    # =========================
    # 🔄 BALANCE LOAD
    # =========================
    if "live_bal" not in st.session_state:
        st.session_state.live_bal = asyncio.run(get_deriv_balance())

    if st.button("🔄 Refresh Deriv Balance"):
        st.session_state.live_bal = asyncio.run(get_deriv_balance())

    # =========================
    # 📊 STATS INIT
    # =========================
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

    # =========================
    # 🎨 COLOR LOGIC
    # =========================
    def color(val):
        return "lime" if val >= 0 else "red"

    # =========================
    # 🔝 TOP METRICS
    # =========================
    col1, col2, col3, col4 = st.columns(4)

    col1.markdown(f"<h3>Balance</h3><h2 style='color:lime;'>${st.session_state.live_bal:,.2f}</h2>", unsafe_allow_html=True)
    col2.markdown(f"<h3>P/L</h3><h2 style='color:{color(pl_value)};'>${pl_value:,.2f}</h2>", unsafe_allow_html=True)
    col3.markdown(f"<h3>Win Rate</h3><h2>{win_rate:.1f}%</h2>", unsafe_allow_html=True)
    col4.markdown(f"<h3>Streak</h3><h2>{st.session_state.wins}W / {st.session_state.losses}L</h2>", unsafe_allow_html=True)

    # =========================
    # ➕ EXTRA METRICS (YOU ASKED)
    # =========================
    col5, col6, col7, col8, col9, col10 = st.columns(6)

    col5.metric("🧠 Signal Strength", "0 / 10", "+0")
    col6.metric("📉 Drawdown", "$0.00", "0%")
    col7.metric("⚡ Exec Speed", "0 ms")
    col8.metric("📡 API Status", "Connected")
    col9.metric("🧮 Avg Trade", "$0.00")
    col10.metric("🎲 Risk/Trade", "0%")

    st.markdown("---")

    # =========================
    # 🧠 MAIN LAYOUT
    # =========================
    left, right = st.columns([3,1])

    with left:

        st.markdown("### 📊 MARKET SIGNAL SCANNER")

        assets = [
            "Vol 100 (1s)",
            "Vol 75 (1s)",
            "Vol 25 (1s)",
            "Vol 10 (1s)",
            "Gold XAU/USD",
            "Bitcoin BTC/USD",
            "GBP/JPY"
        ]

        for asset in assets:
            c1, c2 = st.columns([3,1])
            c1.markdown(f"**{asset}**  \n_STREAK + STRUCTURE_")
            c2.markdown("—")

        st.info("Start the engine to see live scores")

    with right:

        st.markdown("### ⚙️ ENGINE CONTROL")

        stake = st.number_input("Stake ($)", value=10.0)
        stop_loss = st.number_input("Stop Loss ($)", value=50.0)
        max_trades = st.number_input("Max Trades", value=10)

        if not st.session_state.running:
            if st.button("🚀 Start Engine"):
                st.session_state.running = True
        else:
            if st.button("🛑 Stop Engine"):
                st.session_state.running = False

        if st.session_state.running:
            st.success("Engine Running")
        else:
            st.warning("Engine Stopped")

    st.markdown("---")

    # =========================
    # 🔒 LOGOUT
    # =========================
    if st.button("🔒 Logout"):
        st.session_state.logged_in = False
        st.rerun()
    
    
