"""Unit tests for v0.2.0 modules: shodan_internetdb, threatfox, ipinfo,
greynoise, intelligencex, netlas, pulsedive."""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

INPUTS = {"email": "test@example.com"}
NO_INPUTS = {}


# ── helpers ─────────────────────────────────────────────────────────────────

def _mock_http(status: int, body: dict):
    """Patch httpx.AsyncClient to return a fake response."""
    mock_resp = MagicMock()
    mock_resp.status_code = status
    mock_resp.json.return_value = body

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(return_value=mock_resp)
    mock_client.post = AsyncMock(return_value=mock_resp)

    return patch("httpx.AsyncClient", return_value=mock_client)


# ── shodan_internetdb ────────────────────────────────────────────────────────

class TestShodanInternetdb:
    async def test_returns_ip_scan_finding(self):
        body = {
            "ip": "93.184.216.34",
            "ports": [80, 443],
            "vulns": ["CVE-2021-44228"],
            "cpes": ["cpe:/a:apache:http_server"],
            "hostnames": ["example.com"],
            "tags": ["cdn"],
        }
        with patch("osintkit.modules.shodan_internetdb._resolve", return_value="93.184.216.34"):
            with _mock_http(200, body):
                from osintkit.modules.shodan_internetdb import run_shodan_internetdb
                results = await run_shodan_internetdb(INPUTS)

        assert len(results) == 1
        assert results[0]["source"] == "shodan_internetdb"
        assert results[0]["type"] == "ip_scan"
        assert results[0]["data"]["open_ports"] == [80, 443]
        assert "CVE-2021-44228" in results[0]["data"]["vulnerabilities"]

    async def test_404_returns_empty(self):
        with patch("osintkit.modules.shodan_internetdb._resolve", return_value="1.2.3.4"):
            with _mock_http(404, {}):
                from osintkit.modules.shodan_internetdb import run_shodan_internetdb
                results = await run_shodan_internetdb(INPUTS)
        assert results == []

    async def test_no_email_returns_empty(self):
        from osintkit.modules.shodan_internetdb import run_shodan_internetdb
        results = await run_shodan_internetdb(NO_INPUTS)
        assert results == []

    async def test_dns_failure_returns_empty(self):
        with patch("osintkit.modules.shodan_internetdb._resolve", return_value=None):
            from osintkit.modules.shodan_internetdb import run_shodan_internetdb
            results = await run_shodan_internetdb(INPUTS)
        assert results == []


# ── threatfox ────────────────────────────────────────────────────────────────

class TestThreatfox:
    async def test_returns_ioc_findings(self):
        body = {
            "query_status": "ok",
            "data": [
                {
                    "id": "123",
                    "ioc": "example.com",
                    "ioc_type": "domain",
                    "threat_type": "botnet_cc",
                    "malware_printable": "Emotet",
                    "confidence_level": 75,
                    "first_seen": "2024-01-01",
                    "last_seen": "2024-03-01",
                    "tags": ["emotet"],
                }
            ],
        }
        with _mock_http(200, body):
            from osintkit.modules.threatfox import run_threatfox
            results = await run_threatfox(INPUTS)

        assert len(results) == 1
        assert results[0]["source"] == "threatfox"
        assert results[0]["type"] == "threat_ioc"
        assert results[0]["data"]["malware"] == "Emotet"
        assert results[0]["data"]["threat_type"] == "botnet_cc"

    async def test_no_results_returns_empty(self):
        body = {"query_status": "ok", "data": []}
        with _mock_http(200, body):
            from osintkit.modules.threatfox import run_threatfox
            results = await run_threatfox(INPUTS)
        assert results == []

    async def test_no_email_returns_empty(self):
        from osintkit.modules.threatfox import run_threatfox
        results = await run_threatfox(NO_INPUTS)
        assert results == []

    async def test_non_ok_status_returns_empty(self):
        body = {"query_status": "no_results"}
        with _mock_http(200, body):
            from osintkit.modules.threatfox import run_threatfox
            results = await run_threatfox(INPUTS)
        assert results == []


