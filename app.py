import streamlit as st

# --- PAGE CONFIG ---
st.set_page_config(page_title="Slimmy Pro V21.0", layout="wide")

# --- SESSION STATE ---
if "live_bal" not in st.session_state:
    st.session_state.live_bal = 0.0
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
    background: linear-gradient(145deg, #062e1c, #041f14);
    border: 1px solid #1f7a4c;
    box-shadow: 0 0 12px rgba(140, 198, 63, 0.25);
    padding: 14px;
    border-radius: 10px;
    text-align: center;
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

.scanner-box {
    border: 1px solid #1f7a4c;
    border-radius: 10px;
    padding: 15px;
    background: #041f14;
}

.signal-row {
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid #0a3d2a;
}

.tag {
    padding: 3px 8px;
    border-radius: 5px;
    font-size: 11px;
    font-weight: bold;
}

.synth { background:#0b3d91; color:white; }
.metal { background:#b59f00; color:black; }
.crypto { background:#c46c00; color:black; }
.forex { background:#5c2ca0; color:white; }

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

col9.metric("🧠 Signal Strength", "0 / 10", "+0")
col10.metric("📉 Drawdown", "$0.00", "0%")
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
    st.components.v1.html(
        '<iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:BTCUSDT&interval=5&theme=dark" height="250" width="100%"></iframe>',
        height=250
    )

with b2:
    st.markdown("### GBP/JPY")
    st.components.v1.html(
        '<iframe src="https://s.tradingview.com/widgetembed/?symbol=OANDA:GBPJPY&interval=5&theme=dark" height="250" width="100%"></iframe>',
        height=250
    )

with b3:
    st.markdown("### EUR/USD")
    st.components.v1.html(
        '<iframe src="https://s.tradingview.com/widgetembed/?symbol=OANDA:EURUSD&interval=5&theme=dark" height="250" width="100%"></iframe>',
        height=250
    )

# ==============================
# 🔥 NEW: MARKET SIGNAL SCANNER
# ==============================

st.markdown("---")
st.markdown("### 📡 MARKET SIGNAL SCANNER")

st.markdown("""
<div class="scanner-box">

<div class="signal-row"><span><span class="tag synth">SYNTH</span> Vol 100 (1s)</span><span>—</span></div>
<div class="signal-row"><span><span class="tag synth">SYNTH</span> Vol 75 (1s)</span><span>—</span></div>
<div class="signal-row"><span><span class="tag synth">SYNTH</span> Vol 25 (1s)</span><span>—</span></div>
<div class="signal-row"><span><span class="tag synth">SYNTH</span> Vol 10 (1s)</span><span>—</span></div>

<div class="signal-row"><span><span class="tag metal">METAL</span> Gold XAU/USD</span><span>—</span></div>
<div class="signal-row"><span><span class="tag crypto">CRYPTO</span> BTC/USD</span><span>—</span></div>
<div class="signal-row"><span><span class="tag forex">FOREX</span> GBP/JPY</span><span>—</span></div>

</div>
""", unsafe_allow_html=True)
