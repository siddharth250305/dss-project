"""
Page 2: Drone Inventory — view, add, and edit drone records.
"""
import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Drone Inventory — Drone DSS", page_icon="🚁", layout="wide")

API = "http://localhost:8000"

st.markdown("# 🚁 Drone Inventory")
st.markdown("Manage the drone fleet — view status, add new drones, or edit existing records.")
st.markdown("---")

# ── Fetch drones ──
try:
    drones = requests.get(f"{API}/drones/").json()
except Exception:
    st.error("⚠️ Cannot connect to the backend API.")
    st.stop()

# ── Filters ──
with st.expander("🔍 Filter Drones", expanded=False):
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        filter_status = st.multiselect(
            "Maintenance Status",
            ["Good", "Scheduled", "Poor", "Grounded"],
            default=["Good", "Scheduled", "Poor", "Grounded"],
        )
    with fc2:
        filter_night = st.selectbox("Night Vision", ["All", "Yes", "No"])
    with fc3:
        filter_thermal = st.selectbox("Thermal Sensor", ["All", "Yes", "No"])

# Apply filters
filtered = drones
if filter_status:
    filtered = [d for d in filtered if d["maintenance_status"] in filter_status]
if filter_night == "Yes":
    filtered = [d for d in filtered if d["night_vision"]]
elif filter_night == "No":
    filtered = [d for d in filtered if not d["night_vision"]]
if filter_thermal == "Yes":
    filtered = [d for d in filtered if d["thermal_sensor"]]
elif filter_thermal == "No":
    filtered = [d for d in filtered if not d["thermal_sensor"]]

# ── Drone Table ──
st.markdown(f"### Fleet Overview ({len(filtered)} drones)")

if filtered:
    STATUS_BADGE = {
        "Good": "🟢 Good",
        "Scheduled": "🟡 Scheduled",
        "Poor": "🔴 Poor",
        "Grounded": "⚫ Grounded",
    }
    table_data = []
    for d in filtered:
        table_data.append({
            "ID": d["drone_id"],
            "Name": d["drone_name"],
            "Range (km)": d["flight_radius_km"],
            "Battery (min)": d["battery_endurance_min"],
            "Payload (kg)": d["payload_capacity_kg"],
            "Camera": d["camera_quality"],
            "Night": "✅" if d["night_vision"] else "❌",
            "Thermal": "✅" if d["thermal_sensor"] else "❌",
            "Wind Res (km/h)": d["wind_resistance_kmh"],
            "Status": STATUS_BADGE.get(d["maintenance_status"], d["maintenance_status"]),
            "Reliability": f"{d['reliability_score']:.0%}",
        })
    st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)
else:
    st.info("No drones match the current filters.")

st.markdown("---")

# ── Tabs: Add / Edit ──
tab_add, tab_edit = st.tabs(["➕ Add New Drone", "✏️ Edit Drone"])

