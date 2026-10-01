"""Standard MCP Prompts for Wongo.

Provides pre-packaged prompt templates for submission audit, coauthor review, and revision diffing.
"""
from __future__ import annotations

from mcp.server.mcpserver import MCPServer


def register_prompts(server: MCPServer) -> None:
    """Register standard Wongo workflow prompts on the MCP server."""

    @server.prompt(name="wongo-pre-submission-audit", description="Audit manuscript against target journal profile and prepare verified submission DOCX.")
    def prompt_pre_submission_audit(project: str = ".") -> str:
        return (
            f"Please conduct a comprehensive pre-submission audit for the Wongo manuscript in '{project}':\n\n"
            "1. Run `wongo_status` to see current readiness and configured journal.\n"
            "2. Run `wongo_check` (strict mode) to validate against journal word limits, headings, citekeys, and crossrefs.\n"
            "3. If any checks fail, review their `actionable_patch_hints` and propose exact minimal fixes to the .qmd or refs.bib.\n"
            "4. Once checks pass, execute `wongo_render(target='submission')` to generate the journal-ready DOCX.\n"
            "5. Verify that line numbering, booktabs table formatting, and abstract rules match journal requirements."
        )

    @server.prompt(name="wongo-coauthor-review", description="Process coauthor Word track changes and comments into an auditable merge worksheet.")
    def prompt_coauthor_review(docx_path: str, project: str = ".") -> str:
        return (
            f"Please process the coauthor edits in '{docx_path}' for manuscript project '{project}':\n\n"
            f"1. Run `wongo_roundtrip(docx_path='{docx_path}', project='{project}')` to extract changes.\n"
            "2. Inspect the resulting merge worksheet with `wongo_worksheet_status`.\n"
            "3. For each pending row, evaluate the edit:\n"
            "   - If the edit alters an auto-generated R calculation or inline value, propose `fix-code`.\n"
            "   - If the edit adds/modifies citations, verify the citekey exists.\n"
            "   - If the edit is a sound prose improvement, propose `apply`.\n"
            "   - If the edit introduces errors or conflicts, propose `reject: <rationale>`.\n"
            "4. Use `wongo_worksheet_batch_propose` to record all reasoned proposals.\n"
            "5. Present an executive summary table of proposed resolutions to the author for final confirmation."
        )

    @server.prompt(name="wongo-revision-diff", description="Compare revised manuscript against original submission and produce Word tracked-changes revision.")
    def prompt_revision_diff(original_docx: str, revised_docx: str) -> str:
        return (
            f"Please generate a tracked-changes revision DOCX from '{original_docx}' to '{revised_docx}':\n\n"
            f"1. Run `wongo_diff(original='{original_docx}', revised='{revised_docx}')`.\n"
            "2. Verify that inline math, breaks, and tabs were cleanly preserved and that table differences are noted.\n"
            "3. Summarize the inserted and deleted word counts.\n"
            "4. Draft an itemized 'Response to Reviewers' template aligning each major revision block with potential referee comments."
        )
