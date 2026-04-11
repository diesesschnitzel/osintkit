"""Epieos email OSINT — Google/Apple account lookup (Stage 2 — requires API key).

Free tier available.
Get a key at: https://epieos.com
"""

from typing import Dict, List

import httpx

from osintkit.modules import RateLimitError, InvalidKeyError


async def run(inputs: dict, api_key: str) -> List[Dict]:
    """Look up Google/Apple account details tied to an email via Epieos."""
    email = inputs.get("email")
    if not email:
        return []

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0, connect=5.0)) as client:
            resp = await client.get(
                "https://epieos.com/api/social",
                params={"email": email},
                headers={"Authorization": f"Token {api_key}"},
            )

        if resp.status_code == 429:
            raise RateLimitError("Epieos rate limit reached")
        if resp.status_code in (401, 403):
            raise InvalidKeyError("Epieos API key invalid")
        if resp.status_code != 200:
            return []

        data = resp.json()
        if not data:
            return []

        google = data.get("google", {})
        apple = data.get("apple", {})
        findings = []

        if google:
            findings.append({
                "source": "epieos",
                "type": "google_account",
                "data": {
                    "email": email,
                    "google_id": google.get("id"),
                    "name": google.get("name"),
                    "photo": google.get("photo"),
                    "last_seen": google.get("last_seen"),
                    "reviews": google.get("reviews"),
                    "photos": google.get("photos"),
                    "calendar_public": google.get("calendar"),
                },
                "confidence": 0.9,
                "url": f"https://epieos.com/?q={email}",
            })

        if apple:
            findings.append({
                "source": "epieos",
                "type": "apple_account",
                "data": {
                    "email": email,
                    "apple_id_exists": bool(apple),
                    "facetime": apple.get("facetime"),
                    "imessage": apple.get("imessage"),
                },
                "confidence": 0.85,
                "url": f"https://epieos.com/?q={email}",
            })

        return findings

    except (RateLimitError, InvalidKeyError):
        raise
    except Exception:
        return []
