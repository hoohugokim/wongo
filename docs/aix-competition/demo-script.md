# Wongo-AIX 3-Minute Video Demo Script

**Project Title:** Wongo (원고) — Zero-Hallucination LLM Work Surfaces for Verified Scientific Publishing  
**Presenter:** Hoo Hugo Kim (Center for Water Cycle Research, KIST)  
**Target Duration:** 3 minutes (180 seconds)  
**Language:** Bilingual (Korean primary narration with English subtitles / cues)  

---

## Video Production Overview

| Timecode | Scene / Screen Capture | Primary Narration (Korean) | English Subtitle / Visual Cue |
|:---|:---|:---|:---|
| **00:00 - 00:30** | Slide 1 & Split Screen: Quarto `.qmd` vs messy Word Track Changes | "연구자들이 논문을 쓸 때 겪는 가장 큰 고통은 Quarto의 재현성과 공동저자의 워드 '변경 내용 추적' 사이의 괴리입니다. AI에게 수정을 맡기면 코드를 임의로 지우거나 거짓 인용구를 만들어냅니다." | *The Scientific Publishing Dilemma: Markdown reproducibility vs. Word track changes chaos vs. AI hallucinations.* |
| **00:30 - 01:15** | Claude Desktop / Cursor connecting to `wongo mcp run`, calling `wongo_status` & `wongo_check` | "Wongo는 LLM을 위한 네이티브 MCP 서버를 제공합니다. 12개의 결정론적 도구를 통해 저널 프로필을 검증합니다. 검증 실패 시 모호한 에러 대신 정확한 `patch_hint`를 제공하여 AI가 자가 치유할 수 있게 합니다." | *Native MCP Server in action: 12 tools, instant audit, structured self-healing patch hints.* |
| **01:15 - 02:15** | Running `wongo_roundtrip` on `coauthor-edits.docx`, showing tagged rows and calling `wongo_worksheet_batch_propose` | "공동저자가 보낸 워드 수정본을 `wongo_roundtrip`으로 한 번에 추출합니다. Wongo는 인라인 R 코드나 계산값이 손상되지 않도록 의미론적 태그를 부여합니다. AI는 배치 제안을 작성하고, 연구자는 1분 만에 승인합니다." | *Lossless Roundtrip: Semantic tagging protects inline R calculations; batch proposal speeds up review.* |
| **02:15 - 02:45** | Terminal running `wongo_render(target="submission")`, opening resulting Word DOCX with KIST-WCR styling | "HARD 게이트를 통과하면 *Water Research* 규격에 완벽히 부합하는 투고용 DOCX가 생성됩니다. 줄 번호, 북탭 표, Elsevier CSL이 오차 없이 렌더링됩니다." | *Zero-defect Submission Render: Booktabs tables, line numbering, and Elsevier-Harvard citation parity.* |
| **02:45 - 03:00** | Slide 10: Summary & GitHub repository | "Wongo는 연구자의 논문 투고 준비 시간을 3일에서 15분으로 단축합니다. `uv tool install wongo`로 지금 바로 사용하실 수 있습니다. 감사합니다." | *Ready for all KIST researchers: Fast, deterministic, and 100% open-source.* |

---

## Detailed Step-by-Step Screenplay & Narration Cues

### Scene 1: Introduction & The Core Bottleneck (00:00 - 00:30)
- **Visual [Screen]:** Split-screen display.
  - Left: Terminal running Quarto with clean math and inline R code (`index.qmd`).
  - Right: Microsoft Word cluttered with 45 overlapping red tracked changes and comment bubbles.
- **Audio Cue:** Subtle, confident tech background music fades in.
- **Narration (KR):**
  > "KIST 연구원 여러분, 최상위 저널에 논문을 투고할 때 마크다운의 재현성과 선임 교수님의 워드 '변경 내용 추적' 사이에서 밤새워 수작업 하신 적 있으신가요? 
  > 기존 LLM에게 논문 수정을 맡기면 본문의 R 계산 코드를 임의로 덮어쓰거나, 존재하지 않는 가짜 인용구를 만들어내는 치명적인 문제가 있었습니다."

---

### Scene 2: Wongo Native MCP Server in Action (00:30 - 01:15)
- **Visual [Screen]:** Claude Desktop interface with MCP connected (`wongo` server active).
- **Action 1:** Type: *"Please audit the manuscript in `examples/aix-demo` for Water Research submission."*
- **Tool Call Animation:**
  - `wongo_status(project="examples/aix-demo")` $\rightarrow$ returns JSON showing journal: `wr`, style: `kist-wcr`.
  - `wongo_check(project="examples/aix-demo", strict=True)` $\rightarrow$ runs 6 validation checks.
