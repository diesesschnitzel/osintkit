"""AbuseIPDB IP abuse lookup (Stage 2 — requires API key).

Free tier: 1,000 checks/day.
Get a free key at: https://www.abuseipdb.com/register
"""

import asyncio
import socket
from typing import Dict, List

import httpx

from osintkit.modules import RateLimitError, InvalidKeyError


def _resolve_domain(domain: str) -> str | None:
    """Resolve domain to IP via DNS. Returns None on failure."""
    try:
        return socket.gethostbyname(domain)
    except Exception:
        return None


def _extract_domain(inputs: dict) -> str | None:
    email = inputs.get("email", "")
    if email and "@" in email:
        return email.split("@")[1].lower()
    return None


async def run(inputs: dict, api_key: str) -> List[Dict]:
    """Look up abuse reports for the IP behind the target's email domain."""
    domain = _extract_domain(inputs)
    if not domain:
        return []

    loop = asyncio.get_event_loop()
    ip = await loop.run_in_executor(None, _resolve_domain, domain)
    if not ip:
        return []

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
            resp = await client.get(
                "https://api.abuseipdb.com/api/v2/check",
                params={"ipAddress": ip, "maxAgeInDays": "90"},
                headers={"Key": api_key, "Accept": "application/json"},
            )

        if resp.status_code == 429:
            raise RateLimitError("AbuseIPDB rate limit reached")
        if resp.status_code in (401, 403):
            raise InvalidKeyError("AbuseIPDB API key invalid")
        if resp.status_code != 200:
            return []

        data = resp.json().get("data", {})

        return [{
            "source": "abuseipdb",
            "type": "ip_abuse",
            "data": {
                "domain": domain,
                "ip_address": data.get("ipAddress"),
                "abuse_confidence_score": data.get("abuseConfidenceScore"),
                "country_code": data.get("countryCode"),
                "isp": data.get("isp"),
                "domain_name": data.get("domain"),
                "total_reports": data.get("totalReports"),
                "num_distinct_users": data.get("numDistinctUsers"),
                "last_reported_at": data.get("lastReportedAt"),
                "is_tor": data.get("isTor"),
                "usage_type": data.get("usageType"),
            },
            "confidence": 0.85,
            "url": f"https://www.abuseipdb.com/check/{data.get('ipAddress', ip)}",
        }]

    except (RateLimitError, InvalidKeyError):
        raise
    except Exception:
        return []
