#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["PyYAML>=6", "python-docx>=1.1"]
# ///
"""Render a Quarto manuscript to collaboration- or submission-grade DOCX.

LEGACY SHIM — the engine moved to wongo.engine (HANDOFF step 4); this script
only forwards CLI arguments. See `wongo render --help`.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from wongo.engine import render_project


def main() -> int:
    ap = argparse.ArgumentParser(description="Render collab- or submission-grade DOCX (main + SI)")
    ap.add_argument("--target", required=True, choices=("collab", "submission"))
    ap.add_argument("--project", default=".")
    args = ap.parse_args()
    return render_project(Path(args.project).resolve(), args.target)


if __name__ == "__main__":
    raise SystemExit(main())
