"""Smoke test: the package imports and reports its version.

Exists so the CI test+coverage gate has something to run before the engine
lands (issue #12 onward). Replace/extend as real modules arrive.
"""

from copthief import __version__


def test_version_is_expected_string() -> None:
    assert isinstance(__version__, str)
    assert __version__ == "1.0.0"
