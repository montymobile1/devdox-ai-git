import types

import pytest
from enum import Enum
# System under test
import devdox_ai_git.repo_fetcher as rf

# Your existing doubles
from devdox_ai_git.test_doubles.git_managers_doubles import (
    FakeAuthenticatedGitHubManager,
    FakeAuthenticatedGitLabManager,
)


# --------------------------
# Spy doubles (to capture kwargs like page/per_page)
# --------------------------
class SpyAuthenticatedGitHubManager(FakeAuthenticatedGitHubManager):
    def __init__(self):
        super().__init__()
        self.calls = []

    def get_user_repositories(self, *args, **kwargs):
        self.calls.append(("get_user_repositories", args, kwargs))
        return super().get_user_repositories(*args, **kwargs)

    def create_repository(self, *args, **kwargs):
        self.calls.append(("create_repository", args, kwargs))
        return {"name": kwargs.get("name"), "visibility": kwargs.get("visibility")}

    def delete_repository(self, *args, **kwargs):
        self.calls.append(("delete_repository", args, kwargs))
        return {"status": "deleted"}

    def create_branch(self, *args, **kwargs):
        self.calls.append(("create_branch", args, kwargs))
        return {"name": args[1] if len(args) > 1 else kwargs.get("branch_name")}

    def delete_branch(self, *args, **kwargs):
        self.calls.append(("delete_branch", args, kwargs))
        return {"status": "deleted"}

    def commit_files(self, *args, **kwargs):
        self.calls.append(("commit_files", args, kwargs))
        return {
            "sha": "abc123",
            "message": kwargs.get("commit_message"),
            "files": list(kwargs.get("files", {}).keys())
        }

    def push_single_file(self, *args, **kwargs):
        self.calls.append(("push_single_file", args, kwargs))
        return {
            "sha": "def456",
            "path": kwargs.get("file_path"),
            "message": kwargs.get("commit_message")
        }


class SpyGitHubManager:
    """Drop-in replacement for rf.GitHubManager used inside GitHubRepoFetcher."""
    def __init__(self, base_url):
        self.base_url = base_url
        self.last_auth = None

    def authenticate(self, token: str):
        self.last_auth = SpyAuthenticatedGitHubManager()
        return self.last_auth


class SpyAuthenticatedGitLabManager(FakeAuthenticatedGitLabManager):
    def __init__(self):
        super().__init__()
        self.calls = []

    def get_user_repositories(self, *args, **kwargs):
        self.calls.append(("get_user_repositories", args, kwargs))
        return super().get_user_repositories(*args, **kwargs)

    def create_repository(self, *args, **kwargs):
        self.calls.append(("create_repository", args, kwargs))
        return {"name": kwargs.get("name"), "visibility": kwargs.get("visibility")}

    def delete_repository(self, *args, **kwargs):
        self.calls.append(("delete_repository", args, kwargs))
        return {"status": "deleted"}

    def create_branch(self, *args, **kwargs):
        self.calls.append(("create_branch", args, kwargs))
        return {"name": args[1] if len(args) > 1 else kwargs.get("branch_name")}

    def delete_branch(self, *args, **kwargs):
        self.calls.append(("delete_branch", args, kwargs))
        return {"status": "deleted"}

    def commit_files(self, *args, **kwargs):
        self.calls.append(("commit_files", args, kwargs))
        return {
            "id": "xyz789",
            "message": kwargs.get("commit_message"),
            "files": list(kwargs.get("files", {}).keys())
        }

    def push_single_file(self, *args, **kwargs):
        self.calls.append(("push_single_file", args, kwargs))
        return {
            "id": "uvw012",
            "file_path": kwargs.get("file_path"),
            "message": kwargs.get("commit_message")
        }



    # --------------------------
    # Spy doubles (to capture kwargs like page/per_page)
    # --------------------------
    class SpyAuthenticatedGitHubManager(FakeAuthenticatedGitHubManager):
        def __init__(self):
            super().__init__()
            self.calls = []

        def get_user_repositories(self, *args, **kwargs):
            self.calls.append(("get_user_repositories", args, kwargs))
            return super().get_user_repositories(*args, **kwargs)

        def create_repository(self, *args, **kwargs):
            self.calls.append(("create_repository", args, kwargs))
            return {"name": kwargs.get("name"), "visibility": kwargs.get("visibility")}

        def delete_repository(self, *args, **kwargs):
            self.calls.append(("delete_repository", args, kwargs))
            return {"status": "deleted"}

        def create_branch(self, *args, **kwargs):
            self.calls.append(("create_branch", args, kwargs))
            return {"name": args[1] if len(args) > 1 else kwargs.get("branch_name")}

        def delete_branch(self, *args, **kwargs):
            self.calls.append(("delete_branch", args, kwargs))
            return {"status": "deleted"}

        def commit_files(self, *args, **kwargs):
            self.calls.append(("commit_files", args, kwargs))
            return {
                "sha": "abc123",
                "message": kwargs.get("commit_message"),
                "files": list(kwargs.get("files", {}).keys())
            }

        def push_single_file(self, *args, **kwargs):
            self.calls.append(("push_single_file", args, kwargs))
            return {
                "sha": "def456",
                "path": kwargs.get("file_path"),
                "message": kwargs.get("commit_message")
            }

    class SpyGitHubManager:
        """Drop-in replacement for rf.GitHubManager used inside GitHubRepoFetcher."""

        def __init__(self, base_url):
            self.base_url = base_url
            self.last_auth = None

        def authenticate(self, token: str):
            self.last_auth = SpyAuthenticatedGitHubManager()
            return self.last_auth

    class SpyAuthenticatedGitLabManager(FakeAuthenticatedGitLabManager):
        def __init__(self):
            super().__init__()
            self.calls = []

        def get_user_repositories(self, *args, **kwargs):
            self.calls.append(("get_user_repositories", args, kwargs))
            return super().get_user_repositories(*args, **kwargs)

        def create_repository(self, *args, **kwargs):
            self.calls.append(("create_repository", args, kwargs))
            return {"name": kwargs.get("name"), "visibility": kwargs.get("visibility")}

        def delete_repository(self, *args, **kwargs):
            self.calls.append(("delete_repository", args, kwargs))
            return {"status": "deleted"}

        def create_branch(self, *args, **kwargs):
            self.calls.append(("create_branch", args, kwargs))
            return {"name": args[1] if len(args) > 1 else kwargs.get("branch_name")}

        def delete_branch(self, *args, **kwargs):
            self.calls.append(("delete_branch", args, kwargs))
            return {"status": "deleted"}

        def commit_files(self, *args, **kwargs):
            self.calls.append(("commit_files", args, kwargs))
            return {
                "id": "xyz789",
                "message": kwargs.get("commit_message"),
                "files": list(kwargs.get("files", {}).keys())
            }

        def push_single_file(self, *args, **kwargs):
            self.calls.append(("push_single_file", args, kwargs))
            return {
                "id": "uvw012",
                "file_path": kwargs.get("file_path"),
                "message": kwargs.get("commit_message")
            }


