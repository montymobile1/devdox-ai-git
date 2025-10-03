import pytest
import requests
from github import GithubException
from gitlab import GitlabError

from devdox_ai_git.exceptions import exception_constants
from devdox_ai_git.exceptions.base_exceptions import DevDoxGitException
from devdox_ai_git.git_managers import (
    AuthenticatedGitHubManager,
    AuthenticatedGitLabManager,
    GitHubManager,
    GitLabManager,
)

real_module_path = "devdox_ai_git.git_managers"


class DummyGitHubRepo:
    id = 100
    name = "repo"
    full_name = "org/repo"
    description = "description"
    private = True
    html_url = "https://github.com/org/repo"
    clone_url = "https://github.com/org/repo.git"
    ssh_url = "git@github.com:org/repo.git"
    default_branch = "main"
    language = "Python"
    size = 1234
    stargazers_count = 10
    watchers_count = 5
    forks_count = 1
    open_issues_count = 0
    created_at = None
    updated_at = None
    pushed_at = None
    owner = type("Owner", (), {"login": "dev", "id": 1, "type": "User"})
    permissions = type("Perms", (), {"admin": True, "push": False, "pull": True})()


class DummyGitHubUser:
    login = "dev"
    id = 1
    name = "Dev"
    email = "dev@example.com"
    avatar_url = "https://avatar"
    html_url = "https://github.com/dev"

    def get_repos(self, **kwargs):
        class DummyPaginated:
            totalCount = 1
            per_page = 2

            def get_page(self, page_index):
                return [DummyGitHubRepo()]

        return DummyPaginated()


class TestGitHubManager:
    def test_extract_repo_info(self):
        repo = DummyGitHubRepo()
        info = GitHubManager.extract_repo_info(repo)
        assert info["id"] == 100
        assert info["permissions"] == {"admin": True, "push": False, "pull": True}

    def test_authenticated_repo_pagination_bounds(self):
        assert GitHubManager.validate_per_page(200) == 30  # default fallback
        assert GitHubManager.validate_page(-1) == 1

    def test_authenticate_failure(self, monkeypatch):
        class FailingGithub:
            def __init__(*args, **kwargs):
                raise GithubException(401, "Unauthorized", None)

        monkeypatch.setattr(f"{real_module_path}.Github", FailingGithub)

        manager = GitHubManager()
        with pytest.raises(DevDoxGitException) as exc_info:
            manager.authenticate("bad-token")
        assert exception_constants.GIT_AUTH_FAILED in str(exc_info.value)

    def test_get_user_repositories_raises(self, monkeypatch):
        class FailingUser:
            def get_repos(self, **kwargs):
                class Bad:
                    def get_page(self, i):
                        raise GithubException(500, "Fail", None)

                    per_page = 2
                    totalCount = 1

                return Bad()

        class Client:
            def get_user(self):
                return FailingUser()

        manager = AuthenticatedGitHubManager("https://api.github.com", Client())

        with pytest.raises(DevDoxGitException) as exc_info:
            manager.get_user_repositories()
        assert exception_constants.GIT_REPOS_FETCH_FAILED in str(exc_info.value)


class TestAuthenticatedGitHubManager:
    def test_github_manager_authenticate_default(self, monkeypatch):
        dummy_auth = AuthenticatedGitHubManager(
            "https://api.github.com", "dummy_client"
        )

        class DummyGitHub:
            def __init__(self, token):
                assert token == "valid"

            def authenticate(self, token):
                return dummy_auth

        monkeypatch.setattr(f"{real_module_path}.Github", DummyGitHub)

        manager = GitHubManager()
        auth = manager.authenticate("valid")
        assert isinstance(auth, AuthenticatedGitHubManager)

    def test_authenticated_manager_get_user(self, monkeypatch):
        dummy_user = DummyGitHubUser()

        dummy_client = type("Client", (), {"get_user": lambda self: dummy_user})()
        manager = AuthenticatedGitHubManager("https://api.github.com", dummy_client)

        user_info = manager.get_user()
        assert user_info.login == "dev"
        assert hasattr(user_info, "html_url")

    def test_authenticated_manager_repositories(self, monkeypatch):
        dummy_client = type(
            "Client", (), {"get_user": lambda self: DummyGitHubUser()}
        )()
        manager = AuthenticatedGitHubManager("https://api.github.com", dummy_client)

        result = manager.get_user_repositories(page=2, per_page=5)
        assert result["pagination_info"]["current_page"] == 2
        assert isinstance(result["repositories"], list)

    def test_authenticate_custom_url(self, monkeypatch):
        dummy_auth = AuthenticatedGitHubManager("https://custom.api", "client")

        class DummyGitHub:
            def __init__(self, base_url, login_or_token):
                assert base_url == "https://custom.api"
                assert login_or_token == "valid"

        monkeypatch.setattr(f"{real_module_path}.Github", DummyGitHub)

        manager = GitHubManager(base_url="https://custom.api")
        manager.authenticate("valid")




