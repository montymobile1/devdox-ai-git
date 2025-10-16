import time
import uuid

import pytest
from github import (
    BadCredentialsException,
    Github,
    GithubException,
    UnknownObjectException,
)

from devdox_ai_git.exceptions.base_exceptions import DevDoxGitException
from devdox_ai_git.exceptions.exception_constants import (
    GIT_AUTH_FAILED,
    GIT_PROJECT_FETCH_FAILED,
    GIT_PROJECT_LANGUAGE_FETCH_FAILED,
)
from devdox_ai_git.git_managers import GitHubManager

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
github_email_account = "monty_testing_acc@outlook.com"
github_username = "montytestingacc"
github_access_token = "<A GITHUB USER ACCESS TOKEN>"
github_projects = {
    "prj1": {
        "full_name": "montytestingacc/HTMLPortfolioProject",
        "id": 1072987067,
        "project_languages": ["HTML", "JavaScript"],
    },
    "prj2": {
        "full_name": "montytestingacc/tictactoe",
        "id": 1073020304,
        "project_languages": ["Dart", "HTML", "Ruby", "Swift", "Java", "Kotlin"],
    },
    "prj3": {
        "full_name": "montytestingacc/cppcheck",
        "id": 1073022186,
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

class TestGitHubManager:
    manager = GitHubManager()

    def test_authenticate_should_authenticate_successfully_with_base_url(self):
        authenticated_git_hub_manager = self.manager.authenticate(github_access_token)

        assert authenticated_git_hub_manager

    def test_authenticate_should_raise_exception_when_access_token_invalid(self):
        with pytest.raises(DevDoxGitException) as exp:
            _ = self.manager.authenticate("<SOME INVALID ACCESS TOKEN>")

        assert exp.value.user_message == GIT_AUTH_FAILED
        assert isinstance(exp.value.__context__, BadCredentialsException)
        assert exp.value.__context__.status == 401

class TestAuthenticatedGitHubManager:
    authenticated_git_hub_manager = GitHubManager().authenticate(github_access_token)

    @pytest.fixture
    def gh_temp_repo(self):
        """
        Creates a temporary GitHub repo (auto_init=True so default branch exists),
        yields the Repository object and a cleanup function that safely deletes it.
        """
        repo = self.authenticated_git_hub_manager.create_repository(
            name=f"it-{uuid.uuid4().hex[:12]}-gh",
            description="Ephemeral test repo (GitHub)",
            visibility="private",
            auto_init=True,
        )

        def _cleanup():
            try:
                repo.delete()
            except Exception:
                pass

        try:
            yield repo, _cleanup
        finally:
            _cleanup()

    def test_get_project_should_succeed_with_full_name_or_id(self):
        project_meta = github_projects["prj1"]

        project_via_full_name = self.authenticated_git_hub_manager.get_project(
            project_meta["full_name"]
        )
        project_via_id = self.authenticated_git_hub_manager.get_project(
            project_meta["id"]
        )

        assert project_via_full_name.id == project_meta["id"]
        assert project_via_id.full_name == project_meta["full_name"]

    def test_get_project_should_raise_exception_when_project_does_not_exist(self):
        with pytest.raises(DevDoxGitException) as exp:
            _ = self.authenticated_git_hub_manager.get_project("<NON_EXISTENT_PROJECT>")

        assert exp.value.user_message == GIT_PROJECT_FETCH_FAILED
        assert isinstance(exp.value.__context__, UnknownObjectException)
        assert exp.value.__context__.status == 404

    def test_get_project_languages_should_return_with_full_name_or_id_or_repository(
        self,
    ):
        project_meta = github_projects["prj1"]

        project_languages_via_full_name = (
            self.authenticated_git_hub_manager.get_project_languages(
                project_meta["full_name"]
            )
        )

        project_languages_via_id = (
            self.authenticated_git_hub_manager.get_project_languages(project_meta["id"])
        )

        repository = self.authenticated_git_hub_manager.get_project(project_meta["id"])
        project_languages_via_repository = (
            self.authenticated_git_hub_manager.get_project_languages(repository)
        )

        assert all(
            n in project_meta["project_languages"]
            for n in project_languages_via_full_name
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
            _ = self.authenticated_git_hub_manager.get_project_languages(
                "<NON_EXISTENT_PROJECT>"
            )

        assert exp.value.user_message == GIT_PROJECT_LANGUAGE_FETCH_FAILED
        assert isinstance(exp.value.__context__, UnknownObjectException)
        assert exp.value.__context__.status == 404

    def test_get_user_should_return_when_user_exists(self):
        retrieved_user = self.authenticated_git_hub_manager.get_user()

        assert retrieved_user.login == github_username

    def test_get_user_repositories_returns_paginated_values(self):
        per_page = 2

        # Call SUT (manager) for page 1 and 2
        page1 = self.authenticated_git_hub_manager.get_user_repositories(
            page=1, per_page=per_page
        )
        page2 = self.authenticated_git_hub_manager.get_user_repositories(
            page=2, per_page=per_page
        )

        repos1 = page1["repositories"]
        repos2 = page2["repositories"]
        meta1 = page1["pagination_info"]
        meta2 = page2["pagination_info"]

        # Basic invariants
        assert len(repos1) <= per_page
        assert len(repos2) <= per_page
        assert meta1["current_page"] == 1
        assert meta2["current_page"] == 2

        # Independent verification with a raw PyGithub client (NOT the manager)
        raw = Github(github_access_token)
        raw.per_page = per_page  # force same page size
        raw_user = raw.get_user()
        raw_paginated = raw_user.get_repos(
            visibility="all",
            affiliation="owner,collaborator,organization_member",
            sort="updated",
            direction="desc",
        )
        raw_p1 = raw_paginated.get_page(0)
        raw_p2 = raw_paginated.get_page(1)

        # Page content must match raw client for the same (page, per_page)
        ids1 = {r.id for r in repos1}
        ids2 = {r.id for r in repos2}
        raw_ids1 = {r.id for r in raw_p1}
        raw_ids2 = {r.id for r in raw_p2}
        assert ids1 == raw_ids1
        assert ids2 == raw_ids2

        # If SUT says there's a next page from page 1, page 2 must not be empty and must not overlap page 1
        if meta1["has_next_page"]:
            assert len(repos2) > 0
            assert meta1["next_page"] == 2
            assert meta2["has_prev_page"] is True
            assert meta2["prev_page"] == 1
            assert ids1.isdisjoint(ids2)
        else:
            # No next page → second page should be empty
            assert len(repos2) == 0

        # Arithmetic correctness for total_pages given total_count and per_page
        expected_total_pages = (meta1["total_count"] + per_page - 1) // per_page
        assert meta1["total_pages"] == expected_total_pages

    def test_github_create_delete_repository(self):
        repo = None
        verifier = Github(github_access_token)  # independent raw client

        try:
            # Create
            repo = self.authenticated_git_hub_manager.create_repository(
                name="it-" + str(int(time.time())),
                description="ephemeral",
                visibility="private",
                auto_init=True,
            )
            assert repo.id is not None

            # Verify creation with raw client (not via manager)
            v_repo = verifier.get_repo(repo.id)
            assert v_repo.full_name == repo.full_name

            # Delete via manager API
            res = self.authenticated_git_hub_manager.delete_repository(repo)
            assert res["deleted"] is True

            # Verify gone with raw client
            with pytest.raises(UnknownObjectException) as ge:
                _ = verifier.get_repo(repo.id)
            assert ge.value.status == 404

            repo = None
        finally:
            if repo:
                try:
                    repo.delete()
                except Exception:
                    pass

    def test_github_create_delete_branch(self, gh_temp_repo):
        (repo, _cleanup) = gh_temp_repo
        verifier = Github(github_access_token)  # independent raw client
        v_repo = verifier.get_repo(repo.id)

        # Create branch from default (None -> default)
        created = self.authenticated_git_hub_manager.create_branch(
            repository=repo, branch_name="br1", source_branch=None
        )
        assert created["ref"].endswith("/br1")
        assert "sha" in created and created["sha"]

        # Verify existence with raw client
        v_branch = v_repo.get_branch("br1")
        assert v_branch.name == "br1"

        # Delete it
        res = self.authenticated_git_hub_manager.delete_branch(
            repository=repo, branch_name="br1"
        )
        assert res["deleted"] is True

        # Verify 404 on raw client
        with pytest.raises(GithubException) as ge:
            v_repo.get_branch("br1")
        assert ge.value.status == 404

    def test_github_commit_files(self, gh_temp_repo):
        (repo, _cleanup) = gh_temp_repo
        verifier = Github(github_access_token)  # independent raw client
        v_repo = verifier.get_repo(repo.id)

        # Create working branch
        _ = self.authenticated_git_hub_manager.create_branch(
            repository=repo, branch_name="feat", source_branch=None
        )

        files = {
            "src/app.py": "print('hello')\n",
            "README.md": "# Ephemeral\nThis is a test.\n",
        }
        commit_msg = "feat: add two files"

        commit = self.authenticated_git_hub_manager.commit_files(
            repository=repo,
            branch="feat",
            files=files,
            commit_message=commit_msg,
            author_name="CI Bot",
            author_email="ci@example.com",
        )

        assert commit["commit_sha"]
        assert commit["files_count"] == 2

        # Verify with raw client
        v_commit = v_repo.get_commit(commit["commit_sha"])
        assert commit_msg in v_commit.commit.message

        for path, content in files.items():
            blob = v_repo.get_contents(path, ref="feat")
            assert blob.decoded_content.decode("utf-8") == content

    def test_github_push_single_file_create_update(self, gh_temp_repo):
        (repo, _cleanup) = gh_temp_repo
        verifier = Github(github_access_token)  # independent raw client
        v_repo = verifier.get_repo(repo.id)
        branch = repo.default_branch

        # Create file
        r1 = self.authenticated_git_hub_manager.push_single_file(
            repository=repo,
            file_path="docs/hello.txt",
            content="hello world\n",
            commit_message="chore: add hello.txt",
            branch=branch,
            update=False,
        )
        assert r1["file_path"] == "docs/hello.txt"

        # Verify create with raw client
        blob1 = v_repo.get_contents("docs/hello.txt", ref=branch)
        assert blob1.decoded_content.decode("utf-8") == "hello world\n"

        # Update file
        r2 = self.authenticated_git_hub_manager.push_single_file(
            repository=repo,
            file_path="docs/hello.txt",
            content="hello world (updated)\n",
            commit_message="chore: update hello.txt",
            branch=branch,
            update=True,
        )
        assert r2["file_path"] == "docs/hello.txt"

        # Verify update with raw client
        blob2 = v_repo.get_contents("docs/hello.txt", ref=branch)
        assert blob2.decoded_content.decode("utf-8") == "hello world (updated)\n"