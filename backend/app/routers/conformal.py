from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..database import get_db
from ..conformal import get_q_state

router = APIRouter()

@router.get("/conformal/state")
async def conformal_state(sensor_id: str, db: AsyncSession = Depends(get_db)):
    q = await get_q_state(db, sensor_id)
    return {"sensor_id": sensor_id, "q_value": q, "corrected_width_delta": q*2, "alpha": 0.1}

@router.post("/conformal/reset")
async def reset_conformal(sensor_id: str, db: AsyncSession = Depends(get_db)):
    from .. import models
    result = await db.execute(select(models.ConformalState).filter_by(sensor_id=sensor_id))
    state = result.scalars().first()
    if state: state.q_value = 0; await db.commit()
    return {"reset": True, "sensor_id": sensor_id}