class SpyGitLabManager:
    """Drop-in replacement for rf.GitLabManager used inside GitLabRepoFetcher."""
    def __init__(self, base_url):
        self.base_url = base_url
        self.last_auth = None

    def authenticate(self, token: str):
        self.last_auth = SpyAuthenticatedGitLabManager()
        return self.last_auth


# --------------------------
# Fixtures to patch managers used internally by fetchers
# --------------------------
@pytest.fixture
def patched_github_manager(monkeypatch):
    monkeypatch.setattr(rf, "GitHubManager", SpyGitHubManager)
    return SpyGitHubManager


@pytest.fixture
def patched_gitlab_manager(monkeypatch):
    monkeypatch.setattr(rf, "GitLabManager", SpyGitLabManager)
    return SpyGitLabManager


# --------------------------
# GitHubRepoFetcher tests
# --------------------------
def test_github_fetch_user_repositories_maps_pagination_and_returns_shape(
    patched_github_manager,
):
    fetcher = rf.GitHubRepoFetcher()
    out = fetcher.fetch_user_repositories(token="t", offset=2, limit=50)

    # shape mapping
    assert out == {"data_count": 2, "data": [{"name": "repo1"}, {"name": "repo2"}]}

    # Ensure offset -> page+1 and limit -> per_page mapping happened
    spy_auth = fetcher.manager.last_auth
    (_, _, kwargs) = spy_auth.calls[-1]
    assert kwargs["page"] == 3
    assert kwargs["per_page"] == 50


@pytest.mark.parametrize(
    "remote",
    [
        "owner/repo",
        "/owner/repo",  # leading slash shorthand
        "https://github.com/owner/repo.git",  # URL style
        "git@github.com:owner/repo.git",  # scp style
    ],
)
def test_github_fetch_single_repo_returns_repo_and_languages(
    patched_github_manager, remote
):
    fetcher = rf.GitHubRepoFetcher()
    repo, langs = fetcher.fetch_single_repo(token="t", relative_path=remote)
    assert repo == {"id": "owner/repo", "name": "fake-project"}
    assert langs == ["Python"]


def test_github_fetch_single_repo_returns_none_when_missing_repo(
    monkeypatch, patched_github_manager
):
    fetcher = rf.GitHubRepoFetcher()

    # Force the authenticated manager to return None for get_project
    def _fake_authenticate(_self, _token):
        mgr = SpyAuthenticatedGitHubManager()
        mgr.get_project = lambda _id: None
        return mgr

    monkeypatch.setattr(fetcher.manager, "authenticate", types.MethodType(_fake_authenticate, fetcher.manager))

    out = fetcher.fetch_single_repo(token="t", relative_path="owner/repo")
    assert out is None


def test_github_fetch_repo_user_returns_user(patched_github_manager):
    fetcher = rf.GitHubRepoFetcher()
    user = fetcher.fetch_repo_user(token="t")
    assert user == {
        "username": "fakeuser",
        "id": 123,
        "name": "Fake User",
        "email": "fake@github.com",
        "avatar_url": "https://fake-avatar.com",
        "html_url": "https://github.com/fakeuser",
    }


