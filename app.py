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

# --- TOP METRICS (PRO VERSION) ---
col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)

win_rate = (st.session_state.wins / max(1, st.session_state.trade_count)) * 100

col1.metric("💰 Balance", f"${st.session_state.live_bal:,.2f}")
col2.metric("📈 P/L", f"${st.session_state.session_profit - st.session_state.session_loss:,.2f}")
col3.metric("🎯 Win Rate", f"{win_rate:.1f}%")
col4.metric("🔥 Streak", f"{st.session_state.wins}W / {st.session_state.losses}L")
col5.metric("📊 Trades", int(st.session_state.trade_count))
col6.metric("⚖️ Risk", f"${st.session_state.session_loss:,.2f}")
col7.metric("⏱ Session", "Live")
col8.metric("📡 Status", "Active" if st.session_state.running else "Idle")

st.markdown("---")

# --- MAIN GRID ---
left, center, right = st.columns([2, 3, 1])

# --- LEFT PANEL (Deriv Chart) ---
with left:
    st.markdown("### VOLATILITY INDEX")
    st.components.v1.html(
        '<iframe src="https://tradingview.binary.com/v1.3.10/main.html?symbol=1HZ100V&theme=black" height="400" width="100%"></iframe>',
        height=400
    )

# --- CENTER PANEL (Gold Chart) ---
with center:
    st.markdown("### XAU/USD (GOLD)")
    st.components.v1.html(
        '<iframe src="https://s.tradingview.com/widgetembed/?symbol=OANDA:XAUUSD&interval=5&theme=dark" height="400" width="100%"></iframe>',
        height=400
    )

# --- RIGHT PANEL (ENGINE CONTROL) ---
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