- **Visual Focus:** Zoom in on a failing check with `patch_hint`:
  ```json
  "patch_hint": {
    "action": "add_bibtex",
    "missing_keys": ["park2025"],
    "hint": "Add BibTeX entries for park2025 to refs.bib"
  }
  ```
- **Narration (KR):**
  > "Wongo는 이러한 한계를 극복하기 위해 네이티브 Model Context Protocol(MCP) 서버를 탑재했습니다. 
  > Claude나 Cursor 같은 AI 도구는 Wongo가 제공하는 12개의 도구를 통해 *Water Research*의 공식 투고 규격을 즉시 파악합니다. 
  > 인용구나 단어 수 초과 등 문제가 발견되면 Wongo는 AI에게 정확한 `patch_hint`를 제공하여, 환각 없이 정확한 수정안만을 도출하도록 통제합니다."

---

### Scene 3: Lossless Coauthor Roundtrip & Batch Propose (01:15 - 02:15)
- **Visual [Screen]:** Primary author receives `coauthor-edits.docx` from senior collaborator.
- **Action 2:** Claude calls `wongo_roundtrip(docx_path="examples/aix-demo/from-coauthors/coauthor-edits.docx")`.
- **Tool Call Output:** Shows `merge-20261002-coauthor-edits.md` created with 2 changes.
- **Visual Focus:** Highlight row with semantic tags:
  - `Row 1: replacement 12.4 -> approximately 13.1` (tagged with `inline-code`).
  - Claude explains: *"Row 1 modifies a calculated current density. Proposing `fix-code` to preserve computational reproducibility."*
- **Action 3:** Claude executes `wongo_worksheet_batch_propose`:
  ```json
  [
    {"row": 1, "disposition": "fix-code", "rationale": "update R calculation"},
    {"row": 2, "disposition": "apply", "rationale": "methodological clarity"}
  ]
  ```
- **Narration (KR):**
  > "공동저자가 피드백을 담아 보낸 워드 문서는 `wongo_roundtrip` 도구로 단 1초 만에 무손실 마크다운 워크시트로 추출됩니다. 
  > 특히 Wongo는 변경 사항을 분석하여 인라인 계산 코드를 건드리는지 자동으로 감지합니다. 
  > AI는 계산된 수치를 하드코딩하지 않고 코드 수정을 제안하며, 50개의 수정 사항을 일괄 검토하여 연구자의 승인을 기다립니다."

---

### Scene 4: Zero-Defect Submission Render & Parity (02:15 - 02:45)
- **Visual [Screen]:** Claude executes `wongo_render(target="submission")`.
- **Action 4:** Terminal log displays clean compilation:
  ```bash
  [PASS] HARD word-limit: 1008 words vs limit 8000
  [PASS] HARD citekeys: all citekeys resolve
  [PASS] HARD crossrefs: all cross-references resolve
  [PASS] HARD figures: all referenced figures exist
  wrote output/main-submission.docx
  wrote output/si-submission.docx
  ```
- **Visual Focus:** Open Microsoft Word showing `main-submission.docx`:
  - Double spacing, continuous line numbers (mandated by *Water Research*).
  - Perfect booktabs tables without vertical borders.
  - Formatted Elsevier-Harvard references and separate Supporting Information document.
- **Narration (KR):**
  > "검증을 통과한 원고는 저널 맞춤형 투고 등급 워드 파일로 렌더링됩니다. 
  > 하드 게이트가 걸려 있을 때는 투고용 파일 생성을 원천 차단하여 부실 투고를 방지하며, 규정에 부합하는 줄 번호, 북탭 표, 참고문헌 CSL이 완벽하게 적용됩니다."

---

### Scene 5: Researcher Impact & Open Availability (02:45 - 03:00)
- **Visual [Screen]:** Final slide with terminal installation command and GitHub QR code.
  - `uv tool install wongo`
  - `https://github.com/hoohugokim/wongo`
- **Narration (KR):**
  > "Wongo는 연구자가 포맷팅과 공동저자 피드백 정리에 낭비하던 3일을 단 15분으로 줄여줍니다. 
  > 지금 바로 `uv tool install wongo`로 여러분의 연구실에 도입하십시오. 
  > KIST의 뛰어난 연구 성과가 세계 최고의 저널에 더 빠르고 완벽하게 게재되도록 Wongo가 지원하겠습니다. 감사합니다."

---
*Production notes: Recorded at 1080p60 on macOS Sonoma using OBS Studio and Claude Desktop.*
