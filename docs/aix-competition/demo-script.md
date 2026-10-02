# Wongo-AIX three-minute demo script

**Presenter:** Hoo Hugo Kim, Center for Water Cycle Research, KIST

**Working title:** Verified manuscript tools for LLM-assisted review

**Recording plan:** Korean narration with English captions; capture actual outputs.

**Visual treatment:** Follow the [Wongo design system](../../brand/README.md)
for title cards and captions. Place the [bilingual lockup](../../brand/logos/wongo-lockup.svg)
on white, or its [reverse variant](../../brand/logos/wongo-lockup-reverse.svg)
on ink `#21313D`, retaining the artwork's clear space. Use Source Serif 4 for
English titles, Source Sans 3 for English captions and Noto Sans KR for Korean
text. Keep captions in ink on white and petrol `#416C78` for restrained emphasis.
Use opening and closing cards for branding; keep captured code, checks and
journal DOCX pages readable in their original appearance.

## Before recording

Use a current `main` checkout containing the v0.3.1 source. The latest tagged
release is v0.3.0; a v0.3.1 release tag and PyPI publication are pending. From the
repository root:

```fish
uv sync --all-extras
uv run wongo doctor --project examples/aix-demo
uv run python tools/aix_eval.py
uv run wongo mcp install --client vscode --project examples/aix-demo
```

Open the demo project in VS Code and enable the configured MCP server. Check its
tool list before recording. The
[main source archive](https://github.com/hoohugokim/wongo/archive/refs/heads/main.zip)
also includes the MCP integration; use the checkout above to run the benchmark
and regenerate the demo fixtures.

The manuscript, measurements, figure and coauthor edits are synthetic examples,
not KIST experimental results. The fixture contains exactly two tracked edits:
row 1 inserts a methods clarification; row 2 replaces an R-generated current
density. Regenerate it with `uv run python examples/aix-demo/generate_coauthor_fixture.py`
if the manuscript changes. Use the returned worksheet path and URI; dates and
source line numbers may change. `scorecard.md` records this machine's latest
benchmark results; do not substitute rehearsed timings or pass labels.

## 00:00–00:25 — Source and Word review

Show `index.qmd`, its inline R expression, and `coauthor-edits.docx` in Word.

> **KR:** “재현 가능한 Quarto 원고를 작성해도 공동저자는 Word의 변경 내용 추적으로
> 의견을 줍니다. Wongo는 이 두 작업 방식을 연결하고, AI의 수정 제안을 연구자가
> 검토할 수 있는 기록으로 남깁니다. 화면의 데이터는 시연용 합성 데이터입니다.”

**Caption:** Quarto source → Word review → an auditable decision worksheet.

## 00:25–01:05 — Audit and a bounded repair hint

Call `wongo_status(project="<absolute demo path>")`, then
`wongo_check(project="<absolute demo path>", strict=True)`.
Show the actual checks, including the warning that the WR reference-inclusive
word count is finalized during submission rendering.

In a scratch copy, append `A demonstration defect [@ghostCite2029].` to the
manuscript and rerun the check. Highlight the returned `add_bibtex` patch hint.
Explain that the researcher must verify a real reference or remove the invalid
citation; a missing-key hint does not establish that a paper exists.
Return to the clean project for the rest of the recording.

> **KR:** “검증 도구는 누락된 인용 키처럼 확인 가능한 문제와 수정 범위를 알려줍니다.
> AI가 제안한 참고문헌의 실재 여부와 과학적 타당성은 연구자가 확인해야 합니다.”

**Caption:** Structured evidence bounds the repair; scientific judgment remains with the author.

## 01:05–02:05 — Extract, propose, and decide

Call `wongo_roundtrip` with both the fixture's absolute `docx_path` and the
absolute `project` path. Read its returned `worksheet_uri` and call
`wongo_worksheet_status(file="<returned worksheet path>")`.

Show the measured rows:

| Row | Tracked edit | Source-aware tag | Proposed decision |
|:---|:---|:---|:---|
| 1 | Insert “under steady-state potentiostatic polarization” | None | `apply` after methodological review |
| 2 | Replace `12.4` with “approximately 13.1” | `inline-code` | `fix-code` pending verification of the calculation |

Call `wongo_worksheet_batch_propose` using that file and these proposals:

```json
[
  {"row": 1, "disposition": "apply", "rationale": "methodological clarification; author must confirm accuracy"},
  {"row": 2, "disposition": "fix-code", "rationale": "inspect the R calculation before changing its generated value"}
]
```

Show that both rows remain proposals and lint requires decisions. Demonstrate
explicit author confirmation in `wongo review`, then lint again. No manuscript
edit is applied by Wongo. Do not approve real research changes for the recording.

> **KR:** “Word에는 계산식 대신 결과 숫자만 남습니다. Wongo는 연결된 원고의 소스도
> 확인해 인라인 계산이 포함된 줄을 표시합니다. AI는 제안만 기록하고, 연구자가
> 승인하거나 바꿉니다. 승인 기록을 남겨도 Wongo가 원고를 자동 수정하지는 않습니다.”

**Caption:** Source-aware tags flag review risks; proposals require author decisions.

## 02:05–02:40 — Submission output and refusal evidence

Call `wongo_render(project="<absolute demo path>", target="submission")`.
Open the returned main and SI DOCX paths. Water Research submission output must
**omit line numbering**; the kist-wcr collaboration output may retain it. Show
references and tables without claiming complete journal compliance from those
visual checks alone.

Show the current scorecard's gate result: the benchmark injects an invalid
citation into a scratch copy, requires the expected `GateError`, and compares
hashes of existing outputs and their manifest before and after the refusal.
Render parity against a previous release is a separate `tools/bytecompare.py`
check, not a claim made by this demo benchmark.

> **KR:** “투고용 렌더링은 새로 생성한 참고문헌까지 포함해 단어 수를 검사합니다.
> Water Research 규정에 따라 투고 파일의 줄 번호는 제거합니다. 시연 검증에서는
> 잘못된 인용을 넣었을 때 기존 출력과 검증 기록이 보존되는지도 확인합니다.”

## 02:40–03:00 — Evidence and availability

Show the generated scorecard with its timestamp and pass/fail results, then the
repository URL. State that this is a development preview and invite a pilot
with real coauthor workflows. Do not claim measured time savings, zero
hallucinations, or performance beyond the tested fixture.

> **KR:** “현재 결과는 이 합성 원고를 이용한 회귀 검증입니다. 실제 연구자의 시간
> 절감 효과는 앞으로 측정할 계획입니다. 개발 버전의 설치와 재현 절차는 저장소에
> 있습니다. 감사합니다.”

**Caption:** [Source and setup](https://github.com/hoohugokim/wongo) · development preview.
