"""
Page 5: Mission Schedule — view upcoming and active missions.
"""
import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Mission Schedule — Drone DSS", page_icon="📅", layout="wide")

API = "http://localhost:8000"

st.markdown("# 📅 Mission Schedule")
st.markdown("View all missions and their current status.")
st.markdown("---")

# ── Fetch missions ──
try:
    missions = requests.get(f"{API}/missions/").json()
except Exception:
    st.error("⚠️ Cannot connect to the backend API.")
    st.stop()

# ── Status filter ──
status_filter = st.multiselect(
    "Filter by Status",
    ["Draft", "Scheduled", "Active", "Completed", "Cancelled"],
    default=["Draft", "Scheduled", "Active", "Completed", "Cancelled"],
)

filtered = [m for m in missions if m.get("status") in status_filter]

STATUS_COLORS = {
    "Draft": "⚪",
    "Scheduled": "🔵",
    "Active": "🟢",
    "Completed": "✅",
    "Cancelled": "🔴",
}

URGENCY_BADGE = {
    "Low": "🟢 Low",
    "Medium": "🟡 Medium",
    "High": "🟠 High",
    "Emergency": "🔴 Emergency",
}

if filtered:
    table_data = []
    for m in filtered:
        table_data.append({
            "Mission ID": m["mission_id"],
            "Type": m["mission_type"],
            "Urgency": URGENCY_BADGE.get(m["urgency_level"], m["urgency_level"]),
            "Cargo Zone": m.get("cargo_zone_id", "—"),
            "Distance (km)": m["required_distance_km"],
            "Assigned Drone": m.get("assigned_drone_id", "—") or "Pending",
            "Scheduled": str(m.get("scheduled_time", "—") or "—")[:16],
            "Status": f"{STATUS_COLORS.get(m['status'], '⚪')} {m['status']}",
            "Created": str(m.get("created_at", ""))[:16],
        })
    st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

    # ── Status summary metrics ──
    st.markdown("---")
    st.markdown("### 📊 Status Summary")
    sc1, sc2, sc3, sc4, sc5 = st.columns(5)
    counts = {}
    for m in missions:
        s = m.get("status", "Unknown")
        counts[s] = counts.get(s, 0) + 1
    sc1.metric("⚪ Draft", counts.get("Draft", 0))
    sc2.metric("🔵 Scheduled", counts.get("Scheduled", 0))
    sc3.metric("🟢 Active", counts.get("Active", 0))
    sc4.metric("✅ Completed", counts.get("Completed", 0))
    sc5.metric("🔴 Cancelled", counts.get("Cancelled", 0))
else:
    st.info("No missions found. Create a mission from the **Create Mission** page.")
