# Manuscript evidence

Wongo connects manuscript builds with scoped observations and explicit human
decisions. The following terms describe different kinds of evidence.

## Language

**Build subject**: One exact manuscript build, including its declared inputs,
profile, style, tools, engine source and final outputs.

**Audit observation**: A project-defined assertion evaluated against one build
subject. Its stated coverage limits what a passing result establishes.
_Avoid_: Scientific validation, scientific truth

**Converted preview**: Pages produced by a named document renderer. Their
inspection establishes that representation's appearance.
_Avoid_: Microsoft Word certification

**Reviewer claim**: An attributed statement about exact source or artifact
locations whose correctness remains for a maintainer to assess.
_Avoid_: Tool observation

**Maintainer disposition**: A person's attributed acceptance, rejection or request
for work on a reviewer claim concerning one build subject.

**Author authorization**: A person's explicit decision on a configured manual
gate for one build subject. It is separate from technical readiness.
_Avoid_: Checks passed
