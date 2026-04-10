"""SecurityTrails subdomain enumeration (Stage 2 — requires API key)."""

from typing import Dict, List

import httpx

from osintkit.modules import RateLimitError, InvalidKeyError


async def run(inputs: dict, api_key: str) -> List[Dict]:
    """Enumerate subdomains for the target's email domain via SecurityTrails API.

    Args:
        inputs: dict with at least 'email' key (domain extracted) or 'domain' key
        api_key: SecurityTrails API key

    Returns:
        List of subdomain findings or [] on no results.

    Raises:
        Exception: on rate limiting (429) or invalid key (401/403).
    """
    domain = inputs.get("domain")
    if not domain:
        email = inputs.get("email")
        if email and "@" in email:
            domain = email.split("@", 1)[1].strip()

    if not domain:
        return []

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
            response = await client.get(
                f"https://api.securitytrails.com/v1/domain/{domain}/subdomains",
                headers={"APIKEY": api_key},
            )

        if response.status_code == 429:
            raise RateLimitError("SecurityTrails rate limit reached")
        if response.status_code in (401, 403):
            raise InvalidKeyError("SecurityTrails API key invalid or unauthorized")

        data = response.json()
        subdomains = data.get("subdomains", [])
        if not subdomains:
            return []

        findings = []
        for sub in subdomains:
            full = f"{sub}.{domain}"
            findings.append({
                "source": "securitytrails",
                "type": "subdomain",
                "data": {
                    "subdomain": sub,
                    "domain": domain,
                    "fqdn": full,
                },
                "url": f"https://{full}",
            })
        return findings

    except (RateLimitError, InvalidKeyError):
        raise
    except Exception:
        return []
