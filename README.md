# WorkSight

## Project Status

**MVP state:** functional end-to-end prototype with an edge agent, Django backend APIs, MySQL persistence, and a server-rendered dashboard.

### Fully working (current code)
- Agent bootstraps a backend session and receives a token.
- Periodic screenshot capture and upload to backend.
- Periodic heartbeat updates per session.
- Periodic screen recording, optional ffmpeg compression, Google Drive upload, and recording metadata upload.
- On-agent AI pipeline for screenshot text extraction/features/scoring.
- Durable local AI queue (SQLite) with retries, exponential backoff, dead-letter marking, and idempotency keys.
- Backend ingestion APIs for sessions, screenshots, heartbeats, recordings, and AI metrics.
- Token/session binding checks for protected ingestion endpoints.
- Dashboard with screenshot activity table, AI metric summary, and risk summary based on recent anomaly counts.

### Experimental / partial
- AI models are heuristic/rule-based (not trained models).
- OCR is optional and degrades to partial pipeline status when unavailable.
- Statistical anomaly mode depends on baseline maturity; analytics expects `model_info.anomaly_mode`, but agent currently sends mode outside `model_info`, so maturity analytics can be inaccurate.
- `HealthMonitor` service exists but is not wired into runtime workers.
- Agent config is mostly constant-based (not env-driven).

### Planned for V2 (not implemented yet)
- Centralized configuration management for agent runtime and secrets.
- Stronger backend/API hardening (TLS-first, secure defaults in production, stricter auth lifecycle).
- Richer AI pipeline (trained models, improved calibration, stronger explainability schema).
- Better operational tooling (queue/dead-letter visibility, alerting, retention policies, cleanup jobs).

## Architecture Overview

WorkSight is split into an endpoint agent and a Django backend.

- **Agent:** captures screenshots/recordings, computes AI metrics locally, and uploads telemetry.
- **Backend:** receives and stores telemetry, enforces token checks, renders dashboard.
- **Storage:** MySQL for backend data; local filesystem + SQLite on agent.
- **Dashboard:** Django template view over stored sessions/screenshots/AI metrics.
- **Logging:** JSON rotating file logs on agent; container/Gunicorn logs on backend.
- **Cloud integration:** Google Drive archival for recorded videos.

### Data flow

```text
+-------------------------+          HTTP (token + idempotency)          +------------------------------+
| WorkSight Agent         | --------------------------------------------> | Django Backend (monitoring)  |
|-------------------------|                                               |------------------------------|
| capture-worker          |                                               | session/screenshot APIs      |
| heartbeat-worker        |                                               | heartbeat/recording APIs     |
| ai-worker               |                                               | ai-metrics API (dedupe)      |
| upload-worker           |                                               | dashboard + analytics svc    |
+------------+------------+                                               +--------------+---------------+
             |                                                                          |
             | local files + queue                                                      | ORM
             v                                                                          v
+-------------------------------+                                         +------------------------------+
| Agent Local Storage           |                                         | MySQL                        |
|-------------------------------|                                         |------------------------------|
| agent/storage/screenshots/    |                                         | AgentSession, ScreenshotLog  |
| agent/storage/videos/         |                                         | AgentHeartbeat, Recording    |
| agent/storage/logs/agent.log  |                                         | AgentToken, AIMetric         |
| agent/storage/ai_queue.sqlite3|                                         +------------------------------+
+-----------------------+-------+
                        |
                        | upload recording clips
                        v
              +-----------------------+
              | Google Drive          |
              +-----------------------+
```

## Features (Implemented)

- Multi-threaded agent runtime with dedicated workers (`heartbeat`, `capture`, `ai`, `upload`, `health`).
- Screenshot capture via `mss` and upload to `/api/screenshots/`.
- Session creation via `/api/sessions/` and bearer-token auth on protected endpoints.
- Heartbeat updates via `/api/sessions/<id>/heartbeat/`.
- Recording pipeline:
  - screen recording via OpenCV + MSS,
  - optional ffmpeg compression,
  - Google Drive upload,
  - backend metadata logging via `/api/sessions/<id>/recordings/`.
- AI pipeline on agent:
  - OCR extraction (when available),
  - redaction + text features,
  - rule-based productivity scoring,
  - hybrid anomaly scoring (static + baseline z-score mode),
  - payload enqueue with idempotency hash.
- Durable AI queue in SQLite with:
  - unique idempotency key,
  - retry scheduling,
  - dead-letter marking.
- AI ingestion endpoint with validation and idempotent dedupe (`X-Idempotency-Key`).
- Dashboard pages with:
  - searchable screenshot logs,
  - AI health counters,
  - per-session risk summary (top 8 sessions).
- Django admin registrations for all core models.
- Tests for API retry behavior, recording service flows, video compression behavior, and analytics service logic.

