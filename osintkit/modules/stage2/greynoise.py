"""GreyNoise Community — IP noise/scanner classification (Stage 2, free key).

Free community account at: https://www.greynoise.io/plans/free-intelligence
50 lookups/week on the community plan.
"""

import asyncio
import socket
from typing import Dict, List

import httpx

from osintkit.modules import RateLimitError, InvalidKeyError


def _extract_domain(inputs: dict) -> str | None:
    email = inputs.get("email", "")
    if email and "@" in email:
        return email.split("@")[1].lower()
    return None


def _resolve(domain: str) -> str | None:
    try:
        return socket.gethostbyname(domain)
    except Exception:
        return None


async def run(inputs: dict, api_key: str) -> List[Dict]:
    """Classify the IP behind the target's email domain via GreyNoise Community API."""
    domain = _extract_domain(inputs)
    if not domain:
        return []

    loop = asyncio.get_event_loop()
    ip = await loop.run_in_executor(None, _resolve, domain)
    if not ip:
        return []

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
            resp = await client.get(
                f"https://api.greynoise.io/v3/community/{ip}",
                headers={"key": api_key},
            )

        if resp.status_code == 429:
            raise RateLimitError("GreyNoise rate limit reached (50/week on free plan)")
        if resp.status_code in (401, 403):
            raise InvalidKeyError("GreyNoise API key invalid")
        if resp.status_code == 404:
            # IP not in GreyNoise dataset — nothing found
            return []
        if resp.status_code != 200:
            return []

        data = resp.json()

        return [{
            "source": "greynoise",
            "type": "ip_noise",
            "data": {
                "domain": domain,
                "ip": ip,
                "noise": data.get("noise"),             # True = known internet scanner
                "riot": data.get("riot"),               # True = benign service (Google, etc.)
                "classification": data.get("classification"),  # benign/malicious/unknown
                "name": data.get("name"),
                "last_seen": data.get("last_seen"),
                "message": data.get("message"),
            },
            "confidence": 0.85,
            "url": data.get("link", f"https://viz.greynoise.io/ip/{ip}"),
        }]

    except (RateLimitError, InvalidKeyError):
        raise
    except Exception:
        return []
