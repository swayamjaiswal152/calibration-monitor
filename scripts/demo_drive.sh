#!/usr/bin/env bash
# Drives the live dashboard through a clean demo arc for recording a GIF:
#   1. Baseline      - calibrated data, PICP climbs toward 90% (green)
#   2. Drift onset   - injected bias pushes actuals outside intervals, PICP
#                      drops, a drift alert fires, conformal q rises (widening)
#   3. Recovery      - calibrated data returns; corrected coverage recovers
#
# Usage:  ./scripts/demo_drive.sh [API_BASE_URL] [SENSOR_ID]
# Default API_BASE_URL is the public Render deployment.
#
# Start screen recording first, then run this. Total runtime ~35s - a good
# length to trim into a looping GIF. The dashboard polls every 3s and the
# worker pushes over WebSocket every 15s, so transitions animate on their own.
set -euo pipefail

BASE="${1:-https://calib-api.onrender.com}"
SENSOR="${2:-sensor-1}"

post() { curl -sS -m 90 -X POST "${BASE}${1}" >/dev/null; }
show() { printf '\n>> %s\n' "${1}"; }

show "Resetting conformal correction for ${SENSOR} ..."
post "/api/v1/conformal/reset?sensor_id=${SENSOR}"
sleep 2

show "1) Baseline: injecting calibrated forecasts (drift=0) -> coverage ~90%"
for _ in 1 2 3; do
  post "/api/v1/simulate/drift?sensor_id=${SENSOR}&drift=0&n=20"
  sleep 3
done

show "2) Drift onset: injecting biased actuals (drift=5) -> coverage drops, ALERT fires"
for _ in 1 2 3 4; do
  post "/api/v1/simulate/drift?sensor_id=${SENSOR}&drift=5&n=15"
  sleep 3
done

show "   ...Adaptive Conformal Prediction widens intervals (q up) to catch the drift"
sleep 4

show "3) Recovery: calibrated data returns (drift=0) -> corrected coverage recovers"
for _ in 1 2 3 4; do
  post "/api/v1/simulate/drift?sensor_id=${SENSOR}&drift=0&n=25"
  sleep 3
done

show "Done. Stop the recording and trim to a loop."
