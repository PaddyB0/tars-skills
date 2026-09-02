---
description: Read-only overnight TARS sentinel — validate vault health, PM pressure, ingest backlog, and automation evidence without changing local or external state.
---

# /night-watch

Run an unattended, **read-only** health pass over TARS and return one concise
morning report. This routine observes, verifies, and queues decisions; it never
repairs or advances work.

## Non-negotiable boundary

The entire run is read-only:

- Do not edit, create, move, rename, or delete any file.
- Do not invoke `/lint` as a workflow because its post-run logging writes files.
  Run its deterministic checker directly, without `--fix`.
- Do not run `/ingest-meeting`, `/pulse`, `/handoff`, `/safe-push`,
  `/submit-timesheets`, or any other mutating workflow.
- Do not run `git pull`, `git fetch`, `git commit`, `git push`, branch operations,
  package installation, deployment, or dependency upgrades.
- Do not call connectors or APIs that create, update, submit, send, label, or
  delete anything. A read-only remote-tip query performed by the repository's
  health verifier is allowed.
- Do not read `.obsidian/plugins/tars-os/data.json` directly; it contains a real
  API key. Only use the credential-safe health verifier below.
- Treat a non-zero check exit as evidence to report, never permission to fix it.
- If access, network, or a command is unavailable, mark that evidence
  **UNVERIFIED** and continue with the remaining read-only checks. Do not seek
  broader access during an unattended run.

## 1. Establish the observation point

1. Read root `CLAUDE.md`, `Cowork/CLAUDE.md`, and
   `Cowork/os/automations/CLAUDE.md`.
2. Use the real local date in `America/Edmonton`; call it `TODAY`.
3. Record:
   - `git branch --show-current`
   - `git rev-parse HEAD`
   - `git status --short`
4. Do not change branches or clean a dirty worktree. A dirty worktree is a
   morning-review item, not an overnight blocker.

## 2. Run the deterministic checks

Run each command from the repository root. Preserve its output and exit code.
`PYTHONDONTWRITEBYTECODE=1` prevents Python bytecode writes.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8 \
  python3 .claude/skills/lint/lint.py --today <TODAY>

PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8 \
  python3 .claude/skills/review/review.py --today <TODAY>

PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8 \
  python3 Cowork/os/automations/ingest-backlog.py \
  --vault /path/to/TARS --today <TODAY>

PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8 \
  python3 Cowork/os/automations/verify_automation_health.py \
  --runtime-vault /path/to/TARS
```

Interpret automation evidence narrowly:

- source code proves capability, not a deployed trigger;
- configured or active proves scheduling, not successful completion;
- a Gong capture commit proves observed output, not trigger health;
- a Claude `lastRunAt` proves launch evidence, not successful edits;
- a lint-log entry does not identify which actor ran lint;
- Salesforce remains supervised/on-demand regardless of receipt count;
- Apps Script triggers remain unverified until Patrick inspects the authenticated
  Google Triggers UI.

## 3. Read-only reasoning pass

Use the check output and source files to answer:

1. What could make TARS wrong-answer Patrick tomorrow?
2. Which PM item has the greatest time pressure?
3. Which meetings are awaiting ingestion, and which are over the two-day P1
   threshold?
4. Which automation has stale, missing, ambiguous, or merely configuration-level
   evidence?
5. Are any findings new enough to plausibly come from today's local changes?
   Use local Git history only; do not fetch.
6. Which findings require Patrick's judgment rather than a mechanical repair?

Do not open raw meeting bodies merely to enrich the report. The sentinel measures
the propagation loop; it must not conceal a thin or stale dossier by bypassing it.

## 4. Return the report

Return the report in chat only. Do not file it into `Notes/`, `audits/`, `log.md`,
or a handoff note.

```markdown
# TARS Night Watch — YYYY-MM-DD

**Verdict:** GREEN | YELLOW | RED
**Observed:** <branch> @ <12-char SHA> · worktree clean/dirty
**Tomorrow's biggest risk:** <one sentence>

## Needs Patrick
- <decision or supervised workflow, with evidence path>

## Vault and PM
- Lint: <errors/warnings and most important finding>
- Work: <overdue, due soon, stale in-progress, hours exception>
- Meeting backlog: <total, overdue, oldest>

## Automation evidence
- <process>: <last evidence> · <what that evidence does and does not prove>

## Changes or regressions
- <new or plausibly recent finding; distinguish evidence from inference>

## Suggested daylight queue
1. <highest-value approved action or skill>
2. <next action>

## Checks
- PASS/FAIL/UNVERIFIED — <command/check and exit code or reason>
```

Verdict rules:

- **RED** — a schema error, broken core route, credential exposure, or evidence
  that could make the system materially wrong today.
- **YELLOW** — warnings, overdue ingestion, stale operational evidence, dirty
  worktree, or a decision queue that needs attention.
- **GREEN** — all checks clean and no decision is time-sensitive.

Keep the report concise. Report clean checks once; spend detail on exceptions and
the morning decision queue.
