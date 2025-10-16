import uuid

import pytest
import requests
from gitlab import Gitlab, GitlabAuthenticationError, GitlabGetError

from devdox_ai_git.exceptions.base_exceptions import DevDoxGitException
from devdox_ai_git.exceptions.exception_constants import (
    GIT_AUTH_FAILED,
    GIT_PROJECT_FETCH_FAILED,
    GIT_PROJECT_LANGUAGE_FETCH_FAILED,
)
from devdox_ai_git.git_managers import GitLabManager

# ********************************************************************
# YOU NEED TO COMMENT THIS IF YOU WILL USE THIS MODULE IN REAL TESTS
# ********************************************************************
pytest.skip("manual test module", allow_module_level=True)
# ********************************************************************
# ********************************************************************
# ********************************************************************

# ********************************************************************
# SETUP:: SOME VALUES NEED TO BE CHANGED
# ********************************************************************

gitlab_email_account = "monty_testing_acc@outlook.com"
gitlab_username = "montytestingacc"
gitlab_access_token = "<A GITLAB USER ACCESS TOKEN>"
gitlab_projects = {
    "prj1": {
        "full_name": "montytestingacc/HTMLPortfolioProject",
        "id": 5,
        "project_languages": ["HTML", "JavaScript"],
    },
    "prj2": {
        "full_name": "montytestingacc/tictactoe",
        "id": 6,
        "project_languages": ["Dart", "HTML", "Ruby", "Swift", "Java", "Kotlin"],
    },
    "prj3": {
        "full_name": "montytestingacc/cppcheck",
        "id": 4,
        "project_languages": [
            "C++",
            "Python",
            "C",
            "Makefile",
            "CMake",
            "Shell",
            "Other",
        ],
    },
}
# ********************************************************************
# ********************************************************************
# ********************************************************************

class TestGitLabManager:
    manager = GitLabManager(base_url="http://localhost:8080")

    def test_authenticate_should_authenticate_successfully_with_base_url(self):
        authenticated_git_lab_manager = self.manager.authenticate(gitlab_access_token)

        assert authenticated_git_lab_manager

    def test_authenticate_should_raise_exception_when_access_token_invalid(self):
        with pytest.raises(DevDoxGitException) as exp:
            _ = self.manager.authenticate("<SOME INVALID ACCESS TOKEN>")

        assert exp.value.user_message == GIT_AUTH_FAILED
        assert isinstance(exp.value.__context__, GitlabAuthenticationError)
        assert exp.value.__context__.response_code == 401