class DummyGitLab:
    def __init__(self, url, private_token):
        assert private_token == "good-token"
        assert url.startswith("https://gitlab.com")
        self._authenticated = False

    def auth(self):
        self._authenticated = True

    def projects(self):
        """Dummy Project, meant to just mimic the actual operation"""
        pass


class DummyGitLabRepo:
    def __init__(self):
        self._data = [{"id": 1, "name": "test"}]
        self._headers = {"X-Total-Pages": "1", "X-Next-Page": "", "X-Prev-Page": ""}

    def json(self):
        return self._data

    def raise_for_status(self):
        """
        For Testing, should remain empty
        """
        pass

    @property
    def headers(self):
        return self._headers


class DummySession:
    def get(self, url, headers=None):
        return DummyGitLabRepo()


class TestGitLabManager:
    def test_gitlab_authenticate_success(self, monkeypatch):
        monkeypatch.setattr(f"{real_module_path}.gitlab.Gitlab", DummyGitLab)
        manager = GitLabManager()
        auth = manager.authenticate("good-token")
        assert isinstance(auth, AuthenticatedGitLabManager)
        assert auth._git_client._authenticated is True

    def test_gitlab_authenticate_failure(self, monkeypatch):
        def raise_auth(*args, **kwargs):
            raise GitlabError("auth failed")

        monkeypatch.setattr(f"{real_module_path}.gitlab.Gitlab", raise_auth)

        manager = GitLabManager()
        with pytest.raises(DevDoxGitException) as exc_info:
            manager.authenticate("bad-token")
        assert exception_constants.GIT_AUTH_FAILED in str(exc_info.value)


class TestAuthenticatedGitLabManager:
    def test_get_user_success(self):
        class DummyRequests:
            def get(self, url, headers=None, *args, **kwargs):
                class Response:
                    def raise_for_status(self):
                        """
                        For Testing, should remain empty
                        """
                        pass

                    def json(self):
                        return {"id": 1, "username": "dev"}

                return Response()

            def Session(self):
                return self

        manager = AuthenticatedGitLabManager(
            "https://gitlab.com",
            DummyGitLab("https://gitlab.com", "good-token"),
            "good-token",
            session=DummyRequests(),
        )
        user = manager.get_user()
        assert user["username"] == "dev"

    def test_get_user_failure(self):
        class DummyRequests:
            def get(self, url, headers=None, *args, **kwargs):
                raise requests.exceptions.RequestException("fail")

            def Session(self):
                return self

        manager = AuthenticatedGitLabManager(
            "https://gitlab.com",
            DummyGitLab("https://gitlab.com", "good-token"),
            "good-token",
            session=DummyRequests(),
        )
        with pytest.raises(DevDoxGitException) as exc_info:
            manager.get_user()
        assert exception_constants.GIT_USER_FETCH_FAILED in str(exc_info.value)

    def test_get_user_repositories_success(self):
        class DummyRequests:
            def get(self, url, headers=None, *args, **kwargs):
                class Response:
                    def raise_for_status(self):
                        """
                        For Testing, should remain empty
                        """
                        pass

                    def json(self):
                        return [{"id": 42, "name": "repo"}]

                    headers = {
                        "X-Total-Pages": "2",
                        "X-Next-Page": "2",
                        "X-Prev-Page": "",
                    }

                return Response()

            def Session(self):
                return self

        manager = AuthenticatedGitLabManager(
            "https://gitlab.com",
            DummyGitLab("https://gitlab.com", "good-token"),
            "good-token",
            session=DummyRequests(),
        )
        repos = manager.get_user_repositories(page=1, per_page=20)
        assert isinstance(repos["repositories"], list)
        assert repos["pagination_info"]["total_pages"] == 2

    def test_get_user_repositories_failure(self):
        class DummyRequests:
            def get(self, url, headers=None, *args, **kwargs):
                raise requests.exceptions.RequestException("fail")

            def Session(self):
                return self

        manager = AuthenticatedGitLabManager(
            "https://gitlab.com",
            DummyGitLab("https://gitlab.com", "good-token"),
            "good-token",
            session=DummyRequests(),
        )
        with pytest.raises(DevDoxGitException) as exc_info:
            manager.get_user_repositories()
        assert exception_constants.GIT_REPOS_FETCH_FAILED in str(exc_info.value)

    def test_get_user_repositories_missing_headers(self):
        class DummyRequests:
            def get(self, url, headers=None, *args, **kwargs):
                class Response:
                    def raise_for_status(self):
                        """
                        For Testing, should remain empty
                        """
                        pass

                    def json(self):
                        return [{"id": 99}]

                    headers = {}

                return Response()

            def Session(self):
                return self

        manager = AuthenticatedGitLabManager(
            "https://gitlab.com",
            DummyGitLab("https://gitlab.com", "good-token"),
            "good-token",
            session=DummyRequests(),
        )
        result = manager.get_user_repositories()
        assert result["pagination_info"]["total_pages"] == 1


