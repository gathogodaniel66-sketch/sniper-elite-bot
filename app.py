import streamlit as st
import asyncio
from deriv_api import DerivAPI

# --- PAGE CONFIG ---
st.set_page_config(page_title="Slimmy Pro V21.0", layout="wide")

# ==============================
# 🔥 ADD: DERIV API TOKEN
# ==============================
DERIV_TOKEN = "PASTE_YOUR_TOKEN_HERE"

# ==============================
# 🔥 ADD: GET LIVE BALANCE
# ==============================
async def get_deriv_balance():
    try:
        api = DerivAPI(app_id=1089)
        await api.authorize(DERIV_TOKEN)
        res = await api.balance()
        await api.clear()
        return float(res["balance"]["balance"])
    except:
        return 0.0

# ==============================
# 🔥 ADD: INITIAL BALANCE LOAD
# ==============================
if "live_bal" not in st.session_state:
    try:
        st.session_state.live_bal = asyncio.run(get_deriv_balance())
    except:
        st.session_state.live_bal = 0.0

# ==============================
# 🔥 ADD: REFRESH BUTTON (SAFE)
# ==============================
if st.button("🔄 Refresh Deriv Balance"):
    try:
        st.session_state.live_bal = asyncio.run(get_deriv_balance())
    except:
        st.error("Failed to fetch balance")

# --- SESSION STATE ---
if "session_profit" not in st.session_state:
    st.session_state.session_profit = 0.0
if "session_loss" not in st.session_state:
    st.session_state.session_loss = 0.0
if "wins" not in st.session_state:
    st.session_state.wins = 0
if "losses" not in st.session_state:
    st.session_state.losses = 0
if "trade_count" not in st.session_state:
    st.session_state.trade_count = 0
if "running" not in st.session_state:
    st.session_state.running = False

# --- CALCULATIONS ---
pl_value = st.session_state.session_profit - st.session_state.session_loss
win_rate = (st.session_state.wins / max(1, st.session_state.trade_count)) * 100

# --- STYLING ---
st.markdown("""
<style>
.stApp { background-color: #020d08; color: #8cc63f; }

div[data-testid="stMetric"] {
    background: #05140d;
    border: 1px solid #1a3a2a;
    padding: 12px;
    border-radius: 8px;
    text-align: center;
    box-shadow: 0 0 10px rgba(140,198,63,0.15);
}

div[data-testid="stMetric"]:hover {
    box-shadow: 0 0 18px rgba(140,198,63,0.35);
    transform: scale(1.02);
}

div[data-testid="stMetric"] > div:nth-child(2) {
    color: #00ff88 !important;
    font-size: 26px;
    font-weight: bold;
}

.stButton>button {
    background-color: #8cc63f !important;
    color: black !important;
    font-weight: bold;
    width: 100%;
}

/* SCANNER */
.adv-scanner {
    border: 1px solid #1a3a2a;
    border-radius: 10px;
    padding: 15px;
    background: #041f14;
}

.scan-row {
    display: flex;
    justify-content: space-between;
    padding: 10px 0;
    border-bottom: 1px solid #0a3d2a;
}

.scan-tag {
    padding: 2px 8px;
    border-radius: 5px;
    font-size: 10px;
    font-weight: bold;
}

.synth { background:#0b3d91; color:white; }
.metal { background:#b59f00; color:black; }
.crypto { background:#c46c00; color:black; }
.forex { background:#5c2ca0; color:white; }

.scan-title { color:#d8ffb0; font-size:14px; }
.scan-sub { color:#4e805d; font-size:10px; }

</style>
""", unsafe_allow_html=True)

# --- TOP METRICS ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Balance", f"${st.session_state.live_bal:,.2f}")
col2.metric("P/L", f"${pl_value:,.2f}")
col3.metric("Win Rate", f"{win_rate:.1f}%")
col4.metric("Streak", f"{st.session_state.wins}W / {st.session_state.losses}L")

# --- EXTRA METRICS ---
col9, col10, col11, col12, col13, col14 = st.columns(6)
col9.metric("🧠 Signal Strength", "0 / 10")
col10.metric("📉 Drawdown", "$0.00")
col11.metric("⚡ Exec Speed", "0 ms")
col12.metric("📡 API Status", "Connected")
col13.metric("🧮 Avg Trade", "$0.00")
col14.metric("🎲 Risk/Trade", "0%")

