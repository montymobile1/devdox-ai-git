import types

import pytest

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
    class _FakeGitHosting:
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
    class _FakeGitHosting:
        GITHUB = "github"
        GITLAB = "gitlab"

    monkeypatch.setattr(rf, "GitHosting", _FakeGitHosting)

    repo_fetcher = rf.RepoFetcher()
    out = repo_fetcher.get_components("bitbucket")
    assert out == (None, None)
