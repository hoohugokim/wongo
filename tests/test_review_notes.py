"""Reviewer claims and human dispositions stay separate from observed evidence."""
from __future__ import annotations

import json

import pytest

from wongo import evidence
from wongo.engine import render_project
from wongo.errors import InputError
from wongo.review_notes import add_review_note, record_disposition, review_status


@pytest.fixture(autouse=True)
def _stable_runtime(monkeypatch):
    monkeypatch.setattr(evidence, "engine_identity", lambda: {"version": "test-runtime"})


def _note(project, **kwargs):
    return add_review_note(project, "Ada Reviewer", "Check this wording.",
                           [{"source_file": "index.qmd", "line": 10, "end_line": 12}], **kwargs)


def test_note_is_attributed_claim_with_exact_source_hash(stub_quarto, wongo_project):
    render_project(wongo_project, "submission")
    response = _note(wongo_project, reviewer_identity="claimed@example.org")
    note = response["record"]
    assert note["kind"] == "review-note"
    assert note["result"]["claim_status"] == "unverified"
    assert note["result"]["reviewer"] == "Ada Reviewer"
    assert note["producer"]["identity_authenticated"] is False
    reference = note["result"]["references"][0]
    assert reference["sha256"] == evidence.hash_file(wongo_project / "index.qmd")
    assert evidence.verify_record(wongo_project, note)["state"] == "fresh"
    assert review_status(wongo_project)["notes"][0]["state"] == "fresh"


def test_source_reference_never_copies_raw_data(stub_quarto, wongo_project):
    private = wongo_project / "private-data.txt"
    private.write_text("SECRET ONLY IN INPUT\n", encoding="utf-8")
    render_project(wongo_project, "submission")
    result = add_review_note(wongo_project, "Reviewer", "Please verify the source.",
                             [{"source_file": "private-data.txt", "line": 1}])
    record = result["record"]
    assert "SECRET ONLY IN INPUT" not in json.dumps(record)
    assert record["artifacts"] == [{"path": "private-data.txt", "sha256": evidence.hash_file(private)}]
    assert sorted(evidence.evidence_dir(wongo_project).rglob("*.*")) == [result["path"]]
    private.write_text("CHANGED\n", encoding="utf-8")
    assert evidence.verify_record(wongo_project, record)["state"] == "stale"


@pytest.mark.parametrize("reference", [
    {"source_file": "index.qmd", "line": 0},
    {"source_file": "index.qmd", "line": True},
    {"source_file": "index.qmd", "line": 10, "end_line": 9},
    {"source_file": "index.qmd", "line": 999},
    {"source_file": "../outside.txt", "line": 1},
    {"source_file": "index.qmd", "line": 1, "artifact": "refs.bib", "pointer": "/"},
    {"artifact": "missing.json", "pointer": "/"},
    {"artifact": "refs.bib", "pointer": "unsupported-location"},
])
def test_invalid_references_create_no_note(stub_quarto, wongo_project, reference):
    render_project(wongo_project, "submission")
    with pytest.raises(InputError):
        add_review_note(wongo_project, "Reviewer", "A claim.", [reference])
    assert evidence.load_records(wongo_project, "review-note") == []


def test_json_pointer_and_docx_member_are_validated(stub_quarto, wongo_project):
    data = wongo_project / "facts.json"
    data.write_text('{"a/b": [{"value": 12.4}]}', encoding="utf-8")
    render_project(wongo_project, "submission")
    output = next((wongo_project / "output").glob("*-submission.docx"))
    artifact = output.relative_to(wongo_project).as_posix()
    response = add_review_note(wongo_project, "Reviewer", "Review these locations.", [
        {"artifact": "facts.json", "pointer": "/a~1b/0/value"},
        {"artifact": artifact, "pointer": "word/document.xml#xpath=/w:document/w:body/w:p[1]"},
    ])
    assert len(response["record"]["result"]["references"]) == 2
    for bad in ("/a~1b/9/value", "/a~2b", "/a~1b/-1/value"):
        with pytest.raises(InputError, match="pointer"):
            add_review_note(wongo_project, "Reviewer", "Claim.", [{"artifact": "facts.json", "pointer": bad}])
    for bad in ("missing.xml", "word/document.xml#xpath=/w:document/w:missing"):
        with pytest.raises(InputError, match="pointer|member"):
            add_review_note(wongo_project, "Reviewer", "Claim.", [{"artifact": artifact, "pointer": bad}])


