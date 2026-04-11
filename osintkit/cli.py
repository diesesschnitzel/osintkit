"""osintkit CLI - OSINT tool for personal digital footprint analysis."""

import sys
import json
import logging
import threading
from pathlib import Path
from typing import Optional
from datetime import datetime

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

from osintkit import __version__
from osintkit.scanner import Scanner
from osintkit.config import load_config, save_config, Config, APIKeys
from osintkit.profiles import Profile, ProfileStore, ScanHistory
from osintkit.setup import update_api_key

app = typer.Typer(help="OSINT CLI for personal digital footprint analysis", invoke_without_command=True)
console = Console()
store = ProfileStore()
logger = logging.getLogger(__name__)
_update_thread = None


@app.callback()
def _startup(ctx: typer.Context):
    """Run startup checks and start background version check on every invocation."""
    global _update_thread
    _update_thread = _start_update_check()
    from osintkit.startup import check_startup
    check_startup()

# ---- Version update check ----

_update_available: Optional[str] = None  # Set to newer version string if one exists


def _check_for_update_bg():
    """Check npm registry for a newer version in a background thread (non-blocking)."""
    global _update_available
    try:
        import httpx
        resp = httpx.get(
            "https://registry.npmjs.org/osintkit/latest",
            timeout=3.0,
            headers={"Accept": "application/json"},
        )
        if resp.status_code == 200:
            latest = resp.json().get("version", "")
            if latest and latest != __version__:
                from packaging.version import Version
                if Version(latest) > Version(__version__):
                    _update_available = latest
    except Exception:
        pass  # Never crash the app over a version check


def _start_update_check():
    """Start the background version check thread."""
    t = threading.Thread(target=_check_for_update_bg, daemon=True)
    t.start()
    return t


def _print_update_notice():
    """Print update notice if a newer version was found."""
    if _update_available:
        console.print(Panel(
            f"[bold cyan]osintkit {_update_available}[/bold cyan] is available "
            f"[dim](you have {__version__})[/dim]\n"
            "[dim]Run:[/dim] [bold]npm install -g osintkit[/bold]",
            title="[bold yellow]⬆  Update available[/bold yellow]",
            border_style="yellow",
            padding=(0, 2),
        ))


def _print_ethics_banner():
    """Print the ethics and legal notice before every scan."""
    console.print(Panel(
        "[yellow]Only use osintkit on targets you have explicit permission to investigate.\n"
        "GDPR applies to EU subjects. Unauthorized use may be illegal.[/yellow]",
        title="[bold red]Ethics Notice[/bold red]",
        border_style="red",
    ))


def validate_and_format_phone(phone_str: str) -> Optional[str]:
    """Parse and validate a phone number string, returning E.164 format.

    Args:
        phone_str: Raw phone number string entered by the user.

    Returns:
        E.164 formatted string (e.g. '+15555550100') if valid, None otherwise.
    """
    if not phone_str:
        return None
    try:
        import phonenumbers
        parsed = phonenumbers.parse(phone_str, None)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        # Try with US as default region
        parsed = phonenumbers.parse(phone_str, "US")
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        logger.warning(f"Phone number appears invalid: {phone_str!r}")
        return None
    except Exception:
        try:
            import phonenumbers
            parsed = phonenumbers.parse(phone_str, "US")
            if phonenumbers.is_valid_number(parsed):
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except Exception:
            pass
        logger.warning(f"Could not parse phone number: {phone_str!r}")
        return None

# ============ SETUP ============

