# forecasts.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from .. import models, schemas

router = APIRouter()
@router.post("/forecasts")
async def create_forecast(payload: schemas.ForecastCreate, db: AsyncSession = Depends(get_db)):
    f = models.Forecast(**payload.model_dump())
    db.add(f)
    await db.commit()
    await db.refresh(f)
    return f