"""
Drone CRUD endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List

from database import get_db
from models import Drone
from schemas import DroneCreate, DroneUpdate, DroneOut

router = APIRouter(prefix="/drones", tags=["Drones"])


@router.get("/", response_model=List[DroneOut])
def list_drones(db: Session = Depends(get_db)):
    return db.query(Drone).all()


@router.get("/{drone_id}", response_model=DroneOut)
def get_drone(drone_id: str, db: Session = Depends(get_db)):
    drone = db.query(Drone).filter(Drone.drone_id == drone_id).first()
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")
    return drone


@router.post("/", response_model=DroneOut)
def create_drone(payload: DroneCreate, db: Session = Depends(get_db)):
    drone = Drone(**payload.model_dump(), last_updated=datetime.now(timezone.utc))
    db.add(drone)
    db.commit()
    db.refresh(drone)
    return drone


@router.put("/{drone_id}", response_model=DroneOut)
def update_drone(drone_id: str, payload: DroneUpdate, db: Session = Depends(get_db)):
    drone = db.query(Drone).filter(Drone.drone_id == drone_id).first()
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(drone, key, value)
    drone.last_updated = datetime.now(timezone.utc)
    db.commit()
    db.refresh(drone)
    return drone
