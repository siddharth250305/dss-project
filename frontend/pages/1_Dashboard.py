"""
Page 1: Dashboard Overview — at-a-glance operational status.
"""
import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Dashboard — Drone DSS", page_icon="📊", layout="wide")

API = "http://localhost:8000"

st.markdown("# 📊 Dashboard Overview")
st.markdown("---")

# ── Fetch data ──
try:
    drones = requests.get(f"{API}/drones/").json()
    missions = requests.get(f"{API}/missions/").json()
    alerts = requests.get(f"{API}/decisions/alerts").json()
    logs = requests.get(f"{API}/decisions/logs").json()
    cargo_zones = requests.get(f"{API}/cargo-zones/").json()
except Exception:
    st.error("⚠️ Cannot connect to the backend API. Make sure the FastAPI server is running on port 8000.")
    st.stop()

# ── Metric Cards ──
total_drones = len(drones)
available_drones = len([d for d in drones if d["maintenance_status"] == "Good"])
active_missions = len([m for m in missions if m["status"] in ("Scheduled", "Active")])
high_risk_zones = len([z for z in cargo_zones if z["safety_risk_level"] in ("High", "Critical")])

c1, c2, c3, c4 = st.columns(4)
c1.metric("🚁 Total Drones", total_drones)
c2.metric("✅ Available Drones", available_drones)
c3.metric("🎯 Active Missions", active_missions)
c4.metric("⚠️ High-Risk Zones", high_risk_zones)

st.markdown("---")

# ── Two-column layout ──
left, right = st.columns(2)

with left:
    st.markdown("### 🌤️ Fleet Status")
    if drones:
        status_counts = {}
        for d in drones:
            s = d["maintenance_status"]
            status_counts[s] = status_counts.get(s, 0) + 1

        status_colors = {"Good": "🟢", "Scheduled": "🟡", "Poor": "🔴", "Grounded": "⚫"}
        for status, count in status_counts.items():
            icon = status_colors.get(status, "⚪")
            st.markdown(f"{icon} **{status}**: {count} drones")
    else:
        st.info("No drones in the fleet.")

    st.markdown("---")
    st.markdown("### 🚨 Recent Alerts")
    if alerts:
        for alert in alerts[:5]:
            severity_icon = {"Info": "ℹ️", "Warning": "⚠️", "Critical": "🔴"}.get(alert["severity"], "ℹ️")
            st.markdown(f"{severity_icon} {alert['description']}")
    else:
        st.success("✅ No active alerts.")

with right:
    st.markdown("### 📝 Recent Decisions")
    if logs:
        log_data = []
        for log in logs[:5]:
            log_data.append({
                "Mission": log["mission_id"],
                "Drone": log.get("recommended_drone_name", "—"),
                "Score": f"{log.get('recommended_score', 0):.2f}" if log.get("recommended_score") else "—",
                "Override": "Yes" if log.get("override") else "No",
                "Time": log.get("created_at", "")[:16] if log.get("created_at") else "—",
            })
        st.dataframe(pd.DataFrame(log_data), use_container_width=True, hide_index=True)
    else:
        st.info("No decisions recorded yet. Create a mission to get started.")

    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("➕ New Mission", use_container_width=True):
            st.switch_page("pages/3_Create_Mission.py")
    with col_b:
        if st.button("🔄 Update Drone", use_container_width=True):
            st.switch_page("pages/2_Drone_Inventory.py")
