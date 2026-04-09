"""Certificate transparency check via crt.sh."""

import httpx
from typing import Any, Dict, List

from osintkit.modules import ModuleError

COMMON_DOMAINS = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com"]


async def run_cert_transparency(inputs: Dict[str, Any]) -> List[Dict]:
    """Query certificate transparency logs via crt.sh."""
    email = inputs.get("email")
    if not email or "@" not in email:
        return []
    
    domain = email.split("@")[1]
    if domain in COMMON_DOMAINS:
        return []

    url = f"https://crt.sh/?q={domain}&output=json"
    try:
        resp = await httpx.AsyncClient(timeout=30).get(url)
        if resp.status_code == 404:
            return []
        if resp.status_code != 200:
            raise ModuleError(f"crt.sh error: {resp.status_code}")

        certs = resp.json()
        findings = []
        seen = set()
        for cert in certs:
            for name in cert.get("name_value", "").split("\n"):
                name = name.strip()
                if name and name not in seen:
                    seen.add(name)
                    findings.append({"source": "crtsh", "type": "ssl_cert",
                        "data": {"domain": name, "issuer": cert.get("issuer_name")},
                        "confidence": 0.8, "url": f"https://crt.sh/?q={name}"})
        return findings
    except httpx.HTTPError as e:
        raise ModuleError(f"crt.sh failed: {e}")
