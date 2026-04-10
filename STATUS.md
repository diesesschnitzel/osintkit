# osintkit OSS - Current Status

**Last Updated:** 2026-04-10

---

## Current Status: SHIP-READY ✅

v0.1.2 — All QA issues resolved.

---

## What Works ✅

### CLI Commands
```bash
npm install -g osintkit    # Global install
osintkit new               # Create profile
osintkit list              # List profiles
osintkit refresh <id>      # Run scan
osintkit open <id>         # View profile
osintkit export <id>       # Export JSON/MD
osintkit setup             # Configure API keys
osintkit version           # Print version
```

Or run directly from source:
```bash
cd /Users/Shared/projekte/osintkit-oss
PYTHONPATH=. python3 -m osintkit.cli new
```

### Features
- First-time setup wizard with API key prompts
- Profile management (create, list, show, delete)
- Duplicate detection (warns if name/email already exists)
- Async parallel scan with progress display
- JSON, HTML, and Markdown export
- Risk score calculation (0–100)
- API key scrubbing — keys never appear in output files
- 15 Stage 1 modules (no API key required)
- 5 Stage 2 modules (activated when keys are configured)

### Modules
```
osintkit/modules/
├── social.py               # Maigret (3000+ sites)
├── sherlock.py             # Sherlock (400+ sites)
├── holehe.py               # Email → 120+ platform check
├── hibp.py                 # HIBP full breach lookup
├── hibp_kanon.py           # HIBP k-anonymity (no key)
├── gravatar.py             # Gravatar email check
├── harvester.py            # theHarvester web presence
├── certs.py                # crt.sh certificate transparency
├── breach.py               # BreachDirectory / LeakCheck
├── dark_web.py             # Intelbase / Ahmia
├── paste.py                # psbdmp paste search
├── brokers.py              # Google CSE data broker search
├── phone.py                # NumVerify phone lookup
├── libphonenumber_info.py  # Offline carrier/region/type
├── wayback.py              # Wayback Machine CDX API
└── stage2/
    ├── leakcheck.py
    ├── hunter.py
    ├── numverify.py
    ├── github_api.py
    └── securitytrails.py
```

---

## QA Results (2026-04-10)

| Category | Status |
|----------|--------|
| Unit Tests | ✅ 12/12 PASS |
| Stage 1 Scan | ✅ 13/15 (2 optional tools) |
| Phone Scan | ✅ PASS |
| Output Files | ✅ JSON/HTML/MD all valid |
| API Key Security | ✅ No leaks |
| NPM Shim | ✅ Fixed in v0.1.2 |

### Optional tools (improve coverage, not required)
```bash
pip install -r requirements-tools.txt   # maigret, holehe, theHarvester
```

---

## v0.1.2 Fixes

**NPM Shim (bin/osintkit.js)**
- Root cause: shim was not setting `PYTHONPATH`, so `python -m osintkit` failed unless the package had been pip-installed globally.
- Fix: shim now injects `PYTHONPATH=<packageDir>` so the package is always importable regardless of install method.
- Shim now checks for a local `.venv` or `venv` Python first — works correctly with venv-based local installs.

---

## Configuration

```
~/.osintkit/
├── config.yaml     # API keys and settings (created on first run)
└── profiles.json   # Profiles + scan history (auto-created)
```

## Free API Keys (all optional)

| Service | Free Limit | Purpose |
|---------|------------|---------|
| Have I Been Pwned | 10/min | Full breach names |
| NumVerify | 100/month | Phone carrier/location |
| Intelbase | 100/month | Dark web + paste |
| BreachDirectory | 50/day | Breach lookups |
| Google CSE | 100/day | Data broker detection |
| LeakCheck | Free tier | 7.5B breach records |
| Hunter.io | 50/month | Email finder |
| GitHub | 5000/hr w/ key | Profile enrichment |
| SecurityTrails | Free tier | DNS history |

---

**END OF STATUS REPORT**