with tab_add:
    with st.form("add_drone_form"):
        st.markdown("#### Add a New Drone")
        ac1, ac2, ac3 = st.columns(3)
        with ac1:
            name = st.text_input("Drone Name *", placeholder="e.g. SkyHawk X2")
            radius = st.number_input("Flight Radius (km)", min_value=1.0, value=15.0)
            battery = st.number_input("Battery Endurance (min)", min_value=1, value=45)
            payload = st.number_input("Payload Capacity (kg)", min_value=0.0, value=2.0)
        with ac2:
            camera = st.selectbox("Camera Quality", ["SD", "HD", "4K"], index=1)
            night = st.checkbox("Night Vision")
            thermal = st.checkbox("Thermal Sensor")
            height = st.number_input("Max Flight Height (m)", min_value=1, value=120)
        with ac3:
            wind = st.number_input("Wind Resistance (km/h)", min_value=1.0, value=40.0)
            charge = st.number_input("Charging Time (min)", min_value=1, value=60)
            maint = st.selectbox("Maintenance Status", ["Good", "Scheduled", "Poor", "Grounded"])
            reg = st.checkbox("Regulatory Compliant", value=True)

        submitted = st.form_submit_button("➕ Add Drone", use_container_width=True)
        if submitted:
            if not name.strip():
                st.error("Drone name is required.")
            else:
                payload_data = {
                    "drone_name": name,
                    "flight_radius_km": radius,
                    "battery_endurance_min": battery,
                    "payload_capacity_kg": payload,
                    "camera_quality": camera,
                    "night_vision": night,
                    "thermal_sensor": thermal,
                    "max_flight_height_m": height,
                    "wind_resistance_kmh": wind,
                    "charging_time_min": charge,
                    "maintenance_status": maint,
                    "regulatory_compliant": reg,
                }
                resp = requests.post(f"{API}/drones/", json=payload_data)
                if resp.status_code == 200:
                    st.success(f"✅ Drone '{name}' added successfully!")
                    st.rerun()
                else:
                    st.error(f"Error: {resp.text}")

with tab_edit:
    st.markdown("#### Edit an Existing Drone")
    drone_options = {f"{d['drone_id']} — {d['drone_name']}": d for d in drones}
    if drone_options:
        selected = st.selectbox("Select Drone", list(drone_options.keys()))
        drone = drone_options[selected]

        with st.form("edit_drone_form"):
            ec1, ec2, ec3 = st.columns(3)
            with ec1:
                e_name = st.text_input("Drone Name", value=drone["drone_name"])
                e_radius = st.number_input("Flight Radius (km)", value=drone["flight_radius_km"], key="e_rad")
                e_battery = st.number_input("Battery Endurance (min)", value=drone["battery_endurance_min"], key="e_bat")
                e_payload = st.number_input("Payload (kg)", value=drone["payload_capacity_kg"], key="e_pay")
            with ec2:
                e_camera = st.selectbox("Camera", ["SD", "HD", "4K"], index=["SD","HD","4K"].index(drone["camera_quality"]), key="e_cam")
                e_night = st.checkbox("Night Vision", value=drone["night_vision"], key="e_nv")
                e_thermal = st.checkbox("Thermal Sensor", value=drone["thermal_sensor"], key="e_ts")
                e_height = st.number_input("Max Height (m)", value=drone["max_flight_height_m"], key="e_ht")
            with ec3:
                e_wind = st.number_input("Wind Res (km/h)", value=drone["wind_resistance_kmh"], key="e_wr")
                e_charge = st.number_input("Charge Time (min)", value=drone["charging_time_min"], key="e_ch")
                e_maint = st.selectbox("Maintenance", ["Good","Scheduled","Poor","Grounded"],
                                       index=["Good","Scheduled","Poor","Grounded"].index(drone["maintenance_status"]), key="e_mt")
                e_reg = st.checkbox("Regulatory Compliant", value=drone["regulatory_compliant"], key="e_rg")

            e_submitted = st.form_submit_button("💾 Save Changes", use_container_width=True)
            if e_submitted:
                update_data = {
                    "drone_name": e_name,
                    "flight_radius_km": e_radius,
                    "battery_endurance_min": e_battery,
                    "payload_capacity_kg": e_payload,
                    "camera_quality": e_camera,
                    "night_vision": e_night,
                    "thermal_sensor": e_thermal,
                    "max_flight_height_m": e_height,
                    "wind_resistance_kmh": e_wind,
                    "charging_time_min": e_charge,
                    "maintenance_status": e_maint,
                    "regulatory_compliant": e_reg,
                }
                resp = requests.put(f"{API}/drones/{drone['drone_id']}", json=update_data)
                if resp.status_code == 200:
                    st.success(f"✅ Drone '{e_name}' updated successfully!")
                    st.rerun()
                else:
                    st.error(f"Error: {resp.text}")
    else:
        st.info("No drones in the fleet to edit.")
