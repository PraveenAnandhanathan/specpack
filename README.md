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
    <strong>SpecPack extends Spec Kit with brownfield codebase profiling, performance and customer analysis, and progressive per-task validation — so AI-generated code adapts to existing projects and is validated against real data.</strong>
</p>

---

## Table of Contents

- [What is SpecPack?](#what-is-specpack)
- [SpecPack vs Spec Kit](#specpack-vs-spec-kit)
- [Install](#install)
- [Greenfield Flow](#greenfield-flow)
- [Brownfield Flow](#brownfield-flow)
- [All Commands & Flags](#all-commands--flags)
  - [specify analyse-codebase](#specify-analyse-codebase)
  - [specify analyse-performance](#specify-analyse-performance)
  - [specify analyse-customer](#specify-analyse-customer)
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

SpecPack adds two key capabilities on top of Spec Kit:

1. **Brownfield profiling** — before writing specs, analyse an existing codebase, performance data, and customer reports. The profiles are automatically injected into the SDD flow so AI-generated code adapts to what already exists.

2. **Progressive parallel validation** — functional, performance, and customer validation fires after *each implemented task*, not just at the end. By the time all tasks are done, you have per-task coverage plus a wholesome E2E suite.

---

## SpecPack vs Spec Kit

| Capability | Spec Kit | SpecPack |
|-----------|---------|---------|
| Greenfield SDD flow | ✓ | ✓ |
| Brownfield codebase analysis | — | ✓ |
| Performance baseline profiling | — | ✓ |
| Customer data profiling | — | ✓ |
| Profile auto-injection into constitution | — | ✓ |
| Per-task progressive validation | — | ✓ |
| Wholesome E2E validation suite | — | ✓ |
| Cross-profile validation (customer × performance) | — | ✓ |
| Existing test framework detection & reuse | — | ✓ |
| 30+ AI agent integrations | ✓ | ✓ |
| Extensions & presets system | ✓ | ✓ |

---

## Install

### Option 1 — Persistent install (recommended)

```bash
uv tool install specpack-cli --from git+https://github.com/PraveenAnandhanathan/specpack.git
```

### Option 2 — Latest from main

```bash
uv tool install specpack-cli --from git+https://github.com/PraveenAnandhanathan/specpack.git@main
```

### Option 3 — Editable local install

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
Step 4:  /specpack.tasks            ← break plan into ordered tasks
Step 5:  /specpack.implement        ← AI executes tasks + progressive validation fires per task
                                       + wholesome E2E after all tasks complete
```

### Greenfield file output

```
.specify/
  memory/
    constitution.md          ← project principles (source of truth for all SDD)
  templates/
    spec-template.md
    plan-template.md
    tasks-template.md
    constitution-template.md
specs/
  001-feature-name/
    spec.md                  ← WHAT to build
    plan.md                  ← HOW to build it (tech approach)
    tasks.md                 ← ordered task list for AI
    data-model.md            ← data structures (if applicable)
    research.md              ← background decisions (if applicable)
    contracts/               ← API contracts (if applicable)
```

---

## Brownfield Flow

Use this when adding new features to an **existing codebase** — so new code adapts to what's already there.

### Step 1 — Analyse (optional but recommended)

Run one or more of these before starting the SDD flow:

```bash
# Analyse existing codebase
specify analyse-codebase --here
specify analyse-codebase --here --static              # no AI tokens
specify analyse-codebase --repopath /path/to/repo
specify analyse-codebase --repopath /path/to/repo --static
specify analyse-codebase --repourl https://github.com/org/repo    # public only

# Analyse performance data
specify analyse-performance --reportpath ./load-test-results/     # AI analyses all files
specify analyse-performance --reportfile ./results.csv            # static parse, no AI

# Analyse customer data
specify analyse-customer --reportpath ./analytics-exports/        # AI analyses all files
specify analyse-customer --reportfile ./users.json                # static parse, no AI
```

Each command writes a profile to `profiles/`:

```
profiles/
  codebase-profile.md        ← languages, conventions, test framework, structure
  performance-profile.md     ← P90/P95/P99 baselines, throughput, error budget
  customer-profile.md        ← scale, usage patterns, segments, customer model
```

### Step 2 — SDD flow (same as greenfield, now profile-aware)

```
specify init . --ai <AGENT>   ← or skip if already initialised
```

In your AI agent:

```
Step 1:  /specpack.constitution     ← auto-reads profiles/ and embeds them as constraints
Step 2:  /specpack.specify          ← spec inherits codebase, perf, and customer constraints
Step 3:  /specpack.plan             ← plan respects existing code style and perf baselines
Step 4:  /specpack.tasks            ← tasks align with existing test framework
Step 5:  /specpack.implement        ← progressive validation uses existing test framework
```

### Brownfield file output

Everything from the greenfield flow, plus:

```
profiles/
  codebase-profile.md
  performance-profile.md
  customer-profile.md
  .validation-status.md      ← per-task and E2E validation results (auto-generated)
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
# ...supports 30+ agents (see: specify integration list)
```

---

### `specify analyse-codebase`

Analyse an existing codebase and write `profiles/codebase-profile.md`.

```bash
specify analyse-codebase --here
```
Analyse the current working directory. Requires project to be initialised (`specify init` run first) so `profiles/` has a home.

```bash
specify analyse-codebase --repopath /path/to/repo
```
Analyse a local repo at the given path. Profile is written to `profiles/` in the current working directory.

```bash
specify analyse-codebase --repourl https://github.com/org/repo
```
Clone a public GitHub repo, analyse it, then delete the clone. No auth required. Profile written to current working directory.

```bash
specify analyse-codebase --here --static
specify analyse-codebase --repopath /path/to/repo --static
specify analyse-codebase --repourl https://github.com/org/repo --static
```
`--static` flag: pure filesystem scan — **no AI tokens used**. Detects:
- File extensions and counts
- Language distribution
- Project structure (directory tree, up to 4 levels)
- Frameworks and tooling (from config files: `package.json`, `pyproject.toml`, `pom.xml`, `Cargo.toml`, etc.)
- Test frameworks (from `pytest.ini`, `jest.config.*`, `vitest.config.*`, etc.)
- Code style tools (ESLint, Prettier, Ruff, EditorConfig)

Without `--static`: triggers `/specpack.analyse-codebase` in your AI agent for deep semantic analysis (naming conventions, module patterns, error handling style, etc.).

**Output**: `profiles/codebase-profile.md`

---

### `specify analyse-performance`

Analyse performance reports and write `profiles/performance-profile.md`.

```bash
specify analyse-performance --reportpath /path/to/reports/
```
AI-assisted analysis of a directory of report files (`.csv`, `.json`, `.yaml`, `.yml`, `.jtl`, Gatling `simulation.log`, k6 output, Locust CSVs). Triggers `/specpack.analyse-performance` in your AI agent.

```bash
specify analyse-performance --reportfile /path/to/results.csv
specify analyse-performance --reportfile /path/to/results.json
specify analyse-performance --reportfile /path/to/results.yaml
```
`--reportfile`: **static parse — no AI tokens**. Parses the file directly and extracts:
- Latency stats: min, mean, P50, P90, P95, P99, max
- Throughput stats
- Error rate stats
- Auto-generates implementation constraints from the baselines

Supported formats: `.csv`, `.json`, `.yaml` / `.yml`

**Output**: `profiles/performance-profile.md`

---

### `specify analyse-customer`

Analyse customer/analytics reports and write `profiles/customer-profile.md`.

```bash
specify analyse-customer --reportpath /path/to/analytics/
```
AI-assisted analysis of a directory of customer data files. Triggers `/specpack.analyse-customer` in your AI agent.

```bash
specify analyse-customer --reportfile /path/to/users.csv
specify analyse-customer --reportfile /path/to/cohorts.json
specify analyse-customer --reportfile /path/to/events.yaml
```
`--reportfile`: **static parse — no AI tokens**. Parses the file and extracts:
- Scale metrics (user counts, DAU/MAU, peak concurrent)
- Usage pattern metrics (session length, frequency)
- Categorical distributions (segments, plans, regions)
- Auto-generates scale-based implementation constraints

Supported formats: `.csv`, `.json`, `.yaml` / `.yml`

**Output**: `profiles/customer-profile.md`

---

### AI Slash Commands

These run inside your AI agent (Claude Code, Cursor, Copilot, etc.) after `specify init`.

| Command | What it does |
|---------|-------------|
| `/specpack.constitution` | Create/update project constitution. Auto-reads `profiles/` and embeds codebase, performance, and customer constraints. |
| `/specpack.specify` | Write the feature specification (`spec.md`). Inherits all constraints from constitution. |
| `/specpack.plan` | Create the technical implementation plan (`plan.md`). Respects codebase style and performance baselines. |
| `/specpack.tasks` | Break the plan into ordered, executable tasks (`tasks.md`). Aligns with detected test framework. |
| `/specpack.implement` | Execute tasks with progressive per-task validation. Runs E2E suite when all tasks complete. |
| `/specpack.analyse-codebase` | AI-assisted codebase analysis (when `--static` not used). Writes `profiles/codebase-profile.md`. |
| `/specpack.analyse-performance` | AI-assisted performance analysis (when `--reportpath` used). Writes `profiles/performance-profile.md`. |
| `/specpack.analyse-customer` | AI-assisted customer analysis (when `--reportpath` used). Writes `profiles/customer-profile.md`. |
| `/specpack.functionalvalidation` | Functional validation — per-task (`--task T1`) or full E2E (`--e2e`). Uses existing test framework. |
| `/specpack.performancevalidation` | Performance validation — per-task micro-benchmarks or full load test E2E. Cross-references customer profile for scale targets. |
| `/specpack.customervalidation` | Customer flow validation — per-task and E2E. Cross-references performance profile for load targets. |
| `/specpack.clarify` | Clarify ambiguous requirements in the spec. |
| `/specpack.analyze` | Cross-artifact consistency check (spec, plan, tasks). |
| `/specpack.checklist` | Generate domain-specific checklists. |

**Arguments**: pass arguments after the command name. Example:
```
/specpack.implement start with the auth module
/specpack.functionalvalidation --task T3
/specpack.performancevalidation --e2e
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

These constraints then flow downstream into every spec, plan, and task — without you repeating them.

**Cross-profile awareness**: Each validation command reads ALL profiles:

| Validation | Primary profile | Also reads |
|-----------|----------------|-----------|
| `/specpack.functionalvalidation` | `spec.md` | `codebase-profile.md` (test framework) |
| `/specpack.performancevalidation` | `performance-profile.md` | `customer-profile.md` (scale/concurrency) |
| `/specpack.customervalidation` | `customer-profile.md` | `performance-profile.md` (perf at customer scale) |

---

## Progressive Validation

During `/specpack.implement`, after **each task** is marked complete:

```
Task 1 ✓  →  [FUNCTIONAL: ✓ PASS]  [PERF: SKIPPED — not perf-sensitive]  [CUSTOMER: ✓ PASS]
Task 2 ✓  →  [FUNCTIONAL: ✓ PASS]  [PERF: ⚠ WARN — P90 near threshold]  [CUSTOMER: SKIPPED]
Task 3 ✓  →  [FUNCTIONAL: ✗ FAIL]  [PERF: ✓ PASS]                        [CUSTOMER: ✓ PASS]
```

Live dashboard in terminal:

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

**Key design decision**: failures do NOT halt implementation. You see them in the dashboard and address them either immediately or in the E2E phase.

### Wholesome E2E (after all tasks complete)

Once all tasks are marked `[X]` in `tasks.md`, three E2E validation commands run sequentially:

1. **`/specpack.functionalvalidation --e2e`**
   - Full test suite (`TEST_COMMAND`)
   - Spec coverage check: every requirement in `spec.md` has a test
   - Cross-feature regression check

2. **`/specpack.performancevalidation --e2e`**
   - Load test at customer-scale concurrency (from `profiles/customer-profile.md`)
   - Scenarios: normal load, peak load, spike (2× peak for 30s)
   - Compare all metrics against `profiles/performance-profile.md` targets

3. **`/specpack.customervalidation --e2e`**
   - Critical feature coverage for all user segments
   - Scale simulation: peak concurrent users × top 3 flows
   - Cross-profile: customer scale × performance baselines
   - Regression check on existing customer flows

Final consolidated output:

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

### Test framework detection

SpecPack detects your existing test framework from (in priority order):

1. `profiles/codebase-profile.md` → `Test framework:` and `Test command:` fields
2. Mentions in `constitution.md`, `spec.md`, `plan.md`, `tasks.md`
3. Config files: `jest.config.*`, `pytest.ini`, `pyproject.toml [tool.pytest]`, `vitest.config.*`, `.rspec`, etc.

It **reuses your existing framework** — it does not create a new one. Per-task validation writes granular tests; E2E runs the full suite.

---

## Supported AI Agents

SpecPack supports 30+ AI coding agents out of the box:

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

### Extensions — add commands to existing projects

```bash
specify extension list                        # list installed extensions
specify extension add git                     # add git extension (adds /specpack.git.* commands)
specify extension add <name> --from <url>     # from a custom source
specify extension remove <name>
```

### Presets — replace core command templates

```bash
specify preset list
specify preset add lean                       # minimal, token-efficient preset
specify preset add <name>
specify preset remove <name>
```

### Syncing with upstream Spec Kit

SpecPack tracks the upstream Spec Kit repo. To pull in new upstream features:

```bash
git fetch upstream
git merge upstream/main
```

Upstream remote: `https://github.com/github/spec-kit.git`

---

## Contributing

```bash
git clone https://github.com/PraveenAnandhanathan/specpack.git
cd specpack
pip install -e ".[test]"
pytest tests/
```

New commands go in `templates/commands/`.
Python CLI commands go in `src/specify_cli/`.
Brownfield-specific logic: `src/specify_cli/analyse.py`.

---

## License

MIT — see [LICENSE](./LICENSE).

Original Spec Kit by GitHub. SpecPack extensions by [PraveenAnandhanathan](https://github.com/PraveenAnandhanathan).
