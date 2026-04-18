"""
SpecPack analyse commands — brownfield context profiling.

Static modes run entirely in Python (no AI tokens).
AI modes write a trigger context file; the slash command drives the agent.
"""

from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path
from typing import Optional

import typer
import yaml
from rich.console import Console
from rich.panel import Panel

console = Console()

analyse_app = typer.Typer(
    name="analyse",
    help="Analyse existing codebases and reports to build brownfield profiles",
    add_completion=False,
)

PROFILES_DIR = "profiles"

LANG_MAP: dict[str, str] = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
    ".jsx": "JavaScript/React", ".tsx": "TypeScript/React",
    ".java": "Java", ".kt": "Kotlin", ".scala": "Scala",
    ".cs": "C#", ".vb": "VB.NET", ".fs": "F#",
    ".go": "Go", ".rs": "Rust", ".cpp": "C++", ".c": "C",
    ".rb": "Ruby", ".php": "PHP", ".swift": "Swift",
    ".r": "R", ".m": "MATLAB/Objective-C",
    ".html": "HTML", ".css": "CSS", ".scss": "SCSS", ".sass": "SASS",
    ".sql": "SQL", ".sh": "Shell", ".bash": "Bash", ".zsh": "Zsh",
    ".ps1": "PowerShell", ".yaml": "YAML", ".yml": "YAML",
    ".json": "JSON", ".toml": "TOML", ".xml": "XML", ".md": "Markdown",
    ".dart": "Dart", ".lua": "Lua", ".ex": "Elixir", ".exs": "Elixir",
    ".clj": "Clojure", ".hs": "Haskell", ".erl": "Erlang",
}

FRAMEWORK_SIGNALS: list[tuple[str, str]] = [
    ("package.json", "Node.js"),
    ("requirements.txt", "Python/pip"),
    ("pyproject.toml", "Python/pyproject"),
    ("Pipfile", "Python/pipenv"),
    ("pom.xml", "Java/Maven"),
    ("build.gradle", "Java/Gradle"),
    ("Cargo.toml", "Rust/Cargo"),
    ("go.mod", "Go modules"),
    ("Gemfile", "Ruby/Bundler"),
    ("composer.json", "PHP/Composer"),
    ("pubspec.yaml", "Dart/Flutter"),
    ("mix.exs", "Elixir/Mix"),
    ("*.csproj", "C#/.NET"),
    ("Dockerfile", "Docker"),
    ("docker-compose.yml", "Docker Compose"),
    ("docker-compose.yaml", "Docker Compose"),
    ("terraform.tf", "Terraform"),
    (".github/workflows", "GitHub Actions CI"),
    ("Makefile", "Make"),
    ("justfile", "Just"),
]

SKIP_DIRS = {
    ".git", ".svn", "node_modules", "__pycache__", ".venv", "venv",
    "env", ".env", "dist", "build", "target", ".idea", ".vscode",
    ".specify", "profiles", ".next", ".nuxt", "coverage", ".tox",
    "site-packages", ".mypy_cache", ".pytest_cache", ".ruff_cache",
}


# ─── helpers ──────────────────────────────────────────────────────────────────

def _ensure_profiles_dir(project_root: Path) -> Path:
    profiles = project_root / PROFILES_DIR
    profiles.mkdir(parents=True, exist_ok=True)
    return profiles


def _resolve_project_root(here: bool, repopath: Optional[Path]) -> Path:
    if here:
        return Path.cwd()
    if repopath:
        p = Path(repopath).expanduser().resolve()
        if not p.is_dir():
            console.print(f"[red]Error:[/red] Path does not exist: {p}")
            raise typer.Exit(1)
        return p
    return Path.cwd()


