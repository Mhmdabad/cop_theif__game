#!/usr/bin/env python3
"""Fail if obvious secrets appear in tracked files (defense-in-depth, §7.4).

Scans git-tracked text files for private keys and quoted credential literals.
Placeholder files (.env-example) and this scanner are skipped. Run by CI.
"""

from __future__ import annotations

import re
import subprocess
import sys

PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"""(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*['"][^'"]{8,}['"]"""),
)
SKIP_SUFFIXES = (".env-example", "secret_scan.py", ".lock")


def tracked_files() -> list[str]:
    """Return the list of files tracked by git."""
    result = subprocess.run(["git", "ls-files"], capture_output=True, text=True, check=True)
    return [line for line in result.stdout.splitlines() if line]


def main() -> int:
    findings: list[str] = []
    for path in tracked_files():
        if path.endswith(SKIP_SUFFIXES):
            continue
        try:
            with open(path, encoding="utf-8", errors="ignore") as handle:
                for num, line in enumerate(handle, 1):
                    if any(pattern.search(line) for pattern in PATTERNS):
                        findings.append(f"{path}:{num}")
        except OSError:
            continue
    if findings:
        print("Potential secrets found in tracked files:")
        print("\n".join(findings))
        return 1
    print("Secret scan passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
