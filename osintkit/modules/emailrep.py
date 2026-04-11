"""Email reputation check via emailrep.io.

Works without an API key (strict rate limit). Set the 'emailrep' key in
config for higher limits and richer data.
"""

from typing import Any, Dict, List

import httpx

from osintkit.modules import RateLimitError, InvalidKeyError


async def run_emailrep(inputs: Dict[str, Any], api_key: str = "") -> List[Dict]:
    """Check email reputation via emailrep.io."""
    email = inputs.get("email")
    if not email:
        return []

    headers = {"User-Agent": "osintkit/0.1"}
    if api_key:
        headers["Key"] = api_key

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
            resp = await client.get(f"https://emailrep.io/{email}", headers=headers)

        if resp.status_code == 429:
            raise RateLimitError("emailrep.io rate limit reached")
        if resp.status_code in (401, 403):
            raise InvalidKeyError("emailrep.io API key invalid")
        if resp.status_code != 200:
            return []

        data = resp.json()
        details = data.get("details", {})

        return [{
            "source": "emailrep",
            "type": "email_reputation",
            "data": {
                "email": email,
                "reputation": data.get("reputation"),
                "suspicious": data.get("suspicious"),
                "references": data.get("references", 0),
                "blacklisted": details.get("blacklisted"),
                "malicious_activity": details.get("malicious_activity"),
                "malicious_activity_recent": details.get("malicious_activity_recent"),
                "credentials_leaked": details.get("credentials_leaked"),
                "spam": details.get("spam"),
                "disposable": details.get("disposable"),
                "free_provider": details.get("free_provider"),
                "profiles": details.get("profiles", []),
                "domain_exists": details.get("domain_exists"),
                "days_since_domain_creation": details.get("days_since_domain_creation"),
            },
            "confidence": 0.85,
            "url": f"https://emailrep.io/{email}",
        }]

    except (RateLimitError, InvalidKeyError):
        raise
    except Exception:
        return []
