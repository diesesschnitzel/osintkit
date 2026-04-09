"""Hunter.io email verifier (Stage 2 — requires API key)."""

from typing import Dict, List

import httpx


async def run(inputs: dict, api_key: str) -> List[Dict]:
    """Verify an email address via Hunter.io email-verifier endpoint.

    Args:
        inputs: dict with at least 'email' key
        api_key: Hunter.io API key

    Returns:
        List with a single email verification finding or [] on no result.

    Raises:
        Exception: on rate limiting (429) or invalid key (401/403).
    """
    email = inputs.get("email")
    if not email:
        return []

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
            response = await client.get(
                "https://api.hunter.io/v2/email-verifier",
                params={"email": email, "api_key": api_key},
            )

        if response.status_code == 429:
            raise Exception("429 rate limited")
        if response.status_code in (401, 403):
            raise Exception("401 invalid key")

        data = response.json()
        result = data.get("data", {})
        if not result:
            return []

        return [{
            "source": "hunter",
            "type": "email_verification",
            "data": {
                "status": result.get("status"),
                "score": result.get("score"),
                "regexp": result.get("regexp"),
                "gibberish": result.get("gibberish"),
                "disposable": result.get("disposable"),
                "webmail": result.get("webmail"),
                "mx_records": result.get("mx_records"),
                "smtp_server": result.get("smtp_server"),
                "smtp_check": result.get("smtp_check"),
                "accept_all": result.get("accept_all"),
                "email": email,
            },
            "url": None,
        }]

    except Exception as e:
        if "429" in str(e) or "401" in str(e):
            raise
        return []