def _tree_snapshot(root: Path, max_depth: int = 4) -> list[str]:
    lines: list[str] = []

    def _walk(path: Path, prefix: str, depth: int) -> None:
        if depth > max_depth:
            return
        try:
            children = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        except PermissionError:
            return
        dirs = [c for c in children if c.is_dir() and c.name not in SKIP_DIRS]
        files = [c for c in children if c.is_file()]
        for i, d in enumerate(dirs):
            connector = "└── " if (i == len(dirs) - 1 and not files) else "├── "
            lines.append(f"{prefix}{connector}{d.name}/")
            ext = "    " if connector.startswith("└") else "│   "
            _walk(d, prefix + ext, depth + 1)
        for i, f in enumerate(files):
            connector = "└── " if i == len(files) - 1 else "├── "
            lines.append(f"{prefix}{connector}{f.name}")

    lines.append(f"{root.name}/")
    _walk(root, "", 1)
    return lines


def _detect_extensions(root: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            ext = Path(fname).suffix.lower()
            if ext:
                counts[ext] = counts.get(ext, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: -x[1]))


def _detect_languages(ext_counts: dict[str, int]) -> list[tuple[str, int]]:
    lang_counts: dict[str, int] = {}
    for ext, count in ext_counts.items():
        lang = LANG_MAP.get(ext)
        if lang:
            lang_counts[lang] = lang_counts.get(lang, 0) + count
    return sorted(lang_counts.items(), key=lambda x: -x[1])


def _detect_frameworks(root: Path) -> list[str]:
    found: list[str] = []
    for signal, label in FRAMEWORK_SIGNALS:
        if "*" in signal:
            pattern = signal.replace("*", "")
            if any(f.suffix == pattern for f in root.rglob("*") if f.is_file()):
                found.append(label)
        elif (root / signal).exists():
            found.append(label)
    return found


def _detect_test_framework(root: Path) -> list[str]:
    found: list[str] = []
    markers = {
        "pytest.ini": "pytest", "pytest": "pytest",
        "jest.config.js": "Jest", "jest.config.ts": "Jest",
        "vitest.config.ts": "Vitest", "vitest.config.js": "Vitest",
        "karma.conf.js": "Karma",
        "build.gradle": "JUnit (Gradle)",
        "pom.xml": "JUnit (Maven)",
        ".rspec": "RSpec",
        "phpunit.xml": "PHPUnit",
    }
    for fname, label in markers.items():
        if (root / fname).exists() and label not in found:
            found.append(label)
    if not found:
        pkg = root / "package.json"
        if pkg.exists():
            try:
                data = json.loads(pkg.read_text(encoding="utf-8"))
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                for key in deps:
                    if "jest" in key:
                        found.append("Jest")
                        break
                    if "vitest" in key:
                        found.append("Vitest")
                        break
                    if "mocha" in key:
                        found.append("Mocha")
                        break
            except Exception:
                pass
    return found


def _detect_styling(root: Path, ext_counts: dict[str, int]) -> list[str]:
    styles: list[str] = []
    if ".py" in ext_counts:
        for cfg in [".flake8", "setup.cfg", "pyproject.toml", ".pylintrc"]:
            if (root / cfg).exists():
                styles.append(f"Python linting config: {cfg}")
                break
    for cfg in [".eslintrc", ".eslintrc.js", ".eslintrc.json", ".eslintrc.yaml",
                "eslint.config.js", "eslint.config.ts"]:
        if (root / cfg).exists():
            styles.append("ESLint")
            break
    for cfg in [".prettierrc", ".prettierrc.js", ".prettierrc.json"]:
        if (root / cfg).exists():
            styles.append("Prettier")
            break
    if (root / ".editorconfig").exists():
        styles.append("EditorConfig")
    return styles


def _load_report_file(path: Path) -> list[dict]:
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")
    if suffix == ".json":
        data = json.loads(text)
        return data if isinstance(data, list) else [data]
    if suffix in (".yaml", ".yml"):
        data = yaml.safe_load(text)
        return data if isinstance(data, list) else [data]
    if suffix == ".csv":
        reader = csv.DictReader(text.splitlines())
        return list(reader)
    console.print(f"[red]Error:[/red] Unsupported file type '{suffix}'. Use .csv, .json, or .yaml")
    raise typer.Exit(1)


def _numeric_stats(values: list[float]) -> dict[str, float]:
    if not values:
        return {}
    values = sorted(values)
    n = len(values)
    return {
        "min": values[0],
        "max": values[-1],
        "mean": sum(values) / n,
        "p50": values[int(n * 0.50)],
        "p90": values[int(n * 0.90)],
        "p95": values[int(n * 0.95)],
        "p99": values[int(n * 0.99)],
    }


