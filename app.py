import streamlit as st
import pandas as pd
import asyncio
import time
import requests
import json
import os
from deriv_api import DerivAPI

# --- 1. UI STYLING (UNTOUCHED) ---
st.set_page_config(page_title="Slimmy Pro V18.5", layout="centered") 
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
    .stDownloadButton button { width: 100%; background-color: #8cc63f !important; color: #041a12 !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. PERMANENT DATABASE (UNTOUCHED) ---
DB_FILE = "slimmy_vault_v18.json"
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try: return json.load(f)
            except: return {}
    return {}
def save_member(email, data):
    db = load_db(); db[email] = data
    with open(DB_FILE, "w") as f: json.dump(db, f)

# --- 3. STATE ---
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

# --- 4. HEADER & EXPORT ---
st.markdown("<div class='bank-header'><h2 style='color:white; margin:0;'>SLIMMY PRO V18.5</h2><p style='color:#8cc63f; margin:0;'>MULTI-LAYER DECISION SYSTEM</p></div>", unsafe_allow_html=True)

if st.session_state.trades:
    df_export = pd.DataFrame(st.session_state.trades)
    csv = df_export.to_csv(index=False).encode('utf-8')
    st.download_button("📥 DOWNLOAD PERFORMANCE LOG", csv, f"Sovereign_Report_{time.strftime('%H%M')}.csv", "text/csv")

total_pl = sum([t['Profit'] for t in st.session_state.trades])
total_t = st.session_state.wins + st.session_state.losses
win_rate = (st.session_state.wins / total_t * 100) if total_t > 0 else 0

c1, c2, c3 = st.columns(3)
with c1: st.metric("💳 BALANCE", f"${st.session_state.live_bal:,.2f}")
with c2: st.metric("💰 SESSION P/L", f"${total_pl:.2f}")
with c3: st.metric("🎯 WIN RATE", f"{win_rate:.0f}%")

st.markdown("---")
status_area = st.empty()
chart_area = st.empty()

# --- 5. SIDEBAR (UNTOUCHED LOGIC) ---
st.sidebar.title("👥 User Center")
choice = st.sidebar.selectbox("Access Mode", ["Login", "Register"])
db = load_db()

if choice == "Register":
    r_email = st.sidebar.text_input("Email")
    r_user = st.sidebar.text_input("Username")
    r_pass = st.sidebar.text_input("Password", type="password")
    r_bot = st.sidebar.text_input("Bot Token")
    r_cid = st.sidebar.text_input("Chat ID")
    r_deriv = st.sidebar.text_input("Deriv Token")
    if st.sidebar.button("Create Account"):
        save_member(r_email, {"name": r_user, "pass": r_pass, "bot": r_bot, "cid": r_cid, "deriv": r_deriv})
        st.sidebar.success("Member Saved!")

elif choice == "Login":
    l_email = st.sidebar.text_input("Email")
    l_pass = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        if l_email in db and db[l_email]["pass"] == l_pass:
            st.session_state.user_session = db[l_email]
            st.sidebar.success(f"✅ Welcome, {db[l_email]['name']}")

# --- STRATEGY CONFIG (IMPROVED) ---
st.sidebar.markdown("---")
st.sidebar.title("⚙️ Sovereign Filters")
risk_pct = st.sidebar.slider("Risk Per Trade (%)", 0.5, 5.0, 2.0) / 100
conf_threshold = st.sidebar.slider("Confluence Threshold (Points)", 5, 10, 7)
max_streak_limit = st.sidebar.number_input("Loss Streak Kill-Switch", value=3)
live_trade = st.sidebar.toggle("🟢 LIVE TRADING ACTIVE")

# Admin Gate (UNTOUCHED)
st.sidebar.markdown("---")
admin_key = st.sidebar.text_input("System Access", type="password")
if admin_key == "SlimmyAdmin2026":
    with st.sidebar.expander("🛠️ ADMIN BACK-END"):
        st.write(f"Total Users: {len(db)}")
        st.dataframe(pd.DataFrame.from_dict(db, orient='index')[['name']])

if st.sidebar.button("🚀 DEPLOY QUANT ENGINE", use_container_width=True):
    u = st.session_state.user_session
    if u and u["deriv"]:
        st.session_state.trades = []; st.session_state.wins = 0; st.session_state.losses = 0; st.session_state.loss_streak = 0
        st.session_state.running = True
    else: st.sidebar.error("Please Login First!")

if st.sidebar.button("🛑 EMERGENCY STOP", use_container_width=True): st.session_state.running = False

# --- 6. QUANT ENGINE (THE DECISION SYSTEM) ---
async def worker():
    u = st.session_state.user_session
    api = DerivAPI(app_id=36544)
    try:
        await api.authorize(u["deriv"])
        status_area.success("🟢 SOVEREIGN SYSTEM RUNNING")
        
        while st.session_state.running:
            # 1. KILL-SWITCH CHECK
            if st.session_state.loss_streak >= max_streak_limit:
                status_area.error("🚨 LOSS STREAK LIMIT REACHED. AUTO-SHUTDOWN.")
                send_tele("⚠️ Bot disabled due to loss streak limit.", u["bot"], u["cid"])
                st.session_state.running = False; break

            # 2. DATA ACQUISITION (Multi-Timeframe)
            ticks = await api.ticks_history({"ticks_history": "1HZ100V", "count": 200, "end": "latest"})
            prices = [float(p) for p in ticks["history"]["prices"]]
            chart_area.line_chart(prices[-50:])
            
            # --- 3. THE SCORING MODEL (Total 10 Points) ---
            score = 0
            
            # A. Trend Alignment (4 Points)
            ma200 = sum(prices[-200:]) / 200 # Higher Timeframe
            ma50 = sum(prices[-50:]) / 50   # Medium Timeframe
            ma10 = sum(prices[-10:]) / 10   # Execution Timeframe
            
            is_bullish = (ma10 > ma50 > ma200)
            is_bearish = (ma10 < ma50 < ma200)
            if is_bullish or is_bearish: score += 4
            
            # B. Momentum RSI Behavior (3 Points)
            deltas = pd.Series(prices).diff()
            gain = (deltas.where(deltas > 0, 0)).rolling(window=14).mean()
            loss = (-deltas.where(deltas < 0, 0)).rolling(window=14).mean()
            rsi_series = 100 - (100 / (1 + (gain/loss)))
            rsi = rsi_series.iloc[-1]
            rsi_delta = rsi - rsi_series.iloc[-3] # RSI Direction (The Vector)
            
            if is_bullish and rsi_delta > 0 and 50 < rsi < 70: score += 3
            if is_bearish and rsi_delta < 0 and 30 < rsi < 50: score += 3
            
            # C. Volatility Check (3 Points)
            volatility = pd.Series(prices[-20:]).std()
            if volatility > 0.15: score += 3 # Filters out flat markets
            
            # --- 4. EXECUTION GATE ---
            if score >= conf_threshold:
                direction = "CALL" if is_bullish else "PUT"
                # Fixed % Position Sizing
                stake = round(st.session_state.live_bal * risk_pct, 2)
                if stake < 1.0: stake = 1.0 # Minimum Deriv Stake
                
                status_area.warning(f"💎 HIGH CONFIDENCE ({score}/10): {direction}")
                
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
                st.session_state.trades.append({"Time": time.strftime("%H:%M:%S"), "Type": direction, "Score": score, "Profit": p_val, "Balance": st.session_state.live_bal})
                
                send_tele(f"📊 Result: {p_val} | Conf: {score}/10 | Streak: {st.session_state.loss_streak}", u["bot"], u["cid"])
                await asyncio.sleep(120) # Hard Cooldown
            else:
                status_area.info(f"⏳ Scanning Market... Confidence: {score}/{conf_threshold}")
            
            await asyncio.sleep(2)
    except Exception as e: st.error(f"Error: {e}")

if st.session_state.running: asyncio.run(worker())
