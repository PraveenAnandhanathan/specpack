---
description: Execute the implementation plan by processing and executing all tasks defined in tasks.md
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Pre-Execution Checks

**Check for extension hooks (before implementation)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_implement` key
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- For each executable hook, output the following based on its `optional` flag:
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Pre-Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```
  - **Mandatory hook** (`optional: false`):
    ```
    ## Extension Hooks

    **Automatic Pre-Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}
    
    Wait for the result of the hook command before proceeding to the Outline.
    ```
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently

## Outline

1. Run `{SCRIPT}` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Check checklists status** (if FEATURE_DIR/checklists/ exists):
   - Scan all checklist files in the checklists/ directory
   - For each checklist, count:
     - Total items: All lines matching `- [ ]` or `- [X]` or `- [x]`
     - Completed items: Lines matching `- [X]` or `- [x]`
     - Incomplete items: Lines matching `- [ ]`
   - Create a status table:

     ```text
     | Checklist | Total | Completed | Incomplete | Status |
     |-----------|-------|-----------|------------|--------|
     | ux.md     | 12    | 12        | 0          | ✓ PASS |
     | test.md   | 8     | 5         | 3          | ✗ FAIL |
     | security.md | 6   | 6         | 0          | ✓ PASS |
     ```

   - Calculate overall status:
     - **PASS**: All checklists have 0 incomplete items
     - **FAIL**: One or more checklists have incomplete items

   - **If any checklist is incomplete**:
     - Display the table with incomplete item counts
     - **STOP** and ask: "Some checklists are incomplete. Do you want to proceed with implementation anyway? (yes/no)"
     - Wait for user response before continuing
     - If user says "no" or "wait" or "stop", halt execution
     - If user says "yes" or "proceed" or "continue", proceed to step 3

   - **If all checklists are complete**:
     - Display the table showing all checklists passed
     - Automatically proceed to step 3

3. **Load brownfield profiles and initialise validation status**:

   Check for validation profiles (optional — skip silently if absent):
   - `profiles/codebase-profile.md` → extract `TEST_FRAMEWORK`, `TEST_COMMAND`
   - `profiles/performance-profile.md` → extract performance targets
   - `profiles/customer-profile.md` → extract `PEAK_CONCURRENT`, `CRITICAL_FEATURES`

   Initialise `profiles/.validation-status.md` (create/overwrite):
   ```markdown
   # Validation Status

   | Task | Functional | Performance | Customer | Updated |
   |------|-----------|------------|---------|---------|
   ```

   Display the **live validation dashboard** (update after each task):
   ```
   ┌──────────────────────────────────────────┐
   │ SpecPack Validation Dashboard            │
   ├──────────────────────────────────────────┤
   │ Tasks: 0/N complete                      │
   │                                          │
   │ Functional   [ ] pending                 │
   │ Performance  [ ] pending                 │
   │ Customer     [ ] pending                 │
   └──────────────────────────────────────────┘
   ```

3b. Load and analyze the implementation context:
   - **REQUIRED**: Read tasks.md for the complete task list and execution plan
   - **REQUIRED**: Read plan.md for tech stack, architecture, and file structure
   - **IF EXISTS**: Read data-model.md for entities and relationships
   - **IF EXISTS**: Read contracts/ for API specifications and test requirements
   - **IF EXISTS**: Read research.md for technical decisions and constraints
   - **IF EXISTS**: Read quickstart.md for integration scenarios

