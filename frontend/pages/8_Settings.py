"""
Page 8: Settings / Criteria Weights — adjust decision criteria weights.
"""
import streamlit as st
import requests

st.set_page_config(page_title="Settings — Drone DSS", page_icon="⚙️", layout="wide")

API = "http://localhost:8000"

st.markdown("# ⚙️ Settings — Criteria Weights")
st.markdown("Adjust the weight of each decision criterion. Weights must sum to 100%.")
st.markdown("---")

# ── Fetch weights ──
try:
    weights = requests.get(f"{API}/settings/weights").json()
except Exception:
    st.error("⚠️ Cannot connect to the backend API.")
    st.stop()

if not weights:
    st.info("No criteria weights found in the database.")
    st.stop()

# ── Group by category ──
categories = {}
for w in weights:
    cat = w["category"]
    if cat not in categories:
        categories[cat] = []
    categories[cat].append(w)

# ── Weight sliders ──
updated_weights = {}

for cat_name, criteria in categories.items():
    cat_icons = {
        "Capability": "🚁",
        "Mission": "🎯",
        "Environmental": "🌤️",
        "Safety": "🛡️",
        "Operational": "⚙️",
    }
    icon = cat_icons.get(cat_name, "📊")
    st.markdown(f"### {icon} {cat_name} Criteria")

    cols = st.columns(3)
    for i, cw in enumerate(criteria):
        with cols[i % 3]:
            val = st.number_input(
                f"{cw['criterion_name']} ({cw['criterion_id']})",
                min_value=0.0,
                max_value=100.0,
                value=float(cw["weight_pct"]),
                step=0.5,
                help=cw.get("description", ""),
                key=f"weight_{cw['criterion_id']}",
            )
            updated_weights[cw["criterion_id"]] = val

    st.markdown("---")

# ── Total indicator ──
total = sum(updated_weights.values())
tc1, tc2 = st.columns([3, 1])
with tc1:
    if abs(total - 100.0) < 0.01:
        st.success(f"✅ Total weight: **{total:.1f}%** — Valid")
    else:
        st.warning(f"⚠️ Total weight: **{total:.1f}%** — Must sum to 100%. Difference: {total - 100:.1f}%")

with tc2:
    if st.button("💾 Save Weights", use_container_width=True, type="primary"):
        if abs(total - 100.0) >= 0.5:
            st.error(f"Cannot save: weights sum to {total:.1f}%, not 100%.")
        else:
            payload = [
                {"criterion_id": cid, "weight_pct": val}
                for cid, val in updated_weights.items()
            ]
            resp = requests.put(f"{API}/settings/weights", json=payload)
            if resp.status_code == 200:
                st.success("✅ Weights saved successfully! Changes will apply to the next evaluation.")
                st.balloons()
            else:
                st.error(f"Error saving weights: {resp.text}")
