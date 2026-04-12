"""IPInfo.io — ASN, country, ISP for an IP (Stage 1, optional free token).

Works anonymously (no key). With a free token (50 k/month):
  https://ipinfo.io/signup
"""

import asyncio
import socket
from typing import Any, Dict, List

import httpx


def _extract_domain(inputs: Dict[str, Any]) -> str | None:
    email = inputs.get("email", "")
    if email and "@" in email:
        return email.split("@")[1].lower()
    return None


def _resolve(domain: str) -> str | None:
    try:
        return socket.gethostbyname(domain)
    except Exception:
        return None


async def run_ipinfo(inputs: Dict[str, Any], api_key: str = "") -> List[Dict]:
    """Geolocate and identify the ASN/ISP behind the target's email domain."""
    domain = _extract_domain(inputs)
    if not domain:
        return []

    loop = asyncio.get_event_loop()
    ip = await loop.run_in_executor(None, _resolve, domain)
    if not ip:
        return []

    url = f"https://ipinfo.io/{ip}/json"
    params = {"token": api_key} if api_key else {}

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
            resp = await client.get(url, params=params)

        if resp.status_code == 429:
            return []  # rate limited — skip silently
        if resp.status_code != 200:
            return []

        data = resp.json()
        if "bogon" in data:
            return []  # private/reserved IP — nothing useful

        return [{
            "source": "ipinfo",
            "type": "ip_geolocation",
            "data": {
                "domain": domain,
                "ip": ip,
                "hostname": data.get("hostname"),
                "city": data.get("city"),
                "region": data.get("region"),
                "country": data.get("country"),
                "org": data.get("org"),        # "ASnnnn ISP Name"
                "timezone": data.get("timezone"),
                "loc": data.get("loc"),        # "lat,lon"
            },
            "confidence": 0.8,
            "url": f"https://ipinfo.io/{ip}",
        }]

    except Exception:
        return []
