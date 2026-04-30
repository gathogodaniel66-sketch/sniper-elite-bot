import streamlit as st
import pandas as pd
import asyncio
import time
import requests
import json
import os
from deriv_api import DerivAPI

# --- 1. UI STYLING (KEEPING YOUR EXACT LOOK) ---
st.set_page_config(page_title="Slimmy Pro V18.6", layout="centered") 
st.markdown("""
    <style>
    .main { background-color: #041a12; }
    .bank-header {
        background: linear-gradient(135deg, #0a3d2e 0%, #155e46 100%);
        padding: 20px; border-radius: 0 0 25px 25px;
        text-align: center; border-bottom: 2px solid #8cc63f;
        margin-bottom: 15px;
    }
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(140, 198, 63, 0.2);
        border-radius: 12px; padding: 12px; margin-bottom: -15px;
    }
    div[data-testid="stMetricValue"] { color: #8cc63f !important; font-size: 24px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. TELEGRAM FUNCTION ---
def send_tele(msg, token, cid):
    if token and cid:
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={cid}&text={msg}"
            requests.get(url)
        except: pass

# --- 3. STATE & DATABASE ---
if "trades" not in st.session_state: st.session_state.trades = []
if "running" not in st.session_state: st.session_state.running = False
if "wins" not in st.session_state: st.session_state.wins = 0
if "losses" not in st.session_state: st.session_state.losses = 0
if "live_bal" not in st.session_state: st.session_state.live_bal = 0.0
if "user_db" not in st.session_state: st.session_state.user_db = {} 
if "active_user" not in st.session_state: st.session_state.active_user = None

# --- 4. HEADER ---
st.markdown("<div class='bank-header'><h2 style='color:white; margin:0;'>SLIMMY PRO</h2><p style='color:#8cc63f; margin:0; font-size:12px;'>V18.6 SOVEREIGN ENGINE + ORIGINAL UI</p></div>", unsafe_allow_html=True)

# Math
total_pl = sum([t['Profit'] for t in st.session_state.trades])
total_t = st.session_state.wins + st.session_state.losses
win_rate = (st.session_state.wins / total_t * 100) if total_t > 0 else 0

# --- 5. DASHBOARD ---
st.metric("💳 BALANCE", f"${st.session_state.live_bal:,.2f}")
st.metric("💰 SESSION P/L", f"${total_pl:.2f}")
st.metric("🎯 WIN RATE", f"{win_rate:.0f}%")
st.metric("✅ WINS", st.session_state.wins)
st.metric("❌ LOSSES", st.session_state.losses)

st.markdown("---")
if st.session_state.trades:
    df_export = pd.DataFrame(st.session_state.trades)
    csv = df_export.to_csv(index=False).encode('utf-8')
    st.download_button("📥 DOWNLOAD PERFORMANCE LOG", csv, f"Slimmy_Report.csv", "text/csv")

status_area = st.empty()
chart_area = st.empty()

# --- 6. SIDEBAR & USER CENTER (REVERTED TO YOUR PREFERRED FLOW) ---
st.sidebar.title("👥 User Center")
menu = st.sidebar.radio("Select Action", ["Login", "Register", "Forgot Password"])

v_bot = ""
v_cid = ""
v_deriv = ""

if menu == "Register":
    st.sidebar.subheader("Create Account")
    new_user = st.sidebar.text_input("Username")
    new_email = st.sidebar.text_input("Email")
    new_pass = st.sidebar.text_input("Password", type="password")
    reg_bot = st.sidebar.text_input("Telegram Bot Token")
    reg_cid = st.sidebar.text_input("Telegram Chat ID")
    reg_deriv = st.sidebar.text_input("Deriv Token")
    if st.sidebar.button("💾 Register Account"):
        st.session_state.user_db[new_user] = {"email": new_email, "pass": new_pass, "bot": reg_bot, "cid": reg_cid, "deriv": reg_deriv}
        st.sidebar.success("✅ Registered!")

elif menu == "Login":
    st.sidebar.subheader("Account Login")
    u_name = st.sidebar.text_input("Username")
    u_pass = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("🔓 Login Now"):
        if u_name in st.session_state.user_db and st.session_state.user_db[u_name]["pass"] == u_pass:
            st.session_state.active_user = st.session_state.user_db[u_name]
            st.sidebar.success(f"✅ Welcome {u_name}!")
        else: st.sidebar.error("❌ Wrong details")

elif menu == "Forgot Password":
    st.sidebar.subheader("Recovery")
    rec_u = st.sidebar.text_input("Username")
    rec_e = st.sidebar.text_input("Email")
    if st.sidebar.button("🔑 Send to Telegram"):
        if rec_u in st.session_state.user_db and st.session_state.user_db[rec_u]["email"] == rec_e:
            send_tele(f"Your password is: {st.session_state.user_db[rec_u]['pass']}", st.session_state.user_db[rec_u]['bot'], st.session_state.user_db[rec_u]['cid'])
            st.sidebar.success("✅ Sent!")

# --- AUTO-LOAD LOADED DATA ---
if st.session_state.active_user:
    v_bot = st.session_state.active_user["bot"]
    v_cid = st.session_state.active_user["cid"]
    v_deriv = st.session_state.active_user["deriv"]

st.sidebar.markdown("---")
st.sidebar.title("📲 Connection Details")
tele_token = st.sidebar.text_input("Bot Token", value=v_bot, type="password")
tele_id = st.sidebar.text_input("Chat ID", value=v_cid)
deriv_token = st.sidebar.text_input("Deriv Token", value=v_deriv, type="password")

st.sidebar.markdown("---")
st.sidebar.title("🏦 Risk & Trade")
risk_pct = st.sidebar.slider("Risk Per Trade (%)", 1.0, 5.0, 2.0) / 100
max_loss = st.sidebar.number_input("Stop Loss Limit ($)", value=50.0)
live_trade = st.sidebar.toggle("🟢 ACTIVATE LIVE TRADING")

# Admin Gate
st.sidebar.markdown("---")
admin_key = st.sidebar.text_input("System Access", type="password")
if admin_key == "SlimmyAdmin2026": 
    with st.sidebar.expander("🛠️ OWNER BACK-END"):
        st.write(f"📊 Total Members: {len(st.session_state.user_db)}")

if st.sidebar.button("🚀 DEPLOY (START FRESH)", use_container_width=True):
    if deriv_token: 
        st.session_state.trades = []
        st.session_state.wins = 0; st.session_state.losses = 0
        st.session_state.running = True
    else: st.sidebar.error("Please Login first!")

if st.sidebar.button("🛑 STOP SESSION", use_container_width=True):
    st.session_state.running = False

# --- 7. ENGINE (THE ADVANCED SCORING SYSTEM) ---
async def worker():
    api = DerivAPI(app_id=36544)
    try:
        await api.authorize(deriv_token)
        status_area.success("🟢 SOVEREIGN ENGINE ACTIVE")
        while st.session_state.running:
            # Multi-layer data
            ticks = await api.ticks_history({"ticks_history": "1HZ100V", "count": 200, "end": "latest"})
            prices = [float(p) for p in ticks["history"]["prices"]]
            chart_area.line_chart(prices[-50:])
            
            # --- SCORING SYSTEM ---
            score = 0
            ma200 = sum(prices[-200:]) / 200
            ma50 = sum(prices[-50:]) / 50
            
            # Trend Layer
            is_bull = (prices[-1] > ma50 > ma200)
            is_bear = (prices[-1] < ma50 < ma200)
            if is_bull or is_bear: score += 4
            
            # Momentum Layer
            deltas = pd.Series(prices).diff()
            gain = (deltas.where(deltas > 0, 0)).rolling(window=14).mean()
            loss = (-deltas.where(deltas < 0, 0)).rolling(window=14).mean()
            rsi = 100 - (100 / (1 + (gain/loss).iloc[-1]))
            if (is_bull and 50 < rsi < 70) or (is_bear and 30 < rsi < 50): score += 3
            
            # Volatility Layer
            vol = pd.Series(prices[-20:]).std()
            if vol > 0.18: score += 3
            
            # EXECUTION
            if score >= 7:
                trade_type = "CALL" if is_bull else "PUT"
                stake = round(st.session_state.live_bal * risk_pct, 2)
                if stake < 1.0: stake = 1.0
                
                if live_trade:
                    await api.buy({"buy": 1, "price": stake, "parameters": {"amount": stake, "basis": "stake", "contract_type": trade_type, "currency": "USD", "duration": 5, "duration_unit": "t", "symbol": "1HZ100V"}})
                
                await asyncio.sleep(8)
                history = await api.profit_table({"profit_table": 1, "limit": 1})
                res = history['profit_table']['transactions'][0]
                p_val = float(res['sell_price']) - float(res['buy_price'])
                
                if p_val > 0: st.session_state.wins += 1
                else: st.session_state.losses += 1
                
                bal_upd = await api.balance(); st.session_state.live_bal = bal_upd['balance']['balance']
                st.session_state.trades.append({"Time": time.strftime("%H:%M:%S"), "Type": trade_type, "Score": score, "Profit": p_val, "Balance": st.session_state.live_bal})
                send_tele(f"💰 Result: {p_val} | Score: {score}/10", tele_token, tele_id)
                await asyncio.sleep(120)
            
            await asyncio.sleep(1)
    except Exception as e: st.error(f"Error: {e}")

if st.session_state.running: asyncio.run(worker())
