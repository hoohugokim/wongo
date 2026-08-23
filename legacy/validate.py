#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["PyYAML>=6"]
# ///
"""Validate a Quarto manuscript project against its journal profile.

Usage: validate.py [--project DIR] [--strict]

HARD checks (gate submission renders): word limit per the profile's counting
rule, unresolved citekeys, orphaned cross-references, referenced-but-missing
figure files. WARN checks: journal profile older than 6 months, expected SI
file absent. --strict exits 1 on any HARD failure (render.py relies on this).
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import mslib

STALE_DAYS = 183


@dataclass
class Check:
    name: str
    level: str  # "HARD" | "WARN"
    ok: bool
    detail: str


def run_checks(project: Path) -> list[Check]:
    project = Path(project)
    cfg = mslib.load_journal_config(project)
    profile = mslib.load_profile(cfg["journal"])
    mtype = mslib.manuscript_type(profile, cfg["ms_type"])
    checks: list[Check] = []

    texts = {}
    for name in ("index.qmd", "si.qmd"):
        p = project / name
        if p.exists():
            texts[name] = p.read_text(encoding="utf-8")
    if "index.qmd" not in texts:
        raise SystemExit(f"index.qmd not found in {project}")

    wc = mslib.word_count(texts["index.qmd"])
    limit = mtype.get("word_limit")
    checks.append(Check(
        "word-limit", "HARD", limit is None or wc <= limit,
        f"{wc} words vs limit {limit} for {cfg['ms_type']} "
        f"(rule: {mtype.get('counting_rule', 'unspecified')})",
    ))

    bib_path = project / "refs.bib"
    bib = mslib.bib_keys(bib_path.read_text(encoding="utf-8")) if bib_path.exists() else set()
    used = set().union(*(mslib.citekeys_used(t) for t in texts.values()))
    missing = sorted(used - bib)
    checks.append(Check(
        "citekeys", "HARD", not missing,
        "all citekeys resolve" if not missing else f"missing from refs.bib: {', '.join(missing)}",
    ))

    defined = set().union(*(mslib.labels_defined(t) for t in texts.values()))
    orphans = sorted(set().union(*(mslib.crossrefs_used(t) for t in texts.values())) - defined)
    checks.append(Check(
        "crossrefs", "HARD", not orphans,
        "all cross-references resolve" if not orphans else f"orphaned: {', '.join(orphans)}",
    ))

    missing_figs = []
    for name, text in texts.items():
        for rel in mslib.image_paths(text):
            if not (project / rel).exists():
                missing_figs.append(f"{name} -> {rel}")
    checks.append(Check(
        "figures", "HARD", not missing_figs,
        "all referenced figures exist" if not missing_figs else "; ".join(missing_figs),
    ))

    days = mslib.profile_staleness_days(profile)
    checks.append(Check(
        "profile-staleness", "WARN", days is not None and days <= STALE_DAYS,
        f"profile verified {days} days ago" if days is not None
        else "profile has no verified_date",
    ))

    si_expected = (profile.get("si") or {}).get("separate_file")
    checks.append(Check(
        "si-file", "WARN", not si_expected or "si.qmd" in texts,
        "si.qmd present" if "si.qmd" in texts else "profile expects separate SI but si.qmd is absent",
    ))
    return checks


def print_report(checks: list[Check]) -> None:
    for c in checks:
        mark = "PASS" if c.ok else ("FAIL" if c.level == "HARD" else "WARN")
        print(f"[{mark}] {c.level:4} {c.name}: {c.detail}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
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
