import streamlit as st
import pandas as pd
import asyncio
import time
import requests
import json
import os
from deriv_api import DerivAPI

# --- 1. UI STYLING ---
st.set_page_config(page_title="Slimmy Pro V18.1", layout="centered") 
st.markdown("""
    <style>
    .main { background-color: #041a12; }
    .bank-header {
        background: linear-gradient(135deg, #072b1d 0%, #155e46 100%);
        padding: 25px; border-radius: 0 0 30px 30px;
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
        with open(DB_FILE, "r") as f: return json.load(f)
    return {}
def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f)

if "trades" not in st.session_state: st.session_state.trades = []
if "running" not in st.session_state: st.session_state.running = False
if "wins" not in st.session_state: st.session_state.wins = 0
if "losses" not in st.session_state: st.session_state.losses = 0
if "live_bal" not in st.session_state: st.session_state.live_bal = 0.0
if "user_session" not in st.session_state: st.session_state.user_session = None
if "current_stake" not in st.session_state: st.session_state.current_stake = 0.0

def send_tele(msg, token, cid):
    if token and cid:
        try: requests.get(f"https://api.telegram.org/bot{token}/sendMessage?chat_id={cid}&text={msg}")
        except: pass

# --- 3. HEADER ---
st.markdown("<div class='bank-header'><h2 style='color:white; margin:0;'>SLIMMY PRO V18.1</h2><p style='color:#8cc63f; margin:0;'>PERFORMANCE TRACKING ACTIVE</p></div>", unsafe_allow_html=True)

total_pl = sum([t['Profit'] for t in st.session_state.trades])
total_t = st.session_state.wins + st.session_state.losses
win_rate = (st.session_state.wins / total_t * 100) if total_t > 0 else 0

c1, c2, c3 = st.columns(3)
with c1: st.metric("💳 BALANCE", f"${st.session_state.live_bal:,.2f}")
with c2: st.metric("💰 SESSION P/L", f"${total_pl:.2f}")
with c3: st.metric("🎯 WIN RATE", f"{win_rate:.0f}%")

st.markdown("---")

# --- 📊 PERFORMANCE EXPORT (NEW) ---
if st.session_state.trades:
    st.markdown("### 📥 Export Session Data")
    report_df = pd.DataFrame(st.session_state.trades)
    csv = report_df.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label="DOWNLOAD TRADE LOG (CSV)",
        data=csv,
        file_name=f"Slimmy_Pro_Report_{time.strftime('%Y%m%d_%H%M')}.csv",
        mime='text/csv',
    )

st.markdown("### 📈 Round Analysis")
if st.session_state.trades:
    df_analysis = pd.DataFrame(st.session_state.trades)
    st.table(df_analysis.tail(5)) # Show last 5 trades
else:
    st.info("No trade data available yet. Start the bot to generate records.")

# --- 4. SIDEBAR & USER CENTER ---
st.sidebar.title("👥 User Center")
choice = st.sidebar.selectbox("Action", ["Login", "Register", "Recovery"])
db = load_db()

if choice == "Register":
    r_email = st.sidebar.text_input("Email")
    r_pass = st.sidebar.text_input("Password", type="password")
    r_bot = st.sidebar.text_input("Bot Token")
    r_cid = st.sidebar.text_input("Chat ID")
    r_deriv = st.sidebar.text_input("Deriv Token")
    if st.sidebar.button("Create Pro Account"):
        db[r_email] = {"pass": r_pass, "bot": r_bot, "cid": r_cid, "deriv": r_deriv}
        save_db(db); st.sidebar.success("Done! Login now.")

elif choice == "Login":
    l_email = st.sidebar.text_input("Email")
    l_pass = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Unlock Dashboard"):
        if l_email in db and db[l_email]["pass"] == l_pass:
            st.session_state.user_session = db[l_email]
            st.sidebar.success("✅ Access Granted")

# --- 5. RISK & ENGINE ---
u = st.session_state.user_session
v_bot, v_cid, v_deriv = (u["bot"], u["cid"], u["deriv"]) if u else ("", "", "")

st.sidebar.markdown("---")
base_stake = st.sidebar.number_input("Base Stake ($)", value=2.0)
martingale = st.sidebar.number_input("Recovery Multiplier", value=2.2)
max_loss = st.sidebar.number_input("Hard Stop Loss ($)", value=100.0)
live_trade = st.sidebar.toggle("🟢 LIVE TRADING ACTIVE")

# Back-End Access
st.sidebar.markdown("---")
admin = st.sidebar.text_input("System Access", type="password")
if admin == "SlimmyAdmin2026":
    st.sidebar.info(f"Total Members: {len(db)}")

if st.sidebar.button("🚀 DEPLOY SNIPER", use_container_width=True):
    if v_deriv:
        st.session_state.trades = []; st.session_state.wins = 0; st.session_state.losses = 0
        st.session_state.current_stake = base_stake
        st.session_state.running = True
    else: st.sidebar.error("Login first!")

if st.sidebar.button("🛑 KILL SWITCH", use_container_width=True): st.session_state.running = False

status_area = st.empty()
chart_area = st.empty()

async def worker():
    api = DerivAPI(app_id=36544)
    try:
        await api.authorize(v_deriv)
        status_area.success("🟢 ENGINE CONNECTED")
        while st.session_state.running:
            if total_pl <= -max_loss:
                send_tele("🛑 STOP LOSS HIT.", v_bot, v_cid)
                st.session_state.running = False; break

            ticks = await api.ticks_history({"ticks_history": "1HZ100V", "count": 50, "end": "latest"})
            prices = [float(p) for p in ticks["history"]["prices"]]
            chart_area.line_chart(prices)
            
            # Indicators
            deltas = pd.Series(prices).diff()
            gain = (deltas.where(deltas > 0, 0)).rolling(window=14).mean()
            loss = (-deltas.where(deltas < 0, 0)).rolling(window=14).mean()
            rsi = 100 - (100 / (1 + (gain/loss).iloc[-1]))
            ma_short = sum(prices[-10:])/10
            
            # SNIPER RECOVERY LOGIC
            is_recovery = st.session_state.current_stake > base_stake
            if not is_recovery:
                do_call = (prices[-1] > ma_short) and (rsi < 65) and (rsi > 50)
                do_put = (prices[-1] < ma_short) and (rsi > 35) and (rsi < 50)
            else:
                do_call = (rsi < 30) 
                do_put = (rsi > 70)

            if do_call or do_put:
                trade_type = "CALL" if do_call else "PUT"
                if live_trade:
                    await api.buy({"buy": 1, "price": st.session_state.current_stake, "parameters": {"amount": st.session_state.current_stake, "basis": "stake", "contract_type": trade_type, "currency": "USD", "duration": 5, "duration_unit": "t", "symbol": "1HZ100V"}})
                
                await asyncio.sleep(8)
                history = await api.profit_table({"profit_table": 1, "limit": 1})
                res = history['profit_table']['transactions'][0]
                p_val = float(res['sell_price']) - float(res['buy_price'])
                
                if p_val > 0:
                    st.session_state.wins += 1; st.session_state.current_stake = base_stake
                else:
                    st.session_state.losses += 1; st.session_state.current_stake = round(st.session_state.current_stake * martingale, 2)
                
                bal_upd = await api.balance(); st.session_state.live_bal = bal_upd['balance']['balance']
                st.session_state.trades.append({
                    "Time": time.strftime("%H:%M:%S"), 
                    "Type": trade_type, 
                    "Stake": st.session_state.current_stake, 
                    "Profit": p_val,
                    "Balance": st.session_state.live_bal
                })
                send_tele(f"💰 {'WIN' if p_val > 0 else 'LOSS'} (${p_val:.2f})", v_bot, v_cid)
                await asyncio.sleep(45)
            await asyncio.sleep(1)
    except Exception as e: st.error(f"Error: {e}")

if st.session_state.running: asyncio.run(worker())
