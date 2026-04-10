"""Risk score calculation for osintkit."""

from typing import Dict, List


def calculate_risk_score(findings: Dict[str, List]) -> int:
    """Calculate risk score 0-100 based on findings.
    
    Formula:
    - Breach findings: 3 pts each, max 30 (cap at 10)
    - Social profiles: 2 pts each, max 20 (cap at 10)
    - Data brokers: 4 pts each, max 20 (cap at 5)
    - Dark web/paste: 5 pts each, max 15 (cap at 3)
    
    Returns: int 0-100
    """
    score = 0
    
    # Breach exposure (30 points max)
    breach_count = len(findings.get("breach_exposure", []))
    score += min(30, breach_count * 3)
    
    # Social profiles (20 points max)
    social_count = len(findings.get("social_profiles", []))
    score += min(20, social_count * 2)
    
    # Data brokers (20 points max)
    broker_count = len(findings.get("data_brokers", []))
    score += min(20, broker_count * 4)
    
    # Dark web + paste sites (15 points max)
    dark_count = len(findings.get("dark_web", [])) + len(findings.get("paste_sites", []))
    score += min(15, dark_count * 5)
    
    # Password / hash exposure (15 points max)
    # Covers both: HIBP full API ("password_exposure") and k-anonymity check ("hibp_kanon")
    pw_score = 0
    for key in ("password_exposure", "hibp_kanon"):
        pw_data = findings.get(key, [])
        if pw_data and isinstance(pw_data[0], dict):
            count = pw_data[0].get("data", {}).get("count", 0)
            if count:
                pw_score = max(pw_score, min(15, count // 1000))
    # Even a single confirmed exposure without a count is worth some points
    if pw_score == 0:
        all_pw = findings.get("password_exposure", []) + findings.get("hibp_kanon", [])
        if all_pw:
            pw_score = 5
    score += pw_score

    return min(100, score)
