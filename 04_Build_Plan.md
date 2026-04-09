# osintkit OSS — 5-Week Build Plan

**Version:** 1.0  
**Status:** Planning  
**Last Updated:** 2026-04-09  
**Target Launch:** End of Q2 2026 (Week 10)  
**Team Capacity:** 1-2 engineers

---

## Overview

This is a **5-week phased build plan** for osintkit OSS — a free, keyless OSINT tool. Phases progress from foundation → OSINT modules → frontend → polish & release. Simpler than the hosted version due to: no auth, no admin, no user accounts, no migrations.

---

## Phase 0: Preparation (Week 0, Pre-Build)

### Goal
Set up project structure, scaffolding, CI/CD, and development environment.

### Tasks

#### 0.1 Repository Setup
- [ ] Create GitHub repository `osintkit-oss`
- [ ] Initialize git with standard structure (frontend/, backend/, docs/, .github/)
- [ ] Add `.gitignore` (Python, Node.js, Docker, .env)
- [ ] Create LICENSE file (MIT)
- [ ] Create CONTRIBUTING.md
- [ ] Create CODE_OF_CONDUCT.md (standard OSS)
- [ ] Create `.env.example` (zero required keys)
- [ ] Create `.dockerignore` (exclude node_modules, .git, __pycache__)

#### 0.2 Docker Setup
- [ ] Create Dockerfile for API service (Python 3.11, FastAPI, Celery)
- [ ] Create Dockerfile for frontend service (Node 18, Next.js)
- [ ] Create docker-compose.yml (4 services: api, frontend, worker, redis)
- [ ] Create docker-compose.dev.yml (hot reload, debug logs)
- [ ] Test: `docker-compose up` on clean machine

#### 0.3 Backend Scaffolding
- [ ] Create FastAPI app structure (main.py, models.py, tasks.py, utils/)
- [ ] Setup Celery config (Redis broker, result backend)
- [ ] Setup SQLite schema init function
- [ ] Setup logging (stdout, JSON format optional)
- [ ] Setup requirements.txt (FastAPI, Celery, Redis, SQLAlchemy, httpx, etc.)
- [ ] Setup pytest + conftest for tests

#### 0.4 Frontend Scaffolding
- [ ] Create Next.js 14 app (`npx create-next-app@14`)
- [ ] Setup TypeScript + Tailwind
- [ ] Setup package.json + package-lock.json
- [ ] Setup basic layout (navbar, footer)
- [ ] Setup API client wrapper (lib/api.ts)

#### 0.5 CI/CD
- [ ] Create GitHub Actions workflow (test, build, push)
- [ ] Workflow runs on PR: pytest, prettier, type check
- [ ] Manual release workflow (on tag): build images, push to Docker Hub (optional)

#### 0.6 Documentation Scaffolding
- [ ] Create docs/MODULES.md (template for each module)
- [ ] Create docs/API.md (API reference template)
- [ ] Create docs/DEPLOYMENT.md (self-hosting guide)
- [ ] Create README.md (stub, fill in during Phase 5)

**Deliverables:**
- GitHub repo with clean structure
- All services start with `docker compose up`
- Tests run with `pytest`
- Frontend builds with `npm run build`

**Estimated Time:** 2-3 days

---

## Phase 1: Foundation (Week 1)

### Goal
Build core API, database, task queue, and health checks.

### Tasks

#### 1.1 FastAPI Core
- [ ] Implement POST /api/scans (create scan, enqueue task)
- [ ] Implement GET /api/scans/{scan_id}/status (poll status)
- [ ] Implement GET /api/scans/{scan_id} (get results)
- [ ] Add input validation (Pydantic models)
- [ ] Add CORS middleware (localhost:3000, 0.0.0.0)
- [ ] Add health check endpoint GET /api/health
- [ ] Add request logging middleware

#### 1.2 SQLite Database
- [ ] Design schema (scans, findings tables)
- [ ] Implement init_db() (called on startup, CREATE TABLE IF NOT EXISTS)
- [ ] Implement query functions (get_scan, create_scan, update_scan)
- [ ] Test: scan created and retrieved from SQLite

#### 1.3 Celery + Redis
- [ ] Configure Celery with Redis broker/backend
- [ ] Implement `run_scan` Celery task (placeholder, chains OSINT modules)
- [ ] Implement task status callback (update scan.status in DB)
- [ ] Test: task queued, executed, status updated