def check_first_time():
    """Check if this is first run and prompt for API keys."""
    config_path = Path.home() / ".osintkit" / "config.yaml"
    
    if not config_path.exists():
        console.print("\n[bold cyan]═══ First Time Setup ═══[/bold cyan]\n")
        console.print("osintkit needs API keys for full functionality.")
        console.print("[dim]You can skip this and add keys later.[/dim]\n")
        console.print(
            "[dim]Tip: for social profile enumeration install optional tools:\n"
            "  pip install -r requirements-tools.txt  (maigret, holehe, sherlock)[/dim]\n"
        )
        
        keys = {}
        api_key_list = [
            ("hibp", "HaveIBeenPwned", "Free tier available"),
            ("breachdirectory", "BreachDirectory", "Via RapidAPI"),
            ("leakcheck", "LeakCheck", "Free tier available"),
            ("intelbase", "Intelbase", "Dark web + paste search"),
            ("google_cse_key", "Google CSE Key", "Data broker search"),
            ("google_cse_cx", "Google CSE CX ID", "Engine ID"),
            ("numverify", "NumVerify", "Phone validation"),
            ("emailrep", "EmailRep", "Email reputation"),
            ("hunter", "Hunter.io (email finder)", "https://hunter.io"),
            ("github", "GitHub Personal Access Token", "https://github.com/settings/tokens"),
            ("securitytrails", "SecurityTrails", "https://securitytrails.com"),
        ]
        
        for key_name, service_name, note in api_key_list:
            value = Prompt.ask(f"{service_name} ({note})", default="")
            keys[key_name] = value.strip()
        
        # Create config
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_content = f"""# osintkit Configuration
output_dir: ~/osint-results
timeout_seconds: 120

api_keys:
  hibp: "{keys.get('hibp', '')}"
  breachdirectory: "{keys.get('breachdirectory', '')}"
  leakcheck: "{keys.get('leakcheck', '')}"
  intelbase: "{keys.get('intelbase', '')}"
  google_cse_key: "{keys.get('google_cse_key', '')}"
  google_cse_cx: "{keys.get('google_cse_cx', '')}"
  numverify: "{keys.get('numverify', '')}"
  emailrep: "{keys.get('emailrep', '')}"
  resend: ""
  hunter: "{keys.get('hunter', '')}"
  github: "{keys.get('github', '')}"
  securitytrails: "{keys.get('securitytrails', '')}"
  epieos: ""
"""
        config_path.write_text(config_content)
        config_path.chmod(0o600)  # API keys must not be world-readable
        console.print(f"\n[green]✓[/green] Config saved to {config_path}")
        return True
    
    return False


def get_profile_by_identifier(name=None, email=None, username=None, phone=None) -> Optional[Profile]:
    """Find profile by any identifier."""
    profiles = store.list()
    for p in profiles:
        if name and p.name and name.lower().strip() == p.name.lower().strip():
            return p
        if email and p.email and email.lower().strip() == p.email.lower().strip():
            return p
        if username and p.username and username.lower().strip() == p.username.lower().strip():
            return p
        if phone and p.phone and phone.strip() == p.phone.strip():
            return p
    return None


def select_profile() -> Optional[Profile]:
    """Let user select a profile from list."""
    profiles = store.list()
    
    if not profiles:
        console.print("[yellow]No profiles found. Use 'osintkit new' to create one.[/yellow]")
        return None
    
    console.print("\n[bold]Select a profile:[/bold]\n")
    
    for i, p in enumerate(profiles, 1):
        scan_info = f"{len(p.scan_history)} scans" if p.scan_history else "no scans"
        console.print(f"  [cyan]{i}.[/cyan] {p.name or 'Unnamed'} - {p.email or p.username or 'no email'} ({scan_info})")
    
    console.print()
    choice = Prompt.ask("Enter number (or Enter to cancel)", default="")
    
    if not choice:
        return None
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(profiles):
            return profiles[idx]
    except ValueError:
        pass
    
    console.print("[red]Invalid selection[/red]")
    return None


