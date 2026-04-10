# osintkit

OSINT CLI for personal digital footprint analysis. Input an email, phone, username, or name — get a risk-scored report saved locally as JSON, HTML, and Markdown.

MIT licensed. No server. Everything stays on your machine.

## Installation

```bash
npm install -g osintkit
```

This automatically installs all Python dependencies (core + optional OSINT tools) via the postinstall script. Just run `osintkit new` when it's done.

**Requirements:** Python 3.10+, Node.js 16+

## Quick Start

```bash
osintkit setup      # Configure API keys (optional, all have free tiers)
osintkit new        # Create a profile and run a scan
osintkit list       # View all profiles
osintkit refresh    # Re-run scan on a profile
osintkit open       # View profile details + open latest report
```

## Commands

| Command | Description |
|---------|-------------|
| `osintkit new` | Create a new profile and optionally run a scan |
| `osintkit list` | List all profiles with last risk score |
| `osintkit refresh [id]` | Re-run scan for a profile |
| `osintkit open [id]` | Show profile details and open latest report |
| `osintkit export [id]` | Export as JSON or Markdown |
| `osintkit setup` | Configure API keys interactively (preserves existing keys) |
| `osintkit config set-key <key> <value>` | Update a single API key without touching others |
| `osintkit config show` | Show which API keys are set (values hidden) |
| `osintkit delete [id]` | Delete a profile |
| `osintkit version` | Show version |

## What It Checks

### Stage 1 — No API keys needed, works out of the box

| Module | Input | What it does |
|--------|-------|-------------|
| Maigret | username | 3000+ sites |
| Sherlock | username | 400+ sites |
| Holehe | email | 120+ platform registrations |
| HIBP k-anonymity | email | Password breach check (no key) |
| Gravatar | email | Profile existence + avatar |
| theHarvester | email/domain | Web presence, subdomains |
| crt.sh | email/domain | Certificate transparency |
| Wayback CDX | email | Historical web appearances |
| libphonenumber | phone | Carrier, region, line type (offline) |
| Paste search | email | Paste site appearances |
| Data brokers | name/email | Google CSE broker scan |
| Dark web | email | Ahmia / public index |
| Breach lookup | email | BreachDirectory |
| GitHub | username | Public profile (always runs, no key needed) |

### Stage 2 — Optional API keys, unlocks extra data sources

| Service | Input | Tier |
|---------|-------|------|
| HaveIBeenPwned | email | Paid ($3.50/month) |
| LeakCheck | email/phone/user | Free tier |
| NumVerify | phone | 100/month free |
| Hunter.io | email | 25/month free |
| SecurityTrails | domain | Paid |

Stage 2 modules only run when a key is configured. If rate-limited, the scan continues gracefully with Stage 1 results — rate-limited modules are shown as yellow, not red.

## Output

Each scan creates a folder at `~/osint-results/<target>_<date>/` containing:
- `report.html` — rendered report with risk score
- `findings.json` — full structured data
- `findings.md` — markdown summary

Risk score is 0–100 based on breach exposure, social footprint, data broker listings, and dark web/paste appearances.

## API Keys (All Optional)

Keys are stored in `~/.osintkit/config.yaml` (permissions: 600).

```bash
osintkit config set-key hunter YOUR_KEY    # add or update one key
osintkit config show                        # see which keys are set
osintkit setup                              # interactive wizard (preserves existing keys)
```

| Service | Where to get it | Free? |
|---------|----------------|-------|
| HaveIBeenPwned | haveibeenpwned.com/API/Key | Paid ($3.50/mo) |
| LeakCheck | leakcheck.io | Free tier |
| NumVerify | numverify.com | 100 req/month free |
| Hunter.io | hunter.io | 25 req/month free |
| GitHub | github.com/settings/tokens | Free (raises rate limit) |
| Intelbase | intelbase.is | 100 req/month free |
| BreachDirectory | rapidapi.com (search "BreachDirectory") | 50 req/day free |
| Google CSE | developers.google.com/custom-search | 100 req/day free |
| SecurityTrails | securitytrails.com | Paid |

## Run from Source

```bash
git clone https://github.com/diesesschnitzel/osintkit.git
cd osintkit
pip install -r requirements.txt -r requirements-tools.txt
PYTHONPATH=. python3 -m osintkit.cli new
```

## Ethics

Only use osintkit on targets you have explicit permission to investigate. GDPR applies to EU subjects. A disclaimer is shown before every scan.

## License

MIT
