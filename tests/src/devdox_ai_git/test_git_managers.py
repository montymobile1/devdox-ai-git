import pytest
import requests
from github import GithubException
from github.Repository import Repository
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

    def create_repo(self, name, description="", private=False, auto_init=True):

        repo = DummyGitHubRepo()
        repo.name = name
        repo.description = description
        repo.private = private
        return repo

class DummyGitHubBranch:
    def __init__(self, name="main"):
        self.name = name
        self.commit = type("Commit", (), {"sha": "abc123def456"})()


class DummyGitHubRef:
    def __init__(self, ref_name, sha):
        self.ref = ref_name
        self.object = type("Object", (), {"sha": sha})()
        self.url = f"https://api.github.com/repos/org/repo/git/refs/{ref_name}"

    def edit(self, sha):
        self.object.sha = sha

    def delete(self):
        pass


class DummyGitHubCommit:
    def __init__(self, sha="newcommit123", message="Test commit"):
        self.sha = sha
        self.html_url = f"https://github.com/org/repo/commit/{sha}"
        self.message = message


class DummyGitHubBlob:
    def __init__(self):
        self.sha = "blob123"


class DummyGitHubTree:
    def __init__(self):
        self.sha = "tree123"


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

    def test_get_project_success(self):
        dummy_repo = DummyGitHubRepo()

        class Client:
            def get_repo(self, full_name):
                return dummy_repo

        manager = AuthenticatedGitHubManager("https://api.github.com", Client())
        repo = manager.get_project("org/repo")

        assert repo.full_name == "org/repo"
        assert repo.name == "repo"


    def test_get_project_failure(self):
        dummy_repo = DummyGitHubRepo()
        class Client:
            def get_repo(self, full_name):
                raise GithubException(404, "Not Found", None)

        manager = AuthenticatedGitHubManager("https://api.github.com", Client())

        with pytest.raises(DevDoxGitException) as exc_info:
            manager.get_project("org/nonexistent")
        assert exception_constants.GIT_PROJECT_FETCH_FAILED in str(exc_info.value)



    def test_get_project_languages_with_string(self):
        dummy_repo = DummyGitHubRepo()
        dummy_repo.get_languages = lambda: {"Python": 1500}

        class Client:
            def get_repo(self, full_name):
                return dummy_repo

        manager = AuthenticatedGitHubManager("https://api.github.com", Client())
        languages = manager.get_project_languages("org/repo")

        assert languages == {"Python": 1500}

    def test_get_project_languages_failure(self):
        class Client:
            def get_repo(self, full_name):
                raise GithubException(500, "Server Error", None)

        manager = AuthenticatedGitHubManager("https://api.github.com", Client())

        with pytest.raises(DevDoxGitException) as exc_info:
            manager.get_project_languages("org/repo")
        assert exception_constants.GIT_PROJECT_LANGUAGE_FETCH_FAILED in str(exc_info.value)

    def test_get_user_failure(self):
        class Client:
            def get_user(self):
                raise GithubException(401, "Unauthorized", None)

        manager = AuthenticatedGitHubManager("https://api.github.com", Client())

        with pytest.raises(DevDoxGitException) as exc_info:
            manager.get_user()
        assert exception_constants.GIT_USER_FETCH_FAILED in str(exc_info.value)

    def test_create_repository_private(self):
        dummy_user = DummyGitHubUser()

        class Client:
            def get_user(self):
                return dummy_user

        manager = AuthenticatedGitHubManager("https://api.github.com", Client())
        repo = manager.create_repository(
            name="test-repo",
            description="Test description",
            visibility="private",
            auto_init=True
        )

        assert repo.name == "test-repo"
        assert repo.private is True

    def test_create_repository_public(self):
        dummy_user = DummyGitHubUser()

        class Client:
            def get_user(self):
                return dummy_user

        manager = AuthenticatedGitHubManager("https://api.github.com", Client())
        repo = manager.create_repository(
            name="public-repo",
            description="Public repo",
            visibility="public"
        )

        assert repo.name == "public-repo"
        assert repo.private is False

    def test_create_repository_failure(self):
        class FailingUser:
            def create_repo(self, **kwargs):
                raise GithubException(422, "Validation Failed", None)

        class Client:
            def get_user(self):
                return FailingUser()

        manager = AuthenticatedGitHubManager("https://api.github.com", Client())

        with pytest.raises(DevDoxGitException) as exc_info:
            manager.create_repository(name="test-repo")
        assert "Failed to create repository" in str(exc_info.value)

    def test_delete_repository_with_string(self):
        dummy_repo = DummyGitHubRepo()
        dummy_repo.delete = lambda: None

        class Client:
            def get_repo(self, full_name):
                return dummy_repo

        manager = AuthenticatedGitHubManager("https://api.github.com", Client())
        result = manager.delete_repository("org/repo")

        assert result["deleted"] is True
        assert result["repository_name"] == "org/repo"

    def test_delete_repository_with_object(self):
        dummy_repo = DummyGitHubRepo()
        dummy_repo.delete = lambda: None

        class Client:
            pass

        manager = AuthenticatedGitHubManager("https://api.github.com", Client())
        result = manager.delete_repository(dummy_repo)

        assert result["deleted"] is True
        assert "org/repo" in result["repository_name"]

    def test_delete_repository_failure(self):
        class Client:
            def get_repo(self, full_name):
                raise GithubException(403, "Forbidden", None)

        manager = AuthenticatedGitHubManager("https://api.github.com", Client())

        with pytest.raises(DevDoxGitException) as exc_info:
            manager.delete_repository("org/repo")
        assert "Failed to delete repository" in str(exc_info.value)


    def test_create_branch_success(self):
        dummy_repo = DummyGitHubRepo()
        dummy_branch = DummyGitHubBranch("main")
        dummy_ref = DummyGitHubRef("refs/heads/feature", "abc123")

        dummy_repo.default_branch = "main"
        dummy_repo.get_branch = lambda name: dummy_branch
        dummy_repo.create_git_ref = lambda ref, sha: dummy_ref

        class Client:
            def get_repo(self, full_name):
                return dummy_repo

        manager = AuthenticatedGitHubManager("https://api.github.com", Client())
        result = manager.create_branch("org/repo", "feature", "main")

        assert "refs/heads/feature" in result["ref"]
        assert result["sha"] == "abc123"

    def test_create_branch_default_source(self):
        dummy_repo = DummyGitHubRepo()
        dummy_branch = DummyGitHubBranch("main")
        dummy_ref = DummyGitHubRef("refs/heads/feature", "abc123")

        dummy_repo.default_branch = "main"
        dummy_repo.get_branch = lambda name: dummy_branch
        dummy_repo.create_git_ref = lambda ref, sha: dummy_ref

        class Client:
            def get_repo(self, full_name):
                return dummy_repo

        manager = AuthenticatedGitHubManager("https://api.github.com", Client())
        result = manager.create_branch("org/repo", "feature", None)

        assert result is not None


    def test_create_branch_failure(self):
        class FailingRepo:
            default_branch = "main"

            def get_branch(self, name):
                raise GithubException(404, "Branch not found", None)

        class Client:
            def get_repo(self, full_name):
                return FailingRepo()

        manager = AuthenticatedGitHubManager("https://api.github.com", Client())

        with pytest.raises(DevDoxGitException) as exc_info:
            manager.create_branch("org/repo", "feature", "nonexistent")
        assert "Failed to create branch" in str(exc_info.value)


    def test_delete_branch_success(self):
        dummy_ref = DummyGitHubRef("heads/feature", "abc123")
        dummy_repo = DummyGitHubRepo()
        dummy_repo.get_git_ref = lambda ref: dummy_ref

        class Client:
            def get_repo(self, full_name):
                return dummy_repo

        manager = AuthenticatedGitHubManager("https://api.github.com", Client())
        result = manager.delete_branch("org/repo", "feature")

        assert result["deleted"] is True
        assert result["branch_name"] == "feature"


    def test_delete_branch_failure(self):
        class FailingRepo:
            full_name = "org/repo"

            def get_git_ref(self, ref):
                raise GithubException(404, "Reference not found", None)

        class Client:
            def get_repo(self, full_name):
                return FailingRepo()

        manager = AuthenticatedGitHubManager("https://api.github.com", Client())

        with pytest.raises(DevDoxGitException) as exc_info:
            manager.delete_branch("org/repo", "feature")
        assert "Failed to delete branch" in str(exc_info.value)

    def test_commit_files_success(self):
        dummy_repo = DummyGitHubRepo()
        dummy_ref = DummyGitHubRef("heads/main", "oldcommit123")
        dummy_blob = DummyGitHubBlob()
        dummy_tree = DummyGitHubTree()
        dummy_commit = DummyGitHubCommit()

        dummy_repo.get_git_ref = lambda ref: dummy_ref
        dummy_repo.get_git_tree = lambda sha: dummy_tree
        dummy_repo.create_git_blob = lambda content, encoding: dummy_blob
        dummy_repo.create_git_tree = lambda tree, base_tree: dummy_tree
        dummy_repo.get_git_commit = lambda sha: dummy_commit
        dummy_repo.create_git_commit = lambda message, tree, parents, author: dummy_commit

        class Client:
            def get_repo(self, full_name):
                return dummy_repo

        manager = AuthenticatedGitHubManager("https://api.github.com", Client())
        result = manager.commit_files(
            repository="org/repo",
            branch="main",
            files={"file1.txt": "content1", "file2.py": "content2"},
            commit_message="Add files"
        )

        assert result["commit_sha"] == "newcommit123"
        assert result["files_count"] == 2



    def test_commit_files_failure(self):
        class FailingRepo:
            def get_git_ref(self, ref):
                raise GithubException(404, "Reference not found", None)

        class Client:
            def get_repo(self, full_name):
                return FailingRepo()

        manager = AuthenticatedGitHubManager("https://api.github.com", Client())

        with pytest.raises(DevDoxGitException) as exc_info:
            manager.commit_files(
                repository="org/repo",
                branch="main",
                files={"file.txt": "content"},
                commit_message="Test"
            )
        assert "Failed to commit files" in str(exc_info.value)


    def test_push_single_file_create(self):
        dummy_repo = DummyGitHubRepo()

        def create_file(path, message, content, branch):
            return {
                "commit": type("Commit", (), {
                    "sha": "commit123",
                    "html_url": "https://github.com/org/repo/commit/commit123"
                })(),
                "content": type("Content", (), {"sha": "content123"})()
            }

        dummy_repo.create_file = create_file

        class Client:
            def get_repo(self, full_name):
                return dummy_repo

        manager = AuthenticatedGitHubManager("https://api.github.com", Client())
        result = manager.push_single_file(
            repository="org/repo",
            file_path="new_file.txt",
            content="content",
            commit_message="Add file",
            branch="main",
            update=False
        )

        assert result["commit_sha"] == "commit123"
        assert result["file_path"] == "new_file.txt"


    def test_push_single_file_update(self):
        dummy_repo = DummyGitHubRepo()

        existing_file = type("File", (), {"sha": "old123"})()
        dummy_repo.get_contents = lambda path, ref: existing_file

        def update_file(path, message, content, sha, branch):
            return {
                "commit": type("Commit", (), {
                    "sha": "commit456",
                    "html_url": "https://github.com/org/repo/commit/commit456"
                })(),
                "content": type("Content", (), {"sha": "content456"})()
            }

        dummy_repo.update_file = update_file

        class Client:
            def get_repo(self, full_name):
                return dummy_repo

        manager = AuthenticatedGitHubManager("https://api.github.com", Client())
        result = manager.push_single_file(
            repository="org/repo",
            file_path="existing_file.txt",
            content="updated content",
            commit_message="Update file",
            branch="main",
            update=True
        )

        assert result["commit_sha"] == "commit456"

    def test_push_single_file_failure(self):
        class FailingRepo:
            def create_file(self, **kwargs):
                raise GithubException(422, "Validation Failed", None)

        class Client:
            def get_repo(self, full_name):
                return FailingRepo()

        manager = AuthenticatedGitHubManager("https://api.github.com", Client())

        with pytest.raises(DevDoxGitException) as exc_info:
            manager.push_single_file(
                repository="org/repo",
                file_path="file.txt",
                content="content",
                commit_message="Add file",
                branch="main"
            )
        assert "Failed to push file" in str(exc_info.value)