class TestAuthenticatedGitLabManager:
    git_lab_manager = GitLabManager(base_url="http://localhost:8080")
    authenticated_git_lab_manager = git_lab_manager.authenticate(gitlab_access_token)

    @pytest.fixture
    def gl_temp_project(self):
        """
        Creates a temporary GitLab project (initialize_with_readme=True),
        yields the Project and a cleanup function that permanently removes it.
        """
        name = f"it-{uuid.uuid4().hex[:12]}-gl"
        project = self.authenticated_git_lab_manager.create_repository(
            name=name,
            description="Ephemeral test project (GitLab)",
            visibility="private",
            auto_init=True,
        )

        def _cleanup():
            try:
                project.delete(permanently_remove=True, full_path=project.path_with_namespace)
            except Exception:
                pass

        try:
            yield project, _cleanup
        finally:
            _cleanup()

    def test_get_project_should_succeed_with_project_or_project_id(self):
        project_meta = gitlab_projects["prj1"]

        project_via_project_id = self.authenticated_git_lab_manager.get_project(
            project_meta["id"]
        )

        assert project_via_project_id.id == project_meta["id"]
        assert project_via_project_id.statistics

    def test_get_project_should_raise_exception_when_project_does_not_exist(self):
        with pytest.raises(DevDoxGitException) as exp:
            _ = self.authenticated_git_lab_manager.get_project("<NON_EXISTENT_PROJECT>")

        assert exp.value.user_message == GIT_PROJECT_FETCH_FAILED
        assert isinstance(exp.value.__context__, GitlabGetError)
        assert exp.value.__context__.response_code == 404

    def test_get_project_languages_should_return_with_project_or_id(
        self,
    ):
        project_meta = gitlab_projects["prj1"]

        project_languages_via_id = (
            self.authenticated_git_lab_manager.get_project_languages(
                project_meta["id"]
            )
        )

        project = self.authenticated_git_lab_manager.get_project(project_meta["id"])
        project_languages_via_repository = (
            self.authenticated_git_lab_manager.get_project_languages(project)
        )

        assert all(
            n in project_meta["project_languages"] for n in project_languages_via_id
        )
        assert all(
            n in project_meta["project_languages"]
            for n in project_languages_via_repository
        )

    def test_get_project_languages_should_raise_exception_when_project_does_not_exist(
        self,
    ):
        with pytest.raises(DevDoxGitException) as exp:
            _ = self.authenticated_git_lab_manager.get_project_languages(
                "<NON_EXISTENT_PROJECT>"
            )

        assert exp.value.user_message == GIT_PROJECT_LANGUAGE_FETCH_FAILED
        assert isinstance(exp.value.__context__, GitlabGetError)
        assert exp.value.__context__.response_code == 404

    def test_get_user_should_return_when_user_exists(self):
        retrieved_user: dict = self.authenticated_git_lab_manager.get_user()

        assert retrieved_user["username"] == gitlab_username

    def test_get_user_repositories_returns_paginated_values(self):
        per_page = 2

        # Call SUT (manager) for page 1 and 2
        page1 = self.authenticated_git_lab_manager.get_user_repositories(
            page=1, per_page=per_page
        )
        page2 = self.authenticated_git_lab_manager.get_user_repositories(
            page=2, per_page=per_page
        )

        repos1 = page1["repositories"]  # list[dict]
        repos2 = page2["repositories"]  # list[dict]
        meta1 = page1["pagination_info"]
        meta2 = page2["pagination_info"]

        # Basic invariants
        assert len(repos1) <= per_page
        assert len(repos2) <= per_page
        assert meta1["current_page"] == 1
        assert meta2["current_page"] == 2

        # Independent verification with raw GitLab REST (NOT the manager)
        base_url = (
            self.git_lab_manager.base_url
            if hasattr(self, "git_lab_manager")
            else "http://localhost:8080"
        )
        headers = {"PRIVATE-TOKEN": gitlab_access_token}

        r1 = requests.get(
            f"{base_url}/api/v4/projects?membership=true&min_access_level=30&per_page={per_page}&page=1",
            headers=headers,
            timeout=30,
        )
        r2 = requests.get(
            f"{base_url}/api/v4/projects?membership=true&min_access_level=30&per_page={per_page}&page=2",
            headers=headers,
            timeout=30,
        )
        r1.raise_for_status()
        r2.raise_for_status()
        raw1 = r1.json()
        raw2 = r2.json()

        ids1 = {p["id"] for p in repos1}
        ids2 = {p["id"] for p in repos2}
        raw_ids1 = {p["id"] for p in raw1}
        raw_ids2 = {p["id"] for p in raw2}

        # SUT results must match raw page content for the same (page, per_page)
        assert ids1 == raw_ids1
        assert ids2 == raw_ids2

        # If SUT says there's a next page from page 1, page 2 must not be empty and must not overlap page 1
        if meta1["next_page"]:
            assert len(repos2) > 0
            assert meta1["next_page"] == 2
            assert meta2["prev_page"] == 1
            assert ids1.isdisjoint(ids2)
        else:
            assert len(repos2) == 0

        # Arithmetic correctness for total_pages
        expected_total_pages = (meta1["total_count"] + per_page - 1) // per_page
        assert meta1["total_pages"] == expected_total_pages

    def test_gitlab_create_delete_branch(self, gl_temp_project):
        (project, _cleanup) = gl_temp_project
        verifier = Gitlab(
            url="http://localhost:8080", private_token=gitlab_access_token
        )
        verifier.auth()
        v_proj = verifier.projects.get(project.id)

        # Create
        b = self.authenticated_git_lab_manager.create_branch(
            project_or_id=project,
            branch_name="br1",
            source_branch=None,
        )
        assert b["name"] == "br1"
        assert b["commit"]["id"]

        # Verify with raw client
        v_branch = v_proj.branches.get("br1")
        assert v_branch.name == "br1"

        # Delete
        res = self.authenticated_git_lab_manager.delete_branch(
            project_or_id=project,
            branch_name="br1",
        )
        assert res["deleted"] is True

        # Verify 404 with raw client
        with pytest.raises(GitlabGetError) as ge:
            v_proj.branches.get("br1")
        assert ge.value.response_code == 404

    def test_gitlab_commit_files(self, gl_temp_project):
        (project, _cleanup) = gl_temp_project
        verifier = Gitlab(
            url="http://localhost:8080", private_token=gitlab_access_token
        )
        verifier.auth()
        v_proj = verifier.projects.get(project.id)

        # Create working branch
        _ = self.authenticated_git_lab_manager.create_branch(
            project_or_id=project, branch_name="feat", source_branch=None
        )

        files = {
            "src/app.py": "print('hello from gitlab')\n",
            "README.md": "# Ephemeral GL\nThis is a test.\n",
        }
        msg = "feat: add two files (GL)"

        commit = self.authenticated_git_lab_manager.commit_files(
            project_or_id=project,
            branch="feat",
            files=files,
            commit_message=msg,
            author_name="CI Bot",
            author_email="ci@example.com",
        )
        assert commit["commit_id"]
        assert commit["files_count"] == 2

        # Verify with raw client
        v_commit = v_proj.commits.get(commit["commit_id"])
        assert msg in v_commit.message

        for path, content in files.items():
            f = v_proj.files.get(file_path=path, ref="feat")
            assert f.decode() == content

    def test_gitlab_push_single_file_create_update(self, gl_temp_project):
        (project, _cleanup) = gl_temp_project
        verifier = Gitlab(
            url="http://localhost:8080", private_token=gitlab_access_token
        )
        verifier.auth()
        v_proj = verifier.projects.get(project.id)
        branch = project.default_branch

        # Create
        r1 = self.authenticated_git_lab_manager.push_single_file(
            project_or_id=project,
            file_path="docs/hello.txt",
            content="hello world (GL)\n",
            commit_message="chore: add hello",
            branch=branch,
            update=False,
            author_name="CI Bot",
            author_email="ci@example.com",
        )
        assert r1.get("created") is True

        # Verify with raw client
        f1 = v_proj.files.get(file_path="docs/hello.txt", ref=branch)
        assert f1.decode() == "hello world (GL)\n"

        # Update
        r2 = self.authenticated_git_lab_manager.push_single_file(
            project_or_id=project,
            file_path="docs/hello.txt",
            content="hello world (GL updated)\n",
            commit_message="chore: update hello",
            branch=branch,
            update=True,
            author_name="CI Bot",
            author_email="ci@example.com",
        )
        assert r2.get("updated") is True

        # Verify update with raw client
        f2 = v_proj.files.get(file_path="docs/hello.txt", ref=branch)
        assert f2.decode() == "hello world (GL updated)\n"
