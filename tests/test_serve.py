"""Tests for specify serve web UI."""

import json
import os
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from specify_cli.serve import _build_app


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
def client(tmp_project):
    app = _build_app(tmp_project)
    return TestClient(app)


@pytest.fixture()
def project_with_feature(tmp_project):
    fd = tmp_project / "specs" / "001-auth"
    fd.mkdir()
    (fd / "spec.md").write_text(
        "# Auth Spec\n\n"
        "- [ADDED] User registration\n"
        "- [MODIFIED] Login requires 2FA\n"
        "- [REMOVED] SMS OTP\n"
        "- [UNCHANGED] OAuth via Google\n",
        encoding="utf-8",
    )
    (fd / "plan.md").write_text("# Plan\n\n- [ADDED] New auth service\n", encoding="utf-8")
    (fd / "tasks.md").write_text(
        "- [x] T001 [ADDED] Create auth endpoint\n"
        "- [ ] T002 [MODIFIED] Update login handler\n",
        encoding="utf-8",
    )
    return fd


@pytest.fixture()
def project_with_archive(tmp_project, project_with_feature):
    archive_dir = tmp_project / "specs" / "archive" / "001-auth"
    archive_dir.mkdir(parents=True)
    (archive_dir / "ARCHIVE.md").write_text(
        "# Archive: 001-auth\n\nArchived: 2026-04-19\nStatus: ALL VALIDATIONS PASSED\n\n"
        "## Delta Summary\n\n- ADDED: 2 items\n- MODIFIED: 1 item\n\n"
        "## Validation Results\n\n"
        "| Type | E2E Status |\n|------|---|\n"
        "| Functional | PASS |\n| Performance | PASS |\n| Customer | PASS |\n\n"
        "## Tasks\n\n- Total: 2\n- Completed: 2\n",
        encoding="utf-8",
    )
    (archive_dir / "spec.md").write_text("# Archived spec\n", encoding="utf-8")
    return archive_dir


@pytest.fixture()
def project_with_profiles(tmp_project):
    p = tmp_project / "profiles"
    (p / "codebase-profile.md").write_text("# Codebase Profile\n\nLanguage: Python\n", encoding="utf-8")
    (p / "performance-profile.md").write_text("# Performance Profile\n\nP95: 200ms\n", encoding="utf-8")
    (p / "customer-profile.md").write_text("# Customer Profile\n\nPeak: 1000 users\n", encoding="utf-8")
    (p / ".validation-status.md").write_text(
        "# Validation Status\n\n## E2E overall functional PASS\n## E2E overall performance PASS\n## E2E overall customer PASS\n",
        encoding="utf-8",
    )
    return p


# ─── home ─────────────────────────────────────────────────────────────────────

class TestHome:
    def test_home_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_home_html_content(self, client):
        resp = client.get("/")
        assert "SPECPACK" in resp.text

    def test_home_shows_no_features_message(self, client):
        resp = client.get("/")
        assert "No active features" in resp.text

    def test_home_lists_active_features(self, tmp_project, project_with_feature):
        app = _build_app(tmp_project)
        c = TestClient(app)
        resp = c.get("/")
        assert "001-auth" in resp.text

    def test_home_shows_delta_badges(self, tmp_project, project_with_feature):
        app = _build_app(tmp_project)
        c = TestClient(app)
        resp = c.get("/")
        assert "added" in resp.text.lower()

    def test_home_shows_task_count(self, tmp_project, project_with_feature):
        app = _build_app(tmp_project)
        c = TestClient(app)
        resp = c.get("/")
        assert "1/2" in resp.text  # 1 done, 2 total

    def test_home_links_to_archive(self, tmp_project, project_with_archive):
        app = _build_app(tmp_project)
        c = TestClient(app)
        resp = c.get("/")
        assert "/archive" in resp.text


# ─── feature ──────────────────────────────────────────────────────────────────