# ── ipinfo ───────────────────────────────────────────────────────────────────

class TestIpinfo:
    async def test_returns_geolocation_finding(self):
        body = {
            "ip": "93.184.216.34",
            "city": "Norwell",
            "region": "Massachusetts",
            "country": "US",
            "org": "AS15133 Edgecast Inc.",
            "timezone": "America/New_York",
            "loc": "42.1595,-70.8229",
        }
        with patch("osintkit.modules.ipinfo._resolve", return_value="93.184.216.34"):
            with _mock_http(200, body):
                from osintkit.modules.ipinfo import run_ipinfo
                results = await run_ipinfo(INPUTS)

        assert len(results) == 1
        assert results[0]["source"] == "ipinfo"
        assert results[0]["type"] == "ip_geolocation"
        assert results[0]["data"]["country"] == "US"
        assert results[0]["data"]["org"] == "AS15133 Edgecast Inc."

    async def test_bogon_ip_returns_empty(self):
        body = {"ip": "192.168.1.1", "bogon": True}
        with patch("osintkit.modules.ipinfo._resolve", return_value="192.168.1.1"):
            with _mock_http(200, body):
                from osintkit.modules.ipinfo import run_ipinfo
                results = await run_ipinfo(INPUTS)
        assert results == []

    async def test_no_email_returns_empty(self):
        from osintkit.modules.ipinfo import run_ipinfo
        results = await run_ipinfo(NO_INPUTS)
        assert results == []


# ── greynoise ────────────────────────────────────────────────────────────────

class TestGreynoise:
    async def test_returns_ip_noise_finding(self):
        body = {
            "ip": "93.184.216.34",
            "noise": False,
            "riot": True,
            "classification": "benign",
            "name": "Edgecast CDN",
            "last_seen": "2024-03-01",
            "link": "https://viz.greynoise.io/ip/93.184.216.34",
            "message": "This IP is commonly associated with benign services.",
        }
        with patch("osintkit.modules.stage2.greynoise._resolve", return_value="93.184.216.34"):
            with _mock_http(200, body):
                from osintkit.modules.stage2.greynoise import run
                results = await run(INPUTS, "testkey")

        assert len(results) == 1
        assert results[0]["source"] == "greynoise"
        assert results[0]["data"]["classification"] == "benign"
        assert results[0]["data"]["riot"] is True

    async def test_malicious_classification(self):
        body = {
            "ip": "1.2.3.4",
            "noise": True,
            "riot": False,
            "classification": "malicious",
            "name": "Unknown",
            "last_seen": "2024-03-01",
        }
        with patch("osintkit.modules.stage2.greynoise._resolve", return_value="1.2.3.4"):
            with _mock_http(200, body):
                from osintkit.modules.stage2.greynoise import run
                results = await run(INPUTS, "testkey")

        assert results[0]["data"]["classification"] == "malicious"

    async def test_404_returns_empty(self):
        with patch("osintkit.modules.stage2.greynoise._resolve", return_value="1.2.3.4"):
            with _mock_http(404, {}):
                from osintkit.modules.stage2.greynoise import run
                results = await run(INPUTS, "testkey")
        assert results == []

    async def test_invalid_key_raises(self):
        from osintkit.modules import InvalidKeyError
        with patch("osintkit.modules.stage2.greynoise._resolve", return_value="1.2.3.4"):
            with _mock_http(401, {}):
                from osintkit.modules.stage2.greynoise import run
                with pytest.raises(InvalidKeyError):
                    await run(INPUTS, "badkey")


# ── netlas ───────────────────────────────────────────────────────────────────

