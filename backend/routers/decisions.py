"""
Decision evaluation, confirmation, and log endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import (
    Drone, Mission, CargoZone, EnvironmentalData,
    DecisionLog, SafetyAlert, CriterionWeight
)
from schemas import (
    EvaluationRequest, EvaluationResult,
    DecisionLogOut, OverrideRequest, ConfirmRequest, SafetyAlertOut
)
from decision_engine import evaluate

router = APIRouter(prefix="/decisions", tags=["Decisions"])


def _drone_to_dict(d):
    return {
        "drone_id": d.drone_id,
        "drone_name": d.drone_name,
        "flight_radius_km": d.flight_radius_km,
        "battery_endurance_min": d.battery_endurance_min,
        "payload_capacity_kg": d.payload_capacity_kg,
        "camera_quality": d.camera_quality,
        "night_vision": d.night_vision,
        "thermal_sensor": d.thermal_sensor,
        "max_flight_height_m": d.max_flight_height_m,
        "wind_resistance_kmh": d.wind_resistance_kmh,
        "charging_time_min": d.charging_time_min,
        "maintenance_status": d.maintenance_status,
        "regulatory_compliant": d.regulatory_compliant,
        "reliability_score": d.reliability_score,
        "daily_missions_done": d.daily_missions_done,
    }


def _mission_to_dict(m):
    return {
        "mission_id": m.mission_id,
        "mission_type": m.mission_type,
        "urgency_level": m.urgency_level,
        "cargo_zone_id": m.cargo_zone_id,
        "required_distance_km": m.required_distance_km,
        "required_height_m": m.required_height_m,
        "requires_night_vision": m.requires_night_vision,
        "requires_thermal": m.requires_thermal,
    }


def _zone_to_dict(z):
    return {
        "zone_id": z.zone_id,
        "zone_name": z.zone_name,
        "distance_from_base_km": z.distance_from_base_km,
        "obstacle_density": z.obstacle_density,
        "safety_risk_level": z.safety_risk_level,
        "cargo_priority": z.cargo_priority,
    }


# ───────── POST /decisions/evaluate ─────────

@router.post("/evaluate", response_model=EvaluationResult)
def evaluate_mission(req: EvaluationRequest, db: Session = Depends(get_db)):
    # Fetch mission
    mission = db.query(Mission).filter(Mission.mission_id == req.mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    # Fetch cargo zone (or create a default)
    cargo_zone = None
    if mission.cargo_zone_id:
        cargo_zone = db.query(CargoZone).filter(CargoZone.zone_id == mission.cargo_zone_id).first()
    if not cargo_zone:
        # Fallback zone
        cargo_zone_dict = {
            "zone_id": "UNKNOWN",
            "zone_name": "Unknown",
            "distance_from_base_km": mission.required_distance_km,
            "obstacle_density": "Low",
            "safety_risk_level": "Low",
            "cargo_priority": "Standard",
        }
    else:
        cargo_zone_dict = _zone_to_dict(cargo_zone)

    # Environmental data from request
    env_dict = {
        "weather_condition": req.weather_condition,
        "wind_speed_kmh": req.wind_speed_kmh,
        "visibility_m": req.visibility_m,
        "temperature_c": req.temperature_c,
    }

    # Save environmental data
    env_record = EnvironmentalData(
        mission_id=req.mission_id,
        weather_condition=req.weather_condition,
        wind_speed_kmh=req.wind_speed_kmh,
        visibility_m=req.visibility_m,
        temperature_c=req.temperature_c,
        data_source="Manual",
    )
    db.add(env_record)

    # Fetch all drones
    drones = db.query(Drone).all()
    drone_dicts = [_drone_to_dict(d) for d in drones]

    # Fetch criterion weights
    cw_rows = db.query(CriterionWeight).all()
    weights = {cw.criterion_id: cw.weight_pct / 100.0 for cw in cw_rows}

    # Run evaluation
    result = evaluate(
        drones=drone_dicts,
        mission=_mission_to_dict(mission),
        env=env_dict,
        cargo_zone=cargo_zone_dict,
        weights=weights,
        operator_available=req.operator_available,
    )

    # Create decision log
    rec = result["recommended_drone"]
    log = DecisionLog(
        mission_id=req.mission_id,
        recommended_drone_id=rec["drone_id"] if rec else None,
        recommended_drone_name=rec["drone_name"] if rec else None,
        recommended_score=rec["total_score"] if rec else None,
        score_breakdown=rec["breakdown"] if rec else None,
        ranked_drones=[
            {"drone_id": r["drone_id"], "drone_name": r["drone_name"], "total_score": r["total_score"], "breakdown": r["breakdown"]}
            for r in result["ranked_drones"]
        ],
        rejected_drones=result["rejected_drones"],
        safety_alerts=result["safety_alerts"],
        operator_id=mission.operator_id,
    )
    db.add(log)

    # Create safety alert records
    for alert_msg in result["safety_alerts"]:
        severity = "Critical" if "Critical" in alert_msg else ("Warning" if "⚠️" in alert_msg else "Info")
        alert = SafetyAlert(
            mission_id=req.mission_id,
            severity=severity,
            description=alert_msg,
        )
        db.add(alert)

    db.commit()
    db.refresh(log)

    return EvaluationResult(
        mission_id=req.mission_id,
        recommended_drone=rec,
        ranked_drones=result["ranked_drones"],
        rejected_drones=result["rejected_drones"],
        safety_alerts=result["safety_alerts"],
        log_id=log.log_id,
    )


# ───────── POST /decisions/override ─────────

@router.post("/override", response_model=DecisionLogOut)
def override_decision(req: OverrideRequest, db: Session = Depends(get_db)):
    log = db.query(DecisionLog).filter(DecisionLog.log_id == req.log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Decision log not found")
    if not req.override_reason.strip():
        raise HTTPException(status_code=422, detail="Override reason is mandatory")

    log.override = True
    log.override_drone_id = req.override_drone_id
    log.override_reason = req.override_reason
    log.operator_id = req.operator_id or log.operator_id

    # Update mission assigned drone
    mission = db.query(Mission).filter(Mission.mission_id == log.mission_id).first()
    if mission:
        mission.assigned_drone_id = req.override_drone_id
        mission.status = "Scheduled"

    log.confirmed = True
    db.commit()
    db.refresh(log)
    return log


# ───────── POST /decisions/confirm ─────────

@router.post("/confirm", response_model=DecisionLogOut)
def confirm_decision(req: ConfirmRequest, db: Session = Depends(get_db)):
    log = db.query(DecisionLog).filter(DecisionLog.log_id == req.log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Decision log not found")

    log.confirmed = True
    log.operator_id = req.operator_id or log.operator_id

    # Update mission assigned drone with recommended drone
    mission = db.query(Mission).filter(Mission.mission_id == log.mission_id).first()
    if mission and log.recommended_drone_id:
        mission.assigned_drone_id = log.recommended_drone_id
        mission.status = "Scheduled"

    db.commit()
    db.refresh(log)
    return log


# ───────── GET /decisions/logs ─────────

@router.get("/logs", response_model=List[DecisionLogOut])
def list_decision_logs(db: Session = Depends(get_db)):
    return db.query(DecisionLog).order_by(DecisionLog.created_at.desc()).all()


@router.get("/logs/{log_id}", response_model=DecisionLogOut)
def get_decision_log(log_id: str, db: Session = Depends(get_db)):
    log = db.query(DecisionLog).filter(DecisionLog.log_id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Decision log not found")
    return log


# ───────── GET /decisions/alerts ─────────

@router.get("/alerts", response_model=List[SafetyAlertOut])
def list_alerts(db: Session = Depends(get_db)):
    return db.query(SafetyAlert).order_by(SafetyAlert.created_at.desc()).all()
