"""Scanner orchestrator - runs all OSINT modules in parallel with progress."""

import asyncio
from pathlib import Path
from datetime import datetime
from typing import Any, Callable, Dict, List
from rich.console import Console
from rich.progress import Progress

from osintkit.config import Config
from osintkit.modules import RateLimitError, InvalidKeyError, MissingToolError
from osintkit.output.json_writer import write_json
from osintkit.output.html_writer import write_html
from osintkit.output.md_writer import write_md
from osintkit.risk import calculate_risk_score


class Scanner:
    """Orchestrates OSINT module execution with progress display."""

    def __init__(self, config: Config, output_dir: Path, console: Console):
        self.config = config
        self.output_dir = output_dir
        self.console = console
        self.modules = self._load_modules()

    def _load_modules(self) -> List[tuple]:
        """Load all available OSINT modules (Stage 1 + Stage 2 if keys present)."""
        modules = [
            ("social_profiles", self._run_social_profiles, "Social media profiles"),
            ("email_accounts", self._run_email_accounts, "Email accounts"),
            ("password_exposure", self._run_password_exposure, "Password breaches"),
            ("web_presence", self._run_web_presence, "Web presence"),
            ("cert_transparency", self._run_cert_transparency, "SSL certificates"),
            ("breach_exposure", self._run_breach_exposure, "Data breaches"),
            ("dark_web", self._run_dark_web, "Dark web"),
            ("paste_sites", self._run_paste_sites, "Paste sites"),
            ("data_brokers", self._run_data_brokers, "Data brokers"),
            ("phone", self._run_phone, "Phone info"),
            # New Stage 1 modules
            ("sherlock", self._run_sherlock, "Social profiles (Sherlock)"),
            ("gravatar", self._run_gravatar, "Gravatar profile"),
            ("wayback", self._run_wayback, "Wayback Machine"),
            ("phone_info", self._run_phone_info, "Phone analysis"),
            ("hibp_kanon", self._run_hibp_kanon, "Password k-anonymity check"),
            ("github_api", self._run_stage2_github, "GitHub profile"),  # always runs; token optional
            ("emailrep", self._run_emailrep, "Email reputation"),
            ("whois", self._run_whois, "WHOIS domain registration"),
            ("urlscan", self._run_urlscan, "Domain scan history"),
        ]

        # Stage 2 modules — only included when corresponding API key is set
        api_keys = self.config.api_keys
        stage2_map = [
            ("leakcheck", api_keys.leakcheck, self._run_stage2_leakcheck, "LeakCheck breach lookup"),
            ("hunter", api_keys.hunter, self._run_stage2_hunter, "Hunter email verify"),
            ("numverify", api_keys.numverify, self._run_stage2_numverify, "NumVerify phone"),
            (
                "securitytrails",
                api_keys.securitytrails,
                self._run_stage2_securitytrails,
                "SecurityTrails subdomains",
            ),
            ("virustotal", api_keys.virustotal, self._run_stage2_virustotal, "VirusTotal domain"),
            ("otx", api_keys.otx, self._run_stage2_otx, "OTX AlienVault threat intel"),
            ("abuseipdb", api_keys.abuseipdb, self._run_stage2_abuseipdb, "AbuseIPDB IP check"),
            ("epieos", api_keys.epieos, self._run_stage2_epieos, "Epieos Google/Apple lookup"),
        ]

        for name, key, func, desc in stage2_map:
            if key and key.strip():
                modules.append((name, func, desc))

        return modules

    # ---- Stage 1 module runners ----

    async def _run_social_profiles(self, inputs: Dict) -> List[Dict]:
        from osintkit.modules.social import run_social_profiles
        return await run_social_profiles(inputs, self.config.timeout_seconds)

    async def _run_email_accounts(self, inputs: Dict) -> List[Dict]:
        from osintkit.modules.holehe import run_email_accounts
        return await run_email_accounts(inputs, self.config.timeout_seconds)

    async def _run_password_exposure(self, inputs: Dict) -> List[Dict]:
        from osintkit.modules.hibp import run_password_exposure
        return await run_password_exposure(inputs)

    async def _run_web_presence(self, inputs: Dict) -> List[Dict]:
        from osintkit.modules.harvester import run_web_presence
        return await run_web_presence(inputs, self.config.timeout_seconds)

    async def _run_cert_transparency(self, inputs: Dict) -> List[Dict]:
        from osintkit.modules.certs import run_cert_transparency
        return await run_cert_transparency(inputs)

    async def _run_breach_exposure(self, inputs: Dict) -> List[Dict]:
        from osintkit.modules.breach import run_breach_exposure
        return await run_breach_exposure(inputs, self.config.api_keys)

    async def _run_dark_web(self, inputs: Dict) -> List[Dict]:
        from osintkit.modules.dark_web import run_dark_web
        return await run_dark_web(inputs, self.config.api_keys)

    async def _run_paste_sites(self, inputs: Dict) -> List[Dict]:
        from osintkit.modules.paste import run_paste_sites
        return await run_paste_sites(inputs, self.config.api_keys)

    async def _run_data_brokers(self, inputs: Dict) -> List[Dict]:
        from osintkit.modules.brokers import run_data_brokers
        return await run_data_brokers(inputs, self.config.api_keys)

    async def _run_phone(self, inputs: Dict) -> List[Dict]:
        from osintkit.modules.phone import run_phone
        return await run_phone(inputs, self.config.api_keys)

    async def _run_sherlock(self, inputs: Dict) -> List[Dict]:
        from osintkit.modules.sherlock import run_sherlock
        return await run_sherlock(inputs, self.config.timeout_seconds)

    async def _run_gravatar(self, inputs: Dict) -> List[Dict]:
        from osintkit.modules.gravatar import run_gravatar
        return await run_gravatar(inputs)

    async def _run_wayback(self, inputs: Dict) -> List[Dict]:
        from osintkit.modules.wayback import run_wayback
        return await run_wayback(inputs)

    async def _run_phone_info(self, inputs: Dict) -> List[Dict]:
        from osintkit.modules.libphonenumber_info import run_libphonenumber
        return await run_libphonenumber(inputs)

    async def _run_hibp_kanon(self, inputs: Dict) -> List[Dict]:
        from osintkit.modules.hibp_kanon import run_hibp_kanon
        return await run_hibp_kanon(inputs)

    async def _run_emailrep(self, inputs: Dict) -> List[Dict]:
        from osintkit.modules.emailrep import run_emailrep
        return await run_emailrep(inputs, self.config.api_keys.emailrep or "")

    async def _run_whois(self, inputs: Dict) -> List[Dict]:
        from osintkit.modules.whois_lookup import run_whois
        return await run_whois(inputs)

    async def _run_urlscan(self, inputs: Dict) -> List[Dict]:
        from osintkit.modules.urlscan import run_urlscan
        return await run_urlscan(inputs)

    # ---- Stage 2 module runners ----

    async def _run_stage2_leakcheck(self, inputs: Dict) -> List[Dict]:
        from osintkit.modules.stage2.leakcheck import run
        return await run(inputs, self.config.api_keys.leakcheck)

    async def _run_stage2_hunter(self, inputs: Dict) -> List[Dict]:
        from osintkit.modules.stage2.hunter import run
        return await run(inputs, self.config.api_keys.hunter)

    async def _run_stage2_numverify(self, inputs: Dict) -> List[Dict]:
        from osintkit.modules.stage2.numverify import run
        return await run(inputs, self.config.api_keys.numverify)

    async def _run_stage2_github(self, inputs: Dict) -> List[Dict]:
        from osintkit.modules.stage2.github_api import run
        return await run(inputs, self.config.api_keys.github)

    async def _run_stage2_securitytrails(self, inputs: Dict) -> List[Dict]:
        from osintkit.modules.stage2.securitytrails import run
        return await run(inputs, self.config.api_keys.securitytrails)

    async def _run_stage2_virustotal(self, inputs: Dict) -> List[Dict]:
        from osintkit.modules.stage2.virustotal import run
        return await run(inputs, self.config.api_keys.virustotal)

    async def _run_stage2_otx(self, inputs: Dict) -> List[Dict]:
        from osintkit.modules.stage2.otx import run
        return await run(inputs, self.config.api_keys.otx)

    async def _run_stage2_abuseipdb(self, inputs: Dict) -> List[Dict]:
        from osintkit.modules.stage2.abuseipdb import run
        return await run(inputs, self.config.api_keys.abuseipdb)

    async def _run_stage2_epieos(self, inputs: Dict) -> List[Dict]:
        from osintkit.modules.stage2.epieos import run
        return await run(inputs, self.config.api_keys.epieos)

    # ---- Execution ----

    def run(self, inputs: Dict) -> Dict[str, Any]:
        """Run all modules without progress display."""
        findings = {
            "scan_date": datetime.now().isoformat(),
            "inputs": inputs,
            "modules": {},
            "findings": {},
            "risk_score": 0,
        }

        async def run_one(name: str, func: Callable):
            try:
                result = await func(inputs)
                findings["modules"][name] = {"status": "done", "count": len(result)}
                findings["findings"][name] = result
            except RateLimitError as e:
                findings["modules"][name] = {"status": "rate_limited", "error": str(e)}
                findings["findings"][name] = []
            except InvalidKeyError as e:
                findings["modules"][name] = {"status": "invalid_key", "error": str(e)}
                findings["findings"][name] = []
            except MissingToolError as e:
                findings["modules"][name] = {"status": "not_installed", "error": str(e)}
                findings["findings"][name] = []
            except Exception as e:
                findings["modules"][name] = {"status": "failed", "error": str(e)}
                findings["findings"][name] = []

        async def main():
            await asyncio.gather(*[run_one(n, f) for n, f, _ in self.modules])

        asyncio.run(main())
        findings["risk_score"] = calculate_risk_score(findings["findings"])
        return findings

    def run_with_progress(self, inputs: Dict, progress: Progress) -> Dict[str, Any]:
        """Run all modules with progress display."""
        findings = {
            "scan_date": datetime.now().isoformat(),
            "inputs": inputs,
            "modules": {},
            "findings": {},
            "risk_score": 0,
        }

        tasks = {}
        for name, func, desc in self.modules:
            task_id = progress.add_task(f"[cyan]{desc}...", total=None)
            tasks[name] = {"func": func, "task_id": task_id, "desc": desc}

        async def run_one(name: str):
            task_info = tasks[name]
            try:
                result = await task_info["func"](inputs)
                findings["modules"][name] = {"status": "done", "count": len(result)}
                findings["findings"][name] = result
                progress.update(
                    task_info["task_id"],
                    completed=True,
                    description=f"[green]done {task_info['desc']} ({len(result)})[/green]",
                )
            except RateLimitError as e:
                findings["modules"][name] = {"status": "rate_limited", "error": str(e)}
                findings["findings"][name] = []
                progress.update(
                    task_info["task_id"],
                    completed=True,
                    description=f"[yellow]rate limited {task_info['desc']}[/yellow]",
                )
            except InvalidKeyError as e:
                findings["modules"][name] = {"status": "invalid_key", "error": str(e)}
                findings["findings"][name] = []
                progress.update(
                    task_info["task_id"],
                    completed=True,
                    description=f"[yellow]invalid key {task_info['desc']}[/yellow]",
                )
            except MissingToolError as e:
                findings["modules"][name] = {"status": "not_installed", "error": str(e)}
                findings["findings"][name] = []
                progress.update(
                    task_info["task_id"],
                    completed=True,
                    description=f"[yellow]not installed — {task_info['desc']}[/yellow]",
                )
            except Exception as e:
                findings["modules"][name] = {"status": "failed", "error": str(e)}
                findings["findings"][name] = []
                progress.update(
                    task_info["task_id"],
                    completed=True,
                    description=f"[red]failed {task_info['desc']}[/red]",
                )

        async def main():
            await asyncio.gather(*[run_one(name) for name in tasks])

        asyncio.run(main())
        findings["risk_score"] = calculate_risk_score(findings["findings"])
        return findings

    def write_json(self, findings: Dict) -> Path:
        api_keys = self._get_api_key_values()
        return write_json(findings, self.output_dir, api_keys=api_keys)

    def write_html(self, findings: Dict) -> Path:
        api_keys = self._get_api_key_values()
        return write_html(findings, self.output_dir, api_keys=api_keys)

    def write_md(self, findings: Dict) -> Path:
        api_keys = self._get_api_key_values()
        return write_md(findings, self.output_dir, api_keys=api_keys)

    def _get_api_key_values(self) -> Dict[str, str]:
        """Return dict of all non-empty API key values for scrubbing."""
        keys = {}
        for field, value in self.config.api_keys.model_dump().items():
            if value and isinstance(value, str):
                keys[field] = value
        return keys
