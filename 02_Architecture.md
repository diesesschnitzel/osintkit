# osintkit OSS — Architecture Document

**Version:** 1.0  
**Status:** Planning  
**Last Updated:** 2026-04-09

---

## High-Level Overview

osintkit OSS is a containerized, three-tier web application designed for local or private-network deployment. It consists of a Next.js frontend, FastAPI backend, async task queue (Celery + Redis), and SQLite database — all orchestrated via Docker Compose.

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Host                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐      ┌──────────────┐                   │
│  │  Frontend    │      │     API      │                   │
│  │  (Next.js)   │◄────►│  (FastAPI)   │                   │
│  │  :3000       │      │  :8000       │                   │
│  └──────────────┘      └──────────────┘                   │
│                              │                             │
│                              │ enqueue tasks              │
│                              ▼                             │
│                         ┌──────────────┐                  │
│                         │    Redis     │                  │
│                         │  (Broker)    │                  │
│                         │  :6379       │                  │
│                         └──────────────┘                  │
│                              ▲                             │
│                              │ consume tasks              │
│                              │                             │
│                         ┌──────────────┐                  │
│                         │    Worker    │                  │
│                         │   (Celery)   │                  │
│                         │  (4 threads) │                  │
│                         └──────────────┘                  │
│                              │                             │
│                              │ r/w findings              │
│                              ▼                             │
│                         ┌──────────────┐                  │
│                         │   SQLite     │                  │
│                         │ (scan.db)    │                  │
│                         └──────────────┘                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Docker Compose Services (4 total)

