---
description: Run functional validation against spec.md — per-task granular checks during implementation AND full E2E suite after completion. Uses existing test framework if detected in project profiles/constitution.
handoffs:
  - label: Performance Validation
    agent: specpack.performancevalidation
    prompt: Run performance validation checks.
  - label: Customer Validation
    agent: specpack.customervalidation
    prompt: Run customer validation checks.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding.
If `--task <TASK_ID>` is provided, run granular per-task validation only.
If `--e2e` is provided (or no arguments after all tasks complete), run full E2E suite.

## Outline

You are running functional validation. This command runs in two modes:

- **Per-task mode** (triggered automatically after each task during `/specpack.implement`): validates that the just-completed task meets its functional requirement from `spec.md`.
- **E2E mode** (triggered after all tasks complete): runs the full functional test suite end-to-end.

Both modes use the existing test framework if one is detected — **do not create a new framework**.

---

### Step 1 — Load context

Read all of the following (if they exist):

1. `spec.md` — the functional source of truth. Every requirement here must be met.
2. `plan.md` — architecture context.
3. `tasks.md` — task list with IDs and descriptions.
4. `profiles/codebase-profile.md` — to know test framework, test command, test file naming.
5. `.specify/memory/constitution.md` — project-level constraints.

**Detect test framework** (priority order):
1. From `profiles/codebase-profile.md` → `Test framework:` and `Test command:` fields.
2. Scan `.specify/memory/constitution.md`, `spec.md`, `plan.md`, `tasks.md` for any mention of test frameworks (Jest, pytest, JUnit, RSpec, Vitest, Mocha, PHPUnit, Go test, etc.).
3. Check config files: `jest.config.*`, `pytest.ini`, `pyproject.toml [tool.pytest]`, `vitest.config.*`, etc.
4. If none found: use language-appropriate default and note it.

Record: `TEST_FRAMEWORK`, `TEST_COMMAND`, `TEST_FILE_PATTERN`, `TEST_DIR`.

---

### Step 2 — Per-task validation mode

**Triggered when**: `--task <TASK_ID>` argument provided, or called from `/specpack.implement` after a task completes.

1. Identify the task from `tasks.md` by ID.
2. Map the task to the corresponding requirement(s) in `spec.md` (match by feature area, keyword, or explicit reference).
3. Check if a test already exists for this task's scope:
   - Search `TEST_DIR` for test files matching `TEST_FILE_PATTERN` that cover this task's files/functions.
4. **If test exists**: Run `TEST_COMMAND --testPathPattern <relevant_pattern>` (or equivalent) and capture result.
5. **If no test exists**: Write a targeted test for this task's requirement:
   - Follow the naming convention from `profiles/codebase-profile.md`.
   - Test only the scope of this specific task (unit/integration, not E2E).
   - Run the new test immediately.
6. Report result:

```
┌─────────────────────────────────────────────────┐
│ Functional Validation — Task [ID]: [TASK_NAME]  │
├─────────────────────────────────────────────────┤
│ Requirement: [FROM_SPEC_MD]                     │
│ Test: [TEST_FILE]:[TEST_NAME]                   │
│ Result: ✓ PASS / ✗ FAIL                        │
│ [If FAIL: failure message + suggested fix]      │
└─────────────────────────────────────────────────┘
```

7. **If FAIL**: Report the failure and pause. Do not auto-fix. Let the implementer address it.
8. Update `profiles/.validation-status.md` with this task's result (create if not exists).

---

### Step 3 — E2E validation mode

**Triggered when**: All tasks in `tasks.md` are marked `[X]`, or `--e2e` flag passed.

1. Verify all per-task validations in `profiles/.validation-status.md` passed. List any that failed.
2. **Full test suite run**: Execute `TEST_COMMAND` (full suite, no filter).
3. **Integration tests**: If an integration test directory exists (`tests/integration/`, `e2e/`, `cypress/`, `playwright/`), run those too.
4. **Spec coverage check**: For each requirement in `spec.md`, confirm at least one test covers it. List uncovered requirements as gaps.
5. **Cross-feature regression check**: Run any tests outside the current feature's scope to detect regressions.

6. Output E2E report:

```markdown
## Functional Validation — E2E Report

### Per-task Summary
| Task | Requirement | Status |
|------|------------|--------|
| T1   | ...        | ✓ PASS |
| T2   | ...        | ✗ FAIL |

### Full Suite
- Tests run: X
- Passed: X
- Failed: X
- Coverage: X%

### Spec Coverage
| Requirement | Covered By | Status |
|-------------|-----------|--------|

### Regressions
[None / list of regressions detected]

### Overall: ✓ PASS / ✗ FAIL
```

7. Update `profiles/.validation-status.md` with E2E result.

---

### Step 4 — Post-validation

- If ALL checks pass: output `[FUNCTIONAL: ✓ PASS]` and suggest next step (`/specpack.performancevalidation`).
- If ANY check fails: output `[FUNCTIONAL: ✗ FAIL]` with a prioritised fix list. Do not proceed to other validations automatically — let the user decide.
