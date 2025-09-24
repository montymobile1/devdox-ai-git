# tests/unit/test_fake_git_managers.py
import pytest

from devdox_ai_git.test_doubles.git_managers_doubles import (
    FakeAuthenticatedGitHubManager,
    FakeAuthenticatedGitLabManager,
    FakeGitHubManager,
    FakeGitLabManager,
)


def make_auth(manager_cls, token="any-token"):
    """Helper: create an authenticated fake from a provider."""
    return manager_cls().authenticate(token)


@pytest.mark.parametrize(
    "provider_cls, expected_auth_cls",
    [
        (FakeGitHubManager, FakeAuthenticatedGitHubManager),
        (FakeGitLabManager, FakeAuthenticatedGitLabManager),
    ],
)
def test_authenticate_returns_expected_type(provider_cls, expected_auth_cls):
    # Arrange & Act
    auth = make_auth(provider_cls, token="abc123")

    # Assert (behavior only)
    assert isinstance(auth, expected_auth_cls)


@pytest.mark.parametrize("token1, token2", [("t1", "t2"), ("", "🔥.token"), ("same", "same")])
@pytest.mark.parametrize(
    "provider_cls",
    [FakeGitHubManager, FakeGitLabManager],
)
def test_authenticate_is_token_agnostic_and_returns_fresh_instances(provider_cls, token1, token2):
    # Arrange & Act
    auth1 = make_auth(provider_cls, token1)
    auth2 = make_auth(provider_cls, token2)

    # Assert: type is correct, and each authenticate() yields a fresh instance (no shared state)
    assert type(auth1) is type(auth2)
    assert auth1 is not auth2


@pytest.mark.parametrize(
    "provider_cls, expected_url_key",
    [
        (FakeGitHubManager, "html_url"),
        (FakeGitLabManager, "web_url"),
    ],
)
def test_get_user_has_expected_identity_and_service_url(provider_cls, expected_url_key):
    # Arrange
    auth = make_auth(provider_cls)

    # Act
    user = auth.get_user()

    # Assert: stable identity fields and the service-specific URL key
    assert user["username"] == "fakeuser"
    assert user["name"] == "Fake User"
    assert user["email"].startswith("fake@")
    assert isinstance(user["id"], int)
    assert expected_url_key in user


@pytest.mark.parametrize(
    "provider_cls, project_id",
    [
        (FakeGitHubManager, 42),
        (FakeGitHubManager, "owner/repo"),
        (FakeGitLabManager, 777),
        (FakeGitLabManager, "group/project"),
    ],
)
def test_get_project_echoes_identifier_and_fixed_name(provider_cls, project_id):
    auth = make_auth(provider_cls)
    project = auth.get_project(project_id)
    assert project == {"id": project_id, "name": "fake-project"}


@pytest.mark.parametrize("provider_cls", [FakeGitHubManager, FakeGitLabManager])
def test_get_project_languages_python_only_100(provider_cls):
    auth = make_auth(provider_cls)
    langs = auth.get_project_languages(object())
    assert langs == {"Python": 100}


@pytest.mark.parametrize("provider_cls", [FakeGitHubManager, FakeGitLabManager])
def test_get_user_repositories_shape_and_count(provider_cls):
    auth = make_auth(provider_cls)

    result = auth.get_user_repositories(page=1, per_page=2)  # kwargs accepted but ignored
    assert set(result.keys()) == {"repositories", "pagination_info"}

    repos = result["repositories"]
    meta = result["pagination_info"]

    assert isinstance(repos, list) and len(repos) == 2
    assert {r["name"] for r in repos} == {"repo1", "repo2"}
    assert meta == {"total_count": 2}
