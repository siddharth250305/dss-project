"""
Settings / Criterion Weights endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import CriterionWeight
from schemas import CriterionWeightOut, CriterionWeightUpdate

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/weights", response_model=List[CriterionWeightOut])
def list_weights(db: Session = Depends(get_db)):
    return db.query(CriterionWeight).order_by(CriterionWeight.criterion_id).all()


@router.put("/weights", response_model=List[CriterionWeightOut])
def update_weights(updates: List[CriterionWeightUpdate], db: Session = Depends(get_db)):
    for u in updates:
        cw = db.query(CriterionWeight).filter(CriterionWeight.criterion_id == u.criterion_id).first()
        if not cw:
            raise HTTPException(status_code=404, detail=f"Criterion {u.criterion_id} not found")
        cw.weight_pct = u.weight_pct
    db.commit()
    return db.query(CriterionWeight).order_by(CriterionWeight.criterion_id).all()
