from datetime import datetime
from enum import Enum
from types import SimpleNamespace
from typing import Any

from github.AuthenticatedUser import AuthenticatedUser
from github.Repository import Repository
from gitlab.v4.objects import Project
from pydantic import BaseModel, Field

class GitHosting(str, Enum):
    GITLAB = "gitlab"
    GITHUB = "github"

class NormalizedGitRepo(BaseModel):
    """Schema for Git provider repository response (unified format)"""

    id: str = Field(..., description="Repository ID from provider")
    repo_name: str = Field(..., description="Repository name")
    description: str | None = Field(None, description="Repository description")
    html_url: str = Field(..., description="Repository URL")
    relative_path: str = Field(
        ..., description="The part of the repository's url excluding the domain"
    )

    default_branch: str = Field(..., description="Default branch name")
    forks_count: int = Field(..., description="Number of forks")
    stargazers_count: int = Field(..., description="Number of stars")
    size: int | None = Field(None, description="Repository size in KB")  # noqa: UP045
    repo_created_at: datetime | None = Field(  # noqa: UP045
        None, description="Repository creation date from provider"
    )

    # Platform-specific fields (one will be None depending on provider)
    private: bool | None = Field(None, description="Private flag (GitHub)")
    visibility: str | None = Field(
        None, description="Visibility setting (GitLab)"
    )  # noqa: UP045


class GitUserResponse(BaseModel):
    username: str | None = Field(None, description="Git Username")
    id: int | None = Field(None, description="Git user Id")
    name: str | None = Field(None, description="Git user display name")  # noqa: UP045
    email: str | None = Field(None, description="Git user email")
    avatar_url: str | None = Field(None, description="Git user avatar url")
    html_url: str | None = Field(None, description="Git user html url")


class GitLabRepoResponseTransformer:

    @classmethod
    def derive_storage_size(cls, statistics: dict[str, Any]) -> int | None:
        if not statistics:
            return None

        return statistics.get("repository_size", 0)

    @classmethod
    def derived_private_field(cls, visibility: str) -> bool | None:
        if not visibility:
            return None

        if visibility.lower() in ("private", "internal"):
            derived_private = True
        else:
            derived_private = False

        return derived_private

    @classmethod
    def transform_project_to_dict(
        cls, project: Project | SimpleNamespace
    ) -> dict[str, Any]:
        extracted_visibility = getattr(project, "visibility", None)
        extracted_statistics = getattr(project, "statistics", None)

        return {
            "id": str(project.id),
            "name": project.name,
            "description": project.description,
            "default_branch": project.default_branch,
            "forks_count": project.forks_count,
            "visibility": extracted_visibility,
            "created_at": project.created_at,
            "star_count": project.star_count,
            "http_url_to_repo": project.http_url_to_repo,
            "path_with_namespace": project.path_with_namespace,
            "statistics": extracted_statistics,
        }

    @classmethod
    def from_git(
        cls, data: Project | SimpleNamespace | dict[str, Any]
    ) -> NormalizedGitRepo | None:
        if not data:
            return None
        elif isinstance(data, Project) or isinstance(data, SimpleNamespace):
            dict_data = cls.transform_project_to_dict(data)
        elif isinstance(data, dict):
            dict_data = data
        else:
            raise TypeError(
                f"Unsupported type for `data`: {type(data)}. Expected Project, SimpleNamespace, or dict."
            )

        return NormalizedGitRepo(
            id=str(dict_data.get("id", "")),
            repo_name=dict_data.get("name"),
            description=dict_data.get("description"),
            default_branch=dict_data.get("default_branch", "main"),
            forks_count=dict_data.get("forks_count", 0),
            stargazers_count=dict_data.get("star_count", 0),
            html_url=dict_data.get("http_url_to_repo"),
            relative_path=dict_data.get("path_with_namespace"),
            visibility=dict_data.get("visibility"),
            repo_created_at=dict_data.get("created_at"),
            size=cls.derive_storage_size(dict_data.get("statistics")) or 0,
            private=cls.derived_private_field(dict_data.get("visibility")),
        )

    @classmethod
    def from_git_user(cls, data: dict) -> GitUserResponse | None:
        if not data:
            return None
        elif isinstance(data, dict):
            dict_data = data
        else:
            raise TypeError(
                f"Unsupported type for `data`: {type(data)}. Expected dict."
            )

        return GitUserResponse(
            username=dict_data.get("username"),
            id=dict_data.get("id"),
            name=dict_data.get("name"),
            email=dict_data.get("email"),
            avatar_url=dict_data.get("avatar_url"),
            html_url=dict_data.get("html_url"),
        )