def _extract_numeric_columns(rows: list[dict]) -> dict[str, dict[str, float]]:
    if not rows:
        return {}
    columns: dict[str, list[float]] = {}
    for row in rows:
        for k, v in row.items():
            try:
                columns.setdefault(k, []).append(float(str(v).replace(",", "")))
            except (ValueError, TypeError):
                pass
    return {col: _numeric_stats(vals) for col, vals in columns.items() if vals}


# ─── codebase ─────────────────────────────────────────────────────────────────

@analyse_app.command("codebase")
def analyse_codebase(
    here: bool = typer.Option(False, "--here", help="Analyse current working directory"),
    repopath: Optional[Path] = typer.Option(None, "--repopath", help="Path to local repo"),
    repourl: Optional[str] = typer.Option(None, "--repourl", help="Public GitHub URL to clone and analyse"),
    static: bool = typer.Option(False, "--static", help="Static analysis only — no AI tokens used"),
) -> None:
    """Analyse an existing codebase and write profiles/codebase-profile.md."""
    import tempfile, shutil

    # Resolve source
    clone_tmp: Optional[Path] = None
    if repourl:
        console.print(f"[cyan]Cloning[/cyan] {repourl} …")
        clone_tmp = Path(tempfile.mkdtemp())
        result = __import__("subprocess").run(
            ["git", "clone", "--depth=1", repourl, str(clone_tmp / "repo")],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            console.print(f"[red]Clone failed:[/red] {result.stderr.strip()}")
            raise typer.Exit(1)
        source = clone_tmp / "repo"
    else:
        source = _resolve_project_root(here, repopath)

    try:
        project_root = Path.cwd()
        profiles_dir = _ensure_profiles_dir(project_root)

        if static:
            _static_codebase_analysis(source, profiles_dir)
        else:
            _ai_codebase_trigger(source, profiles_dir)
    finally:
        if clone_tmp and clone_tmp.exists():
            shutil.rmtree(clone_tmp, ignore_errors=True)


def _static_codebase_analysis(source: Path, profiles_dir: Path) -> None:
    console.print(f"[cyan]Static analysis:[/cyan] {source}")

    ext_counts = _detect_extensions(source)
    languages = _detect_languages(ext_counts)
    frameworks = _detect_frameworks(source)
    test_frameworks = _detect_test_framework(source)
    styling = _detect_styling(source, ext_counts)
    tree = _tree_snapshot(source)

    total_files = sum(ext_counts.values())
    top_exts = list(ext_counts.items())[:15]

    lines: list[str] = [
        "# Codebase Profile",
        "",
        "> Generated by: `specify analyse-codebase --static`",
        f"> Source: `{source}`",
        "",
        "## Summary",
        "",
        f"- **Total files analysed**: {total_files}",
        f"- **Primary languages**: {', '.join(l for l, _ in languages[:5]) or 'Unknown'}",
        f"- **Frameworks / tooling**: {', '.join(frameworks) or 'None detected'}",
        f"- **Test frameworks**: {', '.join(test_frameworks) or 'None detected'}",
        "",
        "## Languages",
        "",
        "| Language | File Count |",
        "|----------|-----------|",
    ]
    for lang, count in languages:
        lines.append(f"| {lang} | {count} |")

    lines += [
        "",
        "## File Extensions",
        "",
        "| Extension | Count |",
        "|-----------|-------|",
    ]
    for ext, count in top_exts:
        lines.append(f"| `{ext}` | {count} |")

    if frameworks:
        lines += ["", "## Detected Frameworks & Tooling", ""]
        for f in frameworks:
            lines.append(f"- {f}")

    if test_frameworks:
        lines += ["", "## Test Frameworks", ""]
        for t in test_frameworks:
            lines.append(f"- {t}")

    if styling:
        lines += ["", "## Code Style & Linting", ""]
        for s in styling:
            lines.append(f"- {s}")

    lines += [
        "",
        "## Project Structure",
        "",
        "```",
        *tree[:80],
        "```",
        "",
        "## AI Guidance",
        "",
        "When generating new code for this project:",
        "",
    ]
    if languages:
        primary = languages[0][0]
        lines.append(f"- **Primary language**: Write new code in {primary} unless the task specifies otherwise.")
    if frameworks:
        lines.append(f"- **Respect existing tooling**: {', '.join(frameworks[:3])} patterns are already in use.")
    if test_frameworks:
        lines.append(f"- **Test framework**: Write tests using {test_frameworks[0]}.")
    lines += [
        "- **Match file structure**: Place new files consistent with the directory tree above.",
        "- **Match style**: Follow existing linting and formatting conventions detected above.",
        "",
        "---",
        "*Update this profile by re-running `specify analyse-codebase --static`.*",
    ]

    out = profiles_dir / "codebase-profile.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    console.print(f"[green]✓[/green] Written: {out}")


def _ai_codebase_trigger(source: Path, profiles_dir: Path) -> None:
    trigger = profiles_dir / ".codebase-analyse-context.md"
    trigger.write_text(
        f"# Codebase Analysis Context\n\n"
        f"Source path: `{source}`\n\n"
        f"Run `/specpack.analyse-codebase` in your AI agent to complete AI-assisted analysis.\n",
        encoding="utf-8",
    )
    console.print(Panel(
        f"Context written to [bold]{trigger}[/bold]\n\n"
        "Now run [bold cyan]/specpack.analyse-codebase[/bold cyan] in your AI agent.\n"
        "The agent will analyse the codebase and write [bold]profiles/codebase-profile.md[/bold].",
        title="AI Analysis Ready",
        border_style="cyan",
    ))


# ─── performance ──────────────────────────────────────────────────────────────

@analyse_app.command("performance")
def analyse_performance(
    reportpath: Optional[Path] = typer.Option(None, "--reportpath", help="Directory of performance report files"),
    reportfile: Optional[Path] = typer.Option(None, "--reportfile", help="Single processed report file (csv/json/yaml)"),
) -> None:
    """Analyse performance reports and write profiles/performance-profile.md."""
    if not reportpath and not reportfile:
        console.print("[red]Error:[/red] Provide --reportpath or --reportfile.")
        raise typer.Exit(1)

    project_root = Path.cwd()
    profiles_dir = _ensure_profiles_dir(project_root)

    if reportfile:
        _static_performance_analysis(Path(reportfile).expanduser().resolve(), profiles_dir)
    else:
        _ai_performance_trigger(Path(reportpath).expanduser().resolve(), profiles_dir)


def _static_performance_analysis(report: Path, profiles_dir: Path) -> None:
    if not report.exists():
        console.print(f"[red]Error:[/red] File not found: {report}")
        raise typer.Exit(1)

    console.print(f"[cyan]Parsing performance report:[/cyan] {report}")
    rows = _load_report_file(report)
    stats = _extract_numeric_columns(rows)

    perf_keywords = ["time", "latency", "duration", "response", "ms", "sec",
                     "throughput", "rps", "tps", "error", "rate", "cpu", "memory", "mem"]

    perf_cols = {
        k: v for k, v in stats.items()
        if any(kw in k.lower() for kw in perf_keywords)
    }
    other_cols = {k: v for k, v in stats.items() if k not in perf_cols}

    lines: list[str] = [
        "# Performance Profile",
        "",
        "> Generated by: `specify analyse-performance --reportfile`",
        f"> Source: `{report.name}`",
        f"> Total records: {len(rows)}",
        "",
        "## Performance Metrics",
        "",
    ]

    def _stats_table(col_stats: dict[str, dict[str, float]]) -> list[str]:
        out = ["| Metric | Min | Mean | P50 | P90 | P95 | P99 | Max |",
               "|--------|-----|------|-----|-----|-----|-----|-----|"]
        for col, s in col_stats.items():
            out.append(
                f"| {col} | {s.get('min','-'):.2f} | {s.get('mean','-'):.2f} | "
                f"{s.get('p50','-'):.2f} | {s.get('p90','-'):.2f} | "
                f"{s.get('p95','-'):.2f} | {s.get('p99','-'):.2f} | "
                f"{s.get('max','-'):.2f} |"
            )
        return out

    if perf_cols:
        lines += _stats_table(perf_cols)
    else:
        lines.append("*No latency/throughput columns auto-detected. See raw stats below.*")

    if other_cols:
        lines += ["", "## Other Numeric Columns", ""]
        lines += _stats_table(other_cols)

    lines += [
        "",
        "## Implementation Constraints",
        "",
        "Apply these benchmarks when validating implementation performance:",
        "",
    ]
    for col, s in perf_cols.items():
        if "latency" in col.lower() or "time" in col.lower() or "response" in col.lower():
            lines.append(f"- **{col}**: target ≤ P90 baseline of `{s.get('p90', 0):.2f}`, never exceed `{s.get('p99', 0):.2f}`")
        elif "error" in col.lower():
            lines.append(f"- **{col}**: keep below observed mean of `{s.get('mean', 0):.4f}`")
        elif "throughput" in col.lower() or "rps" in col.lower() or "tps" in col.lower():
            lines.append(f"- **{col}**: maintain ≥ P50 baseline of `{s.get('p50', 0):.2f}`")

    lines += [
        "",
        "---",
        "*Update this profile by re-running `specify analyse-performance --reportfile <path>`.*",
    ]

    out = profiles_dir / "performance-profile.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    console.print(f"[green]✓[/green] Written: {out}")


def _ai_performance_trigger(reportpath: Path, profiles_dir: Path) -> None:
    if not reportpath.exists():
        console.print(f"[red]Error:[/red] Directory not found: {reportpath}")
        raise typer.Exit(1)

    report_files = [f for f in reportpath.rglob("*") if f.suffix.lower() in (".csv", ".json", ".yaml", ".yml")]
    trigger = profiles_dir / ".performance-analyse-context.md"
    trigger.write_text(
        f"# Performance Analysis Context\n\n"
        f"Report path: `{reportpath}`\n\n"
        f"Files found: {len(report_files)}\n\n" +
        "\n".join(f"- `{f.name}`" for f in report_files[:20]) +
        f"\n\nRun `/specpack.analyse-performance` in your AI agent to complete AI-assisted analysis.\n",
        encoding="utf-8",
    )
    console.print(Panel(
        f"Context written to [bold]{trigger}[/bold]\n\n"
        "Now run [bold cyan]/specpack.analyse-performance[/bold cyan] in your AI agent.\n"
        "The agent will analyse the reports and write [bold]profiles/performance-profile.md[/bold].",
        title="AI Analysis Ready",
        border_style="cyan",
    ))


# ─── customer ─────────────────────────────────────────────────────────────────

@analyse_app.command("customer")
def analyse_customer(
    reportpath: Optional[Path] = typer.Option(None, "--reportpath", help="Directory of customer report files"),
    reportfile: Optional[Path] = typer.Option(None, "--reportfile", help="Single processed report file (csv/json/yaml)"),
) -> None:
    """Analyse customer reports and write profiles/customer-profile.md."""
    if not reportpath and not reportfile:
        console.print("[red]Error:[/red] Provide --reportpath or --reportfile.")
        raise typer.Exit(1)

    project_root = Path.cwd()
    profiles_dir = _ensure_profiles_dir(project_root)

    if reportfile:
        _static_customer_analysis(Path(reportfile).expanduser().resolve(), profiles_dir)
    else:
        _ai_customer_trigger(Path(reportpath).expanduser().resolve(), profiles_dir)


def _static_customer_analysis(report: Path, profiles_dir: Path) -> None:
    if not report.exists():
        console.print(f"[red]Error:[/red] File not found: {report}")
        raise typer.Exit(1)

    console.print(f"[cyan]Parsing customer report:[/cyan] {report}")
    rows = _load_report_file(report)
    stats = _extract_numeric_columns(rows)

    scale_keywords = ["user", "customer", "session", "active", "dau", "mau", "count",
                      "total", "volume", "load", "concurrent", "peak"]
    usage_keywords = ["usage", "frequency", "request", "call", "event", "action",
                      "page", "view", "click", "conversion", "retention", "churn"]

    scale_cols = {k: v for k, v in stats.items() if any(kw in k.lower() for kw in scale_keywords)}
    usage_cols = {k: v for k, v in stats.items() if any(kw in k.lower() for kw in usage_keywords)}
    other_cols = {k: v for k, v in stats.items() if k not in scale_cols and k not in usage_cols}

    string_cols: dict[str, dict[str, int]] = {}
    for row in rows:
        for k, v in row.items():
            if k not in stats:
                string_cols.setdefault(k, {})
                val = str(v).strip()
                if val:
                    string_cols[k][val] = string_cols[k].get(val, 0) + 1

    lines: list[str] = [
        "# Customer Profile",
        "",
        "> Generated by: `specify analyse-customer --reportfile`",
        f"> Source: `{report.name}`",
        f"> Total records: {len(rows)}",
        "",
        "## Scale",
        "",
    ]

    def _stats_table(col_stats: dict[str, dict[str, float]]) -> list[str]:
        out = ["| Metric | Min | Mean | P50 | P90 | P95 | Max |",
               "|--------|-----|------|-----|-----|-----|-----|"]
        for col, s in col_stats.items():
            out.append(
                f"| {col} | {s.get('min',0):.1f} | {s.get('mean',0):.1f} | "
                f"{s.get('p50',0):.1f} | {s.get('p90',0):.1f} | "
                f"{s.get('p95',0):.1f} | {s.get('max',0):.1f} |"
            )
        return out

    if scale_cols:
        lines += _stats_table(scale_cols)
    else:
        lines.append("*No scale columns auto-detected.*")

    lines += ["", "## Usage Patterns", ""]
    if usage_cols:
        lines += _stats_table(usage_cols)
    else:
        lines.append("*No usage columns auto-detected.*")

    if string_cols:
        lines += ["", "## Categorical Distributions", ""]
        for col, value_counts in list(string_cols.items())[:8]:
            top = sorted(value_counts.items(), key=lambda x: -x[1])[:5]
            lines.append(f"### {col}")
            lines += ["| Value | Count |", "|-------|-------|"]
            for val, cnt in top:
                lines.append(f"| {val} | {cnt} |")
            lines.append("")

    lines += [
        "## Implementation Constraints",
        "",
        "Apply these customer insights when validating implementation:",
        "",
    ]
    for col, s in scale_cols.items():
        lines.append(f"- **{col}**: system must handle peak of `{s.get('max', 0):.0f}`, design for P95 of `{s.get('p95', 0):.0f}`")
    for col, s in usage_cols.items():
        lines.append(f"- **{col}**: typical load `{s.get('p50', 0):.1f}`, burst to `{s.get('p90', 0):.1f}`")

    lines += [
        "",
        "---",
        "*Update this profile by re-running `specify analyse-customer --reportfile <path>`.*",
    ]

    out = profiles_dir / "customer-profile.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    console.print(f"[green]✓[/green] Written: {out}")


def _ai_customer_trigger(reportpath: Path, profiles_dir: Path) -> None:
    if not reportpath.exists():
        console.print(f"[red]Error:[/red] Directory not found: {reportpath}")
        raise typer.Exit(1)

    report_files = [f for f in reportpath.rglob("*") if f.suffix.lower() in (".csv", ".json", ".yaml", ".yml")]
    trigger = profiles_dir / ".customer-analyse-context.md"
    trigger.write_text(
        f"# Customer Analysis Context\n\n"
        f"Report path: `{reportpath}`\n\n"
        f"Files found: {len(report_files)}\n\n" +
        "\n".join(f"- `{f.name}`" for f in report_files[:20]) +
        f"\n\nRun `/specpack.analyse-customer` in your AI agent to complete AI-assisted analysis.\n",
        encoding="utf-8",
    )
    console.print(Panel(
        f"Context written to [bold]{trigger}[/bold]\n\n"
        "Now run [bold cyan]/specpack.analyse-customer[/bold cyan] in your AI agent.\n"
        "The agent will analyse the reports and write [bold]profiles/customer-profile.md[/bold].",
        title="AI Analysis Ready",
        border_style="cyan",
    ))
