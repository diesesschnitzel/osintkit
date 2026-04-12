"""Configuration loader for osintkit."""

from pathlib import Path
from typing import Any
import yaml
from pydantic import BaseModel, Field


class APIKeys(BaseModel):
    """Optional API keys for osintkit modules.

    Stage 1 tokens (optional — raise rate limits):
      emailrep, ipinfo, github

    Stage 2 keys (free accounts — activate module when present):
      virustotal, otx, abuseipdb, greynoise, intelligencex, netlas, pulsedive,
      securitytrails, hunter, numverify
    """

    # Stage 1 — optional tokens (module runs without them, but slower/limited)
    emailrep: str = ""
    ipinfo: str = ""          # https://ipinfo.io/signup — free, 50k/month
    github: str = ""          # https://github.com/settings/tokens — free

    # Stage 1 — data enrichment keys
    breachdirectory: str = ""
    google_cse_key: str = ""
    google_cse_cx: str = ""
    intelbase: str = ""

    # Stage 2 — free-tier keys (sign up, no credit card)
    virustotal: str = ""      # https://www.virustotal.com/gui/join-us
    otx: str = ""             # https://otx.alienvault.com/
    abuseipdb: str = ""       # https://www.abuseipdb.com/register
    greynoise: str = ""       # https://www.greynoise.io/plans/free-intelligence
    intelligencex: str = ""   # https://intelx.io/
    netlas: str = ""          # https://app.netlas.io/plans/
    pulsedive: str = ""       # https://pulsedive.com/

    # Stage 2 — other free-tier keys
    securitytrails: str = ""  # https://securitytrails.com/ — 50/month
    hunter: str = ""          # https://hunter.io/ — 25/month
    numverify: str = ""       # https://numverify.com/ — 100/month

    # Legacy / internal
    resend: str = ""
    hibp: str = ""


class Config(BaseModel):
    """osintkit configuration."""

    output_dir: str = "~/osint-results"
    timeout_seconds: int = 120
    api_keys: APIKeys = Field(default_factory=APIKeys)
    last_seen_version: str = ""  # tracks which version the user last ran (for update notices)


def save_config(config: Config, config_path: Path) -> None:
    """Save configuration to YAML file."""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "output_dir": config.output_dir,
        "timeout_seconds": config.timeout_seconds,
        "api_keys": config.api_keys.model_dump(),
        "last_seen_version": config.last_seen_version,
    }
    with open(config_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False)
    config_path.chmod(0o600)


def load_config(config_path: Path) -> Config:
    """Load configuration from YAML file.

    Returns default config if file doesn't exist.
    """
    if not config_path.exists():
        return Config()

    with open(config_path) as f:
        data = yaml.safe_load(f) or {}

    api_keys_data = data.pop("api_keys", {})

    return Config(
        **data,
        api_keys=APIKeys(**api_keys_data) if api_keys_data else APIKeys(),
    )
