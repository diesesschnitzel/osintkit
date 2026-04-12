"""ThreatFox (abuse.ch) — IOC lookup for malware C2, threat tags (Stage 1, no key).

Free, no account required.
Docs: https://threatfox.abuse.ch/api/
"""

from typing import Any, Dict, List

import httpx


def _extract_domain(inputs: Dict[str, Any]) -> str | None:
    email = inputs.get("email", "")
    if email and "@" in email:
        return email.split("@")[1].lower()
    return None


async def run_threatfox(inputs: Dict[str, Any]) -> List[Dict]:
    """Search ThreatFox IOC database for the target's email domain."""
    domain = _extract_domain(inputs)
    if not domain:
        return []

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
            resp = await client.post(
                "https://threatfox-api.abuse.ch/api/v1/",
                json={"query": "search_ioc", "search_term": domain},
                headers={"Content-Type": "application/json"},
            )

        if resp.status_code != 200:
            return []

        result = resp.json()
        if result.get("query_status") != "ok":
            return []

        iocs = result.get("data", []) or []
        if not iocs:
            return []

        findings = []
        for ioc in iocs[:10]:
            findings.append({
                "source": "threatfox",
                "type": "threat_ioc",
                "data": {
                    "domain": domain,
                    "ioc_id": ioc.get("id"),
                    "ioc_value": ioc.get("ioc"),
                    "ioc_type": ioc.get("ioc_type"),
                    "threat_type": ioc.get("threat_type"),
                    "malware": ioc.get("malware_printable"),
                    "confidence": ioc.get("confidence_level"),
                    "first_seen": ioc.get("first_seen"),
                    "last_seen": ioc.get("last_seen"),
                    "tags": ioc.get("tags") or [],
                },
                "confidence": (ioc.get("confidence_level", 0) or 0) / 100,
                "url": f"https://threatfox.abuse.ch/ioc/{ioc.get('id', '')}",
            })

        return findings

    except Exception:
        return []
