"""Wayback Machine CDX API lookup for email domain and username."""

from typing import Any, Dict, List

import httpx


async def run_wayback(inputs: Dict[str, Any]) -> List[Dict]:
    """Query the Wayback CDX API for archived URLs related to target inputs.

    Checks the email domain and any handles/usernames found in inputs.
    Returns a list of archived URL findings.
    """
    targets = []

    email = inputs.get("email")
    if email and "@" in email:
        domain = email.split("@", 1)[1].strip()
        if domain:
            targets.append(domain)

    username = inputs.get("username")
    if username:
        targets.append(username)

    if not targets:
        return []

    findings = []

    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
        for target in targets:
            try:
                params = {
                    "url": f"*.{target}",
                    "output": "json",
                    "limit": "5",
                    "fl": "original,timestamp",
                }
                response = await client.get(
                    "http://web.archive.org/cdx/search/cdx",
                    params=params,
                )

                if response.status_code != 200:
                    continue

                rows = response.json()
                # First row is header when output=json
                if not rows or len(rows) < 2:
                    continue

                for row in rows[1:]:
                    if len(row) >= 2:
                        archived_url, timestamp = row[0], row[1]
                        findings.append({
                            "source": "wayback",
                            "type": "web_archive",
                            "data": {
                                "url": archived_url,
                                "timestamp": timestamp,
                                "target": target,
                            },
                            "url": f"https://web.archive.org/web/{timestamp}/{archived_url}",
                        })

            except Exception:
                continue

    return findings
