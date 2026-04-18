"""
SpecPack delta/archive commands and validate-stubs command.

delta    — show ADDED/MODIFIED/REMOVED summary for current feature
archive  — move completed feature to specs/archive/ with ARCHIVE.md
validate-stubs — confirm all stub tests are RED before implementation
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from datetime import date
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

DELTA_PATTERN = re.compile(
    r"^\s*[-*]\s*\[?(ADDED|MODIFIED|REMOVED|UNCHANGED)\]?\s+(.+)$",
    re.IGNORECASE,
)
VALIDATION_STATUS_FILE = "profiles/.validation-status.md"
FEATURE_JSON = ".specify/feature.json"


# ─── helpers ──────────────────────────────────────────────────────────────────

def _read_feature_dir(project_root: Path) -> Optional[Path]:
    fj = project_root / FEATURE_JSON
    if not fj.exists():
        return None
    try:
        data = json.loads(fj.read_text(encoding="utf-8"))
        rel = data.get("feature_directory")
        if rel:
            return (project_root / rel).resolve()
    except Exception:
        pass
    return None


def _scan_delta_markers(file: Path) -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = {
        "ADDED": [], "MODIFIED": [], "REMOVED": [], "UNCHANGED": []
    }
    if not file.exists():
        return buckets
    for line in file.read_text(encoding="utf-8", errors="replace").splitlines():
        m = DELTA_PATTERN.match(line)
        if m:
            tag = m.group(1).upper()
            desc = m.group(2).strip()
            buckets[tag].append(desc)
    return buckets


def _detect_test_command(project_root: Path) -> tuple[str, str]:
    """Return (framework_name, test_command)."""
    profile = project_root / "profiles" / "codebase-profile.md"
    if profile.exists():
        text = profile.read_text(encoding="utf-8", errors="replace")
        cmd_m = re.search(r"Test command[:\s`]+([^\n`]+)", text, re.IGNORECASE)
        fw_m = re.search(r"Test framework[:\s`]+([^\n`|]+)", text, re.IGNORECASE)
        if cmd_m:
            return (fw_m.group(1).strip() if fw_m else "unknown"), cmd_m.group(1).strip()

    markers = {
        "pytest.ini": ("pytest", "pytest"),
        "pyproject.toml": ("pytest", "pytest"),
        "jest.config.js": ("Jest", "npm test"),
        "jest.config.ts": ("Jest", "npm test"),
        "vitest.config.ts": ("Vitest", "npx vitest"),
        "vitest.config.js": ("Vitest", "npx vitest"),
        ".rspec": ("RSpec", "bundle exec rspec"),
        "phpunit.xml": ("PHPUnit", "vendor/bin/phpunit"),
    }
    for fname, (fw, cmd) in markers.items():
        if (project_root / fname).exists():
            return fw, cmd
    return "unknown", "pytest"


def _read_validation_status(project_root: Path) -> dict[str, str]:
    """Parse profiles/.validation-status.md → {task_id: status_line}."""
    vf = project_root / VALIDATION_STATUS_FILE
    if not vf.exists():
        return {}
    results: dict[str, str] = {}
    for line in vf.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("|") and "|" in line[1:]:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if parts and parts[0] not in ("Task", "---", "-"):
                results[parts[0]] = line
    return results


def _all_validations_passed(project_root: Path) -> tuple[bool, dict]:
    """Check if all E2E validations passed. Returns (passed, summary_dict)."""
    vf = project_root / VALIDATION_STATUS_FILE
    if not vf.exists():
        return False, {"error": "profiles/.validation-status.md not found"}

    text = vf.read_text(encoding="utf-8", errors="replace")
    summary = {
        "functional": "UNKNOWN",
        "performance": "UNKNOWN",
        "customer": "UNKNOWN",
    }
    for line in text.splitlines():
        ll = line.lower()
        if "e2e" in ll or "wholesome" in ll or "overall" in ll:
            if "functional" in ll:
                summary["functional"] = "PASS" if "pass" in ll else "FAIL"
            if "performance" in ll or "perf" in ll:
                summary["performance"] = "PASS" if "pass" in ll else ("WARN" if "warn" in ll else "FAIL")
            if "customer" in ll:
                summary["customer"] = "PASS" if "pass" in ll else "FAIL"

    all_pass = all(v in ("PASS", "WARN") for v in summary.values())
    return all_pass, summary


# ─── validate-stubs ───────────────────────────────────────────────────────────

def run_validate_stubs():
    """Confirm all stub tests are RED (failing) before implementation starts."""
    project_root = Path.cwd()
    feature_dir = _read_feature_dir(project_root)

    stub_dirs: list[Path] = []
    if feature_dir and (feature_dir / "tests" / "stubs").exists():
        stub_dirs.append(feature_dir / "tests" / "stubs")

    # Also scan all specs/*/tests/stubs/
    specs_root = project_root / "specs"
    if specs_root.exists():
        for d in specs_root.iterdir():
            if d.is_dir() and (d / "tests" / "stubs").is_dir():
                stub_dirs.append(d / "tests" / "stubs")

    stub_dirs = list({str(d): d for d in stub_dirs}.values())  # deduplicate

    if not stub_dirs:
        console.print(Panel(
            "No stub test directories found.\n\n"
            "Stubs are generated by [bold]/specpack.tasks[/bold] and live in:\n"
            "[cyan]specs/<feature>/tests/stubs/[/cyan]",
            title="validate-stubs",
            border_style="yellow",
        ))
        raise typer.Exit(0)

    fw, test_cmd = _detect_test_command(project_root)
    console.print(f"[cyan]Test framework:[/cyan] {fw}  [cyan]Command:[/cyan] {test_cmd}")
    console.print()

    table = Table(title="Stub Test Status", border_style="cyan")
    table.add_column("Stub File", style="white")
    table.add_column("Status", justify="center")
    table.add_column("Note")

    red_count = 0
    green_count = 0
    error_count = 0

    for stub_dir in stub_dirs:
        stubs = sorted(stub_dir.rglob("*"))
        stubs = [f for f in stubs if f.is_file() and not f.name.startswith(".")]

        for stub in stubs:
            rel = str(stub.relative_to(project_root))
            display_name = stub.name  # show filename so it's never truncated
            try:
                result = subprocess.run(
                    [*test_cmd.split(), str(stub)],
                    capture_output=True, text=True,
                    cwd=str(project_root), timeout=30
                )
                if result.returncode != 0:
                    table.add_row(display_name, "[red]🔴 RED[/red]", "Correct — test is failing as expected")
                    red_count += 1
                else:
                    table.add_row(display_name, "[green]🟢 GREEN[/green]", "[yellow]WARNING: already passing — test may be wrong or feature already exists[/yellow]")
                    green_count += 1
            except subprocess.TimeoutExpired:
                table.add_row(display_name, "[yellow]TIMEOUT[/yellow]", "Test took too long")
                error_count += 1
            except Exception as e:
                table.add_row(display_name, "[yellow]ERROR[/yellow]", str(e)[:60])
                error_count += 1

    console.print(table)
    console.print()

    if green_count > 0:
        console.print(f"[yellow]⚠  {green_count} stub(s) are already GREEN — review before implementing.[/yellow]")
    if red_count > 0:
        console.print(f"[green]✓  {red_count} stub(s) are RED — ready for implementation.[/green]")

    if green_count == 0 and red_count > 0:
        console.print(Panel(
            f"[bold green]All {red_count} stubs confirmed RED.[/bold green]\n\n"
            "Run [bold cyan]/specpack.implement[/bold cyan] to begin Red→Green cycle.",
            border_style="green",
        ))
    elif green_count > 0:
        console.print(Panel(
            f"[yellow]{green_count} stub(s) need review before starting.[/yellow]\n"
            "Investigate why they pass before implementing.",
            border_style="yellow",
        ))


# ─── delta ────────────────────────────────────────────────────────────────────

def run_delta(feature_path: Optional[str] = None):
    """Show ADDED/MODIFIED/REMOVED delta summary for the current feature."""
    project_root = Path.cwd()

    if feature_path:
        feature_dir = (project_root / feature_path).resolve()
    else:
        feature_dir = _read_feature_dir(project_root)

    if not feature_dir or not feature_dir.exists():
        console.print("[red]Error:[/red] No active feature found. Run /specpack.specify first or pass --feature <path>.")
        raise typer.Exit(1)

    scan_files = ["spec.md", "plan.md", "tasks.md"]
    total: dict[str, list[tuple[str, str]]] = {
        "ADDED": [], "MODIFIED": [], "REMOVED": [], "UNCHANGED": []
    }

    for fname in scan_files:
        f = feature_dir / fname
        if not f.exists():
            continue
        buckets = _scan_delta_markers(f)
        for tag, items in buckets.items():
            for item in items:
                total[tag].append((fname, item))

    grand_total = sum(len(v) for v in total.values())

    if grand_total == 0:
        console.print(Panel(
            "No delta markers found in spec.md / plan.md / tasks.md.\n\n"
            "Delta markers are added by [bold]/specpack.specify[/bold] for brownfield changes.\n"
            "Format: [ADDED] / [MODIFIED] / [REMOVED] / [UNCHANGED]",
            title=f"Delta — {feature_dir.name}",
            border_style="yellow",
        ))
        return

    console.print(f"\n[bold]Delta Summary — [cyan]{feature_dir.name}[/cyan][/bold]\n")

    colors = {"ADDED": "green", "MODIFIED": "yellow", "REMOVED": "red", "UNCHANGED": "white"}
    icons = {"ADDED": "+", "MODIFIED": "~", "REMOVED": "-", "UNCHANGED": "="}

    for tag in ["ADDED", "MODIFIED", "REMOVED", "UNCHANGED"]:
        items = total[tag]
        if not items:
            continue
        color = colors[tag]
        icon = icons[tag]
        console.print(f"[{color}]{icon} {tag} ({len(items)})[/{color}]")
        for fname, desc in items:
            console.print(f"  [{color}]{icon}[/{color}]  {desc}  [dim]({fname})[/dim]")
        console.print()

    table = Table(border_style="dim")
    table.add_column("Type")
    table.add_column("Count", justify="right")
    for tag, color in colors.items():
        count = len(total[tag])
        if count:
            table.add_row(f"[{color}]{tag}[/{color}]", str(count))
    console.print(table)


# ─── archive ──────────────────────────────────────────────────────────────────

def run_archive(feature_path: Optional[str] = None, force: bool = False):
    """Archive completed feature to specs/archive/ with ARCHIVE.md."""
    project_root = Path.cwd()

    if feature_path:
        feature_dir = (project_root / feature_path).resolve()
    else:
        feature_dir = _read_feature_dir(project_root)

    if not feature_dir or not feature_dir.exists():
        console.print("[red]Error:[/red] No active feature found. Pass --feature <path> or ensure .specify/feature.json exists.")
        raise typer.Exit(1)

    # Validation check
    if not force:
        passed, summary = _all_validations_passed(project_root)
        if not passed:
            console.print(Panel(
                f"[red]Validation not fully passed — cannot archive.[/red]\n\n"
                f"Functional:   {summary.get('functional', 'UNKNOWN')}\n"
                f"Performance:  {summary.get('performance', 'UNKNOWN')}\n"
                f"Customer:     {summary.get('customer', 'UNKNOWN')}\n\n"
                "Run [bold]/specpack.implement --e2e[/bold] first, or use [bold]--force[/bold] to override.",
                title="Archive Blocked",
                border_style="red",
            ))
            raise typer.Exit(1)
    else:
        passed, summary = True, {"functional": "SKIPPED", "performance": "SKIPPED", "customer": "SKIPPED"}
        _, summary = _all_validations_passed(project_root)

    # Delta summary
    scan_files = ["spec.md", "plan.md", "tasks.md"]
    delta_totals: dict[str, list[str]] = {"ADDED": [], "MODIFIED": [], "REMOVED": [], "UNCHANGED": []}
    for fname in scan_files:
        f = feature_dir / fname
        if f.exists():
            buckets = _scan_delta_markers(f)
            for tag, items in buckets.items():
                delta_totals[tag].extend(items)

    # Task count
    tasks_file = feature_dir / "tasks.md"
    total_tasks = 0
    completed_tasks = 0
    if tasks_file.exists():
        for line in tasks_file.read_text(encoding="utf-8", errors="replace").splitlines():
            if re.match(r"\s*-\s*\[[ xX]\]", line):
                total_tasks += 1
            if re.match(r"\s*-\s*\[[xX]\]", line):
                completed_tasks += 1

    # Build ARCHIVE.md
    today = date.today().isoformat()
    overall = "✓ ALL VALIDATIONS PASSED" if passed else "⚠ ARCHIVED WITH WARNINGS"

    archive_lines = [
        f"# Archive: {feature_dir.name}",
        "",
        f"Archived: {today}",
        f"Status: {overall}",
        "",
        "## Delta Summary",
        "",
        f"- ADDED:     {len(delta_totals['ADDED'])} items",
        f"- MODIFIED:  {len(delta_totals['MODIFIED'])} items",
        f"- REMOVED:   {len(delta_totals['REMOVED'])} items",
        f"- UNCHANGED: {len(delta_totals['UNCHANGED'])} items",
        "",
    ]

    for tag in ["ADDED", "MODIFIED", "REMOVED"]:
        if delta_totals[tag]:
            archive_lines.append(f"### {tag}")
            for item in delta_totals[tag]:
                archive_lines.append(f"- {item}")
            archive_lines.append("")

    archive_lines += [
        "## Validation Results",
        "",
        "| Type | E2E Status |",
        "|------|-----------|",
        f"| Functional   | {summary.get('functional', 'UNKNOWN')} |",
        f"| Performance  | {summary.get('performance', 'UNKNOWN')} |",
        f"| Customer     | {summary.get('customer', 'UNKNOWN')} |",
        "",
        "## Tasks",
        "",
        f"- Total: {total_tasks}",
        f"- Completed: {completed_tasks}",
        "",
        "---",
        f"*Archived by SpecPack on {today}.*",
    ]

    (feature_dir / "ARCHIVE.md").write_text("\n".join(archive_lines), encoding="utf-8")

    # Move to archive
    archive_root = project_root / "specs" / "archive"
    archive_root.mkdir(parents=True, exist_ok=True)
    dest = archive_root / feature_dir.name

    if dest.exists():
        console.print(f"[yellow]Warning:[/yellow] {dest} already exists — overwriting.")
        shutil.rmtree(dest)

    shutil.move(str(feature_dir), str(dest))

    # Clear feature.json
    fj = project_root / FEATURE_JSON
    if fj.exists():
        fj.write_text("{}", encoding="utf-8")

    console.print(Panel(
        f"[bold green]Archived:[/bold green] [cyan]{feature_dir.name}[/cyan]\n\n"
        f"Location: [white]specs/archive/{feature_dir.name}/[/white]\n"
        f"ARCHIVE.md written with delta summary and validation results.\n\n"
        f"[dim]Delta: +{len(delta_totals['ADDED'])} ~{len(delta_totals['MODIFIED'])} "
        f"-{len(delta_totals['REMOVED'])}[/dim]",
        title="Feature Archived",
        border_style="green",
    ))
