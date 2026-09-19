"""Focused CLI safety and precedence checks."""

from wongo import profiles
from wongo.cli import _url_allowed, main


def test_url_filter_rejects_trailing_dot_localhost():
    assert _url_allowed("http://localhost./guidelines") is not None


def test_profile_list_deduplicates_override_and_packaged_slug(
    tmp_path, monkeypatch, capsys
):
    roots = [tmp_path / "override", tmp_path / "packaged"]
    for root, journal in zip(roots, ("Preferred copy", "Shadowed copy")):
        profile_dir = root / "demo"
        profile_dir.mkdir(parents=True)
        (profile_dir / "profile.yml").write_text(
            f"slug: demo\njournal: {journal}\nverified_date: 2026-08-30\n",
            encoding="utf-8",
        )
    monkeypatch.setattr(profiles, "candidate_dirs", lambda project=None: roots)

    assert main(["profile", "list"]) == 0

    output = capsys.readouterr().out
    assert output.count("demo") == 1
    assert "Preferred copy" in output
    assert "Shadowed copy" not in output


def test_profile_verify_reports_missing_verified_date_plainly(tmp_path, monkeypatch, capsys):
    root = tmp_path / "root"
    (root / "demo").mkdir(parents=True)
    (root / "demo" / "profile.yml").write_text("slug: demo\njournal: Demo\n", encoding="utf-8")
    monkeypatch.setattr(profiles, "candidate_dirs", lambda project=None: [root])

    assert main(["profile", "verify", "demo", "--offline"]) == 1

    out = capsys.readouterr().out
    assert "no verified_date" in out
    assert "older than 6 months" not in out
