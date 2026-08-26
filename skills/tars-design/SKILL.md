---
name: tars-design
description: Apply the canonical TARS visual system to production UI, UX reviews, prototypes, and visual artifacts. Use for TAR-OS or Obsidian interface work involving layout, typography, color, components, interaction states, responsive behavior, icons, motion, or product voice.
---

# TARS Design

Use this skill as the canonical agent doorway to the vendored TARS design system. The files under `.obsidian/design-system/` remain the visual authority; this skill routes to them without copying or replacing them.

## Load the authority

1. Read the repository-root `CLAUDE.md`.
2. Read `.obsidian/design-system/SKILL.md` and `.obsidian/design-system/readme.md`.
3. Read only the design-system files needed for the requested surface:
   - tokens: `.obsidian/design-system/tokens/*.css`
   - component visuals: `.obsidian/design-system/components/components.css`
   - component usage: the matching `components/**/<Component>.prompt.md`
   - approved compositions: `.obsidian/design-system/ui_kits/`
4. For TAR-OS production work, also read:
   - `.obsidian/plugins/tars-os/PRODUCT.md`
   - `.obsidian/plugins/tars-os/DESIGN.md`
   - the current binding implementation plan named by the task

Treat authority in this order:

1. `CLAUDE.md` and live FileClass schema for data and write contracts.
2. The current binding implementation plan for product behavior and accepted composition.
3. TAR-OS `PRODUCT.md` for durable product intent.
4. TAR-OS `DESIGN.md` and `.obsidian/design-system/` for visual rules.
5. Existing production UI as implementation evidence.

Do not let a generic design heuristic override a higher authority.

## Apply the system

- Preserve the dark-first, information-dense Obsidian console identity.
- Use the cool gunmetal neutral ramp and reserve indigo for selected/active state and the single primary action.
- Use Inter for interface/reading text and JetBrains Mono for numerals, dates, metadata, keybinds, counts, and instrument labels.
- Use the 3/4/6/10px slab radius scale, hairline seams, and flat layered surfaces. Do not introduce decorative gradients or routine card shadows.
- Keep labels sentence case. Reserve mono uppercase for instrument labels. Use terse, factual copy without emoji, exclamation marks, or praise.
- Use Lucide through Obsidian's native icon APIs at stroke width 1.9. Do not introduce emoji or a parallel icon set.
- Use segmented gauges for progress. Do not replace them with smooth bars.
- Keep motion mechanical at 90–220ms with `cubic-bezier(0.2, 0, 0, 1)` and honor reduced motion.
- Preserve native Obsidian chrome and interaction patterns. Build only the plugin-owned content surface.

Do not load `_ds_bundle.js` in production. It is a prototype artifact. Re-express the documented component contract in typed production components.

## Verify

For production changes:

1. Check default, empty, loading, error, disabled, hover, focus, active, and overflow states that apply.
2. Check keyboard operation and visible focus.
3. Check reduced motion.
4. Check 1440, 900, 736, and 320px widths when the surface can resize; reject root horizontal overflow.
5. Build and reload the plugin in Obsidian, then inspect runtime errors and the live DOM. A static code review is not visual verification.
