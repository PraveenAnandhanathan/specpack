---
description: Run customer validation — validates that the implementation serves the actual customer model defined in profiles/customer-profile.md. Covers critical user flows, scale, and segment-specific behaviour. Cross-references performance-profile.md for load targets.
handoffs:
  - label: Functional Validation
    agent: specpack.functionalvalidation
    prompt: Run functional validation checks.
  - label: Performance Validation
    agent: specpack.performancevalidation
    prompt: Run performance validation checks.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding.
If `--task <TASK_ID>` is provided, run granular per-task validation only.
If `--e2e` is provided (or no arguments after all tasks complete), run full customer validation suite.

## Outline

You are running customer validation. This validates that the implementation correctly serves real customers as modelled in `profiles/customer-profile.md`.

**Cross-profile awareness (mandatory)**:
- `profiles/performance-profile.md` — performance baselines that must hold under customer-scale load.
- `profiles/codebase-profile.md` — test framework and conventions.

---

### Step 1 — Load context

Read all of the following (if they exist):

1. `profiles/customer-profile.md` — **primary**: scale, usage patterns, segments, critical features, customer model.
2. `profiles/performance-profile.md` — **cross-reference**: ensure customer-scale load meets perf targets.
3. `profiles/codebase-profile.md` — test framework, test command, conventions.
4. `spec.md` — functional requirements to map to customer flows.
5. `plan.md` — technical implementation to validate against customer expectations.
6. `.specify/memory/constitution.md` — any customer-facing SLAs or non-negotiables.

**Extract from customer profile**:
- `PEAK_CONCURRENT` — max concurrent users
- `CRITICAL_FEATURES` — top features by usage frequency
- `USER_SEGMENTS` — list of user segments
- `CUSTOMER_VALIDATION_TARGETS` — table from customer profile

---

### Step 2 — Per-task customer validation

**Triggered when**: `--task <TASK_ID>` argument provided, or called from `/specpack.implement` after a task completes.

For the completed task:

1. Map the task to one or more **customer flows** from `profiles/customer-profile.md → Usage Patterns`.
   - If no customer flow is impacted: skip and output `[CUSTOMER: SKIPPED — no customer flow impact]`.

2. For each impacted flow, verify:
   - The flow is **completable** end-to-end with the current implementation state.
   - The flow works correctly for **all user segments** that use it (check segment-specific requirements).
   - The feature is accessible to the segments that use it most (top % from customer profile).

3. **Scale awareness check**: If this task handles a `CRITICAL_FEATURE`:
   - Cross-reference `profiles/performance-profile.md` — does this path meet perf targets at `PEAK_CONCURRENT` users?
   - Flag if perf targets not met under customer-realistic load.

4. Report:

```
┌──────────────────────────────────────────────────────────┐
│ Customer Validation — Task [ID]: [TASK_NAME]            │
├──────────────────────────────────────────────────────────┤
│ Customer flow: [FLOW_NAME]                              │
│ Segments affected: [SEGMENT_LIST]                       │
│ Flow completable: ✓ / ✗                                │
│ Segment coverage: ✓ all / ✗ [FAILING_SEGMENT]         │
│ Perf at peak load: ✓ / ⚠ / ✗                          │
│ [If FAIL: what breaks for which customers]             │
└──────────────────────────────────────────────────────────┘
```

5. Update `profiles/.validation-status.md` with this task's result.

---

### Step 3 — E2E customer validation

**Triggered when**: All tasks complete, or `--e2e` flag passed.

1. **Critical feature coverage**:
   For each feature in `CRITICAL_FEATURES` (ordered by usage %):
   - Verify it is implemented and reachable.
   - Run its primary user flow test (create if missing, following `codebase-profile.md` conventions).
   - Verify it works for each user segment that uses it.

2. **Scale simulation**:
   - Simulate `PEAK_CONCURRENT` users running the top 3 critical flows concurrently.
   - Measure response times — cross-reference against `profiles/performance-profile.md` baselines.
   - Flag any flow that degrades beyond acceptable thresholds at customer scale.

3. **Segment-specific validation**:
   For each `USER_SEGMENT`:
   - Identify the 2–3 most important flows for that segment.
   - Verify those flows work correctly for that segment's characteristics (plan tier, role, data volume, etc.).

4. **Regression check on existing customer flows**:
   - Run any pre-existing customer flow tests to ensure no regressions.
   - Flag any flow that previously worked but now fails.

5. **Customer satisfaction proxy check**:
   - Are error messages human-readable (not stack traces)?
   - Are critical flows accessible without friction (no unnecessary steps)?
   - Does the implementation match the customer model described in the profile?

6. Output E2E report:

```markdown
## Customer Validation — E2E Report

### Critical Features Coverage
| Feature | Usage % | Implemented | Flow Test | Segments OK | Status |
|---------|---------|-------------|-----------|-------------|--------|

### Scale Validation (at [PEAK_CONCURRENT] concurrent users)
| Flow | P90 (ms) | Perf Target | Status |
|------|----------|-------------|--------|

### Segment Validation
| Segment | Key Flows | Status | Notes |
|---------|-----------|--------|-------|

### Customer Profile Targets
| Check | Target | Actual | Status |
|-------|--------|--------|--------|

### Regressions
[None / list]

### Overall: ✓ PASS / ⚠ WARN / ✗ FAIL

### Customer Impact Summary
[1–2 sentence summary: "Customers can/cannot do X because Y"]
```

7. Update `profiles/.validation-status.md` with E2E result.

---

### Step 4 — Post-validation

- PASS: output `[CUSTOMER: ✓ PASS]`.
  - If all three validations (functional, performance, customer) show PASS in `profiles/.validation-status.md`: output the final consolidated status:
    ```
    ╔══════════════════════════════════════╗
    ║  ALL VALIDATIONS PASSED              ║
    ║  ✓ Functional  ✓ Performance  ✓ Customer ║
    ║  Implementation is ready for review. ║
    ╚══════════════════════════════════════╝
    ```
- WARN: output `[CUSTOMER: ⚠ WARN]` with specific customer impact and suggested fixes.
- FAIL: output `[CUSTOMER: ✗ FAIL]` describing which customers are affected, what breaks, and priority order for fixes.