### 1. Frontend Service
**Image:** `osintkit-frontend` (custom build)  
**Port:** `3000`  
**Environment:**
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NODE_ENV=production
```
**Startup:** `npm run start`  
**Dependencies:** None (communicates with API only)  
**Volumes:** None (stateless)

### 2. API Service
**Image:** `osintkit-api` (custom build)  
**Port:** `8000`  
**Environment:**
```
FASTAPI_ENV=production
REDIS_URL=redis://redis:6379/0
DATABASE_URL=sqlite:///./data/scan.db
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2
LOG_LEVEL=INFO
```
**Startup:** `uvicorn main:app --host 0.0.0.0 --port 8000`  
**Dependencies:** Redis, SQLite  
**Volumes:**
- `/app/data` (shared SQLite database)
- `/app/logs` (optional, request logs)

### 3. Worker Service
**Image:** `osintkit-api` (same as API, different CMD)  
**Port:** None (internal only)  
**Environment:** (same as API, plus)
```
WORKER_CONCURRENCY=4
```
**Startup:** `celery -A tasks worker --loglevel=info --concurrency=4`  
**Dependencies:** Redis, SQLite  
**Volumes:**
- `/app/data` (shared SQLite database)
- `/app/logs` (task execution logs)

### 4. Redis Service
**Image:** `redis:7-alpine`  
**Port:** `6379`  
**Persistence:** None (ephemeral, OK for development; can add RDB for production)  
**Environment:** None  
**Volumes:** None

---

## Technology Stack

### Frontend
- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS 3.4
- **HTTP Client:** fetch API + React hooks
- **State Management:** React Context (minimal) + local state
- **Real-time updates:** Polling (2s interval) or WebSocket (stretch goal)
- **Build output:** Static HTML + client-side JS (no server-side rendering needed)

### Backend
- **Framework:** FastAPI 0.109+
- **Language:** Python 3.11
- **Task Queue:** Celery 5.3 with Redis broker
- **Database:** SQLite 3 (file-based, no migrations)
- **ORM:** SQLAlchemy 2.0 (optional, simple SQL OK too)
- **Async Runtime:** asyncio (FastAPI native)
- **HTTP Server:** Uvicorn 0.27+
- **Validation:** Pydantic v2
- **Logging:** Python logging (stdout)

### OSINT Tools (subprocess calls, no Python wrappers)
- **Maigret:** CLI tool, JSON output
- **WhatsMyName:** JSON database, grep-based
- **Holehe:** Python package or CLI
- **theHarvester:** Python package or CLI
- **crt.sh:** curl/requests to public API
- **psbdmp.ws:** requests HTTP API
- **Ahmia.fi:** requests HTTP API

### Data Persistence
- **Database:** SQLite (file: `/data/scan.db`)
- **Schema:** Auto-created on startup (no migrations)
- **Tables:**
  - `scans` — scan metadata
  - `findings` — individual results per module
- **Query mode:** Raw SQL or SQLAlchemy ORM
- **Backup:** Users can copy `/data/scan.db` manually

---

## Data Model

### Scans Table
```sql
CREATE TABLE scans (
    id TEXT PRIMARY KEY,  -- UUID v4
    target TEXT NOT NULL,
    target_type TEXT NOT NULL,  -- 'email', 'username', 'domain', 'phone'
    status TEXT NOT NULL,  -- 'pending', 'running', 'completed', 'failed'
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    modules TEXT NOT NULL,  -- JSON array: ["social", "email", "breach", "web", "cert", "paste", "dark_web"]
    results TEXT,  -- JSON object: {module: {findings: [...]}}
    error_message TEXT  -- if status='failed'
);
```

### Findings Table (optional, for querying)
```sql
CREATE TABLE findings (
    id TEXT PRIMARY KEY,  -- UUID v4
    scan_id TEXT NOT NULL,
    module TEXT NOT NULL,
    finding_type TEXT,  -- 'profile', 'email_account', 'breach', 'subdomain', etc.
    data TEXT NOT NULL,  -- JSON object with details
    source_url TEXT,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (scan_id) REFERENCES scans(id)
);
```

### Example Results JSON
```json
{
  "social": {
    "status": "completed",
    "duration_ms": 15000,
    "findings": [
      {
        "username": "alice@example.com",
        "platform": "github",
        "url": "https://github.com/alice@example.com",
        "confidence": "high"
      }
    ]
  },
  "email": {
    "status": "completed",
    "duration_ms": 8000,
    "findings": [
      {
        "email": "alice@example.com",
        "service": "google",
        "has_account": true,
        "reset_url": "https://accounts.google.com/ForgotPassword"
      }
    ]
  },
  "paste": {
    "status": "completed_partial",
    "duration_ms": 3000,
    "error": "Rate limit reached (~100 req/day)",
    "findings": [
      {
        "email": "alice@example.com",
        "paste_site": "pastebin",
        "paste_id": "abc123",
        "url": "https://pastebin.com/abc123",
        "content_preview": "password=... email=alice@example.com"
      }
    ]
  }
}
```

---

## API Specification

### POST /api/scans
**Request:**
```json
{
  "target": "alice@example.com",
  "target_type": "email",
  "modules": ["social", "email", "breach", "web", "cert", "paste", "dark_web"]
}
```
**Response (201 Created):**
```json
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "created_at": "2026-04-09T12:00:00Z"
}
```
**Errors:**
- 400: Invalid target or modules
- 500: Redis/database unavailable

---

### GET /api/scans/{scan_id}/status
**Response (200 OK):**
```json
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "progress": {
    "social": "completed",
    "email": "running",
    "breach": "pending",
    "web": "pending",
    "cert": "pending",
    "paste": "pending",
    "dark_web": "pending"
  },
  "updated_at": "2026-04-09T12:00:15Z"
}
```
**Errors:**
- 404: Scan not found

---

### GET /api/scans/{scan_id}
**Response (200 OK):**
```json
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "target": "alice@example.com",
  "status": "completed",
  "results": { ...results object... },
  "created_at": "2026-04-09T12:00:00Z",
  "completed_at": "2026-04-09T12:02:30Z"
}
```
**Errors:**
- 404: Scan not found

---

### GET /api/scans/{scan_id}/export/json
**Response (200 OK):**
```
Content-Type: application/json
Content-Disposition: attachment; filename="scan_550e8400.json"
{...full results...}
```

---

### GET /api/scans/{scan_id}/export/pdf
**Response (200 OK):**
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="scan_550e8400.pdf"
[PDF binary]
```
**Note:** Uses ReportLab or WeasyPrint for PDF generation; renders results in structured table format.

