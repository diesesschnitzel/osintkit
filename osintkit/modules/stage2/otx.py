"""OTX AlienVault threat intelligence (Stage 2 — requires API key).

Free account at: https://otx.alienvault.com/
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
    """Look up domain threat indicators in OTX AlienVault."""
    domain = _extract_domain(inputs)
    if not domain:
        return []

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0, connect=5.0)) as client:
            resp = await client.get(
                f"https://otx.alienvault.com/api/v1/indicators/domain/{domain}/general",
                headers={"X-OTX-API-KEY": api_key},
            )

        if resp.status_code == 429:
            raise RateLimitError("OTX AlienVault rate limit reached")
        if resp.status_code in (401, 403):
            raise InvalidKeyError("OTX API key invalid")
        if resp.status_code != 200:
            return []

        data = resp.json()
        pulse_info = data.get("pulse_info", {})

        return [{
            "source": "otx",
            "type": "threat_intel",
            "data": {
                "domain": domain,
                "pulse_count": pulse_info.get("count", 0),
                "malware_families": [
                    p.get("name") for p in pulse_info.get("pulses", [])[:5]
                ],
                "tags": pulse_info.get("tags", []),
                "whois": data.get("whois"),
                "alexa": data.get("alexa"),
                "indicator": data.get("indicator"),
            },
            "confidence": 0.8,
            "url": f"https://otx.alienvault.com/indicator/domain/{domain}",
        }]

    except (RateLimitError, InvalidKeyError):
        raise
    except Exception:
        return []
