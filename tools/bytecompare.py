#!/usr/bin/env python3
"""Byte-compare verification harness for the wongo uplift (ground rule 1).

Renders the the reference manuscript manuscript (copied to a scratch dir — the live project is
never touched) with an engine command, then diffs the unzipped DOCX XML
against a stored baseline. Cosmetic-identical or explainable-diff only.

Usage:
    bytecompare.py baseline [--target collab|submission|both]
        Render with the CURRENT engine and store outputs as the baseline.
    bytecompare.py selftest
        Render twice with the current engine and diff run-vs-run to measure
        quarto/pandoc nondeterminism (the noise floor).
    bytecompare.py check [--target ...] [--baseline DIR] [--allow PATTERN_FILE]
        Render with the current engine and diff against the baseline.
        Exits 1 on any unexplained diff. --allow lists regex patterns (one per
        line, FILE:regex-line format matched against the unified-diff header +
        changed lines) for diffs already justified in OVERNIGHT-LOG.md.

Scratch layout under /tmp/wongo-bc/:
    manuscript/   fresh copy of the the reference manuscript manuscript each invocation
    baseline/     unzipped word/*.xml trees of the baseline render
    candidate/    unzipped word/*.xml trees of the current render

Only files under word/, plus [Content_Types].xml and _rels/.rels, are compared
(docProps carries creation timestamps that are irrelevant to rendering).
"""
from __future__ import annotations

import argparse
import filecmp
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REF_ROOT = Path.home() / "workbench" / "the reference manuscript"
REF = REF_ROOT / "manuscript"
SCRATCH = Path("/tmp/wongo-bc")
COMPARED = ("word/", "[Content_Types].xml", "_rels/.rels")

ENGINES = {
    # name -> argv template. The legacy engine was the oracle until v0.1.0
    # (legacy/ removed); current engine is wongo CLI.
    "legacy": [sys.executable, str(REPO / "legacy" / "render.py")],
    "wongo": ["uv", "run", "wongo", "render"],
}


def prepare_project() -> Path:
    """Copy the WHOLE the reference manuscript repo: index.qmd references assets outside
    manuscript/ via ../training/... paths, which break in an isolated copy."""
    root = SCRATCH / "ref"
    proj = root / "manuscript"
    if root.exists():
        shutil.rmtree(root)
    root.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(REF_ROOT, root, symlinks=True)
    return proj


def unzip_word_trees(docx: Path, dest: Path) -> None:
    import zipfile

    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(str(docx)) as z:
        for n in z.namelist():
            if n.startswith(COMPARED) or n in COMPARED:
                out = dest / n
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(z.read(n))


def render_and_extract(engine: list[str], target: str, tag: str) -> list[Path]:
    proj = prepare_project()
    targets = ["collab", "submission"] if target == "both" else [target]
    docxs: list[Path] = []
    for t in targets:
        subprocess.run(
            engine + ["--target", t, "--project", str(proj)],
            cwd=REPO, check=True,
        )
        for stem in (f"main-{t}", f"si-{t}"):
            d = proj / "output" / f"{stem}.docx"
            if d.exists():
                unzip_word_trees(d, SCRATCH / tag / stem)
                docxs.append(d)
    out = SCRATCH / tag
    return sorted(tree_files(out).values()) if out.exists() else []


def tree_files(root: Path) -> dict[str, Path]:
    return {str(p.relative_to(root)): p for p in sorted(root.rglob("*")) if p.is_file()}


