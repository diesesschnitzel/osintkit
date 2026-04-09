# osintkit OSS — AI/Agent Coding Rules

**Version:** 1.0  
**Status:** Planning  
**Last Updated:** 2026-04-09  
**Intended for:** LLM coding agents, developers implementing osintkit OSS

---

## Core Philosophy

osintkit OSS is designed for **simplicity, transparency, and self-hosting**. Code must be:
- **Understandable** — OSS users read and modify code; avoid premature optimization
- **Keyless** — Zero API keys, zero secrets in code or config
- **Stateless** — Scans are ephemeral; no persistent user data across restarts
- **Graceful** — Never fail hard; degrade gracefully when APIs hit rate limits
- **Self-contained** — No external SaaS dependencies; Docker Compose runs offline

---

## Rule 1: No Authentication or User Accounts

**REQUIRED:**
- No login system
- No user table, user model, or session management
- No JWT, OAuth, cookies, or bearer tokens
- No admin dashboard or privileged endpoints
- All API endpoints are public

**Allowed:**
- Rate limiting by IP (optional, on self-hosted deployments)
- Basic HTTP auth on reverse proxy (nginx, external)

**Not allowed:**
- Database columns for user_id, username, password_hash
- Supabase, Firebase Auth, Auth0, Clerk, or any auth provider
- Middleware checking request authorization
- "Anonymous" user model (still a user)

**Implementation pattern:**
```python
# GOOD: Public endpoint, no auth required
@app.post("/api/scans")
async def create_scan(request: ScanRequest):
    # No auth check
    scan_id = generate_uuid()
    # Process scan
    return {"scan_id": scan_id}

# BAD: Auth middleware or user context
@app.post("/api/scans")
@require_auth  # DO NOT ADD
async def create_scan(request: ScanRequest, user: User = Depends(get_current_user)):
    # NO
    pass
```

---

## Rule 2: No Database Migrations or External Database Service

**REQUIRED:**
- SQLite only (file-based, no service)
- Schema auto-created on first run (init script in API startup)
- No alembic, Flyway, or migration tool

**Allowed:**
- SQL CREATE TABLE statements in Python startup code
- `db.init_db()` function called on `@app.on_event("startup")`
- Simple schema versioning in code comments

**Not allowed:**
- Postgres, MySQL, MongoDB, or any external database
- Migration files (.sql scripts in migrations/ directory)
- Database URL configuration requiring setup steps
- Schema rollback logic

**Implementation pattern:**
```python
# GOOD: Auto-create schema at startup
def init_db():
    """Create tables if not exist."""
    with sqlite3.connect(DATABASE_URL) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS scans (
                id TEXT PRIMARY KEY,
                target TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                results TEXT
            )
        ''')
        conn.commit()

@app.on_event("startup")
async def startup():
    init_db()

# BAD: Migration system
# DO NOT create migrations/ directory
# DO NOT use alembic, SQLAlchemy migration tools
```

---

## Rule 3: No API Keys Required (True Keyless)

**REQUIRED:**
- All OSINT modules use free APIs or bundled databases
- No API keys in `.env`, `.env.example`, or environment variables
- No placeholder keys ("FILL_YOUR_KEY_HERE")
- No key validation or key-checking code

**Allowed:**
- Timeouts, rate limits, retries (all modules handle gracefully)
- API URLs in code (public endpoints only)
- Tool version pinning in Dockerfile/requirements.txt

**Not allowed:**
- Hunter.io, RocketReach, Clearbit, Shodan, Censys, VirusTotal API (all require keys)
- Config requiring users to add API keys before first run
- "Optional" API keys that enhance functionality
- Documentation suggesting users get API keys

**Included modules (keyless):**
- Maigret (local database of 400+ networks)
- WhatsMyName (JSON database, searchable offline)
- Holehe (free public API, no key)
- theHarvester (open source, no key)
- crt.sh (public Certificate Transparency logs)
- psbdmp.ws (free API, rate limited but free)
- Ahmia.fi (Tor search engine, free API)
- HIBP PwnedPasswords (free, privacy-preserving k-anon API)

**Implementation pattern:**
```python
# GOOD: Free API call, no key needed
async def search_paste_sites(email: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://psbdmp.ws/api/v3/search?q={email}",
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            return {"status": "rate_limited", "findings": []}

# BAD: API key required
# DO NOT:
api_key = os.getenv("HUNTER_API_KEY")  # Wrong tool
if not api_key:
    raise ValueError("HUNTER_API_KEY required")
```

---

## Rule 4: No Telemetry, Analytics, or Tracking

**REQUIRED:**
- No event tracking, log shipping, or analytics
- No Google Analytics, Mixpanel, Amplitude, Sentry, etc.
- No telemetry SDK calls in code
- No user data collection or reporting

