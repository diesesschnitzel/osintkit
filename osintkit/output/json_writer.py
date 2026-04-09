"""JSON output writer."""

import json
from pathlib import Path
from typing import Any, Dict, Optional


def _scrub_keys(content: str, api_keys: Optional[Dict[str, str]] = None) -> str:
    """Replace any API key values in content with [REDACTED]."""
    if not api_keys:
        return content
    for _name, value in api_keys.items():
        if value and len(value) > 6:
            content = content.replace(value, "[REDACTED]")
    return content


def write_json(
    findings: Dict[str, Any],
    output_dir: Path,
    api_keys: Optional[Dict[str, str]] = None,
) -> Path:
    """Write findings to JSON file with 2-space indent.

    API key values are scrubbed from the output before writing.
    """
    output_file = output_dir / "findings.json"
    content = json.dumps(findings, indent=2, default=str)
    content = _scrub_keys(content, api_keys)
    output_file.write_text(content, encoding="utf-8")
    return output_file