def test_whole_artifact_pointer_can_name_preview_image(stub_quarto, wongo_project):
    render_project(wongo_project, "submission")
    preview = wongo_project / "output" / "page-1.png"
    preview.write_bytes(b"page bytes")
    note = add_review_note(wongo_project, "Reviewer", "The page needs attention.",
                           [{"artifact": "output/page-1.png", "pointer": "/"}])["record"]
    assert note["artifacts"][0]["sha256"] == evidence.hash_file(preview)


def test_disposition_requires_deliberate_confirmation_and_preserves_claim(stub_quarto, wongo_project):
    render_project(wongo_project, "submission")
    note = _note(wongo_project)["record"]
    for confirmed in (False, 1, "yes"):
        with pytest.raises(InputError, match="human confirmation"):
            record_disposition(wongo_project, note["record_id"], "accept", "Maintainer", "Reviewed.",
                               confirmed=confirmed)
    response = record_disposition(wongo_project, note["record_id"], "accept", "Maintainer", "Reviewed.",
                                  confirmed=True)
    disposition = response["record"]
    assert disposition["kind"] == "review-disposition"
    assert disposition["result"]["review_note_id"] == note["record_id"]
    assert disposition["producer"]["mechanism"] == "local-human-attestation"
    assert disposition["producer"]["identity_authenticated"] is False
    assert evidence.load_records(wongo_project, "review-note")[0]["result"]["claim_status"] == "unverified"
    summary = review_status(wongo_project)
    assert summary["notes"][0]["dispositions"][0]["decision"] == "accept"
    assert "ready" not in summary and "scientifically_valid" not in summary


@pytest.mark.parametrize("decision", ["reject", "needs-work"])
def test_disposition_vocabulary(stub_quarto, wongo_project, decision):
    render_project(wongo_project, "submission")
    note = _note(wongo_project)["record"]
    response = record_disposition(wongo_project, note["record_id"], decision, "Maintainer", "Explanation.",
                                  confirmed=True)
    assert response["record"]["result"]["decision"] == decision


def test_stale_or_missing_notes_cannot_receive_current_disposition(stub_quarto, wongo_project):
    render_project(wongo_project, "submission")
    note = _note(wongo_project)["record"]
    source = wongo_project / "index.qmd"
    source.write_text(source.read_text(encoding="utf-8") + "\nChanged.\n", encoding="utf-8")
    render_project(wongo_project, "submission")
    with pytest.raises(InputError, match="stale"):
        record_disposition(wongo_project, note["record_id"], "accept", "Maintainer", "Reviewed.", confirmed=True)
    with pytest.raises(InputError, match="missing"):
        record_disposition(wongo_project, "0" * 64, "accept", "Maintainer", "Reviewed.", confirmed=True)
    assert review_status(wongo_project)["notes"][0]["state"] == "stale"
    assert evidence.load_records(wongo_project, "review-disposition") == []


def test_disposition_stales_if_referenced_note_deleted(stub_quarto, wongo_project):
    render_project(wongo_project, "submission")
    note = _note(wongo_project)
    disposition = record_disposition(wongo_project, note["record"]["record_id"], "accept", "Maintainer",
                                      "Reviewed.", confirmed=True)["record"]
    note["path"].unlink()
    assert evidence.verify_record(wongo_project, disposition)["state"] != "fresh"


def test_review_claims_and_dispositions_do_not_change_readiness(stub_quarto, wongo_project):
    from wongo.gates import readiness

    render_project(wongo_project, "submission")
    before = readiness(wongo_project)
    note = _note(wongo_project)["record"]
    record_disposition(wongo_project, note["record_id"], "accept", "Maintainer", "Reviewed.", confirmed=True)
    assert readiness(wongo_project) == before
