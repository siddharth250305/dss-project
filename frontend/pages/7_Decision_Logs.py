"""
Page 7: Decision Logs — searchable audit trail of all past decisions.
"""
import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Decision Logs — Drone DSS", page_icon="📜", layout="wide")

API = "http://localhost:8000"

st.markdown("# 📜 Decision Logs")
st.markdown("Review the full audit trail of all drone selection decisions.")
st.markdown("---")

# ── Fetch logs ──
try:
    logs = requests.get(f"{API}/decisions/logs").json()
except Exception:
    st.error("⚠️ Cannot connect to the backend API.")
    st.stop()

if not logs:
    st.info("No decision logs yet. Create and evaluate a mission to generate logs.")
    st.stop()

# ── Search bar ──
search = st.text_input("🔍 Search by Mission ID, Drone Name, or Operator", "")

filtered = logs
if search:
    search_lower = search.lower()
    filtered = [
        l for l in logs
        if search_lower in str(l.get("mission_id", "")).lower()
        or search_lower in str(l.get("recommended_drone_name", "")).lower()
        or search_lower in str(l.get("operator_id", "")).lower()
    ]

# ── Log Table ──
table_data = []
for log in filtered:
    table_data.append({
        "Log ID": log["log_id"],
        "Mission ID": log["mission_id"],
        "Recommended Drone": log.get("recommended_drone_name", "—"),
        "Score": f"{log.get('recommended_score', 0):.2f}" if log.get("recommended_score") else "—",
        "Override": "✅ Yes" if log.get("override") else "❌ No",
        "Confirmed": "✅" if log.get("confirmed") else "⏳",
        "Operator": log.get("operator_id", "—") or "—",
        "Timestamp": str(log.get("created_at", ""))[:19] if log.get("created_at") else "—",
    })

st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

# ── Expandable detail view ──
st.markdown("---")
st.markdown("### 🔎 Decision Detail")

log_options = {f"{l['log_id']} — Mission {l['mission_id']}": l for l in filtered}
if log_options:
    selected_key = st.selectbox("Select a decision to expand", list(log_options.keys()))
    log = log_options[selected_key]

    dc1, dc2 = st.columns(2)

    with dc1:
        st.markdown("#### 📊 Score Breakdown")
        breakdown = log.get("score_breakdown")
        if breakdown:
            bd_data = [{"Criterion": k, "Score Contribution": f"{v:.4f}"} for k, v in breakdown.items()]
            st.dataframe(pd.DataFrame(bd_data), use_container_width=True, hide_index=True)
        else:
            st.info("No score breakdown available.")

    with dc2:
        st.markdown("#### ❌ Rejected Drones")
        rejected = log.get("rejected_drones", [])
        if rejected:
            for r in rejected:
                reasons = ", ".join([reason.get("message", "") for reason in r.get("reasons", [])])
                st.markdown(f"- **{r.get('drone_name', r.get('drone_id'))}**: {reasons}")
        else:
            st.info("No drones were rejected.")

    # Safety Alerts
    alerts = log.get("safety_alerts", [])
    if alerts:
        st.markdown("#### 🚨 Safety Alerts")
        for a in alerts:
            st.warning(a)

    # Override info
    if log.get("override"):
        st.markdown("#### 🔄 Override Details")
        st.markdown(f"- **Override Drone:** {log.get('override_drone_id', '—')}")
        st.markdown(f"- **Reason:** {log.get('override_reason', '—')}")
