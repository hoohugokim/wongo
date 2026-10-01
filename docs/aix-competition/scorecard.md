# Wongo-AIX Benchmark & Evaluation Scorecard

**Evaluated Version:** Wongo v0.3.1  
**Evaluation Date:** 2026-10-01 19:02:53 UTC  
**Target Manuscript:** `examples/aix-demo` (*Water Research*, `wr` profile, `kist-wcr` house style)

---

## Executive Summary

| AIX Evaluation Dimension | Status | Key Metric | Target Benchmark | Result |
|:---|:---:|:---|:---:|:---:|
| **1. Tool & Resource Discovery** | `PASS` | Total MCP Tools Registered | 12 tools | **12 tools (0.0 ms)** |
| **2. Pre-Submission Audit & Patch Hints** | `PASS` | Actionable Remediation Accuracy | 100% | **100% (6/7 checks passed)** |
| **3. Coauthor Roundtrip & Batch Review** | `PASS` | Lossless Change Extraction & Tags | $\ge 2$ changes | **2 changes (951.39 ms)** |
| **4. Strict Gate & Parity Enforcement** | `PASS` | HARD Submission Gate Enforcement | Block invalid renders | **PASS (zero unverified leaks)** |

---

## 1. Tool & Resource Discovery

- **MCP Protocol Conformance:** Model Context Protocol (MCP 2.x standard)
- **Discovery Latency:** `0.0 ms`
- **Exposed Tools (12):**
  `wongo_check, wongo_diff, wongo_doctor, wongo_profile_get, wongo_render, wongo_roundtrip, wongo_scaffold, wongo_status, wongo_worksheet_batch_propose, wongo_worksheet_lint, wongo_worksheet_set, wongo_worksheet_status`
- **Exposed Prompts (3):**
  `wongo-coauthor-review, wongo-pre-submission-audit, wongo-revision-diff`
- **Exposed Resources:** Dynamic project status (`wongo://project/status`), journal profile rules (`wongo://profile/{slug}`), and merge worksheets (`wongo://worksheet/{path}`).

## 2. Pre-Submission Audit & Actionable Patch Hints

Wongo never leaves an LLM or researcher with a vague failure message. Every failing check emits a structured `patch_hint` with exact guidance:

| Defect Tested | HARD Gate Name | Patch Hint Action | Hint Emitted | Verified |
|:---|:---|:---|:---|:---:|
| Missing Reference | `citekeys` | `add_bibtex` | Add BibTeX entries for missing citekeys to refs.bib | ✅ |
| Orphaned Reference | `crossrefs` | `define_labels` | Define labels using `#| label:` or `{#label}` | ✅ |
| Missing Graphic Asset | `figures` | `create_assets` | Place image file at expected path | ✅ |
| Word Limit Overrun | `word-limit` | `trim_words` | Trim excess words with exact headroom calculation | ✅ |

- **Baseline Audit Speed:** `18.46 ms` across 6 strict validation gates.

## 3. Coauthor Roundtrip & Batch Propose

- **Target Word Document:** `from-coauthors/coauthor-edits.docx`
- **Extraction Latency:** `951.39 ms`
- **Extracted Changes:** `2` changes across kinds: `{"replacement": 1, "insertion": 1}`
- **Semantic Tagging:** Each row is tagged with semantic properties (`inline-code`, `citation`, `major-length-change`, `unmatched`) to protect auto-generated R calculations from being overwritten by hand-typed numbers.
- **Batch Resolution:** Successfully proposed `2` reasoned dispositions in one single atomic operation.

## 4. Strict Submission Gate & Render Parity

- **Collab Render Latency:** `1719.89 ms` (generated `2` DOCX files: Main + Supporting Information).
- **HARD Gate Verification:** Intentionally injected defects strictly aborted the submission pipeline, preventing partial or defective documents from being staged.

---
*Scorecard generated automatically by `tools/aix_eval.py`.*