**Allowed:**
- Server logs to stdout (for debugging, not for analysis)
- Simple request logging (method, path, status, latency)
- Performance metrics within single machine (no external service)

**Not allowed:**
- Crash reporting (Sentry, Rollbar, etc.)
- User behavior tracking
- Error aggregation services
- Monitoring SaaS
- Usage statistics collection

**Implementation pattern:**
```python
# GOOD: Local logging only
import logging
logger = logging.getLogger(__name__)

@app.post("/api/scans")
async def create_scan(request: ScanRequest):
    logger.info(f"POST /api/scans HTTP 201 (25ms)")  # Stdout only
    scan_id = generate_uuid()
    return {"scan_id": scan_id}

# BAD: External telemetry
# DO NOT:
import sentry_sdk
sentry_sdk.init("https://...")  # NO
telemetry.capture("scan_created", {"scan_id": scan_id})  # NO
```

---

## Rule 5: Graceful Degradation for Rate-Limited APIs

**REQUIRED:**
- When psbdmp.ws or Ahmia.fi hit rate limits (HTTP 429), do NOT fail the scan
- Return partial results with metadata about the rate limit
- Continue other modules (parallel execution or after catching exception)
- User should see: "Rate limit reached. Results may be incomplete. Run again tomorrow."

**Allowed:**
- Retry once with exponential backoff (max 5s delay)
- Log rate limit hit (to help debug, not fail)
- Cap number of requests to prevent hammering

**Not allowed:**
- Failing entire scan due to one module hitting rate limit
- Blocking other modules while waiting for rate-limited module
- Throwing unhandled exception that crashes worker

**Implementation pattern:**
```python
# GOOD: Graceful degradation
async def run_paste_search(email: str) -> dict:
    """Search paste sites; return partial results if rate limited."""
    findings = []
    try:
        for site in ["pastebin", "pastie", "github_gist"]:
            try:
                response = await http_client.get(
                    f"https://psbdmp.ws/api/v3/search?q={email}",
                    timeout=30
                )
                if response.status_code == 429:
                    # Rate limit hit; return what we have so far
                    return {
                        "status": "completed_partial",
                        "findings": findings,
                        "error": "Rate limit reached (~100 req/day allowed)",
                        "retry_after": 86400
                    }
                findings.extend(response.json().get("data", []))
            except Exception as e:
                logger.warning(f"Error searching {site}: {e}")
                continue  # Continue with next site
    except Exception as e:
        logger.error(f"Paste search failed: {e}")
        # Return what we have, don't crash scan
    
    return {
        "status": "completed",
        "findings": findings
    }

# BAD: Hard failure on rate limit
# DO NOT:
if response.status_code == 429:
    raise RateLimitError("API exhausted")  # Crashes scan
```

---

## Rule 6: All OSINT Tools Run as Subprocesses

**REQUIRED:**
- Maigret, WhatsMyName, theHarvester, crt.sh (curl), psbdmp.ws (HTTP), Ahmia.fi (HTTP) all invoked as CLI or HTTP calls
- No Python wrapper libraries unless absolutely necessary
- Output parsed from JSON or text format, not imported as Python modules (except where tool ships Python package)

**Allowed:**
- Subprocess calls with timeout
- HTTP requests via httpx or requests
- Parsing JSON/CSV output
- Python packages that are essentially CLI wrappers (e.g., Holehe)

**Not allowed:**
- Forking entire tool codebases into this repo
- Creating custom Python bindings for CLI tools
- Import-time initialization or expensive setup

**Implementation pattern:**
```python
# GOOD: Subprocess or HTTP call
import subprocess
import httpx

async def run_maigret(username: str) -> dict:
    """Run Maigret CLI, parse JSON output."""
    try:
        result = subprocess.run(
            ["maigret", "--json", username],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        logger.warning(f"Maigret timeout for {username}")
    return {"findings": []}

async def search_crt_sh(domain: str) -> list:
    """Query Certificate Transparency via public API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://crt.sh/?q={domain}&output=json",
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
    return []

# BAD: Importing tool as library (avoid if possible)
# from theHarvester.lib.hunter import Hunter  # Only if unavoidable
```

---

## Rule 7: Keep Code Simple and Readable

**REQUIRED:**
- Prefer readability over cleverness
- Function signatures with type hints
- Docstrings on public functions
- Comments on complex logic
- Simple data structures (dict, list, not custom classes where dict works)

**Allowed:**
- SQLAlchemy ORM (optional; simple SQL fine too)
- Pydantic for request/response validation
- Standard library + FastAPI + Celery + SQLite

**Not allowed:**
- Metaclass magic, decorators stacking, functional programming tricks
- Premature optimization ("fast code" before "right code")
- Custom dependency injection frameworks
- Complex abstraction layers (CQRS, event sourcing, etc.)