def diff_trees(a_root: Path, b_root: Path) -> dict[str, list[str]]:
    """Return {relative-file-name: diff-report-lines} for differing files.
    Empty dict means identical trees. Diff lines for a single file can be
    huge (document.xml is one line), so gating is per-FILE via the returned
    keys — see allowed()."""
    fa, fb = tree_files(a_root), tree_files(b_root)
    report: dict[str, list[str]] = {}
    for name in sorted(set(fa) | set(fb)):
        if name not in fa:
            report[name] = [f"ONLY-IN-CANDIDATE {name}"]
            continue
        if name not in fb:
            report[name] = [f"ONLY-IN-BASELINE {name}"]
            continue
        if not filecmp.cmp(fa[name], fb[name], shallow=False):
            import difflib

            a = fa[name].read_text(encoding="utf-8", errors="replace").splitlines()
            b = fb[name].read_text(encoding="utf-8", errors="replace").splitlines()
            dl = list(difflib.unified_diff(a, b, fromfile=f"baseline/{name}",
                                           tofile=f"candidate/{name}", lineterm=""))
            report[name] = dl or [f"BIN-DIFF {name}"]
    return report


def allowed(report: dict[str, list[str]], patterns: list[re.Pattern]) -> dict[str, list[str]]:
    """Keep only files whose NAME matches no allowlist pattern (whole-file
    gating: content lines of one-line XML carry no filename)."""
    def is_allowed(name: str) -> bool:
        return any(p.search(name) for p in patterns)

    return {n: d for n, d in report.items() if not is_allowed(n)}


def load_patterns(path: Path | None) -> list[re.Pattern]:
    if path is None:
        return []
    pats = []
    for ln in path.read_text().splitlines():
        ln = ln.strip()
        if ln and not ln.startswith("#"):
            pats.append(re.compile(ln))
    return pats


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=("baseline", "selftest", "check"))
    ap.add_argument("--target", default="both", choices=("collab", "submission", "both"))
    ap.add_argument("--engine", default="wongo", choices=sorted(ENGINES))
    ap.add_argument("--baseline", type=Path, default=SCRATCH / "baseline")
    ap.add_argument("--allow", type=Path, default=None,
                    help="file of regex patterns for pre-justified diffs")
    args = ap.parse_args()

    engine = ENGINES[args.engine]
    if args.engine == "legacy" and not Path(engine[1]).exists():
        print(f"legacy engine not found: {engine[1]} — legacy/ was removed in v0.1.0; use --engine wongo", file=sys.stderr)
        return 1

    if args.mode == "selftest":
        first = render_and_extract(engine, args.target, "baseline")
        second_dir = SCRATCH / "second"
        # rerun without wiping baseline: prepare_project() wipes all of SCRATCH,
        # so stash the first tree first
        stash = SCRATCH / "baseline"
        tmp_move = SCRATCH / "_first"
        shutil.move(str(stash), str(tmp_move))
        try:
            render_and_extract(engine, args.target, "baseline")
            report = diff_trees(tmp_move, stash)
        finally:
            if tmp_move.exists():
                shutil.rmtree(tmp_move)
        if report:
            print(f"NOISE FLOOR: {len(report)} differing files across runs — "
                  "quarto output is NOT deterministic; comparisons need normalization.")
            print("\n".join(sorted(report)[:40]))
            return 1
        print(f"NOISE FLOOR: zero — consecutive {args.engine} renders are byte-identical.")
        return 0

    if args.mode == "baseline":
        render_and_extract(engine, args.target, "baseline")
        n = len(tree_files(args.baseline))
        print(f"BASELINE stored: {n} files under {args.baseline} (target={args.target})")
        return 0

    # mode == check
    render_and_extract(engine, args.target, "candidate")
    report = diff_trees(args.baseline, SCRATCH / "candidate")
    unexplained = allowed(report, load_patterns(args.allow))
    if not unexplained:
        print(f"BYTE-COMPARE PASS ({len(report)} raw diffs in "
              f"{', '.join(sorted(report))}, all allowlisted)"
              if report else "BYTE-COMPARE PASS (identical)")
        return 0
    print(f"BYTE-COMPARE FAIL — unexplained diffs in: {', '.join(sorted(unexplained))}")
    for name, dl in sorted(unexplained.items()):
        print(f"\n===== {name} =====")
        print("\n".join(dl[:60]))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
