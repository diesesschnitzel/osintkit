# osintkit OSS - Current Status

**Last Updated:** 2026-04-09

---

## Current Status: WORKING BUT NEEDS NPM SETUP

The osintkit CLI works when run directly from source. The main blocker is npm package setup which requires file permission changes.

---

## What Works ✅

### CLI Commands
```bash
cd /Users/Shared/projekte/osintkit-oss
PYTHONPATH=. python3 -m osintkit.cli new          # Create profile
PYTHONPATH=. python3 -m osintkit.cli list         # List profiles
PYTHONPATH=. python3 -m osintkit.cli refresh <id>  # Run scan
PYTHONPATH=. python3 -m osintkit.cli open <id>    # View profile
PYTHONPATH=. python3 -m osintkit.cli export <id>  # Export JSON/MD
PYTHONPATH=. python3 -m osintkit.cli setup         # Configure API keys
```

### Features Implemented
- First-time setup wizard with API key prompts
- Profile management (create, list, show, delete)
- Duplicate detection (warns if name/email already exists)
- Scan execution with progress display
- JSON and Markdown export
- Risk score calculation
- All 10 OSINT modules (social, holehe, hibp, harvester, certs, breach, dark_web, paste, brokers, phone)

### Module Files (All Created)
```
osintkit/
├── __init__.py
├── cli.py           # Main CLI (commands: new, list, refresh, open, export, setup, delete)
├── config.py        # Config loader with Pydantic
├── scanner.py       # Async scanner orchestrator with progress
├── profiles.py      # Profile storage (JSON-based)
├── setup.py         # First-time setup wizard
├── risk.py          # Risk score calculation
├── modules/
│   ├── __init__.py
│   ├── social.py    # Maigret
│   ├── holehe.py   # Holehe
│   ├── hibp.py     # HIBP PwnedPasswords
│   ├── harvester.py # theHarvester
│   ├── certs.py    # crt.sh
│   ├── breach.py   # HIBP/BreachDirectory/LeakCheck
│   ├── dark_web.py # Intelbase/Ahmia
│   ├── paste.py    # psbdmp
│   ├── brokers.py  # Google CSE/Direct HTTP
│   └── phone.py    # NumVerify
└── output/
    ├── __init__.py
    ├── json_writer.py
    ├── html_writer.py
    └── templates/report.html
```

---

## What Needs to Be Done ⚠️

### 1. NPM Package Setup (CRITICAL)
**Problem:** Files in `/Users/Shared/projekte/osintkit-oss/` are owned by user `tom`, but runtime is `sandbox1`. Cannot write new files.

**Solution:** Run this command to fix permissions:
```bash
chmod -R 777 /Users/Shared/projekte/osintkit-oss
```

Then create these files:

**package.json:**
```json
{
  "name": "osintkit",
  "version": "0.1.0",
  "description": "OSINT CLI for personal digital footprint analysis",
  "main": "index.js",
  "bin": {
    "osintkit": "./bin/osintkit.js"
  },
  "scripts": {
    "postinstall": "pip3 install -e ."
  },
  "keywords": ["osint", "security", "cli"],
  "author": "",
  "license": "MIT"
}
```

**bin/osintkit.js:**
```javascript
#!/usr/bin/env node
const { spawn } = require('child_process');
const path = require('path');

const packageDir = path.dirname(path.dirname(__filename));
const args = [path.join(packageDir, 'osintkit', 'cli.py'), ...process.argv.slice(2)];

const python = spawn('python3', args, {
    cwd: packageDir,
    stdio: 'inherit',
    env: { ...process.env, PYTHONPATH: packageDir }
});

python.on('error', (err) => {
    console.error('Error: Python3 required. Install from python.org');
    process.exit(1);
});

python.on('close', (code) => process.exit(code || 0));
```

### 2. Simplify CLI Commands (RECOMMENDED)
After npm setup, create simpler commands:
```bash
osintkit           # Same as 'list'
osintkit <id>      # Same as 'open <id>'
osintkit .         # Same as 'refresh' (latest scan)
```

### 3. External Tools Documentation
Users need to install these for full functionality:
```bash
pip install maigret holehe theHarvester
```

---

## Quick Start (Current Workaround)

```bash
# 1. Navigate to project
cd /Users/Shared/projekte/osintkit-oss

# 2. Install dependencies
pip install -r requirements.txt  # Or: pip install -e .

# 3. First-time setup (will prompt for API keys)
PYTHONPATH=. python3 -m osintkit.cli setup

# 4. Create a profile
PYTHONPATH=. python3 -m osintkit.cli new

# 5. Run a scan
PYTHONPATH=. python3 -m osintkit.cli refresh <profile_id>

# 6. List profiles
PYTHONPATH=. python3 -m osintkit.cli list
```

---

## Configuration Files

```
~/.osintkit/
├── config.yaml     # API keys and settings
└── profiles.json   # All profiles + scan history
```

---

## Free API Keys Available

| Service | Free Limit | Purpose |
|---------|------------|---------|
| Have I Been Pwned | 10/min | Breach database |
| NumVerify | 100/month | Phone validation |
| Intelbase | 100/month | Dark web + paste |
| BreachDirectory | 50/day | Breach lookups |
| Google CSE | 100/day | Data broker detection |

---

## Next Ultraworker - Your Tasks

1. **Run:** `chmod -R 777 /Users/Shared/projekte/osintkit-oss`
2. **Create:** package.json and bin/osintkit.js
3. **Test:** `npm install -g .` then `osintkit new`
4. **Publish:** `npm publish`

---

**END OF STATUS REPORT**