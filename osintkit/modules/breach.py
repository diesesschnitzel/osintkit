"""Breach exposure check via multiple sources."""

import httpx
from typing import Any, Dict, List

from osintkit.config import APIKeys
from osintkit.modules import ModuleError


async def run_breach_exposure(inputs: Dict[str, Any], api_keys: APIKeys) -> List[Dict]:
    """Check breach exposure with fallback chain: HIBP -> BreachDirectory -> LeakCheck."""
    email = inputs.get("email")
    if not email:
        return []

    if api_keys.hibp:
        try:
            return await _check_hibp(email, api_keys.hibp)
        except ModuleError:
            pass

    if api_keys.breachdirectory:
        try:
            return await _check_breachdirectory(email, api_keys.breachdirectory)
        except ModuleError:
            pass

    if api_keys.leakcheck:
        try:
            return await _check_leakcheck(email, api_keys.leakcheck)
        except ModuleError:
            pass

    return []


async def _check_hibp(email: str, api_key: str) -> List[Dict]:
    url = f"https://haveibeenpwned.com/api/v3/breaches?email={email}"
    headers = {"hibp-api-key": api_key, "user-agent": "osintkit-CLI"}
    resp = await httpx.AsyncClient(timeout=30, headers=headers).get(url)
    if resp.status_code == 404:
        return []
    if resp.status_code != 200:
        raise ModuleError(f"HIBP error: {resp.status_code}")
    findings = []
    for b in resp.json():
        findings.append({"source": "hibp", "type": "breach",
            "data": {"breach": b.get("Name"), "domain": b.get("Domain"),
                "date": b.get("BreachDate"), "classes": b.get("DataClasses", [])},
            "confidence": 0.95, "url": f"https://haveibeenpwned.com/breach/{b.get('Name')}"})
    return findings


async def _check_breachdirectory(email: str, api_key: str) -> List[Dict]:
    # Updated endpoint: RapidAPI listing removed; now using breachdirectory.com (Logoutify)
    url = "https://breachdirectory.com/api/"
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await httpx.AsyncClient(timeout=30, headers=headers).get(url, params={"func": "auto", "term": email})
    if resp.status_code != 200:
        raise ModuleError(f"BreachDirectory error: {resp.status_code}")
    findings = []
    for b in resp.json().get("result", []):
        findings.append({"source": "breachdirectory", "type": "breach",
            "data": {"breach": b.get("breach"), "fields": b.get("fields", [])},
            "confidence": 0.85, "url": None})
    return findings


async def _check_leakcheck(email: str, api_key: str) -> List[Dict]:
    url = f"https://leakcheck.io/api/public?check={email}"
    headers = {"X-API-Key": api_key}
    resp = await httpx.AsyncClient(timeout=30, headers=headers).get(url)
    if resp.status_code != 200:
        raise ModuleError(f"LeakCheck error: {resp.status_code}")
    data = resp.json()
    if not data.get("found"):
        return []
    findings = []
    for s in data.get("sources", []):
        findings.append({"source": "leakcheck", "type": "breach",
            "data": {"breach": s.get("name"), "date": s.get("date")},
            "confidence": 0.80, "url": None})
    return findings
