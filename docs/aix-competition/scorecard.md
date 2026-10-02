# Wongo-AIX fixture regression scorecard

- Wongo version: `0.3.1`
- Evaluation time (UTC): `2026-10-02 09:05:54`
- Fixture: `examples/aix-demo` (synthetic demonstration, Water Research profile, kist-wcr style)
- Overall: **PASS** (4/4 dimensions passed)

| Measured dimension | Result |
|:---|:---:|
| Stdio discovery, schemas, resources and prompts | PASS |
| Injected defects and patch hints | PASS |
| Exact edits, source tags and decision lifecycle | PASS |
| Submission refusal and existing-output preservation | PASS |

Discovery launches a real stdio server and checks the advertised schema and read
surfaces. The other dimensions exercise the engine in fresh temporary projects.
Proposal lint errors are expected until simulated author decisions are recorded;
final lint must be clean. The gate check requires the expected citation GateError
and unchanged hashes of every existing output file, including the manifest.

These are bounded fixture checks. They do not measure LLM decision accuracy,
hallucination rates, time saved, scientific validity, journal acceptance, or
release-to-release XML parity. Run `tools/bytecompare.py` separately for the
reference-manuscript parity gate. SDK and negotiated protocol versions below are
distinct values. Latencies describe this local run and have no pass threshold.

## Measurements from this run

```json
{
  "discovery": {
    "status": "PASS",
    "tool_count": 12,
    "prompt_count": 3,
    "resource_count": 3,
    "tools": [
      "wongo_check",
      "wongo_diff",
      "wongo_doctor",
      "wongo_profile_get",
      "wongo_render",
      "wongo_roundtrip",
      "wongo_scaffold",
      "wongo_status",
      "wongo_worksheet_batch_propose",
      "wongo_worksheet_lint",
      "wongo_worksheet_set",
      "wongo_worksheet_status"
    ],
    "prompts": [
      "wongo-coauthor-review",
      "wongo-pre-submission-audit",
      "wongo-revision-diff"
    ],
    "checks": {
      "tool_names_match": true,
      "tool_schemas_valid": true,
      "prompt_names_match": true,
      "prompt_arguments_valid": true,
      "resource_uris_match": true,
      "resource_reads_valid": true,
      "worksheet_resource_read_valid": true,
      "prompt_reads_valid": true
    },
    "latency_ms": 611.51,
    "protocol_version": "2025-11-25",
    "sdk_version": "2.2.0"
  },
  "audit": {
    "status": "PASS",
    "clean_audit_latency_ms": 16.46,
    "clean_hard_checks_pass": true,
    "clean_checks_passed": 6,
    "total_checks": 7,
    "defects_verified": {
      "citekeys": true,
      "crossrefs": true,
      "figures": true,
      "word-limit": true
    },
    "verified_defects": 4,
    "tested_defects": 4
  },
  "roundtrip": {
    "status": "PASS",
    "extraction_latency_ms": 704.81,
    "extracted_changes": 2,
    "change_kinds": {
      "insertion": 1,
      "replacement": 1
    },
    "rows": [
      {
        "row": 1,
        "kind": "insertion",
        "author": "Synthetic reviewer",
        "location": "index.qmd:71",
        "qmd": "index.qmd",
        "line": 71,
        "unmatched": false,
        "old": "—",
        "new": "under steady-state potentiostatic polarization",
        "context": "…Electrochemical Diagnostics Chronoamperometry was conducted…",
        "disposition": "PENDING",
        "state": "pending",
        "decision": null,
        "proposal": null,
        "note": "",
        "problem": null,
        "needs_decision": true,
        "apply_blocker": null,
        "tags": [],
        "word_count_delta": 4,
        "source": {
          "path": "/var/folders/8_/rh35ssj92h173ngj0pp8v6cr0000gn/T/wongo-aix-roundtrip-954qby1v/manuscript/index.qmd",
          "line": 71,
          "text": "Chronoamperometry was conducted at a poised anode potential of +0.20 V (vs. Ag/AgCl) using a multi-channel potentiostat.",
          "reason": null,
          "problem": null,
          "alignment": "unverified",
          "hint": "Tags are review hints; verify the current source location before applying edits."
        }
      },
      {
        "row": 2,
        "kind": "replacement",
        "author": "Synthetic reviewer",
        "location": "index.qmd:117",
        "qmd": "index.qmd",
        "line": 117,
        "unmatched": false,
        "old": "12.4",
        "new": "approximately 13.1",
        "context": "…unctionalized electrodes sustained a peak current density of…",
        "disposition": "PENDING",
        "state": "pending",
        "decision": null,
        "proposal": null,
        "note": "",
        "problem": null,
        "needs_decision": true,
        "apply_blocker": null,
        "tags": [
          "inline-code"
        ],
        "word_count_delta": 1,
        "source": {
          "path": "/var/folders/8_/rh35ssj92h173ngj0pp8v6cr0000gn/T/wongo-aix-roundtrip-954qby1v/manuscript/index.qmd",
          "line": 117,
          "text": "Under continuous flow conditions, functionalized electrodes sustained a peak current density of `r sprintf(\"%.1f\", demo_peak_density)` A/m² with a marked reduction in interfacial charge-transfer resistance.",
          "reason": null,
          "problem": null,
          "alignment": "unverified",
          "hint": "Tags are review hints; verify the current source location before applying edits."
        }
      }
    ],
    "checks": {
      "exact_edits": true,
      "source_tags_and_deltas": true,
      "initial_pending": true,
      "proposals_recorded": true,
      "proposals_require_decision": true,
      "final_decisions_and_lint": true,
      "sources_unchanged": true
    }
  },
  "gate": {
    "status": "PASS",
    "checks": {
      "clean_outputs_present": true,
      "expected_citekey_gate": true,
      "manifest_present": true,
      "outputs_and_manifest_unchanged": true,
      "no_staging_leftovers": true
    },
    "collab_render_latency_ms": 2224.77,
    "collab_outputs_count": 2,
    "submission_outputs_count": 2,
    "failing_gate_checks": [
      "citekeys"
    ],
    "preserved_file_count": 5,
    "error": null
  }
}
```

Generated by `tools/aix_eval.py`; rerun after changing code or fixtures.
