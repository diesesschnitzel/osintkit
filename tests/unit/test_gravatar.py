"""Unit tests for the gravatar module."""

import json
import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock


FAKE_GRAVATAR_RESPONSE = {
    "entry": [
        {
            "displayName": "Test User",
            "name": {"formatted": "Test User"},
            "profileUrl": "https://www.gravatar.com/testprofile",
        }
    ]
}


@pytest.mark.asyncio
async def test_gravatar_returns_finding_on_200():
    """When Gravatar returns 200, the module should return an email_profile finding."""
    inputs = {"email": "test@example.com"}

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = FAKE_GRAVATAR_RESPONSE

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient", return_value=mock_client):
        from osintkit.modules.gravatar import run_gravatar
        results = await run_gravatar(inputs)

    assert len(results) == 1
    assert results[0]["type"] == "email_profile"
    assert results[0]["source"] == "gravatar"
    assert "display_name" in results[0]["data"]


@pytest.mark.asyncio
async def test_gravatar_returns_empty_on_404():
    """When Gravatar returns 404, the module should return an empty list."""
    inputs = {"email": "nobody@example.com"}

    mock_response = MagicMock()
    mock_response.status_code = 404

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient", return_value=mock_client):
        from osintkit.modules.gravatar import run_gravatar
        results = await run_gravatar(inputs)

    assert results == []


@pytest.mark.asyncio
async def test_gravatar_returns_empty_without_email():
    """When no email is provided, the module should return an empty list immediately."""
    from osintkit.modules.gravatar import run_gravatar
    results = await run_gravatar({})
    assert results == []
