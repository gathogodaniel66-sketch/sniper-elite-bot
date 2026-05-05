import streamlit as st
import asyncio
from deriv_api import DerivAPI
import json
import os
import random

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
# 🔐 LOGIN / REGISTER
# ==============================
if not st.session_state.logged_in:

    st.markdown("## KIHATOGATHOGO PRO")

    mode = st.radio("", ["AUTH_LOGIN", "INIT_SYSTEM"], horizontal=True)

    if mode == "AUTH_LOGIN":
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("🔓 LOGIN"):
            users = st.session_state.users
            if email in users and users[email]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.user_token = users[email]["token"]
                st.rerun()
            else:
                st.error("Invalid credentials")

    if mode == "INIT_SYSTEM":
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        token = st.text_input("Deriv API Token")

        if st.button("🚀 REGISTER"):
            result = asyncio.run(validate_deriv(token))

            if not result["valid"]:
                st.error(result["error"])
            else:
                users = st.session_state.users
                users[email] = {
                    "password": password,
                    "token": token
                }
                save_users(users)
                st.success("Account Created")

# ==============================
# 🔥 DASHBOARD + TRADING ENGINE
# ==============================
else:

    DERIV_TOKEN = st.session_state.user_token

    # =========================
    # 🔄 GET BALANCE
    # =========================
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
    # 🔥 EXECUTE TRADE
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

            await api.buy({"buy": pid, "price": stake})
            await api.clear()
            return True

        except Exception as e:
            st.error(f"Trade error: {e}")
            return False

    # =========================
    # 📊 INIT STATES
    # =========================
    if "live_bal" not in st.session_state:
        st.session_state.live_bal = asyncio.run(get_deriv_balance())

    if "running" not in st.session_state:
        st.session_state.running = False

    if "wins" not in st.session_state:
        st.session_state.wins = 0

    if "losses" not in st.session_state:
        st.session_state.losses = 0

    if "trade_count" not in st.session_state:
        st.session_state.trade_count = 0

    # =========================
    # 🔄 REFRESH
    # =========================
    if st.button("🔄 Refresh Balance"):
        st.session_state.live_bal = asyncio.run(get_deriv_balance())

    # =========================
    # 📊 METRICS
    # =========================
    col1, col2, col3 = st.columns(3)

    col1.metric("Balance", f"${st.session_state.live_bal:,.2f}")
    col2.metric("Trades", st.session_state.trade_count)
    col3.metric("Wins", st.session_state.wins)

    st.markdown("---")

    # =========================
    # ⚙️ CONTROL PANEL
    # =========================
    stake = st.number_input("Stake ($)", value=1.0)

    if not st.session_state.running:
        if st.button("🚀 Start Engine"):
            st.session_state.running = True
    else:
        if st.button("🛑 Stop Engine"):
            st.session_state.running = False

    # =========================
    # 🤖 AUTO TRADING ENGINE
    # =========================
    if st.session_state.running:

        st.success("Engine Running...")

        # simple signal (replace later)
        signal = random.choice(["CALL", "PUT"])

        result = asyncio.run(
            execute_trade("R_100", stake, signal)
        )

        if result:
            st.session_state.trade_count += 1

            if signal == "CALL":
                st.session_state.wins += 1
            else:
                st.session_state.losses += 1

        st.write(f"Last Trade: {signal}")

    # =========================
    # 🔒 LOGOUT
    # =========================
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
