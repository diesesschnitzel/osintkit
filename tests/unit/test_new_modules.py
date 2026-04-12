"""Unit tests for modules added in v0.1.6/v0.1.7.

Covers: emailrep, urlscan, whois_lookup, virustotal, otx, abuseipdb, risk.
All HTTP calls are mocked — no real network traffic.
asyncio_mode = auto (set in pyproject.toml), so all async tests run automatically.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _resp(status: int, body: dict):
    r = MagicMock()
    r.status_code = status
    r.json = MagicMock(return_value=body)
    return r


def _mock_http(status: int, body: dict):
    """Context manager helper that patches httpx.AsyncClient."""
    mc = MagicMock()
    mc.__aenter__ = AsyncMock(return_value=mc)
    mc.__aexit__ = AsyncMock(return_value=False)
    mc.get = AsyncMock(return_value=_resp(status, body))
    return patch("httpx.AsyncClient", return_value=mc)


# ── emailrep ─────────────────────────────────────────────────────────────────

class TestEmailrep:
    async def test_returns_finding_on_200(self):
        from osintkit.modules.emailrep import run_emailrep
        body = {"email": "t@e.com", "reputation": "high", "suspicious": False, "references": 1,
                "details": {"blacklisted": False, "malicious_activity": False, "credentials_leaked": False,
                            "spam": False, "disposable": False, "free_provider": True,
                            "profiles": [], "domain_exists": True}}
        with _mock_http(200, body):
            result = await run_emailrep({"email": "t@e.com"})
        assert len(result) == 1
        assert result[0]["type"] == "email_reputation"
        assert result[0]["data"]["reputation"] == "high"

    async def test_returns_empty_without_email(self):
        from osintkit.modules.emailrep import run_emailrep
        assert await run_emailrep({"username": "x"}) == []

    async def test_raises_rate_limit_on_429(self):
        from osintkit.modules.emailrep import run_emailrep
        from osintkit.modules import RateLimitError
        with _mock_http(429, {}):
            with pytest.raises(RateLimitError):
                await run_emailrep({"email": "t@e.com"})

    async def test_raises_invalid_key_on_403(self):
        from osintkit.modules.emailrep import run_emailrep
        from osintkit.modules import InvalidKeyError
        with _mock_http(403, {}):
            with pytest.raises(InvalidKeyError):
                await run_emailrep({"email": "t@e.com"}, api_key="bad")

    async def test_returns_empty_on_server_error(self):
        from osintkit.modules.emailrep import run_emailrep
        with _mock_http(500, {}):
            assert await run_emailrep({"email": "t@e.com"}) == []


# ── urlscan ───────────────────────────────────────────────────────────────────

class TestUrlscan:
    async def test_returns_findings_on_200(self):
        from osintkit.modules.urlscan import run_urlscan
        body = {"results": [{"_id": "abc", "task": {"time": "2024-01-01T00:00:00Z", "url": "https://example.com"},
                              "page": {"country": "US", "server": "nginx", "ip": "1.2.3.4"},
                              "verdicts": {"overall": {"malicious": False, "score": 0, "tags": []}},
                              "screenshot": "https://urlscan.io/ss/abc.png"}]}
        with _mock_http(200, body):
            result = await run_urlscan({"email": "u@example.com"})
        assert len(result) == 1
        assert result[0]["type"] == "domain_scan"
        assert result[0]["data"]["domain"] == "example.com"

    async def test_returns_empty_without_domain(self):
        from osintkit.modules.urlscan import run_urlscan
        assert await run_urlscan({"phone": "123"}) == []

    async def test_returns_empty_on_no_results(self):
        from osintkit.modules.urlscan import run_urlscan
        with _mock_http(200, {"results": []}):
            assert await run_urlscan({"email": "u@example.com"}) == []

    async def test_extracts_domain_from_username(self):
        from osintkit.modules.urlscan import run_urlscan
        with _mock_http(200, {"results": []}):
            result = await run_urlscan({"username": "example.com"})
        assert result == []


# ── whois_lookup ──────────────────────────────────────────────────────────────

class TestWhoisLookup:
    async def test_raises_missing_tool_when_not_installed(self):
        from osintkit.modules.whois_lookup import run_whois
        from osintkit.modules import MissingToolError
        import builtins
        real = builtins.__import__

        def no_whois(name, *a, **kw):
            if name == "whois":
                raise ImportError("No module named 'whois'")
            return real(name, *a, **kw)

        with patch("builtins.__import__", side_effect=no_whois):
            with pytest.raises(MissingToolError):
                await run_whois({"email": "u@example.com"})

    async def test_returns_empty_without_domain(self):
        from osintkit.modules.whois_lookup import run_whois
        assert await run_whois({"phone": "+1234"}) == []

    async def test_returns_finding_with_whois_data(self):
        from osintkit.modules.whois_lookup import run_whois
        from datetime import datetime
        mock_whois = MagicMock()
        mock_whois.whois = MagicMock(return_value={
            "domain_name": "example.com", "registrar": "GoDaddy",
            "creation_date": datetime(2000, 1, 1), "expiration_date": datetime(2030, 1, 1),
            "updated_date": None, "name_servers": ["ns1.example.com"], "status": "active",
            "country": "US", "org": "Example Inc", "dnssec": "unsigned",
        })
        with patch.dict("sys.modules", {"whois": mock_whois}):
            result = await run_whois({"email": "u@example.com"})
        assert len(result) == 1
        assert result[0]["type"] == "domain_registration"
        assert result[0]["data"]["registrar"] == "GoDaddy"


# ── virustotal ────────────────────────────────────────────────────────────────

class TestVirusTotal:
    async def test_returns_domain_reputation(self):
        from osintkit.modules.stage2.virustotal import run
        body = {"data": {"attributes": {
            "last_analysis_stats": {"malicious": 2, "suspicious": 1, "harmless": 65, "undetected": 10},
            "reputation": -5, "categories": {}, "registrar": "Namecheap",
            "creation_date": 1000000, "tags": ["malware"], "total_votes": {},
        }}}
        with _mock_http(200, body):
            result = await run({"email": "u@evil.com"}, "key")
        assert result[0]["type"] == "domain_reputation"
        assert result[0]["data"]["malicious"] == 2

    async def test_returns_empty_without_domain(self):
        from osintkit.modules.stage2.virustotal import run
        assert await run({"phone": "123"}, "key") == []

    async def test_raises_rate_limit_on_429(self):
        from osintkit.modules.stage2.virustotal import run
        from osintkit.modules import RateLimitError
        with _mock_http(429, {}):
            with pytest.raises(RateLimitError):
                await run({"email": "u@x.com"}, "key")

    async def test_raises_invalid_key_on_401(self):
        from osintkit.modules.stage2.virustotal import run
        from osintkit.modules import InvalidKeyError
        with _mock_http(401, {}):
            with pytest.raises(InvalidKeyError):
                await run({"email": "u@x.com"}, "bad")


# ── otx ───────────────────────────────────────────────────────────────────────

class TestOTX:
    async def test_returns_threat_intel(self):
        from osintkit.modules.stage2.otx import run
        body = {"indicator": "example.com",
                "pulse_info": {"count": 3, "pulses": [{"name": "Malware"}], "tags": ["malware"]},
                "whois": "registrar: GoDaddy", "alexa": "1000"}
        with _mock_http(200, body):
            result = await run({"email": "u@example.com"}, "key")
        assert result[0]["type"] == "threat_intel"
        assert result[0]["data"]["pulse_count"] == 3

    async def test_returns_empty_without_domain(self):
        from osintkit.modules.stage2.otx import run
        assert await run({"phone": "123"}, "key") == []

    async def test_raises_rate_limit_on_429(self):
        from osintkit.modules.stage2.otx import run
        from osintkit.modules import RateLimitError
        with _mock_http(429, {}):
            with pytest.raises(RateLimitError):
                await run({"email": "u@x.com"}, "key")


# ── abuseipdb ─────────────────────────────────────────────────────────────────

class TestAbuseIPDB:
    async def test_returns_ip_abuse(self):
        from osintkit.modules.stage2.abuseipdb import run
        body = {"data": {"ipAddress": "1.2.3.4", "abuseConfidenceScore": 75, "countryCode": "CN",
                         "isp": "SomeISP", "domain": "example.com", "totalReports": 12,
                         "numDistinctUsers": 5, "lastReportedAt": "2024-01-01T00:00:00Z",
                         "isTor": False, "usageType": "Data Center"}}
        with patch("osintkit.modules.stage2.abuseipdb._resolve_domain", return_value="1.2.3.4"):
            with _mock_http(200, body):
                result = await run({"email": "u@example.com"}, "key")
        assert result[0]["type"] == "ip_abuse"
        assert result[0]["data"]["abuse_confidence_score"] == 75

    async def test_returns_empty_without_email(self):
        from osintkit.modules.stage2.abuseipdb import run
        assert await run({"username": "x"}, "key") == []

    async def test_returns_empty_when_dns_fails(self):
        from osintkit.modules.stage2.abuseipdb import run
        with patch("osintkit.modules.stage2.abuseipdb._resolve_domain", return_value=None):
            assert await run({"email": "u@example.com"}, "key") == []

    async def test_raises_invalid_key_on_401(self):
        from osintkit.modules.stage2.abuseipdb import run
        from osintkit.modules import InvalidKeyError
        with patch("osintkit.modules.stage2.abuseipdb._resolve_domain", return_value="1.2.3.4"):
            with _mock_http(401, {}):
                with pytest.raises(InvalidKeyError):
                    await run({"email": "u@example.com"}, "bad")


# ── risk score ────────────────────────────────────────────────────────────────

class TestRiskScore:
    def test_virustotal_malicious_adds_score(self):
        from osintkit.risk import calculate_risk_score
        score = calculate_risk_score({"virustotal": [{"data": {"malicious": 5, "suspicious": 0}}]})
        assert score > 0

    def test_abuseipdb_high_confidence(self):
        from osintkit.risk import calculate_risk_score
        assert calculate_risk_score({"abuseipdb": [{"data": {"abuse_confidence_score": 100}}]}) == 20

    def test_abuseipdb_zero_confidence(self):
        from osintkit.risk import calculate_risk_score
        assert calculate_risk_score({"abuseipdb": [{"data": {"abuse_confidence_score": 0}}]}) == 0

    def test_emailrep_blacklisted(self):
        from osintkit.risk import calculate_risk_score
        data = {"blacklisted": True, "malicious_activity": False, "suspicious": False,
                "credentials_leaked": False, "reputation": "low"}
        assert calculate_risk_score({"emailrep": [{"data": data}]}) >= 15

    def test_emailrep_credentials_leaked_stacks(self):
        from osintkit.risk import calculate_risk_score
        data = {"blacklisted": True, "credentials_leaked": True, "malicious_activity": False,
                "suspicious": False, "reputation": "low"}
        score = calculate_risk_score({"emailrep": [{"data": data}]})
        assert score >= 20  # 15 blacklisted + 5 credentials

    def test_urlscan_malicious_verdict(self):
        from osintkit.risk import calculate_risk_score
        findings = {"urlscan": [{"data": {"malicious": True}}, {"data": {"malicious": False}}]}
        assert calculate_risk_score(findings) == 5

    def test_otx_pulse_count(self):
        from osintkit.risk import calculate_risk_score
        assert calculate_risk_score({"otx": [{"data": {"pulse_count": 3}}]}) == 6

    def test_empty_findings_score_zero(self):
        from osintkit.risk import calculate_risk_score
        assert calculate_risk_score({}) == 0

    def test_score_capped_at_100(self):
        from osintkit.risk import calculate_risk_score
        findings = {
            "breach_exposure": [{}] * 20, "social_profiles": [{}] * 20,
            "data_brokers": [{}] * 10, "dark_web": [{}] * 10,
            "virustotal": [{"data": {"malicious": 50, "suspicious": 10}}],
            "abuseipdb": [{"data": {"abuse_confidence_score": 100}}],
            "emailrep": [{"data": {"blacklisted": True, "credentials_leaked": True,
                                   "malicious_activity": True, "suspicious": True,
                                   "malicious_activity_recent": True, "reputation": "none"}}],
        }
        assert calculate_risk_score(findings) == 100