# ---------------------------------------------
# Extra coverage for GitHub manager branches
# ---------------------------------------------

def test_github_get_project_parses_string_and_returns_repo(monkeypatch):
    class DummyClient:
        def get_repo(self, full_name):
            assert full_name == "org/repo"
            return "OK"

    # make parse_git_remote return an object that has .full_name
    RemoteRef = type("RemoteRef", (), {"full_name": "org/repo"})
    monkeypatch.setattr(
        f"{real_module_path}.parse_git_remote", lambda s: RemoteRef()
    )

    mgr = AuthenticatedGitHubManager("https://api.github.com", DummyClient())
    assert mgr.get_project("https://github.com/org/repo.git") == "OK"


def test_github_get_project_raises_githubexception(monkeypatch):
    class DummyClient:
        def get_repo(self, full_name):
            from github import GithubException
            raise GithubException(404, "not found", None)

    mgr = AuthenticatedGitHubManager("https://api.github.com", DummyClient())
    with pytest.raises(DevDoxGitException) as exc:
        mgr.get_project("org/repo")
    assert exception_constants.GIT_PROJECT_FETCH_FAILED in str(exc.value)


def test_github_get_project_languages_from_string(monkeypatch):
    class RepoObj:
        def get_languages(self):
            return {"Go": 999}

    class DummyClient:
        def get_repo(self, full_name):
            assert full_name == "org/repo"
            return RepoObj()

    RemoteRef = type("RemoteRef", (), {"full_name": "org/repo"})
    monkeypatch.setattr(f"{real_module_path}.parse_git_remote", lambda s: RemoteRef())

    mgr = AuthenticatedGitHubManager("https://api.github.com", DummyClient())
    assert mgr.get_project_languages("https://github.com/org/repo.git") == {"Go": 999}


def test_github_get_project_languages_raises(monkeypatch):
    class DummyClient:
        def get_repo(self, _):
            from github import GithubException
            raise GithubException(500, "boom", None)

    mgr = AuthenticatedGitHubManager("https://api.github.com", DummyClient())
    with pytest.raises(DevDoxGitException) as exc:
        mgr.get_project_languages("org/repo")
    assert exception_constants.GIT_PROJECT_LANGUAGE_FETCH_FAILED in str(exc.value)


def test_github_get_user_raises(monkeypatch):
    class DummyClient:
        def get_user(self):
            from github import GithubException
            raise GithubException(401, "nope", None)

    mgr = AuthenticatedGitHubManager("https://api.github.com", DummyClient())
    with pytest.raises(DevDoxGitException) as exc:
        mgr.get_user()
    assert exception_constants.GIT_USER_FETCH_FAILED in str(exc.value)


def test_github_is_supported_file_true_false():
    mgr = AuthenticatedGitHubManager("https://api.github.com", git_client=None)
    assert mgr._is_supported_file("a/b/c/module.py") is True
    assert mgr._is_supported_file("a/b/archive.bin") is False


@pytest.mark.parametrize(
    "total_count,page,per_page,expect",
    [
        (0, 1, 30, {"total_pages": 0, "has_next_page": False, "has_prev_page": False,
                    "next_page": None, "prev_page": None}),
        (10, 1, 10, {"total_pages": 1, "has_next_page": False, "has_prev_page": False,
                     "next_page": None, "prev_page": None}),
        (11, 1, 10, {"total_pages": 2, "has_next_page": True, "has_prev_page": False,
                     "next_page": 2, "prev_page": None}),
        (20, 2, 10, {"total_pages": 2, "has_next_page": False, "has_prev_page": True,
                     "next_page": None, "prev_page": 1}),
    ],
)
def test_github_get_pagination_info_edges(total_count, page, per_page, expect):
    info = GitHubManager.get_pagination_info(total_count, page, per_page)
    for k, v in expect.items():
        assert info[k] == v


