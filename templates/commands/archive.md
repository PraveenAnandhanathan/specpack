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
If `--force` is provided, skip validation check and archive anyway.
If `--feature <path>` is provided, use that feature directory instead of `.specify/feature.json`.

## Outline

You are archiving a completed feature. This moves it out of the active `specs/` directory into `specs/archive/` and creates a permanent `ARCHIVE.md` audit record.

### Step 1 — Identify the feature

1. If `--feature <path>` provided: use that path.
2. Otherwise read `.specify/feature.json` → `feature_directory`.
3. If neither: error "No active feature found."

Confirm the feature directory exists and contains at least `spec.md` or `tasks.md`.

### Step 2 — Validation gate (skip if --force)

Read `profiles/.validation-status.md`. Check that E2E results for Functional, Performance, and Customer are all PASS or WARN (not FAIL or UNKNOWN).

If any are FAIL or UNKNOWN:
```
[ARCHIVE BLOCKED]
Functional:   FAIL
Performance:  UNKNOWN
Customer:     PASS

Run /specpack.implement --e2e first, or use --force to override.
```
Stop. Do not archive.

### Step 3 — Build delta summary

Scan `spec.md`, `plan.md`, `tasks.md` for delta markers:
- `[ADDED]` — count and list
- `[MODIFIED]` — count and list
- `[REMOVED]` — count and list
- `[UNCHANGED]` — count only

### Step 4 — Count task completion

In `tasks.md`, count:
- Total tasks: lines matching `- [ ]` or `- [x]`/`- [X]`
- Completed: lines matching `- [x]`/`- [X]`

### Step 5 — Write ARCHIVE.md

Write `specs/<feature>/ARCHIVE.md`:

```markdown
# Archive: <feature-name>

Archived: <TODAY>
Status: ✓ ALL VALIDATIONS PASSED  (or ⚠ ARCHIVED WITH WARNINGS if --force)

## Delta Summary

- ADDED:     N items
- MODIFIED:  N items
- REMOVED:   N items
- UNCHANGED: N items

### Added
- [item]

### Modified
- [item]

### Removed
- [item]

## Validation Results

| Type | E2E Status |
|------|-----------|
| Functional   | PASS |
| Performance  | PASS |
| Customer     | PASS |

## Tasks

- Total: N
- Completed: N

---
*Archived by SpecPack on <TODAY>.*
```

### Step 6 — Move feature directory

```
specs/<feature>/  →  specs/archive/<feature>/
```

Create `specs/archive/` if it does not exist.
If destination already exists: error and stop (do not overwrite without --force).

### Step 7 — Clear active feature

Write `{}` to `.specify/feature.json` to clear the active feature pointer.

### Step 8 — Report

```
[ARCHIVED] specs/<feature>/ → specs/archive/<feature>/

Delta:      +N added  ~N modified  -N removed
Validation: Functional ✓  Performance ✓  Customer ✓
Tasks:      N/N complete

ARCHIVE.md written.
```

Suggest next step: `/specpack.specify` to start the next feature.
