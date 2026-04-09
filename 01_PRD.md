# osintkit OSS — Product Requirements Document

**Version:** 1.0  
**Status:** Planning  
**Last Updated:** 2026-04-09  
**Target Release:** Q2 2026

---

## Executive Summary

osintkit OSS is a free, open-source OSINT (Open Source Intelligence) digital footprint tool designed for developers, privacy researchers, and self-hosters. It aggregates data from social platforms, breach databases, paste sites, and dark web indexes to show users what personal information about them is publicly available.

**Key differentiator:** Zero API keys required. No accounts. No login. No quotas. Runs entirely offline or self-hosted with a single `docker compose up` command.

---

## Goals

1. **Enable privacy awareness** — Help individuals understand their digital footprint without proprietary tooling or vendor lock-in
2. **Reduce barrier to entry** — No API key signup, no paid tier, no SaaS friction — clone, run, scan
3. **Support self-hosting** — Designed from day one for privacy-conscious users who want to control their own infrastructure
4. **Remain fully open-source** — Publishable to GitHub under MIT license; no proprietary dependencies
5. **Gracefully degrade** — When free APIs hit rate limits, return partial results rather than failing

---

## Target Users

### Primary
- **Privacy researchers** — Need to understand commercial OSINT pipelines and what data is available for doxing/identification
- **Developers** — Want to self-host OSINT tools for personal or internal research, understand web scraping/API patterns
- **Self-hosters** — Prefer to run tools on their own infrastructure, avoid SaaS vendor risk

### Secondary
- **Security teams** — Use as part of phishing campaign research or employee digital footprint audits
- **Journalists** — Research public information for investigative reporting

### Non-target
- Penetration testers with restricted budgets (they have commercial tools)
- Enterprise OSINT platforms (this is intentionally simple)
- High-volume commercial data brokers (out of scope)

---

## Core Features

### 1. Social Profile Discovery
**Module:** Maigret + WhatsMyName  
**What it does:** Searches 400+ social networks (Reddit, Twitter, TikTok, LinkedIn, Facebook, GitHub, etc.) for usernames  
**Inputs:** Email, username, or phone  
**Rate limit:** None (local databases)  
**Output:** Discovered profiles with direct links  
**Graceful degradation:** N/A

### 2. Email Account Detection
**Module:** Holehe  
**What it does:** Checks if an email is registered on 100+ services (Google, Microsoft, Apple, PayPal, Spotify, etc.)  
**Inputs:** Email address  
**Rate limit:** None  
**Output:** List of services with registration status + password reset link status  
**Graceful degradation:** N/A

### 3. Breach & Password History
**Module:** HIBP PwnedPasswords (k-anonymity)  
**What it does:** Checks if a password or email appears in known breaches, using Privacy Pass protocol (no plaintext transmitted)  
**Inputs:** Email address or password  
**Rate limit:** None (API free, no key needed)  
**Output:** Breach count, breach names, password compromise status  
**Graceful degradation:** N/A

### 4. Web Presence & DNS Records
**Module:** theHarvester  
**What it does:** Discovers subdomains, email addresses, and DNS records for a target domain  
**Inputs:** Domain name  
**Rate limit:** None  
**Output:** Discovered subdomains, MX records, A records, associated email addresses  
**Graceful degradation:** N/A

### 5. SSL Certificate Transparency
**Module:** crt.sh (Certificate Transparency logs)  
**What it does:** Queries public CT logs for all SSL certificates issued for a domain  
**Inputs:** Domain name  
**Rate limit:** None  
**Output:** Certificate history, subdomains, issuance dates  
**Graceful degradation:** N/A

### 6. Paste Site Dumps
**Module:** psbdmp.ws API  
**What it does:** Searches publicly available paste sites (Pastebin, Pastie, etc.) for exposed data containing email/username/domain  
**Inputs:** Email, username, domain  
**Rate limit:** ~100 requests/day (free API)  
**Output:** Matching pastes with links  
**Graceful degradation:** Module runs until limit hit, returns partial results with note: "Rate limit reached — results may be incomplete. Run again tomorrow or self-host your own paste database."

### 7. Dark Web Index Search
**Module:** Ahmia.fi (Tor search engine)  
**What it does:** Searches dark web index for mentions of email/username/domain  
**Inputs:** Email, username, domain  
**Rate limit:** ~200 requests/day (free API)  
**Output:** Dark web references with .onion links  
**Graceful degradation:** Module runs until limit hit, returns partial results with note: "Rate limit reached — results may be incomplete. Run again tomorrow or self-host your own Ahmia instance."

---

## Out of Scope

### Not Included (Requires API Keys)
- BreachDirectory
- LeakCheck
- emailrep.io
- Google Custom Search Engine
- Hunter.io
- RocketReach
- Clearbit
- Shodan
- Censys
- VirusTotal API

**Rationale:** These require paid API keys or restrictive ToS. This version is truly keyless.

### Not Implemented
- User authentication or login
- Admin dashboard
- Database migrations
- Persistent user accounts
- Saved reports
- Email delivery of results
- Webhook notifications
- Caching across scans (ephemeral only)
- Rate limiting enforcement (transparent degradation instead)
- Telemetry or analytics

