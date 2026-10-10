# Impeccable Phase 1 pilot

## Reviewed pins

- Upstream: `pbakaus/impeccable`
- Reviewed upstream commit: `cd12f86`
- Skill: `skill-v4.3.1` (4.3.1)
- CLI package: `impeccable@4.1.0`
- CLI runtime requirement: Node.js `>=22.18.0`
- Engine: `0.1.5`, downloaded by the skill launcher into `~/.impeccable/bin/0.1.5/` on first run and never stored in the vault

The repository lock is `.obsidian/plugins/tars-os/impeccable.lock.json`. The TAR-OS package lock pins the CLI. Never substitute a floating `npx impeccable` or `@latest`.

The upstream skill is vendored in agent source (`System/Agent Runtime/source/claude/skills/impeccable/`) and projected to `.claude/`, `.agents/` and `~/.claude/`. The `/ui-*` wrappers in source are the sanctioned aliases, and the upstream `pin` script stays forbidden. The four upstream subagents (`impeccable-*` under `.claude/agents/`) are not vendored, so the skill's `reference/degraded/` fallbacks apply. The `tars-ui` workflow carries the approved orchestration while the exact CLI supplies deterministic detection.

## Authority boundary

Impeccable may shape a brief, expose design defects, harden states, and polish execution. It may not choose a replacement visual world. The binding order is:

1. vault contract and FileClasses;
2. current TAR-OS implementation plan;
3. TAR-OS `PRODUCT.md`;
4. TAR-OS `DESIGN.md` and `.obsidian/design-system/`;
5. production implementation evidence;
6. Impeccable heuristics.

## Detector commands

From `.obsidian/plugins/tars-os/`:

```bash
nvm use
npm install --ignore-scripts --omit=optional
npm run design:baseline
```

The runner:

- refuses Node older than `22.12.0`;
- refuses an installed CLI other than `3.4.0`;
- runs the local package entry directly;
- scans `src/` as JSON with the tracked project config;
- propagates exit `2` when findings exist.

The exit code is informational in Phase 1. Do not wire it into build, test, pre-commit, pre-push, CI, or agent hooks.

Use `npm run design:baseline -- --raw` only to compare configuration effects. Raw mode passes `--no-config` and does not define the normal project baseline.

## Finding policy

Fix true findings before writing exceptions. Never ignore a whole real UI file.

### Confirmed intentional value

`Inter` is the canonical TARS interface face. The shared config contains only the value-specific `overused-font=inter` exception. Do not suppress the `overused-font` rule or other font values.

### Status cursor

The blinking cursor in `src/styles/chrome.css` is explicitly permitted by the TARS design system when reduced motion disables it. If the detector flags it, add an exception only for the matching animation rule and this file. Do not waive other looping animation findings. Focus pulses, activity indicators, and spinners require their own functional justification.

### Timeline measurement grid

The `repeating-linear-gradient` in `src/styles/phase4.css` renders timeline measurement lines, not decoration. If `repeating-stripes-gradient` flags it, scope that rule only to `src/styles/phase4.css`. Do not broadly allow gradients or repeating stripes.

### Small functional text

Functional text below 11px is a true finding until live inspection proves it remains legible and non-interactive. Do not suppress tiny-text or design-system font-size rules globally. Increase the text or record a selector-specific rationale after checking the real pane and target widths.

## Phase 1 exclusions

Do not enable:

- hook manifests or automatic edit/stop checks;
- upstream `pin` aliases (the `/ui-*` wrappers in source are the only shortcuts);
- CI blocking;
- Live mode;
- automatic update checks that change the pin;
- upstream aesthetic generation or replacement-world workflows.
