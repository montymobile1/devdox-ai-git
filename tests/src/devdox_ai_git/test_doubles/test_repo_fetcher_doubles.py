import pytest

from devdox_ai_git.schema.repo import (
    GitHubRepoResponseTransformer,
    GitLabRepoResponseTransformer,
)
from devdox_ai_git.test_doubles.repo_fetcher_doubles import (
    FakeGitHubRepoFetcher,
    FakeGitLabRepoFetcher,
    FakeRepoFetcher,
)


# ------------------------------
# Fixtures
# ------------------------------
@pytest.fixture
def gh_fetcher() -> FakeGitHubRepoFetcher:
    return FakeGitHubRepoFetcher()


@pytest.fixture
def gl_fetcher() -> FakeGitLabRepoFetcher:
    return FakeGitLabRepoFetcher()


@pytest.fixture
def repo_fetcher() -> FakeRepoFetcher:
    return FakeRepoFetcher()


# ------------------------------
# FakeGitHubRepoFetcher
# ------------------------------
def test_github_fetch_user_repositories_records_and_returns_shape(gh_fetcher):
    out = gh_fetcher.fetch_user_repositories(token="t", offset=0, limit=10)
    assert out == {"data_count": 1, "data": ["mock-repo"]}
    assert gh_fetcher.received_calls == [("fetch_user_repositories", "t", 0, 10)]


@pytest.mark.parametrize("relative_path", ["owner/repo", 12345])  # accepts str or int
def test_github_fetch_single_repo_records_and_returns_tuple(gh_fetcher, relative_path):
    out = gh_fetcher.fetch_single_repo(token="t", relative_path=relative_path)
    assert out == ("mock-repo", ["Python"])
    assert gh_fetcher.received_calls[-1] == ("fetch_single_repo", "t", relative_path)


def test_github_fetch_repo_user_records_and_returns_user(gh_fetcher):
    out = gh_fetcher.fetch_repo_user(token="t")
    assert out == {"login": "mockuser"}
    assert gh_fetcher.received_calls[-1] == ("fetch_repo_user", "t")


# ------------------------------
# FakeGitLabRepoFetcher
# ------------------------------
def test_gitlab_fetch_user_repositories_records_and_returns_shape(gl_fetcher):
    out = gl_fetcher.fetch_user_repositories(token="t", offset=2, limit=5)
    assert out == {"data_count": 1, "data": ["mock-repo"]}
    assert gl_fetcher.received_calls == [("fetch_user_repositories", "t", 2, 5)]


def test_gitlab_fetch_single_repo_records_and_returns_tuple(gl_fetcher):
    out = gl_fetcher.fetch_single_repo(token="t", relative_path="group/project")
    assert out == ("mock-repo", ["Python"])
    assert gl_fetcher.received_calls[-1] == ("fetch_single_repo", "t", "group/project")


def test_gitlab_fetch_repo_user_records_and_returns_user(gl_fetcher):
    out = gl_fetcher.fetch_repo_user(token="t")
    assert out == {"username": "mockuser"}
    assert gl_fetcher.received_calls[-1] == ("fetch_repo_user", "t")


def test_github_and_gitlab_calls_are_isolated(gh_fetcher, gl_fetcher):
    gh_fetcher.fetch_repo_user("tg")
    gl_fetcher.fetch_repo_user("tl")
    assert gh_fetcher.received_calls == [("fetch_repo_user", "tg")]
    assert gl_fetcher.received_calls == [("fetch_repo_user", "tl")]


# ------------------------------
# FakeRepoFetcher.get_components
# ------------------------------
@pytest.mark.parametrize(
    "provider_value, expected_fetcher_type, expected_xformer_type, attr_name",
    [
        ("github", FakeGitHubRepoFetcher, GitHubRepoResponseTransformer, "github_fetcher"),
        ("GitHub", FakeGitHubRepoFetcher, GitHubRepoResponseTransformer, "github_fetcher"),
        ("GITHUB", FakeGitHubRepoFetcher, GitHubRepoResponseTransformer, "github_fetcher"),
        ("gitlab", FakeGitLabRepoFetcher, GitLabRepoResponseTransformer, "gitlab_fetcher"),
        ("GitLab", FakeGitLabRepoFetcher, GitLabRepoResponseTransformer, "gitlab_fetcher"),
        ("GITLAB", FakeGitLabRepoFetcher, GitLabRepoResponseTransformer, "gitlab_fetcher"),
    ],
)
def test_get_components_returns_expected_pair_and_same_instance(
    repo_fetcher, provider_value, expected_fetcher_type, expected_xformer_type, attr_name
):
    fetcher, transformer = repo_fetcher.get_components(provider_value)

    # Type checks
    assert isinstance(fetcher, expected_fetcher_type)
    assert isinstance(transformer, expected_xformer_type)

    # Identity: must return the *same* embedded fetcher instance
    assert fetcher is getattr(repo_fetcher, attr_name)

    # Call log includes the provider value passed
    assert repo_fetcher.calls[-1] == ("get_components", provider_value)


def test_get_components_unknown_provider_returns_none_pair_and_logs(repo_fetcher):
    fetcher, transformer = repo_fetcher.get_components("bitbucket?")
    assert (fetcher, transformer) == (None, None)
    assert repo_fetcher.calls[-1] == ("get_components", "bitbucket?")


def test_get_components_log_accumulates_calls(repo_fetcher):
    repo_fetcher.get_components("github")
    repo_fetcher.get_components("gitlab")
    repo_fetcher.get_components("??")
    assert repo_fetcher.calls == [
        ("get_components", "github"),
        ("get_components", "gitlab"),
        ("get_components", "??"),
    ]
