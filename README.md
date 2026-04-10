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
| `osintkit setup` | Configure API keys |
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

### Stage 2 — Optional free API keys, runs first when configured

| Service | Input | Free Tier |
|---------|-------|-----------|
| HaveIBeenPwned | email | Free w/ key |
| LeakCheck | email/phone/user | Free tier |
| NumVerify | phone | 100/month |
| Hunter.io | name + domain | 50/month |
| GitHub API | username | 5000/hr w/ key |
| SecurityTrails | domain | Free tier |

Stage 2 always runs first when a key is configured. If rate-limited or key missing, falls back to Stage 1 automatically.

## Output

Each scan creates a folder at `~/osint-results/<target>_<date>/` containing:
- `report.html` — rendered report with risk score
- `findings.json` — full structured data
- `findings.md` — markdown summary

Risk score is 0–100 based on breach exposure, social footprint, data broker listings, and dark web/paste appearances.

## API Keys (All Optional)

Run `osintkit setup` to configure. All keys are optional — the tool works without any of them.

```
~/.osintkit/config.yaml
```

| Service | Get key at |
|---------|-----------|
| HaveIBeenPwned | haveibeenpwned.com/API/Key |
| LeakCheck | leakcheck.io |
| NumVerify | numverify.com |
| Hunter.io | hunter.io |
| GitHub | github.com/settings/tokens |
| Intelbase | intelbase.is |
| BreachDirectory | rapidapi.com |
| Google CSE | developers.google.com/custom-search |
| SecurityTrails | securitytrails.com |

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
