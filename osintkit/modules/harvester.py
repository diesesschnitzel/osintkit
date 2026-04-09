"""Web presence enumeration via theHarvester."""

import asyncio
import logging
import shutil
import tempfile
import json
from pathlib import Path
from typing import Any, Dict, List

from osintkit.modules import ModuleError

logger = logging.getLogger(__name__)

COMMON_PROVIDERS = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com"]


async def run_web_presence(inputs: Dict[str, Any], timeout_seconds: int) -> List[Dict]:
    """Run web presence enumeration using theHarvester."""
    email = inputs.get("email")
    if not email or "@" not in email:
        return []
    
    domain = email.split("@")[1]
    if domain in COMMON_PROVIDERS:
        return []

    if not shutil.which("theHarvester"):
        raise ModuleError("theHarvester not installed")

    tmp_base = tempfile.mkdtemp(prefix="osintkit_harvester_")
    output_file = Path(tmp_base) / f"harvester_{domain}.json"
    try:
        proc = await asyncio.create_subprocess_exec(
            "theHarvester", "-d", domain, "-b", "all", "-f", str(output_file),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        await asyncio.wait_for(proc.communicate(), timeout=timeout_seconds + 30)

        findings = []
        if output_file.exists():
            try:
                with open(output_file) as f:
                    data = json.load(f)
                for e in data.get("emails", []):
                    findings.append({"source": "harvester", "type": "associated_email",
                        "data": {"email": e, "domain": domain}, "confidence": 0.7, "url": None})
                for h in data.get("hosts", []):
                    findings.append({"source": "harvester", "type": "associated_host",
                        "data": {"host": h}, "confidence": 0.6, "url": f"http://{h}"})
            except Exception as e:
                raise ModuleError(str(e))
        shutil.rmtree(tmp_base, ignore_errors=True)
        return findings
    except asyncio.TimeoutError:
        raise ModuleError("theHarvester timed out")
