"""
Pydantic schemas for request validation and response serialisation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ──────────────────── Drone ────────────────────

class DroneBase(BaseModel):
    drone_name: str
    flight_radius_km: float = Field(gt=0)
    battery_endurance_min: int = Field(gt=0)
    payload_capacity_kg: float = Field(ge=0)
    camera_quality: str = "HD"
    night_vision: bool = False
    thermal_sensor: bool = False
    max_flight_height_m: int = Field(gt=0)
    wind_resistance_kmh: float = Field(gt=0)
    charging_time_min: int = Field(gt=0)
    maintenance_status: str = "Good"
    regulatory_compliant: bool = True
    reliability_score: float = Field(ge=0, le=1, default=0.9)
    daily_missions_done: int = Field(ge=0, default=0)

class DroneCreate(DroneBase):
    pass

class DroneUpdate(BaseModel):
    drone_name: Optional[str] = None
    flight_radius_km: Optional[float] = None
    battery_endurance_min: Optional[int] = None
    payload_capacity_kg: Optional[float] = None
    camera_quality: Optional[str] = None
    night_vision: Optional[bool] = None
    thermal_sensor: Optional[bool] = None
    max_flight_height_m: Optional[int] = None
    wind_resistance_kmh: Optional[float] = None
    charging_time_min: Optional[int] = None
    maintenance_status: Optional[str] = None
    regulatory_compliant: Optional[bool] = None
    reliability_score: Optional[float] = None
    daily_missions_done: Optional[int] = None

class DroneOut(DroneBase):
    drone_id: str
    last_updated: Optional[datetime] = None
    class Config:
        from_attributes = True


# ──────────────────── Cargo Zone ────────────────────

class CargoZoneBase(BaseModel):
    zone_name: str
    location_description: str = ""
    distance_from_base_km: float = Field(gt=0)
    obstacle_density: str = "Low"
    safety_risk_level: str = "Low"
    cargo_priority: str = "Standard"
    inspection_requirements: str = ""

class CargoZoneCreate(CargoZoneBase):
    pass

class CargoZoneOut(CargoZoneBase):
    zone_id: str
    class Config:
        from_attributes = True


# ──────────────────── Mission ────────────────────

class MissionBase(BaseModel):
    mission_type: str
    urgency_level: str = "Medium"
    cargo_zone_id: Optional[str] = None
    required_distance_km: float = Field(gt=0)
    required_height_m: int = Field(gt=0)
    requires_night_vision: bool = False
    requires_thermal: bool = False
    operator_id: Optional[str] = None
    scheduled_time: Optional[datetime] = None

class MissionCreate(MissionBase):
    pass

class MissionUpdate(BaseModel):
    mission_type: Optional[str] = None
    urgency_level: Optional[str] = None
    cargo_zone_id: Optional[str] = None
    required_distance_km: Optional[float] = None
    required_height_m: Optional[int] = None
    requires_night_vision: Optional[bool] = None
    requires_thermal: Optional[bool] = None
    operator_id: Optional[str] = None
    assigned_drone_id: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    status: Optional[str] = None

class MissionOut(MissionBase):
    mission_id: str
    assigned_drone_id: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True


# ──────────────────── Environmental Data ────────────────────

class EnvironmentalDataBase(BaseModel):
    weather_condition: str = "Clear"
    wind_speed_kmh: float = Field(ge=0, default=0.0)
    visibility_m: int = Field(gt=0, default=10000)
    temperature_c: float = 20.0
    data_source: str = "Manual"

class EnvironmentalDataCreate(EnvironmentalDataBase):
    mission_id: Optional[str] = None

class EnvironmentalDataOut(EnvironmentalDataBase):
    env_id: str
    mission_id: Optional[str] = None
    recorded_at: Optional[datetime] = None
    class Config:
        from_attributes = True


# ──────────────────── Decision Evaluation Request ────────────────────

class EvaluationRequest(BaseModel):
    mission_id: str
    weather_condition: str = "Clear"
    wind_speed_kmh: float = 0.0
    visibility_m: int = 10000
    temperature_c: float = 20.0
    operator_available: bool = True


class EvaluationResult(BaseModel):
    mission_id: str
    recommended_drone: Optional[Dict[str, Any]] = None
    ranked_drones: List[Dict[str, Any]] = []
    rejected_drones: List[Dict[str, Any]] = []
    safety_alerts: List[str] = []
    log_id: Optional[str] = None


# ──────────────────── Decision Log ────────────────────

class DecisionLogOut(BaseModel):
    log_id: str
    mission_id: str
    recommended_drone_id: Optional[str] = None
    recommended_drone_name: Optional[str] = None
    recommended_score: Optional[float] = None
    score_breakdown: Optional[Dict[str, Any]] = None
    ranked_drones: Optional[List[Dict[str, Any]]] = None
    rejected_drones: Optional[List[Dict[str, Any]]] = None
    safety_alerts: Optional[List[str]] = None
    operator_id: Optional[str] = None
    override: bool = False
    override_drone_id: Optional[str] = None
    override_reason: Optional[str] = None
    confirmed: bool = False
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True


class OverrideRequest(BaseModel):
    log_id: str
    override_drone_id: str
    override_reason: str
    operator_id: Optional[str] = None


class ConfirmRequest(BaseModel):
    log_id: str
    operator_id: Optional[str] = None


# ──────────────────── Safety Alert ────────────────────

class SafetyAlertOut(BaseModel):
    alert_id: str
    mission_id: Optional[str] = None
    severity: str
    description: str
    rule_triggered: Optional[str] = None
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True


# ──────────────────── Criterion Weight ────────────────────

class CriterionWeightOut(BaseModel):
    criterion_id: str
    criterion_name: str
    weight_pct: float
    category: str
    description: str = ""
    class Config:
        from_attributes = True

class CriterionWeightUpdate(BaseModel):
    criterion_id: str
    weight_pct: float
