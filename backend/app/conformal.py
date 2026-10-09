# Adaptive Conformal Prediction - Online Quantile Correction
# Paper: Gibbs & Candes 2021 - Adaptive Conformal Inference
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from . import models

ALPHA = 0.1  # 90% interval
ETA = 0.05   # learning rate

async def get_q_state(db: AsyncSession, sensor_id: str) -> float:
    # Read-only: never mutate on a GET. Absent state just means q=0 (uncorrected).
    result = await db.execute(select(models.ConformalState).filter_by(sensor_id=sensor_id))
    state = result.scalars().first()
    return state.q_value if state else 0.0

async def update_conformal(db: AsyncSession, sensor_id: str, y_true: float, y_lower: float, y_upper: float):
    """ q_{t+1} = q_t + eta * (err - alpha) """
    result = await db.execute(select(models.ConformalState).filter_by(sensor_id=sensor_id))
    state = result.scalars().first()
    if not state:
        state = models.ConformalState(sensor_id=sensor_id, q_value=0.0)
        db.add(state)
        await db.flush()
    
    err = 0 if (y_lower <= y_true <= y_upper) else 1
    # If miscovered, increase q (widen intervals), else shrink
    state.q_value += ETA * (err - ALPHA)
    # Keep q bounded
    state.q_value = max(-2.0, min(8.0, state.q_value))
    await db.commit()
    return state.q_value

def get_corrected_interval(y_pred: float, y_lower: float, y_upper: float, q: float):
    # Apply correction symmetrically
    return y_lower - q, y_upper + q