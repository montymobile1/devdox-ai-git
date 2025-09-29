from typing import Any, Protocol

from github.AuthenticatedUser import AuthenticatedUser
from github.Repository import Repository
from gitlab.v4.objects import Project

from devdox_ai_git.git_managers import GitHubManager, GitLabManager
from devdox_ai_git.schema.repo import (
    GitHosting,
    GitHubRepoResponseTransformer,
    GitLabRepoResponseTransformer,
)
from devdox_ai_git.utils.repository_url_parser import RepoRef, parse_git_remote


class IRepoFetcher(Protocol):
    def fetch_user_repositories(
        self, token: str, offset: int, limit: int
    ) -> dict[str, Any]: ...

    def fetch_single_repo(self, token: str, relative_path: str): ...

    def fetch_repo_user(self, token): ...


class GitHubRepoFetcher(IRepoFetcher):
    def __init__(self, base_url: str = GitHubManager.default_base_url):
        self.manager = GitHubManager(base_url)

    def fetch_user_repositories(
        self, token: str, offset: int, limit: int
    ) -> dict[str, Any]:
        authenticated_github_manager = self.manager.authenticate(token)
        result = authenticated_github_manager.get_user_repositories(
            page=offset + 1, per_page=limit
        )

        return {
            "data_count": result["pagination_info"]["total_count"],
            "data": result["repositories"],
        }

    def fetch_single_repo(
        self, token: str, relative_path: str
    ) -> tuple[Repository, list[str]] | None:

        authenticated_github_manager = self.manager.authenticate(token)

        repo_ref:RepoRef = parse_git_remote(relative_path)

        repository = authenticated_github_manager.get_project(repo_ref.full_name)

        if not repository:
            return None

        repository_languages = authenticated_github_manager.get_project_languages(
            repository
        )

        return repository, [*repository_languages]

    def fetch_repo_user(self, token) -> AuthenticatedUser | None:
        authenticated_github_manager = self.manager.authenticate(token)

        user = authenticated_github_manager.get_user()

        if not user:
            return None

        return user


class GitLabRepoFetcher(IRepoFetcher):
    def __init__(self, base_url: str = GitLabManager.default_base_url):
        self.manager = GitLabManager(base_url)

    def fetch_user_repositories(
        self, token: str, offset: int, limit: int
    ) -> dict[str, Any]:
        authenticated_gitlab_manager = self.manager.authenticate(token)
        result = authenticated_gitlab_manager.get_user_repositories(
            page=offset + 1, per_page=limit
        )

        return {
            "data_count": result["pagination_info"]["total_count"],
            "data": result["repositories"],
        }

    def fetch_single_repo(
        self, token: str, relative_path: str
    ) -> tuple[Project, list[str]] | None:

        authenticated_gitlab_manager = self.manager.authenticate(token)

        repo_ref:RepoRef = parse_git_remote(relative_path)

        repository = authenticated_gitlab_manager.get_project(repo_ref.full_name)

        if not repository:
            return None

        repository_languages = authenticated_gitlab_manager.get_project_languages(
            repository
        )

        return repository, [*repository_languages]

    def fetch_repo_user(self, token) -> dict | None:
        authenticated_gitlab_manager = self.manager.authenticate(token)

        user = authenticated_gitlab_manager.get_user()

        if not user:
            return None

        return user


class RepoFetcher:

    def get_components(
        self, provider: GitHosting | str
    ) -> (
        tuple[GitHubRepoFetcher, GitHubRepoResponseTransformer]
        | tuple[GitLabRepoFetcher, GitLabRepoResponseTransformer]
        | tuple[None, None]
    ):
        """bool represents whether it has a data transformer which can aid"""
        provider_value = provider.value if isinstance(provider, GitHosting) else provider
        if provider_value == GitHosting.GITHUB.value or provider == GitHosting.GITHUB:
            return GitHubRepoFetcher(), GitHubRepoResponseTransformer()
        elif provider_value == GitHosting.GITLAB.value or provider == GitHosting.GITLAB:
            return GitLabRepoFetcher(), GitLabRepoResponseTransformer()

        return None, None
