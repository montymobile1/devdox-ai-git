from abc import abstractmethod
from typing import Protocol, Optional, Dict, Any
import base64

import gitlab
import requests
from github import Github, GithubException, InputGitTreeElement, InputGitAuthor
from github.AuthenticatedUser import AuthenticatedUser
from github.Repository import Repository
from gitlab import Gitlab, GitlabError
from gitlab.v4.objects import Project

from devdox_ai_git.exceptions.base_exceptions import DevDoxGitException
from devdox_ai_git.exceptions.exception_constants import (
    GIT_AUTH_FAILED,
    GIT_PROJECT_FETCH_FAILED,
    GIT_PROJECT_LANGUAGE_FETCH_FAILED,
    GIT_REPOS_FETCH_FAILED,
    GIT_USER_FETCH_FAILED,
)

GITHUB_REPOSITORY_NAME = "GitHub"
GITLAB_REPOSITORY_NAME = "GitLab"

SUPPORTED_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".java",
    ".go",
    ".rs",
    ".cpp",
    ".c",
    ".hpp",
    ".h",
    ".rb",
    ".php",
    ".cs",
    ".jsx",
    ".tsx",
    ".vue",
    ".swift",
    ".kt",
    ".scala",
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".xml",
}

class IManager(Protocol):
    @abstractmethod
    def authenticate(self, access_token): ...

