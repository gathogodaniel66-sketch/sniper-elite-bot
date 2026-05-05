import streamlit as st
import asyncio
from deriv_api import DerivAPI
import json
import os
import random
import requests

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
# TELEGRAM
# ==============================
def send_telegram(msg):
    try:
        token = st.session_state.get("tg_token")
        chat_id = st.session_state.get("tg_chat")

        if token and chat_id:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            requests.post(url, data={
                "chat_id": chat_id,
                "text": msg
            })
    except:
        pass

# ==============================
# DERIV VALIDATION
# ==============================
async def validate_deriv(token):
    try:
        api = DerivAPI(app_id=1089)
        await api.authorize(token)
        await api.clear()
        return {"valid": True}
    except:
        return {"valid": False}

# ==============================
# LOGIN / REGISTER
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
                st.session_state.tg_token = users[email].get("tg_token")
                st.session_state.tg_chat = users[email].get("tg_chat")
                st.rerun()
            else:
                st.error("Invalid login")

    if mode == "INIT_SYSTEM":
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        token = st.text_input("Deriv API Token")
        tg_token = st.text_input("Telegram Bot Token (optional)")
        tg_chat = st.text_input("Telegram Chat ID (optional)")

        if st.button("REGISTER"):
            result = asyncio.run(validate_deriv(token))

            if result["valid"]:
                users = st.session_state.users
                users[email] = {
                    "password": password,
                    "token": token,
                    "tg_token": tg_token,
                    "tg_chat": tg_chat
                }
                save_users(users)
                st.success("Account created")
            else:
                st.error("Invalid Deriv token")

# ==============================
# DASHBOARD + TRADING ENGINE
# ==============================
else:

    DERIV_TOKEN = st.session_state.user_token

    # =========================
    # GET BALANCE
    # =========================
    async def get_balance():
        try:
            api = DerivAPI(app_id=1089)
            await api.authorize(DERIV_TOKEN)
            res = await api.balance()
            await api.clear()
            return float(res["balance"]["balance"])
        except:
            return 0.0

    # =========================
    # EXECUTE TRADE (REAL RESULT)
    # =========================
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

            buy = await api.buy({"buy": pid, "price": stake})
            contract_id = buy["buy"]["contract_id"]

            # wait for contract result
            await asyncio.sleep(65)

            result = await api.proposal_open_contract({
                "proposal_open_contract": 1,
                "contract_id": contract_id
            })

            await api.clear()

            profit = result["proposal_open_contract"]["profit"]

            return profit

        except Exception as e:
            st.error(e)
            return 0

    # =========================
    # INIT STATE
    # =========================
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
    # REFRESH BALANCE
    # =========================
    if st.button("🔄 Refresh Balance"):
        st.session_state.balance = asyncio.run(get_balance())

    # =========================
    # METRICS
    # =========================
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Balance", f"${st.session_state.balance:.2f}")
    col2.metric("Trades", st.session_state.trades)
    col3.metric("Wins", st.session_state.wins)
    col4.metric("Losses", st.session_state.losses)

    col5, col6, col7, col8, col9, col10 = st.columns(6)

    col5.metric("Signal", "0/10")
    col6.metric("Drawdown", "0")
    col7.metric("Speed", "0ms")
    col8.metric("API", "Connected")
    col9.metric("Avg Trade", "0")
    col10.metric("Risk", "0%")

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
    # AUTO TRADING ENGINE
    # =========================
    if st.session_state.running:

        signal = random.choice(["CALL", "PUT"])

        profit = asyncio.run(execute_trade("R_100", stake, signal))

        st.session_state.trades += 1

        if profit > 0:
            st.session_state.wins += 1
        else:
            st.session_state.losses += 1

        # update balance
        st.session_state.balance = asyncio.run(get_balance())

        # telegram alert
        send_telegram(f"{signal} | Profit: {profit}")

        st.success(f"Trade {signal} → Profit: {profit}")

    # =========================
    # LOGOUT
    # =========================
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
