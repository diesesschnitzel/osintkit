"""Risk score calculation for osintkit."""

from typing import Dict, List


def calculate_risk_score(findings: Dict[str, List]) -> int:
    """Calculate risk score 0–100 based on findings across all modules.

    Scoring buckets
    ───────────────
    Breach / credential exposure   → up to 30 pts
    Social footprint               → up to 20 pts
    Data broker listings           → up to 20 pts
    Dark web / paste dumps         → up to 15 pts
    Password / hash exposure       → up to 15 pts
    Threat intelligence signals    → up to 25 pts  (new in 0.1.7)

    Total can exceed 100 before capping, so we clamp at the end.
    """
    score = 0

    # ── Breach exposure (30 pts max) ────────────────────────────
    breach_count = len(findings.get("breach_exposure", []))
    score += min(30, breach_count * 3)

    # ── Social profiles (20 pts max) ────────────────────────────
    social_count = len(findings.get("social_profiles", []))
    score += min(20, social_count * 2)

    # ── Data brokers (20 pts max) ────────────────────────────────
    broker_count = len(findings.get("data_brokers", []))
    score += min(20, broker_count * 4)

    # ── Dark web + paste (15 pts max) ───────────────────────────
    dark_count = len(findings.get("dark_web", [])) + len(findings.get("paste_sites", []))
    score += min(15, dark_count * 5)

    # ── Password / hash exposure (15 pts max) ────────────────────
    # Covers both HIBP full API ("password_exposure") and k-anonymity ("hibp_kanon")
    pw_score = 0
    for key in ("password_exposure", "hibp_kanon"):
        pw_data = findings.get(key, [])
        if pw_data and isinstance(pw_data[0], dict):
            count = pw_data[0].get("data", {}).get("count", 0)
            if count:
                pw_score = max(pw_score, min(15, count // 1000))
    if pw_score == 0:
        all_pw = findings.get("password_exposure", []) + findings.get("hibp_kanon", [])
        if all_pw:
            pw_score = 5
    score += pw_score

    # ── VirusTotal domain reputation (up to 20 pts) ─────────────
    for f in findings.get("virustotal", []):
        data = f.get("data", {})
        malicious = data.get("malicious", 0) or 0
        suspicious = data.get("suspicious", 0) or 0
        if malicious > 0:
            # Any malicious hit is serious; scale up with count
            score += min(20, 10 + malicious)
        elif suspicious > 0:
            score += min(10, 3 + suspicious)

    # ── AbuseIPDB IP abuse confidence (up to 20 pts) ────────────
    for f in findings.get("abuseipdb", []):
        confidence = f.get("data", {}).get("abuse_confidence_score") or 0
        # Scale: score 100 → 20 pts, score 50 → 10 pts
        score += min(20, int(confidence / 5))

    # ── emailrep reputation flags (up to 15 pts) ────────────────
    for f in findings.get("emailrep", []):
        data = f.get("data", {})
        rep = data.get("reputation", "none")
        if data.get("blacklisted"):
            score += 15
        elif data.get("malicious_activity_recent"):
            score += 12
        elif data.get("malicious_activity"):
            score += 8
        elif data.get("suspicious") or rep in ("low", "none"):
            score += 4
        if data.get("credentials_leaked"):
            score += 5  # additional hit on top

    # ── urlscan malicious verdicts (up to 10 pts) ───────────────
    malicious_scans = sum(
        1 for f in findings.get("urlscan", [])
        if f.get("data", {}).get("malicious")
    )
    score += min(10, malicious_scans * 5)

    # ── OTX threat intel pulse count (up to 10 pts) ─────────────
    for f in findings.get("otx", []):
        pulses = f.get("data", {}).get("pulse_count", 0) or 0
        score += min(10, pulses * 2)

    # ── GreyNoise IP classification (up to 15 pts) ───────────────
    for f in findings.get("greynoise", []):
        classification = f.get("data", {}).get("classification", "")
        if classification == "malicious":
            score += 15
        elif classification == "unknown" and f.get("data", {}).get("noise"):
            score += 5  # known scanner but unclassified

    # ── ThreatFox IOC hits (up to 15 pts) ───────────────────────
    threatfox_hits = findings.get("threatfox", [])
    if threatfox_hits:
        # Each IOC hit is significant; cap quickly
        score += min(15, len(threatfox_hits) * 5)

    # ── Shodan open CVEs (up to 10 pts) ─────────────────────────
    for f in findings.get("shodan_internetdb", []):
        vulns = f.get("data", {}).get("vulnerabilities", []) or []
        score += min(10, len(vulns) * 2)

    # ── Pulsedive IOC risk level (up to 15 pts) ──────────────────
    _pulsedive_risk = {"critical": 15, "high": 12, "medium": 8, "low": 4, "none": 0}
    for f in findings.get("pulsedive", []):
        risk_level = f.get("data", {}).get("risk", "none")
        score += _pulsedive_risk.get(risk_level, 0)

    # ── IntelligenceX leaked records (up to 10 pts) ──────────────
    ix_hits = findings.get("intelligencex", [])
    if ix_hits:
        score += min(10, len(ix_hits) * 2)

    return min(100, score)
