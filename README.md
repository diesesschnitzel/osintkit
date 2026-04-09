# osintkit

OSINT CLI tool for personal digital footprint analysis.

## Installation

```bash
# From source
cd osintkit-oss
npm install -g .

# Or use directly without installation
PYTHONPATH=. python3 -m osintkit.cli <command>
```

## Quick Start

```bash
# First-time setup (configure API keys)
osintkit setup

# Create a new profile
osintkit new

# List all profiles
osintkit list

# Run a scan
osintkit refresh <profile_id>

# View profile details
osintkit open <profile_id>

# Export data
osintkit export <profile_id>
```

## Commands

| Command | Description |
|---------|-------------|
| `osintkit new` | Create new profile |
| `osintkit list` | List all profiles |
| `osintkit refresh <id>` | Run scan for profile |
| `osintkit open <id>` | Show profile details |
| `osintkit export <id>` | Export as JSON/Markdown |
| `osintkit setup` | Configure API keys |
| `osintkit delete <id>` | Delete profile |
| `osintkit version` | Show version |

## Features

- **Profile Management** - Store and manage multiple target profiles
- **Duplicate Detection** - Warns when creating profiles with existing info
- **OSINT Modules** - 10 integrated OSINT data sources
- **Risk Scoring** - 0-100 risk score based on findings
- **Export** - JSON and Markdown report formats

## API Keys (Optional)

Free API keys available for enhanced functionality:

| Service | Free Limit | Purpose |
|---------|------------|---------|
| Have I Been Pwned | 10/min | Breach database |
| NumVerify | 100/month | Phone validation |
| Intelbase | 100/month | Dark web + paste |
| BreachDirectory | 50/day | Breach lookups |
| Google CSE | 100/day | Data broker detection |

## Requirements

- Python 3.11+
- Node.js 12+
- pip

## External Tools (Optional)

For full functionality, install:
```bash
pip install maigret holehe theHarvester
```

## License

MIT