def run_scan_for_profile(profile: Profile) -> dict:
    """Execute scan for a profile with progress display."""
    _print_ethics_banner()

    config_path = Path.home() / ".osintkit" / "config.yaml"
    cfg = load_config(config_path)

    # Create output directory (use ~/osint-results or config setting)
    target = "_".join(filter(None, [profile.name, profile.email, profile.username, profile.phone])).replace(" ", "_")
    date_str = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    # Use config output_dir or default to ~/osint-results
    base_dir = Path(cfg.output_dir).expanduser() if cfg.output_dir else Path.home() / "osint-results"
    output_dir = base_dir / f"{target}_{date_str}"
    output_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"\n[bold]Scanning: {profile.name or profile.email or profile.username}[/bold]")
    console.print(f"[dim]Output: {output_dir}[/dim]\n")

    # Run scanner
    scanner = Scanner(config=cfg, output_dir=output_dir, console=console)
    inputs = {
        "name": profile.name,
        "email": profile.email,
        "username": profile.username,
        "phone": profile.phone,
    }

    findings = scanner.run(inputs)

    # Write outputs
    json_path = scanner.write_json(findings)
    html_path = scanner.write_html(findings)
    md_path = scanner.write_md(findings)

    # Show results
    score = findings.get("risk_score", 0)
    color = "red" if score >= 70 else "yellow" if score >= 40 else "green"

    total_findings = sum(len(f) for f in findings.get("findings", {}).values())

    console.print(f"\n[bold {color}]Risk Score: {score}/100[/bold {color}]")
    console.print(f"Total findings: {total_findings}")
    console.print(f"\n[green]✓[/green] JSON: {json_path}")
    console.print(f"[green]✓[/green] HTML: {html_path}")
    console.print(f"[green]✓[/green] Markdown: {str(md_path)}")

    return {
        "findings": findings,
        "json_path": json_path,
        "html_path": html_path,
        "md_path": md_path,
        "score": score,
        "total": total_findings,
    }


# ============ COMMANDS ============

@app.command()
def setup():
    """Configure API keys. Existing keys are preserved unless a new value is entered."""
    config_path = Path.home() / ".osintkit" / "config.yaml"
    existing = load_config(config_path)

    console.print("\n[bold cyan]═══ API Key Setup ═══[/bold cyan]\n")
    console.print("Press [bold]Enter[/bold] to keep an existing key. Type a new value to update it.\n")

    api_key_list = [
        ("hibp", "HaveIBeenPwned", "https://haveibeenpwned.com/API/Key"),
        ("breachdirectory", "BreachDirectory", "https://rapidapi.com/"),
        ("leakcheck", "LeakCheck", "https://leakcheck.io/"),
        ("intelbase", "Intelbase", "https://intelbase.is/"),
        ("google_cse_key", "Google CSE API Key", "https://developers.google.com/custom-search/"),
        ("google_cse_cx", "Google CSE Engine ID", ""),
        ("numverify", "NumVerify", "https://numverify.com/"),
        ("emailrep", "EmailRep", "https://emailrep.io/"),
        ("hunter", "Hunter.io (email finder)", "https://hunter.io"),
        ("github", "GitHub Personal Access Token", "https://github.com/settings/tokens"),
        ("securitytrails", "SecurityTrails", "https://securitytrails.com"),
    ]

    keys_dict = existing.api_keys.model_dump()

    for key_name, label, url in api_key_list:
        current = keys_dict.get(key_name, "")
        status = "[green][set][/green]" if current else "[dim][not set][/dim]"
        hint = f" ({url})" if url else ""
        value = Prompt.ask(f"  {status} {label}{hint}", default="")
        if value.strip():
            keys_dict[key_name] = value.strip()

    updated = Config(
        output_dir=existing.output_dir,
        timeout_seconds=existing.timeout_seconds,
        api_keys=APIKeys(**keys_dict),
    )
    save_config(updated, config_path)
    console.print(f"\n[green]✓[/green] Config saved: {config_path}")


config_app = typer.Typer(help="Manage osintkit configuration.")
app.add_typer(config_app, name="config")


