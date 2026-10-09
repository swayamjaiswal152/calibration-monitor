from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from ..database import get_db
from ..conformal import get_q_state

router = APIRouter()

@router.get("/metrics")
async def get_metrics(sensor_id: str, window: int = 168, db: AsyncSession = Depends(get_db)):
    # FIX: Do aggregation in DB, not Pandas. Order by TIME DESC for out-of-order data
    q = await get_q_state(db, sensor_id)
    result = await db.execute(text("""
        SELECT
            AVG(CASE WHEN a.y_true BETWEEN f.y_lower AND f.y_upper THEN 1 ELSE 0 END) as picp,
            AVG(CASE WHEN a.y_true BETWEEN f.y_lower - :q AND f.y_upper + :q THEN 1 ELSE 0 END) as picp_corrected,
            AVG(ABS(a.y_true - f.y_pred)) as mae,
            AVG(f.y_upper - f.y_lower) as mpiw
        FROM (SELECT * FROM forecasts WHERE sensor_id = :sid ORDER BY time DESC LIMIT :window) f
        JOIN actuals a ON a.forecast_id = f.id
    """), {"sid": sensor_id, "window": window, "q": q})
    row = result.first()
    if not row or row._mapping["picp"] is None:
        return {"picp": 1.0, "picp_corrected": 1.0, "mae": 0, "mpiw": 0, "winkler": 0, "q_value": q}
    m = row._mapping
    return {
        "picp": float(m["picp"]),
        "picp_corrected": float(m["picp_corrected"]),
        "mae": float(m["mae"]),
        "mpiw": float(m["mpiw"]),
        "winkler": 0,
        "q_value": q,
    }

@router.get("/alerts")
async def get_alerts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT * FROM alerts ORDER BY id DESC LIMIT 50"))
    return [dict(r._mapping) for r in result]