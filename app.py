import streamlit as st

# --- PAGE CONFIG ---
st.set_page_config(page_title="Slimmy Pro V21.0", layout="wide")

# --- SESSION STATE (for dynamic metrics) ---
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

# --- TOP METRICS (ORIGINAL) ---
col1, col2, col3, col4 = st.columns(4)

col1.metric("Balance", "$0.00")
col2.metric("P/L", "$0.00")
col3.metric("Win Rate", "0%")
col4.metric("Streak", "0W / 0L")

# --- EXTRA METRICS ROW (ADDED — DO NOT REMOVE ORIGINAL) ---
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

# --- LEFT PANEL ---
with left:
    st.markdown("### VOLATILITY INDEX")
    st.components.v1.html(
        '<iframe src="https://tradingview.binary.com/v1.3.10/main.html?symbol=1HZ100V&theme=black" height="400" width="100%"></iframe>',
        height=400
    )

# --- CENTER PANEL ---
with center:
    st.markdown("### XAU/USD (GOLD)")
    st.components.v1.html(
        '<iframe src="https://s.tradingview.com/widgetembed/?symbol=OANDA:XAUUSD&interval=5&theme=dark" height="400" width="100%"></iframe>',
        height=400
    )

# --- RIGHT PANEL ---
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