**Implementation pattern:**
```python
# GOOD: Clear, simple, easy to modify
@app.post("/api/scans")
async def create_scan(request: ScanRequest) -> dict:
    """
    Create a new scan.
    
    Args:
        request: Scan parameters (target, modules)
    
    Returns:
        scan_id and initial status
    """
    scan_id = str(uuid.uuid4())
    
    # Validate target
    if not is_valid_email(request.target):
        raise HTTPException(status_code=400, detail="Invalid email")
    
    # Save scan metadata
    with get_db() as conn:
        conn.execute(
            "INSERT INTO scans (id, target, status, created_at) VALUES (?, ?, ?, ?)",
            (scan_id, request.target, "pending", datetime.utcnow())
        )
    
    # Queue task
    run_scan.delay(scan_id, request.target, request.modules)
    
    return {
        "scan_id": scan_id,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat()
    }

# BAD: Overly abstract, hard to follow
# DO NOT:
class ScanFactory:
    def __init__(self, db_session, event_bus, scan_validator, scan_repository):
        self.db = db_session
        self.bus = event_bus
        self.validator = scan_validator
        self.repo = scan_repository
    
    def create(self, request):
        if not self.validator.validate(request):
            self.bus.emit(ValidationFailedEvent(request))
            raise ValidationError()
        scan = Scan.from_request(request)
        self.repo.save(scan)
        self.bus.emit(ScanCreatedEvent(scan))
        return scan
```

---

## Rule 8: Good README is Essential

**REQUIRED:**
- Setup instructions in 5 steps max
- `docker compose up` works without config steps
- Screenshots of scan flow
- Example output (JSON + PDF)
- License (MIT), Contributing, Code of Conduct

