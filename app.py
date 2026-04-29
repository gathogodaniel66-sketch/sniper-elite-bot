import streamlit as st
import pandas as pd
import asyncio
import time
from deriv_api import DerivAPI

# --- 1. THE GRID & BANKING UI ---
st.set_page_config(page_title="Slimmy Sniper Pro", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #041a12; }
    
    /* Header Area */
    .bank-header {
        background: linear-gradient(135deg, #0a3d2e 0%, #155e46 100%);
        padding: 15px; border-radius: 0 0 20px 20px;
        text-align: center; border-bottom: 2px solid #8cc63f;
    }

    /* FORCE HORIZONTAL GRID */
    [data-testid="column"] {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }

    .icon-circle {
        background: #ffffff; width: 45px; height: 45px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3); font-size: 20px;
        margin-bottom: 5px;
    }

    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(140, 198, 63, 0.2);
        border-radius: 12px; padding: 8px; width: 100%;
    }
    div[data-testid="stMetricValue"] { color: #8cc63f !important; font-size: 18px !important; }
    div[data-testid="stMetricLabel"] { font-size: 11px !important; color: #8b949e !important; }
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
live_trade = st.sidebar.toggle("🟢 LIVE TRADING", value=False)

if st.sidebar.button("🚀 DEPLOY SYSTEM", use_container_width=True):
    if token: st.session_state.running = True
    else: st.sidebar.error("Please enter a Token first!")

if st.sidebar.button("🛑 STOP SYSTEM", use_container_width=True):
    st.session_state.running = False

# --- 4. HEADER ---
st.markdown("<div class='bank-header'><h3 style='color:white; margin:0;'>SLIMMY SNIPER PRO</h3><p style='color:#8cc63f; margin:0; font-size:12px;'>V9.2 FINTECH ENGINE</p></div>", unsafe_allow_html=True)

# Math
total_pl = sum([t['Profit'] for t in st.session_state.trades])
total_t = st.session_state.wins + st.session_state.losses
win_rate = (st.session_state.wins / total_t * 100) if total_t > 0 else 0

# --- 5. THE HORIZONTAL GRID ---
st.write("") # Spacer
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("<div class='icon-circle'>💰</div>", unsafe_allow_html=True)
    st.metric("NET P/L", f"${total_pl:.2f}")
with c2:
    st.markdown("<div class='icon-circle'>🎯</div>", unsafe_allow_html=True)
    st.metric("ACCURACY", f"{win_rate:.0f}%")
with c3:
    st.markdown("<div class='icon-circle'>❌</div>", unsafe_allow_html=True)
    st.metric("LOSSES", st.session_state.losses)

# --- 6. LIVE FEED ---
status_area = st.empty()
chart_area = st.empty()
st.markdown("<p style='color:#8cc63f; font-weight:bold; font-size:14px; margin-bottom:5px;'>Statement</p>", unsafe_allow_html=True)
log_table = st.empty()

async def run_system():
    # Stable connection attempt
    try:
        api = DerivAPI(app_id=36544) 
        await api.authorize(token)
        while st.session_state.running:
            ticks = await api.ticks_history({"ticks_history": "1HZ100V", "count": 50, "end": "latest"})
            prices = [float(p) for p in ticks["history"]["prices"]]
            last_p, sma = prices[-1], sum(prices[-20:]) / 20
            momentum = prices[-1] - prices[-10]
            
            chart_area.line_chart(prices)
            
            # ACCURACY LOGIC
            is_up = prices[-1] > prices[-2] > prices[-3]
            is_down = prices[-1] < prices[-2] < prices[-3]

            if (last_p > sma and momentum > 1.8 and is_up) or (last_p < sma and momentum < -1.8 and is_down):
                trade_type = "CALL" if last_p > sma else "PUT"
                entry_p = last_p
                status_area.markdown(f"<div style='background:#112b21; padding:10px; border-radius:10px; border:1px solid #ffc107; text-align:center; color:#ffc107;'>🟡 PENDING {trade_type}...</div>", unsafe_allow_html=True)
                
                if live_trade:
                    await api.buy({"buy": 1, "price": stake, "parameters": {"amount": stake, "basis": "stake", "contract_type": trade_type, "currency": "USD", "duration": 5, "duration_unit": "t", "symbol": "1HZ100V"}})
                
                await asyncio.sleep(7)
                
                res = await api.ticks_history({"ticks_history": "1HZ100V", "count": 1, "end": "latest"})
                exit_p = float(res["history"]["prices"][0])
                won = (trade_type == "CALL" and exit_p > entry_p) or (trade_type == "PUT" and exit_p < entry_p)
                
                if won:
                    st.session_state.wins += 1
                    p_val = stake * 0.95
                    status_area.markdown("<div style='background:#112b21; padding:10px; border-radius:10px; border:1px solid #8cc63f; text-align:center; color:#8cc63f;'>✅ SUCCESSFUL</div>", unsafe_allow_html=True)
                else:
                    st.session_state.losses += 1
                    p_val = -stake
                    status_area.markdown("<div style='background:#112b21; padding:10px; border-radius:10px; border:1px solid #ff4b4b; text-align:center; color:#ff4b4b;'>❌ FAILED</div>", unsafe_allow_html=True)
                
                st.session_state.trades.append({"Time": time.strftime("%H:%M"), "Type": trade_type, "Profit": p_val})
                await asyncio.sleep(5)
            else:
                status_area.markdown("<div style='background:#112b21; padding:10px; border-radius:10px; border:1px solid #58a6ff; text-align:center; color:#58a6ff;'>📡 SCANNING...</div>", unsafe_allow_html=True)

            if st.session_state.trades:
                log_table.dataframe(pd.DataFrame(st.session_state.trades).tail(5), use_container_width=True)
            await asyncio.sleep(1)
            
    except Exception as e:
        st.error(f"⚠️ Authorization Error: {e}")
        st.session_state.running = False

if st.session_state.running:
    asyncio.run(run_system())
            
