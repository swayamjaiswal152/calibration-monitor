import datetime

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app import models
from app.main import app


@pytest_asyncio.fixture
async def client():
    # In-memory aiosqlite shared across the connection pool for the test's lifetime
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, expire_on_commit=False)

    # Seed: "bad" sensor never covered (0% PICP), "good" sensor always covered
    t0 = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    async with Session() as db:
        for i in range(5):
            bad = models.Forecast(sensor_id="bad", y_pred=25, y_lower=21, y_upper=29,
                                  time=t0 + datetime.timedelta(hours=i))
            db.add(bad)
            await db.flush()
            db.add(models.Actual(forecast_id=bad.id, sensor_id="bad", y_true=40,
                                 time=t0 + datetime.timedelta(hours=i)))
            good = models.Forecast(sensor_id="good", y_pred=25, y_lower=21, y_upper=29,
                                   time=t0 + datetime.timedelta(hours=i))
            db.add(good)
            await db.flush()
            db.add(models.Actual(forecast_id=good.id, sensor_id="good", y_true=25,
                                 time=t0 + datetime.timedelta(hours=i)))
        await db.commit()

    async def override_get_db():
        async with Session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_metrics_endpoint_exposes_per_sensor_gauges(client):
    resp = await client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]
    body = resp.text

    # Gauge families are declared with HELP/TYPE even before any sample
    assert "calibration_picp" in body
    assert "calibration_mpiw" in body

    # Per-sensor labeled samples are present with correct coverage
    assert 'calibration_picp{sensor_id="good"} 1.0' in body
    assert 'calibration_picp{sensor_id="bad"} 0.0' in body
    # 5 matched pairs per sensor in the window
    assert 'calibration_window_samples{sensor_id="good"} 5.0' in body
