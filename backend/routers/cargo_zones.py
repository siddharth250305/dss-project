"""
Cargo Zone CRUD endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import CargoZone
from schemas import CargoZoneCreate, CargoZoneOut

router = APIRouter(prefix="/cargo-zones", tags=["Cargo Zones"])


@router.get("/", response_model=List[CargoZoneOut])
def list_cargo_zones(db: Session = Depends(get_db)):
    return db.query(CargoZone).all()


@router.get("/{zone_id}", response_model=CargoZoneOut)
def get_cargo_zone(zone_id: str, db: Session = Depends(get_db)):
    zone = db.query(CargoZone).filter(CargoZone.zone_id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Cargo zone not found")
    return zone


@router.post("/", response_model=CargoZoneOut)
def create_cargo_zone(payload: CargoZoneCreate, db: Session = Depends(get_db)):
    zone = CargoZone(**payload.model_dump())
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone
