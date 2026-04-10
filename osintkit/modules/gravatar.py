"""Gravatar profile lookup via MD5 email hash."""

import hashlib
from typing import Any, Dict, List

import httpx


async def run_gravatar(inputs: Dict[str, Any]) -> List[Dict]:
    """Check Gravatar for an email address profile.

    Uses MD5 hash of the email (lowercase, stripped) to query the Gravatar API.
    Returns [] if no email or no profile found.
    """
    email = inputs.get("email")
    if not email:
        return []

    email_normalized = email.strip().lower()
    email_hash = hashlib.md5(email_normalized.encode()).hexdigest()
    url = f"https://www.gravatar.com/{email_hash}.json"

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
            response = await client.get(url)

        if response.status_code != 200:
            return []

        data = response.json()
        entry = data.get("entry", [{}])[0]

        name = entry.get("name", {})
        display_name = entry.get("displayName", "")
        formatted_name = name.get("formatted", "") if isinstance(name, dict) else str(name)
        profile_url = entry.get("profileUrl", f"https://www.gravatar.com/{email_hash}")

        return [{
            "source": "gravatar",
            "type": "email_profile",
            "data": {
                "hash": email_hash,
                "display_name": display_name,
                "formatted_name": formatted_name,
            },
            "url": profile_url,
        }]

    except Exception:
        return []