def test_github_get_repo_permissions_missing_attr():
    class R:  # no 'permissions' attribute
        pass
    perms = GitHubManager._get_repo_permissions(R())
    assert perms == {"admin": False, "push": False, "pull": False}


def test_extract_repo_info_with_dates_and_missing_permissions(monkeypatch):
    # Build a repo with date fields + no permissions attribute
    from types import SimpleNamespace
    repo = SimpleNamespace(
        id=7, name="r", full_name="o/r", description=None, private=False,
        html_url="h", clone_url="c", ssh_url="s", default_branch="main",
        language="Python", size=1, stargazers_count=2, watchers_count=3,
        forks_count=4, open_issues_count=0,
        created_at=__import__("datetime").datetime(2024, 1, 1),
        updated_at=__import__("datetime").datetime(2024, 1, 2),
        pushed_at=__import__("datetime").datetime(2024, 1, 3),
        owner=SimpleNamespace(login="me", id=1, type="User"),
    )
    info = GitHubManager.extract_repo_info(repo)
    assert info["created_at"].startswith("2024-01-01")
    assert info["permissions"] == {"admin": False, "push": False, "pull": False}


# ---------------------------------------------
# Extra coverage for GitLab manager branches
# ---------------------------------------------

def test_gitlab_get_project_parses_string_and_returns_project(monkeypatch):
    class Projects:
        def get(self, pid, statistics=True, timeout=None):
            assert pid == "group/proj"
            assert statistics is True
            assert timeout == 30  # DEFAULT_TIMEOUT via method default
            return "PROJ"
    class DummyClient:
        projects = Projects()

    RemoteRef = type("RemoteRef", (), {"full_name": "group/proj"})
    monkeypatch.setattr(f"{real_module_path}.parse_git_remote", lambda s: RemoteRef())

    mgr = AuthenticatedGitLabManager("https://gitlab.com", DummyClient(), "tkn")
    assert mgr.get_project("https://gitlab.com/group/proj.git") == "PROJ"


def test_gitlab_get_project_raises(monkeypatch):
    class Projects:
        def get(self, *_args, **_kwargs):
            from gitlab import GitlabError
            raise GitlabError("broken")
    class DummyClient:
        projects = Projects()
    mgr = AuthenticatedGitLabManager("https://gitlab.com", DummyClient(), "tkn")
    with pytest.raises(DevDoxGitException) as exc:
        mgr.get_project(123)
    assert exception_constants.GIT_PROJECT_FETCH_FAILED in str(exc.value)

def test_gitlab_get_project_languages_from_id(monkeypatch):
    class Proj:
        def languages(self):
            return {"Rust": 33}
    class Projects:
        def get(self, pid, timeout=None):
            assert pid == "g/p"
            return Proj()
    class DummyClient:
        projects = Projects()

    RemoteRef = type("RemoteRef", (), {"full_name": "g/p"})
    monkeypatch.setattr(f"{real_module_path}.parse_git_remote", lambda s: RemoteRef())

    mgr = AuthenticatedGitLabManager("https://gitlab.com", DummyClient(), "tkn")
    assert mgr.get_project_languages("ssh://git@gitlab.com/g/p.git") == {"Rust": 33}


def test_gitlab_get_project_languages_raises():
    class Projects:
        def get(self, *_a, **_k):
            from gitlab import GitlabError
            raise GitlabError("boom")
    class DummyClient:
        projects = Projects()
    mgr = AuthenticatedGitLabManager("https://gitlab.com", DummyClient(), "tkn")
    with pytest.raises(DevDoxGitException) as exc:
        mgr.get_project_languages(999)
    assert exception_constants.GIT_PROJECT_LANGUAGE_FETCH_FAILED in str(exc.value)


def test_gitlab_user_repos_boundary_clamps_and_url(monkeypatch):
    class DummyRequests:
        def get(self, url, headers=None, timeout=None):
            # per_page should be clamped to 100, page to 1
            assert "per_page=100" in url
            assert "page=1" in url
            class R:
                def raise_for_status(self): pass
                def json(self): return [{"id": 1}]
                headers = {"X-Total-Pages": "1", "X-Next-Page": "", "X-Prev-Page": "", "X-Total": "1"}
            return R()
        def Session(self): return self

    mgr = AuthenticatedGitLabManager(
        "https://gitlab.com",
        DummyGitLab("https://gitlab.com", "good-token"),
        "good-token",
        session=DummyRequests(),
    )
    out = mgr.get_user_repositories(page=-5, per_page=123)  # triggers clamping
    assert out["pagination_info"]["per_page"] == 100
    assert out["pagination_info"]["current_page"] == 1