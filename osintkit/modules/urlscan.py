"""Domain scan history lookup via urlscan.io (no API key required)."""

from typing import Any, Dict, List

import httpx


def _extract_domain(inputs: Dict[str, Any]) -> str | None:
    email = inputs.get("email", "")
    if email and "@" in email:
        return email.split("@")[1].lower()
    username = inputs.get("username", "")
    if username and "." in username:
        return username.lower()
    return None


async def run_urlscan(inputs: Dict[str, Any]) -> List[Dict]:
    """Search urlscan.io for recent scans of the target's domain."""
    domain = _extract_domain(inputs)
    if not domain:
        return []

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0, connect=5.0)) as client:
            resp = await client.get(
                "https://urlscan.io/api/v1/search/",
                params={"q": f"domain:{domain}", "size": "10"},
                headers={"User-Agent": "osintkit/0.1"},
            )

        if resp.status_code != 200:
            return []

        results = resp.json().get("results", [])
        if not results:
            return []

        findings = []
        for item in results[:5]:
            task = item.get("task", {})
            page = item.get("page", {})
            verdicts = item.get("verdicts", {}).get("overall", {})
            findings.append({
                "source": "urlscan",
                "type": "domain_scan",
                "data": {
                    "domain": domain,
                    "scan_date": task.get("time"),
                    "url": task.get("url"),
                    "country": page.get("country"),
                    "server": page.get("server"),
                    "ip": page.get("ip"),
                    "malicious": verdicts.get("malicious"),
                    "score": verdicts.get("score"),
                    "tags": verdicts.get("tags", []),
                    "screenshot": item.get("screenshot"),
                    "report_url": f"https://urlscan.io/result/{item.get('_id', '')}/",
                },
                "confidence": 0.75,
                "url": f"https://urlscan.io/result/{item.get('_id', '')}/",
            })

        return findings

    except Exception:
        return []