st.markdown("---")

# --- MAIN GRID ---
left, center, right = st.columns([2, 3, 1])

with left:
    st.markdown("### VOLATILITY INDEX")
    st.components.v1.html(
        '<iframe src="https://tradingview.binary.com/v1.3.10/main.html?symbol=1HZ100V&theme=black" height="400" width="100%"></iframe>',
        height=400
    )

with center:
    st.markdown("### XAU/USD (GOLD)")
    st.components.v1.html(
        '<iframe src="https://s.tradingview.com/widgetembed/?symbol=OANDA:XAUUSD&interval=5&theme=dark" height="400" width="100%"></iframe>',
        height=400
    )

with right:
    st.markdown("### ⚙️ ENGINE CONTROL")
    stake = st.number_input("Stake ($)", value=10.0)
    stop_loss = st.number_input("Stop Loss ($)", value=50.0)
    max_trades = st.number_input("Max Trades", value=10)

    if st.button("▶️ START BOT"):
        st.session_state.running = True
    if st.button("🛑 STOP BOT"):
        st.session_state.running = False

st.markdown("---")

# --- BOTTOM MARKETS ---
b1, b2, b3 = st.columns(3)

with b1:
    st.markdown("### BTC/USD")
    st.components.v1.html('<iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:BTCUSDT&theme=dark" height="250" width="100%"></iframe>', height=250)

with b2:
    st.markdown("### GBP/JPY")
    st.components.v1.html('<iframe src="https://s.tradingview.com/widgetembed/?symbol=OANDA:GBPJPY&theme=dark" height="250" width="100%"></iframe>', height=250)

with b3:
    st.markdown("### EUR/USD")
    st.components.v1.html('<iframe src="https://s.tradingview.com/widgetembed/?symbol=OANDA:EURUSD&theme=dark" height="250" width="100%"></iframe>', height=250)

# ==============================
# 🔥 ADVANCED MARKET SCANNER
# ==============================

st.markdown("---")
st.markdown("### 📡 MARKET SIGNAL SCANNER")

st.markdown("""
<div class="adv-scanner">

<div class="scan-row"><span><span class="scan-tag synth">SYNTH</span> <span class="scan-title">Vol 100 (1s)</span><br><span class="scan-sub">STREAK + STRUCTURE</span></span><span>—</span></div>

<div class="scan-row"><span><span class="scan-tag synth">SYNTH</span> <span class="scan-title">Vol 75 (1s)</span><br><span class="scan-sub">STREAK + STRUCTURE</span></span><span>—</span></div>

<div class="scan-row"><span><span class="scan-tag synth">SYNTH</span> <span class="scan-title">Vol 25 (1s)</span><br><span class="scan-sub">STREAK + STRUCTURE</span></span><span>—</span></div>

<div class="scan-row"><span><span class="scan-tag synth">SYNTH</span> <span class="scan-title">Vol 10 (1s)</span><br><span class="scan-sub">STREAK + STRUCTURE</span></span><span>—</span></div>

<div class="scan-row"><span><span class="scan-tag metal">METAL</span> <span class="scan-title">Gold XAU/USD</span><br><span class="scan-sub">EMA21 + EMA50</span></span><span>—</span></div>

<div class="scan-row"><span><span class="scan-tag crypto">CRYPTO</span> <span class="scan-title">Bitcoin BTC/USD</span><br><span class="scan-sub">EMA21 + EMA50</span></span><span>—</span></div>

<div class="scan-row"><span><span class="scan-tag forex">FOREX</span> <span class="scan-title">GBP/JPY</span><br><span class="scan-sub">EMA21 + EMA50</span></span><span>—</span></div>

</div>
""", unsafe_allow_html=True)

# --- ENGINE BUTTON ---
colA, colB, colC = st.columns([1,2,1])

with colB:
    if st.button("🚀 Start Engine (Activate Scanner)"):
        st.session_state.running = True

# --- STATUS ---
if st.session_state.running:
    st.success("✅ Engine Active — Live signals running...")
else:
    st.info("⚠️ Engine is OFF — Start to receive signals")

# --- FOOTER ---
st.markdown("""
<div style="text-align:center;margin-top:10px;color:#4e805d;">
Start the engine to see live scores
</div>
""", unsafe_allow_html=True)
