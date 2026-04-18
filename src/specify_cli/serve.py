"""SpecPack serve — local read-only web UI for specs, archive, and profiles."""

from __future__ import annotations

import re
import threading
import webbrowser
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

console = Console()

# ─── helpers ──────────────────────────────────────────────────────────────────

def _project_root() -> Path:
    return Path.cwd()


def _render_md(text: str) -> str:
    """Convert markdown to HTML, colour-coding delta markers."""
    try:
        import markdown as md_lib
        html = md_lib.markdown(
            text,
            extensions=["tables", "fenced_code", "codehilite", "toc"],
        )
    except ImportError:
        # Minimal fallback: escape HTML, wrap paragraphs
        import html as html_lib
        safe = html_lib.escape(text)
        html = "<br>".join(safe.splitlines())

    # Colour delta markers wherever they appear
    html = re.sub(r"\[ADDED\]", '<span class="delta-added">[ADDED]</span>', html)
    html = re.sub(r"\[MODIFIED\]", '<span class="delta-modified">[MODIFIED]</span>', html)
    html = re.sub(r"\[REMOVED\]", '<span class="delta-removed">[REMOVED]</span>', html)
    html = re.sub(r"\[UNCHANGED\]", '<span class="delta-unchanged">[UNCHANGED]</span>', html)
    return html


def _scan_delta(text: str) -> dict[str, int]:
    pattern = re.compile(r"\[(ADDED|MODIFIED|REMOVED|UNCHANGED)\]", re.IGNORECASE)
    counts: dict[str, int] = {"ADDED": 0, "MODIFIED": 0, "REMOVED": 0, "UNCHANGED": 0}
    for m in pattern.finditer(text):
        counts[m.group(1).upper()] += 1
    return counts


def _parse_validation_status(root: Path) -> dict[str, str]:
    """Read profiles/.validation-status.md and return {functional, performance, customer}."""
    vf = root / "profiles" / ".validation-status.md"
    result = {"functional": "unknown", "performance": "unknown", "customer": "unknown"}
    if not vf.exists():
        return result
    text = vf.read_text(encoding="utf-8")
    for line in text.splitlines():
        low = line.lower()
        if "e2e overall functional" in low:
            result["functional"] = "PASS" if "pass" in low else ("FAIL" if "fail" in low else "WARN")
        elif "e2e overall performance" in low:
            result["performance"] = "PASS" if "pass" in low else ("FAIL" if "fail" in low else "WARN")
        elif "e2e overall customer" in low:
            result["customer"] = "PASS" if "pass" in low else ("FAIL" if "fail" in low else "WARN")
    return result


def _active_features(root: Path) -> list[Path]:
    specs = root / "specs"
    if not specs.exists():
        return []
    return sorted(
        d for d in specs.iterdir()
        if d.is_dir() and d.name != "archive" and not d.name.startswith(".")
    )


def _archived_features(root: Path) -> list[Path]:
    archive = root / "specs" / "archive"
    if not archive.exists():
        return []
    return sorted(d for d in archive.iterdir() if d.is_dir() and not d.name.startswith("."))


def _profiles_exist(root: Path) -> dict[str, bool]:
    p = root / "profiles"
    return {
        "codebase": (p / "codebase-profile.md").exists(),
        "performance": (p / "performance-profile.md").exists(),
        "customer": (p / "customer-profile.md").exists(),
    }


# ─── HTML / CSS ───────────────────────────────────────────────────────────────

_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
     display:flex;min-height:100vh;background:#f6f8fa;color:#24292f}
/* sidebar */
nav{width:230px;min-height:100vh;background:#2d333b;color:#cdd9e5;
    padding:0;position:fixed;top:0;left:0;overflow-y:auto;z-index:10}