@config_app.command("set-key")
def config_set_key(
    key: str = typer.Argument(..., help="API key name (e.g. github, hunter)"),
    value: str = typer.Argument(..., help="The API key value"),
):
    """Update a single API key without touching others."""
    valid_keys = set(APIKeys.model_fields.keys())
    if key not in valid_keys:
        console.print(f"[red]Unknown key '{key}'.[/red]")
        console.print(f"Valid keys: {', '.join(sorted(valid_keys))}")
        raise typer.Exit(1)
    update_api_key(key, value)


@config_app.command("show")
def config_show():
    """Show which API keys are set (values are not shown)."""
    config_path = Path.home() / ".osintkit" / "config.yaml"
    cfg = load_config(config_path)
    keys_dict = cfg.api_keys.model_dump()

    table = Table(title="API Keys", show_header=True)
    table.add_column("Key", style="cyan")
    table.add_column("Status")

    for key_name in sorted(keys_dict.keys()):
        status = "[green]set[/green]" if keys_dict[key_name] else "[dim]not set[/dim]"
        table.add_row(key_name, status)

    console.print(table)


@app.command()
def new():
    """Create a new person profile."""
    check_first_time()
    
    console.print("\n[bold cyan]═══ New Profile ═══[/bold cyan]\n")
    
    # Step-by-step input
    name = Prompt.ask("1. Full name").strip()
    email = Prompt.ask("2. Email (optional)", default="").strip()
    username = Prompt.ask("3. Username (optional)", default="").strip()
    phone_raw = Prompt.ask("4. Phone (optional)", default="").strip()
    if phone_raw:
        phone = validate_and_format_phone(phone_raw)
        if phone is None:
            console.print(f"[yellow]Warning: Could not parse phone '{phone_raw}' — storing as-is[/yellow]")
            phone = phone_raw
    else:
        phone = ""
    
    if not any([name, email, username, phone]):
        console.print("[red]Error: Need at least name, email, username, or phone[/red]")
        raise typer.Exit(1)
    
    # Check for existing
    existing = get_profile_by_identifier(name, email, username, phone)
    if existing:
        console.print(f"\n[yellow]⚠ Profile already exists:[/yellow] {existing.id}")
        console.print(f"   Name: {existing.name or '—'}")
        console.print(f"   Email: {existing.email or '—'}")
        if Confirm.ask("\nUpdate this profile?"):
            profile = existing
            if name:
                profile.name = name
            if email:
                profile.email = email
            if username:
                profile.username = username
            if phone:
                profile.phone = phone
            store.update(profile)
            console.print(f"[green]✓[/green] Updated profile: {profile.id}")
        else:
            console.print("[red]Cancelled[/red]")
            return
    else:
        profile = Profile(
            name=name or None,
            email=email or None,
            username=username or None,
            phone=phone or None,
        )
        store.create(profile)
        console.print(f"\n[green]✓[/green] Created profile: {profile.id}")
        console.print(f"   Name: {name or '—'}")
        console.print(f"   Email: {email or '—'}")
        console.print(f"   Username: {username or '—'}")
        console.print(f"   Phone: {phone or '—'}")
    
    # Ask to scan
    if Confirm.ask("\nRun scan now?"):
        result = run_scan_for_profile(profile)
        
        # Save to history
        scan_record = ScanHistory(
            scan_id=datetime.now().strftime("%Y%m%d_%H%M%S"),
            timestamp=datetime.now().isoformat(),
            inputs={"name": profile.name, "email": profile.email, "username": profile.username, "phone": profile.phone},
            risk_score=result["score"],
            findings_count=result["total"],
            findings_file=str(result["json_path"]),
            html_file=str(result["html_path"]),
        )
        store.add_scan_result(profile.id, scan_record)


