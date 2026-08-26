---
name: grill
description: Conduct an explicit, user-directed decision interview that resolves a plan or design one consequential question at a time. Use only when the user asks to be grilled, interviewed, challenged, or walked through a decision tree before action.
---

# Grill

Resolve the decision tree before acting. This skill is conversational and deliberately
has no write phase.

## 1. Orient

Restate the decision, intended outcome, and why it matters. Read available repository
context and inspect discoverable facts before asking questions. Never ask the user
for a fact that can be safely found in the workspace or connected tools.

Separate:

- **facts** — discover them;
- **assumptions** — surface and test them;
- **decisions** — put them to the user.

## 2. Walk one branch at a time

Ask exactly one consequential question per turn. Lead with the recommended answer,
then explain the material trade-off in one or two sentences. Wait for the user's
answer before moving to a dependent decision.

Prefer questions that resolve:

- objective and measurable success;
- users, owners, and affected systems;
- scope and explicit exclusions;
- constraints and non-negotiable contracts;
- data ownership and source of truth;
- failure modes, reversibility, and recovery;
- verification, rollout, and handoff.

Skip branches already settled by context. Do not ask ceremonial questions whose
answer would not change the plan.

## 3. Maintain the decision ledger

Keep a compact ledger in conversation:

- decisions made;
- assumptions confirmed or rejected;
- facts discovered;
- open decisions;
- out-of-scope items.

Use the ledger to prevent repetition and to notice contradictions. When a new answer
conflicts with an earlier one or with the repository contract, surface the conflict
immediately and resolve it before continuing.

Stress-test important answers with one concrete edge case. Do not expand every branch
equally; spend depth where the decision is expensive, irreversible, or ambiguous.

## 4. Converge

Stop questioning when every decision that could materially change the result is
resolved. Present a concise synthesis containing:

- agreed outcome and success criteria;
- decisions and rationale;
- scope and exclusions;
- risks and mitigations;
- unresolved facts, if any;
- the recommended next workflow.

Ask the user to confirm that shared understanding has been reached. Do not implement,
write documentation, create tasks, commit, or send anything while this skill is
active. After confirmation, end the skill so the user can authorize the appropriate
execution workflow separately.

## Completion criterion

Complete only when no consequential decision remains hidden, contradictions are
resolved, the user has confirmed the synthesis, and no implementation action has
occurred.
