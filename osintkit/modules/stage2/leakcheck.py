"""LeakCheck.io email breach lookup (Stage 2 — requires API key)."""

from typing import Dict, List

import httpx


async def run(inputs: dict, api_key: str) -> List[Dict]:
    """Query LeakCheck.io for email breach records.

    Args:
        inputs: dict with at least 'email' key
        api_key: LeakCheck API key

    Returns:
        List of breach finding dicts or [] on no results.

    Raises:
        Exception: on rate limiting (429) or invalid key (401/403).
    """
    email = inputs.get("email")
    if not email:
        return []

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
            response = await client.get(
                "https://leakcheck.io/api/public",
                params={"key": api_key, "check": email},
            )

        if response.status_code == 429:
            raise Exception("429 rate limited")
        if response.status_code in (401, 403):
            raise Exception("401 invalid key")

        data = response.json()
        if not data.get("success") or not data.get("result"):
            return []

        findings = []
        for record in data["result"]:
            findings.append({
                "source": "leakcheck",
                "type": "breach_record",
                "data": {
                    "source_name": record.get("source", {}).get("name", "unknown"),
                    "fields": record.get("fields", []),
                    "email": email,
                },
                "url": None,
            })
        return findings

    except Exception as e:
        if "429" in str(e) or "401" in str(e):
            raise
        return []