class DummyGitLab:
    def __init__(self, url, private_token):
        assert private_token == "good-token"
        assert url.startswith("https://gitlab.com")
        self.projects = DummyGitLabProjects()
        self._authenticated = False

    def auth(self):
        self._authenticated = True

    def projects(self):
        """Dummy Project, meant to just mimic the actual operation"""
        pass


class DummyGitLabProjects:
    def get(self, project_id, **kwargs):
        return DummyGitLabProject()

    def create(self, data, **kwargs):
        project = DummyGitLabProject()
        project.name = data.get("name")
        project.visibility = data.get("visibility")
        return project


class DummyGitLabProject:
    def __init__(self):
        self.id = 1
        self.name = "test"
        self.path_with_namespace = "group/test"
        self.default_branch = "main"
        self.branches = DummyGitLabBranches()
        self.commits = DummyGitLabCommits()
        self.files = DummyGitLabFiles()

    def languages(self):
        return {"Python": 80.0, "JavaScript": 20.0}

    def delete(self):
        pass

class DummyGitLabBranches:
    def create(self, data, **kwargs):
        class Branch:
            def __init__(self, branch_name):
                self.name = branch_name
                self.commit = {"id": "commit123", "message": "Test"}
                self.protected = False
                self.web_url = "https://gitlab.com/group/test/-/tree/feature"

            def delete(self):
                pass  # Do nothing in test

        return Branch(data["branch"])

    def get(self, branch_name, **kwargs):
        class Branch:
            def __init__(self, name):
                self.name = name

            def delete(self):
                pass  # Do nothing in test

        return Branch(branch_name)

