"""Unit tests for Scanner error classification."""

import asyncio
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
import pytest

from osintkit.modules import RateLimitError, InvalidKeyError, MissingToolError, ModuleError
from osintkit.scanner import Scanner


def _make_scanner():
    """Return a Scanner with fully mocked dependencies."""
    config = MagicMock()
    config.api_keys = MagicMock(
        leakcheck=None, hunter=None, numverify=None, securitytrails=None, github=None,
        model_dump=MagicMock(return_value={})
    )
    config.timeout_seconds = 10
    console = MagicMock()
    scanner = Scanner(config, Path("/tmp"), console)
    return scanner


def _run_with_single_module(scanner, raiser):
    """Replace scanner.modules with one module that calls raiser, then run."""
    async def mock_func(inputs):
        return raiser()

    scanner.modules = [("test_module", mock_func, "Test module")]
    return scanner.run({"username": "testuser"})


def test_missing_tool_classified_as_not_installed():
    scanner = _make_scanner()
    findings = _run_with_single_module(
        scanner,
        lambda: (_ for _ in ()).throw(MissingToolError("Tool not installed. Install with: pip install tool"))
    )
    assert findings["modules"]["test_module"]["status"] == "not_installed"
    assert findings["findings"]["test_module"] == []


def test_rate_limit_classified_correctly():
    scanner = _make_scanner()
    findings = _run_with_single_module(
        scanner,
        lambda: (_ for _ in ()).throw(RateLimitError("429 Too Many Requests"))
    )
    assert findings["modules"]["test_module"]["status"] == "rate_limited"


def test_invalid_key_classified_correctly():
    scanner = _make_scanner()
    findings = _run_with_single_module(
        scanner,
        lambda: (_ for _ in ()).throw(InvalidKeyError("401 Unauthorized"))
    )
    assert findings["modules"]["test_module"]["status"] == "invalid_key"


def test_generic_exception_classified_as_failed():
    scanner = _make_scanner()
    findings = _run_with_single_module(
        scanner,
        lambda: (_ for _ in ()).throw(RuntimeError("unexpected crash"))
    )
    assert findings["modules"]["test_module"]["status"] == "failed"


def test_successful_module_returns_results():
    scanner = _make_scanner()

    async def mock_func(inputs):
        return [{"source": "test", "type": "profile", "data": {}, "url": None}]

    scanner.modules = [("test_module", mock_func, "Test module")]
    findings = scanner.run({"username": "testuser"})

    assert findings["modules"]["test_module"]["status"] == "done"
    assert findings["modules"]["test_module"]["count"] == 1
    assert len(findings["findings"]["test_module"]) == 1


def test_missing_tool_error_message_preserved():
    scanner = _make_scanner()
    msg = "Holehe not installed. Install with: pip install holehe"
    findings = _run_with_single_module(
        scanner,
        lambda: (_ for _ in ()).throw(MissingToolError(msg))
    )
    assert findings["modules"]["test_module"]["error"] == msg
