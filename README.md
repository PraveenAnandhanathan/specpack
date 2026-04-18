<div align="center">
    <h1>SpecPack</h1>
    <h3><em>Spec-Driven Development for greenfield and brownfield projects.</em></h3>
    <p>Forked from <a href="https://github.com/github/spec-kit">GitHub Spec Kit</a></p>
</div>

<p align="center">
    <a href="https://github.com/PraveenAnandhanathan/specpack/releases/latest"><img src="https://img.shields.io/github/v/release/PraveenAnandhanathan/specpack" alt="Latest Release"/></a>
    <a href="https://github.com/PraveenAnandhanathan/specpack/stargazers"><img src="https://img.shields.io/github/stars/PraveenAnandhanathan/specpack?style=social" alt="GitHub stars"/></a>
    <a href="https://github.com/PraveenAnandhanathan/specpack/blob/main/LICENSE"><img src="https://img.shields.io/github/license/PraveenAnandhanathan/specpack" alt="License"/></a>
</p>

<p align="center">
    <strong>SpecPack extends Spec Kit with brownfield codebase profiling, Red→Green TDD cycle, delta change tracking, feature archiving, and progressive per-task validation — so AI-generated code adapts to existing projects, is verified before it ships, and leaves an audit trail when it's done.</strong>
</p>

---

## Table of Contents

