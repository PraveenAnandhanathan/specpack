---
description: Run performance validation — per-task checks during implementation AND full load simulation after completion. Validates against profiles/performance-profile.md baselines. Cross-references customer-profile.md for scale targets.
handoffs:
  - label: Functional Validation
    agent: specpack.functionalvalidation
    prompt: Run functional validation checks.
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
If `--e2e` is provided (or no arguments after all tasks complete), run full performance suite.

## Outline

You are running performance validation. This validates that the implementation meets the performance baselines defined in `profiles/performance-profile.md`.

**Cross-profile awareness**: Also load `profiles/customer-profile.md` — peak concurrent users and scale targets there define the load levels for performance tests.

---

### Step 1 — Load context

Read all of the following (if they exist):

1. `profiles/performance-profile.md` — **primary**: baselines, P90/P95/P99 targets, error budgets.
2. `profiles/customer-profile.md` — **secondary**: peak concurrent users, scale headroom, critical features.
3. `profiles/codebase-profile.md` — language / framework for test tooling decisions.
4. `spec.md` — to identify performance-sensitive endpoints/operations.
5. `plan.md` — architecture decisions affecting performance (caching, DB queries, async, etc.).
6. `.specify/memory/constitution.md` — any performance SLAs or NFRs defined.

**Detect performance test tooling**:
- Scan for: `k6`, `locust`, `artillery`, `autocannon`, `wrk`, `gatling`, `jmeter`, `ab` in `package.json`, `requirements.txt`, `pyproject.toml`, `Makefile`, `justfile`.
- Check `.github/workflows/` for performance test job steps.
- If found, use it. If not found, use lightweight in-process timing tests appropriate to the language.

---

### Step 2 — Per-task performance validation

**Triggered when**: `--task <TASK_ID>` argument provided, or called from `/specpack.implement` after a task completes.

For the completed task:

1. Identify if this task introduces or modifies a **performance-sensitive path** (API endpoint, DB query, loop, file I/O, network call, cache operation).
   - If not performance-sensitive: skip and output `[PERF: SKIPPED — not perf-sensitive]`.

2. For performance-sensitive tasks, run a **micro-benchmark**:
   - Instrument the relevant function/endpoint with timing.
   - Run N=100 (or framework minimum) iterations.
   - Capture: min, mean, P90, P99, max.

3. Compare against `profiles/performance-profile.md` targets:
   - If P90 ≤ target P90: PASS
   - If P90 > target P90 but ≤ critical threshold: WARN
   - If P90 > critical threshold: FAIL

4. Report:

```
┌─────────────────────────────────────────────────────┐
│ Performance Validation — Task [ID]: [TASK_NAME]     │
├─────────────────────────────────────────────────────┤
│ Path: [FUNCTION/ENDPOINT]                           │
│ P90: [X]ms  Target: [Y]ms  → ✓/⚠/✗               │
│ P99: [X]ms  Critical: [Y]ms → ✓/⚠/✗              │
│ [If FAIL/WARN: specific suggestion]                 │
└─────────────────────────────────────────────────────┘
```

5. Update `profiles/.validation-status.md` with this task's result.

---

### Step 3 — E2E performance validation

**Triggered when**: All tasks complete, or `--e2e` flag passed.

1. **Load scale from customer profile**:
   - Peak concurrent users: `[PEAK_CONCURRENT]` from `profiles/customer-profile.md`
   - Growth headroom: `[GROWTH]%` — test at `PEAK_CONCURRENT * (1 + GROWTH/100)`

2. **Run load test** against the full application:
   - If performance test tooling detected: use it with the scale targets above.
   - If not: write a concurrent-request test using the project's test framework.
   - Test scenarios: normal load (DAU level), peak load, spike (2x peak for 30s).

3. **Collect and compare** against all targets in `profiles/performance-profile.md → Performance Validation Targets` table.

4. **Check architecture-level concerns** from `plan.md`:
   - N+1 query patterns (if DB used)
   - Missing indexes (if schema present)
   - Synchronous calls in hot paths that could be async
   - Cache hit rates (if caching used)

5. Output E2E report:

```markdown
## Performance Validation — E2E Report

### Load Test Configuration
- Normal load: [X] concurrent users
- Peak load: [X] concurrent users  
- Spike: [X] concurrent users × 30s

### Results vs Baselines

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| P90 latency | ≤ Xms | Xms | ✓/⚠/✗ |
| P99 latency | ≤ Xms | Xms | ✓/⚠/✗ |
| Error rate | ≤ X% | X% | ✓/⚠/✗ |
| Throughput | ≥ X req/s | X req/s | ✓/⚠/✗ |

### Per-task Summary
| Task | Perf-sensitive | P90 | Status |
|------|---------------|-----|--------|

### Architecture Concerns
[None / list]

### Overall: ✓ PASS / ⚠ WARN / ✗ FAIL
```

6. Update `profiles/.validation-status.md` with E2E result.

---

### Step 4 — Post-validation

- PASS: output `[PERFORMANCE: ✓ PASS]` and suggest `/specpack.customervalidation`.
- WARN: output `[PERFORMANCE: ⚠ WARN]` with specific optimisation suggestions. User decides whether to address before proceeding.
- FAIL: output `[PERFORMANCE: ✗ FAIL]` with a prioritised fix list and estimated impact.
