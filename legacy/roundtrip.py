#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["PyYAML>=6"]
# ///
"""Extract coauthor tracked changes/comments from a DOCX into a merge worksheet.

LEGACY SHIM — the logic moved to wongo.engine.roundtrip (HANDOFF step 4); this
script only forwards CLI arguments. See `wongo roundtrip --help`.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from wongo.engine.roundtrip import main as _rt_main  # noqa: E402


def main() -> int:
    return _rt_main()


if __name__ == "__main__":
    raise SystemExit(main())
