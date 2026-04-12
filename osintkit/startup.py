"""Startup checks for osintkit — first-run welcome and version-change notifications.

Called once per CLI invocation from the app callback. Never blocks more than
a console.print; the interactive setup wizard lives in setup.py.
"""

from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from osintkit import __version__
from osintkit.config import Config, load_config, save_config

DOCS_URL = "https://docs.codecho.de/osintkit/"
CONFIG_PATH = Path.home() / ".osintkit" / "config.yaml"

# Full changelog — every version with human-readable changes + new API keys.
# Shown cumulatively when the user updates: if they skipped v0.1.8 and go straight
# to v0.2.0 they see everything that changed in 0.1.8 AND 0.2.0.
CHANGELOG: dict[str, dict] = {
    "0.1.6": {
        "changes": [
            "New: VirusTotal domain malware scanner",
            "New: OTX AlienVault threat intelligence",
            "New: AbuseIPDB IP abuse reports",
        ],
        "new_keys": [
            ("virustotal", "VirusTotal — domain malware & reputation", "https://virustotal.com/gui/join-us"),
            ("otx",        "OTX AlienVault — threat intelligence",    "https://otx.alienvault.com"),
            ("abuseipdb",  "AbuseIPDB — IP abuse reports",            "https://abuseipdb.com/register"),
        ],
    },
    "0.1.7": {
        "changes": [
            "Fix: various stability improvements",
        ],
        "new_keys": [],
    },
    "0.1.8": {
        "changes": [
            "New: GreyNoise IP noise classification",
            "New: IntelligenceX darknet + leak search",
            "New: Netlas internet scan data",
            "New: Pulsedive IOC risk scoring",
            "New: IPInfo geolocation / ASN (free token)",
            "New: Shodan InternetDB, ThreatFox, Sherlock, Gravatar, Wayback modules",
        ],
        "new_keys": [
            ("greynoise",     "GreyNoise — IP noise classification",      "https://www.greynoise.io/plans/free-intelligence"),
            ("intelligencex", "IntelligenceX — darknet + leak search",    "https://intelx.io/"),
            ("netlas",        "Netlas — internet scan data",              "https://app.netlas.io/plans/"),
            ("pulsedive",     "Pulsedive — IOC risk scoring",             "https://pulsedive.com/"),
            ("ipinfo",        "IPInfo — IP geolocation / ASN (optional)", "https://ipinfo.io/signup"),
        ],
    },
    "0.1.9": {
        "changes": [
            "Fix: setup wizard now uses the correct interactive flow",
            "Fix: startup update notice removed obsolete paid-API references",
        ],
        "new_keys": [],
    },
    "0.2.0": {
        "changes": [
            "New: osintkit scan <target> — run a scan without creating a profile first",
            "New: short command aliases (ls, n, r, o, exp, rm, sc, s, v, up, cfg)",
            "Fix: API key input now shows * per keystroke in setup wizard",
            "Fix: ThreatFox API endpoint corrected (threatfox-api.abuse.ch)",
            "Fix: BreachDirectory migrated from dead RapidAPI listing to breachdirectory.com",
            "Fix: Wayback Machine URL upgraded to HTTPS",
            "Fix: CLI now shows 'osintkit' in usage line (not 'python -m osintkit')",
        ],
        "new_keys": [],
    },
}

_console = Console()


def check_startup() -> None:
    """Run on every CLI invocation — silently if nothing to report."""
    if not CONFIG_PATH.exists():
        _show_first_run_welcome()
        return

    try:
        cfg = load_config(CONFIG_PATH)
    except Exception:
        return

    if cfg.last_seen_version != __version__:
        _show_update_notice(cfg)


# ── private helpers ──────────────────────────────────────────────────────────

def _show_first_run_welcome() -> None:
    _console.print(Panel(
        f"[bold green]Successfully installed osintkit v{__version__}[/bold green]\n\n"
        f"Full documentation, API key guides, and CLI reference:\n"
        f"[bold cyan]{DOCS_URL}[/bold cyan]\n\n"
        "Configure optional API keys to unlock all modules:\n"
        "  [bold]osintkit setup[/bold]\n\n"
        "Create your first profile and run a scan:\n"
        "  [bold]osintkit new[/bold]",
        title="[bold]🎉  Welcome to osintkit[/bold]",
        border_style="green",
        padding=(1, 2),
    ))


def _show_update_notice(cfg: Config) -> None:
    last = cfg.last_seen_version or "unknown"
    api_keys_set = cfg.api_keys.model_dump()

    # Collect all changes and new keys for every version between prev and curr
    version_sections: list[tuple[str, list[str], list[tuple[str, str, str]]]] = []
    new_keys_unconfigured: list[tuple[str, str, str]] = []

    try:
        from packaging.version import Version
        prev = Version(last) if last != "unknown" else Version("0.0.0")
        curr = Version(__version__)
        for ver_str, entry in CHANGELOG.items():
            try:
                if prev < Version(ver_str) <= curr:
                    changes = entry.get("changes", [])
                    keys = [
                        (k, s, u) for k, s, u in entry.get("new_keys", [])
                        if not api_keys_set.get(k)
                    ]
                    version_sections.append((ver_str, changes, keys))
                    new_keys_unconfigured.extend(keys)
            except Exception:
                pass
    except Exception:
        pass

    lines: list[str] = [
        f"[bold green]Updated to osintkit v{__version__}[/bold green] "
        f"[dim](was v{last})[/dim]",
    ]

    for ver_str, changes, keys in version_sections:
        lines.append(f"\n[bold yellow]v{ver_str}[/bold yellow]")
        for change in changes:
            lines.append(f"  [cyan]•[/cyan] {change}")
        for key_name, service, url in keys:
            lines.append(f"\n  [green]+[/green] [bold]{key_name}[/bold] — {service}")
            lines.append(f"    [dim]{url}[/dim]")
            lines.append(f"    [dim]osintkit config set-key {key_name} <your-key>[/dim]")

    lines.append(f"\n[dim]Full changelog & API key guide: {DOCS_URL}[/dim]")

    _console.print(Panel(
        "\n".join(lines),
        title="[bold yellow]✨  What's new[/bold yellow]",
        border_style="yellow",
        padding=(1, 2),
    ))

    # Mark this version as seen so we don't show the notice again
    try:
        updated = cfg.model_copy(update={"last_seen_version": __version__})
        save_config(updated, CONFIG_PATH)
    except Exception:
        pass