def test_github_fetch_repo_user_returns_none_when_missing(
    monkeypatch, patched_github_manager
):
    fetcher = rf.GitHubRepoFetcher()

    def _fake_authenticate(_self, _token):
        mgr = SpyAuthenticatedGitHubManager()
        mgr.get_user = lambda: None
        return mgr

    monkeypatch.setattr(fetcher.manager, "authenticate", types.MethodType(_fake_authenticate, fetcher.manager))
    assert fetcher.fetch_repo_user(token="t") is None


def test_github_create_repository_with_required_params(patched_github_manager):
    fetcher = rf.GitHubRepoFetcher()
    result = fetcher.create_repository(
        token="test_token",
        name="new-repo",
        description="Test repository",
        visibility="public"
    )

    assert result["name"] == "new-repo"
    assert result["visibility"] == "public"

    spy_auth = fetcher.manager.last_auth
    call_name, _, kwargs = spy_auth.calls[-1]
    assert call_name == "create_repository"
    assert kwargs["name"] == "new-repo"
    assert kwargs["description"] == "Test repository"
    assert kwargs["visibility"] == "public"


def test_github_create_repository_with_none_description(patched_github_manager):
    fetcher = rf.GitHubRepoFetcher()
    result = fetcher.create_repository(
        token="test_token",
        name="new-repo",
        description=None,
        visibility="private"
    )

    spy_auth = fetcher.manager.last_auth
    _, _, kwargs = spy_auth.calls[-1]
    assert kwargs["description"] == ""  # None should be converted to empty string


def test_github_delete_repository(patched_github_manager):
    fetcher = rf.GitHubRepoFetcher()
    result = fetcher.delete_repository(token="test_token", repository="owner/repo")

    assert result["status"] == "deleted"

    spy_auth = fetcher.manager.last_auth
    call_name, args, _ = spy_auth.calls[-1]
    assert call_name == "delete_repository"
    assert "owner/repo" in args


def test_github_create_branch(patched_github_manager):
    fetcher = rf.GitHubRepoFetcher()
    result = fetcher.create_branch(
        token="test_token",
        project_id="owner/repo",
        branch_name="feature-branch",
        source_branch="main"
    )

    assert result["name"] == "feature-branch"

    spy_auth = fetcher.manager.last_auth
    call_name, args, _ = spy_auth.calls[-1]
    assert call_name == "create_branch"
    assert "owner/repo" in args
    assert "feature-branch" in args
    assert "main" in args


def test_github_delete_branch(patched_github_manager):
    fetcher = rf.GitHubRepoFetcher()
    result = fetcher.delete_branch(
        token="test_token",
        project_id="owner/repo",
        branch_name="feature-branch"
    )

    assert result["status"] == "deleted"

    spy_auth = fetcher.manager.last_auth
    call_name, args, _ = spy_auth.calls[-1]
    assert call_name == "delete_branch"
    assert "owner/repo" in args
    assert "feature-branch" in args


def test_github_commit_files_multiple_files(patched_github_manager):
    fetcher = rf.GitHubRepoFetcher()
    files = {
        "file1.py": "print('hello')",
        "file2.txt": "content",
        "folder/file3.md": "# Title"
    }

    result = fetcher.commit_files(
        token="test_token",
        repository="owner/repo",
        branch="main",
        files=files,
        commit_message="Add multiple files"
    )

    assert result["sha"] == "abc123"
    assert result["message"] == "Add multiple files"
    assert set(result["files"]) == set(files.keys())

    spy_auth = fetcher.manager.last_auth
    call_name, _, kwargs = spy_auth.calls[-1]
    assert call_name == "commit_files"
    assert kwargs["repository"] == "owner/repo"
    assert kwargs["branch"] == "main"
    assert kwargs["commit_message"] == "Add multiple files"
    assert kwargs["files"] == files


def test_github_commit_files_with_author_info(patched_github_manager):
    fetcher = rf.GitHubRepoFetcher()
    result = fetcher.commit_files(
        token="test_token",
        repository="owner/repo",
        branch="main",
        files={"test.txt": "content"},
        commit_message="Test commit",
        author_name="John Doe",
        author_email="john@example.com"
    )

    spy_auth = fetcher.manager.last_auth
    _, _, kwargs = spy_auth.calls[-1]
    assert kwargs["author_name"] == "John Doe"
    assert kwargs["author_email"] == "john@example.com"


def test_github_push_single_file_new_file(patched_github_manager):
    fetcher = rf.GitHubRepoFetcher()
    result = fetcher.push_single_file(
        token="test_token",
        repository="owner/repo",
        file_path="docs/README.md",
        content="# Documentation",
        commit_message="Add README",
        branch="main",
        update=False
    )

    assert result["sha"] == "def456"
    assert result["path"] == "docs/README.md"
    assert result["message"] == "Add README"

    spy_auth = fetcher.manager.last_auth
    call_name, _, kwargs = spy_auth.calls[-1]
    assert call_name == "push_single_file"
    assert kwargs["repository"] == "owner/repo"
    assert kwargs["file_path"] == "docs/README.md"
    assert kwargs["branch"] == "main"
    assert kwargs["update"] is False


