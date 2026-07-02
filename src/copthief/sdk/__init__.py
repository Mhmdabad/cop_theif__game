"""copthief.sdk — single entry point for all business logic (SDK layer)."""

from copthief import __version__ as __version__
from copthief.sdk.sdk import CopThiefSDK

__all__ = ["__version__", "CopThiefSDK"]
