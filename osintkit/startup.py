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

# Maps version string → list of (key_name, service_name, get_key_url)
# Add an entry here whenever a new Stage 2 integration ships.
KEYS_ADDED_IN: dict[str, list[tuple[str, str, str]]] = {
    "0.1.6": [
        ("virustotal", "VirusTotal — domain malware & reputation", "https://virustotal.com/gui/join-us"),
        ("otx",        "OTX AlienVault — threat intelligence",    "https://otx.alienvault.com"),
        ("abuseipdb",  "AbuseIPDB — IP abuse reports",           "https://abuseipdb.com/register"),
        ("epieos",     "Epieos — Google/Apple account lookup",   "https://epieos.com"),
    ],
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

    # Collect keys that were added since the user's last version and are not yet configured
    new_keys: list[tuple[str, str, str]] = []
    try:
        from packaging.version import Version
        prev = Version(last) if last != "unknown" else Version("0.0.0")
        curr = Version(__version__)
        for ver_str, keys in KEYS_ADDED_IN.items():
            try:
                if prev < Version(ver_str) <= curr:
                    for key_name, service, url in keys:
                        if not api_keys_set.get(key_name):
                            new_keys.append((key_name, service, url))
            except Exception:
                pass
    except Exception:
        pass

    lines: list[str] = [
        f"[bold green]Updated to osintkit v{__version__}[/bold green] "
        f"[dim](was v{last})[/dim]",
    ]

    if new_keys:
        lines.append("\n[bold]New optional integrations — get free API keys:[/bold]")
        for key_name, service, url in new_keys:
            lines.append(f"\n  [cyan]•[/cyan] [bold]{key_name}[/bold] — {service}")
            lines.append(f"    [dim]{url}[/dim]")
            lines.append(f"    [dim]osintkit config set-key {key_name} <your-key>[/dim]")

    lines.append(f"\n[dim]Docs & full API key guide: {DOCS_URL}[/dim]")

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
