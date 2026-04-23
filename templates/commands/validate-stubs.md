---
description: Confirm all stub tests are RED (failing) before implementation starts — the Red→Green pre-flight check.
handoffs:
  - label: Start Implementation
    agent: specpack.implement
    prompt: All stubs confirmed RED. Begin implementation.
---

## User Input

```text
$ARGUMENTS
```

## Outline

You are running the Red→Green pre-flight check. This confirms every stub test is **failing** before any code is written — a requirement of the Red→Green cycle.

### Step 1 — Run validate-stubs

Run the following command from the project root:

```
specify validate-stubs
```

Capture and display the full output.

### Step 2 — Interpret the results

**If all stubs are RED:**

```
[RED CONFIRMED] All N stubs are failing — Red→Green cycle ready.

Run /specpack.implement to begin implementation.
```

Suggest the next step: `/specpack.implement`.

**If any stubs are GREEN (already passing):**

```
[WARNING] N stub(s) are already GREEN:
  - <stub name> — test is passing before implementation

This means either:
  (a) The feature already exists in the codebase
  (b) The stub test is not actually testing the right thing

Review these stubs before proceeding.
```

Ask the user: "Do you want to proceed with implementation anyway, or fix the stubs first?"

**If no stubs are found:**

```
[NO STUBS] No stub tests found in specs/<feature>/tests/stubs/

Run /specpack.tasks first to generate stub tests.
```

Suggest running `/specpack.tasks`.

### Step 3 — Report

Display a concise summary table of all stub files and their RED/GREEN status, then give a clear go/no-go recommendation.
