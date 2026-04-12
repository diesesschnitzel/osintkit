"""Pulsedive — IOC risk scoring for domains and IPs (Stage 2, free key).

Free registered account (10 req/day):
  https://pulsedive.com/
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
    """Get IOC risk score for the target's email domain via Pulsedive."""
    domain = _extract_domain(inputs)
    if not domain:
        return []

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0, connect=5.0)) as client:
            resp = await client.get(
                "https://pulsedive.com/api/",
                params={
                    "indicator": domain,
                    "pretty": "1",
                    "key": api_key,
                },
            )

        if resp.status_code == 429:
            raise RateLimitError("Pulsedive rate limit reached (10 req/day on free plan)")
        if resp.status_code in (401, 403):
            raise InvalidKeyError("Pulsedive API key invalid")
        if resp.status_code == 404:
            # Indicator not in Pulsedive yet — not an error
            return []
        if resp.status_code != 200:
            return []

        data = resp.json()
        if data.get("error"):
            return []

        risk = data.get("risk", "unknown")
        threats = [t.get("name") for t in (data.get("threats") or [])[:5]]
        feeds = [f.get("name") for f in (data.get("feeds") or [])[:5]]
        attributes = data.get("attributes", {}) or {}

        return [{
            "source": "pulsedive",
            "type": "ioc_risk",
            "data": {
                "domain": domain,
                "risk": risk,           # none / low / medium / high / critical
                "threats": threats,
                "feeds": feeds,
                "retired": data.get("retired", False),
                "stamp_seen": data.get("stamp_seen"),
                "stamp_updated": data.get("stamp_updated"),
                "attributes": {
                    "port": attributes.get("port", []),
                    "protocol": attributes.get("protocol", []),
                    "technology": attributes.get("technology", []),
                },
            },
            "confidence": 0.8,
            "url": f"https://pulsedive.com/indicator/?ioc={domain}",
        }]

    except (RateLimitError, InvalidKeyError):
        raise
    except Exception:
        return []
