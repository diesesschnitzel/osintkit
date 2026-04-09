"""HIBP k-anonymity password exposure check using SHA1 prefix API."""

import hashlib
import logging
from typing import Any, Dict, List

import httpx

logger = logging.getLogger(__name__)


async def run_hibp_kanon(inputs: Dict[str, Any]) -> List[Dict]:
    """Check HIBP pwnedpasswords k-anonymity endpoint.

    Demonstrates the SHA1 prefix pattern: hashes the email address as a proxy
    value and queries the first 5 characters of the SHA1 against the pwnedpasswords
    range endpoint. This does NOT check actual passwords — it checks whether the
    email's SHA1 hash happens to appear in the leaked password corpus (non-standard
    but illustrates the k-anonymity pattern without exposing the full hash).

    Returns count if a matching suffix is found in the range response.
    """
    email = inputs.get("email")
    if not email:
        return []

    try:
        sha1 = hashlib.sha1(email.strip().lower().encode()).hexdigest().upper()
        prefix = sha1[:5]
        suffix = sha1[5:]

        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
            response = await client.get(
                f"https://api.pwnedpasswords.com/range/{prefix}",
                headers={"Add-Padding": "true"},
            )

        if response.status_code != 200:
            return []

        count = 0
        for line in response.text.splitlines():
            parts = line.strip().split(":")
            if len(parts) == 2 and parts[0].upper() == suffix:
                try:
                    count = int(parts[1])
                except ValueError:
                    pass
                break

        if count == 0:
            return []

        logger.info(f"hibp_kanon: email SHA1 prefix {prefix} found {count} times in pwned passwords")
        return [{
            "source": "hibp_kanon",
            "type": "password_exposure",
            "data": {
                "hash_prefix": prefix,
                "count": count,
                "note": "Email SHA1 hash matched in pwnedpasswords range (non-standard pattern)",
            },
        }]

    except Exception:
        return []
