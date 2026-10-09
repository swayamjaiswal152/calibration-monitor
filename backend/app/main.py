import os
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from .database import Base, async_engine
from .routers import forecasts, actuals, metrics, simulate, conformal, prometheus
from .websocket_manager import manager

# Lightweight idempotent migrations run on startup (project has no Alembic).
# create_all() only creates missing tables; it will NOT add a column to an
# existing table, so backfill schema changes here.
MIGRATIONS = [
    "ALTER TABLE actuals ADD COLUMN IF NOT EXISTS forecast_id INTEGER REFERENCES forecasts(id)",
    "CREATE INDEX IF NOT EXISTS ix_actuals_forecast_id ON actuals (forecast_id)",
    # Ensure raw-SQL inserts (the worker) get a value for is_active
    "ALTER TABLE alerts ALTER COLUMN is_active SET DEFAULT true",
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables, then apply idempotent migrations for existing databases
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        for stmt in MIGRATIONS:
            await conn.execute(text(stmt))
    # On single-instance deploys (e.g. Render free tier) there is no separate
    # worker container, so optionally run the drift loop as a daemon thread.
    # The worker's Redis lock keeps it single-runner even if this is ever scaled.
    if os.getenv("RUN_WORKER_IN_PROCESS", "").lower() in ("1", "true", "yes"):
        from .worker import run_loop
        threading.Thread(target=run_loop, daemon=True, name="drift-worker").start()
        print("[API] In-process drift worker started (RUN_WORKER_IN_PROCESS)")
    yield

app = FastAPI(title="Forecast Calibration Monitor - Stateless API", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(forecasts.router, prefix="/api/v1")
app.include_router(actuals.router, prefix="/api/v1")
app.include_router(metrics.router, prefix="/api/v1")
app.include_router(simulate.router, prefix="/api/v1")
app.include_router(conformal.router, prefix="/api/v1")
# Prometheus scrape target mounted at root (/metrics) per convention, no /api/v1 prefix
app.include_router(prometheus.router)

@app.websocket("/ws/metrics")
async def ws_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text() # keep alive
    except:
        manager.disconnect(ws)

@app.get("/health")
def health(): return {"status": "ok", "mode": "stateless-api"}

# NO MORE APScheduler here. Worker.py handles it.