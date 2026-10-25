# F5–F8 implementation and acceptance audit

2026-10-23. Implements the separately authorized five-increment plan recorded in
[the contract](T-0040-evidence-contract.md). HEAD remains `8590fe3`; every change
in this cycle is uncommitted. The commit itself does not contain these fixes or
interfaces. The prior accepted F1–F4 review closure remains
[T-0039](T-0039-review-closure.md).

## Acceptance coverage

| Scope | Implementation and exercised evidence |
|---|---|
| F5 execution | `audit.py` explicitly runs configured scripts on allowlisted scratch inputs and sealed outputs. Script, input, runtime/executable, build and result identities are recorded; status/check/render never execute them. Mutation, live drift, timeout and malformed reports refuse receipts. |
| F5 contextual values | `audit_helpers.py` and `test_audit_helpers.py` cover absent keys, empty scalars, null policy, ordinary NA prose, finite values, swapped table cells, wrong paragraph and wrong sentence in the same paragraph, numeric signs/exponents, reordered/deleted images, unique anchors and stale receipts. Coverage lists checked assertions and untested areas. |
| F6 final structure | `qa.py` inventories final OOXML, including embedded image identity/descriptions, captions, tables, OMML, revisions, superscripts and text identity. Tests include long captions, populated nine-column multipage tables, thin/nonbreaking spaces, drawing and VML alt text, footnotes, and alt removal by a registered transform. |
| F6 preview and inspection | Actual LibreOffice/Poppler generated PDF/page PNG artifacts from synthetic main/SI without changing DOCX. Receipts distinguish native OOXML, converted preview, extracted-text identity and native Word human attestation. Carry tests require renderer/version/settings/page hashes and preserve original attribution; changed/omitted pages remain visible. |
| F7 identity | `evidence.py` binds declared inputs, profile/style/assets, tool versions, final outputs and editable Python source hashes. Same-version source edits differ; dirty/clean alone does not stale evidence. Concurrent source saves and storage symlink escapes are rejected. |
| F7 portable review | `review_export.py` enforces explicit file selection, current output/subject bindings, artifact hashes, record-reference closure, visible omissions and separate referenced historical provenance. Raw dependencies/credentials are not copied automatically. Default inventory records omit full manuscript extraction. |
| F7 review and normalization | `review_notes.py` and CLI record unverified attributed claims with validated hashed source lines/JSON/OPC pointers; human dispositions are separate and never approve author gates. DOCX core dates and PDF Info dates have narrow documented normalization; raw hashes remain and cell/field/alt/scientific changes still differ. |
| F8 readiness | `gates.py`, `status.py`, CLI and MCP expose technical, audit, visual and author axes. Agent proposals never approve; confirmation binds a human attribution to exact build/gate definitions. Stale/invalid/missing records, incomplete page inspections and pending coauthor rows cannot imply release. Demonstration projects are labeled. |

## Verification run

- Full suite with `WONGO_REAL_QUARTO_TEST=1`: **953 passed, 4 skipped** in 206.19 s.
- Subsequent final audit found collaboration authorization could be described as
  submission approval in the direct readiness API. A submission-target guard and
  regression fixed it; **39 gate tests passed** after this final code change.
- Optional real QA fixture with `WONGO_REAL_QA_TEST=1`: **1 passed** in 7.44 s.
- Full real synthetic pilot with both opt-ins: **1 passed** in 7.28 s, covering
  Quarto/R → contextual audit → final OOXML → LibreOffice/Poppler → export/verify.
- Installed LibreOffice conversion required host execution outside the sandbox;
  all conversions used synthetic temporary files and an isolated renderer profile.
- AIX real stdio benchmark: **4/4 dimensions passed**, 21 tools; measured receipt
  is [T-0040-aix-scorecard.md](T-0040-aix-scorecard.md). The existing dirty scorecard
  was preserved.
- Fresh synthetic real-Quarto parity vs `8590fe3`: **52 parts identical** across
  main/SI and collab/submission, including document/styles/settings; generated SI
  table reorder changes displayed numbers correctly. Scratch receipt:
  `/private/var/folders/8_/rh35ssj92h173ngj0pp8v6cr0000gn/T/wongo-f1-f4-acceptance-y75mw_ej/receipt.json`.
- Wheel/sdist build, changed-file Ruff, version/profile CLI smokes and whitespace
  checks passed. Full Ruff reports only the existing worksheet.py:1129 E713,
  deliberately preserved. Ledger check passed before final handoff update.

Integration checks and two independent final reviews reproduced and closed: missing MCP status fields
and SDK structured results; export/output-subject mismatch; full manuscript text
in default inspection export; snapshot race; evidence storage symlink escape;
malformed evidence shapes; paragraph sentence and signed-number false passes.
The narrow false-pass regressions are behavioral, not claims of scientific truth.

## Preservation and limits

The initial SHA inventory contained 210 pre-existing dirty files. All remain;
203 are byte-identical after the final handoff/task update. The five necessary integration
deltas were `cli.py`, `engine/inputs.py`, `mcp/tools.py`, `test_mcp.py` and
`tools/aix_eval.py`; the other two changed files are the shared task/handoff
ledgers. Worksheet, five new profiles, research, AIX scorecard
and agent-state contents were preserved. No staging, commit, push, installation,
private scientific data access or accepted-manuscript changes occurred.

Native Microsoft Word pagination, a real Windows/Korean-account pilot and private
reference-manuscript parity remain unperformed. `WONGO_REF_PROJECT` is unset.
Converted previews are not Word certification; recorded decisions are local
human attestations, not authenticated signatures. This implements and verifies
the optional interfaces using synthetic fixtures; it authorizes no submission.

The next implementation outside F5–F8 can be a narrow opt-in main-to-SI reference
interface using rendered SI labels/order, as excluded from D-0016. It needs its
own design decision and generated-float fixtures. Release work first needs the
existing private parity and native Windows/Word checks.