@app.command()
def list(
    filter_tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Filter by tag"),
):
    """List all profiles. Filter with --tag <name>."""
    profiles = store.list(tag=filter_tag)
    
    if not profiles:
        console.print("\n[yellow]No profiles found.[/yellow]")
        console.print("Use [cyan]osintkit new[/cyan] to create one.\n")
        return
    
    console.print(f"\n[bold]Profiles ({len(profiles)}):[/bold]\n")
    
    table = Table()
    table.add_column("#", width=3)
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Email")
    table.add_column("Username")
    table.add_column("Scans")
    table.add_column("Risk")
    
    for i, p in enumerate(profiles, 1):
        last_scan = p.scan_history[-1] if p.scan_history else None
        table.add_row(
            str(i),
            p.id,
            p.name or "—",
            p.email or "—",
            p.username or "—",
            str(len(p.scan_history)),
            str(last_scan.risk_score) if last_scan else "—",
        )
    
    console.print(table)
    console.print()
    if _update_thread:
        _update_thread.join(timeout=4)
    _print_update_notice()


@app.command()
def refresh(profile_ref: str = typer.Argument(None, help="Profile ID or name")):
    """Refresh scan for a profile."""
    if profile_ref:
        # Try to find by ID or name
        profile = store.get(profile_ref)
        if not profile:
            profiles = store.list()
            for p in profiles:
                if p.name and p.name.lower() == profile_ref.lower():
                    profile = p
                    break
        if not profile:
            console.print(f"[red]Profile not found: {profile_ref}[/red]")
            raise typer.Exit(1)
    else:
        profile = select_profile()
        if not profile:
            return
    
    console.print(f"\n[bold]Refreshing: {profile.name or profile.email or profile.id}[/bold]")
    
    result = run_scan_for_profile(profile)
    
    # Save to history
    scan_record = ScanHistory(
        scan_id=datetime.now().strftime("%Y%m%d_%H%M%S"),
        timestamp=datetime.now().isoformat(),
        inputs={"name": profile.name, "email": profile.email, "username": profile.username, "phone": profile.phone},
        risk_score=result["score"],
        findings_count=result["total"],
        findings_file=str(result["json_path"]),
        html_file=str(result["html_path"]),
    )
    store.add_scan_result(profile.id, scan_record)
    console.print(f"\n[green]✓[/green] Scan saved to profile history")
    _print_update_notice()


@app.command()
def open(profile_ref: str = typer.Argument(None, help="Profile ID or name")):
    """Show profile details."""
    if profile_ref:
        profile = store.get(profile_ref)
        if not profile:
            profiles = store.list()
            for p in profiles:
                if p.name and p.name.lower() == profile_ref.lower():
                    profile = p
                    break
        if not profile:
            console.print(f"[red]Profile not found: {profile_ref}[/red]")
            raise typer.Exit(1)
    else:
        profile = select_profile()
        if not profile:
            return
    
    console.print(f"\n[bold cyan]═══ Profile: {profile.name or profile.id} ═══[/bold cyan]\n")
    console.print(f"  [bold]ID:[/bold] {profile.id}")
    console.print(f"  [bold]Name:[/bold] {profile.name or '—'}")
    console.print(f"  [bold]Email:[/bold] {profile.email or '—'}")
    console.print(f"  [bold]Username:[/bold] {profile.username or '—'}")
    console.print(f"  [bold]Phone:[/bold] {profile.phone or '—'}")
    console.print(f"  [bold]Notes:[/bold] {profile.notes or '—'}")
    console.print(f"  [bold]Created:[/bold] {profile.created_at[:10] if profile.created_at else '—'}")
    
    if profile.scan_history:
        console.print(f"\n[bold]Scan History ({len(profile.scan_history)} scans):[/bold]\n")
        
        table = Table()
        table.add_column("Date")
        table.add_column("Risk")
        table.add_column("Findings")
        table.add_column("Report")
        
        for scan in reversed(profile.scan_history[-10:]):
            report_name = Path(scan.html_file).name if scan.html_file else "—"
            table.add_row(
                scan.timestamp[:10],
                str(scan.risk_score),
                str(scan.findings_count),
                report_name,
            )
        
        console.print(table)
        
        # Open latest report
        if profile.scan_history and profile.scan_history[-1].html_file:
            latest = profile.scan_history[-1]
            if Confirm.ask(f"\nOpen latest report?"):
                import webbrowser
                webbrowser.open(f"file://{latest.html_file}")
    else:
        console.print("\n[yellow]No scans yet. Use 'osintkit refresh' to run a scan.[/yellow]")
    
    console.print()


