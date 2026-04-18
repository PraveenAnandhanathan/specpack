"""Tests for SpecPack analyse commands."""

import csv
import json
import os
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specify_cli import app

runner = CliRunner()


@pytest.fixture()
def tmp_project(tmp_path):
    """A temp directory simulating a project root."""
    original = Path.cwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(original)


@pytest.fixture()
def sample_repo(tmp_path):
    """A minimal fake repo for static codebase analysis."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("def main(): pass\n")
    (tmp_path / "src" / "utils.py").write_text("def helper(): pass\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_main.py").write_text("def test_main(): pass\n")
    (tmp_path / "requirements.txt").write_text("typer\nrich\n")
    (tmp_path / "pytest.ini").write_text("[pytest]\n")
    (tmp_path / "README.md").write_text("# My Project\n")
    return tmp_path


@pytest.fixture()
def sample_perf_csv(tmp_path):
    path = tmp_path / "perf.csv"
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["latency_ms", "throughput_rps", "error_rate"])
        w.writeheader()
        for i in range(100):
            w.writerow({"latency_ms": 10 + i, "throughput_rps": 500 - i, "error_rate": 0.01})
    return path


@pytest.fixture()
def sample_customer_json(tmp_path):
    path = tmp_path / "customers.json"
    data = [
        {"user_count": 1000, "dau": 200, "session_length_min": 5, "segment": "free"},
        {"user_count": 200, "dau": 180, "session_length_min": 20, "segment": "paid"},
        {"user_count": 50, "dau": 50, "session_length_min": 45, "segment": "enterprise"},
    ]
    path.write_text(json.dumps(data))
    return path


# ─── codebase ──────────────────────────────────────────────────────────────────

class TestAnalyseCodebaseStatic:

    def test_creates_profiles_dir(self, tmp_project, sample_repo):
        result = runner.invoke(app, ["analyse", "codebase", "--repopath", str(sample_repo), "--static"])
        assert result.exit_code == 0, result.output
        assert (tmp_project / "profiles").is_dir()

    def test_writes_codebase_profile(self, tmp_project, sample_repo):
        runner.invoke(app, ["analyse", "codebase", "--repopath", str(sample_repo), "--static"])
        profile = tmp_project / "profiles" / "codebase-profile.md"
        assert profile.exists()
        content = profile.read_text()
        assert "# Codebase Profile" in content
        assert "Python" in content

    def test_detects_pytest(self, tmp_project, sample_repo):
        runner.invoke(app, ["analyse", "codebase", "--repopath", str(sample_repo), "--static"])
        content = (tmp_project / "profiles" / "codebase-profile.md").read_text()
        assert "pytest" in content.lower()

    def test_detects_requirements_txt(self, tmp_project, sample_repo):
        runner.invoke(app, ["analyse", "codebase", "--repopath", str(sample_repo), "--static"])
        content = (tmp_project / "profiles" / "codebase-profile.md").read_text()
        assert "Python/pip" in content or "requirements" in content.lower()

    def test_here_flag_uses_cwd(self, tmp_project, sample_repo):
        os.chdir(sample_repo)
        result = runner.invoke(app, ["analyse", "codebase", "--here", "--static"])
        assert result.exit_code == 0
        os.chdir(tmp_project)

    def test_invalid_repopath_exits(self, tmp_project):
        result = runner.invoke(app, ["analyse", "codebase", "--repopath", "/nonexistent/path", "--static"])
        assert result.exit_code != 0

    def test_ai_mode_writes_trigger_file(self, tmp_project, sample_repo):
        runner.invoke(app, ["analyse", "codebase", "--repopath", str(sample_repo)])
        trigger = tmp_project / "profiles" / ".codebase-analyse-context.md"
        assert trigger.exists()


# ─── performance ───────────────────────────────────────────────────────────────

class TestAnalysePerformanceStatic:

    def test_creates_performance_profile_csv(self, tmp_project, sample_perf_csv):
        result = runner.invoke(app, ["analyse", "performance", "--reportfile", str(sample_perf_csv)])
        assert result.exit_code == 0
        profile = tmp_project / "profiles" / "performance-profile.md"
        assert profile.exists()
        content = profile.read_text()
        assert "# Performance Profile" in content
        assert "latency" in content.lower()

    def test_performance_profile_has_stats(self, tmp_project, sample_perf_csv):
        runner.invoke(app, ["analyse", "performance", "--reportfile", str(sample_perf_csv)])
        content = (tmp_project / "profiles" / "performance-profile.md").read_text()
        assert "P90" in content
        assert "P99" in content

    def test_performance_profile_has_constraints(self, tmp_project, sample_perf_csv):
        runner.invoke(app, ["analyse", "performance", "--reportfile", str(sample_perf_csv)])
        content = (tmp_project / "profiles" / "performance-profile.md").read_text()
        assert "Implementation Constraints" in content

    def test_missing_reportfile_exits(self, tmp_project):
        result = runner.invoke(app, ["analyse", "performance", "--reportfile", "/nonexistent/file.csv"])
        assert result.exit_code != 0

    def test_no_args_exits(self, tmp_project):
        result = runner.invoke(app, ["analyse", "performance"])
        assert result.exit_code != 0

    def test_ai_mode_with_reportpath(self, tmp_project, tmp_path):
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (reports_dir / "run1.csv").write_text("latency_ms\n10\n20\n")
        result = runner.invoke(app, ["analyse", "performance", "--reportpath", str(reports_dir)])
        assert result.exit_code == 0
        assert (tmp_project / "profiles" / ".performance-analyse-context.md").exists()


# ─── customer ──────────────────────────────────────────────────────────────────

class TestAnalyseCustomerStatic:

    def test_creates_customer_profile_json(self, tmp_project, sample_customer_json):
        result = runner.invoke(app, ["analyse", "customer", "--reportfile", str(sample_customer_json)])
        assert result.exit_code == 0
        profile = tmp_project / "profiles" / "customer-profile.md"
        assert profile.exists()
        content = profile.read_text()
        assert "# Customer Profile" in content

    def test_customer_profile_has_scale(self, tmp_project, sample_customer_json):
        runner.invoke(app, ["analyse", "customer", "--reportfile", str(sample_customer_json)])
        content = (tmp_project / "profiles" / "customer-profile.md").read_text()
        assert "Scale" in content
        assert "user_count" in content.lower() or "User" in content

    def test_customer_profile_has_segments(self, tmp_project, sample_customer_json):
        runner.invoke(app, ["analyse", "customer", "--reportfile", str(sample_customer_json)])
        content = (tmp_project / "profiles" / "customer-profile.md").read_text()
        assert "free" in content or "paid" in content or "enterprise" in content

    def test_customer_profile_has_constraints(self, tmp_project, sample_customer_json):
        runner.invoke(app, ["analyse", "customer", "--reportfile", str(sample_customer_json)])
        content = (tmp_project / "profiles" / "customer-profile.md").read_text()
        assert "Implementation Constraints" in content

    def test_no_args_exits(self, tmp_project):
        result = runner.invoke(app, ["analyse", "customer"])
        assert result.exit_code != 0

    def test_ai_mode_with_reportpath(self, tmp_project, tmp_path):
        reports_dir = tmp_path / "analytics"
        reports_dir.mkdir()
        (reports_dir / "data.json").write_text('[{"users": 100}]')
        result = runner.invoke(app, ["analyse", "customer", "--reportpath", str(reports_dir)])
        assert result.exit_code == 0
        assert (tmp_project / "profiles" / ".customer-analyse-context.md").exists()


# ─── yaml support ──────────────────────────────────────────────────────────────

class TestReportFileFormats:

    def test_yaml_performance_report(self, tmp_project, tmp_path):
        report = tmp_path / "perf.yaml"
        report.write_text("- latency_ms: 50\n  throughput_rps: 300\n- latency_ms: 80\n  throughput_rps: 250\n")
        result = runner.invoke(app, ["analyse", "performance", "--reportfile", str(report)])
        assert result.exit_code == 0
        assert (tmp_project / "profiles" / "performance-profile.md").exists()

    def test_yaml_customer_report(self, tmp_project, tmp_path):
        report = tmp_path / "customers.yaml"
        report.write_text("- user_count: 500\n  dau: 100\n- user_count: 200\n  dau: 180\n")
        result = runner.invoke(app, ["analyse", "customer", "--reportfile", str(report)])
        assert result.exit_code == 0
        assert (tmp_project / "profiles" / "customer-profile.md").exists()

    def test_unsupported_extension_exits(self, tmp_project, tmp_path):
        report = tmp_path / "data.xlsx"
        report.write_text("not parseable")
        result = runner.invoke(app, ["analyse", "performance", "--reportfile", str(report)])
        assert result.exit_code != 0