class TestNetlas:
    async def test_returns_scan_findings(self):
        body = {
            "items": [
                {
                    "data": {
                        "ip": "93.184.216.34",
                        "port": 443,
                        "protocol": "tcp",
                        "http": {"title": "Example Domain", "status_code": 200},
                        "cve": [{"name": "CVE-2021-44228"}],
                        "tag": ["web"],
                    }
                }
            ]
        }
        with _mock_http(200, body):
            from osintkit.modules.stage2.netlas import run
            results = await run(INPUTS, "testkey")

        assert len(results) == 1
        assert results[0]["source"] == "netlas"
        assert results[0]["data"]["port"] == 443
        assert "CVE-2021-44228" in results[0]["data"]["cves"]

    async def test_empty_items_returns_empty(self):
        with _mock_http(200, {"items": []}):
            from osintkit.modules.stage2.netlas import run
            results = await run(INPUTS, "testkey")
        assert results == []

    async def test_rate_limit_raises(self):
        from osintkit.modules import RateLimitError
        with _mock_http(429, {}):
            from osintkit.modules.stage2.netlas import run
            with pytest.raises(RateLimitError):
                await run(INPUTS, "testkey")


# ── pulsedive ────────────────────────────────────────────────────────────────

class TestPulsedive:
    async def test_returns_ioc_risk(self):
        body = {
            "indicator": "example.com",
            "risk": "medium",
            "threats": [{"name": "Phishing"}],
            "feeds": [{"name": "PhishTank"}],
            "stamp_seen": "2024-01-01",
            "stamp_updated": "2024-03-01",
            "attributes": {"port": [443], "protocol": ["https"], "technology": []},
        }
        with _mock_http(200, body):
            from osintkit.modules.stage2.pulsedive import run
            results = await run(INPUTS, "testkey")

        assert len(results) == 1
        assert results[0]["source"] == "pulsedive"
        assert results[0]["data"]["risk"] == "medium"
        assert "Phishing" in results[0]["data"]["threats"]

    async def test_404_returns_empty(self):
        with _mock_http(404, {}):
            from osintkit.modules.stage2.pulsedive import run
            results = await run(INPUTS, "testkey")
        assert results == []

    async def test_error_field_returns_empty(self):
        with _mock_http(200, {"error": "Indicator not found."}):
            from osintkit.modules.stage2.pulsedive import run
            results = await run(INPUTS, "testkey")
        assert results == []

    async def test_invalid_key_raises(self):
        from osintkit.modules import InvalidKeyError
        with _mock_http(401, {}):
            from osintkit.modules.stage2.pulsedive import run
            with pytest.raises(InvalidKeyError):
                await run(INPUTS, "badkey")


# ── risk score for v0.2.0 modules ────────────────────────────────────────────

class TestRiskScoreV2:
    def test_greynoise_malicious_adds_15(self):
        from osintkit.risk import calculate_risk_score
        findings = {
            "greynoise": [{"data": {"classification": "malicious", "noise": True}}]
        }
        assert calculate_risk_score(findings) == 15

    def test_greynoise_benign_adds_0(self):
        from osintkit.risk import calculate_risk_score
        findings = {
            "greynoise": [{"data": {"classification": "benign", "noise": False}}]
        }
        assert calculate_risk_score(findings) == 0

    def test_threatfox_hits_add_score(self):
        from osintkit.risk import calculate_risk_score
        findings = {
            "threatfox": [
                {"data": {"malware": "Emotet"}},
                {"data": {"malware": "Qakbot"}},
            ]
        }
        assert calculate_risk_score(findings) == 10

    def test_threatfox_capped_at_15(self):
        from osintkit.risk import calculate_risk_score
        findings = {"threatfox": [{"data": {}}] * 10}
        score = calculate_risk_score(findings)
        assert score == 15

    def test_pulsedive_critical_adds_15(self):
        from osintkit.risk import calculate_risk_score
        findings = {"pulsedive": [{"data": {"risk": "critical"}}]}
        assert calculate_risk_score(findings) == 15

    def test_shodan_cves_add_score(self):
        from osintkit.risk import calculate_risk_score
        findings = {
            "shodan_internetdb": [
                {"data": {"vulnerabilities": ["CVE-2021-44228", "CVE-2022-0001"]}}
            ]
        }
        assert calculate_risk_score(findings) == 4

    def test_intelligencex_hits_add_score(self):
        from osintkit.risk import calculate_risk_score
        findings = {
            "intelligencex": [{"data": {}}, {"data": {}}, {"data": {}}]
        }
        assert calculate_risk_score(findings) == 6
