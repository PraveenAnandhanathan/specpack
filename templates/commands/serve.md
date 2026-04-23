---
description: Start the SpecPack local web UI — renders specs, archive, and profiles as a read-only website for sharing with non-devs.
---

## User Input

```text
$ARGUMENTS
```

Supported arguments:
- `--port <N>` — port to listen on (default: 4242)
- `--host <addr>` — host to bind (default: 127.0.0.1, use 0.0.0.0 for LAN access)
- `--no-browser` — do not auto-open browser

## Outline

You are starting the SpecPack local web UI.

### Step 1 — Check dependencies

Run:

```
specify serve --no-browser --help
```

If the output contains "serve requires optional dependencies", the `[serve]` extra is not installed. Tell the user:

```
[INSTALL REQUIRED] specify serve needs optional dependencies:

  pip install 'specpack-cli[serve]'
  # or
  uv tool install 'specpack-cli[serve]'

Install this, then run /specpack.serve again.
```

Stop here.

### Step 2 — Build and run the command

Build the command from user arguments:

- No arguments: `specify serve`
- With port: `specify serve --port <N>`
- With host: `specify serve --host <addr>`
- With `--no-browser`: `specify serve --no-browser`

Run the command from the project root. The server runs continuously — output the startup message to the user.

### Step 3 — Report

Once the server is running, tell the user:

```
[SERVING] SpecPack web UI is live at http://127.0.0.1:4242

Pages available:
  /            — Dashboard (active features, delta badges, task progress)
  /feature/*   — Spec / Plan / Tasks / Delta tabs per feature
  /archive     — Archived features with validation badges
  /profiles    — Codebase, performance, customer profiles

Share this URL with PMs, designers, or QA who don't use the CLI.
Press Ctrl+C in the terminal to stop the server.
```

Adjust the URL if a custom `--port` or `--host` was provided.