class GitHubRepoResponseTransformer:

    @classmethod
    def resolve_git_size_from_kb_to_byte(cls, size: int) -> int:
        if not size:
            return 0

        return size * 1024

    @classmethod
    def transform_repository_to_dict(
        cls, repository: Repository | SimpleNamespace
    ) -> dict:
        return {
            "id": str(repository.id),
            "name": repository.name,
            "description": repository.description,
            "default_branch": repository.default_branch or "main",
            "forks_count": repository.forks_count or 0,
            "size": repository.size or 0,
            "stargazers_count": repository.stargazers_count or 0,
            "full_name": repository.full_name,
            "html_url": repository.html_url,
            "private": repository.private,
            "visibility": getattr(repository, "visibility", None),
            "repo_created_at": repository.created_at,
        }

    @classmethod
    def transform_authenticated_user_to_dict(
        cls, authenticated_user: AuthenticatedUser | SimpleNamespace
    ) -> dict:
        return {
            "login": authenticated_user.login,
            "id": authenticated_user.id,
            "name": authenticated_user.name,
            "email": authenticated_user.email,
            "avatar_url": authenticated_user.avatar_url,
            "html_url": authenticated_user.html_url,
        }

    @classmethod
    def from_git(
        cls, data: Repository | SimpleNamespace | dict
    ) -> NormalizedGitRepo | None:

        if not data:
            return None
        elif isinstance(data, Repository) or isinstance(data, SimpleNamespace):
            dict_data = cls.transform_repository_to_dict(data)
        elif isinstance(data, dict):
            dict_data = data
        else:
            raise TypeError(
                f"Unsupported type for `data`: {type(data)}. Expected Repository, SimpleNamespace, or dict."
            )

        return NormalizedGitRepo(
            id=str(dict_data.get("id", "")),
            repo_name=dict_data.get("name"),
            description=dict_data.get("description"),
            default_branch=dict_data.get("default_branch", "main"),
            forks_count=dict_data.get("forks_count", 0),
            stargazers_count=dict_data.get("stargazers_count", 0),
            relative_path=dict_data.get("full_name"),
            html_url=dict_data.get("html_url"),
            private=dict_data.get("private"),
            visibility=dict_data.get("visibility"),
            size=cls.resolve_git_size_from_kb_to_byte(dict_data.get("size", 0)),
            repo_created_at=dict_data.get("repo_created_at"),
        )

    @classmethod
    def from_git_user(
        cls, data: AuthenticatedUser | SimpleNamespace | dict
    ) -> GitUserResponse | None:
        if not data:
            return None
        elif isinstance(data, AuthenticatedUser) or isinstance(data, SimpleNamespace):
            dict_data = cls.transform_authenticated_user_to_dict(data)
        elif isinstance(data, dict):
            dict_data = data
        else:
            raise TypeError(
                f"Unsupported type for `data`: {type(data)}. Expected AuthenticatedUser or SimpleNamespace or dict."
            )

        return GitUserResponse(
            username=dict_data.get("login"),
            id=dict_data.get("id"),
            name=dict_data.get("name"),
            email=dict_data.get("email"),
            avatar_url=dict_data.get("avatar_url"),
            html_url=dict_data.get("html_url"),
        )