#### 1.4 Task Orchestration
- [ ] Implement task chaining (Module1 → Module2 → ... → Module7)
- [ ] Implement error handling (one module fails, others continue)
- [ ] Implement result aggregation (all results in one JSON blob)
- [ ] Test: run_scan completes for all 7 modules (stub implementations)

#### 1.5 Testing
- [ ] Unit tests: POST /api/scans validates input
- [ ] Unit tests: GET /api/scans/{id} returns scan
- [ ] Integration test: create scan → task runs → status updates
- [ ] Test: SQLite auto-creates on startup

**Deliverables:**
- API endpoints working (status polling)
- Celery task queuing + execution
- SQLite persisting scan records
- Health checks passing
- 70%+ test coverage for API

**Estimated Time:** 1 week

---

## Phase 2: OSINT Modules (Week 2-3)

### Goal
Implement all 7 OSINT modules with graceful degradation and rate limit handling.

### Module Implementation Order (easiest → hardest)

#### 2.1 Social Profile Discovery (Maigret)
- [ ] Research Maigret: CLI tool, JSON output, 400+ networks
- [ ] Install Maigret in Docker image (pip install maigret)
- [ ] Implement subprocess wrapper (timeout=60s)
- [ ] Parse JSON output
- [ ] Handle errors (timeout, subprocess exit codes)
- [ ] Test: run Maigret, verify 10+ profiles found
- [ ] Time estimate: 2 days

#### 2.2 Email Account Detection (Holehe)
- [ ] Research Holehe: Python package or CLI
- [ ] Install Holehe in Docker
- [ ] Implement subprocess or direct import
- [ ] Check 100+ services (Google, Microsoft, Apple, PayPal, etc.)
- [ ] Parse output
- [ ] Test: check email, verify 5+ services detected
- [ ] Time estimate: 1.5 days

#### 2.3 Breach & Password History (HIBP)
- [ ] Research HIBP PwnedPasswords API (k-anonymity, no plaintext)
- [ ] Implement HTTP call (5-character prefix hash)
- [ ] Implement binary search for password in response
- [ ] Test: known compromised password returns hit
- [ ] Test: secure password returns miss
- [ ] Time estimate: 1 day

#### 2.4 Web Presence (theHarvester)
- [ ] Research theHarvester: Python package, multiple sources
- [ ] Install in Docker
- [ ] Implement wrapper (limit to public sources: Google, Bing, crt.sh)
- [ ] Parse output (subdomains, emails, A records)
- [ ] Test: run for example.com, verify 5+ subdomains
- [ ] Time estimate: 1.5 days

#### 2.5 SSL Certificate Transparency (crt.sh)
- [ ] Research crt.sh: public API, JSON output
- [ ] Implement HTTP call (no auth needed)
- [ ] Parse certificate data (subdomains, issuance dates)
- [ ] Test: query example.com, verify certs returned
- [ ] Time estimate: 1 day

#### 2.6 Paste Site Search (psbdmp.ws)
- [ ] Research psbdmp.ws API (free, ~100 req/day limit)
- [ ] Implement HTTP call
- [ ] **Implement rate limit handling (HTTP 429 → graceful degradation)**
- [ ] Return partial results + metadata on rate limit
- [ ] Test: verify rate limit returns partial results, doesn't crash
- [ ] Time estimate: 2 days

#### 2.7 Dark Web Search (Ahmia.fi)
- [ ] Research Ahmia API (Tor search, free, ~200 req/day limit)
- [ ] Implement HTTP call
- [ ] **Implement rate limit handling (HTTP 429 → graceful degradation)**
- [ ] Return dark web references (.onion links)
- [ ] Test: verify rate limit returns partial results
- [ ] Time estimate: 2 days

### Module Integration
- [ ] Chain all 7 modules in Celery task
- [ ] Parallel execution (Celery group or sequential with async)
- [ ] Aggregate results into single JSON
- [ ] Test: full scan completes in 60-120s
- [ ] Test: graceful degradation for rate limits

### Testing
- [ ] Unit tests for each module (mock API responses)
- [ ] Integration test: all 7 modules in sequence
- [ ] Stress test: run same scan 3x to verify rate limits
- [ ] Test: partial results on rate limit, scan not blocked

