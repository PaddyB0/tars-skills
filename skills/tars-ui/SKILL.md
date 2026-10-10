---
name: tars-ui
description: Shape, implement, critique, audit, harden, and polish TAR-OS UI through the TARS design system, test-first delivery, deterministic Impeccable checks, live Obsidian verification, and final code review. Use for any TAR-OS screen, component, interaction, responsive, accessibility, or visual-quality task.
---

# TARS UI

Run one TARS-native UI/UX workflow. TARS product plans and design artifacts decide what the product is; the pinned Impeccable pilot supplies critique, detector, hardening, and polish discipline.

## Load context

Before shaping or editing:

1. Read the repository-root `CLAUDE.md`.
2. Read `.claude/skills/tars-design/SKILL.md` completely and follow its authority loading rules.
3. Read `.obsidian/plugins/tars-os/PRODUCT.md`, `.obsidian/plugins/tars-os/DESIGN.md`, and `references/impeccable-pilot.md`.
4. Read the current binding plan and the target TSX/CSS/tests.
5. Inspect both outer and nested git status. Preserve unrelated work and stop at overlapping dirty files unless the user has authorized reconciliation.

## Workflow

### 1. Establish design context

State the user, job, target surface, outcome, binding plan, relevant data contract, and acceptance widths/states. Use repository evidence first. Ask only when a missing choice would materially change the product.

### 2. Shape

Before code, write a compact surface brief:

- user/job/outcome;
- information hierarchy and primary action;
- states and transitions;
- responsive and keyboard behavior;
- proof that the direction follows TARS authorities rather than adding a new aesthetic.

If the user already authorized implementation and the repository resolves the brief, continue without a separate approval pause.

### 3. Implement through TDD

Read `.claude/skills/tdd/SKILL.md` completely and implement behavior in vertical red-green-refactor slices at a stable public seam. Keep presentation changes scoped to plugin-owned surfaces. Do not invent schema, rewrite frontmatter wholesale, duplicate Obsidian chrome, or load design-system prototype bundles.

### 4. Critique

Critique the implemented surface against:

- the surface brief;
- the binding implementation plan;
- `DESIGN.md` and the canonical design-system files;
- hierarchy, density, legibility, affordance, state coverage, copy, responsive behavior, and accessibility;
- generic AI-design tells that conflict with TARS.

Separate contract defects, usability defects, visual drift, and optional polish. Do not treat an intentional TARS signature as a defect merely because it is uncommon.

### 5. Audit and harden

Run the local deterministic detector when the exact dependency is installed:

```bash
cd .obsidian/plugins/tars-os
npm run design:baseline
```

Classify every finding using `references/impeccable-pilot.md`. Fix real findings before adding exceptions. Keep exceptions value- or file/rule-scoped and reviewable.

Harden keyboard flow, focus, reduced motion, loading/error/empty states, content overflow, narrow panes, touch targets where applicable, and destructive-action confirmation.

### 6. Polish

Remove incidental inconsistency without changing the approved visual world. Tighten alignment, spacing rhythm, type roles, labels, hover/focus/active treatment, and empty-state copy. Prefer deleting ornamental noise over adding decoration.

### 7. Verify live in Obsidian

Run the repository gates:

```bash
npm run check
npm test
npm run build
obsidian plugin:reload id=tars-os
obsidian dev:errors
obsidian dev:console level=error
obsidian dev:dom selector=".tars-os-root" text
```

If reload is stale, use the hard-reload command in the plugin README. Inspect the visible surface at the accepted widths and in both themes when the binding plan requires both. Static screenshots or passing tests do not replace live verification.

### 8. Review

Read `.claude/skills/code-review/SKILL.md` completely and perform its Contract, Spec, and Behaviour review on the final diff. Resolve in-scope findings, rerun affected gates, and report any dirty-file boundary.

## Phase 1 constraints

- Keep Impeccable hooks disabled.
- Do not run the upstream `pin` script; the `/ui-*` wrappers in source are the only aliases.
- Do not make detector output CI-blocking.
- Do not enable Impeccable Live mode.
- Do not allow Impeccable to replace TARS product or visual authority.
- Do not commit or publish unless the user separately asks.
