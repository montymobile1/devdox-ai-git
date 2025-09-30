from github.Project import Project
from github.Repository import Repository

from devdox_ai_git.git_managers import (
    IAuthenticatedGitHubManager,
    IAuthenticatedGitLabManager,
    IManager,
)


class FakeAuthenticatedGitHubManager(IAuthenticatedGitHubManager):
    def __init__(self):
        self.user = {
            "username": "fakeuser",
            "id": 123,
            "name": "Fake User",
            "email": "fake@github.com",
            "avatar_url": "https://fake-avatar.com",
            "html_url": "https://github.com/fakeuser",
        }

    def get_user(self):
        return self.user

    def get_project(self, full_name_or_id: str | int):
        return {"id": full_name_or_id, "name": "fake-project"}

    def get_project_languages(
        self, full_name_or_id_or_repository: str | int | Repository
    ):
        return {"Python": 100}

    def get_user_repositories(
        self,
        page=1,
        per_page=20,
        visibility="all",
        affiliation="owner,collaborator,organization_member",
        sort="updated",
        direction="desc",
    ):
        return {
            "repositories": [{"name": "repo1"}, {"name": "repo2"}],
            "pagination_info": {"total_count": 2},
        }


class FakeAuthenticatedGitLabManager(IAuthenticatedGitLabManager):
    def __init__(self):
        self.user = {
            "username": "fakeuser",
            "id": 456,
            "name": "Fake User",
            "email": "fake@gitlab.com",
            "avatar_url": "https://fake-avatar.com",
            "web_url": "https://gitlab.com/fakeuser",
        }

    def get_user(self, timeout=30):
        return self.user

    def get_project(self, project_id, timeout=30):
        return {"id": project_id, "name": "fake-project"}

    def get_project_languages(self,  project_or_id: int | Project, timeout: int=30):
        return {"Python": 100}

    def get_user_repositories(self, timeout: int=30, page=1, per_page=20):
        return {
            "repositories": [{"name": "repo1"}, {"name": "repo2"}],
            "pagination_info": {"total_count": 2},
        }


class FakeGitHubManager(IManager):
    def authenticate(self, access_token: str):
        return FakeAuthenticatedGitHubManager()


class FakeGitLabManager(IManager):
    def authenticate(self, access_token: str):
        return FakeAuthenticatedGitLabManager()
