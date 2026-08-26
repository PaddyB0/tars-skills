---
name: pulse
description: Rewrite Notes/Portfolio Pulse.md — one risk-ranked line per active client (state · risk · next milestone), synthesized from all dossiers + active projects. The narrative complement to the Project Hub (Hub computes; Pulse judges). Use when the user says "run the pulse", "portfolio pulse", "how's the portfolio looking", "/pulse".
---

# /pulse

Rewrite `Notes/Portfolio Pulse.md`: a risk-ranked, one-line-per-active-client read
of the whole book. This is the **narrative** complement to the Project Hub — the Hub
*computes* (status, progress, burn); Pulse *judges* (state, risk, next milestone).
Spec: [[TARS Unified OS - Schema]] § 5.

## Read
- Every `CRM/Clients/*.md` dossier (Snapshot, Commitments, Timeline).
- Active projects — `Projects/*.md` with `Status: 🔵 active` or `🔴 at risk`.
- Open loops and renewal deadlines surfaced in the dossiers.

## Write — `Notes/Portfolio Pulse.md` (REWRITE, whole file)
- One line per **active** client, **ranked most-at-risk first**:
  `- **<Client>** — <state> · <risk> · next: <milestone> ([[dossier]])`
- A short header with the run date and the single top portfolio risk.
- Every judgment traces to a dossier — keep it to what the dossiers support; if a
  client's dossier is stale, say "stale — last touched <DossierUpdated>" rather than
  inventing status.

## After running
- Append to `log.md`: `## [YYYY-MM-DD] pulse | <N> active clients — top risk: <one-liner>`.
- Confirm the Command Center 🩺 embed still points at `Notes/Portfolio Pulse.md`.

## Boundary
Pulse does **not** duplicate the Hub's computed metrics. It reads the dossiers'
synthesized state and ranks risk. If it starts re-deriving burn/progress numbers,
it's overstepping into Hub territory (decision 6).