nav .brand{padding:18px 16px 16px;border-bottom:1px solid #444c56}
nav .brand h1{font-size:15px;font-weight:700;color:#e6edf3;letter-spacing:2px}
nav .brand p{font-size:11px;color:#768390;margin-top:2px}
nav ul{list-style:none;padding:8px 0}
nav li a{display:block;padding:6px 14px;color:#adbac7;text-decoration:none;
         font-size:13px;border-radius:4px;margin:1px 6px;white-space:nowrap;
         overflow:hidden;text-overflow:ellipsis}
nav li a:hover,nav li a.active{background:#373e47;color:#cdd9e5}
nav .sec{padding:12px 14px 3px;font-size:10px;font-weight:700;
         color:#545d68;text-transform:uppercase;letter-spacing:.8px}
/* main */
main{margin-left:230px;padding:32px 36px;width:100%}
/* page header */
.ph{margin-bottom:24px}
.ph h2{font-size:20px;font-weight:700;color:#24292f}
.ph p{color:#57606a;font-size:13px;margin-top:4px}
/* cards */
.card{background:#fff;border:1px solid #d0d7de;border-radius:8px;
      padding:18px 20px;margin-bottom:12px}
.card h3{font-size:14px;font-weight:600;margin-bottom:5px}
.card h3 a{text-decoration:none;color:#0969da}
.card h3 a:hover{text-decoration:underline}
.card .meta{font-size:12px;color:#57606a}
/* grid */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}
/* badges */
.badge{display:inline-block;padding:2px 8px;border-radius:12px;
       font-size:11px;font-weight:600;margin-right:4px;margin-top:3px}
.bg-added{background:#dafbe1;color:#1a7f37}
.bg-modified{background:#fff8c5;color:#9a6700}
.bg-removed{background:#ffebe9;color:#cf222e}
.bg-unchanged{background:#f6f8fa;color:#57606a;border:1px solid #d0d7de}
.bg-pass{background:#dafbe1;color:#1a7f37}
.bg-fail{background:#ffebe9;color:#cf222e}
.bg-warn{background:#fff8c5;color:#9a6700}
.bg-unknown{background:#f6f8fa;color:#57606a;border:1px solid #d0d7de}
/* tabs */
.tabs{display:flex;gap:0;margin-bottom:20px;border-bottom:2px solid #d0d7de}
.tab{padding:8px 18px;text-decoration:none;color:#57606a;font-size:13px;
     border-bottom:2px solid transparent;margin-bottom:-2px}
.tab:hover{color:#24292f}
.tab.active{color:#0969da;border-bottom-color:#0969da;font-weight:600}
/* markdown */
.md{background:#fff;border:1px solid #d0d7de;border-radius:8px;padding:28px 32px}
.md h1,.md h2,.md h3{color:#0d1117;margin:20px 0 8px;
    padding-bottom:6px;border-bottom:1px solid #eaecef}
.md h1{font-size:22px}.md h2{font-size:17px}.md h3{font-size:15px}
.md p{margin:8px 0;line-height:1.65;font-size:14px}
.md ul,.md ol{margin:8px 0 8px 22px;line-height:1.85;font-size:14px}
.md code{background:#f6f8fa;border:1px solid #d0d7de;border-radius:4px;
         padding:1px 6px;font-size:12px;font-family:'SFMono-Regular',Consolas,monospace}
.md pre{background:#f6f8fa;border:1px solid #d0d7de;border-radius:6px;
        padding:14px 16px;overflow-x:auto;margin:12px 0}
.md pre code{border:none;padding:0;background:transparent;font-size:13px}
.md table{border-collapse:collapse;width:100%;margin:12px 0;font-size:13px}
.md th{background:#f6f8fa;font-weight:600}
.md th,.md td{border:1px solid #d0d7de;padding:8px 12px;text-align:left}
/* delta colours */
.delta-added{color:#1a7f37;font-weight:700}
.delta-modified{color:#9a6700;font-weight:700}
.delta-removed{color:#cf222e;font-weight:700}
.delta-unchanged{color:#57606a}
/* empty */
.empty{color:#57606a;font-size:14px;padding:40px 0;text-align:center}
/* validation bar */
.vbar{display:flex;gap:8px;margin-top:6px;flex-wrap:wrap}
/* section divider */
.divider{border:none;border-top:1px solid #d0d7de;margin:24px 0}
/* profile grid */
.profile-col{background:#fff;border:1px solid #d0d7de;border-radius:8px;padding:20px 24px}
.profile-col h3{font-size:14px;font-weight:700;color:#0969da;margin-bottom:12px;
    padding-bottom:8px;border-bottom:1px solid #eaecef}
.profile-col .exists{font-size:12px;color:#1a7f37}
.profile-col .missing{font-size:12px;color:#57606a}
"""

def _page(title: str, body: str, root: Path,
          nav_home: str = "", nav_archive: str = "", nav_profiles: str = "",
          active_feature: str = "") -> str:
    features = _active_features(root)
    feature_links = ""
    for f in features:
        cls = "active" if f.name == active_feature else ""
        feature_links += f'<li><a href="/feature/{f.name}" class="{cls}" title="{f.name}">{f.name}</a></li>\n'
    if not features:
        feature_links = '<li><a href="#" style="opacity:.5;cursor:default">No active features</a></li>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — SpecPack</title>
<style>{_CSS}</style>
</head>
<body>
<nav>
  <div class="brand"><h1>SPECPACK</h1><p>Spec-Driven Development</p></div>
  <ul>
    <li class="sec">Active Features</li>
    {feature_links}
    <li class="sec">History</li>
    <li><a href="/archive" class="{nav_archive}">Archive</a></li>
    <li class="sec">Profiles</li>
    <li><a href="/profiles" class="{nav_profiles}">Profiles</a></li>
    <li class="sec">Project</li>
    <li><a href="/" class="{nav_home}">Dashboard</a></li>
  </ul>
</nav>
<main>{body}</main>
</body>
</html>"""


def _badge(label: str, cls: str) -> str:
    return f'<span class="badge {cls}">{label}</span>'


def _validation_badges(vs: dict[str, str]) -> str:
    out = '<div class="vbar">'
    for key in ("functional", "performance", "customer"):
        val = vs.get(key, "unknown").upper()
        cls = {"PASS": "bg-pass", "FAIL": "bg-fail", "WARN": "bg-warn"}.get(val, "bg-unknown")
        out += _badge(f"{key[:4].capitalize()} {val}", cls)
    out += "</div>"
    return out


def _delta_badges(counts: dict[str, int]) -> str:
    out = ""
    if counts["ADDED"]:
        out += _badge(f"+{counts['ADDED']} added", "bg-added")
    if counts["MODIFIED"]:
        out += _badge(f"~{counts['MODIFIED']} modified", "bg-modified")
    if counts["REMOVED"]:
        out += _badge(f"-{counts['REMOVED']} removed", "bg-removed")
    if counts["UNCHANGED"]:
        out += _badge(f"{counts['UNCHANGED']} unchanged", "bg-unchanged")
    return out or '<span style="font-size:12px;color:#57606a">No delta markers</span>'


# ─── route handlers ───────────────────────────────────────────────────────────

def _home(root: Path) -> str:
    features = _active_features(root)
    vs = _parse_validation_status(root)
    archived = _archived_features(root)

    cards = ""
    for f in features:
        # Gather delta across spec/plan/tasks
        combined = ""
        for fname in ("spec.md", "plan.md", "tasks.md"):
            fp = f / fname
            if fp.exists():
                combined += fp.read_text(encoding="utf-8", errors="replace")
        counts = _scan_delta(combined)
        task_total = len(re.findall(r"^- \[[ xX]\]", combined, re.MULTILINE))
        task_done = len(re.findall(r"^- \[[xX]\]", combined, re.MULTILINE))
        badges = _delta_badges(counts)
        vbadges = _validation_badges(vs)
        tasks_str = f'<span style="font-size:12px;color:#57606a;margin-top:4px;display:block">Tasks: {task_done}/{task_total}</span>' if task_total else ""
        cards += f"""
<div class="card">
  <h3><a href="/feature/{f.name}">{f.name}</a></h3>
  <div style="margin:4px 0">{badges}</div>
  {vbadges}
  {tasks_str}
</div>"""

    if not features:
        cards = '<p class="empty">No active features — run <code>/specpack.specify</code> to create one.</p>'

    archive_count = len(archived)
    archive_note = f'<a href="/archive">{archive_count} archived feature{"s" if archive_count != 1 else ""}</a>' if archive_count else "No archived features yet"

    body = f"""
<div class="ph"><h2>Dashboard</h2>
<p>Active features in <code>specs/</code> &nbsp;·&nbsp; {archive_note}</p></div>
<div class="grid">{cards}</div>"""
    return _page("Dashboard", body, root, nav_home="active")


def _feature(root: Path, name: str, tab: str = "spec") -> str:
    fdir = root / "specs" / name
    if not fdir.exists():
        return _page("Not found", '<p class="empty">Feature not found.</p>', root)

    files = {"spec": "spec.md", "plan": "plan.md", "tasks": "tasks.md", "delta": None}
    tabs_html = ""
    for key in files:
        cls = "tab active" if key == tab else "tab"
        tabs_html += f'<a href="/feature/{name}/{key}" class="{cls}">{key.capitalize()}</a>'

    if tab == "delta":
        combined = ""
        for fname in ("spec.md", "plan.md", "tasks.md"):
            fp = fdir / fname
            if fp.exists():
                combined += fp.read_text(encoding="utf-8", errors="replace")

        DELTA_LINE = re.compile(r"^\s*[-*]\s*\[?(ADDED|MODIFIED|REMOVED|UNCHANGED)\]?\s+(.+)$", re.IGNORECASE)
        buckets: dict[str, list[str]] = {"ADDED": [], "MODIFIED": [], "REMOVED": [], "UNCHANGED": []}
        for line in combined.splitlines():
            m = DELTA_LINE.match(line)
            if m:
                buckets[m.group(1).upper()].append(m.group(2).strip())

        def bucket_html(key: str, cls: str) -> str:
            items = buckets[key]
            if not items:
                return ""
            rows = "".join(f"<li>{i}</li>" for i in items)
            return f'<h3><span class="{cls}">[{key}]</span> — {len(items)} item{"s" if len(items)!=1 else ""}</h3><ul style="margin:4px 0 16px 22px;font-size:14px;line-height:1.8">{rows}</ul>'

        delta_body = (
            bucket_html("ADDED", "delta-added") +
            bucket_html("MODIFIED", "delta-modified") +
            bucket_html("REMOVED", "delta-removed") +
            bucket_html("UNCHANGED", "delta-unchanged")
        )
        if not any(buckets.values()):
            delta_body = '<p style="color:#57606a;font-size:14px">No delta markers found. Run <code>/specpack.specify</code> with a brownfield project to annotate requirements.</p>'
        content = f'<div class="md">{delta_body}</div>'
    else:
        md_file = fdir / files[tab]
        if md_file and md_file.exists():
            text = md_file.read_text(encoding="utf-8", errors="replace")
            content = f'<div class="md">{_render_md(text)}</div>'
        else:
            content = f'<p class="empty"><code>{files[tab]}</code> not found in this feature.</p>'

    body = f"""
<div class="ph"><h2>{name}</h2>
<p><a href="/" style="color:#57606a;font-size:13px">← Dashboard</a></p></div>
<div class="tabs">{tabs_html}</div>
{content}"""
    return _page(name, body, root, active_feature=name)


def _archive_list(root: Path) -> str:
    features = _archived_features(root)
    cards = ""
    for f in features:
        arch_md = f / "ARCHIVE.md"
        archived_date = ""
        counts: dict[str, int] = {"ADDED": 0, "MODIFIED": 0, "REMOVED": 0, "UNCHANGED": 0}
        val_line = ""
        if arch_md.exists():
            text = arch_md.read_text(encoding="utf-8", errors="replace")
            counts = _scan_delta(text)
            m = re.search(r"Archived:\s*(.+)", text)
            if m:
                archived_date = m.group(1).strip()
            for label in ("Functional", "Performance", "Customer"):
                row = re.search(rf"\|\s*{label}\s*\|\s*(\w+)\s*\|", text, re.IGNORECASE)
                if row:
                    val = row.group(1).upper()
                    cls = {"PASS": "bg-pass", "FAIL": "bg-fail", "WARN": "bg-warn"}.get(val, "bg-unknown")
                    val_line += _badge(f"{label[:4]} {val}", cls)

        badges = _delta_badges(counts)
        date_str = f'<span style="font-size:12px;color:#57606a">Archived: {archived_date}</span>' if archived_date else ""
        cards += f"""
<div class="card">
  <h3><a href="/archive/{f.name}">{f.name}</a></h3>
  <div style="margin:4px 0">{badges}</div>
  <div class="vbar">{val_line}</div>
  {date_str}
</div>"""

    if not features:
        cards = '<p class="empty">No archived features yet. Run <code>specify archive</code> after a feature is complete.</p>'

    body = f'<div class="ph"><h2>Archive</h2><p>Completed features in <code>specs/archive/</code></p></div><div class="grid">{cards}</div>'
    return _page("Archive", body, root, nav_archive="active")


def _archive_detail(root: Path, name: str) -> str:
    fdir = root / "specs" / "archive" / name
    if not fdir.exists():
        return _page("Not found", '<p class="empty">Archived feature not found.</p>', root, nav_archive="active")

    arch_md = fdir / "ARCHIVE.md"
    if arch_md.exists():
        text = arch_md.read_text(encoding="utf-8", errors="replace")
        content = f'<div class="md">{_render_md(text)}</div>'
    else:
        content = '<p class="empty">ARCHIVE.md not found.</p>'

    other_tabs = ""
    for fname in ("spec.md", "plan.md", "tasks.md"):
        if (fdir / fname).exists():
            tab = fname.replace(".md", "")
            other_tabs += f'<a href="/archive/{name}/{tab}" class="tab">{tab.capitalize()}</a>'

    tabs_html = f'<a href="/archive/{name}" class="tab active">Archive</a>{other_tabs}'

    body = f"""
<div class="ph"><h2>{name}</h2>
<p><a href="/archive" style="color:#57606a;font-size:13px">← Archive</a></p></div>
<div class="tabs">{tabs_html}</div>
{content}"""
    return _page(name, body, root, nav_archive="active")


def _archive_file(root: Path, name: str, tab: str) -> str:
    fdir = root / "specs" / "archive" / name
    fname = f"{tab}.md"
    fp = fdir / fname
    if not fp.exists():
        return _page("Not found", f'<p class="empty"><code>{fname}</code> not found.</p>', root, nav_archive="active")

    other_tabs = ""
    for fn in ("spec.md", "plan.md", "tasks.md"):
        if (fdir / fn).exists():
            t = fn.replace(".md", "")
            cls = "tab active" if t == tab else "tab"
            other_tabs += f'<a href="/archive/{name}/{t}" class="{cls}">{t.capitalize()}</a>'

    tabs_html = f'<a href="/archive/{name}" class="tab">Archive</a>{other_tabs}'
    text = fp.read_text(encoding="utf-8", errors="replace")
    content = f'<div class="md">{_render_md(text)}</div>'

    body = f"""
<div class="ph"><h2>{name} / {fname}</h2>
<p><a href="/archive/{name}" style="color:#57606a;font-size:13px">← {name}</a></p></div>
<div class="tabs">{tabs_html}</div>
{content}"""
    return _page(f"{name}/{fname}", body, root, nav_archive="active")


def _profiles(root: Path) -> str:
    exists = _profiles_exist(root)
    cols = ""
    for key, fname in (("codebase", "codebase-profile.md"),
                        ("performance", "performance-profile.md"),
                        ("customer", "customer-profile.md")):
        fp = root / "profiles" / fname
        if fp.exists():
            text = fp.read_text(encoding="utf-8", errors="replace")
            rendered = _render_md(text)
            cols += f'<div class="profile-col"><h3>{key.capitalize()} Profile</h3>{rendered}</div>'
        else:
            cmd = f"specify analyse-{key}"
            cols += f"""<div class="profile-col">
  <h3>{key.capitalize()} Profile</h3>
  <p class="missing">Not generated yet.</p>
  <p style="font-size:12px;color:#57606a;margin-top:8px">Run: <code>{cmd}</code></p>
</div>"""

    any_exists = any(exists.values())
    subtitle = "Generated from <code>specify analyse-*</code> commands" if any_exists else "No profiles yet — run <code>specify analyse-codebase</code>, <code>specify analyse-performance</code>, or <code>specify analyse-customer</code>"
    body = f"""
<div class="ph"><h2>Profiles</h2><p>{subtitle}</p></div>
<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px">{cols}</div>"""
    return _page("Profiles", body, root, nav_profiles="active")


# ─── FastAPI app factory ───────────────────────────────────────────────────────

def _build_app(root: Path):
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse

    app = FastAPI(title="SpecPack", docs_url=None, redoc_url=None)

    @app.get("/", response_class=HTMLResponse)
    def home():
        return _home(root)

    @app.get("/feature/{name}", response_class=HTMLResponse)
    def feature(name: str):
        return _feature(root, name, "spec")

    @app.get("/feature/{name}/{tab}", response_class=HTMLResponse)
    def feature_tab(name: str, tab: str):
        if tab not in ("spec", "plan", "tasks", "delta"):
            tab = "spec"
        return _feature(root, name, tab)

    @app.get("/archive", response_class=HTMLResponse)
    def archive_list():
        return _archive_list(root)

    @app.get("/archive/{name}", response_class=HTMLResponse)
    def archive_detail(name: str):
        return _archive_detail(root, name)

    @app.get("/archive/{name}/{tab}", response_class=HTMLResponse)
    def archive_file(name: str, tab: str):
        return _archive_file(root, name, tab)

    @app.get("/profiles", response_class=HTMLResponse)
    def profiles():
        return _profiles(root)

    return app


# ─── CLI entry point ──────────────────────────────────────────────────────────

def run_serve(port: int = 4242, host: str = "127.0.0.1", no_browser: bool = False):
    """Start the SpecPack local web UI."""
    try:
        import uvicorn
    except ImportError:
        console.print("[red]serve requires optional dependencies:[/red]")
        console.print("  [bold]pip install 'specpack-cli\\[serve\\]'[/bold]")
        console.print("  [bold]uv tool install 'specpack-cli\\[serve\\]'[/bold]")
        raise typer.Exit(1)

    root = _project_root()
    if not (root / ".specify").exists():
        console.print("[red]Not a SpecPack project.[/red] Run [bold]specify init[/bold] first.")
        raise typer.Exit(1)

    app = _build_app(root)
    url = f"http://{host}:{port}"

    console.print(f"\n[bold green]SpecPack[/bold green] serving at [cyan]{url}[/cyan]")
    console.print(f"[dim]Project: {root}[/dim]")
    console.print("[dim]Press Ctrl+C to stop.[/dim]\n")

    if not no_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    import uvicorn
    uvicorn.run(app, host=host, port=port, log_level="error")
