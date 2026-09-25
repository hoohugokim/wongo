#!/usr/bin/env python3
"""Byte-compare verification harness for render parity (engine rule 1).

Copies the reference manuscript repository (WONGO_REF_PROJECT = its repo root)
into a scratch directory, renders the COPY with a wongo checkout, and diffs the
unzipped DOCX XML against a stored baseline. The live reference project is
never written to. Cosmetic-identical or explainable diffs only.

Usage:
    bytecompare.py baseline [--target collab|submission|both] [--repo DIR]
        Render and store the result as the baseline. Use --repo to render with
        another checkout, e.g. a worktree at the previous release tag.
    bytecompare.py selftest [--target ...]
        Render twice with the same checkout and diff run-vs-run to measure
        quarto/pandoc nondeterminism (the noise floor). Never touches the
        stored baseline.
    bytecompare.py check [--target ...] [--baseline DIR] [--allow FILE]
        Render with this checkout (or --repo) and diff against the baseline.
        Exits 1 on any unexplained diff. --allow names a file of regex
        patterns matched against compared part names (e.g.
        ^si-collab/word/document\\.xml$) for diffs justified in its comments.

Typical release check (fish):
    git worktree add --detach /tmp/wongo-prev v0.2.0
    uv run tools/bytecompare.py baseline --repo /tmp/wongo-prev
    uv run tools/bytecompare.py check --allow tools/bytecompare-allow.txt

Scratch layout (WONGO_BC_SCRATCH, default <system temp>/wongo-bc):
    ref/          fresh copy of the reference repo for each render pass
                  (.git, .pixi, .venv, node_modules, __pycache__ and
                  manuscript/output are not copied)
    baseline/     unzipped parts of the baseline render
    candidate/    unzipped parts of the render under test
    selftest-a/   selftest renders
    selftest-b/

Only files under word/, plus [Content_Types].xml and _rels/.rels, are compared
(docProps carries creation timestamps that are irrelevant to rendering). Every
expected output must be produced by the render under test: main-<target>.docx
always, si-<target>.docx when si.qmd exists.
"""
from __future__ import annotations

import argparse
import difflib
import filecmp
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
COMPARED = ("word/", "[Content_Types].xml", "_rels/.rels")


def fail(message: str):
    raise SystemExit(f"error: {message}")


def scratch_root() -> Path:
    override = os.environ.get("WONGO_BC_SCRATCH")
    if override:
        return Path(override).expanduser()
    return Path(tempfile.gettempdir()) / "wongo-bc"


def reference_root() -> Path:
    raw = os.environ.get("WONGO_REF_PROJECT")
    if not raw:
        fail("set WONGO_REF_PROJECT to the reference manuscript repo root")
    root = Path(raw).expanduser().resolve()
    if not (root / "manuscript").is_dir():
        fail(f"{root / 'manuscript'} not found (WONGO_REF_PROJECT={raw})")
    return root


# Version-control history and local environments/caches are never render
# inputs; skipping them keeps the per-pass copy small.
SKIPPED_EVERYWHERE = {".git", ".pixi", ".venv", "node_modules", "__pycache__"}


def _copy_filter(source_root: Path):
    """Skip SKIPPED_EVERYWHERE and previous renders in manuscript/output:
    stale outputs in the copy could stand in for files a broken render never
    wrote."""
    manuscript = (source_root / "manuscript").resolve()

    def ignore(directory: str, names: list[str]) -> set[str]:
        skipped = SKIPPED_EVERYWHERE & set(names)
        if "output" in names and Path(directory).resolve() == manuscript:
            skipped.add("output")
        return skipped

    return ignore


def prepare_project() -> Path:
    """Copy the WHOLE reference repo (the manuscript may reference assets
    outside its dir via ../ paths) and return the manuscript dir of the COPY."""
    source = reference_root()
    root = scratch_root() / "ref"
    if root.exists():
        shutil.rmtree(root)
    root.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, root, symlinks=True, ignore=_copy_filter(source))
    return root / "manuscript"


def engine_command(repo: Path | None = None) -> list[str]:
    """`wongo render` from the given checkout (default: this one)."""
    checkout = (repo or REPO).resolve()
    return ["uv", "run", "--project", str(checkout), "wongo", "render"]


def targets_for(target: str) -> list[str]:
    return ["collab", "submission"] if target == "both" else [target]