- [What is SpecPack?](#what-is-specpack)
- [What SpecPack borrows — and why](#what-specpack-borrows--and-why)
- [SpecPack vs Spec Kit](#specpack-vs-spec-kit)
- [Install](#install)
- [Greenfield Flow](#greenfield-flow)
- [Brownfield Flow](#brownfield-flow)
- [Red→Green Cycle (TDD in SDD)](#redgreen-cycle-tdd-in-sdd)
- [Delta Tracking (from OpenSpec)](#delta-tracking-from-openspec)
- [Feature Archive (from OpenSpec)](#feature-archive-from-openspec)
- [All Commands & Flags](#all-commands--flags)
  - [specify init](#specify-init)
  - [specify analyse-codebase](#specify-analyse-codebase)
  - [specify analyse-performance](#specify-analyse-performance)
  - [specify analyse-customer](#specify-analyse-customer)
  - [specify validate-stubs](#specify-validate-stubs)
  - [specify delta](#specify-delta)
  - [specify archive](#specify-archive)
  - [specify serve](#specify-serve)
  - [AI Slash Commands](#ai-slash-commands)
- [Profiles Directory](#profiles-directory)
- [Progressive Validation](#progressive-validation)
- [Supported AI Agents](#supported-ai-agents)
- [Extensions & Presets](#extensions--presets)
- [Contributing](#contributing)
- [License](#license)

---

## What is SpecPack?

SpecPack is a CLI toolkit for **Spec-Driven Development (SDD)** — a workflow where you write precise specifications first and let AI agents generate code from them, rather than vibe-coding from scratch.

**Core idea**: The spec is the source of truth. Code is its expression.

SpecPack adds four key capabilities on top of Spec Kit:

1. **Brownfield profiling** — before writing specs, analyse an existing codebase, performance data, and customer reports. The profiles are automatically injected into the SDD flow so AI-generated code adapts to what already exists.

2. **Red→Green TDD cycle** — stub tests are generated before implementation. Every task must start RED (failing) and finish GREEN (passing). Inspired by classical Test-Driven Development.

3. **Delta change tracking** — every requirement in a brownfield spec is annotated `[ADDED]`, `[MODIFIED]`, `[REMOVED]`, or `[UNCHANGED]`. Inspired by OpenSpec's audit-first philosophy.

4. **Feature archiving** — completed features move to `specs/archive/` with an `ARCHIVE.md` record that captures the delta summary, validation results, and task completion stats. Also inspired by OpenSpec.

---

## What SpecPack borrows — and why

SpecPack draws ideas from two established SDD tools and adapts them to an AI-native, CLI-first workflow.

### From TDD — the Red→Green cycle

Classical **Test-Driven Development** (TDD) demands tests exist *before* code, and every test must start failing (RED) before the implementation makes it pass (GREEN). This creates a tight feedback loop: you can't claim a feature is done until the test proves it.

SpecPack adapts this for SDD:

- When `/specpack.tasks` runs, it generates **failing stub tests** for each non-infrastructure task and places them in `specs/<feature>/tests/stubs/`.
- Before implementation begins, `specify validate-stubs` confirms **all stubs are RED** — any stub already GREEN means the feature may already exist or the test is wrong.
- During `/specpack.implement`, each task follows the Red→Green cycle: confirm the stub is RED → write code → confirm it turns GREEN.
- A live **Red→Green dashboard** tracks which tasks have completed the cycle.

This is not full TDD — you're not writing unit tests for every line — but it brings TDD's core discipline (tests before code, explicit RED → GREEN transition) into a spec-driven workflow.

### From OpenSpec — delta tracking and feature archiving

**OpenSpec** is an SDD tool built around the idea that every change to an existing system must be explicitly classified. Its delta system requires every requirement to be marked as new, modified, removed, or unchanged — so reviewers always know what is changing and why.

SpecPack adapts this with two features:

**Delta markers** — when `/specpack.specify` runs against a brownfield project (a `profiles/codebase-profile.md` exists), it annotates every requirement with:

```
[ADDED]     — new capability, does not exist yet
[MODIFIED]  — changes existing behaviour (identifies what changes)
[REMOVED]   — explicitly removes existing functionality
[UNCHANGED] — existing functionality that must not regress
```

**Feature archive** — when a feature is fully implemented and validated, `specify archive` moves it from `specs/<feature>/` to `specs/archive/<feature>/` and writes an `ARCHIVE.md` with the full delta summary, validation outcomes, and task completion count. This gives you a permanent, queryable audit trail of every feature that shipped.

---

## SpecPack vs Spec Kit

| Capability | Spec Kit | SpecPack |
|-----------|---------|---------|
| Greenfield SDD flow | ✓ | ✓ |
| Brownfield codebase analysis | — | ✓ |
| Performance baseline profiling | — | ✓ |
| Customer data profiling | — | ✓ |
| Profile auto-injection into constitution | — | ✓ |
| Delta markers (`[ADDED]`/`[MODIFIED]`/`[REMOVED]`/`[UNCHANGED]`) | — | ✓ |
| `specify delta` — delta summary from spec/plan/tasks | — | ✓ |
| Stub test generation before implementation | — | ✓ |
| Red→Green cycle (`specify validate-stubs`) | — | ✓ |
| Per-task progressive validation | — | ✓ |
| Wholesome E2E validation suite | — | ✓ |
| Cross-profile validation (customer × performance) | — | ✓ |
| Existing test framework detection & reuse | — | ✓ |
| Feature archive (`specify archive` + `ARCHIVE.md`) | — | ✓ |
| Local web UI (`specify serve`) | — | ✓ |
| 30+ AI agent integrations | ✓ | ✓ |
| Extensions & presets system | ✓ | ✓ |

---

## Install

### Option 1 — pip (PyPI)

```bash
pip install specpack-cli                   # core
pip install 'specpack-cli[serve]'          # + web UI (specify serve)
```

### Option 2 — uv (PyPI)

```bash
uv tool install specpack-cli               # core
uv tool install 'specpack-cli[serve]'      # + web UI (specify serve)
```

`uv` installs from PyPI by default — no extra flags needed.

### Option 3 — Latest from GitHub (pre-release / edge)

```bash
uv tool install specpack-cli --from git+https://github.com/PraveenAnandhanathan/specpack.git
# or
pip install git+https://github.com/PraveenAnandhanathan/specpack.git
```

### Option 4 — Editable local install (development)

```bash
git clone https://github.com/PraveenAnandhanathan/specpack.git
cd specpack
pip install -e ".[test]"
```

Verify:

```bash
specify version        # shows SpecPack ASCII banner + version
specpack version       # alias — same result
```

---

## Greenfield Flow

Use this when starting a brand-new project with no existing codebase.

```
specify init <PROJECT_NAME> --ai <AGENT>
```

Then in your AI agent:

```
Step 1:  /specpack.constitution     ← define project principles and governance
Step 2:  /specpack.specify          ← write the feature specification
Step 3:  /specpack.plan             ← create the technical implementation plan
Step 4:  /specpack.tasks            ← break plan into ordered tasks + generate stub tests
Step 5:  specify validate-stubs     ← confirm all stubs are RED before coding starts
Step 6:  /specpack.implement        ← execute tasks, Red→Green per task, E2E when done
Step 7:  specify archive            ← move completed feature to specs/archive/ with ARCHIVE.md
Step 8:  specify serve              ← share specs with non-devs via local web UI (optional)
```

### Greenfield file output

```
.specify/
  memory/
    constitution.md
  feature.json                   ← active feature pointer
specs/
  001-feature-name/
    spec.md                      ← WHAT to build
    plan.md                      ← HOW to build it
    tasks.md                     ← ordered task list
    tests/
      stubs/
        T001_stub.py             ← failing stub test (RED before implement)
        T002_stub.py
    ARCHIVE.md                   ← written on archive (after implement)
  archive/
    001-feature-name/            ← moved here after specify archive
      ...
      ARCHIVE.md
```

---

## Brownfield Flow

Use this when adding new features to an **existing codebase** — so new code adapts to what's already there.

### Step 1 — Analyse (optional but recommended)

```bash
# Analyse existing codebase
specify analyse-codebase --here
specify analyse-codebase --here --static              # no AI tokens
specify analyse-codebase --repopath /path/to/repo
specify analyse-codebase --repourl https://github.com/org/repo    # public only

# Analyse performance data
specify analyse-performance --reportpath ./load-test-results/
specify analyse-performance --reportfile ./results.csv            # static parse

# Analyse customer data
specify analyse-customer --reportpath ./analytics-exports/
specify analyse-customer --reportfile ./users.json                # static parse
```

Each command writes a profile to `profiles/`:

```
profiles/
  codebase-profile.md        ← languages, conventions, test framework, structure
  performance-profile.md     ← P90/P95/P99 baselines, throughput, error budget
  customer-profile.md        ← scale, usage patterns, segments
```

### Step 2 — SDD flow (profile-aware, delta-annotated)

```
specify init . --ai <AGENT>   ← or skip if already initialised
```

In your AI agent:

```
Step 1:  /specpack.constitution     ← auto-reads profiles/, embeds as constraints
Step 2:  /specpack.specify          ← writes spec with [ADDED]/[MODIFIED]/[REMOVED]/[UNCHANGED] markers
Step 3:  /specpack.plan             ← plan respects existing code style and perf baselines
Step 4:  /specpack.tasks            ← tasks align with existing test framework + generate stubs
Step 5:  specify validate-stubs     ← confirm all stubs are RED
Step 6:  specify delta              ← review what's changing before implementation
Step 7:  /specpack.implement        ← Red→Green per task, E2E when all tasks done
Step 8:  specify archive            ← archive with ARCHIVE.md (delta + validation record)
Step 9:  specify serve              ← share specs and archive with stakeholders (optional)
```

### Brownfield file output

Everything from greenfield, plus:

```
profiles/
  codebase-profile.md
  performance-profile.md
  customer-profile.md
  .validation-status.md      ← per-task and E2E results (auto-generated during implement)
```

---

## Red→Green Cycle (TDD in SDD)

SpecPack adapts TDD's Red→Green discipline into the SDD flow. The idea: every task must have a failing test *before* code is written, and the task is only complete when the test passes.

### How it works

**1. Stub generation (during `/specpack.tasks`)**

For each non-infrastructure task, the AI generates a minimal failing test:

```python
# specs/001-auth/tests/stubs/T001_stub.py
def test_T001_stub():
    assert False, "not implemented — user registration endpoint"
```

Stubs are placed in `specs/<feature>/tests/stubs/` and are explicitly written to fail.

**2. Pre-flight confirmation (`specify validate-stubs`)**

Run this before implementation starts:

```bash
specify validate-stubs
```

```
┌──────────────────────────────────┬────────┬──────────────────────────────────┐
│ Stub File                        │ Status │ Note                             │
├──────────────────────────────────┼────────┼──────────────────────────────────┤
│ T001_stub.py                     │ 🔴 RED │ Correct — test is failing        │
│ T002_stub.py                     │ 🔴 RED │ Correct — test is failing        │
│ T003_stub.py                     │ 🔴 RED │ Correct — test is failing        │
└──────────────────────────────────┴────────┴──────────────────────────────────┘

✓  3 stubs confirmed RED — ready for implementation.
```

If any stub is already GREEN, SpecPack warns you — the feature may already exist or the test is wrong.

**3. Per-task Red→Green (during `/specpack.implement`)**

Before writing code for each task: confirm its stub is RED.
After completing each task: the stub must turn GREEN.

The live dashboard tracks progress:

```
┌──────────────────────────────────────────────────────┐
│ SpecPack — Red→Green Dashboard                       │
├──────────────────────────────────────────────────────┤
│ Tasks: 2/4 complete                                  │
│                                                      │
│ T001  🔴→🟢  Create user registration endpoint      │
│ T002  🔴→🟢  Add email verification flow             │
│ T003  🔴→⏳  Update login handler         ← in progress
│ T004  ⬜      Add 2FA support              ← pending  │
├──────────────────────────────────────────────────────┤
│ Functional   ✓ 2 passed / - 0 failed                 │
│ Performance  ✓ 1 passed / ⚠ 1 warn                  │
│ Customer     ✓ 2 passed / - skip                     │
└──────────────────────────────────────────────────────┘
```

---

## Delta Tracking (from OpenSpec)

When working on an existing codebase, every requirement in `spec.md` is annotated with a delta marker. This makes it immediately clear what the feature changes, adds, or removes — for reviewers, for the AI, and for the archive record.

### Markers

| Marker | Meaning |
|--------|---------|
| `[ADDED]` | New capability that does not exist yet |
| `[MODIFIED]` | Changes existing behaviour — the spec identifies what changes |
| `[REMOVED]` | Explicitly removes existing functionality |
| `[UNCHANGED]` | Existing functionality that must not regress |

### How markers appear in specs

```markdown
## Functional Requirements

- [ADDED] Users can register with email and password
- [MODIFIED] Login now requires 2FA (was: single-factor only)
- [REMOVED] SMS OTP login method
- [UNCHANGED] OAuth via Google — must not regress
```

Delta markers are also placed in `plan.md` and `tasks.md` as the AI propagates them downstream.

### `specify delta` command

At any point, get a summary of what this feature changes:

```bash
specify delta
specify delta --feature specs/001-auth
```

```
Delta Summary — specs/001-auth

  ADDED:      3 items
  MODIFIED:   2 items
  REMOVED:    1 item
  UNCHANGED:  4 items

Added:
  - Users can register with email and password  (spec.md)
  - New auth service module                     (plan.md)
  - Create auth endpoint                        (tasks.md)
  ...
```

Delta markers are also captured in `ARCHIVE.md` when the feature is archived.

---

## Feature Archive (from OpenSpec)

When a feature is fully implemented and validated, archive it to clear the active feature slot and preserve a permanent record.

```bash
specify archive
specify archive --feature specs/001-auth          # explicit feature path
specify archive --force                           # skip validation gate
```

### What archive does

1. **Validation gate** — checks `profiles/.validation-status.md`. Blocks if any E2E result is FAIL or UNKNOWN. Use `--force` to override.
2. **Builds delta summary** — counts `[ADDED]`, `[MODIFIED]`, `[REMOVED]`, `[UNCHANGED]` across spec/plan/tasks.
3. **Writes `ARCHIVE.md`** — permanent audit record inside the feature directory.
4. **Moves directory** — `specs/001-auth/` → `specs/archive/001-auth/`
5. **Clears active feature** — writes `{}` to `.specify/feature.json`.

### ARCHIVE.md contents

```markdown
# Archive: 001-auth

Archived: 2026-04-19
Status: ✓ ALL VALIDATIONS PASSED

## Delta Summary

- ADDED:     3 items
- MODIFIED:  2 items
- REMOVED:   1 item
- UNCHANGED: 4 items

### Added
- User registration with email
- New auth service
- Auth endpoint

### Modified
- Login now requires 2FA

### Removed
- SMS OTP

## Validation Results

| Type         | E2E Status |
|--------------|-----------|
| Functional   | PASS |
| Performance  | PASS |
| Customer     | PASS |

## Tasks

- Total: 5
- Completed: 5

---
*Archived by SpecPack on 2026-04-19.*
```

---

## All Commands & Flags

### `specify init`

Initialise a new SpecPack project.

```bash
specify init <PROJECT_NAME>         # create new directory
specify init .                      # init in current directory
specify init --here                 # same as .
specify init . --ai claude          # specify AI agent integration
specify init . --ai copilot
specify init . --ai cursor
# supports 30+ agents (see: specify integration list)
```

---

### `specify analyse-codebase`

Analyse an existing codebase and write `profiles/codebase-profile.md`.

```bash
specify analyse-codebase --here
```
Analyse the current working directory.

```bash
specify analyse-codebase --repopath /path/to/repo
```
Analyse a local repo at the given path.

```bash
specify analyse-codebase --repourl https://github.com/org/repo
```
Clone a public GitHub repo, analyse it, then delete the clone.

```bash
specify analyse-codebase --here --static
specify analyse-codebase --repopath /path/to/repo --static
```
`--static` flag: pure filesystem scan — **no AI tokens used**. Detects languages, file counts, project structure, test frameworks, and code style tools.

Without `--static`: triggers `/specpack.analyse-codebase` in your AI agent for deep semantic analysis (naming conventions, module patterns, error handling style).

**Output**: `profiles/codebase-profile.md`

---

### `specify analyse-performance`

Analyse performance reports and write `profiles/performance-profile.md`.

```bash
specify analyse-performance --reportpath /path/to/reports/
```
AI-assisted analysis of a directory of report files (`.csv`, `.json`, `.yaml`, `.yml`, `.jtl`, Gatling `simulation.log`, k6 output, Locust CSVs).

```bash
specify analyse-performance --reportfile /path/to/results.csv
specify analyse-performance --reportfile /path/to/results.json
```
`--reportfile`: **static parse — no AI**. Extracts latency stats (P50/P90/P95/P99), throughput, and error rate, and auto-generates implementation constraints.

**Output**: `profiles/performance-profile.md`

---

### `specify analyse-customer`

Analyse customer/analytics data and write `profiles/customer-profile.md`.

```bash
specify analyse-customer --reportpath /path/to/analytics/
```
AI-assisted analysis of a directory of customer data files.

```bash
specify analyse-customer --reportfile /path/to/users.csv
specify analyse-customer --reportfile /path/to/cohorts.json
```
`--reportfile`: **static parse — no AI**. Extracts user counts, DAU/MAU, peak concurrent, session patterns, and user segments.

**Output**: `profiles/customer-profile.md`

---

### `specify validate-stubs`

Confirm all stub tests in the active feature are RED (failing) before implementation starts.

```bash
specify validate-stubs
```

- Scans `specs/<feature>/tests/stubs/` for stub files.
- Runs each stub with the detected test command (`pytest`, `jest`, `go test`, etc.).
- Reports RED (correct — expected failure) or GREEN (warning — already passing).
- Exits non-zero if no stubs found (to catch missing stub generation step).

**When to run**: after `/specpack.tasks` generates stubs, before `/specpack.implement` begins.

---

### `specify delta`

Show a summary of all delta markers (`[ADDED]`, `[MODIFIED]`, `[REMOVED]`, `[UNCHANGED]`) in the active feature's spec, plan, and tasks files.

```bash
specify delta
specify delta --feature specs/001-auth
```

Uses the active feature from `.specify/feature.json` if `--feature` is not provided.

**When to run**: before implementation to review scope; captured automatically in `ARCHIVE.md` on archive.

---

### `specify archive`

Archive a completed feature — moves `specs/<feature>/` to `specs/archive/<feature>/` and writes `ARCHIVE.md`.

```bash
specify archive
specify archive --feature specs/001-auth
specify archive --force                    # skip validation gate
```

**Validation gate** (skipped with `--force`): reads `profiles/.validation-status.md` and blocks if any E2E result is FAIL or UNKNOWN.

**When to run**: after all tasks are complete and `/specpack.implement` E2E has passed. The `/specpack.implement` command will prompt you to archive automatically.

---

### `specify serve`

Start a local read-only web UI that renders specs, archive, and profiles — for sharing with non-devs.

```bash
specify serve                        # http://127.0.0.1:4242, auto-opens browser
specify serve --port 8080
specify serve --host 0.0.0.0         # accessible on local network
specify serve --no-browser           # don't auto-open browser
```

Requires the `[serve]` optional extra:

```bash
pip install 'specpack-cli[serve]'
uv tool install 'specpack-cli[serve]'
```

**What it shows:**

| Page | URL | Content |
|------|-----|---------|
| Dashboard | `/` | Active features with delta badges and task progress |
| Feature | `/feature/<name>` | Spec / Plan / Tasks / Delta tabs, delta markers colour-coded |
| Archive | `/archive` | All archived features with dates and validation badges |
| Archive detail | `/archive/<name>` | ARCHIVE.md + spec/plan/tasks tabs |
| Profiles | `/profiles` | Codebase, performance, customer profiles side by side |

The UI is **read-only** — no editing. Designed for sharing specs with PMs, designers, and QA who don't use the CLI.

---

### AI Slash Commands

These run inside your AI agent (Claude Code, Cursor, Copilot, etc.) after `specify init`.

| Command | What it does |
|---------|-------------|
| `/specpack.constitution` | Create/update project constitution. Auto-reads `profiles/` and embeds codebase, performance, and customer constraints. |
| `/specpack.specify` | Write the feature spec (`spec.md`). In brownfield projects, annotates every requirement with `[ADDED]/[MODIFIED]/[REMOVED]/[UNCHANGED]`. |
| `/specpack.plan` | Create the implementation plan (`plan.md`). Respects codebase style and performance baselines. |
| `/specpack.tasks` | Break the plan into ordered tasks (`tasks.md`). Generates failing stub tests for each task. |
| `/specpack.implement` | Execute tasks with Red→Green per task, progressive validation dashboard, wholesome E2E after all complete, auto-archive prompt. |
| `/specpack.archive` | Archive a completed feature — writes `ARCHIVE.md`, moves to `specs/archive/`. |
| `/specpack.analyse-codebase` | AI-assisted codebase analysis. Writes `profiles/codebase-profile.md`. |
| `/specpack.analyse-performance` | AI-assisted performance analysis. Writes `profiles/performance-profile.md`. |
| `/specpack.analyse-customer` | AI-assisted customer analysis. Writes `profiles/customer-profile.md`. |
| `/specpack.functionalvalidation` | Functional validation — per-task (`--task T1`) or full E2E (`--e2e`). Uses existing test framework. |
| `/specpack.performancevalidation` | Performance validation — micro-benchmarks per task or full load test E2E. Cross-references customer profile for scale targets. |
| `/specpack.customervalidation` | Customer flow validation — per-task and E2E. Cross-references performance profile. |
| `/specpack.clarify` | Clarify ambiguous requirements in the spec. |
| `/specpack.analyze` | Cross-artifact consistency check (spec, plan, tasks). |
| `/specpack.checklist` | Generate domain-specific checklists. |

**Arguments**: pass arguments after the command name.

```
/specpack.specify add user authentication with email and Google OAuth
/specpack.implement start with the auth module
/specpack.functionalvalidation --task T3
/specpack.performancevalidation --e2e
/specpack.archive --force
```

---

## Profiles Directory

```
profiles/
  codebase-profile.md
  performance-profile.md
  customer-profile.md
  .validation-status.md      ← auto-generated during /specpack.implement
```

**Profiles are optional.** If none exist, the SDD flow works exactly like Spec Kit.

**If profiles exist**, `/specpack.constitution` automatically injects them:

```markdown
## Brownfield Profiles  (in constitution.md)

### Codebase Constraints
[language, naming conventions, test framework, test command, style rules]

### Performance Baselines
[P90/P95/P99 targets — every implementation task must meet these]

### Customer Context
[peak scale, critical features, segments — ground all decisions in real data]
```

**Cross-profile awareness**: each validation command reads all profiles.

| Validation | Primary profile | Also reads |
|-----------|----------------|-----------|
| `/specpack.functionalvalidation` | `spec.md` | `codebase-profile.md` (test framework) |
| `/specpack.performancevalidation` | `performance-profile.md` | `customer-profile.md` (scale/concurrency) |
| `/specpack.customervalidation` | `customer-profile.md` | `performance-profile.md` (perf at customer scale) |

---

## Progressive Validation

During `/specpack.implement`, after **each task** is marked complete:

```
Task 1 ✓  →  [FUNCTIONAL: ✓ PASS]  [PERF: SKIPPED]           [CUSTOMER: ✓ PASS]
Task 2 ✓  →  [FUNCTIONAL: ✓ PASS]  [PERF: ⚠ WARN P90 near]  [CUSTOMER: SKIPPED]
Task 3 ✓  →  [FUNCTIONAL: ✗ FAIL]  [PERF: ✓ PASS]            [CUSTOMER: ✓ PASS]
```

Live dashboard:

```
┌──────────────────────────────────────────────────┐
│ SpecPack Validation Dashboard                    │
├──────────────────────────────────────────────────┤
│ Tasks: 3/8 complete                              │
│                                                  │
│ Functional   ✗ 1 failed / ✓ 2 passed            │
│ Performance  ⚠ 1 warn   / ✓ 1 passed / - 1 skip │
│ Customer     ✓ 2 passed / - 1 skipped           │
└──────────────────────────────────────────────────┘
```

Failures do **not** halt implementation — you address them in the E2E phase.

### Wholesome E2E (after all tasks complete)

Once all tasks are marked `[X]` in `tasks.md`, three E2E commands run sequentially:

1. **`/specpack.functionalvalidation --e2e`** — full test suite, spec coverage check, cross-feature regression
2. **`/specpack.performancevalidation --e2e`** — load test at customer-scale concurrency, normal/peak/spike scenarios
3. **`/specpack.customervalidation --e2e`** — critical feature coverage for all segments, scale simulation

Final output:

```
╔══════════════════════════════════════════════════════╗
║  SpecPack Implementation Complete                    ║
╠══════════════════════════════════════════════════════╣
║  Functional   ✓ PASS                                ║
║  Performance  ✓ PASS                                ║
║  Customer     ✓ PASS                                ║
╠══════════════════════════════════════════════════════╣
║  Overall:  READY FOR REVIEW                         ║
╚══════════════════════════════════════════════════════╝
```

After all E2E validations pass, `/specpack.implement` prompts:

```
All validations passed. Archive this feature? (yes/no)
```

Answering yes runs `specify archive` automatically.

### Test framework detection

SpecPack detects your existing test framework from (priority order):

1. `profiles/codebase-profile.md` → `Test framework:` and `Test command:` fields
2. Mentions in `constitution.md`, `spec.md`, `plan.md`, `tasks.md`
3. Config files: `jest.config.*`, `pytest.ini`, `pyproject.toml [tool.pytest]`, `vitest.config.*`, `.rspec`, etc.

It **reuses your existing framework** — it does not create a new one.

---

## Supported AI Agents

SpecPack supports 30+ AI coding agents:

```bash
specify init . --ai claude          # Claude Code
specify init . --ai copilot         # GitHub Copilot
specify init . --ai cursor          # Cursor
specify init . --ai windsurf        # Windsurf
specify init . --ai gemini          # Google Gemini
specify init . --ai codex           # OpenAI Codex CLI
specify init . --ai codeium         # Codeium
specify init . --ai continue        # Continue.dev
# ...and more
specify integration list            # see all available
```

---

## Extensions & Presets

### Extensions

```bash
specify extension list
specify extension add git                     # adds /specpack.git.* commands
specify extension add <name> --from <url>
specify extension remove <name>
```

### Presets

```bash
specify preset list
specify preset add lean                       # minimal, token-efficient preset
specify preset add <name>
specify preset remove <name>
```

### Syncing with upstream Spec Kit

```bash
git fetch upstream
git merge upstream/main
```

Upstream: `https://github.com/github/spec-kit.git`

---

## Contributing

```bash
git clone https://github.com/PraveenAnandhanathan/specpack.git
cd specpack
pip install -e ".[test]"
pytest tests/
```

- New AI slash commands → `templates/commands/`
- Python CLI commands → `src/specify_cli/`
- Brownfield analysis → `src/specify_cli/analyse.py`
- Delta/archive/validate-stubs → `src/specify_cli/delta_archive.py`

---

## License

MIT — see [LICENSE](./LICENSE).

Original Spec Kit by GitHub. SpecPack extensions by [PraveenAnandhanathan](https://github.com/PraveenAnandhanathan).
