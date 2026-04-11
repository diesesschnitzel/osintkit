"""First-time setup wizard for osintkit."""

from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
import yaml

console = Console()

# Free API keys with their limits
FREE_API_KEYS = {
    "hibp": {
        "name": "Have I Been Pwned",
        "description": "Breach database lookups",
        "limits": "10 requests/minute (free tier)",
        "url": "https://haveibeenpwned.com/API/Key",
        "required": False,
    },
    "numverify": {
        "name": "NumVerify",
        "description": "Phone number validation",
        "limits": "100 requests/month (free tier)",
        "url": "https://numverify.com/",
        "required": False,
    },
    "intelbase": {
        "name": "Intelbase",
        "description": "Dark web & paste search",
        "limits": "100 requests/month (free tier)",
        "url": "https://intelbase.is",
        "required": False,
    },
    "breachdirectory": {
        "name": "BreachDirectory (RapidAPI)",
        "description": "Breach lookups",
        "limits": "50 requests/day (RapidAPI free tier)",
        "url": "https://rapidapi.com/rohan-patel/api/breachdirectory",
        "required": False,
    },
    "google_cse": {
        "name": "Google Custom Search",
        "description": "Data broker detection",
        "limits": "100 requests/day (free tier)",
        "url": "https://developers.google.com/custom-search/v1/introduction",
        "required": False,
        "needs_two_keys": True,  # key + cx
    },
    "emailrep": {
        "name": "EmailRep.io",
        "description": "Email reputation, spam, malicious activity flags",
        "limits": "100 requests/day without key, 1,000/day free tier",
        "url": "https://emailrep.io/key",
        "required": False,
    },
    "virustotal": {
        "name": "VirusTotal",
        "description": "Domain/IP malware and reputation scanning",
        "limits": "500 lookups/day, 4 req/min (free tier)",
        "url": "https://www.virustotal.com/gui/join-us",
        "required": False,
    },
    "otx": {
        "name": "OTX AlienVault",
        "description": "Open threat intelligence — domain/IP indicators",
        "limits": "Unlimited on free account",
        "url": "https://otx.alienvault.com/",
        "required": False,
    },
    "abuseipdb": {
        "name": "AbuseIPDB",
        "description": "IP abuse reports for email domain hosts",
        "limits": "1,000 checks/day (free tier)",
        "url": "https://www.abuseipdb.com/register",
        "required": False,
    },
    "epieos": {
        "name": "Epieos",
        "description": "Reverse Google/Apple account lookup from email",
        "limits": "Free tier available",
        "url": "https://epieos.com",
        "required": False,
    },
}


def is_first_run() -> bool:
    """Check if this is the first run."""
    config_path = Path.home() / ".osintkit" / "config.yaml"
    return not config_path.exists()


DOCS_URL = "https://docs.codecho.de/oss/osintkit"


def run_setup_wizard():
    """Run the first-time setup wizard."""
    console.print(Panel.fit(
        "[bold cyan]Welcome to osintkit![/bold cyan]\n\n"
        "OSINT tool for personal digital footprint analysis.\n"
        "All API keys are optional — free tiers available for every service.\n\n"
        f"[dim]Full docs & key guide: {DOCS_URL}[/dim]",
        title="🚀 First-Time Setup",
    ))
    
    console.print("\n[yellow]API keys unlock more search capabilities.[/yellow]")
    console.print("[dim]You can skip any key and add them later with 'osintkit setup'[/dim]\n")
    
    # Show available APIs
    table = Table(title="Available Free APIs")
    table.add_column("Service", style="cyan")
    table.add_column("What it does")
    table.add_column("Free Limits")
    
    for key_id, info in FREE_API_KEYS.items():
        table.add_row(info["name"], info["description"], info["limits"])
    
    console.print(table)
    console.print()
    
    # Collect API keys
    api_keys = {}
    
    if Confirm.ask("\nConfigure API keys now?", default=True):
        for key_id, info in FREE_API_KEYS.items():
            console.print(f"\n[bold]{info['name']}[/bold] - {info['description']}")
            console.print(f"[dim]Limits: {info['limits']}[/dim]")
            console.print(f"[dim]Get key: {info['url']}[/dim]")
            
            if info.get("needs_two_keys"):
                key = Prompt.ask(f"  API Key", default="")
                cx = Prompt.ask(f"  Custom Search Engine ID (cx)", default="")
                api_keys[f"{key_id}_key"] = key.strip()
                api_keys[f"{key_id}_cx"] = cx.strip()
            else:
                key = Prompt.ask(f"  API Key (or press Enter to skip)", default="")
                api_keys[key_id] = key.strip()
    else:
        # Initialize with empty keys
        api_keys = {
            "hibp": "",
            "numverify": "",
            "intelbase": "",
            "breachdirectory": "",
            "google_cse_key": "",
            "google_cse_cx": "",
        }
    
    # Save config — merge with existing keys so we never wipe anything
    config_dir = Path.home() / ".osintkit"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.yaml"

    if config_path.exists():
        with open(config_path) as f:
            existing = yaml.safe_load(f) or {}
        existing_keys = existing.get("api_keys", {})
    else:
        existing = {"output_dir": "~/osint-results", "timeout_seconds": 120}
        existing_keys = {}

    # Only overwrite keys the user actually provided (non-empty)
    for k, v in api_keys.items():
        if v:
            existing_keys[k] = v
        elif k not in existing_keys:
            existing_keys[k] = ""

    existing["api_keys"] = existing_keys
    with open(config_path, "w") as f:
        yaml.dump(existing, f, default_flow_style=False)
    config_path.chmod(0o600)  # owner read/write only — API keys must not be world-readable

    # Create profiles file
    profiles_path = config_dir / "profiles.json"
    if not profiles_path.exists():
        profiles_path.write_text("{}")
    profiles_path.chmod(0o600)
    
    console.print(f"\n[green]✓[/green] Config saved to: {config_path}")
    console.print("[green]✓[/green] Ready to use!")
    console.print("\n[bold]Next steps:[/bold]")
    console.print("  [cyan]osintkit new[/cyan]     - Create a new profile")
    console.print("  [cyan]osintkit list[/cyan]    - List all profiles")
    console.print("  [cyan]osintkit setup[/cyan]   - Reconfigure API keys")


def update_api_key(key_name: str, key_value: str):
    """Update a single API key in config."""
    config_path = Path.home() / ".osintkit" / "config.yaml"
    
    if not config_path.exists():
        run_setup_wizard()
        return
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    if "api_keys" not in config:
        config["api_keys"] = {}
    
    config["api_keys"][key_name] = key_value
    
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
    config_path.chmod(0o600)

    console.print(f"[green]✓[/green] Updated {key_name}")
