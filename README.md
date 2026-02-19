# WorkSight

### Edge-AI Powered Monitoring System (Distributed Architecture Demo)

WorkSight is a **distributed, edge-AI monitoring platform** designed to simulate production-grade telemetry ingestion, on-device AI processing, and idempotent backend architecture.

It demonstrates how to design:

* Edge inference pipelines
* Durable local queuing
* Idempotent API ingestion
* Token-bound session security
* Dockerized backend deployment
* Additive backend evolution without refactors

This project focuses on **architecture and system reliability**, not just feature implementation.

---

## What This Project Demonstrates

* Running AI workloads on edge nodes instead of centralized servers
* Isolating workers to prevent main-loop blocking
* Designing retry-safe, idempotent ingestion APIs
* Handling partial failures gracefully
* Maintaining backward compatibility during feature expansion
* Production-like deployment using Docker + Gunicorn + MySQL

---

# System Architecture

## High-Level Design

```
            ┌──────────────────────────────┐
            │           Agent              │
            │──────────────────────────────│
            │ Capture Worker               │
            │ AI Worker (OCR + Scoring)    │
            │ Upload Worker                │
            │ Durable SQLite Queue         │
            │ Health Snapshot Monitor      │
            └───────────────┬──────────────┘
                            │
                            ▼
            ┌──────────────────────────────┐
            │        Django Backend        │
            │──────────────────────────────│
            │ Session Management API       │
            │ Screenshot Ingestion         │
            │ Recording Metadata           │
            │ AI Metrics Endpoint          │
            │ Idempotency Enforcement      │
            └───────────────┬──────────────┘
                            │
                            ▼
                        MySQL 8
```

---

# Edge AI Pipeline

All AI computation runs **on the agent**.

### Pipeline Flow

1. Screenshot captured
2. OCR extraction (resilient, optional)
3. Feature extraction
4. Productivity scoring (0-100)
5. Anomaly scoring (0-1)
6. Local queue persistence
7. Upload with `X-Idempotency-Key`

### Design Decisions

* No raw OCR text required on server
* Structured feature payload only
* Schema versioning supported
* Partial pipeline failures handled safely
* Queue retry with exponential backoff
* Dead-letter support

This simulates real-world edge telemetry systems.

---

# Key Engineering Features

### Agent

* Worker isolation (capture, AI, upload, heartbeat)
* Non-blocking runtime loop
* Durable local queue (crash-safe)
* Idempotent AI upload
* Health snapshot telemetry
* Google Drive video archival
* Graceful degradation when OCR unavailable

### Backend

* Additive API evolution (no refactors required)
* Session-scoped endpoints
* Token-to-session binding enforcement
* Idempotency dedupe using unique key
* Dockerized deployment
* Gunicorn multi-worker setup
* MySQL strict mode enabled

---

# Repository Structure

```
WorkSight/
│
├── agent/                  # Edge node runtime
│   ├── runtime.py
│   ├── api_client.py
│   ├── ai/
│   ├── services/
│   └── storage/
│
├── server/                 # Django backend
│   ├── monitoring/
│   ├── worksight_server/
│   ├── Dockerfile
│   └── docker-compose.yml
│
└── README.md
```

---

# Running the Backend

From `server/`:

```bash
docker compose up -d --build
docker compose exec web python manage.py migrate
```

Backend URL:

```
http://localhost:8080
```

Dashboard:

```
http://localhost:8080/dashboard/
```

Admin:

```
http://localhost:8080/admin/
```

---

# Running the Agent

From project root:

```bash
python -m agent.main
```

Ensure:

```python
BACKEND_BASE_URL = "http://127.0.0.1:8080/api"
```

---

# API Design

### Sessions

```
POST /api/sessions/
```

Creates session and binds token.

---

### Screenshot Upload

```
POST /api/screenshots/
```

Multipart form:

* image
* session_id
* captured_at (ISO8601 UTC)

---

### AI Metrics Ingestion

```
POST /api/sessions/{session_id}/ai-metrics/
```

Headers:

```
X-Idempotency-Key: <sha256>
```

Server deduplicates automatically.

---

# Data Models

* AgentSession
* AgentHeartbeat
* ScreenshotLog
* Recording
* AIMetric

`AIMetric` stores:

* Feature payload
* Productivity score
* Anomaly score
* Model metadata
* Pipeline status
* Idempotency key

---

# Production-Oriented Choices

### Why Edge AI?

* Reduces backend CPU load
* Improves privacy
* Reduces bandwidth
* Demonstrates distributed inference

### Why Idempotency?

Prevents duplicate metrics during:

* Network retries
* Agent restarts
* Partial failures

### Why Worker Isolation?

Prevents:

* AI blocking screenshot capture
* Upload blocking heartbeat
* Deadlocks in runtime loop

### Why Additive Backend Changes?

Maintains backward compatibility while evolving feature set.

---

# Observability

Agent logs:

```
agent/storage/logs/
```

Backend logs:

```
docker compose logs -f web
```

Health telemetry includes:

* AI worker alive
* Upload worker alive
* Queue backlog
* Last successful AI upload

---

# What Makes This Interview-Ready

This project showcases:

* Distributed system thinking
* Fault tolerance
* Backoff + retry logic
* Idempotent API contracts
* Docker deployment
* MySQL strict configuration
* Edge inference patterns
* Incremental architecture evolution

It demonstrates system design awareness beyond CRUD development.

---

# Tech Stack

* Python 3.11
* Django
* MySQL 8
* Gunicorn
* Docker + Docker Compose
* SQLite (agent queue)
* pytesseract (optional OCR)
* Google Drive API

---

# Version

**Version:** 0.2.0  
**Status:** Edge AI Integrated + Dockerized Backend  
**Architecture:** Agent-First, Additive Backend
