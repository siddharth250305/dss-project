"""
Page 3: Create Mission — define a new mission and trigger the decision engine.
"""
import streamlit as st
import requests

st.set_page_config(page_title="Create Mission — Drone DSS", page_icon="🎯", layout="wide")

API = "http://localhost:8000"

st.markdown("# 🎯 Create New Mission")
st.markdown("Define mission parameters and environmental conditions, then submit to evaluate drones.")
st.markdown("---")

# ── Fetch cargo zones ──
try:
    zones = requests.get(f"{API}/cargo-zones/").json()
except Exception:
    st.error("⚠️ Cannot connect to the backend API.")
    st.stop()

zone_options = {f"{z['zone_id']} — {z['zone_name']}": z for z in zones}

with st.form("create_mission_form"):
    st.markdown("### 📋 Mission Parameters")
    mc1, mc2 = st.columns(2)

    with mc1:
        mission_type = st.selectbox("Mission Type *", ["Inspection", "Surveillance", "Monitoring", "Emergency"])
        urgency = st.selectbox("Urgency Level *", ["Low", "Medium", "High", "Emergency"])
        selected_zone_key = st.selectbox("Cargo Zone *", list(zone_options.keys()))
        selected_zone = zone_options[selected_zone_key]
        distance = st.number_input(
            "Required Distance (km)",
            min_value=0.1,
            value=float(selected_zone["distance_from_base_km"]),
            help="Auto-filled from cargo zone. Adjust if needed.",
        )
        height = st.number_input("Required Flight Height (m)", min_value=1, value=100)

    with mc2:
        night_vision = st.checkbox("Requires Night Vision")
        thermal = st.checkbox("Requires Thermal Sensor")
        st.markdown("---")
        st.markdown("### 🌤️ Environmental Conditions")
        weather = st.selectbox("Weather Condition", ["Clear", "Cloudy", "Rain", "Heavy Rain", "Storm"])
        wind = st.number_input("Wind Speed (km/h)", min_value=0.0, value=15.0)
        visibility = st.number_input("Visibility (m)", min_value=100, value=10000)
        temperature = st.number_input("Temperature (°C)", value=20.0)

    operator_available = st.checkbox("Qualified operator is available", value=True)

    submitted = st.form_submit_button("🔍 Evaluate Drones", use_container_width=True, type="primary")

if submitted:
    # Step 1: Create the mission
    mission_payload = {
        "mission_type": mission_type,
        "urgency_level": urgency,
        "cargo_zone_id": selected_zone["zone_id"],
        "required_distance_km": distance,
        "required_height_m": height,
        "requires_night_vision": night_vision,
        "requires_thermal": thermal,
    }
    resp = requests.post(f"{API}/missions/", json=mission_payload)
    if resp.status_code != 200:
        st.error(f"Failed to create mission: {resp.text}")
        st.stop()

    mission = resp.json()
    mission_id = mission["mission_id"]

    # Step 2: Evaluate drones for this mission
    eval_payload = {
        "mission_id": mission_id,
        "weather_condition": weather,
        "wind_speed_kmh": wind,
        "visibility_m": visibility,
        "temperature_c": temperature,
        "operator_available": operator_available,
    }
    eval_resp = requests.post(f"{API}/decisions/evaluate", json=eval_payload)
    if eval_resp.status_code != 200:
        st.error(f"Evaluation failed: {eval_resp.text}")
        st.stop()

    result = eval_resp.json()

    # Store result in session state for the recommendation page
    st.session_state["last_evaluation"] = result
    st.session_state["last_mission_id"] = mission_id

    st.success(f"✅ Mission **{mission_id}** created and evaluated successfully!")

    # Show quick summary
    rec = result.get("recommended_drone")
    if rec:
        st.markdown(f"### 🏆 Recommended Drone: **{rec['drone_name']}** (Score: {rec['total_score']:.2f})")
    else:
        st.warning("No suitable drones found for this mission.")

    st.markdown(f"- **{len(result.get('ranked_drones', []))}** drones passed filtering")
    st.markdown(f"- **{len(result.get('rejected_drones', []))}** drones were rejected")
    st.markdown(f"- **{len(result.get('safety_alerts', []))}** safety alerts generated")

    st.info("👉 Go to the **Recommendation** page in the sidebar for full details.")
