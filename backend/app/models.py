from sqlalchemy import String, Float, DateTime, Integer, Boolean, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
import datetime
from .database import Base

class Forecast(Base):
    __tablename__ = "forecasts"
    id: Mapped[int] = mapped_column(primary_key=True)
    time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sensor_id: Mapped[str] = mapped_column(String, index=True)
    y_pred: Mapped[float] = mapped_column(Float)
    y_lower: Mapped[float] = mapped_column(Float)
    y_upper: Mapped[float] = mapped_column(Float)

class Actual(Base):
    __tablename__ = "actuals"
    id: Mapped[int] = mapped_column(primary_key=True)
    forecast_id: Mapped[int] = mapped_column(ForeignKey("forecasts.id"), index=True)
    time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sensor_id: Mapped[str] = mapped_column(String, index=True)
    y_true: Mapped[float] = mapped_column(Float)

class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(primary_key=True)
    time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sensor_id: Mapped[str] = mapped_column(String)
    coverage: Mapped[float] = mapped_column(Float)
    message: Mapped[str] = mapped_column(String)
    # server_default so raw-SQL inserts (e.g. the worker) populate it too,
    # not just ORM object creation.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))

# NEW TABLE FOR FEATURE 1
class ConformalState(Base):
    __tablename__ = "conformal_state"
    sensor_id: Mapped[str] = mapped_column(String, primary_key=True)
    q_value: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())