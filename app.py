import streamlit as st
import asyncio
from deriv_api import DerivAPI
import json
import os
import random

st.set_page_config(page_title="Slimmy Pro V21.0", layout="wide")

# ==============================
# DATABASE
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
# DERIV VALIDATION
# ==============================
async def validate_deriv(token):
    try:
        api = DerivAPI(app_id=1089)
        auth = await api.authorize(token)
        await api.clear()
        return {"valid": True}
    except:
        return {"valid": False}

# ==============================
# LOGIN
# ==============================
if not st.session_state.logged_in:

    st.title("KIHATOGATHOGO PRO")

    mode = st.radio("", ["AUTH_LOGIN", "INIT_SYSTEM"], horizontal=True)

    if mode == "AUTH_LOGIN":
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("LOGIN"):
            users = st.session_state.users
            if email in users and users[email]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.user_token = users[email]["token"]
                st.rerun()
            else:
                st.error("Invalid login")

    if mode == "INIT_SYSTEM":
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        token = st.text_input("Deriv Token")

        if st.button("REGISTER"):
            result = asyncio.run(validate_deriv(token))
            if result["valid"]:
                users = st.session_state.users
                users[email] = {"password": password, "token": token}
                save_users(users)
                st.success("Account created")
            else:
                st.error("Invalid token")

# ==============================
# DASHBOARD + BOT
# ==============================
else:

    DERIV_TOKEN = st.session_state.user_token

    async def get_balance():
        api = DerivAPI(app_id=1089)
        await api.authorize(DERIV_TOKEN)
        res = await api.balance()
        await api.clear()
        return float(res["balance"]["balance"])

    async def execute_trade(symbol, stake, direction):
        try:
            api = DerivAPI(app_id=1089)
            await api.authorize(DERIV_TOKEN)

            proposal = await api.proposal({
                "proposal": 1,
                "amount": stake,
                "basis": "stake",
                "contract_type": direction,
                "currency": "USD",
                "duration": 1,
                "duration_unit": "m",
                "symbol": symbol
            })

            pid = proposal["proposal"]["id"]

            await api.buy({"buy": pid, "price": stake})
            await api.clear()
            return True
        except Exception as e:
            st.error(e)
            return False

    if "balance" not in st.session_state:
        st.session_state.balance = asyncio.run(get_balance())

    if "running" not in st.session_state:
        st.session_state.running = False

    if "wins" not in st.session_state:
        st.session_state.wins = 0

    if "losses" not in st.session_state:
        st.session_state.losses = 0

    if "trades" not in st.session_state:
        st.session_state.trades = 0

    # =========================
    # TOP METRICS
    # =========================
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Balance", f"${st.session_state.balance:.2f}")
    c2.metric("Trades", st.session_state.trades)
    c3.metric("Wins", st.session_state.wins)
    c4.metric("Losses", st.session_state.losses)

    # =========================
    # EXTRA METRICS
    # =========================
    c5, c6, c7, c8, c9, c10 = st.columns(6)
    c5.metric("Signal", "0/10")
    c6.metric("Drawdown", "0")
    c7.metric("Speed", "0ms")
    c8.metric("API", "Connected")
    c9.metric("Avg Trade", "0")
    c10.metric("Risk", "0%")

    st.markdown("---")

    left, right = st.columns([3,1])

    # =========================
    # SCANNER
    # =========================
    with left:
        st.subheader("Market Scanner")

        assets = ["Vol 100", "Vol 75", "Vol 25", "Gold", "BTC", "GBPJPY"]

        for a in assets:
            st.write(f"{a} → waiting...")

    # =========================
    # CONTROL PANEL
    # =========================
    with right:
        stake = st.number_input("Stake", value=1.0)

        if not st.session_state.running:
            if st.button("Start Engine"):
                st.session_state.running = True
        else:
            if st.button("Stop Engine"):
                st.session_state.running = False

        if st.session_state.running:
            st.success("Running")
        else:
            st.warning("Stopped")

    # =========================
    # AUTO TRADING
    # =========================
    if st.session_state.running:

        signal = random.choice(["CALL", "PUT"])

        result = asyncio.run(execute_trade("R_100", stake, signal))

        if result:
            st.session_state.trades += 1

            if signal == "CALL":
                st.session_state.wins += 1
            else:
                st.session_state.losses += 1

        st.write(f"Trade: {signal}")

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
