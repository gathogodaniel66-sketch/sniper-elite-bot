st.markdown("""
<style>

/* 🔥 STRONGER METRIC CARDS */
div[data-testid="stMetric"] {
    background: linear-gradient(145deg, #062e1c, #041f14) !important;
    border: 1px solid #1f7a4c !important;
    box-shadow: 0 0 12px rgba(140, 198, 63, 0.25) !important;
    padding: 14px !important;
    border-radius: 10px !important;
}

/* 💡 BIGGER VALUE TEXT */
div[data-testid="stMetric"] > div:nth-child(2) {
    color: #b6ff6a !important;
    font-size: 26px !important;
    font-weight: bold !important;
}

/* 🟢 LABEL TEXT */
div[data-testid="stMetric"] label {
    color: #8cc63f !important;
    font-weight: 600 !important;
}

/* ✨ HOVER EFFECT (PRO FEEL) */
div[data-testid="stMetric"]:hover {
    transform: scale(1.03);
    box-shadow: 0 0 20px rgba(140, 198, 63, 0.5) !important;
    transition: 0.2s ease-in-out;
}

/* 🧠 EXTRA METRICS EMPHASIS */
div[data-testid="stMetric"]:nth-child(n+5) {
    border: 1px solid #39ff14 !important;
    box-shadow: 0 0 14px rgba(57, 255, 20, 0.35) !important;
}

</style>
""", unsafe_allow_html=True)
