"""Social profile enumeration via Maigret."""

import asyncio
import shutil
import json
from typing import Any, Dict, List

from osintkit.modules import ModuleError


async def run_social_profiles(inputs: Dict[str, Any], timeout_seconds: int) -> List[Dict]:
    """Run social profile enumeration using Maigret."""
    username = inputs.get("username")
    if not username:
        return []

    if not shutil.which("maigret"):
        raise ModuleError("Maigret not installed. Install with: pip install maigret")

    try:
        import tempfile, shutil as _shutil
        tmpdir = tempfile.mkdtemp(prefix="osintkit_maigret_")
        proc = await asyncio.create_subprocess_exec(
            "maigret", username,
            "-J", "simple",
            "--folderoutput", tmpdir,
            "--timeout", str(timeout_seconds),
            "--no-progressbar",
            stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE,
        )
        try:
            _, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_seconds + 30)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise ModuleError("Maigret timed out")

        findings = []
        import os, pathlib
        report_path = pathlib.Path(tmpdir) / f"report_{username}_simple.json"
        if report_path.exists():
            try:
                raw = json.loads(report_path.read_text())
                for site, data in raw.items():
                    if isinstance(data, dict) and data.get("status", {}).get("id") in ("claimed", "exists"):
                        findings.append({
                            "source": "maigret", "type": "social_profile",
                            "data": {"platform": site, "username": username},
                            "confidence": 0.9, "url": data.get("url_user")
                        })
            except (json.JSONDecodeError, Exception):
                pass
        _shutil.rmtree(tmpdir, ignore_errors=True)
        return findings
    except asyncio.TimeoutError:
        raise ModuleError(f"Maigret timed out")
    except json.JSONDecodeError as e:
        raise ModuleError(f"Parse error: {e}")
