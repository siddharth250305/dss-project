"""
Decision Engine — implements the two-phase drone selection logic:
  Phase 1: Hard filter rules (R-01 through R-10)
  Phase 2: Weighted multi-criteria scoring and ranking
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple


# ═══════════════════════════════════════════════════════════
#  HARD FILTER RULES  (returns list of (rule_id, message))
# ═══════════════════════════════════════════════════════════

def apply_hard_filters(
    drone: Dict[str, Any],
    mission: Dict[str, Any],
    env: Dict[str, Any],
    cargo_zone: Dict[str, Any],
    operator_available: bool = True,
) -> List[Tuple[str, str]]:
    """
    Evaluate a single drone against the hard filter rules.
    Returns a list of (rule_id, rejection_message) tuples.
    An empty list means the drone passed all filters.
    """
    rejections: List[Tuple[str, str]] = []

    # Required flight time estimate (distance / assumed 40 km/h speed * 60 min)
    estimated_flight_min = (mission["required_distance_km"] / 40.0) * 60.0
    required_endurance = estimated_flight_min * 1.2  # 20% safety margin

    # R-01 Battery endurance
    if drone["battery_endurance_min"] < required_endurance:
        rejections.append(("R-01", "Insufficient battery endurance for this mission distance."))

    # R-02 Wind speed vs drone wind resistance
    if env.get("wind_speed_kmh", 0) > drone["wind_resistance_kmh"]:
        rejections.append(("R-02", "Wind speed exceeds drone wind resistance limit."))

    # R-03 Night vision required but not available
    if mission.get("requires_night_vision") and not drone.get("night_vision"):
        rejections.append(("R-03", "Required night vision sensor not available."))

    # R-04 Thermal sensor required but not available
    if mission.get("requires_thermal") and not drone.get("thermal_sensor"):
        rejections.append(("R-04", "Required thermal sensor not available."))

    # R-05 Maintenance status = Poor or Grounded
    if drone.get("maintenance_status") in ("Poor", "Grounded"):
        rejections.append(("R-05", "Drone is not cleared for operation due to maintenance status."))

    # R-06 Cargo zone distance > drone max flight radius
    zone_dist = cargo_zone.get("distance_from_base_km", mission["required_distance_km"])
    if zone_dist > drone["flight_radius_km"]:
        rejections.append(("R-06", "Cargo zone is beyond the drone's operational range."))

    # R-07 Critical safety risk without supervisor approval
    if cargo_zone.get("safety_risk_level") == "Critical":
        # In MVP we just flag it — a supervisor would need to approve
        rejections.append(("R-07", "Mission safety risk is Critical. Supervisor approval required before deployment."))

    # R-08 Regulatory compliance
    if not drone.get("regulatory_compliant", True):
        rejections.append(("R-08", "Drone does not meet regulatory requirements for this mission type."))

    # R-09 No qualified operator available
    if not operator_available:
        rejections.append(("R-09", "No operator is currently available to supervise this drone."))

    # R-10 Weather = Storm or Heavy Rain
    weather = env.get("weather_condition", "Clear")
    if weather in ("Storm", "Heavy Rain"):
        rejections.append(("R-10", "Current weather conditions are unsafe for drone operations."))

    return rejections


# ═══════════════════════════════════════════════════════════
#  SAFETY ALERTS
# ═══════════════════════════════════════════════════════════

def generate_safety_alerts(
    drone: Dict[str, Any],
    env: Dict[str, Any],
    cargo_zone: Dict[str, Any],
) -> List[str]:
    """Generate warning alerts (not rejection) when thresholds are approached."""
    alerts = []
    wind = env.get("wind_speed_kmh", 0)
    wr = drone.get("wind_resistance_kmh", 999)

    # Wind ≥ 80% of drone limit
    if wind >= wr * 0.8 and wind <= wr:
        alerts.append(f"⚠️  Wind speed ({wind} km/h) is at {wind/wr*100:.0f}% of {drone['drone_name']}'s limit ({wr} km/h).")

    if env.get("weather_condition") == "Rain":
        alerts.append("⚠️  Rain detected — reduced visibility expected.")

    if env.get("visibility_m", 10000) < 2000:
        alerts.append(f"⚠️  Low visibility ({env['visibility_m']} m). Proceed with caution.")

    if drone.get("daily_missions_done", 0) >= 3:
        alerts.append(f"⚠️  {drone['drone_name']} has completed {drone['daily_missions_done']} missions today. Battery fatigue risk.")

    if cargo_zone.get("obstacle_density") == "High":
        alerts.append("⚠️  High obstacle density in the cargo zone. Manual supervision recommended.")

    return alerts


# ═══════════════════════════════════════════════════════════
#  SCORING  (normalised 0-1, weighted sum)
# ═══════════════════════════════════════════════════════════

# Normalisation helpers
def _norm(value, min_val, max_val):
    """Min-max normalise to [0,1]. Higher is better."""
    if max_val == min_val:
        return 1.0
    return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))


def _norm_inverse(value, min_val, max_val):
    """Lower is better (e.g. charging time)."""
    return 1.0 - _norm(value, min_val, max_val)


_CAMERA_SCORE = {"SD": 0.33, "HD": 0.66, "4K": 1.0}
_URGENCY_SCORE = {"Low": 0.25, "Medium": 0.5, "High": 0.75, "Emergency": 1.0}
_WEATHER_SCORE = {"Clear": 1.0, "Cloudy": 0.8, "Rain": 0.5, "Heavy Rain": 0.2, "Storm": 0.0}
_OBSTACLE_SCORE = {"Low": 1.0, "Medium": 0.6, "High": 0.3}
_SAFETY_RISK_SCORE = {"Low": 1.0, "Medium": 0.7, "High": 0.4, "Critical": 0.1}


def score_drones(
    drones: List[Dict[str, Any]],
    mission: Dict[str, Any],
    env: Dict[str, Any],
    cargo_zone: Dict[str, Any],
    weights: Dict[str, float],           # criterion_id → weight as decimal (0.08 for 8%)
) -> List[Dict[str, Any]]:
    """
    Score and rank a list of drones (that already passed hard filters).
    Returns a list of dicts sorted by total_score descending.
    Each dict includes: drone_id, drone_name, total_score, breakdown {criterion_name: score_contribution}.
    """
    if not drones:
        return []

    # Gather fleet-wide min/max for normalisation
    radii   = [d["flight_radius_km"] for d in drones]
    batts   = [d["battery_endurance_min"] for d in drones]
    pays    = [d["payload_capacity_kg"] for d in drones]
    heights = [d["max_flight_height_m"] for d in drones]
    winds   = [d["wind_resistance_kmh"] for d in drones]
    charges = [d["charging_time_min"] for d in drones]
    dailys  = [d["daily_missions_done"] for d in drones]

    results = []
    for d in drones:
        breakdown = {}
        total = 0.0

        # C-01 Flight Radius
        s = _norm(d["flight_radius_km"], min(radii), max(radii))
        w = weights.get("C-01", 0.08)
        breakdown["Flight Radius"] = round(s * w, 4)
        total += s * w

        # C-02 Battery Endurance
        s = _norm(d["battery_endurance_min"], min(batts), max(batts))
        w = weights.get("C-02", 0.11)
        breakdown["Battery Endurance"] = round(s * w, 4)
        total += s * w

        # C-03 Payload Capacity
        s = _norm(d["payload_capacity_kg"], min(pays), max(pays))
        w = weights.get("C-03", 0.06)
        breakdown["Payload Capacity"] = round(s * w, 4)
        total += s * w

        # C-04 Camera Quality
        s = _CAMERA_SCORE.get(d.get("camera_quality", "HD"), 0.66)
        w = weights.get("C-04", 0.05)
        breakdown["Camera Quality"] = round(s * w, 4)
        total += s * w

        # C-05 Night Vision
        s = 1.0 if d.get("night_vision") else 0.0
        w = weights.get("C-05", 0.04)
        breakdown["Night Vision"] = round(s * w, 4)
        total += s * w

        # C-06 Thermal Sensor
        s = 1.0 if d.get("thermal_sensor") else 0.0
        w = weights.get("C-06", 0.04)
        breakdown["Thermal Sensor"] = round(s * w, 4)
        total += s * w

        # C-07 Flight Height
        s = _norm(d["max_flight_height_m"], min(heights), max(heights))
        w = weights.get("C-07", 0.04)
        breakdown["Flight Height"] = round(s * w, 4)
        total += s * w

        # C-08 Wind Resistance
        s = _norm(d["wind_resistance_kmh"], min(winds), max(winds))
        w = weights.get("C-08", 0.08)
        breakdown["Wind Resistance"] = round(s * w, 4)
        total += s * w

        # C-09 Charging Time (lower is better)
        s = _norm_inverse(d["charging_time_min"], min(charges), max(charges))
        w = weights.get("C-09", 0.02)
        breakdown["Charging Time"] = round(s * w, 4)
        total += s * w

        # C-10 Mission Urgency (drones with higher endurance get more score for urgent missions)
        urgency_s = _URGENCY_SCORE.get(mission.get("urgency_level", "Medium"), 0.5)
        endurance_s = _norm(d["battery_endurance_min"], min(batts), max(batts))
        s = urgency_s * endurance_s
        w = weights.get("C-10", 0.08)
        breakdown["Mission Urgency"] = round(s * w, 4)
        total += s * w

        # C-11 Cargo Zone Distance (drone radius vs zone distance — bigger margin is better)
        zone_dist = cargo_zone.get("distance_from_base_km", mission["required_distance_km"])
        s = min(1.0, d["flight_radius_km"] / max(zone_dist, 0.1))
        w = weights.get("C-11", 0.06)
        breakdown["Cargo Zone Distance"] = round(s * w, 4)
        total += s * w

        # C-12 Historical Reliability
        s = d.get("reliability_score", 0.8)
        w = weights.get("C-12", 0.06)
        breakdown["Historical Reliability"] = round(s * w, 4)
        total += s * w

        # C-13 Weather Condition
        s = _WEATHER_SCORE.get(env.get("weather_condition", "Clear"), 0.5)
        w = weights.get("C-13", 0.05)
        breakdown["Weather Condition"] = round(s * w, 4)
        total += s * w

        # C-14 Wind Speed (drone resistance margin over wind)
        wind_speed = env.get("wind_speed_kmh", 0)
        if d["wind_resistance_kmh"] > 0:
            s = max(0, 1.0 - wind_speed / d["wind_resistance_kmh"])
        else:
            s = 0.0
        w = weights.get("C-14", 0.07)
        breakdown["Wind Speed Margin"] = round(s * w, 4)
        total += s * w

        # C-15 Obstacle Density
        s = _OBSTACLE_SCORE.get(cargo_zone.get("obstacle_density", "Low"), 0.6)
        w = weights.get("C-15", 0.03)
        breakdown["Obstacle Density"] = round(s * w, 4)
        total += s * w

        # C-16 Safety Risk Level
        s = _SAFETY_RISK_SCORE.get(cargo_zone.get("safety_risk_level", "Low"), 0.7)
        w = weights.get("C-16", 0.06)
        breakdown["Safety Risk Level"] = round(s * w, 4)
        total += s * w

        # C-17 Regulatory Compliance (binary — already filtered, so 1.0 if here)
        s = 1.0 if d.get("regulatory_compliant") else 0.0
        w = weights.get("C-17", 0.04)
        breakdown["Regulatory Compliance"] = round(s * w, 4)
        total += s * w

        # C-19 Daily Missions (fewer is better)
        s = _norm_inverse(d.get("daily_missions_done", 0), min(dailys), max(dailys)) if max(dailys) > 0 else 1.0
        w = weights.get("C-19", 0.02)
        breakdown["Daily Missions"] = round(s * w, 4)
        total += s * w

        # C-21 Budget (use charging time as proxy — lower cost = lower charge)
        s = _norm_inverse(d["charging_time_min"], min(charges), max(charges))
        w = weights.get("C-21", 0.01)
        breakdown["Budget"] = round(s * w, 4)
        total += s * w

        results.append({
            "drone_id": d["drone_id"],
            "drone_name": d["drone_name"],
            "total_score": round(total, 4),
            "breakdown": breakdown,
        })

    # Sort descending by total score
    results.sort(key=lambda x: x["total_score"], reverse=True)
    return results


# ═══════════════════════════════════════════════════════════
#  FULL EVALUATION PIPELINE
# ═══════════════════════════════════════════════════════════

def evaluate(
    drones: List[Dict[str, Any]],
    mission: Dict[str, Any],
    env: Dict[str, Any],
    cargo_zone: Dict[str, Any],
    weights: Dict[str, float],
    operator_available: bool = True,
) -> Dict[str, Any]:
    """
    Run the full DSS evaluation pipeline.
    Returns: {
        recommended_drone, ranked_drones, rejected_drones, safety_alerts
    }
    """
    passed = []
    rejected = []
    all_alerts = []

    for drone in drones:
        reasons = apply_hard_filters(drone, mission, env, cargo_zone, operator_available)
        if reasons:
            rejected.append({
                "drone_id": drone["drone_id"],
                "drone_name": drone["drone_name"],
                "reasons": [{"rule_id": r[0], "message": r[1]} for r in reasons],
            })
        else:
            passed.append(drone)
            # Generate safety alerts for passing drones
            alerts = generate_safety_alerts(drone, env, cargo_zone)
            all_alerts.extend(alerts)

    ranked = score_drones(passed, mission, env, cargo_zone, weights)
    recommended = ranked[0] if ranked else None

    return {
        "recommended_drone": recommended,
        "ranked_drones": ranked,
        "rejected_drones": rejected,
        "safety_alerts": list(set(all_alerts)),  # de-duplicate
    }
