"""
Streamlit Multi-Page Entry Point — Cargo-Aware Drone Selection DSS.
"""
import streamlit as st

st.set_page_config(
    page_title="Drone DSS — Cargo-Aware Selection",
    page_icon="🚁",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS for premium dark theme ──
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    }
    [data-testid="stSidebar"] .css-1d391kg,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: #e2e8f0;
    }

    /* Main area */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1a1a2e 50%, #16213e 100%);
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(30,41,59,0.8), rgba(51,65,85,0.6));
        border: 1px solid rgba(99,102,241,0.3);
        border-radius: 12px;
        padding: 16px;
        backdrop-filter: blur(10px);
    }
    [data-testid="stMetric"] label {
        color: #94a3b8 !important;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #e2e8f0 !important;
        font-weight: 700;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #818cf8, #a78bfa);
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(99,102,241,0.4);
    }

    /* Data frames / tables */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 8px 16px;
    }

    /* Headers */
    h1, h2, h3 {
        color: #e2e8f0 !important;
    }

    /* Success/warning/error boxes */
    .stAlert {
        border-radius: 8px;
    }

    /* Hide default footer */
    footer {visibility: hidden;}

    /* Glass card effect */
    .glass-card {
        background: rgba(30, 41, 59, 0.6);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 16px;
        padding: 24px;
        margin: 8px 0;
    }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──
with st.sidebar:
    st.markdown("## 🚁 Drone DSS")
    st.markdown("**Cargo-Aware Selection**")
    st.markdown("---")

    # Role selection
    role = st.selectbox(
        "👤 Select Role",
        ["Operator", "Supervisor", "Maintenance", "Admin"],
        key="user_role",
    )
    st.session_state["role"] = role

    st.markdown("---")
    st.markdown(
        '<p style="color:#64748b;font-size:0.75rem;">Group 6 — BTH University Project</p>',
        unsafe_allow_html=True,
    )

# ── Main landing page ──
st.markdown("# 🚁 Cargo-Aware Drone Selection DSS")
st.markdown("### Intelligent Decision Support for Port Drone Operations")
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    <div class="glass-card">
        <h3>🎯 What This System Does</h3>
        <ul>
            <li>Automatically filters unsafe drones using rule-based logic</li>
            <li>Scores and ranks suitable drones with weighted criteria</li>
            <li>Provides clear recommendations with full explanations</li>
            <li>Logs every decision for accountability and audit</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="glass-card">
        <h3>🗺️ Navigation Guide</h3>
        <ul>
            <li><strong>Dashboard</strong> — Operational overview & metrics</li>
            <li><strong>Drone Inventory</strong> — Manage fleet records</li>
            <li><strong>Create Mission</strong> — Define & evaluate a mission</li>
            <li><strong>Recommendation</strong> — Review DSS results</li>
            <li><strong>Schedule</strong> — View mission timeline</li>
            <li><strong>Alerts</strong> — Safety warnings</li>
            <li><strong>Decision Logs</strong> — Audit trail</li>
            <li><strong>Settings</strong> — Adjust criteria weights</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

st.info(f"👤 Logged in as: **{role}** — Use the sidebar pages to navigate.")
