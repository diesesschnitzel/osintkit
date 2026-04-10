"""NumVerify phone validation (Stage 2 — requires API key)."""

from typing import Dict, List

import httpx

from osintkit.modules import RateLimitError, InvalidKeyError


async def run(inputs: dict, api_key: str) -> List[Dict]:
    """Validate a phone number via the NumVerify/apilayer API.

    Args:
        inputs: dict with at least 'phone' key
        api_key: NumVerify/apilayer access key

    Returns:
        List with a single phone validation finding or [] on no result.

    Raises:
        Exception: on rate limiting (429) or invalid key (401/403).
    """
    phone = inputs.get("phone")
    if not phone:
        return []

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
            response = await client.get(
                "https://apilayer.net/api/validate",
                params={"access_key": api_key, "number": phone},
            )

        if response.status_code == 429:
            raise RateLimitError("NumVerify rate limit reached")
        if response.status_code in (401, 403):
            raise InvalidKeyError("NumVerify API key invalid or unauthorized")

        data = response.json()
        if not data.get("valid") and data.get("error"):
            return []

        return [{
            "source": "numverify",
            "type": "phone_validation",
            "data": {
                "valid": data.get("valid"),
                "number": data.get("number"),
                "local_format": data.get("local_format"),
                "international_format": data.get("international_format"),
                "country_prefix": data.get("country_prefix"),
                "country_code": data.get("country_code"),
                "country_name": data.get("country_name"),
                "location": data.get("location"),
                "carrier": data.get("carrier"),
                "line_type": data.get("line_type"),
            },
            "url": None,
        }]

    except (RateLimitError, InvalidKeyError):
        raise
    except Exception:
        return []