class TestFeature:
    def test_feature_spec_tab_returns_200(self, tmp_project, project_with_feature):
        app = _build_app(tmp_project)
        c = TestClient(app)
        resp = c.get("/feature/001-auth")
        assert resp.status_code == 200

    def test_feature_renders_spec_content(self, tmp_project, project_with_feature):
        app = _build_app(tmp_project)
        c = TestClient(app)
        resp = c.get("/feature/001-auth/spec")
        assert "Auth Spec" in resp.text

    def test_feature_colours_added_marker(self, tmp_project, project_with_feature):
        app = _build_app(tmp_project)
        c = TestClient(app)
        resp = c.get("/feature/001-auth/spec")
        assert "delta-added" in resp.text

    def test_feature_colours_removed_marker(self, tmp_project, project_with_feature):
        app = _build_app(tmp_project)
        c = TestClient(app)
        resp = c.get("/feature/001-auth/spec")
        assert "delta-removed" in resp.text

    def test_feature_plan_tab(self, tmp_project, project_with_feature):
        app = _build_app(tmp_project)
        c = TestClient(app)
        resp = c.get("/feature/001-auth/plan")
        assert resp.status_code == 200
        assert "New auth service" in resp.text

    def test_feature_tasks_tab(self, tmp_project, project_with_feature):
        app = _build_app(tmp_project)
        c = TestClient(app)
        resp = c.get("/feature/001-auth/tasks")
        assert resp.status_code == 200
        assert "Create auth endpoint" in resp.text

    def test_feature_delta_tab(self, tmp_project, project_with_feature):
        app = _build_app(tmp_project)
        c = TestClient(app)
        resp = c.get("/feature/001-auth/delta")
        assert resp.status_code == 200
        assert "ADDED" in resp.text
        assert "MODIFIED" in resp.text
        assert "REMOVED" in resp.text

    def test_feature_delta_tab_counts(self, tmp_project, project_with_feature):
        app = _build_app(tmp_project)
        c = TestClient(app)
        resp = c.get("/feature/001-auth/delta")
        # spec has 1 ADDED, 1 MODIFIED, 1 REMOVED, 1 UNCHANGED; plan has 1 ADDED; tasks has 1 ADDED, 1 MODIFIED
        assert "3 items" in resp.text or "item" in resp.text

    def test_feature_not_found(self, client):
        resp = client.get("/feature/nonexistent")
        assert resp.status_code == 200  # returns HTML with not-found message
        assert "not found" in resp.text.lower()

    def test_feature_shows_tabs(self, tmp_project, project_with_feature):
        app = _build_app(tmp_project)
        c = TestClient(app)
        resp = c.get("/feature/001-auth")
        assert "Spec" in resp.text
        assert "Plan" in resp.text
        assert "Tasks" in resp.text
        assert "Delta" in resp.text


# ─── archive ──────────────────────────────────────────────────────────────────

class TestArchiveUI:
    def test_archive_list_returns_200(self, client):
        resp = client.get("/archive")
        assert resp.status_code == 200

    def test_archive_list_empty_message(self, client):
        resp = client.get("/archive")
        assert "No archived features" in resp.text

    def test_archive_list_shows_feature(self, tmp_project, project_with_archive):
        app = _build_app(tmp_project)
        c = TestClient(app)
        resp = c.get("/archive")
        assert "001-auth" in resp.text

    def test_archive_list_shows_archived_date(self, tmp_project, project_with_archive):
        app = _build_app(tmp_project)
        c = TestClient(app)
        resp = c.get("/archive")
        assert "2026-04-19" in resp.text

    def test_archive_list_shows_validation_badges(self, tmp_project, project_with_archive):
        app = _build_app(tmp_project)
        c = TestClient(app)
        resp = c.get("/archive")
        assert "PASS" in resp.text

    def test_archive_detail_returns_200(self, tmp_project, project_with_archive):
        app = _build_app(tmp_project)
        c = TestClient(app)
        resp = c.get("/archive/001-auth")
        assert resp.status_code == 200

    def test_archive_detail_renders_archive_md(self, tmp_project, project_with_archive):
        app = _build_app(tmp_project)
        c = TestClient(app)
        resp = c.get("/archive/001-auth")
        assert "Archive: 001-auth" in resp.text

    def test_archive_detail_shows_spec_tab(self, tmp_project, project_with_archive):
        app = _build_app(tmp_project)
        c = TestClient(app)
        resp = c.get("/archive/001-auth/spec")
        assert resp.status_code == 200
        assert "Archived spec" in resp.text

    def test_archive_detail_not_found(self, client):
        resp = client.get("/archive/nonexistent")
        assert resp.status_code == 200
        assert "not found" in resp.text.lower()


# ─── profiles ─────────────────────────────────────────────────────────────────

class TestProfilesUI:
    def test_profiles_returns_200(self, client):
        resp = client.get("/profiles")
        assert resp.status_code == 200

    def test_profiles_shows_missing_message(self, client):
        resp = client.get("/profiles")
        assert "Not generated yet" in resp.text

    def test_profiles_renders_codebase(self, tmp_project, project_with_profiles):
        app = _build_app(tmp_project)
        c = TestClient(app)
        resp = c.get("/profiles")
        assert "Codebase Profile" in resp.text
        assert "Python" in resp.text

    def test_profiles_renders_performance(self, tmp_project, project_with_profiles):
        app = _build_app(tmp_project)
        c = TestClient(app)
        resp = c.get("/profiles")
        assert "Performance Profile" in resp.text
        assert "P95" in resp.text

    def test_profiles_renders_customer(self, tmp_project, project_with_profiles):
        app = _build_app(tmp_project)
        c = TestClient(app)
        resp = c.get("/profiles")
        assert "Customer Profile" in resp.text
        assert "1000 users" in resp.text


# ─── navigation ───────────────────────────────────────────────────────────────

class TestNavigation:
    def test_sidebar_shows_active_features(self, tmp_project, project_with_feature):
        app = _build_app(tmp_project)
        c = TestClient(app)
        resp = c.get("/")
        assert 'href="/feature/001-auth"' in resp.text

    def test_sidebar_archive_link(self, client):
        resp = client.get("/")
        assert 'href="/archive"' in resp.text

    def test_sidebar_profiles_link(self, client):
        resp = client.get("/")
        assert 'href="/profiles"' in resp.text

    def test_active_nav_highlighted_on_archive(self, client):
        resp = client.get("/archive")
        assert 'class="active"' in resp.text or "active" in resp.text
