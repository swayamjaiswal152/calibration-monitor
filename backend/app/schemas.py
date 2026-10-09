from pydantic import BaseModel
import datetime
class ForecastCreate(BaseModel): sensor_id: str; y_pred: float; y_lower: float; y_upper: float
class ActualCreate(BaseModel): forecast_id: int; sensor_id: str; y_true: float
class MetricsOut(BaseModel): sensor_id: str; picp: float; mae: float; mpiw: float; winkler: float