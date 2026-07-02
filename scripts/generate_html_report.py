"""Generate HTML test and coverage reports under ``results/`` (issue #44).

Run locally with::

    uv run python scripts/generate_html_report.py

The produced artifacts are also uploaded by the CI workflow.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "--cov",
        "--cov-report=html:results/coverage_html",
        "--html=results/report.html",
        "--self-contained-html",
    ]
    print("Running:", " ".join(cmd))
    return subprocess.call(cmd)


if __name__ == "__main__":
    sys.exit(main())
