"""Security tests: API keys must never appear in output files."""

import pytest
from pathlib import Path


SECRET_KEY = "supersecretkey123"

FAKE_CONFIG_KEYS = {
    "hibp": SECRET_KEY,
}

FAKE_FINDINGS = {
    "scan_date": "2026-04-09T12:00:00",
    "inputs": {
        "name": "Leak Test",
        "email": "leak@example.com",
        "username": "leaktest",
        "phone": None,
    },
    "modules": {
        "hibp": {"status": "done", "count": 1},
    },
    "findings": {
        "hibp": [
            {
                "source": "hibp",
                "type": "breach",
                "data": {
                    "breach": "TestBreach",
                    # Simulate accidental key inclusion in data
                    "debug_key": SECRET_KEY,
                },
                "url": None,
            }
        ],
    },
    "risk_score": 30,
}


def test_md_does_not_contain_api_key(tmp_path):
    """The markdown report must not contain the raw API key value."""
    from osintkit.output.md_writer import write_md

    result_path = write_md(FAKE_FINDINGS, tmp_path, api_keys=FAKE_CONFIG_KEYS)
    content = result_path.read_text()

    assert SECRET_KEY not in content, (
        f"API key '{SECRET_KEY}' was found in the markdown output — scrubbing failed!"
    )
    # The placeholder should be there instead
    assert "[REDACTED]" in content


def test_json_does_not_contain_api_key(tmp_path):
    """The JSON output must not contain the raw API key value."""
    from osintkit.output.json_writer import write_json

    result_path = write_json(FAKE_FINDINGS, tmp_path, api_keys=FAKE_CONFIG_KEYS)
    content = result_path.read_text()

    assert SECRET_KEY not in content, (
        f"API key '{SECRET_KEY}' was found in the JSON output — scrubbing failed!"
    )
    assert "[REDACTED]" in content
