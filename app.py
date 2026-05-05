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

# --- BASE STYLING ---
st.markdown("""
<style>
.stApp { background-color: #020d08; color: #8cc63f; }

div[data-testid="stMetric"] {
    background: #05140d;
    border: 1px solid #1a3a2a;
    padding: 12px;
    border-radius: 8px;
    text-align: center;
}

h3 { color: #8cc63f; }

.stButton>button {
    background-color: #8cc63f !important;
    color: black !important;
    font-weight: bold;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

# --- 🔥 EXTRA VISIBILITY STYLING (YOUR FIX) ---
st.markdown("""
<style>

/* STRONGER METRIC CARDS */
div[data-testid="stMetric"] {
    background: linear-gradient(145deg, #062e1c, #041f14) !important;
    border: 1px solid #1f7a4c !important;
    box-shadow: 0 0 12px rgba(140, 198, 63, 0.25) !important;
    padding: 14px !important;
    border-radius: 10px !important;
}

/* BIG VALUE TEXT */
div[data-testid="stMetric"] > div:nth-child(2) {
    color: #b6ff6a !important;
    font-size: 26px !important;
    font-weight: bold !important;
}

/* LABEL TEXT */
div[data-testid="stMetric"] label {
    color: #8cc63f !important;
    font-weight: 600 !important;
}

/* HOVER EFFECT */
div[data-testid="stMetric"]:hover {
    transform: scale(1.03);
    box-shadow: 0 0 20px rgba(140, 198, 63, 0.5) !important;
    transition: 0.2s ease-in-out;
}

</style>
""", unsafe_allow_html=True)

# --- TOP METRICS ---
col1, col2, col3, col4 = st.columns(4)

col1.metric("Balance", "$0.00")
col2.metric("P/L", "$0.00")
col3.metric("Win Rate", "0%")
col4.metric("Streak", "0W / 0L")

# --- EXTRA METRICS (ADDED) ---
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

# LEFT
with left:
    st.markdown("### VOLATILITY INDEX")
    st.components.v1.html(
        '<iframe src="https://tradingview.binary.com/v1.3.10/main.html?symbol=1HZ100V&theme=black" height="400" width="100%"></iframe>',
        height=400
    )

# CENTER
with center:
    st.markdown("### XAU/USD (GOLD)")
    st.components.v1.html(
        '<iframe src="https://s.tradingview.com/widgetembed/?symbol=OANDA:XAUUSD&interval=5&theme=dark" height="400" width="100%"></iframe>',
        height=400
    )

# RIGHT
with right:
    st.markdown("### ⚙️ ENGINE CONTROL")

    stake = st.number_input("Stake ($)", value=10.0)
    stop_loss = st.number_input("Stop Loss ($)", value=50.0)
    max_trades = st.number_input("Max Trades", value=10)

    st.markdown("---")

    if st.button("▶️ START BOT"):
        st.session_state.running = True

    if st.button("🛑 STOP BOT"):
        st.session_state.running = False

# --- BOTTOM MARKETS ---
st.markdown("---")

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
