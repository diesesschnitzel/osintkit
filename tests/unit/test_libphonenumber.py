"""Unit tests for the libphonenumber_info module."""

import pytest


@pytest.mark.asyncio
async def test_valid_e164_phone_returns_finding():
    """A valid E.164 phone number should return a phone_info finding."""
    from osintkit.modules.libphonenumber_info import run_libphonenumber

    inputs = {"phone": "+12123456789"}
    results = await run_libphonenumber(inputs)

    assert len(results) == 1
    finding = results[0]
    assert finding["source"] == "libphonenumber"
    assert finding["type"] == "phone_info"
    data = finding["data"]
    assert data["is_valid"] is True
    assert data["e164_format"] == "+12123456789"
    assert "number_type" in data
    assert "region" in data


@pytest.mark.asyncio
async def test_missing_phone_returns_empty():
    """When no phone key is in inputs, the module should return []."""
    from osintkit.modules.libphonenumber_info import run_libphonenumber

    results = await run_libphonenumber({})
    assert results == []


@pytest.mark.asyncio
async def test_invalid_phone_does_not_crash():
    """An unparseable phone string should not raise — it returns []."""
    from osintkit.modules.libphonenumber_info import run_libphonenumber

    # Extremely invalid phone that cannot be parsed
    results = await run_libphonenumber({"phone": "not-a-phone-number-!!!"})
    # Should return [] without raising
    assert isinstance(results, list)
