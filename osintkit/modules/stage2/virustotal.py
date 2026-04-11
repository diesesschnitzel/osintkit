"""VirusTotal domain reputation (Stage 2 — requires API key).

Free tier: 500 lookups/day, 4 req/min.
Get a free key at: https://www.virustotal.com/gui/join-us
"""

from typing import Dict, List

import httpx

from osintkit.modules import RateLimitError, InvalidKeyError


def _extract_domain(inputs: dict) -> str | None:
    email = inputs.get("email", "")
    if email and "@" in email:
        return email.split("@")[1].lower()
    username = inputs.get("username", "")
    if username and "." in username:
        return username.lower()
    return None


async def run(inputs: dict, api_key: str) -> List[Dict]:
    """Check domain reputation via VirusTotal v3 API."""
    domain = _extract_domain(inputs)
    if not domain:
        return []

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0, connect=5.0)) as client:
            resp = await client.get(
                f"https://www.virustotal.com/api/v3/domains/{domain}",
                headers={"x-apikey": api_key},
            )

        if resp.status_code == 429:
            raise RateLimitError("VirusTotal rate limit reached (4 req/min on free tier)")
        if resp.status_code in (401, 403):
            raise InvalidKeyError("VirusTotal API key invalid")
        if resp.status_code != 200:
            return []

        attrs = resp.json().get("data", {}).get("attributes", {})
        stats = attrs.get("last_analysis_stats", {})

        return [{
            "source": "virustotal",
            "type": "domain_reputation",
            "data": {
                "domain": domain,
                "malicious": stats.get("malicious", 0),
                "suspicious": stats.get("suspicious", 0),
                "harmless": stats.get("harmless", 0),
                "undetected": stats.get("undetected", 0),
                "reputation": attrs.get("reputation"),
                "categories": attrs.get("categories", {}),
                "registrar": attrs.get("registrar"),
                "creation_date": attrs.get("creation_date"),
                "tags": attrs.get("tags", []),
                "total_votes": attrs.get("total_votes", {}),
            },
            "confidence": 0.9,
            "url": f"https://www.virustotal.com/gui/domain/{domain}",
        }]

    except (RateLimitError, InvalidKeyError):
        raise
    except Exception:
        return []