@app.command()
def export(
    profile_ref: str = typer.Argument(None, help="Profile ID or name"),
    format: str = typer.Option("json", "--format", "-f", help="Output format: json or md"),
    output: Path = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Export profile data."""
    if profile_ref:
        profile = store.get(profile_ref)
        if not profile:
            profiles = store.list()
            for p in profiles:
                if p.name and p.name.lower() == profile_ref.lower():
                    profile = p
                    break
        if not profile:
            console.print(f"[red]Profile not found: {profile_ref}[/red]")
            raise typer.Exit(1)
    else:
        profile = select_profile()
        if not profile:
            return
    
    # Load latest findings
    if not profile.scan_history:
        console.print("[yellow]No scans to export. Run 'osintkit refresh' first.[/yellow]")
        return
    
    latest_scan = profile.scan_history[-1]
    
    if format == "json":
        if output is None:
            output = Path.cwd() / f"{profile.name or profile.id}_export.json"
        
        # Load the findings
        if latest_scan.findings_file and Path(latest_scan.findings_file).exists():
            import shutil
            shutil.copy(latest_scan.findings_file, output)
            console.print(f"[green]✓[/green] Exported JSON: {output}")
        else:
            console.print("[red]Findings file not found[/red]")
    
    elif format == "md":
        if output is None:
            output = Path.cwd() / f"{profile.name or profile.id}_export.md"
        
        # Create markdown report
        findings_data = {}
        if latest_scan.findings_file and Path(latest_scan.findings_file).exists():
            with open(latest_scan.findings_file) as f:
                findings_data = json.load(f)
        
        md_content = f"""# osintkit Report: {profile.name or profile.id}

**Generated:** {datetime.now().isoformat()}

## Profile Information

- **Name:** {profile.name or '—'}
- **Email:** {profile.email or '—'}
- **Username:** {profile.username or '—'}
- **Phone:** {profile.phone or '—'}

## Risk Score: {latest_scan.risk_score}/100

## Findings Summary

"""
        for module_name, findings in findings_data.get("findings", {}).items():
            if findings:
                md_content += f"### {module_name}\n\n"
                for finding in findings:
                    md_content += f"- **{finding.get('type', 'Unknown')}** via {finding.get('source', 'unknown')}\n"
                    if finding.get('url'):
                        md_content += f"  - URL: {finding['url']}\n"
                md_content += "\n"
        
        output.write_text(md_content)
        console.print(f"[green]✓[/green] Exported Markdown: {output}")
    
    else:
        console.print(f"[red]Unknown format: {format}[/red]")


@app.command()
def delete(profile_ref: str = typer.Argument(None, help="Profile ID or name")):
    """Delete a profile."""
    if profile_ref:
        profile = store.get(profile_ref)
    else:
        profile = select_profile()
    
    if not profile:
        return
    
    if Confirm.ask(f"\nDelete profile '{profile.name or profile.id}'?"):
        store.delete(profile.id)
        console.print(f"[green]✓[/green] Deleted")


@app.command()
def version():
    """Show version. Also available as: osintkit -v"""
    if _update_thread:
        _update_thread.join(timeout=4)
    console.print(f"osintkit v{__version__}")
    _print_update_notice()


@app.command()
def update():
    """Check for updates and install the latest version."""
    import subprocess

    console.print("\n[bold]Checking for updates...[/bold]")

    if _update_thread:
        _update_thread.join(timeout=5)

    if _update_available:
        console.print(f"[cyan]New version available: {_update_available}[/cyan]")
        console.print(f"[dim]Current: {__version__}[/dim]\n")
        if Confirm.ask("Install now?", default=True):
            console.print("[dim]Running: npm install -g osintkit[/dim]\n")
            result = subprocess.run(["npm", "install", "-g", "osintkit"], check=False)
            if result.returncode == 0:
                console.print(f"\n[green]✓[/green] Updated to osintkit {_update_available}")
                console.print("[dim]Restart your terminal for changes to take effect.[/dim]")
            else:
                console.print("\n[red]Update failed.[/red] Try manually: npm install -g osintkit")
    else:
        console.print(f"[green]✓[/green] Already on latest version (v{__version__})")


@app.command()
def tag(
    profile_ref: str = typer.Argument(..., help="Profile ID or name"),
    add: Optional[str] = typer.Option(None, "--add", "-a", help="Tag to add"),
    remove: Optional[str] = typer.Option(None, "--remove", "-r", help="Tag to remove"),
    list_tags: bool = typer.Option(False, "--list", "-l", help="List tags on profile"),
):
    """Add, remove, or list tags on a profile.

    Examples:
      osintkit tag abc123 --add client
      osintkit tag abc123 --remove client
      osintkit tag abc123 --list
      osintkit list --tag client        (filter list by tag)
    """
    profile = store.get(profile_ref)
    if not profile:
        profiles = store.list()
        for p in profiles:
            if p.name and p.name.lower() == profile_ref.lower():
                profile = p
                break
    if not profile:
        console.print(f"[red]Profile not found: {profile_ref}[/red]")
        raise typer.Exit(1)

    if add:
        if add not in profile.tags:
            profile.tags.append(add)
            store.update(profile)
            console.print(f"[green]✓[/green] Added tag '{add}' to {profile.name or profile.id}")
        else:
            console.print(f"[yellow]Tag '{add}' already exists[/yellow]")

    elif remove:
        if remove in profile.tags:
            profile.tags.remove(remove)
            store.update(profile)
            console.print(f"[green]✓[/green] Removed tag '{remove}' from {profile.name or profile.id}")
        else:
            console.print(f"[yellow]Tag '{remove}' not found[/yellow]")

    else:
        # Default: list tags
        if profile.tags:
            console.print(f"\nTags on [cyan]{profile.name or profile.id}[/cyan]: " +
                         ", ".join(f"[bold]{t}[/bold]" for t in profile.tags))
        else:
            console.print(f"[dim]No tags on {profile.name or profile.id}[/dim]")


@app.command()
def bug():
    """Report a bug or request a feature."""
    import webbrowser
    import urllib.parse

    console.print("\n[bold]Report a bug or request a feature[/bold]\n")
    console.print(f"  [cyan]GitHub Issues[/cyan]    https://github.com/diesesschnitzel/osintkit/issues/new")
    console.print(f"  [cyan]Email[/cyan]             help@oss.codecho.de")
    console.print(f"  [cyan]Docs[/cyan]              https://docs.codecho.de/osintkit/troubleshooting.html\n")

    if Confirm.ask("Open a pre-filled GitHub issue in your browser?", default=True):
        title = urllib.parse.quote("Bug report: ")
        body = urllib.parse.quote(
            f"**osintkit version:** {__version__}\n"
            f"**Python:** {sys.version.split()[0]}\n"
            f"**OS:** {sys.platform}\n\n"
            "**Describe the bug:**\n\n"
            "**Steps to reproduce:**\n1. \n2. \n\n"
            "**Expected behavior:**\n\n"
            "**Actual behavior:**\n"
        )
        webbrowser.open(
            f"https://github.com/diesesschnitzel/osintkit/issues/new"
            f"?title={title}&body={body}&labels=bug"
        )
        console.print("[green]✓[/green] Opened in browser")


if __name__ == "__main__":
    app()
