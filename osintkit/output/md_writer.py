"""Markdown report writer for osintkit scan results."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


def _scrub_keys(content: str, api_keys: Optional[Dict[str, str]] = None) -> str:
    """Replace any API key values in content with [REDACTED].

    Args:
        content: The string to scrub.
        api_keys: Dict mapping key name -> key value. Values longer than
                  6 characters are scrubbed; shorter ones are skipped to
                  avoid over-scrubbing short common strings.

    Returns:
        Scrubbed string.
    """
    if not api_keys:
        return content
    for _name, value in api_keys.items():
        if value and len(value) > 6:
            content = content.replace(value, "[REDACTED]")
    return content


def write_md(
    findings: Dict[str, Any],
    output_dir: Path,
    api_keys: Optional[Dict[str, str]] = None,
) -> Path:
    """Generate a Markdown report from scan findings.

    Args:
        findings: The findings dict produced by Scanner.run().
        output_dir: Directory where findings.md will be written.
        api_keys: Optional dict of API key values to scrub from output.

    Returns:
        Path to the written file.
    """
    inputs = findings.get("inputs", {})
    scan_date = findings.get("scan_date", datetime.now().isoformat())
    risk_score = findings.get("risk_score", 0)
    modules_meta = findings.get("modules", {})
    findings_by_module = findings.get("findings", {})

    name = inputs.get("name") or inputs.get("username") or inputs.get("email") or "Unknown"

    lines = [
        f"# osintkit Report: {name}",
        "",
        f"**Generated:** {scan_date}",
        f"**Date:** {scan_date[:10]}",
        "",
        "## Target Information",
        "",
    ]

    for field in ("name", "email", "username", "phone"):
        value = inputs.get(field) or "—"
        lines.append(f"- **{field.capitalize()}:** {value}")

    lines += [
        "",
        f"## Risk Score: {risk_score}/100",
        "",
    ]

    if risk_score >= 70:
        lines.append("> **HIGH RISK** — significant digital footprint detected.")
    elif risk_score >= 40:
        lines.append("> **MEDIUM RISK** — moderate digital footprint detected.")
    else:
        lines.append("> **LOW RISK** — limited digital footprint detected.")

    lines += ["", "## Module Results", ""]

    for module_name, meta in modules_meta.items():
        status = meta.get("status", "unknown")
        count = meta.get("count", 0)
        error = meta.get("error", "")
        status_str = f"done ({count} findings)" if status == "done" else f"failed: {error}"
        lines.append(f"- **{module_name}**: {status_str}")

    lines += ["", "## Findings", ""]

    for module_name, module_findings in findings_by_module.items():
        if not module_findings:
            continue

        lines.append(f"### {module_name}")
        lines.append("")

        for finding in module_findings:
            ftype = finding.get("type", "unknown")
            source = finding.get("source", "unknown")
            url = finding.get("url")
            data = finding.get("data", {})

            lines.append(f"**{ftype}** (source: {source})")
            if url:
                lines.append(f"- URL: {url}")
            if data:
                for key, val in data.items():
                    lines.append(f"- {key}: {val}")
            lines.append("")

    content = "\n".join(lines)
    content = _scrub_keys(content, api_keys)

    output_file = output_dir / "findings.md"
    output_file.write_text(content, encoding="utf-8")
    return output_file