4. **Project Setup Verification**:
   - **REQUIRED**: Create/verify ignore files based on actual project setup:

   **Detection & Creation Logic**:
   - Check if the following command succeeds to determine if the repository is a git repo (create/verify .gitignore if so):

     ```sh
     git rev-parse --git-dir 2>/dev/null
     ```

   - Check if Dockerfile* exists or Docker in plan.md → create/verify .dockerignore
   - Check if .eslintrc* exists → create/verify .eslintignore
   - Check if eslint.config.* exists → ensure the config's `ignores` entries cover required patterns
   - Check if .prettierrc* exists → create/verify .prettierignore
   - Check if .npmrc or package.json exists → create/verify .npmignore (if publishing)
   - Check if terraform files (*.tf) exist → create/verify .terraformignore
   - Check if .helmignore needed (helm charts present) → create/verify .helmignore

   **If ignore file already exists**: Verify it contains essential patterns, append missing critical patterns only
   **If ignore file missing**: Create with full pattern set for detected technology

   **Common Patterns by Technology** (from plan.md tech stack):
   - **Node.js/JavaScript/TypeScript**: `node_modules/`, `dist/`, `build/`, `*.log`, `.env*`
   - **Python**: `__pycache__/`, `*.pyc`, `.venv/`, `venv/`, `dist/`, `*.egg-info/`
   - **Java**: `target/`, `*.class`, `*.jar`, `.gradle/`, `build/`
   - **C#/.NET**: `bin/`, `obj/`, `*.user`, `*.suo`, `packages/`
   - **Go**: `*.exe`, `*.test`, `vendor/`, `*.out`
   - **Ruby**: `.bundle/`, `log/`, `tmp/`, `*.gem`, `vendor/bundle/`
   - **PHP**: `vendor/`, `*.log`, `*.cache`, `*.env`
   - **Rust**: `target/`, `debug/`, `release/`, `*.rs.bk`, `*.rlib`, `*.prof*`, `.idea/`, `*.log`, `.env*`
   - **Kotlin**: `build/`, `out/`, `.gradle/`, `.idea/`, `*.class`, `*.jar`, `*.iml`, `*.log`, `.env*`
   - **C++**: `build/`, `bin/`, `obj/`, `out/`, `*.o`, `*.so`, `*.a`, `*.exe`, `*.dll`, `.idea/`, `*.log`, `.env*`
   - **C**: `build/`, `bin/`, `obj/`, `out/`, `*.o`, `*.a`, `*.so`, `*.exe`, `*.dll`, `autom4te.cache/`, `config.status`, `config.log`, `.idea/`, `*.log`, `.env*`
   - **Swift**: `.build/`, `DerivedData/`, `*.swiftpm/`, `Packages/`
   - **R**: `.Rproj.user/`, `.Rhistory`, `.RData`, `.Ruserdata`, `*.Rproj`, `packrat/`, `renv/`
   - **Universal**: `.DS_Store`, `Thumbs.db`, `*.tmp`, `*.swp`, `.vscode/`, `.idea/`

   **Tool-Specific Patterns**:
   - **Docker**: `node_modules/`, `.git/`, `Dockerfile*`, `.dockerignore`, `*.log*`, `.env*`, `coverage/`
   - **ESLint**: `node_modules/`, `dist/`, `build/`, `coverage/`, `*.min.js`
   - **Prettier**: `node_modules/`, `dist/`, `build/`, `coverage/`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`
   - **Terraform**: `.terraform/`, `*.tfstate*`, `*.tfvars`, `.terraform.lock.hcl`
   - **Kubernetes/k8s**: `*.secret.yaml`, `secrets/`, `.kube/`, `kubeconfig*`, `*.key`, `*.crt`

5. Parse tasks.md structure and extract:
   - **Task phases**: Setup, Tests, Core, Integration, Polish
   - **Task dependencies**: Sequential vs parallel execution rules
   - **Task details**: ID, description, file paths, parallel markers [P]
   - **Execution flow**: Order and dependency requirements

5b. **Red→Green pre-flight check**:

   Before executing any task, run `specify validate-stubs` to confirm all stubs are RED.
   - If stubs directory does not exist: skip silently (stubs are optional).
   - If any stub is already GREEN: warn the user and ask if they want to proceed.
   - If all stubs are RED: output `[RED CONFIRMED] All stubs failing — Red→Green cycle ready.` and proceed.

6. Execute implementation following the task plan:
   - **Phase-by-phase execution**: Complete each phase before moving to the next
   - **Respect dependencies**: Run sequential tasks in order, parallel tasks [P] can run together  
   - **Follow TDD approach**: Execute test tasks before their corresponding implementation tasks
   - **File-based coordination**: Tasks affecting the same files must run sequentially
   - **Validation checkpoints**: Verify each phase completion before proceeding

7. Implementation execution rules:
   - **Setup first**: Initialize project structure, dependencies, configuration
   - **Tests before code**: If you need to write tests for contracts, entities, and integration scenarios
   - **Core development**: Implement models, services, CLI commands, endpoints
   - **Integration work**: Database connections, middleware, logging, external services
   - **Polish and validation**: Unit tests, performance optimization, documentation

8. Progress tracking and error handling:
   - Report progress after each completed task
   - Halt execution if any non-parallel task fails
   - For parallel tasks [P], continue with successful tasks, report failed ones
   - Provide clear error messages with context for debugging
   - Suggest next steps if implementation cannot proceed
   - **IMPORTANT** For completed tasks, make sure to mark the task off as [X] in the tasks file.

   **Red→Green per task**: Before writing code for each task, confirm its stub test is RED. After completing the task, the stub must turn GREEN.

   **After marking each task [X]** — trigger progressive validation immediately:

   a. Run `/specpack.functionalvalidation --task <TASK_ID>`:
      - Validates the just-completed task against its requirement in `spec.md`.
      - Uses existing test framework from `profiles/codebase-profile.md` if available.
      - Writes a targeted test if none exists for this task's scope.

   b. Run `/specpack.performancevalidation --task <TASK_ID>`:
      - Only runs if task touches a performance-sensitive path.
      - Skips with `[PERF: SKIPPED]` if task is not perf-sensitive.

   c. Run `/specpack.customervalidation --task <TASK_ID>`:
      - Only runs if task affects a customer flow from `profiles/customer-profile.md`.
      - Skips with `[CUSTOMER: SKIPPED]` if no customer flow is impacted.

   **Update the Red→Green dashboard** after each task:
   ```
   ┌──────────────────────────────────────────────────────┐
   │ SpecPack — Red→Green Dashboard                       │
   ├──────────────────────────────────────────────────────┤
   │ Tasks: [DONE]/[TOTAL] complete                       │
   │                                                      │
   │ T001  🔴→🟢  [TASK_NAME]                            │
   │ T002  🔴→🟢  [TASK_NAME]                            │
   │ T003  🔴→⏳  [TASK_NAME]  ← in progress             │
   │ T004  ⬜      [TASK_NAME]  ← pending                 │
   ├──────────────────────────────────────────────────────┤
   │ Functional   [✓ X passed / ✗ Y failed / - skip]     │
   │ Performance  [✓ X passed / ⚠ Y warn  / - skip]      │
   │ Customer     [✓ X passed / ✗ Y failed / - skip]     │
   └──────────────────────────────────────────────────────┘
   ```

   **If a validation FAILS**:
   - Do NOT halt implementation automatically.
   - Display the failure prominently above the dashboard.
   - Continue to the next task.
   - Failures are addressed in the E2E phase or by user decision.

   **If a validation WARNS** (performance only):
   - Log the warning in the dashboard.
   - Continue implementation.

9. Completion validation — Wholesome E2E (all tasks marked [X]):

   Run the full E2E validation suite in sequence:

   a. **`/specpack.functionalvalidation --e2e`**
      - Full test suite run.
      - Spec coverage check (every requirement in `spec.md` has a test).
      - Cross-feature regression check.

   b. **`/specpack.performancevalidation --e2e`**
      - Full load test at customer-scale (`PEAK_CONCURRENT` from customer profile).
      - Test: normal load, peak load, spike (2x peak × 30s).
      - Compare all metrics against `profiles/performance-profile.md → Performance Validation Targets`.

   c. **`/specpack.customervalidation --e2e`**
      - Critical feature coverage for all segments.
      - Scale simulation: `PEAK_CONCURRENT` users running top 3 flows concurrently.
      - Cross-reference: customer scale × performance baselines.
      - Regression check on existing customer flows.

   All three run **sequentially** (E2E results from one inform the next).

   **Final consolidated status**:
   ```
   ╔══════════════════════════════════════════════════════╗
   ║  SpecPack Implementation Complete                    ║
   ╠══════════════════════════════════════════════════════╣
   ║  Functional   ✓ PASS / ✗ FAIL                       ║
   ║  Performance  ✓ PASS / ⚠ WARN / ✗ FAIL             ║
   ║  Customer     ✓ PASS / ✗ FAIL                       ║
   ╠══════════════════════════════════════════════════════╣
   ║  Overall:  READY FOR REVIEW / NEEDS FIXES           ║
   ╚══════════════════════════════════════════════════════╝
   ```

   If any FAIL: output a prioritised fix list. User decides next steps.

10. **Auto-archive prompt**:

    After all E2E validations pass, ask the user:
    ```
    All validations passed. Archive this feature? (yes/no)
    ```
    - If yes: run `specify archive` — moves `specs/<feature>/` to `specs/archive/<feature>/` with ARCHIVE.md.
    - If no: remind user they can archive later with `specify archive`.

Note: This command assumes a complete task breakdown exists in tasks.md. If tasks are incomplete or missing, suggest running `/specpack.tasks` first to regenerate the task list.

10. **Check for extension hooks**: After completion validation, check if `.specify/extensions.yml` exists in the project root.
    - If it exists, read it and look for entries under the `hooks.after_implement` key
    - If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
    - Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
    - For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
      - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
      - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
    - For each executable hook, output the following based on its `optional` flag:
      - **Optional hook** (`optional: true`):
        ```
        ## Extension Hooks

        **Optional Hook**: {extension}
        Command: `/{command}`
        Description: {description}

        Prompt: {prompt}
        To execute: `/{command}`
        ```
      - **Mandatory hook** (`optional: false`):
        ```
        ## Extension Hooks

        **Automatic Hook**: {extension}
        Executing: `/{command}`
        EXECUTE_COMMAND: {command}
        ```
    - If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently
