"""Interactive setup wizard for osintkit API keys."""

import sys
import termios
import tty
from pathlib import Path
from rich.console import Console
from rich.prompt import Confirm
from rich.panel import Panel
from rich.table import Table
import yaml

console = Console()

DOCS_URL = "https://docs.codecho.de/osintkit/api-keys.html"

# ── Key definitions ──────────────────────────────────────────────────────────
# Each entry: (config_key, display_name, description, free_limit, signup_url)
# Stage 1 = always runs, key is optional token for higher rate limits
# Stage 2 = module only activates when key is present

STAGE1_OPTIONAL = [
    (
        "emailrep",
        "EmailRep.io",
        "Email reputation, spam & malicious activity flags",
        "Works without key; key = 250 queries/month (free tier)",
        "https://emailrep.io/key",
    ),
    (
        "ipinfo",
        "IPInfo.io",
        "IP geolocation and ASN lookup",
        "Works without key; free token = 50,000/month",
        "https://ipinfo.io/signup",
    ),
    (
        "github",
        "GitHub Personal Access Token",
        "GitHub profile lookups — raises API rate limit",
        "Free — no scopes needed, just public access",
        "https://github.com/settings/tokens",
    ),
    (
        "intelbase",
        "Intelbase",
        "Dark web & paste site search",
        "100 requests/month (free tier)",
        "https://intelbase.is",
    ),
    (
        "breachdirectory",
        "BreachDirectory (RapidAPI)",
        "Breach record lookup",
        "50 requests/day (RapidAPI free tier)",
        "https://rapidapi.com/rohan-patel/api/breachdirectory",
    ),
]

STAGE2_KEYS = [
    (
        "virustotal",
        "VirusTotal",
        "Domain malware & AV reputation scan",
        "500 lookups/day, 4 req/min — free account",
        "https://www.virustotal.com/gui/join-us",
    ),
    (
        "otx",
        "OTX AlienVault",
        "Threat intelligence — domain/IP indicators & pulses",
        "Unlimited — free account",
        "https://otx.alienvault.com/",
    ),
    (
        "abuseipdb",
        "AbuseIPDB",
        "IP abuse reports and confidence score",
        "1,000 checks/day — free account",
        "https://www.abuseipdb.com/register",
    ),
    (
        "greynoise",
        "GreyNoise Community",
        "IP scanner/noise classification (malicious vs benign)",
        "50 lookups/week — free community account",
        "https://www.greynoise.io/plans/free-intelligence",
    ),
    (
        "intelligencex",
        "IntelligenceX",
        "Darknet + leak database search for email/username",
        "50 searches/day — free account",
        "https://intelx.io/",
    ),
    (
        "netlas",
        "Netlas.io",
        "Internet scan data — open ports, CVEs, banners",
        "50 requests/day — free community account",
        "https://app.netlas.io/plans/",
    ),
    (
        "pulsedive",
        "Pulsedive",
        "IOC risk scoring via threat feeds",
        "10 requests/day — free registered account",
        "https://pulsedive.com/",
    ),
    (
        "securitytrails",
        "SecurityTrails",
        "Historical DNS records and subdomains",
        "Free tier — see securitytrails.com for current limits",
        "https://securitytrails.com/",
    ),
    (
        "hunter",
        "Hunter.io",
        "Email deliverability and SMTP verification",
        "25 searches/month — free account",
        "https://hunter.io/",
    ),
    (
        "numverify",
        "NumVerify",
        "Phone number carrier and line type lookup",
        "100 requests/month — free account",
        "https://numverify.com/",
    ),
]

# Google CSE is special — needs two keys that go together
GOOGLE_CSE = {
    "api_key_field": "google_cse_key",
    "cx_field": "google_cse_cx",
    "name": "Google Custom Search",
    "description": "Data broker detection (people-search site listings)",
    "limits": "100 requests/day — free account",
    "url": "https://developers.google.com/custom-search/v1/introduction",
}


def _prompt_with_stars(label: str) -> str:
    """Prompt that echoes * for each character so the user can see how many chars they've entered."""
    sys.stdout.write(label)
    sys.stdout.flush()
    chars: list = []
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        while True:
            ch = sys.stdin.read(1)
            if ch in ('\r', '\n'):
                break
            elif ch in ('\x7f', '\x08'):   # backspace / delete
                if chars:
                    chars.pop()
                    sys.stdout.write('\b \b')
                    sys.stdout.flush()
            elif ch == '\x03':             # Ctrl-C
                raise KeyboardInterrupt
            elif ch == '\x1b':             # ignore escape sequences (arrow keys etc.)
                sys.stdin.read(2)
            else:
                chars.append(ch)
                sys.stdout.write('*')
                sys.stdout.flush()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    sys.stdout.write('\n')
    return ''.join(chars).strip()


def _mask(value: str) -> str:
    """Return masked display string for an existing key."""
    if not value:
        return "[dim]not set[/dim]"
    visible = value[:4] if len(value) >= 4 else value[:1]
    return f"[green]{visible}{'*' * min(8, len(value) - len(visible))}[/green] [dim](already configured)[/dim]"


def _load_existing_keys(config_path: Path) -> dict:
    if not config_path.exists():
        return {}
    with open(config_path) as f:
        data = yaml.safe_load(f) or {}
    return data.get("api_keys", {})


def _ask_key(label: str, description: str, limits: str, url: str, existing: str) -> str:
    """Prompt for a single API key. Shows masked existing value. Returns new or existing."""
    console.print(f"\n  [bold]{label}[/bold] — {description}")
    console.print(f"  [dim]{limits}[/dim]")
    console.print(f"  [dim]Get key: {url}[/dim]")
    if existing:
        console.print(f"  Current: {_mask(existing)}")
        keep = Confirm.ask("  Keep existing key?", default=True)
        if keep:
            return existing
    value = _prompt_with_stars("  Paste API key (or press Enter to skip): ")
    return value


def run_setup_wizard():
    """Run the interactive API key setup wizard."""
    console.print(Panel.fit(
        "[bold cyan]osintkit — API key setup[/bold cyan]\n\n"
        "All keys are optional. Every service listed here has a free tier.\n"
        "Keys are saved to [dim]~/.osintkit/config.yaml[/dim] (read-only, never committed to git).\n\n"
        f"[dim]Full guide: {DOCS_URL}[/dim]",
        title="⚙  Setup",
    ))

    config_path = Path.home() / ".osintkit" / "config.yaml"
    existing_keys = _load_existing_keys(config_path)

    # ── Summary table ────────────────────────────────────────────
    table = Table(show_header=True, header_style="bold")
    table.add_column("Service", style="cyan", min_width=20)
    table.add_column("Free limit", min_width=28)
    table.add_column("Status", min_width=14)

    console.print("\n[bold]Stage 1[/bold] — run always; key is optional (raises rate limit)\n")
    for key_id, name, _, limits, _ in STAGE1_OPTIONAL:
        status = "[green]configured[/green]" if existing_keys.get(key_id) else "[dim]not set[/dim]"
        table.add_row(name, limits, status)

    console.print("\n[bold]Stage 2[/bold] — module activates only when key is present\n")
    for key_id, name, _, limits, _ in STAGE2_KEYS:
        status = "[green]configured[/green]" if existing_keys.get(key_id) else "[dim]not set[/dim]"
        table.add_row(name, limits, status)

    # Google CSE
    gkey = existing_keys.get(GOOGLE_CSE["api_key_field"])
    gcx = existing_keys.get(GOOGLE_CSE["cx_field"])
    gstatus = "[green]configured[/green]" if (gkey and gcx) else "[dim]not set[/dim]"
    table.add_row(GOOGLE_CSE["name"], GOOGLE_CSE["limits"], gstatus)

    console.print(table)
    console.print()

    if not Confirm.ask("Configure API keys now?", default=True):
        console.print("[dim]Skipped. Run 'osintkit setup' any time to configure.[/dim]")
        return

    new_keys: dict = {}

    # ── Stage 1 keys ─────────────────────────────────────────────
    console.print("\n[bold yellow]── Stage 1 optional tokens ──[/bold yellow]")
    for key_id, name, desc, limits, url in STAGE1_OPTIONAL:
        val = _ask_key(name, desc, limits, url, existing_keys.get(key_id, ""))
        new_keys[key_id] = val

    # ── Google CSE (paired keys) ──────────────────────────────────
    console.print(f"\n  [bold]{GOOGLE_CSE['name']}[/bold] — {GOOGLE_CSE['description']}")
    console.print(f"  [dim]{GOOGLE_CSE['limits']}[/dim]")
    console.print(f"  [dim]Get key: {GOOGLE_CSE['url']}[/dim]")
    if gkey:
        console.print(f"  API Key: {_mask(gkey)}")
        console.print(f"  Engine ID: {_mask(gcx or '')}")
        if Confirm.ask("  Keep existing Google CSE keys?", default=True):
            new_keys[GOOGLE_CSE["api_key_field"]] = gkey
            new_keys[GOOGLE_CSE["cx_field"]] = gcx or ""
        else:
            api_key_val = _prompt_with_stars("  Paste API Key (or Enter to skip): ")
            if api_key_val.strip():
                cx_val = Prompt.ask("  Paste Search Engine ID (cx)", default="")
                new_keys[GOOGLE_CSE["api_key_field"]] = api_key_val.strip()
                new_keys[GOOGLE_CSE["cx_field"]] = cx_val.strip()
    else:
        api_key_val = _prompt_with_stars("  Paste API Key (or Enter to skip): ")
        if api_key_val.strip():
            cx_val = Prompt.ask("  Paste Search Engine ID (cx)", default="")
            new_keys[GOOGLE_CSE["api_key_field"]] = api_key_val.strip()
            new_keys[GOOGLE_CSE["cx_field"]] = cx_val.strip()
        # If no API key entered, leave CSE cx alone — don't ask for it

    # ── Stage 2 keys ─────────────────────────────────────────────
    console.print("\n[bold yellow]── Stage 2 keys (module activates when set) ──[/bold yellow]")
    for key_id, name, desc, limits, url in STAGE2_KEYS:
        val = _ask_key(name, desc, limits, url, existing_keys.get(key_id, ""))
        new_keys[key_id] = val

    # ── Save — merge with existing, only overwrite what user provided ──
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if config_path.exists():
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}
    else:
        config = {"output_dir": "~/osint-results", "timeout_seconds": 120}

    merged = dict(existing_keys)
    for k, v in new_keys.items():
        if v:
            merged[k] = v
        elif k not in merged:
            merged[k] = ""

    config["api_keys"] = merged
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
    config_path.chmod(0o600)

    # Profiles file
    profiles_path = config_path.parent / "profiles.json"
    if not profiles_path.exists():
        profiles_path.write_text("{}")
        profiles_path.chmod(0o600)

    # ── Summary ───────────────────────────────────────────────────
    configured = [k for k, v in merged.items() if v and k not in ("output_dir", "timeout_seconds")]
    console.print(f"\n[green]✓[/green] Config saved → {config_path}")
    console.print(f"[green]✓[/green] {len(configured)} key(s) configured\n")
    console.print("[bold]Next steps:[/bold]")
    console.print("  [cyan]osintkit scan <email>[/cyan]   — run a full scan")
    console.print("  [cyan]osintkit setup[/cyan]           — update keys any time")
    console.print(f"  [cyan]{DOCS_URL}[/cyan]")


def update_api_key(key_name: str, key_value: str):
    """Update a single API key in config."""
    config_path = Path.home() / ".osintkit" / "config.yaml"
    if not config_path.exists():
        run_setup_wizard()
        return
    with open(config_path) as f:
        config = yaml.safe_load(f) or {}
    config.setdefault("api_keys", {})[key_name] = key_value
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
    config_path.chmod(0o600)
    console.print(f"[green]✓[/green] Updated {key_name}")
