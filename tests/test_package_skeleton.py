"""Verify every sub-package exists and re-exports the project version.

Guards issue #6: the src/copthief package must expose sdk, services, agents,
mcp, llm, reporting, gui, and shared, each with __version__.
"""

import importlib

from copthief import __version__

SUBPACKAGES = [
    "copthief.sdk",
    "copthief.services",
    "copthief.agents",
    "copthief.mcp",
    "copthief.llm",
    "copthief.reporting",
    "copthief.gui",
    "copthief.shared",
]


def test_subpackages_import_and_expose_version() -> None:
    for name in SUBPACKAGES:
        module = importlib.import_module(name)
        assert module.__version__ == __version__
