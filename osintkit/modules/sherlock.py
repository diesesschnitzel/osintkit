"""Sherlock social profile enumeration module."""

import asyncio
import shutil
from typing import Any, Dict, List


async def run_sherlock(inputs: Dict[str, Any], timeout_seconds: int) -> List[Dict]:
    """Run sherlock subprocess for username lookup.

    Returns list of found social profiles across platforms.
    Skips gracefully if sherlock is not installed.
    """
    username = inputs.get("username")
    if not username:
        return []

    if not shutil.which("sherlock"):
        from osintkit.modules import MissingToolError
        raise MissingToolError("Sherlock not installed. Install with: pip install sherlock-project")

    try:
        proc = await asyncio.create_subprocess_exec(
            "sherlock", username, "--print-found", "--timeout", "10",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout_seconds + 15)

        findings = []
        for line in stdout.decode(errors="replace").splitlines():
            line = line.strip()
            if line.startswith("[+]"):
                # Format: [+] Platform: https://...
                parts = line[3:].strip().split(":", 1)
                platform = parts[0].strip() if parts else "unknown"
                url = parts[1].strip() if len(parts) > 1 else None
                findings.append({
                    "source": "sherlock",
                    "type": "social_profile",
                    "data": {"platform": platform, "username": username},
                    "url": url,
                })
        return findings

    except asyncio.TimeoutError:
        return []
    except Exception:
        return []