---

## File Structure

```
osintkit-oss/
├── docker-compose.yml
├── .env.example
├── .dockerignore
├── .gitignore
├── LICENSE (MIT)
├── README.md
├── CONTRIBUTING.md
│
├── frontend/
│   ├── Dockerfile
│   ├── next.config.js
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── package.json
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx (scan form + results)
│   │   │   └── scan/[id]/page.tsx (results detail view)
│   │   ├── components/
│   │   │   ├── ScanForm.tsx
│   │   │   ├── ResultsDisplay.tsx
│   │   │   ├── ModuleCard.tsx
│   │   │   └── ExportButtons.tsx
│   │   └── lib/
│   │       └── api.ts (fetch wrapper)
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py (FastAPI app + routes)
│   ├── models.py (SQLAlchemy/Pydantic)
│   ├── tasks.py (Celery task definitions)
│   ├── modules/
│   │   ├── social.py (Maigret + WhatsMyName)
│   │   ├── email.py (Holehe)
│   │   ├── breach.py (HIBP)
│   │   ├── web.py (theHarvester)
│   │   ├── cert.py (crt.sh)
│   │   ├── paste.py (psbdmp.ws)
│   │   └── dark_web.py (Ahmia.fi)
│   ├── utils/
│   │   ├── db.py (SQLite connection, schema init)
│   │   ├── celery_app.py (Celery config)
│   │   ├── logger.py (logging config)
│   │   └── graceful_degrade.py (rate limit handling)
│   ├── data/
│   │   └── scan.db (SQLite, auto-created)
│   └── logs/ (optional)
│
└── docs/
    ├── MODULES.md (detailed module documentation)
    ├── API.md (full API reference)
    ├── DEPLOYMENT.md (self-hosting guide)
    └── SCREENSHOTS/ (sample results)
```

---

## Environment Configuration

**File:** `.env.example` (checked into repo, zero secrets)
```env
# Frontend
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Backend
FASTAPI_ENV=production
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///./data/scan.db
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# Worker
WORKER_CONCURRENCY=4

# OSINT Tools (all optional, most have no keys)
# Leave blank — tools use defaults or bundled databases
AHMIA_API_TIMEOUT=30
PSBDMP_API_TIMEOUT=30
```

**No API keys required in .env** — all OSINT tools are free and keyless.

---

## Deployment Modes

### Local Development
```bash
docker compose -f docker-compose.dev.yml up
# Frontend: http://localhost:3000
# API: http://localhost:8000
# Redis: localhost:6379
```

### Production (Self-Hosted)
```bash
docker compose up -d
# Same URLs if on localhost, or https://your-domain.com if reverse-proxied
```

### Environment-Specific Configs
- **dev:** Hot reload, debug logs, CORS permissive
- **production:** Optimized builds, INFO logs, CORS localhost only

---

## Graceful Degradation Strategy

When rate-limited APIs (psbdmp.ws, Ahmia.fi) are exhausted:

1. **Module catches HTTP 429 (Too Many Requests)**
2. **Returns partial results with metadata:**
   ```json
   {
     "status": "completed_partial",
     "findings": [...results before limit hit...],
     "error": "Rate limit reached after 50 requests (~100/day allowed)",
     "retry_after": 86400,
     "recommendation": "Run scan again tomorrow or self-host your own service"
   }
   ```
3. **Scan continues with other modules** (not blocked)
4. **UI displays partial results + friendly note**

---

## Logging & Observability

### Log Destinations
- **API:** stdout (Uvicorn/FastAPI logs)
- **Worker:** stdout (Celery worker logs)
- **Frontend:** browser console only