class AuthenticatedGitHubManager:
    def __init__(self, base_url, git_client):
        self.base_url = base_url
        self._git_client: Github = git_client

    def get_project(self, full_name_or_id: str | int):
        try:
            return self._git_client.get_repo(full_name_or_id)
        except GithubException as e:
            raise DevDoxGitException(
                user_message=GIT_PROJECT_FETCH_FAILED,
                log_message=GIT_PROJECT_FETCH_FAILED,
                internal_context={
                    "provider": GITHUB_REPOSITORY_NAME,
                    "manager": self.__class__.__name__,
                }
            ) from e

    def get_project_languages(
        self, full_name_or_id_or_repository: str | int | Repository
    ):
        try:
            if isinstance(full_name_or_id_or_repository, Repository):
                return full_name_or_id_or_repository.get_languages()
            else:
                return self._git_client.get_repo(
                    full_name_or_id_or_repository
                ).get_languages()
        except GithubException as e:
            raise DevDoxGitException(
                user_message=GIT_PROJECT_LANGUAGE_FETCH_FAILED,
                log_message=GIT_PROJECT_LANGUAGE_FETCH_FAILED,
                internal_context={
                    "provider": GITHUB_REPOSITORY_NAME,
                    "manager": self.__class__.__name__,
                }
            ) from e

    def get_user(self) -> AuthenticatedUser:
        """Get the authenticated user information using PyGithub."""
        try:
            user = self._git_client.get_user()
            return user
        except GithubException as e:
            raise DevDoxGitException(
                user_message=GIT_USER_FETCH_FAILED,
                log_message=GIT_USER_FETCH_FAILED,
                internal_context={
                    "provider": GITHUB_REPOSITORY_NAME,
                    "manager": self.__class__.__name__,
                }
            ) from e

    def get_user_repositories(
        self,
        page=1,
        per_page=20,
        visibility="all",
        affiliation="owner,collaborator,organization_member",
        sort="updated",
        direction="desc",
    ):
        """
        Get list of repositories that the authenticated user has access to with pagination.
        """
        try:
            per_page = GitHubManager.validate_per_page(per_page)
            page = GitHubManager.validate_page(page)

            user = self._git_client.get_user()

            repos_paginated = user.get_repos(
                visibility=visibility,
                affiliation=affiliation,
                sort=sort,
                direction=direction,
            )
            repos_paginated.per_page = per_page

            repos_page = repos_paginated.get_page(page - 1)

            pagination_info = GitHubManager.get_pagination_info(
                total_count=repos_paginated.totalCount,
                page=page,
                per_page=per_page,
            )

            return {
                "repositories": repos_page,
                "pagination_info": pagination_info,
            }

        except GithubException as e:
            raise DevDoxGitException(
                user_message=GIT_REPOS_FETCH_FAILED,
                log_message=GIT_REPOS_FETCH_FAILED,
                internal_context={
                    "provider": GITHUB_REPOSITORY_NAME,
                    "manager": self.__class__.__name__,
                }
            ) from e

    def create_repository(
            self,
            name: str,
            description: Optional[str] = None,
            visibility: str = "private",
            auto_init: bool = True,

    ) :
        """
        Create a new repository for the authenticated user.

        Args:
            name: Repository name (required)
            description: Repository description
            visibility: Whether the repository is private or public
            auto_init: Whether to initialize with a README
        Returns:
            Repository: The created repository object

        Raises:
            DevDoxGitException: If repository creation fails
        """
        try:
            user = self._git_client.get_user()
            if visibility == "private":
                private = True
            else:
                private = False
            repo = user.create_repo(
                name=name,
                description=description or "",
                private=private,
                auto_init=auto_init
            )

            return repo

        except GithubException as e:
            raise DevDoxGitException(
                user_message=f"Failed to create repository: {str(e)}",
                log_message=f"Repository creation failed for '{name}'",
                internal_context={
                    "provider": GITHUB_REPOSITORY_NAME,
                    "manager": self.__class__.__name__,
                    "repository_name": name,
                },
            ) from e

    def create_branch(
            self,
            repository: str | Repository,
            branch_name: str,
            source_branch: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new branch in a repository.

        Args:
            repository: Repository full name (e.g., 'owner/repo') or Repository object
            branch_name: Name for the new branch
            source_branch: Source branch name (defaults to repository's default branch)

        Returns:
            Dict containing the created reference information

        Raises:
            DevDoxGitException: If branch creation fails
        """
        try:
            # Get repository object if string provided
            if isinstance(repository, str):
                repo = self._git_client.get_repo(repository)
            else:
                repo = repository

            # Get source branch (default to repo's default branch)
            if source_branch is None:
                source_branch = repo.default_branch

            # Get the source branch to get its commit SHA
            src_branch = repo.get_branch(source_branch)

            # Create new branch reference
            ref = repo.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=src_branch.commit.sha
            )

            return {
                "ref": ref.ref,
                "sha": ref.object.sha,
                "url": ref.url,
            }

        except GithubException as e:
            raise DevDoxGitException(
                user_message=f"Failed to create branch: {str(e)}",
                log_message=f"Branch creation failed for '{branch_name}'",
                internal_context={
                    "provider": GITHUB_REPOSITORY_NAME,
                    "manager": self.__class__.__name__,
                    "branch_name": branch_name,
                    "source_branch": source_branch,
                },
            ) from e

    def commit_files(
            self,
            repository: str | Repository,
            branch: str,
            files: Dict[str, str],
            commit_message: str,
            author_name: Optional[str] = None,
            author_email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Commit multiple files to a repository in a single commit.

        Args:
            repository: Repository full name or Repository object
            branch: Branch name to commit to
            files: Dictionary mapping file paths to their content
            commit_message: Commit message
            author_name: Author name (optional, uses authenticated user if not provided)
            author_email: Author email (optional, uses authenticated user if not provided)

        Returns:
            Dict containing commit information

        Raises:
            DevDoxGitException: If commit fails
        """
        try:
            # Get repository object if string provided
            if isinstance(repository, str):
                repo = self._git_client.get_repo(repository)
            else:
                repo = repository

            # Get the branch reference
            branch_ref = repo.get_git_ref(f"heads/{branch}")
            branch_sha = branch_ref.object.sha

            # Get the base tree
            base_tree = repo.get_git_tree(sha=branch_sha)

            # Create blobs for each file
            tree_elements = []
            for file_path, content in files.items():
                blob = repo.create_git_blob(content=content, encoding="utf-8")
                tree_elements.append(
                    InputGitTreeElement(
                        path=file_path,
                        mode="100644",  # Regular file
                        type="blob",
                        sha=blob.sha,
                    )
                )

            # Create tree with the new blobs
            tree = repo.create_git_tree(tree=tree_elements, base_tree=base_tree)

            # Create author object if name and email provided
            author = None
            if author_name and author_email:
                author = InputGitAuthor(name=author_name, email=author_email)

            # Create commit
            commit = repo.create_git_commit(
                message=commit_message,
                tree=tree,
                parents=[repo.get_git_commit(branch_sha)],
                author=author,
            )

            # Update branch reference to point to new commit
            branch_ref.edit(sha=commit.sha)

            return {
                "commit_sha": commit.sha,
                "commit_url": commit.html_url,
                "message": commit_message,
                "files_count": len(files),
            }

        except GithubException as e:
            raise DevDoxGitException(
                user_message=f"Failed to commit files: {str(e)}",
                log_message=f"Commit failed on branch '{branch}'",
                internal_context={
                    "provider": GITHUB_REPOSITORY_NAME,
                    "manager": self.__class__.__name__,
                    "branch": branch,
                    "files_count": len(files),
                },
            ) from e

    def push_single_file(
            self,
            repository: str | Repository,
            file_path: str,
            content: str,
            commit_message: str,
            branch: str,
            update: bool = False,
    ) -> Dict[str, Any]:
        """
        Push a single file to a repository (create or update).

        Args:
            repository: Repository full name or Repository object
            file_path: Path where the file should be created/updated
            content: File content
            commit_message: Commit message
            branch: Branch name
            update: Whether this is an update (requires file to exist)

        Returns:
            Dict containing commit information

        Raises:
            DevDoxGitException: If push fails
        """
        try:
            # Get repository object if string provided
            if isinstance(repository, str):
                repo = self._git_client.get_repo(repository)
            else:
                repo = repository

            if update:
                # Get existing file to get its SHA
                existing_file = repo.get_contents(file_path, ref=branch)
                result = repo.update_file(
                    path=file_path,
                    message=commit_message,
                    content=content,
                    sha=existing_file.sha,
                    branch=branch,
                )
            else:
                # Create new file
                result = repo.create_file(
                    path=file_path,
                    message=commit_message,
                    content=content,
                    branch=branch,
                )

            return {
                "commit_sha": result["commit"].sha,
                "commit_url": result["commit"].html_url,
                "content_sha": result["content"].sha,
                "file_path": file_path,
            }

        except GithubException as e:
            raise DevDoxGitException(
                user_message=f"Failed to push file: {str(e)}",
                log_message=f"File push failed for '{file_path}' on branch '{branch}'",
                internal_context={
                    "provider": GITHUB_REPOSITORY_NAME,
                    "manager": self.__class__.__name__,
                    "file_path": file_path,
                    "branch": branch,
                    "update": update,
                },
            ) from e


    def _is_supported_file(self, filename: str) -> bool:
        """Check if file type is supported"""
        return any(filename.endswith(ext) for ext in SUPPORTED_EXTENSIONS)


class GitHubManager(IManager):

    default_base_url = "https://api.github.com"

    def __init__(self, base_url=default_base_url):
        self.base_url = base_url

    def authenticate(self, access_token: str) -> AuthenticatedGitHubManager:

        try:
            if self.base_url == self.default_base_url:
                github_client = Github(access_token)
            else:
                github_client = Github(
                    base_url=self.base_url, login_or_token=access_token
                )

            return AuthenticatedGitHubManager(
                base_url=self.base_url, git_client=github_client
            )

        except GithubException as e:
            raise DevDoxGitException(
                user_message=GIT_AUTH_FAILED,
                log_message=GIT_AUTH_FAILED,
                internal_context={
                    "provider": GITHUB_REPOSITORY_NAME,
                    "manager": self.__class__.__name__
                }
            ) from e

    @staticmethod
    def validate_per_page(per_page):
        return per_page if 1 <= per_page <= 100 else 30

    @staticmethod
    def validate_page(page):
        return page if page >= 1 else 1

    @staticmethod
    def extract_repo_info(repo):
        return {
            "id": repo.id,
            "name": repo.name,
            "full_name": repo.full_name,
            "description": repo.description,
            "private": repo.private,
            "html_url": repo.html_url,
            "clone_url": repo.clone_url,
            "ssh_url": repo.ssh_url,
            "default_branch": repo.default_branch,
            "language": repo.language,
            "size": repo.size,
            "stargazers_count": repo.stargazers_count,
            "watchers_count": repo.watchers_count,
            "forks_count": repo.forks_count,
            "open_issues_count": repo.open_issues_count,
            "created_at": repo.created_at.isoformat() if repo.created_at else None,
            "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
            "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
            "owner": {
                "login": repo.owner.login,
                "id": repo.owner.id,
                "type": repo.owner.type,
            },
            "permissions": GitHubManager._get_repo_permissions(repo),
        }

    @staticmethod
    def _get_repo_permissions(repo):
        permissions = getattr(repo, "permissions", None)
        return {
            "admin": getattr(permissions, "admin", False),
            "push": getattr(permissions, "push", False),
            "pull": getattr(permissions, "pull", False),
        }

    @staticmethod
    def get_pagination_info(total_count, page, per_page):
        total_pages = (total_count + per_page - 1) // per_page
        has_next_page = page < total_pages
        has_prev_page = page > 1

        return {
            "current_page": page,
            "per_page": per_page,
            "total_count": total_count,
            "total_pages": total_pages,
            "has_next_page": has_next_page,
            "has_prev_page": has_prev_page,
            "next_page": page + 1 if has_next_page else None,
            "prev_page": page - 1 if has_prev_page else None,
        }


class AuthenticatedGitLabManager:

    DEFAULT_TIMEOUT = 50
    FILE_UPLOAD_TIMEOUT = 120
    COMMIT_TIMEOUT = 60

    def __init__(
        self,
        base_url,
        git_client,
        access_token,
        session: requests.Session | None = None,
    ):
        self.base_url = base_url
        self._header = {"PRIVATE-TOKEN": access_token}
        self._git_client: Gitlab = git_client
        self._rq = session or requests.Session()

    def get_project(self, project_id, timeout: int = DEFAULT_TIMEOUT) -> Project:
        try:
            return self._git_client.projects.get(
                project_id, statistics=True, timeout=timeout
            )
        except GitlabError as e:
            raise DevDoxGitException(
                user_message=GIT_PROJECT_FETCH_FAILED,
                log_message=GIT_PROJECT_FETCH_FAILED,
                internal_context={
                    "provider": GITLAB_REPOSITORY_NAME,
                    "manager": self.__class__.__name__,
                }
            ) from e

    def get_project_languages(
        self, project_or_id: int | Project, timeout: int = DEFAULT_TIMEOUT
    ):
        try:
            if isinstance(project_or_id, Project):
                return project_or_id.languages()
            else:
                return self._git_client.projects.get(
                    project_or_id, timeout=timeout
                ).languages()
        except GitlabError as e:
            raise DevDoxGitException(
                user_message=GIT_PROJECT_LANGUAGE_FETCH_FAILED,
                log_message=GIT_PROJECT_LANGUAGE_FETCH_FAILED,
                internal_context={
                    "provider": GITLAB_REPOSITORY_NAME,
                    "manager": self.__class__.__name__,
                }
            ) from e

    def get_user(self, timeout: int = DEFAULT_TIMEOUT):
        try:
            url = f"{self.base_url}/api/v4/user"
            response = self._rq.get(url, headers=self._header, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise DevDoxGitException(
                user_message=GIT_USER_FETCH_FAILED,
                log_message=GIT_USER_FETCH_FAILED,
                internal_context={
                    "provider": GITLAB_REPOSITORY_NAME,
                    "manager": self.__class__.__name__,
                }
            ) from e

    def get_user_repositories(
        self, page=1, per_page=20, timeout: int = DEFAULT_TIMEOUT
    ):
        try:
            per_page = max(1, min(per_page, 100))
            page = max(1, page)

            url = (
                f"{self.base_url}/api/v4/projects"
                f"?membership=true&min_access_level=30&per_page={per_page}&page={page}"
            )
            response = self._rq.get(url, headers=self._header, timeout=timeout)
            response.raise_for_status()

            repos = response.json()
            pagination = {
                "current_page": page,
                "per_page": per_page,
                "total_count": int(response.headers.get("X-Total") or 0) or 0,
                "total_pages": int(response.headers.get("X-Total-Pages") or 1),
                "next_page": int(response.headers.get("X-Next-Page") or 0) or None,
                "prev_page": int(response.headers.get("X-Prev-Page") or 0) or None,
            }
            return {"repositories": repos, "pagination_info": pagination}
        except requests.exceptions.RequestException as e:
            raise DevDoxGitException(
                user_message=GIT_REPOS_FETCH_FAILED,
                log_message=GIT_REPOS_FETCH_FAILED,
                internal_context={
                    "provider": GITLAB_REPOSITORY_NAME,
                    "manager": self.__class__.__name__,
                }
            ) from e

    def create_repository(
            self,
            name: str,
            description: Optional[str] = None,
            visibility: str = "private",
            auto_init: bool = True,
            timeout: int = DEFAULT_TIMEOUT,
    ) :
        """
        Create a new repository/project for the authenticated user.

        Args:
            name: Repository/project name (required)
            description: Repository description
            visibility: Repository visibility ('private', 'internal', or 'public')
            auto_init: Whether to initialize with a README
            timeout: Request timeout in seconds

        Returns:
            Project: The created project object

        Raises:
            DevDoxGitException: If repository creation fails
        """
        try:

            project_data = {
                "name": name,
                "visibility": visibility,
            }

            if description:
                project_data["description"] = description

            if auto_init:
                project_data["initialize_with_readme"] = True

            project = self._git_client.projects.create(project_data, timeout=timeout)

            return project

        except GitlabError as e:
            raise DevDoxGitException(
                user_message=f"Failed to create repository: {str(e)}",
                log_message=f"Repository creation failed for '{name}'",
                internal_context={
                    "provider": GITLAB_REPOSITORY_NAME,
                    "manager": self.__class__.__name__,
                    "repository_name": name,
                },
            ) from e

    def create_branch(
            self,
            project_or_id: int | Project,
            branch_name: str,
            source_branch: Optional[str] = None,
            timeout: int = DEFAULT_TIMEOUT,
    ) -> Dict[str, Any]:
        """
        Create a new branch in a repository.

        Args:
            project_or_id: Project ID or Project object
            branch_name: Name for the new branch
            source_branch: Source branch name (defaults to project's default branch)
            timeout: Request timeout in seconds

        Returns:
            Dict containing the created branch information

        Raises:
            DevDoxGitException: If branch creation fails
        """
        try:
            # Get project object if ID provided
            if isinstance(project_or_id, int):
                project = self._git_client.projects.get(project_or_id, timeout=timeout)
            else:
                project = project_or_id

            # Get source branch (default to project's default branch)
            if source_branch is None:
                source_branch = project.default_branch

            # Create new branch
            branch = project.branches.create(
                {
                    "branch": branch_name,
                    "ref": source_branch
                },
                timeout=timeout
            )

            return {
                "name": branch.name,
                "commit": {
                    "id": branch.commit["id"],
                    "message": branch.commit.get("message", ""),
                },
                "protected": branch.protected,
                "web_url": branch.web_url if hasattr(branch, "web_url") else None,
            }

        except GitlabError as e:
            raise DevDoxGitException(
                user_message=f"Failed to create branch: {str(e)}",
                log_message=f"Branch creation failed for '{branch_name}'",
                internal_context={
                    "provider": GITLAB_REPOSITORY_NAME,
                    "manager": self.__class__.__name__,
                    "branch_name": branch_name,
                    "source_branch": source_branch,
                },
            ) from e

    def commit_files(
            self,
            project_or_id: int | Project,
            branch: str,
            files: Dict[str, str],
            commit_message: str,
            author_name: Optional[str] = None,
            author_email: Optional[str] = None,
            timeout: int = DEFAULT_TIMEOUT,
    ) -> Dict[str, Any]:
        """
        Commit multiple files to a repository in a single commit.

        Args:
            project_or_id: Project ID or Project object
            branch: Branch name to commit to
            files: Dictionary mapping file paths to their content
            commit_message: Commit message
            author_name: Author name (optional)
            author_email: Author email (optional)
            timeout: Request timeout in seconds

        Returns:
            Dict containing commit information

        Raises:
            DevDoxGitException: If commit fails
        """
        try:
            # Get project object if ID provided
            if isinstance(project_or_id, int):
                project = self._git_client.projects.get(project_or_id, timeout=timeout)
            else:
                project = project_or_id

            # Build actions list for all files
            actions = []
            for file_path, content in files.items():
                actions.append({
                    "action": "create",
                    "file_path": file_path,
                    "content": content,
                })

            # Build commit data
            commit_data = {
                "branch": branch,
                "commit_message": commit_message,
                "actions": actions,
            }

            # Add author info if provided
            if author_name:
                commit_data["author_name"] = author_name
            if author_email:
                commit_data["author_email"] = author_email

            # Create commit
            commit = project.commits.create(commit_data, timeout=timeout)

            return {
                "commit_id": commit.id,
                "commit_short_id": commit.short_id,
                "message": commit.message,
                "author_name": commit.author_name,
                "author_email": commit.author_email,
                "created_at": commit.created_at,
                "web_url": commit.web_url if hasattr(commit, "web_url") else None,
                "files_count": len(files),
            }

        except GitlabError as e:
            raise DevDoxGitException(
                user_message=f"Failed to commit files: {str(e)}",
                log_message=f"Commit failed on branch '{branch}'",
                internal_context={
                    "provider": GITLAB_REPOSITORY_NAME,
                    "manager": self.__class__.__name__,
                    "branch": branch,
                    "files_count": len(files),
                },
            ) from e

    def push_single_file(
            self,
            project_or_id: int | Project,
            file_path: str,
            content: str,
            commit_message: str,
            branch: str,
            update: bool = False,
            author_name: Optional[str] = None,
            author_email: Optional[str] = None,
            timeout: int = DEFAULT_TIMEOUT,
    ) -> Dict[str, Any]:
        """
        Push a single file to a repository (create or update).

        Args:
            project_or_id: Project ID or Project object
            file_path: Path where the file should be created/updated
            content: File content
            commit_message: Commit message
            branch: Branch name
            update: Whether this is an update (requires file to exist)
            author_name: Author name (optional)
            author_email: Author email (optional)
            timeout: Request timeout in seconds

        Returns:
            Dict containing commit information

        Raises:
            DevDoxGitException: If push fails
        """
        try:
            # Get project object if ID provided
            if isinstance(project_or_id, int):
                project = self._git_client.projects.get(project_or_id, timeout=timeout)
            else:
                project = project_or_id

            file_data = {
                "file_path": file_path,
                "branch": branch,
                "content": content,
                "commit_message": commit_message,
            }

            # Add author info if provided
            if author_name:
                file_data["author_name"] = author_name
            if author_email:
                file_data["author_email"] = author_email

            if update:
                # Get existing file and update it
                existing_file = project.files.get(file_path=file_path, ref=branch)
                existing_file.content = content
                result = existing_file.save(
                    branch=branch,
                    commit_message=commit_message,
                    **({k: v for k, v in [("author_name", author_name), ("author_email", author_email)] if v})
                )

                return {
                    "file_path": file_path,
                    "branch": branch,
                    "updated": True,
                }
            else:
                # Create new file
                new_file = project.files.create(file_data, timeout=timeout)

                return {
                    "file_path": new_file.file_path,
                    "branch": new_file.branch if hasattr(new_file, "branch") else branch,
                    "created": True,
                }

        except GitlabError as e:
            raise DevDoxGitException(
                user_message=f"Failed to push file: {str(e)}",
                log_message=f"File push failed for '{file_path}' on branch '{branch}'",
                internal_context={
                    "provider": GITLAB_REPOSITORY_NAME,
                    "manager": self.__class__.__name__,
                    "file_path": file_path,
                    "branch": branch,
                    "update": update,
                },
            ) from e

    def _is_supported_file(self, filename: str) -> bool:
        """Check if file type is supported"""
        return any(filename.endswith(ext) for ext in SUPPORTED_EXTENSIONS)


class GitLabManager(IManager):

    default_base_url = "https://gitlab.com"

    def __init__(self, base_url=default_base_url):
        self.base_url = base_url.rstrip("/")

    def authenticate(self, access_token):
        try:
            gl = gitlab.Gitlab(url=self.base_url, private_token=access_token)
            gl.auth()
            return AuthenticatedGitLabManager(
                base_url=self.base_url, git_client=gl, access_token=access_token
            )

        except GitlabError as e:
            raise DevDoxGitException(
                user_message=GIT_AUTH_FAILED,
                log_message=GIT_AUTH_FAILED,
                internal_context={
                    "provider": GITLAB_REPOSITORY_NAME,
                    "manager": self.__class__.__name__
                }
            ) from e

