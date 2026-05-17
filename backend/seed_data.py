"""
Seed data generator — populates the database with realistic simulated
drone fleet (25 drones), cargo zones (12), default criterion weights,
and sample users.
"""
from datetime import datetime, timezone
from database import SessionLocal, engine, Base
from models import (
    Drone, CargoZone, CriterionWeight, User,
    EnvironmentalData, Mission
)


def _now():
    return datetime.now(timezone.utc)


# ────────────── Drones (25) ──────────────

DRONES = [
    # (id, name, radius_km, battery_min, payload_kg, camera, night, thermal, height_m, wind_kmh, charge_min, maint, reg, reliability, daily)
    ("DRN-001", "SkyHawk X1",       18.0, 55, 3.5, "4K",  True,  True,  150, 50.0, 90, "Good",      True,  0.95, 0),
    ("DRN-002", "AeroScout Pro",    15.0, 45, 2.0, "HD",  True,  False, 120, 45.0, 75, "Good",      True,  0.92, 1),
    ("DRN-003", "CargoEye 500",     22.0, 60, 5.0, "4K",  True,  True,  180, 55.0, 110,"Good",      True,  0.97, 0),
    ("DRN-004", "SwiftWing Lite",   10.0, 30, 1.0, "SD",  False, False, 80,  30.0, 45, "Good",      True,  0.88, 2),
    ("DRN-005", "ThermalViper V2",  16.0, 50, 2.5, "HD",  True,  True,  140, 48.0, 80, "Scheduled", True,  0.90, 0),
    ("DRN-006", "PortGuard Max",    20.0, 58, 4.0, "4K",  True,  True,  160, 52.0, 100,"Good",      True,  0.93, 1),
    ("DRN-007", "NightOwl 300",     12.0, 40, 1.5, "HD",  True,  False, 100, 40.0, 60, "Good",      True,  0.89, 0),
    ("DRN-008", "StormBreaker X",   25.0, 65, 6.0, "4K",  True,  True,  200, 65.0, 120,"Good",      True,  0.96, 0),
    ("DRN-009", "Falcon Recon",     14.0, 42, 2.0, "HD",  False, False, 110, 42.0, 70, "Good",      True,  0.87, 3),
    ("DRN-010", "HeavyLifter Pro",  18.0, 48, 8.0, "HD",  False, True,  130, 38.0, 95, "Good",      True,  0.91, 0),
    ("DRN-011", "Specter S1",       13.0, 38, 1.8, "SD",  True,  False, 90,  35.0, 55, "Poor",      True,  0.72, 0),
    ("DRN-012", "ZonePatrol 200",   16.0, 44, 2.2, "HD",  True,  False, 115, 43.0, 65, "Good",      True,  0.90, 1),
    ("DRN-013", "EmergencyFlash",   20.0, 35, 1.0, "4K",  True,  True,  170, 50.0, 50, "Good",      True,  0.94, 0),
    ("DRN-014", "InspectorBot 4K",  11.0, 36, 1.5, "4K",  False, False, 95,  32.0, 55, "Good",      True,  0.86, 2),
    ("DRN-015", "WindRunner 700",   24.0, 62, 4.5, "4K",  True,  True,  190, 60.0, 105,"Good",      True,  0.95, 0),
    ("DRN-016", "MiniScout A",       8.0, 25, 0.5, "SD",  False, False, 60,  25.0, 35, "Good",      True,  0.80, 0),
    ("DRN-017", "CargoDrone C3",    19.0, 52, 5.5, "HD",  True,  True,  155, 47.0, 90, "Scheduled", True,  0.91, 0),
    ("DRN-018", "SurveillancePro",  17.0, 50, 3.0, "4K",  True,  True,  145, 49.0, 85, "Good",      True,  0.93, 1),
    ("DRN-019", "OceanEye 400",     21.0, 56, 3.8, "4K",  True,  True,  165, 54.0, 95, "Good",      True,  0.94, 0),
    ("DRN-020", "PortHopper Mini",   9.0, 28, 1.0, "SD",  False, False, 70,  28.0, 40, "Good",      False, 0.78, 0),
    ("DRN-021", "TitanCargo X5",    26.0, 70, 10.0,"4K",  True,  True,  210, 68.0, 130,"Good",      True,  0.98, 0),
    ("DRN-022", "QuickBird V1",     12.0, 32, 1.2, "HD",  False, False, 85,  34.0, 50, "Grounded",  True,  0.60, 0),
    ("DRN-023", "SafetyHawk 600",   15.0, 46, 2.5, "HD",  True,  False, 125, 44.0, 75, "Good",      True,  0.91, 0),
    ("DRN-024", "DeepScan Thermal", 17.0, 48, 3.0, "HD",  True,  True,  135, 46.0, 80, "Good",      True,  0.92, 1),
    ("DRN-025", "RapidResponse R2", 19.0, 40, 2.0, "4K",  True,  True,  150, 55.0, 60, "Good",      True,  0.93, 0),
]


# ────────────── Cargo Zones (12) ──────────────

