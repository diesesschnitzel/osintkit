"""Data broker search via Google CSE or direct HTTP."""

import httpx
from typing import Any, Dict, List

from osintkit.config import APIKeys
from osintkit.modules import ModuleError

BROKER_SITES = ["whitepages.com", "spokeo.com", "instantcheckmate.com",
    "truepeoplesearch.com", "fastpeoplesearch.com", "familytreenow.com"]


async def run_data_brokers(inputs: Dict[str, Any], api_keys: APIKeys) -> List[Dict]:
    """Search data brokers with fallback: Google CSE -> direct HTTP."""
    name = inputs.get("name")
    if not name:
        return []

    if api_keys.google_cse_key and api_keys.google_cse_cx:
        try:
            return await _search_google_cse(name, api_keys.google_cse_key, api_keys.google_cse_cx)
        except ModuleError:
            pass

    return await _search_direct_http(name)


async def _search_google_cse(name: str, api_key: str, cx: str) -> List[Dict]:
    url = "https://www.googleapis.com/customsearch/v1"
    findings = []
    client = httpx.AsyncClient(timeout=30)
    for site in BROKER_SITES[:3]:
        resp = await client.get(url, params={"key": api_key, "cx": cx, "q": f"{name} site:{site}"})
        if resp.status_code == 200:
            for item in resp.json().get("items", []):
                findings.append({"source": "google_cse", "type": "data_broker",
                    "data": {"site": site, "title": item.get("title"), "snippet": item.get("snippet")},
                    "confidence": 0.85, "url": item.get("link")})
    return findings


async def _search_direct_http(name: str) -> List[Dict]:
    slug = name.replace(" ", "-").lower()
    findings = []
    client = httpx.AsyncClient(timeout=15, follow_redirects=True)
    for site in BROKER_SITES:
        url = f"https://{site}/person/{slug}"
        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                findings.append({"source": "direct_http", "type": "data_broker_potential",
                    "data": {"site": site, "name": name, "url": url},
                    "confidence": 0.4, "url": url})
        except httpx.HTTPError:
            pass
    return findings
