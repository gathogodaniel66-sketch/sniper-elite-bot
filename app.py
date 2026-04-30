import streamlit as st
import pandas as pd
import asyncio
import time
import requests
import json
import os
from deriv_api import DerivAPI

# --- 1. UI STYLING (UNTOUCHED) ---
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

# --- 2. PERMANENT DATA & STATE (UNTOUCHED) ---
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
if "loss_streak" not in st.session_state: st.session_state.loss_streak = 0

def send_tele(msg, token, cid):
    if token and cid:
        try: requests.get(f"https://api.telegram.org/bot{token}/sendMessage?chat_id={cid}&text={msg}")
        except: pass

# --- 3. HEADER (UNTOUCHED) ---
st.markdown("<div class='bank-header'><h2 style='color:white; margin:0;'>SLIMMY PRO V18.5</h2><p style='color:#8cc63f; margin:0;'>CONFLUENCE SCORING SYSTEM</p></div>", unsafe_allow_html=True)

total_pl = sum([t['Profit'] for t in st.session_state.trades])
total_t = st.session_state.wins + st.session_state.losses
win_rate = (st.session_state.wins / total_t * 100) if total_t > 0 else 0

c1, c2, c3 = st.columns(3)
with c1: st.metric("💳 BALANCE", f"${st.session_state.live_bal:,.2f}")
with c2: st.metric("💰 SESSION P/L", f"${total_pl:.2f}")
with c3: st.metric("🎯 WIN RATE", f"{win_rate:.0f}%")

st.markdown("---")

if st.session_state.trades:
    st.markdown("### 📥 Export Session Data")
    report_df = pd.DataFrame(st.session_state.trades)
    csv = report_df.to_csv(index=False).encode('utf-8')
    st.download_button(label="DOWNLOAD TRADE LOG (CSV)", data=csv, file_name=f"Slimmy_Report_{time.strftime('%H%M')}.csv", mime='text/csv')

st.markdown("### 📈 Round Analysis")
if st.session_state.trades:
    st.table(pd.DataFrame(st.session_state.trades).tail(5))
else:
    st.info("No trade data available yet.")

# --- 4. SIDEBAR & USER CENTER (UNTOUCHED) ---
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

# --- 5. RISK & ENGINE (UPGRADED BASED ON YOUR NOTES) ---
u = st.session_state.user_session
v_bot, v_cid, v_deriv = (u["bot"], u["cid"], u["deriv"]) if u else ("", "", "")

st.sidebar.markdown("---")
risk_pct = st.sidebar.slider("Risk Per Trade (%)", 0.5, 5.0, 2.0) / 100
conf_threshold = st.sidebar.slider("Min Confidence Score", 5, 10, 7)
max_loss_streak = st.sidebar.number_input("Loss Streak Kill-Switch", value=3)
live_trade = st.sidebar.toggle("🟢 LIVE TRADING ACTIVE")

st.sidebar.markdown("---")
admin = st.sidebar.text_input("System Access", type="password")
if admin == "SlimmyAdmin2026":
    st.sidebar.info(f"Total Members: {len(db)}")

if st.sidebar.button("🚀 DEPLOY QUANT ENGINE", use_container_width=True):
    if v_deriv:
        st.session_state.trades = []; st.session_state.wins = 0; st.session_state.losses = 0; st.session_state.loss_streak = 0
        st.session_state.running = True
    else: st.sidebar.error("Login first!")

if st.sidebar.button("🛑 KILL SWITCH", use_container_width=True): st.session_state.running = False

status_area = st.empty()
chart_area = st.empty()

# --- 6. THE SCORING ENGINE ---
async def worker():
    api = DerivAPI(app_id=36544)
    try:
        await api.authorize(v_deriv)
        status_area.success("🟢 QUANT ENGINE ACTIVE")
        while st.session_state.running:
            # Check Auto-Disable
            if st.session_state.loss_streak >= max_loss_streak:
                status_area.error("🚨 CRITICAL LOSS STREAK - AUTO-STOPPED")
                st.session_state.running = False; break

            # Multi-Timeframe Data (200 Ticks)
            ticks = await api.ticks_history({"ticks_history": "1HZ100V", "count": 200, "end": "latest"})
            prices = [float(p) for p in ticks["history"]["prices"]]
            chart_area.line_chart(prices[-50:])
            
            # --- 🧠 CONFLUENCE SCORING ---
            score = 0
            ma200 = sum(prices[-200:]) / 200 # Global Trend
            ma50 = sum(prices[-50:]) / 50   # Local Trend
            
            # 1. Trend Alignment (4 Points)
            is_bull = (prices[-1] > ma50 > ma200)
            is_bear = (prices[-1] < ma50 < ma200)
            if is_bull or is_bear: score += 4
            
            # 2. RSI Momentum & Direction (3 Points)
            deltas = pd.Series(prices).diff()
            gain = (deltas.where(deltas > 0, 0)).rolling(14).mean()
            loss = (-deltas.where(deltas < 0, 0)).rolling(14).mean()
            rsi_series = 100 - (100 / (1 + (gain/loss)))
            rsi = rsi_series.iloc[-1]
            rsi_dir = rsi - rsi_series.iloc[-3] # Directional movement
            
            if is_bull and rsi_dir > 0 and 50 < rsi < 68: score += 3
            if is_bear and rsi_dir < 0 and 32 < rsi < 50: score += 3
            
            # 3. Volatility Expansion (3 Points)
            vol = pd.Series(prices[-20:]).std()
            if vol > 0.15: score += 3 # Minimum volatility threshold
            
            # --- ⚡ EXECUTION GATE ---
            if score >= conf_threshold:
                direction = "CALL" if is_bull else "PUT"
                # Fixed Fractional Risk sizing
                stake = max(1.0, round(st.session_state.live_bal * risk_pct, 2))
                
                status_area.warning(f"💎 HIGH CONFIDENCE: {score}/10")
                if live_trade:
                    await api.buy({"buy": 1, "price": stake, "parameters": {"amount": stake, "basis": "stake", "contract_type": direction, "currency": "USD", "duration": 5, "duration_unit": "t", "symbol": "1HZ100V"}})
                
                await asyncio.sleep(8)
                history = await api.profit_table({"profit_table": 1, "limit": 1})
                res = history['profit_table']['transactions'][0]
                p_val = float(res['sell_price']) - float(res['buy_price'])
                
                if p_val > 0:
                    st.session_state.wins += 1; st.session_state.loss_streak = 0
                else:
                    st.session_state.losses += 1; st.session_state.loss_streak += 1
                
                bal_upd = await api.balance(); st.session_state.live_bal = bal_upd['balance']['balance']
                st.session_state.trades.append({
                    "Time": time.strftime("%H:%M:%S"), "Type": direction, 
                    "Conf": f"{score}/10", "Profit": p_val, "Balance": st.session_state.live_bal
                })
                send_tele(f"💰 Result: {p_val} | Conf: {score}/10", v_bot, v_cid)
                await asyncio.sleep(120) # Forced Cooldown
            
            await asyncio.sleep(1)
    except Exception as e: st.error(f"Error: {e}")

if st.session_state.running: asyncio.run(worker())