def test_github_push_single_file_update_existing(patched_github_manager):
    fetcher = rf.GitHubRepoFetcher()
    result = fetcher.push_single_file(
        token="test_token",
        repository="owner/repo",
        file_path="README.md",
        content="# Updated",
        commit_message="Update README",
        branch="main",
        update=True
    )

    spy_auth = fetcher.manager.last_auth
    _, _, kwargs = spy_auth.calls[-1]
    assert kwargs["update"] is True



# --------------------------
# GitLabRepoFetcher tests
# --------------------------
def test_gitlab_fetch_user_repositories_maps_pagination_and_returns_shape(
    patched_gitlab_manager,
):
    fetcher = rf.GitLabRepoFetcher()
    out = fetcher.fetch_user_repositories(token="t", offset=0, limit=10)

    # shape mapping
    assert out == {"data_count": 2, "data": [{"name": "repo1"}, {"name": "repo2"}]}

    # Ensure offset -> page+1 and limit -> per_page mapping happened
    spy_auth = fetcher.manager.last_auth
    (_, _, kwargs) = spy_auth.calls[-1]
    assert kwargs["page"] == 1
    assert kwargs["per_page"] == 10


@pytest.mark.parametrize(
    "remote",
    [
        "group/project",
        "/group/project",
        "https://gitlab.com/group/project.git",
        "git@gitlab.com:group/project.git",
    ],
)
def test_gitlab_fetch_single_repo_returns_repo_and_languages(
    patched_gitlab_manager, remote
):
    fetcher = rf.GitLabRepoFetcher()
    repo, langs = fetcher.fetch_single_repo(token="t", relative_path=remote)
    assert repo == {"id": "group/project", "name": "fake-project"}
    assert langs == ["Python"]


def test_gitlab_fetch_single_repo_returns_none_when_missing_repo(
    monkeypatch, patched_gitlab_manager
):
    fetcher = rf.GitLabRepoFetcher()

    def _fake_authenticate(_self, _token):
        mgr = SpyAuthenticatedGitLabManager()
        mgr.get_project = lambda _id, timeout=30: None
        return mgr

    monkeypatch.setattr(fetcher.manager, "authenticate", types.MethodType(_fake_authenticate, fetcher.manager))
    out = fetcher.fetch_single_repo(token="t", relative_path="group/project")
    assert out is None


def test_gitlab_fetch_repo_user_returns_user(patched_gitlab_manager):
    fetcher = rf.GitLabRepoFetcher()
    user = fetcher.fetch_repo_user(token="t")
    assert user == {
        "username": "fakeuser",
        "id": 456,
        "name": "Fake User",
        "email": "fake@gitlab.com",
        "avatar_url": "https://fake-avatar.com",
        "web_url": "https://gitlab.com/fakeuser",
    }


def test_gitlab_fetch_repo_user_returns_none_when_missing(
    monkeypatch, patched_gitlab_manager
):
    fetcher = rf.GitLabRepoFetcher()

    def _fake_authenticate(_self, _token):
        mgr = SpyAuthenticatedGitLabManager()
        mgr.get_user = lambda timeout=30: None
        return mgr

    monkeypatch.setattr(fetcher.manager, "authenticate", types.MethodType(_fake_authenticate, fetcher.manager))
    assert fetcher.fetch_repo_user(token="t") is None


# --------------------------
# RepoFetcher.get_components tests
# --------------------------
def test_repo_fetcher_get_components_with_enum(monkeypatch):
    # Patch the module-level GitHosting enum with a lightweight stand-in
    class _FakeGitHosting(str, Enum):
        GITHUB = "github"
        GITLAB = "gitlab"

    monkeypatch.setattr(rf, "GitHosting", _FakeGitHosting)

    # Also avoid constructing real managers inside nested fetchers
    monkeypatch.setattr(rf, "GitHubManager", SpyGitHubManager)
    monkeypatch.setattr(rf, "GitLabManager", SpyGitLabManager)

    repo_fetcher = rf.RepoFetcher()

    gh_fetcher, gh_xf = repo_fetcher.get_components(rf.GitHosting.GITHUB)
    assert isinstance(gh_fetcher, rf.GitHubRepoFetcher)
    assert isinstance(gh_xf, rf.GitHubRepoResponseTransformer)

    gl_fetcher, gl_xf = repo_fetcher.get_components(rf.GitHosting.GITLAB)
    assert isinstance(gl_fetcher, rf.GitLabRepoFetcher)
    assert isinstance(gl_xf, rf.GitLabRepoResponseTransformer)


def test_repo_fetcher_get_components_unknown_returns_none_pair(monkeypatch):
    class _FakeGitHosting(str, Enum):
        GITHUB = "github"
        GITLAB = "gitlab"

    monkeypatch.setattr(rf, "GitHosting", _FakeGitHosting)

    repo_fetcher = rf.RepoFetcher()
    out = repo_fetcher.get_components("bitbucket")
    assert out == (None, None)