**Deliverables:**
- All 7 OSINT modules integrated
- Graceful degradation for rate limits (psbdmp, Ahmia)
- Results JSON validated against schema
- 75%+ test coverage for modules

**Estimated Time:** 2 weeks (9 days active development)

---

## Phase 3: Frontend (Week 4)

### Goal
Build responsive web UI for scan submission, real-time results, and export.

### Tasks

#### 3.1 Scan Form
- [ ] Create ScanForm.tsx component (input field, module checkboxes)
- [ ] Add input validation (email/username/domain format)
- [ ] Add submit button (POST /api/scans)
- [ ] Handle loading state (disabled button, spinner)
- [ ] Test: form submission creates scan

#### 3.2 Results Display
- [ ] Create ResultsDisplay.tsx component (tabs or cards for each module)
- [ ] Create ModuleCard.tsx (one card per module: findings count, status)
- [ ] Add real-time polling (GET /api/scans/{id}/status every 2s)
- [ ] Update UI as modules complete
- [ ] Show "Rate limit reached" note for partial results
- [ ] Test: poll status, UI updates in real-time

#### 3.3 Findings View
- [ ] Display findings per module (tables or lists)
- [ ] Show source URLs (clickable links)
- [ ] For social profiles: platform name, username, profile URL
- [ ] For email: service name, account exists, reset URL
- [ ] For breach: breach name, password hit count
- [ ] For web: subdomains, emails, A records
- [ ] For cert: certificate dates, issuers
- [ ] For paste: paste site, content preview
- [ ] For dark web: .onion references

#### 3.4 Export Functionality
- [ ] Create ExportButtons.tsx (JSON, PDF)
- [ ] Implement JSON export (GET /api/scans/{id}/export/json)
- [ ] Implement PDF export (GET /api/scans/{id}/export/pdf)
- [ ] Backend: PDF generation (ReportLab or WeasyPrint)
- [ ] Test: exports download correctly

#### 3.5 Layout & Styling
- [ ] Create main layout (header, scan form, results)
- [ ] Add Tailwind styling (dark mode optional)
- [ ] Responsive design (mobile, tablet, desktop)
- [ ] Add loading spinner, error states
- [ ] Test: responsive on mobile + desktop

#### 3.6 Navigation
- [ ] Home page (/): scan form
- [ ] Results page (/scan/{id}): results display
- [ ] Redirect to results after scan creation
- [ ] Back button to create new scan

### Testing
- [ ] Unit tests: ScanForm validation
- [ ] Integration tests: form → API → results display
- [ ] Manual: full flow (scan → poll → results → export)
- [ ] Visual regression: screenshots on key pages

**Deliverables:**
- Fully functional web UI
- Scan form → results display → export working end-to-end
- Mobile responsive
- 60%+ test coverage for frontend

**Estimated Time:** 1 week

---

## Phase 4: Graceful Degradation & Polish (Week 5)

### Goal
Ensure all edge cases handled, rate limits managed, tests pass, documentation complete.

### Tasks

#### 4.1 Rate Limit Testing
- [ ] Stress test psbdmp.ws module (100+ requests, verify HTTP 429 handling)
- [ ] Stress test Ahmia.fi module (200+ requests, verify graceful degradation)
- [ ] Verify scan continues after rate limit (other modules complete)
- [ ] Verify partial results shown to user with clear note
- [ ] Test: run same email 3x, verify incrementally degrading results

#### 4.2 Error Handling
- [ ] Test: Maigret subprocess timeout (kill process after 60s)
- [ ] Test: API unreachable (Redis down, SQLite locked)
- [ ] Test: invalid input (malformed email, SQL injection attempt)
- [ ] Verify: friendly error messages shown to user
- [ ] Verify: errors logged, not exposed in API response

#### 4.3 Performance Optimization
- [ ] Profile Celery task execution (identify slow modules)
- [ ] Optimize if needed (caching, parallel execution)
- [ ] Target: full scan < 120s
- [ ] Test: cold start (all modules start simultaneously)
- [ ] Test: memory usage (verify no leaks after 10 scans)

#### 4.4 Security Review
- [ ] Verify: no API keys in code or .env
- [ ] Verify: no plaintext passwords logged
- [ ] Verify: CORS correctly configured (localhost only)
- [ ] Verify: no SQL injection vulnerabilities (use parameterized queries)
- [ ] Verify: no stored user data across scans

