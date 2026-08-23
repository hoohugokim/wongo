"""Shared helpers — LEGACY SHIM (uplift complete for this surface).

Everything here moved: text analysis + checks -> wongo.engine.checks;
profile discovery/loading -> wongo.profiles. This shim keeps the sibling
legacy scripts importable until they are deleted (HANDOFF step 6/7 cleanup).
"""
from __future__ import annotations

from wongo.engine.checks import (  # noqa: F401  (re-exported)
    CROSSREF_PREFIXES,
    bib_keys,
    citekeys_used,
    crossrefs_used,
    image_paths,
    labels_defined,
    prose,
    split_front_matter,
    word_count,
)
from wongo.profiles import (  # noqa: F401  (re-exported)
    load_journal_config,
    load_profile,
    manuscript_type,
    profile_staleness_days,
)