def unzip_word_trees(docx: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(str(docx)) as z:
        for name in z.namelist():
            if name.startswith(COMPARED) or name in COMPARED:
                out = dest / name
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(z.read(name))


def render_and_extract(engine: list[str], target: str, dest: Path) -> list[str]:
    """Render a fresh copy of the reference project and unzip every expected
    output into `dest` (replaced, never merged). Returns the document stems."""
    project = prepare_project()
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    stems: list[str] = []
    for t in targets_for(target):
        subprocess.run(engine + ["--target", t, "--project", str(project)],
                       cwd=REPO, check=True)
        expected = [f"main-{t}"]
        if (project / "si.qmd").exists():
            expected.append(f"si-{t}")
        for stem in expected:
            docx = project / "output" / f"{stem}.docx"
            if not docx.exists():
                fail(f"render did not produce {docx.name}; refusing to compare "
                     "a missing or stale output")
            unzip_word_trees(docx, dest / stem)
            stems.append(stem)
    return stems


def tree_files(root: Path, stems: list[str] | None = None) -> dict[str, Path]:
    if not root.exists():
        return {}
    files = {p.relative_to(root).as_posix(): p
             for p in sorted(root.rglob("*")) if p.is_file()}
    if stems is None:
        return files
    wanted = set(stems)
    return {name: p for name, p in files.items() if name.split("/", 1)[0] in wanted}


def diff_trees(a_root: Path, b_root: Path,
               stems: list[str] | None = None) -> dict[str, list[str]]:
    """Return {part-name: diff lines} for differing parts, limited to the given
    document stems when provided. Empty dict means identical. Gating is per
    part (document.xml is one long line), see allowed()."""
    fa, fb = tree_files(a_root, stems), tree_files(b_root, stems)
    report: dict[str, list[str]] = {}
    for name in sorted(set(fa) | set(fb)):
        if name not in fa:
            report[name] = [f"ONLY-IN-CANDIDATE {name}"]
            continue
        if name not in fb:
            report[name] = [f"ONLY-IN-BASELINE {name}"]
            continue
        if not filecmp.cmp(fa[name], fb[name], shallow=False):
            a = fa[name].read_text(encoding="utf-8", errors="replace").splitlines()
            b = fb[name].read_text(encoding="utf-8", errors="replace").splitlines()
            lines = list(difflib.unified_diff(a, b, fromfile=f"baseline/{name}",
                                              tofile=f"candidate/{name}", lineterm=""))
            report[name] = lines or [f"BIN-DIFF {name}"]
    return report


def allowed(report: dict[str, list[str]], patterns: list[re.Pattern]) -> dict[str, list[str]]:
    """Keep only parts whose NAME matches no allowlist pattern."""
    return {n: d for n, d in report.items() if not any(p.search(n) for p in patterns)}


def load_patterns(path: Path | None) -> list[re.Pattern]:
    if path is None:
        return []
    patterns = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            patterns.append(re.compile(line))
    return patterns


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=("baseline", "selftest", "check"))
    ap.add_argument("--target", default="both", choices=("collab", "submission", "both"))
    ap.add_argument("--repo", type=Path, default=None,
                    help="wongo checkout that renders (default: this one)")
    ap.add_argument("--baseline", type=Path, default=None,
                    help="baseline directory (default: <scratch>/baseline)")
    ap.add_argument("--allow", type=Path, default=None,
                    help="file of regex patterns for pre-justified diffs")
    args = ap.parse_args(argv)

    scratch = scratch_root()
    engine = engine_command(args.repo)
    baseline = args.baseline or scratch / "baseline"

    if args.mode == "selftest":
        first = render_and_extract(engine, args.target, scratch / "selftest-a")
        render_and_extract(engine, args.target, scratch / "selftest-b")
        report = diff_trees(scratch / "selftest-a", scratch / "selftest-b", first)
        if report:
            print(f"NOISE FLOOR: {len(report)} differing parts across runs — "
                  "quarto output is NOT deterministic; comparisons need normalization.")
            print("\n".join(sorted(report)[:40]))
            return 1
        print("NOISE FLOOR: zero — consecutive renders are byte-identical.")
        return 0

    if args.mode == "baseline":
        stems = render_and_extract(engine, args.target, baseline)
        count = len(tree_files(baseline))
        print(f"BASELINE stored: {count} parts across {len(stems)} documents "
              f"under {baseline} (target={args.target})")
        return 0

    # mode == check
    if not baseline.is_dir():
        fail(f"no baseline at {baseline}; run `bytecompare.py baseline` first")
    stems = render_and_extract(engine, args.target, scratch / "candidate")
    report = diff_trees(baseline, scratch / "candidate", stems)
    unexplained = allowed(report, load_patterns(args.allow))
    compared = len(tree_files(scratch / "candidate", stems))
    if not unexplained:
        if report:
            print(f"BYTE-COMPARE PASS ({compared} parts compared; {len(report)} raw "
                  f"diffs, all allowlisted: {', '.join(sorted(report))})")
        else:
            print(f"BYTE-COMPARE PASS (identical: {compared} parts across "
                  f"{len(stems)} documents)")
        return 0
    print(f"BYTE-COMPARE FAIL — unexplained diffs in: {', '.join(sorted(unexplained))}")
    for name, lines in sorted(unexplained.items()):
        print(f"\n===== {name} =====")
        print("\n".join(lines[:60]))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
