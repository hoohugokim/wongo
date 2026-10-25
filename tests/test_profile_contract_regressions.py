"""Profiles reject invalid checker configuration before arithmetic or comparison."""
from __future__ import annotations

import json
from datetime import date

import pytest
import yaml

from wongo.engine.checks import run_checks
from wongo.errors import ConfigError
from wongo.profiles import manuscript_type, validate_profile


def _profile(**options):
    return {
        "slug": "demo", "journal": "Demo", "sources": ["https://example.org"],
        "verified_date": date.today().isoformat(),
        "manuscript_types": [{"type": "article", "word_limit": 500}],
        **options,
    }


@pytest.mark.parametrize("field", ["count", "count_general"])
@pytest.mark.parametrize("value", [
    ["three", "five"], [5, 3], [-1, 5], [True, 5], [3], 3, [], None,
])
def test_invalid_highlights_ranges_fail_lint_and_runtime(field, value, wongo_project):
    highlights = {"required": True, field: value}
    profile = _profile(highlights=highlights)
    assert any(f"highlights.{field}" in item for item in validate_profile(profile))

    path = wongo_project / "profiles" / "demo" / "profile.yml"
    path.write_text(yaml.safe_dump(profile), encoding="utf-8")
    (wongo_project / "highlights.md").write_text("- One\n- Two\n- Three\n", encoding="utf-8")
    with pytest.raises(ConfigError, match=f"highlights[.]{field}"):
        run_checks(wongo_project)


@pytest.mark.parametrize("value", [True, 0, -1, "three", [3], None])
def test_invalid_making_waves_count_fails_lint_and_runtime(value):
    profile = _profile(highlights={"required": True, "count_making_waves": value})
    assert any("highlights.count_making_waves" in item for item in validate_profile(profile))
    with pytest.raises(ConfigError, match="highlights[.]count_making_waves"):
        manuscript_type(profile, "article")


@pytest.mark.parametrize("field", ["abstract_min", "abstract_limit", "max_display_items"])
@pytest.mark.parametrize("value", [True, -1, "200", 1.5])
def test_numeric_type_rules_are_validated_when_used(field, value, wongo_project):
    profile = _profile()
    profile["manuscript_types"][0][field] = value
    assert any(field in item for item in validate_profile(profile))
    path = wongo_project / "profiles" / "demo" / "profile.yml"
    path.write_text(yaml.safe_dump(profile), encoding="utf-8")
    with pytest.raises(ConfigError, match=field):
        run_checks(wongo_project)


def test_inverted_abstract_bounds_are_rejected_at_use_time():
    profile = _profile()
    profile["manuscript_types"][0].update(abstract_min=200, abstract_limit=150)
    with pytest.raises(ConfigError, match="abstract_min exceeds abstract_limit"):
        manuscript_type(profile, "article")


def test_invalid_highlights_return_one_actionable_json_error(cli, wongo_project):
    profile = _profile(highlights={"required": True, "count": ["three", "five"]})
    path = wongo_project / "profiles" / "demo" / "profile.yml"
    path.write_text(yaml.safe_dump(profile), encoding="utf-8")
    code, stdout, _ = cli("check", "--project", str(wongo_project), "--json")
    result = json.loads(stdout)
    assert code == 1 and result["ok"] is False
    assert result["error"]["kind"] == "config"
    assert "highlights.count" in result["error"]["message"]
    assert "profile.yml" in result["error"]["message"]


@pytest.mark.parametrize("highlights", [
    None,
    {"required": False},
    {"required": True, "count": [0, 0]},
    {"required": True, "count_general": [3, 5], "count_making_waves": 3},
])
def test_valid_optional_highlights_keep_their_existing_contract(highlights):
    profile = _profile(highlights=highlights)
    assert validate_profile(profile) == []
    assert manuscript_type(profile, "article") is profile["manuscript_types"][0]