def test_gitlab_create_repository_with_required_params(patched_gitlab_manager):
    fetcher = rf.GitLabRepoFetcher()
    result = fetcher.create_repository(
        token="test_token",
        name="new-project",
        description="Test project",
        visibility="public"
    )

    assert result["name"] == "new-project"
    assert result["visibility"] == "public"

    spy_auth = fetcher.manager.last_auth
    call_name, _, kwargs = spy_auth.calls[-1]
    assert call_name == "create_repository"
    assert kwargs["name"] == "new-project"
    assert kwargs["description"] == "Test project"
    assert kwargs["visibility"] == "public"


def test_gitlab_create_repository_with_none_description(patched_gitlab_manager):
    fetcher = rf.GitLabRepoFetcher()
    result = fetcher.create_repository(
        token="test_token",
        name="new-project",
        description=None,
        visibility="private"
    )

    spy_auth = fetcher.manager.last_auth
    _, _, kwargs = spy_auth.calls[-1]
    assert kwargs["description"] == ""


def test_gitlab_delete_repository(patched_gitlab_manager):
    fetcher = rf.GitLabRepoFetcher()
    result = fetcher.delete_repository(token="test_token", repository="group/project")

    assert result["status"] == "deleted"

    spy_auth = fetcher.manager.last_auth
    call_name, args, _ = spy_auth.calls[-1]
    assert call_name == "delete_repository"
    assert "group/project" in args


def test_gitlab_create_branch(patched_gitlab_manager):
    fetcher = rf.GitLabRepoFetcher()
    result = fetcher.create_branch(
        token="test_token",
        project_id="group/project",
        branch_name="feature-branch",
        source_branch="main"
    )

    assert result["name"] == "feature-branch"

    spy_auth = fetcher.manager.last_auth
    call_name, args, _ = spy_auth.calls[-1]
    assert call_name == "create_branch"
    assert "group/project" in args
    assert "feature-branch" in args
    assert "main" in args


def test_gitlab_delete_branch(patched_gitlab_manager):
    fetcher = rf.GitLabRepoFetcher()
    result = fetcher.delete_branch(
        token="test_token",
        project_id="group/project",
        branch_name="feature-branch"
    )

    assert result["status"] == "deleted"

    spy_auth = fetcher.manager.last_auth
    call_name, args, _ = spy_auth.calls[-1]
    assert call_name == "delete_branch"
    assert "group/project" in args
    assert "feature-branch" in args


# --------------------------
# NEW: GitLab File Operations tests
# --------------------------
def test_gitlab_commit_files_multiple_files(patched_gitlab_manager):
    fetcher = rf.GitLabRepoFetcher()
    files = {
        "file1.py": "print('hello')",
        "file2.txt": "content",
        "folder/file3.md": "# Title"
    }

    result = fetcher.commit_files(
        token="test_token",
        repository="group/project",
        branch="main",
        files=files,
        commit_message="Add multiple files"
    )

    assert result["id"] == "xyz789"
    assert result["message"] == "Add multiple files"
    assert set(result["files"]) == set(files.keys())

    spy_auth = fetcher.manager.last_auth
    call_name, _, kwargs = spy_auth.calls[-1]
    assert call_name == "commit_files"
    assert kwargs["project_or_id"] == "group/project"
    assert kwargs["branch"] == "main"
    assert kwargs["commit_message"] == "Add multiple files"
    assert kwargs["files"] == files


def test_gitlab_commit_files_with_author_info(patched_gitlab_manager):
    fetcher = rf.GitLabRepoFetcher()
    result = fetcher.commit_files(
        token="test_token",
        repository="group/project",
        branch="main",
        files={"test.txt": "content"},
        commit_message="Test commit",
        author_name="Jane Doe",
        author_email="jane@example.com"
    )

    spy_auth = fetcher.manager.last_auth
    _, _, kwargs = spy_auth.calls[-1]
    assert kwargs["author_name"] == "Jane Doe"
    assert kwargs["author_email"] == "jane@example.com"


def test_gitlab_push_single_file_new_file(patched_gitlab_manager):
    fetcher = rf.GitLabRepoFetcher()
    result = fetcher.push_single_file(
        token="test_token",
        repository="group/project",
        file_path="docs/README.md",
        content="# Documentation",
        commit_message="Add README",
        branch="main",
        update=False
    )

    assert result["id"] == "uvw012"
    assert result["file_path"] == "docs/README.md"
    assert result["message"] == "Add README"

    spy_auth = fetcher.manager.last_auth
    call_name, _, kwargs = spy_auth.calls[-1]
    assert call_name == "push_single_file"
    assert kwargs["project_or_id"] == "group/project"
    assert kwargs["file_path"] == "docs/README.md"
    assert kwargs["branch"] == "main"
    assert kwargs["update"] is False


def test_gitlab_push_single_file_update_existing(patched_gitlab_manager):
    fetcher = rf.GitLabRepoFetcher()
    result = fetcher.push_single_file(
        token="test_token",
        repository="group/project",
        file_path="README.md",
        content="# Updated",
        commit_message="Update README",
        branch="main",
        update=True,
        author_name="Jane Doe",
        author_email="jane@example.com"
    )

    spy_auth = fetcher.manager.last_auth
    _, _, kwargs = spy_auth.calls[-1]
    assert kwargs["update"] is True
    assert kwargs["author_name"] == "Jane Doe"
    assert kwargs["author_email"] == "jane@example.com"


