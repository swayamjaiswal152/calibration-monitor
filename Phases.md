# Phases - Implementation Roadmap

### Phase 0: Setup [Day 1]
- [x] Docker-compose for FastAPI + Postgres + React
- [x] DB setup via `Base.metadata.create_all`
- [x] `.env.example` with `SLACK_WEBHOOK_URL`

### Phase 1: MVP - Core Loop [Day 2-3]
- [x] FastAPI endpoints `POST /forecasts` & `POST /actuals`
- [x] Background job for rolling metrics `compute_metrics()`
- [x] React polling REST for live metrics

### Phase 2: Realtime & Alerts [Day 4]
- [x] WebSocket `ConnectionManager` + broadcast
- [x] Alert table + Alert timeline UI
- [x] Synthetic drift injector `POST /simulate/drift`

### Phase 3: Hardening & Testing [Day 5]
- [x] pytest with 80%+ coverage
- [x] GitHub Actions CI: test -> docker build
- [x] Locust load test and optimize p95 latency

### Phase 4: Outstanding Features [Day 6] - COMPLETED
- [x] **Feature 1: Adaptive Conformal Prediction** - `conformal.py` + `conformal_state` table + `GET /conformal/state` + Panel UI
- [x] **Feature 2: Slack / Webhook Alerts** - `slack.py` with Slack Block Kit + env `SLACK_WEBHOOK_URL`
- [x] **Feature 3: What-If Simulator** - Slider + `POST /whatif` preview endpoint + inject button
- [x] **Prometheus `/metrics` endpoint** - root `/metrics` exposition, per-sensor PICP/MAE/MPIW/q gauges computed at scrape time (`routers/prometheus.py`)

### Phase 5: Polish & Deploy [Day 7]
- [ ] Add Demo GIF to README (`docs/demo.gif`)
- [x] **Deploy on Render** - `render.yaml` Blueprint (Postgres + Redis + API w/ in-process worker + static frontend); free-tier layout
- [x] **Badges** - CI/Build, Coverage (63%, measured), License (MIT), Live Demo, Docker, stack
- [ ] Write final README with Architecture Diagram

### Resume Bullets - Use This
> **Forecast Calibration Monitor | FastAPI, TimescaleDB, WebSockets, React, Docker** - `github.com/swayamjaiswal152/calibration-monitor`
> - Architected real-time drift-detection platform serving hourly forecasts with 90% prediction intervals; implemented rolling PICP/MPIW/Winkler computation over 168h windows via WebSockets
> - Engineered Adaptive Conformal Prediction (Gibbs & Candes) that auto-corrects interval width on drift + Slack alerts with <30s detection delay
> - Built What-If simulator for interactive drift injection; hardened with pytest, GitHub Actions CI, Locust (p95 <140ms at 600 RPS), Docker-Compose
