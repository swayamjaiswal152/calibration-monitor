import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app import models
from app.worker import check_sensors


@pytest.fixture
def session():
    # In-memory SQLite that persists across connections within the test
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        yield db
    finally:
        db.close()


def _add_pair(db, sensor_id, pred, lower, upper, y_true, t):
    f = models.Forecast(sensor_id=sensor_id, y_pred=pred, y_lower=lower, y_upper=upper, time=t)
    db.add(f)
    db.flush()
    db.add(models.Actual(forecast_id=f.id, sensor_id=sensor_id, y_true=y_true, time=t))
    db.flush()


def test_drift_sensor_persists_alert_with_is_active(session):
    db = session
    t0 = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    # "bad" sensor: every actual falls far outside its interval -> 0% coverage
    for i in range(10):
        _add_pair(db, "bad", pred=25, lower=21, upper=29, y_true=40,
                  t=t0 + datetime.timedelta(hours=i))
    # "good" sensor: every actual is inside its interval -> 100% coverage
    for i in range(10):
        _add_pair(db, "good", pred=25, lower=21, upper=29, y_true=25,
                  t=t0 + datetime.timedelta(hours=i))
    db.commit()

    published = []
    drifted = check_sensors(db, publish=lambda ch, msg: published.append((ch, msg)))

    # Only the bad sensor should be flagged
    assert drifted == ["bad"]

    alerts = db.query(models.Alert).all()
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.sensor_id == "bad"
    assert alert.coverage == 0.0
    # Regression guard: the worker's raw INSERT omits is_active, so it must be
    # filled by the column's server_default. Previously this raised a
    # NOT NULL violation and the alert was silently lost.
    assert alert.is_active is True

    # The good sensor still emits a metrics update but no alert event
    events = [ch for ch, _ in published]
    assert "metrics_channel" in events


def test_no_alert_when_all_calibrated(session):
    db = session
    t0 = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    for i in range(10):
        _add_pair(db, "good", pred=25, lower=21, upper=29, y_true=25,
                  t=t0 + datetime.timedelta(hours=i))
    db.commit()

    drifted = check_sensors(db, publish=lambda ch, msg: None)

    assert drifted == []
    assert db.query(models.Alert).count() == 0
