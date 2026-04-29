import streamlit as st
import pandas as pd
import asyncio
import time
from deriv_api import DerivAPI

# --- 1. FINTECH UI STYLING ---
st.set_page_config(page_title="Slimmy Sniper Pro", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #041a12; }
    .bank-header {
        background: linear-gradient(135deg, #0a3d2e 0%, #155e46 100%);
        padding: 20px; border-radius: 0 0 25px 25px;
        text-align: center; border-bottom: 3px solid #8cc63f;
    }
    .icon-circle {
        background: #ffffff; width: 50px; height: 50px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        margin: 0 auto 5px auto; box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(140, 198, 63, 0.2);
        border-radius: 15px; padding: 10px; text-align: center;
    }
    div[data-testid="stMetricValue"] { color: #8cc63f !important; font-size: 20px !important; }
    .signal-alert {
        background: #112b21; border-radius: 12px; padding: 12px;
        text-align: center; border: 1px solid #8cc63f; margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. STATE ---
if "trades" not in st.session_state: st.session_state.trades = []
if "running" not in st.session_state: st.session_state.running = False
if "wins" not in st.session_state: st.session_state.wins = 0
if "losses" not in st.session_state: st.session_state.losses = 0

# --- 3. SIDEBAR ---
st.sidebar.markdown("<h2 style='color:#8cc63f;'>🏦 WALLET</h2>", unsafe_allow_html=True)
token = st.sidebar.text_input("Deriv Token", type="password")
stake = st.sidebar.number_input("Stake ($)", value=2.0)
target = st.sidebar.number_input("Profit Goal ($)", value=50.0)
live_trade = st.sidebar.toggle("🟢 ACTIVATE LIVE TRADING", value=False)

if st.sidebar.button("🚀 DEPLOY SYSTEM", use_container_width=True): st.session_state.running = True
if st.sidebar.button("🛑 STOP SYSTEM", use_container_width=True): st.session_state.running = False

# --- 4. HEADER ---
st.markdown("<div class='bank-header'><h2 style='color:white; margin:0;'>SLIMMY SNIPER PRO</h2><p style='color:#8cc63f; margin:0;'>FINTECH TRADING ENGINE</p></div>", unsafe_allow_html=True)

# Math
total_pl = sum([t['Profit'] for t in st.session_state.trades])
total_trades = st.session_state.wins + st.session_state.losses
win_rate = (st.session_state.wins / total_trades * 100) if total_trades > 0 else 0

# --- 5. GRID ICONS ---
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("<div class='icon-circle'>💰</div>", unsafe_allow_html=True)
    st.metric("Net P/L", f"${total_pl:.2f}")
with col2:
    st.markdown("<div class='icon-circle'>🎯</div>", unsafe_allow_html=True)
    st.metric("Accuracy", f"{win_rate:.0f}%")
with col3:
    st.markdown("<div class='icon-circle'>❌</div>", unsafe_allow_html=True)
    st.metric("Losses", st.session_state.losses)

# --- 6. LIVE AREA ---
status_area = st.empty()
chart_area = st.empty()
st.markdown("<p style='color:#8cc63f; font-weight:bold;'>Transaction Statement</p>", unsafe_allow_html=True)
log_table = st.empty()

async def run_system():
    api = DerivAPI(app_id=36544)
    try:
        await api.authorize(token)
        while st.session_state.running:
            ticks = await api.ticks_history({"ticks_history": "1HZ100V", "count": 50, "end": "latest"})
            prices = [float(p) for p in ticks["history"]["prices"]]
            last_p, sma = prices[-1], sum(prices[-20:]) / 20
            momentum = prices[-1] - prices[-10]
            
            chart_area.line_chart(prices)
            
            # --- THE TRUTH LOGIC ---
            is_up = prices[-1] > prices[-2] > prices[-3]
            is_down = prices[-1] < prices[-2] < prices[-3]

            if (last_p > sma and momentum > 1.8 and is_up) or (last_p < sma and momentum < -1.8 and is_down):
                trade_type = "CALL" if last_p > sma else "PUT"
                entry_p = last_p # SAVE ENTRY PRICE
                status_area.markdown(f"<div class='signal-alert' style='color:#ffc107;'>🟡 PENDING {trade_type}...</div>", unsafe_allow_html=True)
                
                if live_trade:
                    await api.buy({"buy": 1, "price": stake, "parameters": {"amount": stake, "basis": "stake", "contract_type": trade_type, "currency": "USD", "duration": 5, "duration_unit": "t", "symbol": "1HZ100V"}})
                
                await asyncio.sleep(7) # WAIT FOR TRADE TO FINISH
                
                # VERIFY RESULT
                res = await api.ticks_history({"ticks_history": "1HZ100V", "count": 1, "end": "latest"})
                exit_p = float(res["history"]["prices"][0])
                
                # Check if we actually won or lost
                won = (trade_type == "CALL" and exit_p > entry_p) or (trade_type == "PUT" and exit_p < entry_p)
                
                if won:
                    st.session_state.wins += 1
                    p_val = stake * 0.95
                    status_area.markdown("<div class='signal-alert' style='color:#8cc63f;'>✅ TRANSACTION SUCCESSFUL</div>", unsafe_allow_html=True)
                else:
                    st.session_state.losses += 1
                    p_val = -stake # SUBTRACT FULL STAKE ON LOSS
                    status_area.markdown("<div class='signal-alert' style='color:#ff4b4b;'>❌ TRANSACTION FAILED</div>", unsafe_allow_html=True)
                
                st.session_state.trades.append({"Time": time.strftime("%H:%M"), "Action": trade_type, "Profit": p_val})
                await asyncio.sleep(5)
            else:
                status_area.markdown("<div class='signal-alert' style='color:#58a6ff;'>📡 SCANNING...</div>", unsafe_allow_html=True)

            if st.session_state.trades:
                log_table.dataframe(pd.DataFrame(st.session_state.trades).tail(5), use_container_width=True)
            await asyncio.sleep(1)
            
    except Exception as e:
        st.error(f"Bank Error: {e}")

if st.session_state.running:
    asyncio.run(run_system())
