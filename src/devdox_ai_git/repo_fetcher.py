from typing import Any, Protocol, Optional, Dict

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

    def create_repository(self, token, name, description, visibility): ...

    def create_branch(self, token, project_id, branch_name, source_branch): ...

    def commit_files(
            self,
            token: str,
            repository: str,
            branch: str,
            files: Dict[str, str],
            commit_message: str,
            author_name: Optional[str] = None,
            author_email: Optional[str] = None
    ) -> Dict[str, Any]: ...

    def push_single_file(
            self,
            token: str,
            repository: str,
            file_path: str,
            content: str,
            commit_message: str,
            branch: str,
            update: bool = False,
            author_name: Optional[str] = None,
            author_email: Optional[str] = None
    ) -> Dict[str, Any]: ...


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

    def create_repository(
        self,
        token: str,
        name: str,
        description: str | None,
        visibility: str,
    ) -> Repository:
        authenticated_github_manager = self.manager.authenticate(token)

        repository = authenticated_github_manager.create_repository(
            name=name,
            description=description or "",
            visibility=visibility,
        )

        return repository

    def create_branch(self, token: str, project_id: str, branch_name: str, source_branch: str):
        authenticated_github_manager = self.manager.authenticate(token)
        branch = authenticated_github_manager.create_branch( project_id, branch_name, source_branch)
        return branch

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

    def commit_files(
            self,
            token: str,
            repository: str,
            branch: str,
            files: Dict[str, str],
            commit_message: str,
            author_name: Optional[str] = None,
            author_email: Optional[str] = None
    ) -> Dict[str, Any]:
        authenticated_github_manager = self.manager.authenticate(token)
        return authenticated_github_manager.commit_files(
            repository=repository,
            branch=branch,
            files=files,
            commit_message=commit_message,
            author_name=author_name,
            author_email=author_email
        )

    def push_single_file(
            self,
            token: str,
            repository: str,
            file_path: str,
            content: str,
            commit_message: str,
            branch: str,
            update: bool = False,
            author_name: Optional[str] = None,
            author_email: Optional[str] = None
    ) -> Dict[str, Any]:
        authenticated_github_manager = self.manager.authenticate(token)
        return authenticated_github_manager.push_single_file(
            repository=repository,
            file_path=file_path,
            content=content,
            commit_message=commit_message,
            branch=branch,
            update=update
        )

class GitLabRepoFetcher(IRepoFetcher):
    def __init__(self, base_url: str = GitLabManager.default_base_url):
        self.manager = GitLabManager(base_url)

    def create_repository(  self,
        token: str,
        name: str,
        description: str | None,
        visibility: str)->Project:
        authenticated_gitlab_manager = self.manager.authenticate(token)

        repository = authenticated_gitlab_manager.create_repository(
            name=name,
            description=description or "",
            visibility=visibility,
        )

        return repository

    def create_branch(self, token: str, project_id: str, branch_name: str, source_branch: str):
        authenticated_gitlab_manager = self.manager.authenticate(token)
        branch = authenticated_gitlab_manager.create_branch( project_id, branch_name, source_branch)
        return branch


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

    def commit_files(
            self,
            token: str,
            repository: str,
            branch: str,
            files: Dict[str, str],
            commit_message: str,
            author_name: Optional[str] = None,
            author_email: Optional[str] = None
    ) -> Dict[str, Any]:
        authenticated_gitlab_manager = self.manager.authenticate(token)
        return authenticated_gitlab_manager.commit_files(
            project_or_id=repository,
            branch=branch,
            files=files,
            commit_message=commit_message,
            author_name=author_name,
            author_email=author_email
        )

    def push_single_file(
            self,
            token: str,
            repository: str,
            file_path: str,
            content: str,
            commit_message: str,
            branch: str,
            update: bool = False,
            author_name: Optional[str] = None,
            author_email: Optional[str] = None
    ) -> Dict[str, Any]:
        authenticated_gitlab_manager = self.manager.authenticate(token)
        return authenticated_gitlab_manager.push_single_file(
            project_or_id=repository,
            file_path=file_path,
            content=content,
            commit_message=commit_message,
            branch=branch,
            update=update,
            author_name=author_name,
            author_email=author_email
        )



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
