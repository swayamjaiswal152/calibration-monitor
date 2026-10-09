# Design Document - Forecast Calibration Monitor

## 1. API Design - REST + WebSocket

**REST Endpoints**
| Method | Endpoint | Description |
|---|---|---|
| POST | /api/v1/forecasts | Create hourly forecast |
| POST | /api/v1/actuals | Ingest ground truth |
| GET | /api/v1/metrics?window=168&sensor_id=x | Get rolling PICP/MAE/MPIW/Winkler |
| GET | /api/v1/alerts | List last 50 drift alerts |
| GET | /api/v1/conformal/state?sensor_id=x | Get q-value and width delta |
| POST | /api/v1/conformal/reset?sensor_id=x | Reset conformal correction |
| POST | /api/v1/simulate/drift?drift=5&n=50 | Inject synthetic drift (DB write) |
| POST | /api/v1/simulate/whatif?drift=5 | Preview coverage without DB write |
| WS | /ws/metrics | Live push for metrics + alerts |

**WebSocket Events: `ws://api/ws/metrics`**
json
{"event": "metrics_update", "data": {"sensor_id":"sensor-1","picp":0.82,"mae":1.2,"q_value":1.1}}
{"event": "alert", "data": {"sensor_id":"sensor-1","picp":0.82,"q_value":1.1}}
{"event": "actual_arrived", "data": {"sensor_id":"sensor-1","y_true":28.5}}

## 2. Database Schema - PostgreSQL Hypertables
sql
CREATE TABLE forecasts (
id SERIAL PRIMARY KEY,
time TIMESTAMPTZ DEFAULT NOW(),
sensor_id TEXT,
y_pred DOUBLE PRECISION,
y_lower DOUBLE PRECISION,
y_upper DOUBLE PRECISION
);

CREATE TABLE actuals (
id INT PRIMARY KEY REFERENCES forecasts(id),
time TIMESTAMPTZ DEFAULT NOW(),
sensor_id TEXT,
y_true DOUBLE PRECISION
);

CREATE TABLE alerts (
id SERIAL PRIMARY KEY,
time TIMESTAMPTZ DEFAULT NOW(),
sensor_id TEXT,
coverage DOUBLE PRECISION,
message TEXT,
is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE conformal_state (
sensor_id TEXT PRIMARY KEY,
q_value DOUBLE PRECISION DEFAULT 0.0,
updated_at TIMESTAMPTZ DEFAULT NOW()
);
-- TimescaleDB: SELECT create_hypertable('forecasts', 'time');


## 3. Frontend Design
- **Stack:** React + TypeScript + Vite + Recharts + Axios
- **Layout:** Single Live Dashboard
- **Components:**
  - `CoverageChart` - LineChart with 90% ReferenceLine, 50-point history
  - `WhatIfSimulator` - Slider 0-10, calls /whatif for preview, /drift to inject
  - `ConformalPanel` - Shows q-value, width delta, status (Calibrated/Widening)
- **State:** Polling every 3s + WebSocket push

## 4. Drift Detection & Outstanding Features Logic

python
WINDOW = 168
TARGET = 0.90
EPSILON = 0.05
def is_drift(picp): return picp < (TARGET - EPSILON) # < 0.85

Feature 1: Adaptive Conformal Prediction (Gibbs & Candes 2021)

q_{t+1} = q_t + eta(err - alpha) , eta=0.05, alpha=0.1

err=1 if miscovered else 0. Widens intervals on drift.


Feature 2: Slack Alerts - POST to SLACK_WEBHOOK_URL with Block Kit

Feature 3: What-If - predicted_coverage = 0.9 - drift0.13 (instant preview)

**Metrics Calculated:** PICP, MPIW, MAE, Winkler Score (alpha=0.1)

## 5. Testing Strategy
- **pytest:** Unit tests for `compute_metrics` and `is_drift`
- **Locust:** 1000 concurrent users, assert p95 < 150ms, RPS > 500
- **Drift Validation:** Inject `y_true = pred+drift` and measure detection delay < 4 windows, false alarm <2%
- **CI:** GitHub Actions runs `pytest` + `docker compose build` on push