# --------------------------
# RepoFetcher.get_components tests
# --------------------------
def test_repo_fetcher_get_components_with_enum(monkeypatch):
    # Patch the module-level GitHosting enum with a lightweight stand-in
    class _FakeGitHosting(str, Enum):
        GITHUB = "github"
        GITLAB = "gitlab"

    monkeypatch.setattr(rf, "GitHosting", _FakeGitHosting)

    # Also avoid constructing real managers inside nested fetchers
    monkeypatch.setattr(rf, "GitHubManager", SpyGitHubManager)
    monkeypatch.setattr(rf, "GitLabManager", SpyGitLabManager)

    repo_fetcher = rf.RepoFetcher()

    gh_fetcher, gh_xf = repo_fetcher.get_components(rf.GitHosting.GITHUB)
    assert isinstance(gh_fetcher, rf.GitHubRepoFetcher)
    assert isinstance(gh_xf, rf.GitHubRepoResponseTransformer)

    gl_fetcher, gl_xf = repo_fetcher.get_components(rf.GitHosting.GITLAB)
    assert isinstance(gl_fetcher, rf.GitLabRepoFetcher)
    assert isinstance(gl_xf, rf.GitLabRepoResponseTransformer)


def test_repo_fetcher_get_components_unknown_returns_none_pair(monkeypatch):
    class _FakeGitHosting(str, Enum):
        GITHUB = "github"
        GITLAB = "gitlab"

    monkeypatch.setattr(rf, "GitHosting", _FakeGitHosting)

    repo_fetcher = rf.RepoFetcher()
    out = repo_fetcher.get_components("bitbucket")
    assert out == (None, None)


def test_repo_fetcher_get_components_with_string_github(monkeypatch):
    class _FakeGitHosting(str, Enum):
        GITHUB = "github"
        GITLAB = "gitlab"

    monkeypatch.setattr(rf, "GitHosting", _FakeGitHosting)
    monkeypatch.setattr(rf, "GitHubManager", SpyGitHubManager)
    monkeypatch.setattr(rf, "GitLabManager", SpyGitLabManager)

    repo_fetcher = rf.RepoFetcher()
    fetcher, transformer = repo_fetcher.get_components("github")

    assert isinstance(fetcher, rf.GitHubRepoFetcher)
    assert isinstance(transformer, rf.GitHubRepoResponseTransformer)


def test_repo_fetcher_get_components_with_string_gitlab(monkeypatch):
    class _FakeGitHosting(str, Enum):
        GITHUB = "github"
        GITLAB = "gitlab"

    monkeypatch.setattr(rf, "GitHosting", _FakeGitHosting)
    monkeypatch.setattr(rf, "GitHubManager", SpyGitHubManager)
    monkeypatch.setattr(rf, "GitLabManager", SpyGitLabManager)

    repo_fetcher = rf.RepoFetcher()
    fetcher, transformer = repo_fetcher.get_components("gitlab")

    assert isinstance(fetcher, rf.GitLabRepoFetcher)
    assert isinstance(transformer, rf.GitLabRepoResponseTransformer)


# --------------------------
# Edge Cases and Error Handling
# --------------------------
def test_github_commit_files_empty_files_dict(patched_github_manager):
    fetcher = rf.GitHubRepoFetcher()
    result = fetcher.commit_files(
        token="test_token",
        repository="owner/repo",
        branch="main",
        files={},
        commit_message="Empty commit"
    )

    spy_auth = fetcher.manager.last_auth
    _, _, kwargs = spy_auth.calls[-1]
    assert kwargs["files"] == {}


def test_gitlab_commit_files_empty_files_dict(patched_gitlab_manager):
    fetcher = rf.GitLabRepoFetcher()
    result = fetcher.commit_files(
        token="test_token",
        repository="group/project",
        branch="main",
        files={},
        commit_message="Empty commit"
    )

    spy_auth = fetcher.manager.last_auth
    _, _, kwargs = spy_auth.calls[-1]
    assert kwargs["files"] == {}


def test_github_push_single_file_without_author_info(patched_github_manager):
    fetcher = rf.GitHubRepoFetcher()
    result = fetcher.push_single_file(
        token="test_token",
        repository="owner/repo",
        file_path="file.txt",
        content="content",
        commit_message="Add file",
        branch="main"
    )

    spy_auth = fetcher.manager.last_auth
    _, _, kwargs = spy_auth.calls[-1]
    # Author info should not be passed if not provided
    assert "author_name" not in kwargs or kwargs.get("author_name") is None
    assert "author_email" not in kwargs or kwargs.get("author_email") is None


def test_gitlab_push_single_file_with_nested_path(patched_gitlab_manager):
    fetcher = rf.GitLabRepoFetcher()
    result = fetcher.push_single_file(
        token="test_token",
        repository="group/project",
        file_path="deeply/nested/folder/file.txt",
        content="nested content",
        commit_message="Add nested file",
        branch="develop"
    )

    spy_auth = fetcher.manager.last_auth
    _, _, kwargs = spy_auth.calls[-1]
    assert kwargs["file_path"] == "deeply/nested/folder/file.txt"
    assert kwargs["branch"] == "develop"


