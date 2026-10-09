from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from prometheus_client import CollectorRegistry, Gauge, generate_latest, CONTENT_TYPE_LATEST
from ..database import get_db
from ..conformal import get_q_state

router = APIRouter()

# Per-sensor calibration metrics are computed at scrape time against the same
# 168h rolling window the REST API and worker use, so Prometheus, the dashboard
# and the drift worker never disagree. A fresh registry per scrape keeps series
# from going stale and avoids duplicate-series errors under multiple uvicorn
# workers (each worker scrapes independently; there is no shared process state).
SCRAPE_SQL = """
    SELECT
        AVG(CASE WHEN a.y_true BETWEEN f.y_lower AND f.y_upper THEN 1 ELSE 0 END) as picp,
        AVG(ABS(a.y_true - f.y_pred)) as mae,
        AVG(f.y_upper - f.y_lower) as mpiw,
        COUNT(*) as n
    FROM (SELECT * FROM forecasts WHERE sensor_id = :sid ORDER BY time DESC LIMIT 168) f
    JOIN actuals a ON a.forecast_id = f.id
"""


@router.get("/metrics")
async def prometheus_metrics(db: AsyncSession = Depends(get_db)):
    registry = CollectorRegistry()
    picp_g = Gauge("calibration_picp", "Prediction Interval Coverage Probability (168h window)", ["sensor_id"], registry=registry)
    mae_g = Gauge("calibration_mae", "Mean Absolute Error (168h window)", ["sensor_id"], registry=registry)
    mpiw_g = Gauge("calibration_mpiw", "Mean Prediction Interval Width (168h window)", ["sensor_id"], registry=registry)
    q_g = Gauge("calibration_conformal_q", "Adaptive conformal correction term", ["sensor_id"], registry=registry)
    n_g = Gauge("calibration_window_samples", "Matched forecast/actual pairs in window", ["sensor_id"], registry=registry)

    sensors = [row[0] for row in (await db.execute(text("SELECT DISTINCT sensor_id FROM forecasts"))).fetchall()]
    for sid in sensors:
        row = (await db.execute(text(SCRAPE_SQL), {"sid": sid})).first()
        q = await get_q_state(db, sid)
        q_g.labels(sensor_id=sid).set(q)
        if not row or row._mapping["picp"] is None:
            continue
        m = row._mapping
        picp_g.labels(sensor_id=sid).set(float(m["picp"]))
        mae_g.labels(sensor_id=sid).set(float(m["mae"]))
        mpiw_g.labels(sensor_id=sid).set(float(m["mpiw"]))
        n_g.labels(sensor_id=sid).set(int(m["n"]))

    return Response(content=generate_latest(registry), media_type=CONTENT_TYPE_LATEST)
