"""Phone validation via NumVerify."""

import httpx
from typing import Any, Dict, List

from osintkit.config import APIKeys
from osintkit.modules import ModuleError


async def run_phone(inputs: Dict[str, Any], api_keys: APIKeys) -> List[Dict]:
    """Validate phone number using NumVerify (requires key)."""
    phone = inputs.get("phone")
    if not phone or not api_keys.numverify:
        return []
    
    clean = phone.lstrip("+").replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    url = "https://apilayer.net/api/validate"
    
    resp = await httpx.AsyncClient(timeout=30).get(url,
        params={"access_key": api_keys.numverify, "number": clean, "format": 1})
    
    if resp.status_code != 200:
        raise ModuleError(f"NumVerify error: {resp.status_code}")
    
    data = resp.json()
    if not data.get("valid"):
        return []
    
    return [{"source": "numverify", "type": "phone_info",
        "data": {"number": phone, "country": data.get("country_name"),
            "carrier": data.get("carrier"), "line_type": data.get("line_type")},
        "confidence": 0.9, "url": None}]
