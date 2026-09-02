# TARS Skills

Custom agent skills used by the TARS operating system. This repository is a
sanitized publication snapshot of the authored skill packages, including their
tests, references, evals, and OpenAI agent metadata where present.

## Included skills

### Vault and portfolio operations

- `client-setup` — create or renew a client engagement across TARS identity layers.
- `task` — create schema-valid task notes.
- `ws` — log work sessions against existing tasks and meetings.
- `meeting` — file meeting notes and ensure one authoritative ledger session.
- `ingest-meeting` — propagate meeting knowledge through the TARS wiki layer.
- `prep` — produce a read-only client call brief.
- `pulse` — generate the portfolio risk pulse.
- `review` — produce the weekly PM rollup.
- `lint` — run unified schema, propagation, and graph validation.
- `vault-lint` — validate notes against live fileClass contracts.
- `os-audit` — inspect drift, freshness, routing, organization, and context health.

### Engineering discipline

- `diagnose` — prove the root cause of hard defects and regressions.
- `tdd` — implement authorized behavior test-first.
- `code-review` — review diffs across contract, spec, and behavior.
- `grill` — resolve consequential design decisions through a structured interview.
- `safe-push` — publish TARS changes through its exact-SHA gate.

### Product and engagement design

- `tars-design` — apply the canonical TARS visual system.
- `tars-ui` — implement and verify TAR-OS interface work.
- `planning-template` — design a build-ready Datarails planning-template
  specification, with a deterministic workbook inventory pass.
- `excel-design` — the canonical `.xlsx` visual contract and its deterministic
  workbook linter.

## Repository boundary

The canonical working source currently remains in:

```text
System/Agent Runtime/source/claude/skills/
```

The generated `.claude/`, `.codex/`, and `.agents/` projections are deliberately
excluded. Client-specific examples and freshness-policy overrides are replaced
with synthetic values in this public snapshot. TARS-specific skills expect the
vault contract and repository paths defined by TARS; they are not standalone
applications.

## Installation

Copy an individual directory from `skills/` into the skill directory supported by
your agent runtime. Keep the complete directory so scripts, tests, references,
evals, and agent metadata stay with `SKILL.md`.

Every skill directory that ships code also ships its tests. From the repository
root:

```bash
for d in skills/*/; do [ -d "$d/tests" ] && (cd "$d" && python -m pytest tests -q); done
```

Two suites have external requirements. `excel-design` and `planning-template`
need `openpyxl`. The `lint` scheduler contract tests read the live TARS FileClass
and template sources, so they skip outside a TARS checkout and run inside one.

## Privacy and licensing

This repository is publicly readable, but no open-source license is granted by
this repository. See `NOTICE.md` for upstream influences.