---

## Functional Requirements

### Scan Workflow
1. User opens web UI at `http://localhost:3000`
2. Enters target (email, username, domain, phone)
3. Selects modules to run (all checked by default)
4. Clicks "Scan"
5. Scan runs asynchronously; user polls for status
6. Results displayed in real-time as modules complete
7. User exports results as JSON or PDF (optional)
8. Results are ephemeral — no saved reports after browser close

### Data Model
- **Scans table** — `id`, `target`, `target_type`, `status`, `created_at`, `updated_at`, `modules` (JSON list), `results` (JSON blob)
- **Findings table** (optional) — `id`, `scan_id`, `module`, `finding_type`, `data` (JSON), `source_url`
- No user table — public endpoint, no auth
- SQLite, auto-created on first run

### API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/scans` | Create new scan |
| GET | `/api/scans/{scan_id}/status` | Poll scan status |
| GET | `/api/scans/{scan_id}` | Get full results |
| GET | `/api/scans/{scan_id}/export/json` | Download JSON |
| GET | `/api/scans/{scan_id}/export/pdf` | Download PDF |

### Input Validation
- Email: RFC 5322 basic regex
- Username: alphanumeric + underscore, 2-30 chars
- Domain: valid domain name
- Phone: numeric or international format
- Module list: from allowed enum

### Result Display
- Module results shown in tabs or cards
- Real-time updates (WebSocket or polling every 2s)
- Partial results OK — show what completed, note what failed due to rate limits
- Export buttons visible on completion

---

## Non-Functional Requirements

### Performance
- Scan should complete in 30-120 seconds (target = 60s average)
- Workers scale to 4 concurrent scans by default
- No persistent state between scans

### Reliability
- If one module fails (error, crash), other modules continue
- Rate-limited modules gracefully degrade, never block scan
- Transient API failures retry once
- Permanent API failures show friendly error message

### Scalability
- Designed for single-machine self-hosting (4 cores / 8GB RAM)
- No database connection pooling needed (SQLite)
- Redis serves only as message broker, not data store

### Security
- No external API keys stored (none exist)
- No user session tokens (no auth)
- HTTPS recommended but not required (localhost OK)
- CORS enabled for localhost:3000 and 0.0.0.0:8000
- No PII logging (results JSON may contain PII but not logged)

### Observability
- Simple request logging: method, path, status, latency
- Celery task logs to stdout
- No structured logging backend required

---

## Success Metrics

### Technical
- Setup time: < 5 minutes on fresh Linux VM
- Docker image size: < 2 GB
- Cold scan latency: < 2 minutes for all 7 modules
- Module pass rate: > 95% (graceful degradation for rate limits)

### User
- README completion time: < 10 minutes
- First scan success rate: > 90% (on first try)
- Export functionality used: > 50% of scans
- GitHub stars: > 500 by end of Q2 2026

### Adoption
- Clones/downloads: > 1000
- Pull requests (community contributions): > 5
- Forks: > 100

---

## Constraints

1. **No dependencies on services requiring keys** — Any module that requires paid API key is excluded
2. **Docker Compose only** — No Kubernetes, no serverless, no platform-specific scripts
3. **SQLite only** — No external database service; auto-create schema on startup
4. **Single-machine scope** — Designed for < 100 concurrent users max
5. **No authentication whatsoever** — Public endpoint, open to localhost or private network
6. **Ephemeral results only** — No saved reports, no historical data retention

---

## Risk & Mitigation

| Risk | Mitigation |
|------|-----------|
| Rate-limited APIs go down | Graceful degradation, partial results shown, user can re-run |
| OSINT tools have breaking changes | Pin versions in Docker, monitor GitHub releases, vendor alternatives |
| Users misuse for doxing/harassment | OSS, can't control downstream use; include responsible disclosure in README |
| High memory usage with large payloads | Limit result size per scan to 100 MB, stream JSON export |
| Celery task queue grows unbounded | Set result TTL to 24 hours, auto-clean old scan records |

---

## Release Checklist

- [ ] All 7 modules integrated and tested
- [ ] Web UI complete (scan form, results display, export buttons)
- [ ] Docker Compose setup tested on clean Ubuntu 22.04 VM
- [ ] README with 5-step setup guide
- [ ] `.env.example` with zero required keys
- [ ] LICENSE file (MIT)
- [ ] CONTRIBUTING.md with dev setup
- [ ] GitHub Actions CI/CD pipeline (test, build, push image)
- [ ] Sample scan results (JSON, PDF) in docs/
- [ ] Demo video (5 min): clone → compose up → scan → export

---

## Timeline

- **Week 1-2:** Foundation (Docker, FastAPI, Celery, Redis, SQLite)
- **Week 2-3:** OSINT modules (5 modules, test graceful degradation)
- **Week 4:** Frontend (Next.js, real-time updates, export)
- **Week 5:** Polish, testing, documentation, GitHub release

**Target launch:** End of Q2 2026
