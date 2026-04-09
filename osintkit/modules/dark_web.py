"""Dark web search via Intelbase or Ahmia."""

import httpx
from typing import Any, Dict, List

from osintkit.config import APIKeys
from osintkit.modules import ModuleError


async def run_dark_web(inputs: Dict[str, Any], api_keys: APIKeys) -> List[Dict]:
    """Search dark web with fallback: Intelbase -> Ahmia."""
    query = inputs.get("email") or inputs.get("username") or inputs.get("name")
    if not query:
        return []

    if api_keys.intelbase:
        try:
            return await _search_intelbase(query, api_keys.intelbase)
        except ModuleError:
            pass

    try:
        return await _search_ahmia(query)
    except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError,
            httpx.RemoteProtocolError, Exception):
        return []


async def _search_intelbase(query: str, api_key: str) -> List[Dict]:
    url = "https://api.intelbase.is/v1/darkweb/search"
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await httpx.AsyncClient(timeout=60, headers=headers).post(url, json={"query": query})
    if resp.status_code != 200:
        raise ModuleError(f"Intelbase error: {resp.status_code}")
    findings = []
    for r in resp.json().get("results", []):
        findings.append({"source": "intelbase", "type": "dark_web",
            "data": {"title": r.get("title"), "url": r.get("url"), "snippet": r.get("snippet")},
            "confidence": 0.7, "url": r.get("url")})
    return findings


async def _search_ahmia(query: str) -> List[Dict]:
    url = f"https://ahmia.fi/search/?q={query}"
    resp = await httpx.AsyncClient(timeout=30).get(url)
    if resp.status_code != 200:
        raise ModuleError(f"Ahmia error: {resp.status_code}")
    # Ahmia returns HTML - return query info
    return [{"source": "ahmia", "type": "dark_web_search",
        "data": {"query": query, "search_url": url, "note": "Manual review recommended"},
        "confidence": 0.5, "url": url}]
