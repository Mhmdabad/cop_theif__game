#!/usr/bin/env python3
"""Fail if any source file exceeds 150 lines of code.

Blank lines and full-line comments are excluded, per guidelines §3.2. Scans the
package and tests; run by CI (.github/workflows/ci.yml).
"""

from __future__ import annotations

import sys
from pathlib import Path

LIMIT = 150
ROOTS = ("src", "tests", "scripts")


def code_lines(path: Path) -> int:
    """Count non-blank, non-comment lines in a Python file."""
    count = 0
    for raw in path.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        count += 1
    return count


def main() -> int:
    violations: list[str] = []
    for root in ROOTS:
        for path in Path(root).rglob("*.py"):
            n = code_lines(path)
            if n > LIMIT:
                violations.append(f"{path}: {n} > {LIMIT}")
    if violations:
        print("Files exceeding the 150-line limit:")
        print("\n".join(violations))
        return 1
    print("Line-limit check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
