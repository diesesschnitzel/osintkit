"""Shodan InternetDB — open ports, CVEs, tags for an IP (Stage 1, no key needed).

Free, no account required.
Docs: https://internetdb.shodan.io/
"""

import asyncio
import socket
from typing import Any, Dict, List

import httpx

from osintkit.modules import MissingToolError


def _extract_domain(inputs: Dict[str, Any]) -> str | None:
    email = inputs.get("email", "")
    if email and "@" in email:
        return email.split("@")[1].lower()
    return None


def _resolve(domain: str) -> str | None:
    try:
        return socket.gethostbyname(domain)
    except Exception:
        return None


async def run_shodan_internetdb(inputs: Dict[str, Any]) -> List[Dict]:
    """Look up open ports and CVEs for the IP of the target's email domain."""
    domain = _extract_domain(inputs)
    if not domain:
        return []

    loop = asyncio.get_event_loop()
    ip = await loop.run_in_executor(None, _resolve, domain)
    if not ip:
        return []

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
            resp = await client.get(f"https://internetdb.shodan.io/{ip}")

        if resp.status_code == 404:
            # No data for this IP — not an error
            return []
        if resp.status_code != 200:
            return []

        data = resp.json()
        ports = data.get("ports", [])
        vulns = data.get("vulns", [])
        cpes = data.get("cpes", [])
        hostnames = data.get("hostnames", [])
        tags = data.get("tags", [])

        return [{
            "source": "shodan_internetdb",
            "type": "ip_scan",
            "data": {
                "domain": domain,
                "ip": ip,
                "open_ports": ports,
                "vulnerabilities": vulns,
                "cpes": cpes,
                "hostnames": hostnames,
                "tags": tags,
            },
            "confidence": 0.85,
            "url": f"https://www.shodan.io/host/{ip}",
        }]

    except Exception:
        return []
