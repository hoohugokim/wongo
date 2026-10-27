"""Adapter acceptance: explicit execution, exact receipts, and independent status axes."""
from __future__ import annotations

import asyncio
import json
import os
import shutil
from pathlib import Path

import pytest
import yaml

from wongo.engine import render_project
from wongo.evidence import snapshot
from wongo.mcp.server import create_mcp_server
from wongo.status import project_status


def _configure(project):
    cfg_path = project / "_journal.yml"
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    cfg.update(manual_gates=[{"id": "release", "label": "Author release"}], demonstration=True,
               audits=[{"id": "value", "script": "audit.py", "required": True}])
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    report = {"assertions": [{"id": "one", "ok": True, "detail": "One scoped observation.",
                               "source": "index.qmd:8", "artifact": "value#/one",
                               "rendered_context": "Exact test paragraph"}],
              "coverage": {"checked": ["one"], "untested": ["everything else"]}}
    (project / "audit.py").write_text(
        "import os,json\nfrom pathlib import Path\nprint('DIAGNOSTIC ONLY')\n"
        f"Path(os.environ['WONGO_AUDIT_RESULT']).write_text(json.dumps({report!r}))\n",
        encoding="utf-8")


def test_cli_json_and_mcp_share_scoped_audits_and_pending_author_state(
        stub_quarto, wongo_project, cli, tmp_path):
    _configure(wongo_project)
    render_project(wongo_project, "submission")
    code, out, err = cli("audit", "--project", str(wongo_project), "--json")
    assert code == 0 and json.loads(out)["ok"]
    assert "DIAGNOSTIC ONLY" in err and "DIAGNOSTIC ONLY" not in out
    before = snapshot(wongo_project)

    async def workflow():
        server = create_mcp_server()
        async def call(name, **kwargs):
            res = await server.call_tool(name, kwargs)
            assert not res.is_error
            return res.structured_content
        result = await call("wongo_audit", project=str(wongo_project))
        assert result["ok"] and result["records"][0]["coverage"]["untested"] == ["everything else"]
        direct = project_status(wongo_project)
        status = await call("wongo_status", project=str(wongo_project))
        for field in ("technical", "audit", "visual", "author_decisions", "submission_approved"):
            assert status[field] == getattr(direct, field)
        assert status["technical"]["state"] == "passed"
        assert status["audit"]["state"] == "passed"
        assert status["author_decisions"]["state"] == "not-recorded"
        assert not status["submission_approved"]
        proposal = await call("wongo_gate_propose", project=str(wongo_project), gate="release")
        assert proposal["ok"]
        assert not (await call("wongo_status", project=str(wongo_project)))["submission_approved"]
        archive = tmp_path / "review.zip"
        exported = await call("wongo_review_export", project=str(wongo_project), destination=str(archive), outputs=True)
        assert exported["ok"]
        verified = await call("wongo_review_verify", file=str(archive))
        assert verified["ok"]
    asyncio.run(workflow())
    assert snapshot(wongo_project)["id"] == before["id"]


@pytest.mark.skipif(os.environ.get("WONGO_REAL_QUARTO_TEST") != "1", reason="opt-in real Quarto/R")
def test_real_evidence_demo_render_and_contextual_audit(tmp_path):
    from wongo.audit import run_audits
    from wongo.qa import inspect_outputs
    from wongo.review_export import export_review, verify_bundle

    project = tmp_path / "pilot"
    shutil.copytree(Path(__file__).parents[1] / "examples/evidence-demo", project)
    render_project(project, "submission")
    audited = run_audits(project)
    assert audited["ok"], audited["records"][0]["result"]
    assert inspect_outputs(project)["ok"]
    status = project_status(project)
    assert status.technical["state"] == status.audit["state"] == "passed"
    assert status.visual["state"] == status.author_decisions["state"] == "not-recorded"
    assert not status.submission_approved
    if os.environ.get("WONGO_REAL_QA_TEST") == "1":
        from wongo.qa import create_preview

        preview = create_preview(project, dpi=72)
        assert preview["record"]["result"]["representation"] == "converted-layout-preview"
        status = project_status(project)
        assert status.visual["state"] == "not-recorded" and not status.submission_approved
    export_review(project, tmp_path / "pilot.zip", include_outputs=True,
                   include_artifacts=os.environ.get("WONGO_REAL_QA_TEST") == "1")
    assert verify_bundle(tmp_path / "pilot.zip")["ok"]


def test_claim_and_human_disposition_cli_json(stub_quarto, wongo_project, cli, tmp_path, monkeypatch):
    from wongo import clitools
    from wongo.evidence import load_records

    render_project(wongo_project, "submission")
    refs = tmp_path / "references.json"
    refs.write_text(json.dumps([{"source_file": "index.qmd", "line": 8}]), encoding="utf-8")
    code, out, err = cli("evidence", "note", "--project", str(wongo_project), "--reviewer", "Reviewer",
                         "--statement", "Check this interpretation", "--references", str(refs), "--json")
    assert code == 0 and not err
    note = json.loads(out)["record"]
    assert note["kind"] == "review-note" and note["result"]["claim_status"] == "unverified"
    args = ("evidence", "disposition", note["record_id"], "--project", str(wongo_project),
            "--decision", "needs-work", "--maintainer", "Author", "--reason", "Needs context", "--json")
    monkeypatch.setattr(clitools, "is_interactive", lambda: False)
    code, out, _ = cli(*args)
    assert code == 1 and not json.loads(out)["ok"]
    assert not load_records(wongo_project, "review-disposition")
    monkeypatch.setattr(clitools, "is_interactive", lambda: True)
    monkeypatch.setattr("builtins.input", lambda: "1")
    code, out, err = cli(*args)
    assert code == 0
    assert json.loads(out)["record"]["kind"] == "review-disposition"
    assert "Check this interpretation" in err
    assert not project_status(wongo_project).submission_approved
