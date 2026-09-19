"""Profile contract enforcement: `wongo profile verify` lints profile.yml
against docs/journal-profile-contract.md before trusting its numbers."""
from datetime import date
from pathlib import Path

import pytest
import yaml

from wongo.profiles import validate_profile

GOOD = {
    "journal": "Demo", "slug": "demo", "publisher": "P",
    "manuscript_types": [{"type": "article", "word_limit": 100, "counting_rule": "r"}],
    "sources": ["https://example.org/guide"], "verified_date": date(2026, 1, 1),
    "toc_graphic": {"required": False}, "si": {"separate_file": True},
}


def test_good_profile_has_no_problems():
    assert validate_profile(GOOD) == []


@pytest.mark.parametrize("missing", ["journal", "slug", "manuscript_types", "sources", "verified_date"])
def test_missing_required_key_is_reported(missing):
    profile = {k: v for k, v in GOOD.items() if k != missing}
    problems = validate_profile(profile)
    assert any(missing in p for p in problems), problems


def test_manuscript_type_without_type_or_limit_is_reported():
    profile = dict(GOOD, manuscript_types=[{"word_limit": 5}, {"type": "x"}])
    problems = validate_profile(profile)
    assert any("type" in p for p in problems)
    assert any("word_limit" in p for p in problems)


def test_toc_graphic_block_without_required_key_is_reported():
    profile = dict(GOOD, toc_graphic={"width_mm": 80})
    assert any("toc_graphic.required" in p for p in validate_profile(profile))


def test_unknown_line_numbers_value_is_reported():
    profile = dict(GOOD, line_numbers="sometimes")
    assert any("line_numbers" in p for p in validate_profile(profile))


def test_verified_date_must_be_a_date():
    profile = dict(GOOD, verified_date="soon")
    assert any("verified_date" in p for p in validate_profile(profile))


@pytest.mark.parametrize("pdir", sorted(Path("src/wongo/profiles").glob("*/profile.yml")))
def test_every_shipped_profile_satisfies_the_contract(pdir):
    profile = yaml.safe_load(pdir.read_text(encoding="utf-8"))
    assert validate_profile(profile) == []


def test_profile_verify_offline_fails_on_contract_violation(tmp_path, monkeypatch, capsys):
    from wongo import profiles
    from wongo.cli import main

    root = tmp_path / "root"
    (root / "demo").mkdir(parents=True)
    (root / "demo" / "profile.yml").write_text(
        "slug: demo\njournal: Demo\nverified_date: 2026-09-01\nsources: [https://example.org]\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(profiles, "candidate_dirs", lambda project=None: [root])
    assert main(["profile", "verify", "demo", "--offline"]) == 1
    assert "manuscript_types" in capsys.readouterr().out
