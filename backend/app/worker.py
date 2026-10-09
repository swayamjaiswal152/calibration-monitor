import os
import time
import json
from redis import Redis
from sqlalchemy import text
from .database import SyncSessionLocal
from .slack import send_slack_alert

# This runs as a SEPARATE container (`python -m app.worker`) in Docker Compose,
# or as an in-process daemon thread inside the API when RUN_WORKER_IN_PROCESS is
# set (single-instance free-tier deploys). The Redis lock keeps it single-runner
# either way.

r = Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"), decode_responses=True)
TARGET = 0.9
EPSILON = 0.05

def is_drift(picp: float) -> bool:
    return picp < (TARGET - EPSILON)

METRICS_SQL = """
    SELECT
        AVG(CASE WHEN a.y_true BETWEEN f.y_lower AND f.y_upper THEN 1 ELSE 0 END) as picp,
        AVG(ABS(a.y_true - f.y_pred)) as mae,
        AVG(f.y_upper - f.y_lower) as mpiw
    FROM (SELECT * FROM forecasts WHERE sensor_id = :sid ORDER BY time DESC LIMIT 168) f
    JOIN actuals a ON a.forecast_id = f.id
"""

def check_sensors(db, publish=None):
    """Compute metrics per sensor, publish updates, and persist alerts on drift.

    Pure DB work with an injectable `publish` callable so it can be unit-tested
    without Redis. Returns the list of sensor_ids that drifted.
    """
    drifted = []
    sensors = [row[0] for row in db.execute(text("SELECT DISTINCT sensor_id FROM forecasts")).fetchall()]
    for sid in sensors:
        # FIX 3: Compute in SQL, not Pandas. Order by TIME not ID
        result = db.execute(text(METRICS_SQL), {"sid": sid}).first()

        if not result or result._mapping["picp"] is None:
            continue

        m = {"picp": float(result._mapping["picp"]), "mae": float(result._mapping["mae"]), "mpiw": float(result._mapping["mpiw"])}

        # FIX 2: Publish to Redis, not in-memory list
        if publish:
            publish("metrics_channel", json.dumps({"event": "metrics_update", "data": {**m, "sensor_id": sid}}))

        if is_drift(m["picp"]):
            if publish:
                publish("metrics_channel", json.dumps({"event": "alert", "data": {**m, "sensor_id": sid}}))
            send_slack_alert(sid, m["picp"])
            # Save alert to DB (is_active relies on the column's server_default)
            db.execute(text("INSERT INTO alerts (sensor_id, coverage, message) VALUES (:sid, :cov, :msg)"),
                       {"sid": sid, "cov": m["picp"], "msg": f"Coverage {m['picp']:.2%} < 90% for {sid}"})
            db.commit()
            drifted.append(sid)
            print(f"[WORKER] Drift detected on {sid}: {m['picp']:.2%}")
    return drifted

def run_loop():
    print("[WORKER] Started. Waiting for Redis lock...")
    while True:
        # Distributed Lock: Ensures only 1 worker runs even if you scale worker to 3 replicas
        lock_acquired = r.set("drift_job_lock", "1", nx=True, ex=15)
        if not lock_acquired:
            time.sleep(15)
            continue

        db = None
        try:
            db = SyncSessionLocal()
            check_sensors(db, publish=r.publish)
        except Exception as e:
            print(f"[WORKER ERROR] {e}")
        finally:
            if db is not None:
                db.close()
        time.sleep(15)

if __name__ == "__main__":
    run_loop()