"""Email account enumeration via Holehe."""

import asyncio
import shutil
from typing import Any, Dict, List

from osintkit.modules import ModuleError


async def run_email_accounts(inputs: Dict[str, Any], timeout_seconds: int) -> List[Dict]:
    """Run email account enumeration using Holehe."""
    email = inputs.get("email")
    if not email:
        return []

    if not shutil.which("holehe"):
        raise ModuleError("Holehe not installed. Install with: pip install holehe")

    try:
        proc = await asyncio.create_subprocess_exec(
            "holehe", "--email", email,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_seconds + 10)

        output = stdout.decode()
        findings = []
        for line in output.splitlines():
            if "+" in line or "used" in line.lower():
                parts = line.strip().split()
                if parts:
                    findings.append({
                        "source": "holehe", "type": "email_account",
                        "data": {"platform": parts[0], "email": email},
                        "confidence": 0.8, "url": None
                    })
        return findings
    except asyncio.TimeoutError:
        raise ModuleError("Holehe timed out")
