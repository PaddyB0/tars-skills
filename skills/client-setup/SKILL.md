---
name: client-setup
description: Set up a client in TARS across all three identity layers — CRM company note, Projects engagement note, and the Cowork work folder — with the join keys wired both ways. Pulls the company profile and contacts from Salesforce and classifies stakeholders from Gong so contact pages are created for you. Also handles a NEW ENGAGEMENT / RENEWAL for an existing client (new Project note, prior project completed, company pointer repointed) without duplicating the client or the folder. Use whenever setting up, onboarding, kicking off, or spinning up a client or a new engagement/quarter/renewal in TARS — trigger on "set up <client>", "onboard <client>", "new client", "new engagement", "new project for <client>", "kick off <client>", "renew <client>", "Q<n> renewal", even when the word "project" isn't used. Supersedes the older /new-client command.

---

# /client-setup

Stand up a client in TARS across its three layers. **Write every note's frontmatter
per the root `CLAUDE.md` § Schema contract** — that's the source of truth for enums,
dates, and tags; this skill does not repeat it. Your job here is the orchestration the
schema doesn't cover: picking the right mode, pulling real data from Salesforce/Gong,
and closing the loop with lint — the steps that get skipped when this is done freehand.

## The three layers

| Layer | Location | Cardinality |
|---|---|---|
| Client identity | `CRM/Clients/<Client>.md` (`crm_company`) | one per client, permanent |
| Engagement | `Projects/<Client> - <descriptor>.md` (`project`) | one per deal |
| Work folder | `Cowork/clients/<Client>/` | one per client, permanent |

Two constraints that aren't in the schema tables: the **project basename must differ
from the company basename** (else `[[<Client>]]` is ambiguous — that's why engagements
carry a descriptor/quarter suffix), and the **work folder is named for the client,
never the engagement**.

## Step 0 — pick the mode

Grep for an existing `CRM/Clients/<Client>.md` and `Cowork/clients/<Client>/` (allow
name variants, e.g. folder `Acme` vs note `Acme Holdings`). Then:

- **Neither exists → Mode A** (new client — build all three layers).
- **Both exist → Mode B** (new engagement / renewal — add one project, reuse the rest).
- **Only one exists** → a broken bridge; stop and report, don't guess.

## Mode A — new client

1. **Salesforce → company profile.** `soqlQuery`:
   `SELECT Id, Name, Website, Industry, BillingStreet, BillingCity, BillingState, BillingCountry FROM Account WHERE Name = '<Client>' LIMIT 5`
   (fall back to `find` SOSL on the name). Fill `sf.Url` =
   `https://datarails.lightning.force.com/lightning/r/Account/<Id>/view`, `Industry`,
   `BillingAddress`, and `Timezone` inferred from billing state (`EST/PST/MST/CDT`
   only; omit if unsure). **Dry result → leave those fields empty; never invent them.**
2. **Salesforce → contacts.**
   `SELECT Id, Name, Title, Email FROM Contact WHERE Account.Name = '<Client>' ORDER BY LastModifiedDate DESC`.
3. **Gong → classify stakeholders.** `ask_account` on `<Client>`: *"Who are the key
   stakeholders and each person's role — economic decision maker, champion, or other?"*
   Set `contact.recordtype` from the answer (`Decision Maker`/`Champion`); anyone
   without a signal stays `Contact`. Create a `CRM/Contacts/<Name>.md` per real person.
4. **Write company, project, and contact notes** per the schema contract, mirroring
   contacts into the company `ContactName` and the project `Contacts`. `Project:` on the
   company points at the engagement you just created.
5. **Scaffold the folder.** Copy `Cowork/clients/_template/` → `Cowork/clients/<Client>/`
   and fill its `CLAUDE.md`: the `# CLAUDE.md — <Client>` heading, the
   `**TARS project:** … · **TARS company:** …` pointer, and voice/rules from what
   Patrick gave you. Don't re-state identity that's canonical in the company note.

## Mode B — new engagement / renewal

The client, folder, and company note already exist — reuse them.

1. **Create the new project note** (fresh basename, e.g. `<Client> - PS Q<n> YYYY`),
   `Status: 🔵 active`, new dates.
2. **Complete the prior engagement.** On the client's current active project, set
   `Status: 🟢 complete` **and add `Completed_At: <YYYY-MM-DD HH:mm>`** — the completion
   stamp is the step most easily forgotten. Never rename/reuse the old note.
3. **Repoint** the company note's `Project:` to the new engagement and add a Timeline
   line for the kickoff.
4. **Update the folder's** `CLAUDE.md` `**TARS project:**` pointer to the new engagement.
   No new folder, no second company note.

## Finish (both modes)

- **Pull prior knowledge (the down-step).** Search `Cowork/os/knowledge/index.md` for
  runbooks/concepts/gotchas matching the client's systems + engagement type; list the
  hits so they're on the radar before building.
- **Run `/lint`** and confirm zero findings and that every join key resolves both ways
  (`cowork_client` on company + project ↔ folder pointer; company `Project` ↔ project
  `Company`; company `ContactName` ↔ each contact's `Company`).

## Don't

- Fabricate anything SF/Gong or Patrick didn't give you — a thin true note beats a rich
  wrong one. Say what came back empty.
- Run the interactive Templater templates in `Administrator/`; write frontmatter directly.
- Touch `Bases/*.base`, `Administrator/`, `.obsidian/`, or `tars-pm`.
