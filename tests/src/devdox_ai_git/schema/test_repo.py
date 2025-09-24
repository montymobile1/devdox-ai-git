from datetime import datetime
from types import SimpleNamespace

import pytest

from devdox_ai_git.schema.repo import (
    GitHubRepoResponseTransformer as GHT,
)
from devdox_ai_git.schema.repo import (
    GitLabRepoResponseTransformer as GLT,
)
from devdox_ai_git.schema.repo import (
    GitUserResponse,
    NormalizedGitRepo,
)


# ----------------------------
# GitLabRepoResponseTransformer
# ----------------------------
def test_gitlab_from_git_with_dict_happy_path():
    created = datetime(2020, 1, 1)
    payload = {
        "id": 123,  # should be coerced to str by transformer
        "name": "proj",
        "description": "desc",
        "default_branch": "develop",
        "forks_count": 5,
        "star_count": 7,
        "http_url_to_repo": "https://gitlab.com/group/proj",
        "path_with_namespace": "group/proj",
        "visibility": "internal",  # -> private True
        "created_at": created,
        "statistics": {"repository_size": 2048},
    }

    out = GLT.from_git(payload)
    assert isinstance(out, NormalizedGitRepo)
    assert out.id == "123"
    assert out.repo_name == "proj"
    assert out.description == "desc"
    assert out.default_branch == "develop"
    assert out.forks_count == 5
    assert out.stargazers_count == 7
    assert out.html_url == "https://gitlab.com/group/proj"
    assert out.relative_path == "group/proj"
    assert out.visibility == "internal"
    assert out.repo_created_at == created
    assert out.size == 2048
    assert out.private is True


def test_gitlab_from_git_with_namespace_object_and_defaults():
    created = datetime(2019, 5, 1)
    project = SimpleNamespace(
        id=999,
        name="proj",
        description=None,
        default_branch="main",
        forks_count=0,
        star_count=0,
        http_url_to_repo="https://gitlab.example.com/g/sub/proj",
        path_with_namespace="g/sub/proj",
        visibility="public",        # -> private False
        created_at=created,
        statistics={"repository_size": 0},
    )

    out = GLT.from_git(project)
    assert out.id == "999"
    assert out.private is False
    assert out.size == 0
    assert out.visibility == "public"
    assert out.repo_created_at == created


@pytest.mark.parametrize(
    "visibility, expected_private",
    [
        ("private", True),
        ("PRIVATE", True),
        ("internal", True),
        ("Internal", True),
        ("public", False),
        ("", None),
        (None, None),
    ],
)
def test_gitlab_derived_private_field_cases(visibility, expected_private):
    assert GLT.derived_private_field(visibility) is expected_private


def test_gitlab_derive_storage_size_behaviour():
    assert GLT.derive_storage_size(None) is None
    assert GLT.derive_storage_size({}) is None
    assert GLT.derive_storage_size({"repository_size": 7}) == 7
    # missing key -> default 0
    assert GLT.derive_storage_size({"x": 3}) == 0


def test_gitlab_from_git_user_dict_and_errors():
    user = {
        "username": "alice",
        "id": 1,
        "name": "Alice",
        "email": "a@example.com",
        "avatar_url": "https://img",
        "html_url": "https://gitlab.com/alice",
    }
    out = GLT.from_git_user(user)
    assert isinstance(out, GitUserResponse)
    assert out.username == "alice"
    assert out.id == 1
    assert out.html_url == "https://gitlab.com/alice"

    assert GLT.from_git_user(None) is None
    with pytest.raises(TypeError):
        GLT.from_git_user(SimpleNamespace(username="x"))


def test_gitlab_from_git_none_and_type_error():
    assert GLT.from_git(None) is None
    with pytest.raises(TypeError):
        GLT.from_git(["not-supported"])


# ----------------------------
# GitHubRepoResponseTransformer
# ----------------------------
def test_github_from_git_with_dict_size_conversion_and_mapping():
    created = datetime(2022, 2, 2)
    payload = {
        "id": 100,
        "name": "repo",
        "description": "d",
        "default_branch": "main",
        "forks_count": 3,
        "size": 50,  # KB -> bytes
        "stargazers_count": 11,
        "full_name": "octo/repo",
        "html_url": "https://github.com/octo/repo",
        "private": True,
        "visibility": "private",
        "repo_created_at": created,
    }

    out = GHT.from_git(payload)
    assert isinstance(out, NormalizedGitRepo)
    assert out.id == "100"
    assert out.repo_name == "repo"
    assert out.description == "d"
    assert out.default_branch == "main"
    assert out.forks_count == 3
    assert out.stargazers_count == 11
    assert out.relative_path == "octo/repo"
    assert out.html_url == "https://github.com/octo/repo"
    assert out.private is True
    assert out.visibility == "private"
    assert out.repo_created_at == created
    assert out.size == 50 * 1024  # KB -> bytes


def test_github_from_git_with_namespace_defaults_and_id_str():
    repo = SimpleNamespace(
        id=321,
        name="lib",
        description=None,
        default_branch=None,     # -> "main" via transform
        forks_count=None,        # -> 0 via transform
        size=None,               # -> 0 -> bytes 0
        stargazers_count=None,   # -> 0 via transform
        full_name="me/lib",
        html_url="https://github.com/me/lib",
        private=False,
        visibility=None,
        created_at=None,         # transform uses repo_created_at, so None expected
    )

    out = GHT.from_git(repo)
    assert out.id == "321"
    assert out.default_branch == "main"
    assert out.forks_count == 0
    assert out.stargazers_count == 0
    assert out.size == 0
    assert out.repo_created_at is None
    assert out.private is False
    assert out.relative_path == "me/lib"


def test_github_size_conversion_helper():
    assert GHT.resolve_git_size_from_kb_to_byte(0) == 0
    assert GHT.resolve_git_size_from_kb_to_byte(12) == 12 * 1024
    # falsy/None guarded to 0
    assert GHT.resolve_git_size_from_kb_to_byte(None) == 0  # type: ignore[arg-type]


def test_github_transform_authenticated_user_and_from_git_user():
    auth = SimpleNamespace(
        login="octo",
        id=42,
        name="Octo Cat",
        email="octo@github.com",
        avatar_url="https://avatar",
        html_url="https://github.com/octo",
    )

    # low-level transform
    d = GHT.transform_authenticated_user_to_dict(auth)
    assert d["login"] == "octo" and d["id"] == 42

    # high-level API
    out = GHT.from_git_user(auth)
    assert isinstance(out, GitUserResponse)
    assert out.username == "octo"
    assert out.id == 42
    assert out.html_url == "https://github.com/octo"

    # dict input also valid
    out2 = GHT.from_git_user(dict(d))
    assert out2.username == "octo"

    # edge cases
    assert GHT.from_git_user(None) is None
    with pytest.raises(TypeError):
        GHT.from_git_user(["nope"])  # unsupported type


def test_github_from_git_none_and_type_error():
    assert GHT.from_git(None) is None
    with pytest.raises(TypeError):
        GHT.from_git(object())
