from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import random
from ..database import get_db
from ..conformal import update_conformal
from .. import models
router = APIRouter()

@router.post("/simulate/drift")
async def inject_drift(sensor_id: str = "sensor-1", drift: float = 5.0, n: int = 50, db: AsyncSession = Depends(get_db)):
    for _ in range(n):
        pred = random.uniform(20,30)
        lower, upper = pred - 4, pred + 4
        f = models.Forecast(sensor_id=sensor_id, y_pred=pred, y_lower=lower, y_upper=upper)
        db.add(f); await db.flush()
        y_true = pred + drift + random.uniform(-1, 1)
        a = models.Actual(forecast_id=f.id, sensor_id=sensor_id, y_true=y_true)
        db.add(a)
        await db.flush()
        # Drive the adaptive-conformal state so q reacts to the injected drift
        await update_conformal(db, sensor_id, y_true, lower, upper)
    await db.commit()
    return {"injected": n, "drift": drift, "expected_coverage": max(0, 0.9 - drift*0.12)}

@router.post("/simulate/whatif")
def what_if(drift: float, sensor_id: str = "sensor-1"):
    # No DB write, just preview calculation - for slider
    preview_coverage = max(0, min(1, 0.9 - (drift * 0.13)))
    detection_delay = int(10 + drift*2) if preview_coverage < 0.85 else 999
    will_alert = preview_coverage < 0.85
    return {
        "drift": drift,
        "predicted_coverage": round(preview_coverage, 3),
        "will_trigger_alert": will_alert,
        "estimated_detection_delay_mins": detection_delay
    }