### Log Format
```
2026-04-09T12:00:00 [INFO] POST /api/scans HTTP 201 (23ms)
2026-04-09T12:00:02 [INFO] Starting task: scan_550e8400 module=social
2026-04-09T12:00:15 [INFO] Completed task: scan_550e8400 module=social findings=3
2026-04-09T12:00:20 [WARN] Rate limit hit in module=paste (HTTP 429)
```

### No External Logging
- No Datadog, ELK, Splunk, CloudWatch
- Logs stream to container stdout for `docker logs` inspection

---

## Security Considerations

### No Authentication
- All endpoints public (localhost assumed private)
- No session tokens, cookies, or JWT
- If exposed to internet, recommend nginx reverse proxy with basic auth or IP whitelisting

### No Secrets
- No API keys stored or needed
- No database credentials (.env not needed for SQLite)
- No TLS certificates required (optional for self-hosted)

### Data Handling
- **In-memory:** Celery tasks process data without logging raw results
- **At-rest:** SQLite file accessible to all services (same host)
- **In-transit:** HTTP (unencrypted) assumed safe on localhost; HTTPS recommended for production
- **PII:** Results may contain sensitive data; no automated cleanup

### Rate Limiting
- Not enforced server-side (no auth to rate limit per user)
- API rate limits are soft (modules gracefully degrade)
- No DDoS protection expected

---

## Performance & Scalability

### Baseline Performance (single machine, 4 cores / 8 GB RAM)
| Scenario | Latency | Notes |
|----------|---------|-------|
| Empty scan creation | 50ms | DB write only |
| Single module (social) | 15-30s | Depends on tool speed |
| All 7 modules (serial, no rate limits) | 60-120s | 7 x 15s avg per module |
| Concurrent scans (2 workers x 4 threads) | 8 concurrent | Celery queue limits |

### Bottlenecks
- **Celery worker concurrency:** Capped at 4 threads/processes per service (configurable)
- **OSINT tool speed:** Most tools single-threaded; Maigret slowest (~30s for 400 networks)
- **SQLite write contention:** Negligible for < 100 scans/hour

### Scaling Strategy
- **Horizontal:** Run multiple `worker` services, share Redis + SQLite (via NFS if needed)
- **Vertical:** Increase `WORKER_CONCURRENCY` from 4 to 8-16 on beefy hardware

---

## Deployment Checklist

- [ ] All 4 Docker images build successfully
- [ ] docker-compose.yml passes validation (`docker-compose config`)
- [ ] Services start in correct order (API depends on Redis, Worker depends on Redis)
- [ ] Healthchecks pass (API responds to GET /api/health, Worker is reachable)
- [ ] SQLite schema auto-creates on first run
- [ ] Frontend can reach API at configured URL
- [ ] Sample scan completes end-to-end in < 2 minutes
- [ ] Results exportable as JSON and PDF
- [ ] Logs are readable via `docker logs`
- [ ] Volume mounts preserve data across restarts

---

## Technology Rationale

| Choice | Why Not Alternative |
|--------|----------------------|
| SQLite | Postgres too heavyweight for self-hosters; no external service dependency |
| Celery + Redis | Simpler than Temporal or Kafka; Redis ephemeral OK (no state) |
| Next.js 14 | Fast, built-in API routes, SSG friendly, large community |
| FastAPI | Type-safe, auto-docs, async, modern Python standard |
| Docker Compose | No Kubernetes complexity; fits OSS single-machine use case |
| TypeScript (frontend) | Safer than JS; catches bugs early; good tooling |
| Python 3.11 | Recent, stable, good for scripting; OSINT tools mostly Python |

---

## Migration Path (Future)

If osintkit OSS scales to require:
- **Multi-machine:** Replace SQLite with PostgreSQL, use Kubernetes
- **High availability:** Add API load balancer, replicate workers, cluster Redis
- **User management:** Add optional auth layer (Supabase, Keycloak)
- **Commercial features:** Separate into "OSS" (free, simple) and "Pro" (hosted, advanced)

Current design supports all future upgrades without breaking the open-source core.
