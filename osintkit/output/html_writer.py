"""HTML report writer using Jinja2."""

from pathlib import Path
from typing import Any, Dict, Optional
from jinja2 import Environment, FileSystemLoader


def _scrub_keys(content: str, api_keys: Optional[Dict[str, str]] = None) -> str:
    """Replace any API key values in content with [REDACTED]."""
    if not api_keys:
        return content
    for _name, value in api_keys.items():
        if value and len(value) > 6:
            content = content.replace(value, "[REDACTED]")
    return content


def write_html(
    findings: Dict[str, Any],
    output_dir: Path,
    api_keys: Optional[Dict[str, str]] = None,
) -> Path:
    """Render HTML report via Jinja2 template.

    API key values are scrubbed from the rendered output before writing.
    """
    templates_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template("report.html")

    html_content = template.render(**findings)
    html_content = _scrub_keys(html_content, api_keys)

    output_file = output_dir / "report.html"
    output_file.write_text(html_content, encoding="utf-8")
    return output_file
