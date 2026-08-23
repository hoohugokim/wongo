#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["PyYAML>=6"]
# ///
"""Validate a Quarto manuscript project against its journal profile.

LEGACY SHIM — the checks moved to wongo.engine.checks (HANDOFF step 4); this
script only forwards CLI arguments. See `wongo check --help`.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from wongo.engine.checks import print_report, run_checks


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Run validation checks (word limit, citekeys, crossrefs, figures)"
    )
    ap.add_argument("--project", default=".")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    checks = run_checks(Path(args.project).resolve())
    print_report(checks)
    hard_failures = [c for c in checks if c.level == "HARD" and not c.ok]
    if args.strict and hard_failures:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
