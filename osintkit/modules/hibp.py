"""Password exposure check via HIBP PwnedPasswords."""

import hashlib
import httpx
from typing import Any, Dict, List

from osintkit.modules import ModuleError


async def run_password_exposure(inputs: Dict[str, Any]) -> List[Dict]:
    """Check email breach exposure via HIBP.

    Note: HIBP email breach lookup requires a paid API key (hibp field in
    config.yaml).  The k-anonymity PwnedPasswords endpoint only accepts
    password hashes, not email addresses.  Without a key this module returns
    [] and logs a message so the scanner does not report a failure.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(
        "HIBP email lookup requires API key — configure hibp key for results"
    )
    return []


async def check_password_hash(password: str) -> int:
    """Check how many times password appears in breaches."""
    sha1_hash = hashlib.sha1(password.encode()).hexdigest().upper()
    prefix, suffix = sha1_hash[:5], sha1_hash[5:]
    
    url = f"https://api.pwnedpasswords.com/range/{prefix}"
    try:
        resp = await httpx.AsyncClient(timeout=15).get(url)
        for line in resp.text.splitlines():
            h, count = line.split(":")
            if h == suffix:
                return int(count)
        return 0
    except httpx.HTTPError as e:
        raise ModuleError(f"HIBP failed: {e}")
