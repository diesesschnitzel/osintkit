"""WHOIS domain registration lookup via python-whois."""

import asyncio
from datetime import datetime
from typing import Any, Dict, List

from osintkit.modules import MissingToolError


def _extract_domain(inputs: Dict[str, Any]) -> str | None:
    email = inputs.get("email", "")
    if email and "@" in email:
        return email.split("@")[1].lower()
    username = inputs.get("username", "")
    if username and "." in username:
        return username.lower()
    return None


def _fmt_date(val) -> str | None:
    if val is None:
        return None
    if isinstance(val, list):
        val = val[0]
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d")
    return str(val)


async def run_whois(inputs: Dict[str, Any]) -> List[Dict]:
    """Look up WHOIS registration data for the target's email domain."""
    domain = _extract_domain(inputs)
    if not domain:
        return []

    try:
        import whois  # type: ignore
    except ImportError:
        raise MissingToolError("python-whois not installed. Install with: pip install python-whois")

    try:
        loop = asyncio.get_event_loop()
        w = await loop.run_in_executor(None, whois.whois, domain)

        if not w or not w.get("domain_name"):
            return []

        return [{
            "source": "whois",
            "type": "domain_registration",
            "data": {
                "domain": domain,
                "registrar": w.get("registrar"),
                "creation_date": _fmt_date(w.get("creation_date")),
                "expiration_date": _fmt_date(w.get("expiration_date")),
                "updated_date": _fmt_date(w.get("updated_date")),
                "name_servers": w.get("name_servers"),
                "status": w.get("status"),
                "country": w.get("country"),
                "org": w.get("org"),
                "dnssec": w.get("dnssec"),
            },
            "confidence": 0.9,
            "url": f"https://who.is/whois/{domain}",
        }]

    except MissingToolError:
        raise
    except Exception:
        return []