## Features (Planned / V2 Roadmap)

- True model-driven AI scoring and model lifecycle/version rollout strategy.
- Better anomaly maturity telemetry contract between agent and backend analytics.
- Runtime control plane (remote config, feature flags, policy updates).
- Background cleanup/retention workers for screenshots/videos/queue dead letters.
- Stronger observability stack (structured backend logs, metrics, traces, alerting).
- Production auth/security improvements (token rotation/revocation flow, HTTPS-only posture by default).

## Folder Structure

```text
WorkSight/
|-- agent/
|   |-- main.py
|   |-- runtime.py
|   |-- api_client.py
|   |-- config.py
|   |-- logger.py
|   |-- system_info.py
|   |-- ai/
|   |   |-- baseline_store.py
|   |   |-- queue_store.py
|   |   |-- types.py
|   |   |-- extractors/ocr_extractor.py
|   |   |-- feature_engineering/text_features.py
|   |   `-- models/
|   |       |-- productivity_model.py
|   |       `-- anomaly_model.py
|   |-- services/
|   |   |-- screenshot_service.py
|   |   |-- heartbeat_service.py
|   |   |-- recording_service.py
|   |   |-- ai_service.py
|   |   `-- health_monitor.py
|   |-- recording/
|   |   |-- screen_capture.py
|   |   |-- screen_recorder.py
|   |   |-- video_compressor.py
|   |   `-- bin/ffmpeg.exe
|   |-- cloud/
|   |   |-- drive_client.py
|   |   `-- setup_drive_auth.py
|   `-- storage/
|       |-- base.py
|       |-- local.py
|       `-- cleanup.py
|-- server/
|   |-- manage.py
|   |-- Dockerfile
|   |-- docker-compose.yml
|   |-- requirements-backend.txt
|   |-- worksight_server/
|   |   |-- settings.py
|   |   |-- urls.py
|   |   `-- wsgi.py
|   `-- monitoring/
|       |-- models.py
|       |-- views.py
|       |-- urls.py
|       |-- auth.py
|       |-- admin.py
|       |-- services/analytics.py
|       |-- templates/
|       |   |-- base.html
|       |   `-- monitoring/dashboard.html
|       |-- migrations/
|       `-- tests/test_analytics.py
|-- requirements.txt
|-- .gitignore
`-- README.md
```

## Setup Instructions

### 1. Environment setup

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Backend setup (Docker)

```bash
cd server
docker compose up -d --build
docker compose exec web python manage.py migrate
```

Backend endpoints:
- API base: `http://localhost:8080/api/`
- Dashboard: `http://localhost:8080/dashboard/`
- Admin: `http://localhost:8080/admin/`

### 3. Run agent

From repository root:

```bash
python -m agent.main
```

### 4. Required environment variables

Backend (`server/worksight_server/settings.py`):
- `DJANGO_SECRET_KEY` (required for non-dev deployments)
- `DEBUG`
- `ALLOWED_HOSTS`
- `DB_HOST`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_PORT`

Agent:
- No required env vars in current implementation.
- Runtime values are in `agent/config.py` (backend URL, intervals, queue limits, etc.).

Google Drive integration (agent recording upload):
- Place OAuth client file at `agent/credentials/credentials.json`.
- Run one-time auth helper: `python -m agent.cloud.setup_drive_auth`.
- This creates `agent/credentials/token.json` used by `DriveClient`.

## Production Considerations

- **Logging:**
  - Agent has rotating JSON logs (`agent/storage/logs/agent.log`).
  - Backend relies on container/Gunicorn output; structured backend logging is not yet configured.
- **Scalability limits:**
  - Agent uses local thread workers and local SQLite queue per host.
  - Dashboard and analytics run synchronous ORM queries; no cache layer/background workers.
  - No dedicated ingestion queue on backend.
- **Security gaps:**
  - `DEBUG` is enabled by default in compose.
  - Compose file includes hardcoded DB credentials and secret key examples.
  - Token model has no expiration/rotation/revocation flow.
  - CSRF/session secure flags depend on `DEBUG`; TLS/offload assumptions are not enforced in code.
- **Missing hardening:**
  - No rate limiting or API throttling.
  - Limited request schema validation and no formal OpenAPI contract.
  - No centralized secrets manager integration.
  - No automated retention cleanup for all generated artifacts.

## Structural Notes From Current Codebase

- `agent/__init__.py` contains an invalid stray method definition and is not a functional package initializer.
- `agent/ai/types.py` defines `anomaly_mode` twice and `to_dict()` omits some fields used elsewhere.
- Backend analytics reads `model_info.anomaly_mode`, but agent currently sets anomaly mode as a top-level field in its DTO path.
- Some files include mojibake/unicode artifact characters in comments/log messages.
