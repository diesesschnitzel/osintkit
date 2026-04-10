"""Configuration loader for osintkit."""

from pathlib import Path
from typing import Any
import yaml
from pydantic import BaseModel, Field


class APIKeys(BaseModel):
    """Optional API keys for premium modules."""

    emailrep: str = ""
    breachdirectory: str = ""
    leakcheck: str = ""
    google_cse_key: str = ""
    google_cse_cx: str = ""
    intelbase: str = ""
    numverify: str = ""
    resend: str = ""
    hibp: str = ""
    hunter: str = ""
    github: str = ""
    securitytrails: str = ""
    epieos: str = ""


class Config(BaseModel):
    """osintkit configuration."""

    output_dir: str = "~/osint-results"
    timeout_seconds: int = 120
    api_keys: APIKeys = Field(default_factory=APIKeys)


def save_config(config: Config, config_path: Path) -> None:
    """Save configuration to YAML file."""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "output_dir": config.output_dir,
        "timeout_seconds": config.timeout_seconds,
        "api_keys": config.api_keys.model_dump(),
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
