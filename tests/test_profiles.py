"""Profile and _journal.yml loading: every failure is an actionable ConfigError."""
from __future__ import annotations

import pytest

from wongo import profiles
from wongo.errors import ConfigError, WongoError


def test_missing_journal_config_points_to_scaffold(tmp_path):
    with pytest.raises(ConfigError) as excinfo:
        profiles.load_journal_config(tmp_path)
    assert "wongo scaffold" in str(excinfo.value)


def test_invalid_journal_yaml_names_the_file(tmp_path):
    (tmp_path / "_journal.yml").write_text("journal: [unclosed\n", encoding="utf-8")
    with pytest.raises(ConfigError) as excinfo:
        profiles.load_journal_config(tmp_path)
    assert "_journal.yml" in str(excinfo.value)


def test_unknown_profile_is_a_config_error_pointing_to_the_list(tmp_path):
    with pytest.raises(ConfigError) as excinfo:
        profiles.load_profile("no-such-journal", tmp_path)
    assert "wongo profile list" in str(excinfo.value)


def test_unknown_manuscript_type_lists_the_known_ones():
    profile = {"slug": "demo", "manuscript_types": [{"type": "article"}, {"type": "review"}]}
    with pytest.raises(ConfigError) as excinfo:
        profiles.manuscript_type(profile, "letter")
    assert "article, review" in str(excinfo.value)


def test_config_errors_are_ordinary_exceptions():
    assert issubclass(ConfigError, WongoError)
    assert issubclass(WongoError, Exception)
    assert not issubclass(WongoError, SystemExit)


def test_list_profiles_prefers_the_first_root_for_a_slug(tmp_path, monkeypatch):
    roots = [tmp_path / "override", tmp_path / "packaged"]
    for root, journal in zip(roots, ("Preferred", "Shadowed")):
        (root / "demo").mkdir(parents=True)
        (root / "demo" / "profile.yml").write_text(
            f"slug: demo\njournal: {journal}\nverified_date: 2026-09-01\n", encoding="utf-8")
    monkeypatch.setattr(profiles, "candidate_dirs", lambda project=None: roots)

    listed = profiles.list_profiles()

    assert [(p["slug"], p["journal"]) for p in listed] == [("demo", "Preferred")]
