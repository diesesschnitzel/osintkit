"""Paste site search via Intelbase or psbdmp."""

import httpx
from typing import Any, Dict, List

from osintkit.config import APIKeys
from osintkit.modules import ModuleError


async def run_paste_sites(inputs: Dict[str, Any], api_keys: APIKeys) -> List[Dict]:
    """Search paste sites with fallback: Intelbase -> psbdmp.ws."""
    email = inputs.get("email")
    if not email:
        return []

    if api_keys.intelbase:
        try:
            return await _search_intelbase_paste(email, api_keys.intelbase)
        except ModuleError:
            pass

    try:
        return await _search_psbdmp(email)
    except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError,
            httpx.RemoteProtocolError, Exception):
        return []


async def _search_intelbase_paste(email: str, api_key: str) -> List[Dict]:
    url = "https://api.intelbase.is/v1/paste/search"
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await httpx.AsyncClient(timeout=60, headers=headers).post(url, json={"query": email})
    if resp.status_code != 200:
        raise ModuleError(f"Intelbase error: {resp.status_code}")
    findings = []
    for r in resp.json().get("results", []):
        findings.append({"source": "intelbase", "type": "paste",
            "data": {"paste_id": r.get("id"), "site": r.get("site"), "date": r.get("date")},
            "confidence": 0.75, "url": r.get("url")})
    return findings


async def _search_psbdmp(email: str) -> List[Dict]:
    url = f"https://psbdmp.ws/api/v3/search/{email}"
    resp = await httpx.AsyncClient(timeout=30).get(url)
    if resp.status_code == 404:
        return []
    if resp.status_code != 200:
        raise ModuleError(f"psbdmp error: {resp.status_code}")
    findings = []
    for p in resp.json().get("data", []):
        findings.append({"source": "psbdmp", "type": "paste",
            "data": {"paste_id": p.get("id"), "date": p.get("date")},
            "confidence": 0.65, "url": f"https://psbdmp.ws/{p.get('id')}"})
    return findings
