"""
Page 4: Drone Recommendation — review DSS results, confirm or override.
"""
import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Recommendation — Drone DSS", page_icon="🏆", layout="wide")

API = "http://localhost:8000"

st.markdown("# 🏆 Drone Recommendation")
st.markdown("Review the DSS evaluation result, see score breakdowns, and confirm or override the selection.")
st.markdown("---")

# ── Check for evaluation result ──
result = st.session_state.get("last_evaluation")

if not result:
    # Try to load from the latest decision log
    try:
        logs = requests.get(f"{API}/decisions/logs").json()
        if logs:
            latest = logs[0]
            result = {
                "mission_id": latest["mission_id"],
                "recommended_drone": {
                    "drone_id": latest.get("recommended_drone_id"),
                    "drone_name": latest.get("recommended_drone_name"),
                    "total_score": latest.get("recommended_score", 0),
                    "breakdown": latest.get("score_breakdown", {}),
                },
                "ranked_drones": latest.get("ranked_drones", []),
                "rejected_drones": latest.get("rejected_drones", []),
                "safety_alerts": latest.get("safety_alerts", []),
                "log_id": latest.get("log_id"),
            }
            if not result["recommended_drone"]["drone_id"]:
                result["recommended_drone"] = None
        else:
            st.info("🔍 No evaluations found. Create a mission first from the **Create Mission** page.")
            st.stop()
    except Exception:
        st.info("🔍 No evaluations found. Create a mission first from the **Create Mission** page.")
        st.stop()

rec = result.get("recommended_drone")
ranked = result.get("ranked_drones", [])
rejected = result.get("rejected_drones", [])
alerts = result.get("safety_alerts", [])
log_id = result.get("log_id")
mission_id = result.get("mission_id")

st.markdown(f"**Mission ID:** `{mission_id}`")

# ── Recommended Drone Card ──
if rec:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #065f46, #047857); border-radius: 16px; padding: 24px; margin: 16px 0; border: 1px solid rgba(16,185,129,0.5);">
        <h2 style="color: #ecfdf5; margin: 0;">🏆 Recommended: {name}</h2>
        <p style="color: #a7f3d0; font-size: 1.3rem; margin: 8px 0;">Total Score: <strong style="color: white; font-size: 1.5rem;">{score:.2f}</strong></p>
    </div>
    """.format(name=rec["drone_name"], score=rec["total_score"]), unsafe_allow_html=True)

    # ── Score Breakdown Chart ──
    st.markdown("### 📊 Score Breakdown")
    breakdown = rec.get("breakdown", {})
    if breakdown:
        criteria = list(breakdown.keys())
        scores = list(breakdown.values())

        fig = go.Figure(go.Bar(
            x=scores,
            y=criteria,
            orientation='h',
            marker=dict(
                color=scores,
                colorscale='Viridis',
                line=dict(width=1, color='rgba(255,255,255,0.3)')
            ),
            text=[f"{s:.4f}" for s in scores],
            textposition='outside',
        ))
        fig.update_layout(
            height=500,
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis_title="Score Contribution",
            yaxis=dict(autorange="reversed"),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e2e8f0'),
        )
        st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("⚠️ No suitable drones were found for this mission. All drones were rejected by the safety filters.")

# ── Ranked Drones Table ──
if ranked:
    st.markdown("### 📋 Ranked Drones")
    rank_data = []
    for i, r in enumerate(ranked, 1):
        rank_data.append({
            "Rank": f"#{i}",
            "Drone ID": r["drone_id"],
            "Drone Name": r["drone_name"],
            "Total Score": f"{r['total_score']:.4f}",
        })
    st.dataframe(pd.DataFrame(rank_data), use_container_width=True, hide_index=True)

# ── Rejected Drones Table ──
if rejected:
    st.markdown("### ❌ Rejected Drones")
    rej_data = []
    for r in rejected:
        reasons = ", ".join([reason["message"] for reason in r.get("reasons", [])])
        rej_data.append({
            "Drone ID": r["drone_id"],
            "Drone Name": r["drone_name"],
            "Rejection Reasons": reasons,
        })
    st.dataframe(
        pd.DataFrame(rej_data),
        use_container_width=True,
        hide_index=True,
    )

# ── Safety Alerts ──
if alerts:
    st.markdown("### 🚨 Safety Alerts")
    for alert in alerts:
        if "Critical" in alert:
            st.error(alert)
        else:
            st.warning(alert)

# ── Actions: Confirm / Override ──
st.markdown("---")
st.markdown("### ✅ Actions")

if log_id and rec:
    ac1, ac2 = st.columns(2)

    with ac1:
        if st.button("✅ Confirm Recommendation", use_container_width=True, type="primary"):
            resp = requests.post(f"{API}/decisions/confirm", json={
                "log_id": log_id,
            })
            if resp.status_code == 200:
                st.success(f"✅ Recommendation confirmed! Drone **{rec['drone_name']}** assigned to mission **{mission_id}**.")
                # Clear session
                if "last_evaluation" in st.session_state:
                    del st.session_state["last_evaluation"]
            else:
                st.error(f"Error: {resp.text}")

    with ac2:
        st.markdown("**Override Selection**")
        if ranked and len(ranked) > 1:
            override_options = {f"{r['drone_id']} — {r['drone_name']} (Score: {r['total_score']:.2f})": r["drone_id"] for r in ranked[1:]}
            override_selection = st.selectbox("Select alternative drone", list(override_options.keys()))
            override_reason = st.text_area("Reason for override *", placeholder="Explain why you are overriding the recommendation...")

            if st.button("🔄 Override", use_container_width=True):
                if not override_reason.strip():
                    st.error("Override reason is mandatory.")
                else:
                    resp = requests.post(f"{API}/decisions/override", json={
                        "log_id": log_id,
                        "override_drone_id": override_options[override_selection],
                        "override_reason": override_reason,
                    })
                    if resp.status_code == 200:
                        st.success(f"✅ Override recorded. Alternative drone assigned to mission **{mission_id}**.")
                        if "last_evaluation" in st.session_state:
                            del st.session_state["last_evaluation"]
                    else:
                        st.error(f"Error: {resp.text}")
        else:
            st.info("No alternative drones available to override with.")
elif not rec:
    st.info("No recommendation to confirm or override.")
