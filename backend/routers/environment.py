"""
Environmental data endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import EnvironmentalData
from schemas import EnvironmentalDataCreate, EnvironmentalDataOut

router = APIRouter(prefix="/environment", tags=["Environment"])


@router.get("/", response_model=List[EnvironmentalDataOut])
def list_env_data(db: Session = Depends(get_db)):
    return db.query(EnvironmentalData).order_by(EnvironmentalData.recorded_at.desc()).limit(50).all()


@router.post("/", response_model=EnvironmentalDataOut)
def create_env_data(payload: EnvironmentalDataCreate, db: Session = Depends(get_db)):
    env = EnvironmentalData(**payload.model_dump())
    db.add(env)
    db.commit()
    db.refresh(env)
    return env
