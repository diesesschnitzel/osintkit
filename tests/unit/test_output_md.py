"""Unit tests for the markdown output writer."""

import pytest
from pathlib import Path


FIXTURE_FINDINGS = {
    "scan_date": "2026-04-09T12:00:00",
    "inputs": {
        "name": "Test User",
        "email": "test@example.com",
        "username": "testuser",
        "phone": "+15555550100",
    },
    "modules": {
        "gravatar": {"status": "done", "count": 1},
        "sherlock": {"status": "done", "count": 2},
        "hibp_kanon": {"status": "failed", "error": "timeout"},
    },
    "findings": {
        "gravatar": [
            {
                "source": "gravatar",
                "type": "email_profile",
                "data": {"display_name": "Test User", "hash": "abc123"},
                "url": "https://www.gravatar.com/abc123",
            }
        ],
        "sherlock": [
            {
                "source": "sherlock",
                "type": "social_profile",
                "data": {"platform": "GitHub", "username": "testuser"},
                "url": "https://github.com/testuser",
            },
            {
                "source": "sherlock",
                "type": "social_profile",
                "data": {"platform": "Twitter", "username": "testuser"},
                "url": "https://twitter.com/testuser",
            },
        ],
        "hibp_kanon": [],
    },
    "risk_score": 42,
}


def test_write_md_creates_file(tmp_path):
    """write_md should create a findings.md file in the output directory."""
    from osintkit.output.md_writer import write_md

    result_path = write_md(FIXTURE_FINDINGS, tmp_path)

    assert result_path.exists()
    assert result_path.name == "findings.md"


def test_write_md_contains_risk_score(tmp_path):
    """The generated markdown should contain the risk score."""
    from osintkit.output.md_writer import write_md

    result_path = write_md(FIXTURE_FINDINGS, tmp_path)
    content = result_path.read_text()

    assert "Risk Score" in content
    assert "42" in content


def test_write_md_contains_module_names(tmp_path):
    """The generated markdown should include each module name."""
    from osintkit.output.md_writer import write_md

    result_path = write_md(FIXTURE_FINDINGS, tmp_path)
    content = result_path.read_text()

    assert "gravatar" in content
    assert "sherlock" in content


def test_write_md_contains_finding_details(tmp_path):
    """Findings data should appear in the markdown output."""
    from osintkit.output.md_writer import write_md

    result_path = write_md(FIXTURE_FINDINGS, tmp_path)
    content = result_path.read_text()

    assert "email_profile" in content
    assert "social_profile" in content
    assert "https://github.com/testuser" in content
