# osintkit

OSINT CLI for personal digital footprint analysis. Input an email, phone, username, or name — get a risk-scored report saved locally as JSON, HTML, and Markdown.

MIT licensed. No server. Everything stays on your machine.

📖 **Full documentation:** [docs.codecho.de/osintkit](https://docs.codecho.de/osintkit/)

## Installation

```bash
npm install -g osintkit
```

This automatically installs all Python dependencies via the postinstall script. Just run `osintkit new` when it's done.

**Requirements:** Python 3.10+, Node.js 16+

## Quick Start

```bash
osintkit setup      # Configure API keys (optional, all have free tiers)
osintkit scan alice@example.com  # Scan directly — no profile needed
osintkit new        # Create a profile and run a scan
osintkit list       # View all profiles
osintkit refresh    # Re-run scan on a profile
osintkit open       # View profile details + open latest report
```

## Commands

| Command | Alias | Description |
|---------|-------|-------------|
| `osintkit scan [target]` | `sc` | Scan directly — no profile needed |
| `osintkit new` | `n` | Create a new profile and run a scan |
| `osintkit list` | `ls` | List all profiles with last risk score |
| `osintkit refresh [id]` | `r` | Re-run scan for a profile |
| `osintkit open [id]` | `o` | Show profile details and open latest report |
| `osintkit export [id]` | `exp` | Export as JSON or Markdown |
| `osintkit setup` | `s` | Configure API keys interactively |
| `osintkit config set-key <key> <value>` | `cfg set-key` | Update a single API key |
| `osintkit config show` | `cfg show` | Show which keys are set (values hidden) |
| `osintkit tag [id]` | — | Add, remove, or list tags on a profile |
| `osintkit delete [id]` | `rm` | Delete a profile |
| `osintkit update` | `up` | Check for and install a newer version |
| `osintkit bug` | — | Report a bug (opens GitHub issue pre-filled) |
| `osintkit version` | `v` | Show version |

## What It Checks

### Stage 1 — No API keys needed

| Module | Input | What it does |
|--------|-------|-------------|
| Maigret | username | 3000+ site username search |
| Sherlock | username | 400+ site username search |
| Holehe | email | 120+ platform email registration check |
| HIBP k-anonymity | email | Password breach check (no key needed) |
| Gravatar | email | Profile existence + avatar |
| theHarvester | email/domain | Web presence, subdomains |
| crt.sh | email/domain | Certificate transparency logs |
| Wayback CDX | email | Historical web appearances |
| Shodan InternetDB | email/domain | Open ports + CVEs (no key) |
| ThreatFox | email domain | Malware C2 / IOC check (no key) |
| libphonenumber | phone | Carrier, region, line type (offline) |
| Paste search | email | Paste site appearances |
| Data brokers | name/email | Public broker listing scan |
| Dark web | email | Ahmia / public dark web index |
| Breach lookup | email | BreachDirectory |
| emailrep.io | email | Email reputation, spam, disposable check |
| WHOIS | email domain | Domain registration info |
| urlscan.io | email domain | Domain scan history & malicious verdicts |
| GitHub | username | Public profile (no key needed) |

### Stage 2 — Optional free API keys

| Service | Key name | Input | Free tier | Get key |
|---------|----------|-------|-----------|---------|
| VirusTotal | `virustotal` | email domain | 500/day | virustotal.com |
| OTX AlienVault | `otx` | email domain | Unlimited | otx.alienvault.com |
| AbuseIPDB | `abuseipdb` | email domain | 1,000/day | abuseipdb.com |
| GreyNoise | `greynoise` | email domain | 50/week | greynoise.io |
| IntelligenceX | `intelligencex` | email/username | 50/day | intelx.io |
| Netlas | `netlas` | email domain | 50/day | netlas.io |
| Pulsedive | `pulsedive` | email domain | 10/day | pulsedive.com |
| SecurityTrails | `securitytrails` | domain | see site | securitytrails.com |
| Hunter.io | `hunter` | email | 25/month | hunter.io |
| NumVerify | `numverify` | phone | 100/month | numverify.com |

Stage 2 modules only run when a key is configured. Rate-limited modules show yellow, not red — the scan always completes.

## Output

Each scan creates a folder at `~/osint-results/<target>_<date>/` containing:
- `report.html` — rendered report with risk score and findings
- `findings.json` — full structured data
- `findings.md` — markdown summary

Risk score 0–100 accounts for: breach exposure, social footprint, data broker listings, dark web/paste appearances, domain reputation (VirusTotal), IP abuse score (AbuseIPDB), email reputation flags, and threat intelligence pulse count (OTX).

## API Keys (All Optional)

Keys are stored in `~/.osintkit/config.yaml` (permissions: 600, never readable by other users).

```bash
osintkit config set-key virustotal YOUR_KEY
osintkit config set-key otx        YOUR_KEY
osintkit config set-key abuseipdb  YOUR_KEY
osintkit config show                           # see which keys are set
osintkit setup                                 # interactive wizard
```

Full API key guide: [docs.codecho.de/osintkit/api-keys.html](https://docs.codecho.de/osintkit/api-keys.html)

## Optional Tools

These tools run automatically if installed; modules gracefully show "not installed" if missing.

```bash
pip install maigret holehe sherlock-project theHarvester python-whois
```

## Run from Source

```bash
git clone https://github.com/diesesschnitzel/osintkit.git
cd osintkit
pip install -r requirements.txt -r requirements-tools.txt
PYTHONPATH=. python3 -m osintkit.cli new
```

## Ethics

Only use osintkit on targets you have explicit permission to investigate. GDPR applies to EU subjects. A disclaimer is shown before every scan.

## Support & Bug Reports

- **Docs:** [docs.codecho.de/osintkit](https://docs.codecho.de/osintkit/)
- **GitHub Issues:** [github.com/diesesschnitzel/osintkit/issues](https://github.com/diesesschnitzel/osintkit/issues)
- **Email:** help@oss.codecho.de
- **CLI shortcut:** `osintkit bug` — opens a pre-filled GitHub issue in your browser

## License

MIT
