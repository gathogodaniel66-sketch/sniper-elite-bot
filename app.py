import streamlit as st
import asyncio
from deriv_api import DerivAPI
import json
import os

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
            "balance": float(balance["balance"]["balance"]),
            "currency": balance["balance"]["currency"],
            "loginid": auth["authorize"]["loginid"]
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}

# ==============================
# 🔐 LOGIN / REGISTER UI
# ==============================
if not st.session_state.logged_in:

    st.markdown("""
    <style>
    .card {
        width:420px;
        margin:auto;
        padding:25px;
        background:#041f14;
        border:1px solid #1a3a2a;
        border-radius:10px;
    }
    .title {
        text-align:center;
        color:#8cc63f;
        font-size:26px;
        font-weight:bold;
    }
    .btn button {
        background:#8cc63f !important;
        color:black !important;
        font-weight:bold;
        width:100%;
        height:45px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='title'>KIHATOGATHOGO PRO</div>", unsafe_allow_html=True)
    st.markdown("<center style='color:#4e805d;'>V21.0 GLOBAL PRECISION ARCHITECTURE</center><br>", unsafe_allow_html=True)

    mode = st.radio("", ["AUTH_LOGIN", "INIT_SYSTEM"], horizontal=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)

    # ================= LOGIN =================
    if mode == "AUTH_LOGIN":

        email = st.text_input("OPERATOR_ID (EMAIL)")
        password = st.text_input("SECURITY_KEY", type="password")

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

        email = st.text_input("OPERATOR_ID (EMAIL)")
        password = st.text_input("SECURITY_KEY", type="password")
        token = st.text_input("DERIV_API_TOKEN")

        col1, col2 = st.columns(2)
        tg_bot = col1.text_input("TG_BOT_TOKEN", placeholder="Optional")
        tg_chat = col2.text_input("TG_CHAT_ID", placeholder="Optional")

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
                    "currency": result["currency"]
                }

                save_users(users)

                st.success(f"Account linked: {result['loginid']} ({result['currency']})")

    st.markdown("</div>", unsafe_allow_html=True)

# ==============================
# 🔥 DASHBOARD (UNCHANGED)
# ==============================
else:

    token = st.session_state.user_token

    async def get_balance():
        api = DerivAPI(app_id=1089)
        await api.authorize(token)
        res = await api.balance()
        await api.clear()
        return float(res["balance"]["balance"])

    if "live_bal" not in st.session_state:
        st.session_state.live_bal = asyncio.run(get_balance())

    if st.button("🔄 Refresh Balance"):
        st.session_state.live_bal = asyncio.run(get_balance())

    st.markdown(f"### 👤 {st.session_state.user_email}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Balance", f"${st.session_state.live_bal:,.2f}")
    col2.metric("Account", st.session_state.user.get("loginid","N/A"))
    col3.metric("Currency", st.session_state.user.get("currency","USD"))

    st.markdown("---")

    if st.button("🚀 Start Engine"):
        st.session_state.running = True

    if st.session_state.get("running"):
        st.success("Engine Running")
    else:
        st.warning("Engine Idle")

    if st.button("🔒 Logout"):
        st.session_state.logged_in = False
        st.rerun()
