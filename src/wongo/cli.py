"""wongo CLI — real subcommands (HANDOFF step 5).

Replaces the scaffold-phase runpy delegation into legacy/: render, check,
roundtrip call wongo.engine directly; scaffold copies a starter project;
profile verify is the live-refetch drift audit that caught the 2026-07-30
ES&T guideline revision (Last-Modified newer than the profile's
verified_date). A wheel install now works without a repo checkout.
"""
from __future__ import annotations

import argparse
import shutil
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from wongo import __version__
from wongo.engine import render_project
from wongo.engine.checks import print_report, run_checks


def _cmd_render(args: argparse.Namespace) -> int:
    if args.style:
        # thread the --style override through resolve_style's chain
        import os

        os.environ["WONGO_STYLE"] = args.style
    return render_project(Path(args.project).resolve(), args.target)


def _cmd_check(args: argparse.Namespace) -> int:
    checks = run_checks(Path(args.project).resolve())
    print_report(checks)
    if args.strict and any(c.level == "HARD" and not c.ok for c in checks):
        return 1
    return 0


def _cmd_roundtrip(args: argparse.Namespace) -> int:
    from wongo.engine.roundtrip import main as rt_main

    argv = [args.docx, "--project", args.project]
    return rt_main(argv)


def _cmd_scaffold(args: argparse.Namespace) -> int:
    src = Path(__file__).resolve().parent / "assets" / "scaffold"
    if not (src / "_journal.yml").exists():
        raise SystemExit(f"scaffold template missing next to package: {src}")
    dest = Path(args.dest).resolve()
    if dest.exists() and any(dest.iterdir()):
        raise SystemExit(f"destination not empty: {dest}")
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dest, dirs_exist_ok=True)
    print(f"scaffolded {dest}")
    print("next steps:")
    print("  1. fill in _journal.yml (journal slug + ms_type)")
    print("  2. fill in index.qmd front matter; write ONE SENTENCE PER LINE")
    print("  3. wongo check && wongo render --target collab")
    return 0


def _head(url: str, timeout: float = 20.0) -> dict[str, str] | None:
    req = urllib.request.Request(url, method="HEAD",
                                 headers={"User-Agent": "wongo-profile-verify/" + __version__})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return dict(resp.headers)
    except urllib.error.HTTPError as e:
        # 403/405: bot-blocked or HEAD-refusing servers (ACS does both) —
        # report distinctly so a block is never mistaken for guideline drift
        return {"X-Blocked": str(e.code)}
    except Exception as e:  # noqa: BLE001  (report ANY failure per-source)
        print(f"  [{e.__class__.__name__}] {url}")
        return {"X-Error": str(e)}


def _cmd_profile(args: argparse.Namespace) -> int:
    from wongo.profiles import find_profile_dir, load_profile, profile_staleness_days

    if args.profile_cmd == "list":
        for root in _all_roots():
            for pdir in sorted(root.glob("*")):
                if (pdir / "profile.yml").exists():
                    p = load_profile(pdir.name)
                    print(f"{p.get('slug', pdir.name):16} {p.get('journal', '?'):44} "
                          f"verified: {p.get('verified_date', 'NEVER')}")
        return 0

    slug = args.slug
    pdir = find_profile_dir(slug)
    profile = load_profile(slug)
    days = profile_staleness_days(profile)
    print(f"profile:   {pdir}")
    print(f"journal:   {profile.get('journal', '?')}")
    print(f"verified:  {profile.get('verified_date', 'NEVER')} "
          f"({days}d ago)" if days is not None else "verified:  NEVER")

    problems = 0
    if days is None or days > 183:
        print("WARN: profile older than 6 months — re-verify against live guidelines")
        problems += 1

    if getattr(args, "offline", False):
        print("live sources: skipped (--offline)")
        if problems:
            print(f"\nVERIFY: {problems} issue(s) found — re-fetch and diff content before trusting this profile")
            return 1
        print("\nVERIFY: clean — no evidence of guideline drift since verified_date (offline check only)")
        return 0

    print("live sources:")
    vd = profile.get("verified_date")
    vd_dt = datetime.fromisoformat(str(vd)).replace(tzinfo=timezone.utc) if vd else None
    for url in profile.get("sources") or []:
        if not str(url).startswith("http"):
            print(f"  [local] {url}")
            continue
        h = _head(url)
        if h is None:
            continue
        if "X-Blocked" in h:
            print(f"  [blocked {h['X-Blocked']}] server refuses automated HEAD — verify manually: {url}")
            continue
        if "X-Error" in h:
            problems += 1
            continue
        lm = h.get("Last-Modified")
        size = h.get("Content-Length", "?")
        note = ""
        if lm and vd_dt:
            lmdt = datetime.strptime(lm, "%a, %d %b %Y %H:%M:%S GMT").replace(tzinfo=timezone.utc)
            if lmdt.date().isoformat() > str(vd):
                note = f"  << GUIDELINES REVISED ({lmdt.date()}) AFTER VERIFY DATE — RE-AUDIT CONTENT"
                problems += 1
        print(f"  [ok] Last-Modified: {lm or 'none'}  size: {size}{note}")
        if note:
            print(f"         {url}")

    if problems:
        print(f"\nVERIFY: {problems} issue(s) found — re-fetch and diff content before trusting this profile")
        return 1
    print("\nVERIFY: clean — no evidence of guideline drift since verified_date")
    return 0


def _all_roots():
    from wongo.profiles import _packaged_dir, _repo_root, candidate_dirs

    seen = set()
    out = []
    env = None  # candidate_dirs already includes env/project; list view wants stable roots
    for r in candidate_dirs(env):
        if r not in seen and r.is_dir():
            seen.add(r)
            out.append(r)
    return out


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(
        prog="wongo",
        description="wongo (원고) — Quarto manuscript pipeline: verified journal "
        "profiles, submission-grade DOCX, Word-coauthor round-tripping.",
    )
    parser.add_argument("--version", action="version", version=f"wongo {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("render", help="Render collab- or submission-grade DOCX (main + SI)")
    p.add_argument("--target", required=True, choices=("collab", "submission"))
    p.add_argument("--project", default=".")
    p.add_argument("--style", default=None,
                   help="style profile override (default: _journal.yml style: key)")
    p.set_defaults(fn=_cmd_render)

    p = sub.add_parser("check", help="Run validation checks (word limit, citekeys, crossrefs, figures)")
    p.add_argument("--project", default=".")
    p.add_argument("--strict", action="store_true", help="exit 1 on any HARD failure")
    p.set_defaults(fn=_cmd_check)

    p = sub.add_parser("roundtrip",
                       help="Extract a coauthor DOCX's tracked changes into a merge worksheet")
    p.add_argument("docx")
    p.add_argument("--project", default=".")
    p.set_defaults(fn=_cmd_roundtrip)

    p = sub.add_parser("scaffold", help="Scaffold a new manuscript project")
    p.add_argument("dest", nargs="?", default=".")
    p.set_defaults(fn=_cmd_scaffold)

    p = sub.add_parser("profile", help="Journal profile tools")
    psub = p.add_subparsers(dest="profile_cmd", required=True)
    pv = psub.add_parser("verify", help="Live-refetch drift audit for one profile")
    pv.add_argument("slug")
    pv.add_argument("--offline", action="store_true",
                    help="skip live HEAD checks, only check local staleness")
    pl = psub.add_parser("list", help="List known journal profiles")
    pl.set_defaults(profile_cmd="list")
    pv.set_defaults(profile_cmd="verify")
    p.set_defaults(fn=_cmd_profile)

    args = parser.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