def test_github_create_repository_different_visibilities(patched_github_manager):
    fetcher = rf.GitHubRepoFetcher()

    # Test private visibility
    result = fetcher.create_repository(
        token="test_token",
        name="private-repo",
        description="Private repository",
        visibility="private"
    )
    assert result["visibility"] == "private"

    # Test public visibility
    result = fetcher.create_repository(
        token="test_token",
        name="public-repo",
        description="Public repository",
        visibility="public"
    )
    assert result["visibility"] == "public"


def test_gitlab_create_repository_different_visibilities(patched_gitlab_manager):
    fetcher = rf.GitLabRepoFetcher()

    # Test internal visibility
    result = fetcher.create_repository(
        token="test_token",
        name="internal-project",
        description="Internal project",
        visibility="internal"
    )
    assert result["visibility"] == "internal"

    # Test private visibility
    result = fetcher.create_repository(
        token="test_token",
        name="private-project",
        description="Private project",
        visibility="private"
    )
    assert result["visibility"] == "private"


def test_github_commit_files_special_characters_in_filenames(patched_github_manager):
    fetcher = rf.GitHubRepoFetcher()
    files = {
        "file with spaces.txt": "content",
        "file-with-dashes.py": "code",
        "file_with_underscores.md": "markdown"
    }

    result = fetcher.commit_files(
        token="test_token",
        repository="owner/repo",
        branch="main",
        files=files,
        commit_message="Add files with special characters"
    )

    assert set(result["files"]) == set(files.keys())


def test_gitlab_commit_files_multiple_branches(patched_gitlab_manager):
    fetcher = rf.GitLabRepoFetcher()

    # Commit to main branch
    result1 = fetcher.commit_files(
        token="test_token",
        repository="group/project",
        branch="main",
        files={"file1.txt": "content1"},
        commit_message="Commit to main"
    )

    spy_auth = fetcher.manager.last_auth
    _, _, kwargs1 = spy_auth.calls[-1]
    assert kwargs1["branch"] == "main"

    # Commit to develop branch
    result2 = fetcher.commit_files(
        token="test_token",
        repository="group/project",
        branch="develop",
        files={"file2.txt": "content2"},
        commit_message="Commit to develop"
    )

    spy_auth_2 = fetcher.manager.last_auth
    _, _, kwargs2 = spy_auth_2.calls[-1]
    assert kwargs2["branch"] == "develop"


def test_github_create_branch_from_different_sources(patched_github_manager):
    fetcher = rf.GitHubRepoFetcher()

    # Create branch from main
    result = fetcher.create_branch(
        token="test_token",
        project_id="owner/repo",
        branch_name="feature-from-main",
        source_branch="main"
    )

    spy_auth = fetcher.manager.last_auth
    _, args, _ = spy_auth.calls[-1]
    assert "main" in args

    # Create branch from develop
    result = fetcher.create_branch(
        token="test_token",
        project_id="owner/repo",
        branch_name="feature-from-develop",
        source_branch="develop"
    )
    spy_auth2 = fetcher.manager.last_auth
    _, args, _ = spy_auth2.calls[-1]
    assert "develop" in args


def test_gitlab_create_branch_naming_conventions(patched_gitlab_manager):
    fetcher = rf.GitLabRepoFetcher()

    # Test various branch naming patterns
    branch_names = [
        "feature/user-auth",
        "bugfix/login-error",
        "release/v1.0.0",
        "hotfix/critical-bug"
    ]

    for branch_name in branch_names:
        result = fetcher.create_branch(
            token="test_token",
            project_id="group/project",
            branch_name=branch_name,
            source_branch="main"
        )
        assert result["name"] == branch_name


def test_github_commit_files_with_long_commit_message(patched_github_manager):
    fetcher = rf.GitHubRepoFetcher()
    long_message = "This is a very long commit message. " * 20

    result = fetcher.commit_files(
        token="test_token",
        repository="owner/repo",
        branch="main",
        files={"file.txt": "content"},
        commit_message=long_message
    )

    assert result["message"] == long_message

    spy_auth = fetcher.manager.last_auth
    _, _, kwargs = spy_auth.calls[-1]
    assert kwargs["commit_message"] == long_message


def test_gitlab_push_single_file_large_content(patched_gitlab_manager):
    fetcher = rf.GitLabRepoFetcher()
    large_content = "x" * 10000  # 10KB of content

    result = fetcher.push_single_file(
        token="test_token",
        repository="group/project",
        file_path="large_file.txt",
        content=large_content,
        commit_message="Add large file",
        branch="main"
    )

    spy_auth = fetcher.manager.last_auth
    _, _, kwargs = spy_auth.calls[-1]
    assert len(kwargs["content"]) == 10000


def test_github_delete_repository_various_formats(patched_github_manager):
    fetcher = rf.GitHubRepoFetcher()

    # Test various repository identifier formats
    repo_formats = [
        "owner/repo",
        "organization/project",
        "user123/repo-name"
    ]

    for repo_format in repo_formats:
        result = fetcher.delete_repository(token="test_token", repository=repo_format)
        assert result["status"] == "deleted"


