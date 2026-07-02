"""Code version and config-version compatibility checks (guidelines §8.1).

The app validates that config files were written for a compatible schema version
before using them, so a stale config fails fast with a clear message rather than
producing subtle wrong behavior. The full typed config loader is issue #21.
"""

from __future__ import annotations

from typing import Any

CODE_VERSION = "1.00"
SUPPORTED_CONFIG_VERSION = "1.00"


class ConfigVersionError(RuntimeError):
    """Raised when a config file's version is incompatible with the code."""


def config_version(config: dict[str, Any]) -> str | None:
    """Return the version declared by a config mapping.

    Looks at the top-level ``version`` key, falling back to a nested
    ``rate_limits.version`` (the rate-limits file nests its version).
    """
    if "version" in config:
        return config["version"]
    rate_limits = config.get("rate_limits")
    if isinstance(rate_limits, dict):
        return rate_limits.get("version")
    return None


def validate_config_version(
    config: dict[str, Any], *, expected: str = SUPPORTED_CONFIG_VERSION
) -> str:
    """Return the config version, or raise ``ConfigVersionError`` if incompatible."""
    version = config_version(config)
    if version is None:
        raise ConfigVersionError("config is missing a 'version' field")
    if version != expected:
        raise ConfigVersionError(f"config version {version!r} != expected {expected!r}")
    return version