CARGO_ZONES = [
    ("CZ-001", "Container Terminal A",    "North dock, container stacking area",        2.5, "High",   "Medium",   "Standard",  "Standard container integrity check"),
    ("CZ-002", "Bulk Cargo Yard B",       "East side bulk storage",                     4.0, "Medium", "Low",      "Standard",  "Surface damage inspection"),
    ("CZ-003", "Hazardous Materials Zone", "Restricted southern perimeter",              3.2, "Low",    "Critical", "Hazardous", "Full thermal and visual inspection required"),
    ("CZ-004", "Reefer Container Row",    "Refrigerated container section, west dock",  1.8, "Medium", "Medium",   "Priority",  "Temperature monitoring, seal integrity"),
    ("CZ-005", "Vehicle Roll-on Area",    "Vehicle loading ramp, pier 5",               5.0, "High",   "Medium",   "Standard",  "Vehicle count and damage assessment"),
    ("CZ-006", "Grain Silo Complex",      "North-east grain storage silos",             6.5, "Low",    "Low",      "Standard",  "Silo level monitoring"),
    ("CZ-007", "Oil & Gas Terminal",      "South-west fuel terminal",                   7.0, "Low",    "High",     "Hazardous", "Leak detection, thermal scan mandatory"),
    ("CZ-008", "Empty Container Depot",   "Central staging area",                       1.2, "Medium", "Low",      "Standard",  "Inventory count verification"),
    ("CZ-009", "Passenger Ferry Dock",    "Ferry terminal, pier 1",                     3.5, "High",   "Medium",   "Priority",  "Security surveillance sweep"),
    ("CZ-010", "Construction Material Bay","South dock, open yard",                     4.5, "High",   "Medium",   "Standard",  "Material pile monitoring"),
    ("CZ-011", "LNG Storage Facility",    "Isolated north-west area",                   8.0, "Low",    "Critical", "Hazardous", "Full perimeter thermal scan"),
    ("CZ-012", "General Warehouse C",     "Central warehouse complex",                  2.0, "Medium", "Low",      "Standard",  "Roof and wall condition check"),
]


# ────────────── Default Criterion Weights (PRD Section 7) ──────────────

CRITERION_WEIGHTS = [
    # Drone Capability (52%)
    ("C-01", "Flight Radius",          8.0,  "Capability",     "Maximum distance the drone can travel from base"),
    ("C-02", "Battery Endurance",      11.0, "Capability",     "Total flight time on a full charge"),
    ("C-03", "Payload Capacity",       6.0,  "Capability",     "Maximum cargo weight"),
    ("C-04", "Camera Quality",         5.0,  "Capability",     "Resolution of onboard camera (SD, HD, 4K)"),
    ("C-05", "Night Vision Support",   4.0,  "Capability",     "Low-light operation capability"),
    ("C-06", "Thermal Sensor",         4.0,  "Capability",     "Thermal imaging sensor availability"),
    ("C-07", "Flight Height Capability",4.0, "Capability",     "Maximum safe altitude"),
    ("C-08", "Wind Resistance Level",  8.0,  "Capability",     "Maximum tolerable wind speed"),
    ("C-09", "Charging Time",          2.0,  "Capability",     "Full recharge duration"),
    # Mission Requirement (20%)
    ("C-10", "Mission Urgency",        8.0,  "Mission",        "Time-criticality of mission"),
    ("C-11", "Cargo Zone Distance",    6.0,  "Mission",        "Distance from base to target zone"),
    ("C-12", "Historical Reliability", 6.0,  "Mission",        "Past mission success rate"),
    # Environmental (15%)
    ("C-13", "Weather Condition",      5.0,  "Environmental",  "Current weather state"),
    ("C-14", "Wind Speed",            7.0,  "Environmental",  "Current wind speed at location"),
    ("C-15", "Obstacle Density",       3.0,  "Environmental",  "Physical obstacles in cargo zone"),
    # Safety (10%)
    ("C-16", "Safety Risk Level",      6.0,  "Safety",         "Overall mission risk classification"),
    ("C-17", "Regulatory Compliance",  4.0,  "Safety",         "Required operating certifications"),
    # Operational (3%)
    ("C-19", "Number of Daily Missions",2.0, "Operational",    "Missions already completed today"),
    ("C-21", "Budget Limitation",      1.0,  "Operational",    "Operating cost relative to budget"),
]


# ────────────── Default Users ──────────────

USERS = [
    ("USR-001", "operator1",     "Operator"),
    ("USR-002", "supervisor1",   "Supervisor"),
    ("USR-003", "maintenance1",  "Maintenance"),
    ("USR-004", "admin1",        "Admin"),
]


def seed_database():
    """Create all tables and insert seed data if the tables are empty."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Seed drones
        if db.query(Drone).count() == 0:
            for d in DRONES:
                db.add(Drone(
                    drone_id=d[0], drone_name=d[1], flight_radius_km=d[2],
                    battery_endurance_min=d[3], payload_capacity_kg=d[4],
                    camera_quality=d[5], night_vision=d[6], thermal_sensor=d[7],
                    max_flight_height_m=d[8], wind_resistance_kmh=d[9],
                    charging_time_min=d[10], maintenance_status=d[11],
                    regulatory_compliant=d[12], reliability_score=d[13],
                    daily_missions_done=d[14], last_updated=_now()
                ))

        # Seed cargo zones
        if db.query(CargoZone).count() == 0:
            for cz in CARGO_ZONES:
                db.add(CargoZone(
                    zone_id=cz[0], zone_name=cz[1], location_description=cz[2],
                    distance_from_base_km=cz[3], obstacle_density=cz[4],
                    safety_risk_level=cz[5], cargo_priority=cz[6],
                    inspection_requirements=cz[7]
                ))

        # Seed criterion weights
        if db.query(CriterionWeight).count() == 0:
            for cw in CRITERION_WEIGHTS:
                db.add(CriterionWeight(
                    criterion_id=cw[0], criterion_name=cw[1],
                    weight_pct=cw[2], category=cw[3], description=cw[4]
                ))

        # Seed users
        if db.query(User).count() == 0:
            for u in USERS:
                db.add(User(user_id=u[0], username=u[1], role=u[2]))

        db.commit()
        print("✅  Seed data loaded successfully.")
    except Exception as e:
        db.rollback()
        print(f"❌  Seeding error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
