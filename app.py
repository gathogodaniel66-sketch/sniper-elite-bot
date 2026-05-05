import streamlit as st
import pandas as pd
import time
import requests
import json
import os
import asyncio
from deriv_api import DerivAPI

# --- CONFIG ---
DB_FILE = "slimmy_vault_v18.json"

# --- STYLING ---
st.set_page_config(page_title="KihatoGathogo Pro V21.0", layout="wide") 
st.markdown("""
<style>
.stApp { background-color: #020d08; color: #8cc63f; }
.top-nav { display: flex; justify-content: space-between; padding: 10px; background: #05140d; }
.stButton>button { background-color: #8cc63f !important; color: black !important; }
.stop-btn>div>button { background-color: red !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- DB FUNCTIONS ---
def load_db():
    if os.path.exists(DB_FILE):
        try:
            return json.load(open(DB_FILE, "r"))
        except:
            return {}
    return {}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- SESSION INIT ---
if "db" not in st.session_state:
    st.session_state.db = load_db()

if "uplink_established" not in st.session_state:
    st.session_state.uplink_established = False

if "running" not in st.session_state:
    st.session_state.running = False

if "bot_running" not in st.session_state:
    st.session_state.bot_running = False

stats = ["live_bal","session_profit","session_loss","wins","losses","trade_count"]
for s in stats:
    if s not in st.session_state:
        st.session_state[s] = 0.0

# --- TRADE FUNCTION ---
async def execute_deriv_trade(symbol, stake, contract_type):
    user = st.session_state.user_session
    try:
        api = DerivAPI(app_id=1089)
        await api.authorize(user["deriv"])

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

        if "proposal" in proposal:
            buy = await api.buy({
                "buy": proposal["proposal"]["id"],
                "price": float(stake)
            })

            if "buy" in buy:
                st.session_state.trade_count += 1
                return True
    except Exception as e:
        st.error(str(e))
    return False

# --- AUTO BOT ---
async def auto_trading_engine(symbol, stake, max_trades, sl_limit):
    while st.session_state.running:
        try:
            if st.session_state.trade_count >= max_trades:
                st.warning("Max trades reached")
                st.session_state.running = False
                break

            if st.session_state.session_loss >= sl_limit:
                st.error("Stop loss hit")
                st.session_state.running = False
                break

            direction = "RISE" if int(time.time()) % 2 == 0 else "FALL"

            result = await execute_deriv_trade(symbol, stake, direction)

            if result:
                st.session_state.wins += 1
                st.session_state.session_profit += stake * 0.8
            else:
                st.session_state.losses += 1
                st.session_state.session_loss += stake

            await asyncio.sleep(60)

        except Exception as e:
            st.error(f"Auto error: {e}")
            break

# --- LOGIN / REGISTER ---
if not st.session_state.uplink_established:

    st.title("🔐 KIHATO GATHOGO PRO LOGIN")

    tab1, tab2 = st.tabs(["LOGIN", "REGISTER"])

    # --- LOGIN ---
    with tab1:
        login_email = st.text_input("Email")
        login_pass = st.text_input("Password", type="password")

        if st.button("LOGIN"):
            db = st.session_state.db

            if login_email in db:
                if db[login_email]["pass"] == login_pass:
                    st.session_state.user_session = db[login_email]
                    st.session_state.user_session["email"] = login_email
                    st.session_state.uplink_established = True
                    st.success("Login successful")
                    st.rerun()
                else:
                    st.error("Wrong password")
            else:
                st.error("User not found")

    # --- REGISTER ---
    with tab2:
        reg_email = st.text_input("New Email")
        reg_pass = st.text_input("New Password", type="password")
        deriv_token = st.text_input("Deriv API Token")

        if st.button("REGISTER"):
            db = st.session_state.db

            if reg_email in db:
                st.warning("User already exists")
            else:
                db[reg_email] = {
                    "pass": reg_pass,
                    "deriv": deriv_token
                }
                save_db(db)
                st.success("Account created! Go to login.")

# --- DASHBOARD ---
else:
    st.markdown(f"### Welcome {st.session_state.user_session['email']}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Profit", st.session_state.session_profit)
    col2.metric("Loss", st.session_state.session_loss)
    col3.metric("Trades", int(st.session_state.trade_count))

    asset = st.selectbox("Asset", ["1HZ100V","R_100"])
    stake = st.number_input("Stake", value=1.0)
    max_trades = st.number_input("Max Trades", value=10)
    sl = st.number_input("Stop Loss", value=10.0)

    colA, colB = st.columns(2)

    if colA.button("CALL"):
        asyncio.run(execute_deriv_trade(asset, stake, "RISE"))

    if colB.button("PUT"):
        asyncio.run(execute_deriv_trade(asset, stake, "FALL"))

    if not st.session_state.running:
        if st.button("START BOT"):
            st.session_state.running = True
            asyncio.run(auto_trading_engine(asset, stake, max_trades, sl))
    else:
        if st.button("STOP BOT"):
            st.session_state.running = False
            st.rerun()