**Must include:**
1. What is osintkit OSS?
2. Quick start (clone → compose up → scan)
3. Modules table (what each does, limits)
4. API reference (POST /api/scans, etc.)
5. Self-hosting guide
6. Limitations (rate limits, what's NOT included)
7. Contributing guidelines
8. License

**Good README structure:**
```markdown
# osintkit OSS

## What is it?
[1 paragraph]

## Quick Start
docker clone...
docker compose up
# Visit http://localhost:3000

## Features
| Module | Limit |
|--------|-------|

## API
POST /api/scans
...

## Self-Hosting
## Limitations
## Contributing
## License
```

---

## Rule 9: Docker Setup Must Work Out-of-Box

**REQUIRED:**
- `docker compose up` starts all 4 services without additional commands
- No `docker compose build` needed (images pre-built or auto-built in compose)
- SQLite auto-created, no manual migrations
- All services healthy within 30 seconds
- No volumes requiring `mkdir` before startup

**Allowed:**
- `.dockerignore` to keep images small
- `docker-compose.prod.yml` for production override
- Health checks in docker-compose.yml

**Not allowed:**
- "Run these 5 SQL scripts first"
- "Set these 10 env variables before starting"
- `docker exec` setup scripts required
- Multi-step initialization docs

**Implementation pattern:**
```yaml
# GOOD: docker-compose.yml
version: '3.8'
services:
  api:
    image: osintkit-api:latest
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: sqlite:///./data/scan.db
      REDIS_URL: redis://redis:6379/0
    volumes:
      - ./data:/app/data  # SQLite persists here
    depends_on:
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 10s
      timeout: 5s
      retries: 3
  
  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
```

---

## Rule 10: No Saved Reports or Persistent User Data

**REQUIRED:**
- Scans are ephemeral; deleted when browser closes
- No "saved scans" list
- No persistent database of results (optional: keep for 24 hours only)
- Results shown once, exported if user wants to keep
- No user accounts or scan history

**Allowed:**
- SQLite table storing scan records (for status polling)
- TTL-based cleanup (24 hours = old records deleted)
- Optional export to JSON/PDF before results expire

**Not allowed:**
- "My Scans" dashboard
- Scan history across browser sessions
- Persistent user-owned reports
- API to fetch old scans (only current scan)

**Implementation pattern:**
```python
# GOOD: Ephemeral results
@app.get("/api/scans/{scan_id}")
async def get_scan(scan_id: str):
    """Fetch a scan (only if < 24 hours old)."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM scans WHERE id = ? AND created_at > datetime('now', '-1 day')",
            (scan_id,)
        ).fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Scan not found or expired")
    
    return dict(row)

# Cleanup old scans periodically
@app.on_event("startup")
async def cleanup_old_scans():
    """Delete scans older than 24 hours."""
    async def cleanup():
        while True:
            with get_db() as conn:
                conn.execute(
                    "DELETE FROM scans WHERE created_at < datetime('now', '-1 day')"
                )
                conn.commit()
            await asyncio.sleep(3600)  # Run hourly
    
    asyncio.create_task(cleanup())

# BAD: Persistent user scans
# DO NOT:
class ScanHistory(models.Model):
    user = ForeignKey(User)
    results = JSONField()
    saved_at = DateTimeField(auto_now=True)
```

---

## Rule 11: No External Dependencies Beyond Docker

**REQUIRED:**
- Everything runs inside Docker
- No external services required (no hosted Redis, no hosted DB)
- No SaaS integrations
- All tools bundled in Docker image or installed via package manager

**Allowed:**
- Curl/wget to public APIs (psbdmp.ws, Ahmia.fi, crt.sh)
- Docker Hub images (redis:7, python:3.11, node:18)
- GitHub to fetch code on clone

**Not allowed:**
- Supabase, Firebase, PlanetScale, Heroku, AWS RDS
- Datadog, New Relic, CloudFlare, Vercel
- External message queues (use Redis only)
- CDNs for assets

---

## Rule 12: Version Pinning for Reproducibility

**REQUIRED:**
- Docker images: `python:3.11-slim`, `redis:7-alpine`, `node:18-alpine`
- Python packages: `FastAPI==0.109.0`, `Celery==5.3.4`, etc. (pin exact versions)
- OSINT tool versions: pin in Dockerfile or requirements.txt
- Node packages: pin in package-lock.json

**Allowed:**
- Patch-level pinning (`==1.2.3`)
- Minor-version pinning if tool is stable (`==1.2.*`)

**Not allowed:**
- Floating versions (`FastAPI` without version, `latest` Docker tags)
- Range versions (`>=1.0`)

**Implementation pattern:**
```dockerfile
# GOOD: Pinned versions
FROM python:3.11.2-slim
RUN pip install \
    FastAPI==0.109.0 \
    Celery==5.3.4 \
    redis==5.0.1 \
    SQLAlchemy==2.0.23
```

---

## Rule 13: Error Handling and Timeouts

**REQUIRED:**
- All subprocess/HTTP calls have timeout (30-60s)
- Timeouts caught and logged, don't crash scan
- Partial results returned on timeout
- No unhandled exceptions reaching user

**Implementation pattern:**
```python
async def search_module(query: str, module_name: str) -> dict:
    """Run module with timeout and error handling."""
    try:
        result = await asyncio.wait_for(
            run_subprocess_or_api_call(query),
            timeout=60.0
        )
        return {"status": "completed", "findings": result}
    except asyncio.TimeoutError:
        logger.warning(f"{module_name} timeout for {query}")
        return {"status": "timeout", "findings": [], "error": "Module took too long"}
    except Exception as e:
        logger.error(f"{module_name} error: {e}")
        return {"status": "error", "findings": [], "error": str(e)}
```

---

## Rule 14: Testing (Simple but Thorough)

**Required:**
- Unit tests for API endpoints (mock Celery tasks)
- Integration tests for module graceful degradation
- End-to-end test: create scan → poll status → get results
- Modules tested with real (or mocked) API calls

**Not required:**
- 100% coverage (80%+ is good for OSS)
- Load testing (single machine, low scale)
- UI testing (manual OK for OSS)

**Test structure:**
```
backend/tests/
├── conftest.py (pytest fixtures)
├── test_api.py (endpoint tests)
├── test_modules.py (module tests)
└── test_graceful_degrade.py (rate limit handling)
```

---

## Rule 15: Commit Message and Git Discipline

**Required:**
- Clear commit messages ("Add Maigret module", not "fix stuff")
- One feature per PR
- PR includes tests + documentation updates
- `README.md` updated if user-facing change

**Git workflow:**
```bash
git checkout -b add/maigret-module
# ... code ...
git commit -m "Add Maigret social profile discovery module

- Subprocess call to maigret CLI
- Parse JSON output
- Gracefully handle timeout
- Return 400+ profiles
"
git push origin add/maigret-module
# Create PR with description
```

---

## Checklist for Code Review (AI Agent)

Before marking code complete:
- [ ] No auth system added
- [ ] No API keys in code or .env
- [ ] No database migrations
- [ ] All modules handle timeouts gracefully
- [ ] SQLite auto-created at startup
- [ ] docker-compose up works without additional setup
- [ ] README updated with new features
- [ ] Tests pass (80%+ coverage)
- [ ] No telemetry or analytics
- [ ] All subprocesses have timeout (30-60s)
- [ ] Graceful degradation for rate limits
- [ ] Code is readable (no over-abstraction)
- [ ] Versions pinned in Dockerfile + requirements.txt
- [ ] Error messages are friendly to user

---

## Summary

osintkit OSS is a **keyless, stateless, self-hosted OSINT tool**. Build it to be **simple, transparent, and offline-capable**. Prioritize **code readability over clever optimization**. When APIs fail or rate-limit, **degrade gracefully and let users know**.

This is a tool for privacy researchers and developers who want to understand their digital footprint without vendor lock-in or SaaS friction. Code accordingly.