#### 4.5 Docker Testing
- [ ] Test: `docker-compose up` on clean Ubuntu 22.04 VM (no pre-installed tools)
- [ ] Test: Services start in correct order
- [ ] Test: Health checks pass
- [ ] Test: Data persists across restarts (SQLite volume)
- [ ] Test: Logs readable via `docker logs`

#### 4.6 Documentation
- [ ] Complete README.md (setup, features, modules, API, limitations)
- [ ] Complete CONTRIBUTING.md (dev setup, PR process)
- [ ] Complete docs/MODULES.md (detailed per-module docs)
- [ ] Complete docs/API.md (full API reference with curl examples)
- [ ] Complete docs/DEPLOYMENT.md (self-hosting on VPS, reverse proxy, HTTPS)
- [ ] Create docs/SCREENSHOTS/ (sample results, UI flow)
- [ ] Create LIMITATIONS.md (rate limits, what's not included, responsible use)

#### 4.7 GitHub Release Prep
- [ ] Create GitHub release template (.github/RELEASE_TEMPLATE.md)
- [ ] Create GitHub issue templates (bug, feature request)
- [ ] Create GitHub PR template (.github/pull_request_template.md)
- [ ] Add GitHub Actions status badge to README
- [ ] Add Docker Hub links (if pushing images)

#### 4.8 Demo & Video
- [ ] Record demo video (5 min: clone → compose up → scan → export)
- [ ] Upload to docs/DEMO.md with link
- [ ] Create sample output files (JSON, PDF) in docs/samples/

### Testing
- [ ] Full test suite passes (90%+ coverage)
- [ ] Integration test: full end-to-end scan
- [ ] Load test: 10 concurrent scans
- [ ] Security audit: no hardcoded secrets, no PII leaks

**Deliverables:**
- All tests passing
- Comprehensive documentation
- GitHub repo ready for release
- Demo video
- Sample results (JSON, PDF)

**Estimated Time:** 1 week

---

## Phase 5: Release & Launch (Week 5, Final 2 days)

### Goal
Publish to GitHub, Docker Hub, create release notes.

### Tasks

#### 5.1 Final Checklist
- [ ] All 7 OSINT modules working
- [ ] All tests passing (pytest, frontend tests)
- [ ] docker-compose up works on clean machine
- [ ] README complete with 5-step setup
- [ ] .env.example has zero required keys
- [ ] LICENSE file (MIT) present
- [ ] CONTRIBUTING.md present
- [ ] CODE_OF_CONDUCT.md present
- [ ] GitHub Actions passing on main branch

#### 5.2 GitHub Release
- [ ] Create git tag: `v1.0.0`
- [ ] Create GitHub Release with notes:
  - Description: what is osintkit OSS, quick start
  - Features: list all 7 modules, rate limits
  - Installation: clone → compose up
  - Getting started: link to README
  - Known limitations: rate limits, what's not included
  - Screenshots: sample results
  - Demo video link
- [ ] Attach sample output files (JSON, PDF)

#### 5.3 Docker Hub (Optional)
- [ ] Build images: osintkit-api, osintkit-frontend
- [ ] Push to Docker Hub (optional, GitHub Container Registry OK too)
- [ ] Update docker-compose.yml to use published images
- [ ] Add Docker pull instructions to README

#### 5.4 Community
- [ ] Post on GitHub (Discussions, Releases tab)
- [ ] Post on Hacker News (optional, if appropriate)
- [ ] Post on product communities (ProductHunt, Lobsters, etc.)
- [ ] Link in README to r/privacy, r/osint (optional, if rules allow)

#### 5.5 Post-Launch
- [ ] Monitor GitHub issues (respond to bugs, feature requests)
- [ ] Fix critical bugs within 24h
- [ ] Plan v1.1 features based on feedback

**Deliverables:**
- GitHub Release v1.0.0
- Docker images published (optional)
- README, API docs, deployment guide complete
- Demo video published
- Community posts

**Estimated Time:** 2 days

---

## Parallel Work & Team Allocation

If 2 engineers available:

**Engineer A (Backend Focus):**
- Phases 0-2: Core API, database, all OSINT modules
- Week 3: Rate limit testing, error handling
- Week 4: Support frontend, PDF export

**Engineer B (Frontend Focus):**
- Phase 0: Frontend scaffolding
- Phase 3: UI, forms, results display, export
- Week 4: Polish, responsive design, E2E tests
- Week 5: Demo video, community

**Overlap:**
- Phase 1: Both on API design + DB schema
- Phase 2: Daily standups, integration testing
- Phase 4: Full team on testing + documentation
- Phase 5: Final release together

---

## Risk Mitigation

| Risk | Mitigation | Owner |
|------|-----------|-------|
| OSINT tool breaking changes | Pin versions, monitor GH releases, test on upgrade | Backend |
| Rate limit API changes | Monitor psbdmp, Ahmia status, fallback to alternatives | Backend |
| Docker build failures | Test on clean machine early, version pinning | DevOps |
| Celery task queue bottleneck | Profile early, optimize if needed (parallel execution) | Backend |
| Frontend performance | Test on slow network, optimize bundle size | Frontend |
| Security vulnerability (PII leak) | Code review, no logging PII, HTTPS in prod | Backend + Security |

---

## Success Criteria (End of Week 5)

### Technical
- [ ] All 7 OSINT modules integrated, tested, working
- [ ] Graceful degradation for rate limits (psbdmp, Ahmia)
- [ ] `docker compose up` works on clean Ubuntu 22.04
- [ ] Setup time < 5 minutes
- [ ] Full scan completes in 60-120s
- [ ] All tests passing (80%+ coverage)

### User Experience
- [ ] Scan form intuitive, validation clear
- [ ] Results display real-time, easy to understand
- [ ] Export (JSON, PDF) works without friction
- [ ] README can be followed in < 10 minutes
- [ ] First-time user success rate > 90%

### Community
- [ ] GitHub repo public, MIT licensed
- [ ] README, API docs, deployment guide complete
- [ ] Demo video uploaded
- [ ] 50+ stars in first week (stretch)

---

## Post-Launch Roadmap (Future)

### v1.1 (Month 2)
- [ ] WebSocket for real-time updates (instead of polling)
- [ ] Dark mode UI
- [ ] Advanced filtering (e.g., show only high-confidence results)
- [ ] User feedback integration

### v1.2 (Month 3)
- [ ] API authentication (optional, for self-hosters wanting access control)
- [ ] Multiple search profiles (save scan templates)
- [ ] Scheduled scans (cron-based)
- [ ] Webhook notifications (on completion)

### v2.0 (Future)
- [ ] Commercial "osintkit Pro" variant (hosted, commercial support, more modules)
- [ ] CLI tool (`osintkit-cli` Python package)
- [ ] Browser extension
- [ ] Integration with threat intelligence platforms

---

## Weekly Standup Template

```
## Week X Standup

### Completed
- [ ] Task 1
- [ ] Task 2

### In Progress
- [ ] Task 3 (90%)
- [ ] Task 4 (50%)

### Blockers
- Issue with X (need help from Y)

### Next Week
- Task 5
- Task 6
```

---

## Appendix: Command Reference

### Local Development
```bash
# Setup
git clone https://github.com/username/osintkit-oss
cd osintkit-oss
cp .env.example .env

# Start services
docker compose -f docker-compose.dev.yml up

# Run tests
docker compose exec api pytest
npm test  # (from frontend/)

# Logs
docker compose logs -f api
docker compose logs -f worker
```

### Docker Build
```bash
# Build locally
docker compose build

# Push to registry
docker tag osintkit-api:latest username/osintkit-api:v1.0.0
docker push username/osintkit-api:v1.0.0
```

### Testing
```bash
# Backend tests
cd backend
pytest --cov=. --cov-report=html

# Frontend tests
cd frontend
npm test -- --coverage
```

### Release
```bash
# Tag release
git tag -a v1.0.0 -m "osintkit OSS v1.0.0"
git push origin v1.0.0

# Create GitHub Release
gh release create v1.0.0 --title "osintkit OSS v1.0.0" --notes "See README.md"
```

---

## Summary

**5-week phased build:**
- **Week 0:** Scaffolding & setup
- **Week 1:** Core API, database, task queue
- **Week 2-3:** 7 OSINT modules + graceful degradation
- **Week 4:** Frontend + polish
- **Week 5:** Testing, documentation, release

**Key principles:**
- Ship early, iterate based on feedback
- Graceful degradation over hard failures
- Simple code over clever code
- No API keys, no auth, no migrations
- Docker Compose is the deployment story

**Expected outcome:** Functional, documented, deployable OSINT tool ready for GitHub release.
