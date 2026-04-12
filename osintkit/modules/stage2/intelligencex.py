"""IntelligenceX — leak/darknet search for email and username (Stage 2, free key).

Free account (50 searches/day) at: https://intelx.io/
The search is async: POST to start, GET to collect results.
"""

import asyncio
from typing import Dict, List

import httpx

from osintkit.modules import RateLimitError, InvalidKeyError

_BASE = "https://2.intelx.io"


async def run(inputs: dict, api_key: str) -> List[Dict]:
    """Search IntelligenceX for the target email and/or username."""
    email = inputs.get("email", "")
    username = inputs.get("username", "")
    term = email or username
    if not term:
        return []

    headers = {"x-key": api_key, "Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(20.0, connect=5.0)) as client:
            # Step 1: start search
            start_resp = await client.post(
                f"{_BASE}/intelligent/search",
                headers=headers,
                json={
                    "term": term,
                    "buckets": [],
                    "lookuplevel": 0,
                    "maxresults": 10,
                    "timeout": 0,
                    "datefrom": "",
                    "dateto": "",
                    "sort": 2,
                    "media": 0,
                    "terminate": [],
                },
            )

        if start_resp.status_code == 402:
            raise RateLimitError("IntelligenceX daily search limit reached (50/day on free plan)")
        if start_resp.status_code in (401, 403):
            raise InvalidKeyError("IntelligenceX API key invalid")
        if start_resp.status_code != 200:
            return []

        search_id = start_resp.json().get("id")
        if not search_id:
            return []

        # Step 2: collect results (poll up to 3 times with short delay)
        results = []
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0, connect=5.0)) as client:
            for _ in range(3):
                await asyncio.sleep(1)
                result_resp = await client.get(
                    f"{_BASE}/intelligent/search/result",
                    headers=headers,
                    params={"id": search_id, "limit": 10, "offset": 0},
                )
                if result_resp.status_code == 200:
                    data = result_resp.json()
                    records = data.get("records") or []
                    if records:
                        results = records
                        break
                    if data.get("status") == 1:  # still running
                        continue
                    break

        if not results:
            return []

        findings = []
        for rec in results[:10]:
            findings.append({
                "source": "intelligencex",
                "type": "leaked_data",
                "data": {
                    "term": term,
                    "name": rec.get("name"),
                    "bucket": rec.get("bucket"),
                    "date": rec.get("date"),
                    "media_type": rec.get("mediat"),
                    "storageid": rec.get("storageid"),
                },
                "confidence": 0.75,
                "url": f"https://intelx.io/?s={term}",
            })

        return findings

    except (RateLimitError, InvalidKeyError):
        raise
    except Exception:
        return []