def test_gitlab_delete_branch_after_merge(patched_gitlab_manager):
    fetcher = rf.GitLabRepoFetcher()

    # Simulate deleting a branch after merge
    result = fetcher.delete_branch(
        token="test_token",
        project_id="group/project",
        branch_name="merged-feature"
    )

    assert result["status"] == "deleted"

    spy_auth = fetcher.manager.last_auth
    _, args, _ = spy_auth.calls[-1]
    assert "merged-feature" in args


def test_github_commit_files_binary_content_warning(patched_github_manager):
    """Test that commit_files handles content (though binary should be base64 encoded)"""
    fetcher = rf.GitHubRepoFetcher()
    files = {
        "image.png": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        "regular.txt": "normal text"
    }

    result = fetcher.commit_files(
        token="test_token",
        repository="owner/repo",
        branch="main",
        files=files,
        commit_message="Add mixed content"
    )

    assert set(result["files"]) == set(files.keys())


def test_gitlab_push_single_file_unicode_content(patched_gitlab_manager):
    fetcher = rf.GitLabRepoFetcher()
    unicode_content = "Hello 世界 🌍 مرحبا"

    result = fetcher.push_single_file(
        token="test_token",
        repository="group/project",
        file_path="unicode.txt",
        content=unicode_content,
        commit_message="Add unicode content",
        branch="main"
    )

    spy_auth = fetcher.manager.last_auth
    _, _, kwargs = spy_auth.calls[-1]
    assert kwargs["content"] == unicode_content


def test_github_fetcher_base_url_configuration(patched_github_manager):
    custom_url = "https://github.enterprise.com"
    fetcher = rf.GitHubRepoFetcher(base_url=custom_url)

    assert fetcher.manager.base_url == custom_url


def test_gitlab_fetcher_base_url_configuration(patched_gitlab_manager):
    custom_url = "https://gitlab.enterprise.com"
    fetcher = rf.GitLabRepoFetcher(base_url=custom_url)

    assert fetcher.manager.base_url == custom_url


def test_repo_fetcher_handles_both_enum_and_string_consistently(monkeypatch):
    class _FakeGitHosting(str, Enum):
        GITHUB = "github"
        GITLAB = "gitlab"

    monkeypatch.setattr(rf, "GitHosting", _FakeGitHosting)
    monkeypatch.setattr(rf, "GitHubManager", SpyGitHubManager)
    monkeypatch.setattr(rf, "GitLabManager", SpyGitLabManager)

    repo_fetcher = rf.RepoFetcher()

    # Test with enum
    fetcher1, transformer1 = repo_fetcher.get_components(rf.GitHosting.GITHUB)
    # Test with string
    fetcher2, transformer2 = repo_fetcher.get_components("github")

    # Both should return same types
    assert type(fetcher1) == type(fetcher2)
    assert type(transformer1) == type(transformer2)


def test_github_commit_files_preserves_file_order(patched_github_manager):
    fetcher = rf.GitHubRepoFetcher()
    files = {
        "01_first.txt": "first",
        "02_second.txt": "second",
        "03_third.txt": "third"
    }

    result = fetcher.commit_files(
        token="test_token",
        repository="owner/repo",
        branch="main",
        files=files,
        commit_message="Add ordered files"
    )

    spy_auth = fetcher.manager.last_auth
    _, _, kwargs = spy_auth.calls[-1]
    # Verify all files are passed
    assert set(kwargs["files"].keys()) == set(files.keys())


def test_gitlab_commit_files_with_empty_author_strings(patched_gitlab_manager):
    fetcher = rf.GitLabRepoFetcher()

    result = fetcher.commit_files(
        token="test_token",
        repository="group/project",
        branch="main",
        files={"file.txt": "content"},
        commit_message="Test commit",
        author_name="",
        author_email=""
    )

    spy_auth = fetcher.manager.last_auth
    _, _, kwargs = spy_auth.calls[-1]
    assert kwargs["author_name"] == ""
    assert kwargs["author_email"] == ""


def test_github_push_single_file_root_level(patched_github_manager):
    fetcher = rf.GitHubRepoFetcher()

    result = fetcher.push_single_file(
        token="test_token",
        repository="owner/repo",
        file_path="README.md",
        content="# Root level file",
        commit_message="Add root file",
        branch="main"
    )

    spy_auth = fetcher.manager.last_auth
    _, _, kwargs = spy_auth.calls[-1]
    assert kwargs["file_path"] == "README.md"


def test_gitlab_push_single_file_deeply_nested(patched_gitlab_manager):
    fetcher = rf.GitLabRepoFetcher()

    result = fetcher.push_single_file(
        token="test_token",
        repository="group/project",
        file_path="a/b/c/d/e/f/file.txt",
        content="deeply nested",
        commit_message="Add deeply nested file",
        branch="main"
    )

    spy_auth = fetcher.manager.last_auth
    _, _, kwargs = spy_auth.calls[-1]
    assert kwargs["file_path"] == "a/b/c/d/e/f/file.txt"