class DummyGitLabCommits:
    def create(self, data, **kwargs):
        return type("Commit", (), {
            "id": "commit123",
            "short_id": "commit12",
            "message": data["commit_message"],
            "author_name": data.get("author_name", "Author"),
            "author_email": data.get("author_email", "author@example.com"),
            "created_at": "2024-01-01T00:00:00Z",
            "web_url": "https://gitlab.com/group/test/-/commit/commit123"
        })()


class DummyGitLabFiles:
    def get(self, file_path, ref):
        file_obj = type("File", (), {
            "file_path": file_path,
            "content": "old content",
            "branch": ref
        })()
        file_obj.save = lambda **kwargs: None
        return file_obj

    def create(self, data, **kwargs):
        return type("File", (), {
            "file_path": data["file_path"],
            "branch": data.get("branch", "main")
        })()



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

    def test_get_project_success(self, monkeypatch):
        monkeypatch.setattr(f"{real_module_path}.gitlab.Gitlab", DummyGitLab)

        manager = AuthenticatedGitLabManager(
            "https://gitlab.com",
            DummyGitLab("https://gitlab.com", "good-token"),
            "good-token",
        )

        project = manager.get_project(1)
        assert project.id == 1
        assert project.name == "test"

    def test_get_project_failure(self):
        class FailingProjects:
            def get(self, project_id, **kwargs):
                raise GitlabError("Project not found")

        class FailingGitLab:
            projects = FailingProjects()

        manager = AuthenticatedGitLabManager(
            "https://gitlab.com",
            FailingGitLab(),
            "good-token",
        )

        with pytest.raises(DevDoxGitException) as exc_info:
            manager.get_project(999)
        assert exception_constants.GIT_PROJECT_FETCH_FAILED in str(exc_info.value)

    def test_get_project_languages_with_project_object(self, monkeypatch):
        monkeypatch.setattr(f"{real_module_path}.gitlab.Gitlab", DummyGitLab)

        manager = AuthenticatedGitLabManager(
            "https://gitlab.com",
            DummyGitLab("https://gitlab.com", "good-token"),
            "good-token",
        )

        project = DummyGitLabProject()
        languages = manager.get_project_languages(project)

        assert "Python" in languages
        assert languages["Python"] == 80.0

    def test_get_project_languages_with_id(self, monkeypatch):
        monkeypatch.setattr(f"{real_module_path}.gitlab.Gitlab", DummyGitLab)

        manager = AuthenticatedGitLabManager(
            "https://gitlab.com",
            DummyGitLab("https://gitlab.com", "good-token"),
            "good-token",
        )

        languages = manager.get_project_languages(1)
        assert "Python" in languages

    def test_get_project_languages_failure(self):
        class FailingProjects:
            def get(self, project_id, **kwargs):
                raise GitlabError("Failed to get project")

        class FailingGitLab:
            projects = FailingProjects()

        manager = AuthenticatedGitLabManager(
            "https://gitlab.com",
            FailingGitLab(),
            "good-token",
        )

        with pytest.raises(DevDoxGitException) as exc_info:
            manager.get_project_languages(999)
        assert exception_constants.GIT_PROJECT_LANGUAGE_FETCH_FAILED in str(exc_info.value)

    def test_create_repository_success(self, monkeypatch):
        monkeypatch.setattr(f"{real_module_path}.gitlab.Gitlab", DummyGitLab)

        manager = AuthenticatedGitLabManager(
            "https://gitlab.com",
            DummyGitLab("https://gitlab.com", "good-token"),
            "good-token",
        )

        project = manager.create_repository(
            name="new-project",
            description="Test project",
            visibility="private",
            auto_init=True
        )

        assert project.name == "new-project"
        assert project.visibility == "private"

    def test_create_repository_no_description(self, monkeypatch):
        monkeypatch.setattr(f"{real_module_path}.gitlab.Gitlab", DummyGitLab)

        manager = AuthenticatedGitLabManager(
            "https://gitlab.com",
            DummyGitLab("https://gitlab.com", "good-token"),
            "good-token",
        )

        project = manager.create_repository(
            name="simple-project",
            visibility="public"
        )

        assert project.name == "simple-project"

    def test_create_repository_failure(self):
        class FailingProjects:
            def create(self, data, **kwargs):
                raise GitlabError("Validation failed")

        class FailingGitLab:
            projects = FailingProjects()

        manager = AuthenticatedGitLabManager(
            "https://gitlab.com",
            FailingGitLab(),
            "good-token",
        )

        with pytest.raises(DevDoxGitException) as exc_info:
            manager.create_repository(name="test")
        assert "Failed to create repository" in str(exc_info.value)

    def test_delete_repository_with_id(self, monkeypatch):
        monkeypatch.setattr(f"{real_module_path}.gitlab.Gitlab", DummyGitLab)

        manager = AuthenticatedGitLabManager(
            "https://gitlab.com",
            DummyGitLab("https://gitlab.com", "good-token"),
            "good-token",
        )

        result = manager.delete_repository(1)

        assert result["deleted"] is True
        assert result["project_id"] == 1

    def test_delete_repository_with_object(self, monkeypatch):
        monkeypatch.setattr(f"{real_module_path}.gitlab.Gitlab", DummyGitLab)

        manager = AuthenticatedGitLabManager(
            "https://gitlab.com",
            DummyGitLab("https://gitlab.com", "good-token"),
            "good-token",
        )

        project = DummyGitLabProject()
        result = manager.delete_repository(project)

        assert result["deleted"] is True

    def test_delete_repository_failure(self):
        class FailingProjects:
            def get(self, project_id, **kwargs):
                raise GitlabError("Project not found")

        class FailingGitLab:
            projects = FailingProjects()

        manager = AuthenticatedGitLabManager(
            "https://gitlab.com",
            FailingGitLab(),
            "good-token",
        )

        with pytest.raises(DevDoxGitException) as exc_info:
            manager.delete_repository(999)
        assert "Failed to delete repository" in str(exc_info.value)

    def test_create_branch_success(self, monkeypatch):
        monkeypatch.setattr(f"{real_module_path}.gitlab.Gitlab", DummyGitLab)

        manager = AuthenticatedGitLabManager(
            "https://gitlab.com",
            DummyGitLab("https://gitlab.com", "good-token"),
            "good-token",
        )

        result = manager.create_branch(1, "feature", "main")

        assert result["name"] == "feature"
        assert "commit" in result

    def test_create_branch_default_source(self, monkeypatch):
        monkeypatch.setattr(f"{real_module_path}.gitlab.Gitlab", DummyGitLab)

        manager = AuthenticatedGitLabManager(
            "https://gitlab.com",
            DummyGitLab("https://gitlab.com", "good-token"),
            "good-token",
        )

        result = manager.create_branch(1, "develop", None)

        assert result["name"] == "develop"

    def test_create_branch_failure(self):
        class FailingBranches:
            def create(self, data, **kwargs):
                raise GitlabError("Branch already exists")

        class FailingProject:
            default_branch = "main"
            branches = FailingBranches()

        class FailingProjects:
            def get(self, project_id, **kwargs):
                return FailingProject()

        class FailingGitLab:
            projects = FailingProjects()

        manager = AuthenticatedGitLabManager(
            "https://gitlab.com",
            FailingGitLab(),
            "good-token",
        )

        with pytest.raises(DevDoxGitException) as exc_info:
            manager.create_branch(1, "feature", "main")
        assert "Failed to create branch" in str(exc_info.value)

    def test_delete_branch_success(self, monkeypatch):
        monkeypatch.setattr(f"{real_module_path}.gitlab.Gitlab", DummyGitLab)

        manager = AuthenticatedGitLabManager(
            "https://gitlab.com",
            DummyGitLab("https://gitlab.com", "good-token"),
            "good-token",
        )

        result = manager.delete_branch(1, "feature")

        assert result["deleted"] is True
        assert result["branch_name"] == "feature"

    def test_delete_branch_failure(self):
        class FailingBranches:
            def get(self, branch_name, **kwargs):
                raise GitlabError("Branch not found")

        class FailingProject:
            id = 1
            name = "test"
            branches = FailingBranches()

        class FailingProjects:
            def get(self, project_id, **kwargs):
                return FailingProject()

        class FailingGitLab:
            projects = FailingProjects()

        manager = AuthenticatedGitLabManager(
            "https://gitlab.com",
            FailingGitLab(),
            "good-token",
        )

        with pytest.raises(DevDoxGitException) as exc_info:
            manager.delete_branch(1, "nonexistent")
        assert "Failed to delete branch" in str(exc_info.value)

    def test_commit_files_success(self, monkeypatch):
        monkeypatch.setattr(f"{real_module_path}.gitlab.Gitlab", DummyGitLab)

        manager = AuthenticatedGitLabManager(
            "https://gitlab.com",
            DummyGitLab("https://gitlab.com", "good-token"),
            "good-token",
        )

        result = manager.commit_files(
            project_or_id=1,
            branch="main",
            files={"file1.txt": "content1", "file2.py": "content2"},
            commit_message="Add files"
        )

        assert result["commit_id"] == "commit123"
        assert result["files_count"] == 2

    def test_commit_files_with_author(self, monkeypatch):
        monkeypatch.setattr(f"{real_module_path}.gitlab.Gitlab", DummyGitLab)

        manager = AuthenticatedGitLabManager(
            "https://gitlab.com",
            DummyGitLab("https://gitlab.com", "good-token"),
            "good-token",
        )

        result = manager.commit_files(
            project_or_id=1,
            branch="main",
            files={"file.txt": "content"},
            commit_message="Test commit",
            author_name="Jane Doe",
            author_email="jane@example.com"
        )

        assert result["author_name"] == "Jane Doe"
        assert result["author_email"] == "jane@example.com"

    def test_commit_files_failure(self):
        class FailingCommits:
            def create(self, data, **kwargs):
                raise GitlabError("Commit failed")

        class FailingProject:
            commits = FailingCommits()

        class FailingProjects:
            def get(self, project_id, **kwargs):
                return FailingProject()

        class FailingGitLab:
            projects = FailingProjects()

        manager = AuthenticatedGitLabManager(
            "https://gitlab.com",
            FailingGitLab(),
            "good-token",
        )

        with pytest.raises(DevDoxGitException) as exc_info:
            manager.commit_files(
                project_or_id=1,
                branch="main",
                files={"file.txt": "content"},
                commit_message="Test"
            )
        assert "Failed to commit files" in str(exc_info.value)

    def test_push_single_file_create(self, monkeypatch):
        monkeypatch.setattr(f"{real_module_path}.gitlab.Gitlab", DummyGitLab)

        manager = AuthenticatedGitLabManager(
            "https://gitlab.com",
            DummyGitLab("https://gitlab.com", "good-token"),
            "good-token",
        )

        result = manager.push_single_file(
            project_or_id=1,
            file_path="new_file.txt",
            content="content",
            commit_message="Add file",
            branch="main",
            update=False
        )

        assert result["file_path"] == "new_file.txt"
        assert result["created"] is True

    def test_push_single_file_update(self, monkeypatch):
        monkeypatch.setattr(f"{real_module_path}.gitlab.Gitlab", DummyGitLab)

        manager = AuthenticatedGitLabManager(
            "https://gitlab.com",
            DummyGitLab("https://gitlab.com", "good-token"),
            "good-token",
        )

        result = manager.push_single_file(
            project_or_id=1,
            file_path="existing_file.txt",
            content="updated content",
            commit_message="Update file",
            branch="main",
            update=True
        )

        assert result["file_path"] == "existing_file.txt"
        assert result["updated"] is True

    def test_push_single_file_with_author(self, monkeypatch):
        monkeypatch.setattr(f"{real_module_path}.gitlab.Gitlab", DummyGitLab)

        manager = AuthenticatedGitLabManager(
            "https://gitlab.com",
            DummyGitLab("https://gitlab.com", "good-token"),
            "good-token",
        )

        result = manager.push_single_file(
            project_or_id=1,
            file_path="file.txt",
            content="content",
            commit_message="Add file",
            branch="main",
            update=False,
            author_name="John Doe",
            author_email="john@example.com"
        )

        assert result["created"] is True

    def test_push_single_file_failure(self):
        class FailingFiles:
            def create(self, data, **kwargs):
                raise GitlabError("File creation failed")

        class FailingProject:
            files = FailingFiles()

        class FailingProjects:
            def get(self, project_id, **kwargs):
                return FailingProject()

        class FailingGitLab:
            projects = FailingProjects()

        manager = AuthenticatedGitLabManager(
            "https://gitlab.com",
            FailingGitLab(),
            "good-token",
        )

        with pytest.raises(DevDoxGitException) as exc_info:
            manager.push_single_file(
                project_or_id=1,
                file_path="file.txt",
                content="content",
                commit_message="Add file",
                branch="main"
            )
        assert "Failed to push file" in str(exc_info.value)