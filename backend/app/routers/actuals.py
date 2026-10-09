# actuals.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..conformal import update_conformal
from .. import models, schemas

router = APIRouter()
@router.post("/actuals")
async def create_actual(payload: schemas.ActualCreate, db: AsyncSession = Depends(get_db)):
    forecast = await db.get(models.Forecast, payload.forecast_id)
    if forecast is None:
        raise HTTPException(status_code=404, detail="forecast_id not found")
    a = models.Actual(**payload.model_dump())
    db.add(a)
    await db.commit()
    await db.refresh(a)
    # Online adaptive-conformal update: adjust q from this observation's coverage
    await update_conformal(db, a.sensor_id, a.y_true, forecast.y_lower, forecast.y_upper)
    return a