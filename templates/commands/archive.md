---
description: Archive a completed feature — moves specs/<feature>/ to specs/archive/ and writes ARCHIVE.md with delta summary and validation results. Requires all E2E validations to have passed (or --force).
handoffs:
  - label: Start New Feature
    agent: specpack.specify
    prompt: Start a new feature specification.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding.
- If `--force` is provided, pass `--force` to the CLI command.
- If `--feature <path>` is provided, pass `--feature <path>` to the CLI command.

## Outline

You are archiving a completed feature. Delegate all archiving logic to the `specify archive` CLI — it handles the validation gate, ARCHIVE.md generation, directory move, and feature.json reset.

### Step 1 — Run archive

Build the command from the user's arguments:

- No arguments: `specify archive`
- With `--force`: `specify archive --force`
- With `--feature <path>`: `specify archive --feature <path>`
- With both: `specify archive --feature <path> --force`

Run the command from the project root. Capture and display the full output.

### Step 2 — Interpret the result

**If the command succeeds (exit code 0):**

Display the CLI output, then confirm:

```
[ARCHIVED] Feature moved to specs/archive/<feature>/

ARCHIVE.md written with delta summary and validation results.
Active feature cleared from .specify/feature.json.
```

Suggest next steps:
- `/specpack.specify` — start the next feature
- `specify serve` — browse the archive in the web UI

**If the command exits with BLOCKED (validation not passed):**

Display the blocked message from the CLI output and explain:

```
Archive blocked — not all E2E validations have passed.

Options:
  1. Run /specpack.implement --e2e to complete E2E validation
  2. Run /specpack.archive --force to archive anyway (adds ⚠ warning to ARCHIVE.md)
```

**If any other error:**

Display the error and suggest checking that:
- The feature directory exists
- `.specify/feature.json` points to the right feature
- `specify init` has been run in this project
