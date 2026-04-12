"""Netlas.io — internet scan data: ports, CVEs, banners (Stage 2, free key).

Free community account (50 req/day, non-commercial):
  https://app.netlas.io/plans/
"""

from typing import Dict, List

import httpx

from osintkit.modules import RateLimitError, InvalidKeyError


def _extract_domain(inputs: dict) -> str | None:
    email = inputs.get("email", "")
    if email and "@" in email:
        return email.split("@")[1].lower()
    return None


async def run(inputs: dict, api_key: str) -> List[Dict]:
    """Fetch internet scan data for the target's email domain via Netlas."""
    domain = _extract_domain(inputs)
    if not domain:
        return []

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0, connect=5.0)) as client:
            resp = await client.get(
                "https://app.netlas.io/api/responses/",
                params={
                    "q": f"host:{domain}",
                    "source_type": "include",
                    "start": 0,
                    "fields": "*",
                },
                headers={"X-API-Key": api_key},
            )

        if resp.status_code == 429:
            raise RateLimitError("Netlas rate limit reached (50 req/day on free plan)")
        if resp.status_code in (401, 403):
            raise InvalidKeyError("Netlas API key invalid")
        if resp.status_code != 200:
            return []

        items = resp.json().get("items", []) or []
        if not items:
            return []

        findings = []
        for item in items[:5]:
            data_obj = item.get("data", {}) or {}
            port = data_obj.get("port")
            protocol = data_obj.get("protocol")
            http_info = data_obj.get("http", {}) or {}
            cves = data_obj.get("cve", []) or []

            findings.append({
                "source": "netlas",
                "type": "internet_scan",
                "data": {
                    "domain": domain,
                    "ip": data_obj.get("ip"),
                    "port": port,
                    "protocol": protocol,
                    "http_title": (http_info.get("title") or "").strip() or None,
                    "http_status": http_info.get("status_code"),
                    "cves": [c.get("name") for c in cves[:5] if c.get("name")],
                    "tags": data_obj.get("tag", []) or [],
                },
                "confidence": 0.8,
                "url": f"https://app.netlas.io/responses/?q=host:{domain}",
            })

        return findings

    except (RateLimitError, InvalidKeyError):
        raise
    except Exception:
        return []
