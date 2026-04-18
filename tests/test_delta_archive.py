"""Tests for SpecPack delta/archive commands and validate-stubs."""

import json
import os
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specify_cli import app

runner = CliRunner()


@pytest.fixture()
def tmp_project(tmp_path):
    original = Path.cwd()
    os.chdir(tmp_path)
    (tmp_path / ".specify").mkdir()
    (tmp_path / "specs").mkdir()
    (tmp_path / "profiles").mkdir()
    yield tmp_path
    os.chdir(original)


@pytest.fixture()
def feature_dir(tmp_project):
    fd = tmp_project / "specs" / "001-auth"
    fd.mkdir()
    (tmp_project / ".specify" / "feature.json").write_text(
        json.dumps({"feature_directory": "specs/001-auth"}), encoding="utf-8"
    )
    return fd


@pytest.fixture()
def feature_with_delta(feature_dir):
    (feature_dir / "spec.md").write_text(
        "## Requirements\n"
        "- [ADDED] User can register with email\n"
        "- [MODIFIED] Login requires 2FA\n"
        "- [REMOVED] SMS OTP\n"
        "- [UNCHANGED] OAuth via Google\n",
        encoding="utf-8",
    )
    (feature_dir / "plan.md").write_text(
        "## Design\n- [ADDED] New auth service\n",
        encoding="utf-8",
    )
    (feature_dir / "tasks.md").write_text(
        "- [x] T001 [ADDED] Create auth endpoint\n"
        "- [x] T002 [MODIFIED] Update login handler\n"
        "- [x] T003 [REMOVED] Remove SMS code\n",
        encoding="utf-8",
    )
    return feature_dir


@pytest.fixture()
def validation_status_passed(tmp_project):
    vf = tmp_project / "profiles" / ".validation-status.md"
    vf.write_text(
        "# Validation Status\n\n"
        "| Task | Functional | Performance | Customer | Updated |\n"
        "|------|-----------|------------|---------|--------|\n"
        "| T001 | PASS | PASS | PASS | today |\n"
        "\n## E2E overall functional PASS\n"
        "## E2E overall performance PASS\n"
        "## E2E overall customer PASS\n",
        encoding="utf-8",
    )
    return vf


# ─── delta ────────────────────────────────────────────────────────────────────

class TestDelta:

    def test_delta_shows_added(self, tmp_project, feature_with_delta):
        result = runner.invoke(app, ["delta"])
        assert result.exit_code == 0
        assert "ADDED" in result.output

    def test_delta_shows_modified(self, tmp_project, feature_with_delta):
        result = runner.invoke(app, ["delta"])
        assert "MODIFIED" in result.output

    def test_delta_shows_removed(self, tmp_project, feature_with_delta):
        result = runner.invoke(app, ["delta"])
        assert "REMOVED" in result.output

    def test_delta_no_feature_json_exits(self, tmp_project):
        result = runner.invoke(app, ["delta"])
        assert result.exit_code != 0

    def test_delta_no_markers_shows_message(self, tmp_project, feature_dir):
        (feature_dir / "spec.md").write_text("## Requirements\n- User can login\n")
        result = runner.invoke(app, ["delta"])
        assert result.exit_code == 0
        assert "No delta markers" in result.output or "delta" in result.output.lower()

    def test_delta_with_feature_flag(self, tmp_project, feature_with_delta):
        result = runner.invoke(app, ["delta", "--feature", "specs/001-auth"])
        assert result.exit_code == 0
        assert "ADDED" in result.output

    def test_delta_counts_correctly(self, tmp_project, feature_with_delta):
        result = runner.invoke(app, ["delta"])
        assert result.exit_code == 0
        # spec.md: 1 ADDED, 1 MODIFIED, 1 REMOVED, 1 UNCHANGED
        # plan.md: 1 ADDED
        # tasks.md: 1 ADDED, 1 MODIFIED, 1 REMOVED
        assert "ADDED" in result.output


# ─── archive ──────────────────────────────────────────────────────────────────

class TestArchive:

    def test_archive_blocked_without_validation(self, tmp_project, feature_with_delta):
        result = runner.invoke(app, ["archive"])
        assert result.exit_code != 0
        assert "BLOCKED" in result.output or "not fully passed" in result.output.lower()

    def test_archive_force_bypasses_validation(self, tmp_project, feature_with_delta):
        result = runner.invoke(app, ["archive", "--force"])
        assert result.exit_code == 0
        assert (tmp_project / "specs" / "archive" / "001-auth").exists()

    def test_archive_moves_feature_dir(self, tmp_project, feature_with_delta, validation_status_passed):
        runner.invoke(app, ["archive"])
        assert not (tmp_project / "specs" / "001-auth").exists()
        assert (tmp_project / "specs" / "archive" / "001-auth").exists()

    def test_archive_writes_archive_md(self, tmp_project, feature_with_delta, validation_status_passed):
        runner.invoke(app, ["archive"])
        archive_md = tmp_project / "specs" / "archive" / "001-auth" / "ARCHIVE.md"
        assert archive_md.exists()
        content = archive_md.read_text()
        assert "# Archive: 001-auth" in content

    def test_archive_md_has_delta_summary(self, tmp_project, feature_with_delta, validation_status_passed):
        runner.invoke(app, ["archive"])
        content = (tmp_project / "specs" / "archive" / "001-auth" / "ARCHIVE.md").read_text()
        assert "ADDED" in content
        assert "MODIFIED" in content
        assert "REMOVED" in content

    def test_archive_clears_feature_json(self, tmp_project, feature_with_delta, validation_status_passed):
        runner.invoke(app, ["archive"])
        fj = tmp_project / ".specify" / "feature.json"
        assert fj.read_text() == "{}"

    def test_archive_with_feature_flag(self, tmp_project, feature_with_delta):
        result = runner.invoke(app, ["archive", "--feature", "specs/001-auth", "--force"])
        assert result.exit_code == 0
        assert (tmp_project / "specs" / "archive" / "001-auth").exists()

    def test_archive_missing_feature_exits(self, tmp_project):
        result = runner.invoke(app, ["archive"])
        assert result.exit_code != 0

    def test_archive_creates_archive_dir(self, tmp_project, feature_with_delta, validation_status_passed):
        runner.invoke(app, ["archive"])
        assert (tmp_project / "specs" / "archive").is_dir()

    def test_archive_task_counts_in_archive_md(self, tmp_project, feature_with_delta, validation_status_passed):
        runner.invoke(app, ["archive"])
        content = (tmp_project / "specs" / "archive" / "001-auth" / "ARCHIVE.md").read_text()
        assert "Tasks" in content
        assert "3" in content  # 3 tasks in tasks.md


# ─── validate-stubs ───────────────────────────────────────────────────────────

class TestValidateStubs:

    def test_no_stubs_exits_gracefully(self, tmp_project):
        result = runner.invoke(app, ["validate-stubs"])
        assert result.exit_code == 0
        assert "No stub" in result.output or "stub" in result.output.lower()

    def test_finds_stubs_in_specs(self, tmp_project):
        stub_dir = tmp_project / "specs" / "001-auth" / "tests" / "stubs"
        stub_dir.mkdir(parents=True)
        (stub_dir / "T001_stub.py").write_text(
            "def test_T001_stub():\n    assert False, 'not implemented'\n"
        )
        result = runner.invoke(app, ["validate-stubs"])
        assert result.exit_code == 0
        assert "T001_stub" in result.output
