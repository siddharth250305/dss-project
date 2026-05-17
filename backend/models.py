"""
SQLAlchemy ORM models for the Cargo-Aware Drone Selection DSS.
Covers: Drone, Mission, CargoZone, EnvironmentalData, TelemetryData,
        DecisionLog, SafetyAlert, CriterionWeight, User.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Float, Integer, Boolean, Text, Enum as SAEnum,
    DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship

from database import Base


def _uuid():
    return str(uuid.uuid4())[:8].upper()


# ──────────────────────────── Drone ────────────────────────────

class Drone(Base):
    __tablename__ = "drones"

    drone_id = Column(String, primary_key=True, default=_uuid)
    drone_name = Column(String, nullable=False)
    flight_radius_km = Column(Float, nullable=False)
    battery_endurance_min = Column(Integer, nullable=False)
    payload_capacity_kg = Column(Float, nullable=False)
    camera_quality = Column(String, nullable=False, default="HD")          # SD, HD, 4K
    night_vision = Column(Boolean, default=False)
    thermal_sensor = Column(Boolean, default=False)
    max_flight_height_m = Column(Integer, nullable=False)
    wind_resistance_kmh = Column(Float, nullable=False)
    charging_time_min = Column(Integer, nullable=False)
    maintenance_status = Column(String, nullable=False, default="Good")    # Good, Scheduled, Poor, Grounded
    regulatory_compliant = Column(Boolean, default=True)
    reliability_score = Column(Float, default=0.9)
    daily_missions_done = Column(Integer, default=0)
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# ──────────────────────────── Cargo Zone ────────────────────────────

class CargoZone(Base):
    __tablename__ = "cargo_zones"

    zone_id = Column(String, primary_key=True, default=_uuid)
    zone_name = Column(String, nullable=False)
    location_description = Column(Text, default="")
    distance_from_base_km = Column(Float, nullable=False)
    obstacle_density = Column(String, nullable=False, default="Low")       # Low, Medium, High
    safety_risk_level = Column(String, nullable=False, default="Low")      # Low, Medium, High, Critical
    cargo_priority = Column(String, nullable=False, default="Standard")    # Standard, Priority, Hazardous
    inspection_requirements = Column(Text, default="")


# ──────────────────────────── Mission ────────────────────────────

class Mission(Base):
    __tablename__ = "missions"

    mission_id = Column(String, primary_key=True, default=_uuid)
    mission_type = Column(String, nullable=False)               # Inspection, Surveillance, Monitoring, Emergency
    urgency_level = Column(String, nullable=False, default="Medium")
    cargo_zone_id = Column(String, ForeignKey("cargo_zones.zone_id"), nullable=True)
    required_distance_km = Column(Float, nullable=False)
    required_height_m = Column(Integer, nullable=False)
    requires_night_vision = Column(Boolean, default=False)
    requires_thermal = Column(Boolean, default=False)
    operator_id = Column(String, nullable=True)
    assigned_drone_id = Column(String, ForeignKey("drones.drone_id"), nullable=True)
    scheduled_time = Column(DateTime, nullable=True)
    status = Column(String, default="Draft")                    # Draft, Scheduled, Active, Completed, Cancelled
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# ──────────────────────────── Environmental Data ────────────────────────────

class EnvironmentalData(Base):
    __tablename__ = "environmental_data"

    env_id = Column(String, primary_key=True, default=_uuid)
    mission_id = Column(String, ForeignKey("missions.mission_id"), nullable=True)
    weather_condition = Column(String, nullable=False, default="Clear")    # Clear, Cloudy, Rain, Heavy Rain, Storm
    wind_speed_kmh = Column(Float, nullable=False, default=0.0)
    visibility_m = Column(Integer, nullable=False, default=10000)
    temperature_c = Column(Float, nullable=False, default=20.0)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    data_source = Column(String, default="Manual")                         # Manual, Simulated, API


# ──────────────────────────── Telemetry (Simulated) ────────────────────────────

class TelemetryData(Base):
    __tablename__ = "telemetry_data"

    telemetry_id = Column(String, primary_key=True, default=_uuid)
    drone_id = Column(String, ForeignKey("drones.drone_id"), nullable=False)
    battery_level_pct = Column(Float, default=100.0)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    altitude_m = Column(Float, nullable=True)
    speed_kmh = Column(Float, nullable=True)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# ──────────────────────────── Decision Log ────────────────────────────

class DecisionLog(Base):
    __tablename__ = "decision_logs"

    log_id = Column(String, primary_key=True, default=_uuid)
    mission_id = Column(String, ForeignKey("missions.mission_id"), nullable=False)
    recommended_drone_id = Column(String, nullable=True)
    recommended_drone_name = Column(String, nullable=True)
    recommended_score = Column(Float, nullable=True)
    score_breakdown = Column(JSON, nullable=True)           # dict of criterion → score
    ranked_drones = Column(JSON, nullable=True)             # list of {drone_id, name, score}
    rejected_drones = Column(JSON, nullable=True)           # list of {drone_id, name, reasons[]}
    safety_alerts = Column(JSON, nullable=True)             # list of alert strings
    operator_id = Column(String, nullable=True)
    override = Column(Boolean, default=False)
    override_drone_id = Column(String, nullable=True)
    override_reason = Column(Text, nullable=True)
    confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# ──────────────────────────── Safety Alert ────────────────────────────

class SafetyAlert(Base):
    __tablename__ = "safety_alerts"

    alert_id = Column(String, primary_key=True, default=_uuid)
    mission_id = Column(String, ForeignKey("missions.mission_id"), nullable=True)
    severity = Column(String, nullable=False, default="Warning")       # Info, Warning, Critical
    description = Column(Text, nullable=False)
    rule_triggered = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# ──────────────────────────── Criterion Weight ────────────────────────────

class CriterionWeight(Base):
    __tablename__ = "criterion_weights"

    criterion_id = Column(String, primary_key=True)
    criterion_name = Column(String, nullable=False)
    weight_pct = Column(Float, nullable=False)           # e.g. 8.0 for 8%
    category = Column(String, nullable=False)             # Capability, Mission, Environmental, Safety, Operational
    description = Column(Text, default="")


# ──────────────────────────── User (simple role selection) ────────────────────────────

class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, default=_uuid)
    username = Column(String, nullable=False, unique=True)
    role = Column(String, nullable=False, default="Operator")   # Operator, Supervisor, Maintenance, Admin
