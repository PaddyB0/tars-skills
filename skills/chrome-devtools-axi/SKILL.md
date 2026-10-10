---
name: chrome-devtools-axi
description: Drive a real, signed-in Chrome from the command line through the TARS Chrome profile. Use for any task that needs a browser against a Datarails tenant (signed in to the US, US2, UK and CA regions) or any other site - UI-only publishes, screens the API cannot reach, dashboard screenshots, checking what a page actually shows, debugging a page's failed requests, and recording the API calls a UI action makes so dr-cli or a runbook can repeat it. Skip it when curl, dr-cli or a connector can do the job.
---

# chrome-devtools-axi

## What it is

An attach-mode CLI over the TARS Chrome, a dedicated profile with the DevTools
port on 9333. The profile is signed in to the US, US2, UK and CA Datarails
regions. Chrome lifecycle belongs to
`Cowork/os/automations/tars-chrome/tars-chrome.ps1 start|stop|status`. The bridge
is disposable: `axi.sh stop` stops only the bridge and Chrome keeps running.
`capture.mjs` in the same folder records network traffic with secrets redacted.

## How to call it

Always through the wrapper, from the vault root:

```bash
Cowork/os/automations/tars-chrome/axi.sh <command> [args]
```

`axi.sh --help`, `axi.sh <command> --help` and `node Cowork/os/automations/tars-chrome/capture.mjs --help`
are the command reference. Read them rather than guessing flags. Exit 2 means
Chrome is down: run
`powershell -NoProfile -File Cowork/os/automations/tars-chrome/tars-chrome.ps1 start`.

## Rules

- On a shared browser, run `pages` then `selectpage <id>` before `open`. A restarted bridge has no page selected.
- After `newpage`, run `pages` and `selectpage` the newest id; a redirecting URL leaves nothing selected.
- Close every tab you open with `closepage <id>`, and run `axi.sh stop` when done.
- Never call `navigator.clipboard.readText()`; it hangs. Read the clipboard with `powershell -NoProfile -Command Get-Clipboard -Raw`.
- Never type credentials or sign in to anything. A sign-in page means stop and tell Patrick.
- Tenant hosts are customer production. A tenant write through the browser needs chat confirmation first, exactly as a dr-cli write does.
- Prefer dr-cli when it can do the job. Use the browser for what it cannot: UI Publish after new mapper fields, calc-formula publish past the client lint, gauge and combo widgets, the mappers Library screen, dashboard screenshots.
- Verify a state-changing action with a fresh `snapshot` or `screenshot` before reporting it.
- `ps: unknown option` on stderr during `stop` is Git Bash noise.
- `STALE_REF` means re-snapshot and retry.
- `network`, `network-get` and `console` output stops at 2,000 characters and is not redacted. Page lists with `--limit 12 --page <n>`. Never copy their header output into a note, message or file: it carries the session cookie. Use `capture.mjs` for full, redacted records.
- A full page reload clears the request list and evicts response bodies. Capture before anything reloads.

## Debug a page

1. Select the tab and reproduce the problem.
2. `console --type error`. Two errors are normal: 401s right after a full page load, each followed by a 200 from `/jwt/api/token/refresh/cookie/`, and mixpanel CORS errors.
3. `network --type xhr --limit 12 --page <n>`. Datarails' own calls are `/api/` and `/jwt/` on the tenant host. A failure is a status of 400 or more, or an error instead of a status.
4. When the URL and status are not enough, run `capture.mjs` while you reproduce the problem again and read the failing call's record.
5. Report the method, path, status, error text and `x-trace-id`. The trace id is what Datarails support and R&D need to find the request.

## Learn a UI action

1. Start `node Cowork/os/automations/tars-chrome/capture.mjs --seconds <n> --label <action>` in the background, with every tab the action needs already open.
2. The action runs while it records. Patrick performs a write unless he confirmed in chat that you may. A read-only action you may perform yourself.
3. Read `summary.txt`, then the record of each POST, PUT, PATCH or DELETE call: path, request body, response.
4. Check whether dr-cli already has the operation (`dr <group> --help`). Use it when it does.
5. When it does not, write a runbook in `Cowork/os/knowledge/runbooks/` with the method, path template, body shape and the response that proves success. Use placeholder ids and values. Nothing from the tenant is copied into it.
6. Repeating a captured write is a tenant write and needs chat confirmation first.
7. Captures hold customer data. They stay in `%LOCALAPPDATA%\tars\captures\`, are never copied into the vault, and are deleted when the task is done.

## Gong

Parked. Google blocks sign-in in this profile. Do not attempt it.
