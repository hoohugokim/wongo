"""`wongo profile verify`: contract lint plus a live drift audit of a profile.

The audit sends an HTTP HEAD to every source URL and flags a Last-Modified date
newer than the profile's verified_date (this caught the 2026-07-30 ES&T
guideline revision). Servers that block bots are reported as [blocked], never
as drift. Text lines go through `emit` exactly as the CLI prints them; the
structured VerifyResult serves --json.
"""
from __future__ import annotations

import ipaddress
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse

from wongo import __version__
from wongo.profiles import (
    find_profile_dir,
    load_profile,
    profile_staleness_days,
    validate_profile,
)

STALE_DAYS = 183


def url_allowed(url: str) -> str | None:
    """Return a rejection reason, or None if the URL is safe to HEAD.

    profile.yml sources resolve project-local first, so an untrusted
    manuscript repo could point verify at arbitrary targets. Restrict to
    http(s) and refuse loopback/private/link-local hosts (best-effort:
    a public DNS name resolving to a private IP is not caught — DNS
    rebinding is out of scope for a drift audit)."""
    u = urlparse(url)
    if u.scheme not in ("http", "https"):
        return f"scheme {u.scheme!r} not allowed (http/https only)"
    host = (u.hostname or "").lower().rstrip(".")
    if not host:
        return "no hostname"
    if host == "localhost" or host.endswith((".local", ".internal")):
        return f"host {host!r} is local"
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return None
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
        return f"host {host} is private/reserved"
    return None


class _SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Refuse redirects that leave the http(s)/public-host envelope."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if url_allowed(str(newurl)) is not None:
            raise urllib.error.URLError(f"redirect to disallowed URL: {newurl}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_opener = urllib.request.build_opener(_SafeRedirectHandler)


def head(url: str, emit: Callable[[str], None], timeout: float = 20.0) -> dict[str, str]:
    bad = url_allowed(url)
    if bad:
        emit(f"  [refused] {bad}: {url}")
        return {"X-Refused": bad}
    req = urllib.request.Request(url, method="HEAD",
                                 headers={"User-Agent": "wongo-profile-verify/" + __version__})
    try:
        with _opener.open(req, timeout=timeout) as resp:
            return dict(resp.headers)
    except urllib.error.HTTPError as e:
        # 403/405: bot-blocked or HEAD-refusing servers (ACS does both) —
        # report distinctly so a block is never mistaken for guideline drift
        return {"X-Blocked": str(e.code)}
    except Exception as e:  # noqa: BLE001  (report ANY failure per-source)
        emit(f"  [{e.__class__.__name__}] {url}")
        return {"X-Error": str(e)}


@dataclass
class SourceCheck:
    url: str
    status: str  # local | ok | revised | blocked | refused | error | invalid-date
    detail: str = ""


@dataclass
class VerifyResult:
    slug: str
    profile_dir: Path
    journal: str
    verified_date: str | None
    days: int | None
    offline: bool
    problems: list[str] = field(default_factory=list)
    sources: list[SourceCheck] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems


def verify_profile(slug: str, *, offline: bool = False,
                   emit: Callable[[str], None] = print) -> VerifyResult:
    pdir = find_profile_dir(slug)
    profile = load_profile(slug)
    days = profile_staleness_days(profile)
    vd = profile.get("verified_date")
    result = VerifyResult(slug=slug, profile_dir=pdir, journal=str(profile.get("journal", "?")),
                          verified_date=str(vd) if vd else None, days=days, offline=offline)
    emit(f"profile:   {pdir}")
    emit(f"journal:   {profile.get('journal', '?')}")
    emit(f"verified:  {profile.get('verified_date', 'NEVER')} "
         f"({days}d ago)" if days is not None else "verified:  NEVER")

    for problem in validate_profile(profile):
        emit(f"CONTRACT: {problem} (docs/journal-profile-contract.md)")
        result.problems.append(f"contract: {problem}")
    if days is None:
        emit("WARN: profile has no verified_date — audit it against the live "
             "guidelines and record the date")
        result.problems.append("no verified_date")
    elif days < 0:
        emit(f"WARN: profile verified_date is {-days} day(s) in the future — "
             "fix the date or system clock")
        result.problems.append("verified_date in the future")
    elif days > STALE_DAYS:
        emit("WARN: profile older than 6 months — re-verify against live guidelines")
        result.problems.append("older than 6 months")

    if offline:
        emit("live sources: skipped (--offline)")
        _emit_verdict(result, emit, "(offline check only)")
        return result

    emit("live sources:")
    vd_dt = datetime.fromisoformat(str(vd)).replace(tzinfo=UTC) if vd else None
    for url in profile.get("sources") or []:
        url = str(url)
        if not url.startswith("http"):
            emit(f"  [local] {url}")
            result.sources.append(SourceCheck(url, "local"))
            continue
        h = head(url, emit)
        if "X-Blocked" in h:
            emit(f"  [blocked {h['X-Blocked']}] server refuses automated HEAD — verify manually: {url}")
            result.sources.append(SourceCheck(url, "blocked", h["X-Blocked"]))
            continue
        if "X-Refused" in h:
            result.sources.append(SourceCheck(url, "refused", h["X-Refused"]))
            result.problems.append(f"refused: {url}")
            continue
        if "X-Error" in h:
            result.sources.append(SourceCheck(url, "error", h["X-Error"]))
            result.problems.append(f"unreachable: {url}")
            continue
        lm = h.get("Last-Modified")
        size = h.get("Content-Length", "?")
        note = ""
        status = "ok"
        if lm and vd_dt:
            try:
                lmdt = parsedate_to_datetime(lm)
                if lmdt is None:
                    raise ValueError("empty parsed date")
            except (TypeError, ValueError):
                emit(f"  [invalid Last-Modified: {lm!r}] {url}")
                result.sources.append(SourceCheck(url, "invalid-date", lm))
                result.problems.append(f"invalid Last-Modified: {url}")
                continue
            if lmdt.tzinfo is None:
                lmdt = lmdt.replace(tzinfo=UTC)
            if lmdt.date().isoformat() > str(vd):
                note = f"  << GUIDELINES REVISED ({lmdt.date()}) AFTER VERIFY DATE — RE-AUDIT CONTENT"
                status = "revised"
                result.problems.append(f"revised {lmdt.date()}: {url}")
        emit(f"  [ok] Last-Modified: {lm or 'none'}  size: {size}{note}")
        if note:
            emit(f"         {url}")
        result.sources.append(SourceCheck(url, status, lm or ""))

    _emit_verdict(result, emit, "")
    return result


def _emit_verdict(result: VerifyResult, emit: Callable[[str], None], suffix: str) -> None:
    if result.problems:
        emit(f"\nVERIFY: {len(result.problems)} issue(s) found — re-fetch and diff content "
             "before trusting this profile")
    else:
        tail = f" {suffix}" if suffix else ""
        emit(f"\nVERIFY: clean — no evidence of guideline drift since verified_date{tail}")
