import streamlit as st
import pandas as pd
import asyncio
import time
import requests
import json
import os
from deriv_api import DerivAPI

# --- 1. UI STYLING ---
st.set_page_config(page_title="Slimmy Pro V21.0", layout="wide") 
st.markdown("""
    <style>
    .main { background-color: #041a12; }
    .bank-header {
        background: linear-gradient(135deg, #072b1d 0%, #155e46 100%);
        padding: 25px; border-radius: 20px;
        text-align: center; border-bottom: 3px solid #8cc63f;
        margin-bottom: 20px;
    }
    div[data-testid="stMetric"] {
        background: rgba(140, 198, 63, 0.1);
        border: 1px solid #8cc63f;
        border-radius: 15px; padding: 15px;
    }
    .stDownloadButton button {
        width: 100%;
        background-color: #8cc63f !important;
        color: #041a12 !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. PERMANENT DATA & STATE ---
DB_FILE = "slimmy_vault_v18.json"
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}
def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f)

if "db" not in st.session_state: st.session_state.db = load_db()
if "trades" not in st.session_state: st.session_state.trades = []
if "running" not in st.session_state: st.session_state.running = False
if "wins" not in st.session_state: st.session_state.wins = 0
if "losses" not in st.session_state: st.session_state.losses = 0
if "live_bal" not in st.session_state: st.session_state.live_bal = 0.0 
if "user_session" not in st.session_state: st.session_state.user_session = None

def send_tele(msg, token, cid):
    if token and cid:
        try: requests.get(f"https://api.telegram.org/bot{token}/sendMessage?chat_id={cid}&text={msg}")
        except: pass

# --- 3. HEADER & METRICS ---
st.markdown("<div class='bank-header'><h2 style='color:white; margin:0;'>SLIMMY PRO V21.0</h2><p style='color:#8cc63f; margin:0;'>GLOBAL PRECISION ARCHITECTURE</p></div>", unsafe_allow_html=True)

total_pl = round(sum([t['Profit'] for t in st.session_state.trades]), 2)
total_t = st.session_state.wins + st.session_state.losses
win_rate = (st.session_state.wins / total_t * 100) if total_t > 0 else 0

m1, m2, m3 = st.columns(3)
with m1: st.metric("💳 BALANCE", f"${round(st.session_state.live_bal, 2):,.2f}")
with m2: st.metric("💰 SESSION P/L", f"${total_pl:.2f}")
with m3: st.metric("🎯 WIN RATE", f"{win_rate:.0f}%")

st.markdown("---")

# --- 4. 📈 LIVE MARKET DASHBOARD ---
st.markdown("### 📈 Live Market Dashboard")
col_main_1, col_main_2 = st.columns(2)
with col_main_1:
    st.write("**Gold (XAU/USD)**")
    st.components.v1.html('<iframe src="https://s.tradingview.com/widgetembed/?symbol=OANDA%3AXAUUSD&interval=1&theme=dark" height="350" width="100%"></iframe>', height=350)
with col_main_2:
    st.write("**Volatility 100 (1s) Index**")
    st.components.v1.html('<iframe src="https://tradingview.binary.com/v1.3.10/main.html?symbol=1HZ100V&theme=black" height="350" width="100%"></iframe>', height=350)

# --- 5. SIDEBAR & CONNECTION CENTER ---
st.sidebar.title("👥 User Center")

# --- NEW: DETECT OAUTH TOKENS FROM URL ---
query_params = st.query_params
if "token1" in query_params:
    st.session_state.magic_token = query_params["token1"]
    st.sidebar.success("✅ Secure Gateway Active")

choice = st.sidebar.selectbox("Action", ["Login", "Register", "Secure Gateway"])

if choice == "Login":
    l_email = st.sidebar.text_input("Email")
    l_pass = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Unlock Dashboard"):
        if l_email in st.session_state.db and st.session_state.db[l_email]["pass"] == l_pass:
            st.session_state.user_session = st.session_state.db[l_email]
            st.sidebar.success("✅ Access Accepted.")
            time.sleep(1)
            st.rerun()
        else:
            st.sidebar.error("❌ Access Declined.")

elif choice == "Register":
    r_email = st.sidebar.text_input("New Email")
    r_pass = st.sidebar.text_input("New Password", type="password")
    r_bot = st.sidebar.text_input("Telegram Bot Token")
    r_cid = st.sidebar.text_input("Telegram Chat ID")
    r_deriv = st.sidebar.text_input("Deriv API Token (Optional)")
    if st.sidebar.button("Create Account"):
        st.session_state.db[r_email] = {"pass": r_pass, "bot": r_bot, "cid": r_cid, "deriv": r_deriv}
        save_db(st.session_state.db)
        st.sidebar.success("✅ Account Created!")

elif choice == "Secure Gateway":
    st.sidebar.write("Can't find your token? Click below to log in securely.")
    MY_APP_ID = "1089" # Standard test ID
    auth_url = f"https://oauth.deriv.com/oauth2/authorize?app_id={MY_APP_ID}&l=en&brand=deriv"
    st.sidebar.markdown(f'''
        <a href="{auth_url}" target="_self" style="text-decoration:none;">
            <div style="background-color:#8cc63f; color:#041a12; text-align:center; 
            padding:12px; border-radius:8px; font-weight:bold; cursor:pointer;">
                🚀 CONNECT VIA DERIV OAUTH
            </div>
        </a>
    ''', unsafe_allow_html=True)

# --- 6. SOVEREIGN ENGINE ---
u = st.session_state.user_session
# Priority: Magic Token > Manual Token
v_deriv = st.session_state.get("magic_token") or (u["deriv"] if u else "")
v_bot, v_cid = (u["bot"], u["cid"]) if u else ("", "")

st.sidebar.markdown("---")
base_stake = st.sidebar.number_input("Fixed Stake ($)", value=1.0)
max_loss = st.sidebar.number_input("Hard Stop Loss ($)", value=15.0)
live_trade = st.sidebar.toggle("🟢 LIVE TRADING ACTIVE")

if st.sidebar.button("🚀 DEPLOY SNIPER", use_container_width=True):
    if v_deriv:
        st.session_state.trades = []; st.session_state.wins = 0; st.session_state.losses = 0; st.session_state.running = True
    else: st.sidebar.error("⚠️ Connection Required: Use Login or Secure Gateway.")

if st.sidebar.button("🛑 KILL SWITCH", use_container_width=True): st.session_state.running = False

status_area = st.empty()
chart_area = st.empty()

async def worker():
    api = DerivAPI(app_id=1089)
    try:
        auth = await api.authorize(v_deriv) 
        st.session_state.live_bal = float(auth['authorize']['balance']) 
        status_area.success(f"🟢 ENGINE ACTIVE | Account: {auth['authorize']['loginid']}")
        
        while st.session_state.running:
            # Update balance
            bal_upd = await api.balance()
            st.session_state.live_bal = float(bal_upd['balance']['balance'])

            # Market Data
            ticks = await api.ticks_history({"ticks_history": "1HZ100V", "count": 100, "end": "latest"})
            prices = [float(p) for p in ticks["history"]["prices"]]
            chart_area.line_chart(prices[-50:])

            # --- PRECISION SCORING (STRICT SCORE 9) ---
            ma200, ma50 = sum(prices[-100:])/100, sum(prices[-50:])/50
            is_bull = (prices[-1] > ma50 > ma200)
            is_bear = (prices[-1] < ma50 < ma200)
            
            deltas = pd.Series(prices).diff()
            gain, loss = deltas.where(deltas > 0, 0).rolling(14).mean(), (-deltas.where(deltas < 0, 0)).rolling(14).mean()
            rsi = 100 - (100 / (1 + (gain/loss).iloc[-1])) if loss.iloc[-1] != 0 else 50
            
            score = 0
            if is_bull or is_bear: score += 4
            if (is_bull and 55 <= rsi <= 65) or (is_bear and 35 <= rsi <= 45): score += 2
            if (is_bull and prices[-1] > prices[-2] > prices[-3]) or (is_bear and prices[-1] < prices[-2] < prices[-3]): score += 2
            if 0.12 < pd.Series(prices[-20:]).std() < 0.50: score += 2

            if score >= 9:
                direction = "CALL" if is_bull else "PUT"
                status_area.warning(f"💎 ELITE SIGNAL DETECTED ({score}/10)")
                if live_trade:
                    await api.buy({"buy": 1, "price": base_stake, "parameters": {"amount": base_stake, "basis": "stake", "contract_type": direction, "currency": "USD", "duration": 5, "duration_unit": "t", "symbol": "1HZ100V"}})
                    
                    await asyncio.sleep(8)
                    history = await api.profit_table({"profit_table": 1, "limit": 1})
                    res = history['profit_table']['transactions'][0]
                    p_val = round(float(res['sell_price']) - float(res['buy_price']), 2)
                    
                    if p_val > 0: st.session_state.wins += 1
                    else: st.session_state.losses += 1
                    
                    st.session_state.trades.append({"Time": time.strftime("%H:%M:%S"), "Type": direction, "Profit": p_val, "Score": f"{score}/10"})
                    send_tele(f"📊 {direction} | Profit: {p_val}", v_bot, v_cid)
                    await asyncio.sleep(90)
            await asyncio.sleep(1)
    except Exception as e: status_area.error(f"Engine Alert: {e}")

if st.session_state.running:
    asyncio.run(worker())
