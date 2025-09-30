import pytest

from devdox_ai_git.exceptions.base_exceptions import DevDoxGitException
from devdox_ai_git.utils.repository_url_parser import RepoRef, parse_git_remote


@pytest.mark.parametrize(
    "remote, expected",
    [
        # --- GitHub (SaaS) ---
        (
            "https://github.com/torvalds/linux.git",
            dict(
                host="github.com",
                provider="github",
                namespace=["torvalds"],
                repo="linux",
                full_name="torvalds/linux",
            ),
        ),
        (
            "https://github.com/torvalds/linux",
            dict(
                host="github.com",
                provider="github",
                namespace=["torvalds"],
                repo="linux",
                full_name="torvalds/linux",
            ),
        ),
        (
            "torvalds/linux",
            dict(
                host="",
                provider="unknown",
                namespace=["torvalds"],
                repo="linux",
                full_name="torvalds/linux",
            ),
        ),
        (
            "/torvalds/linux",
            dict(
                host="",
                provider="unknown",
                namespace=["torvalds"],
                repo="linux",
                full_name="torvalds/linux",
            ),
        ),
        (
            "git@github.com:owner/repo.git",
            dict(
                host="github.com",
                provider="github",
                namespace=["owner"],
                repo="repo",
                full_name="owner/repo",
            ),
        ),
        (
            "ssh://git@github.com/Owner/Repo.With.Dots.git",
            dict(
                host="github.com",
                provider="github",
                namespace=["Owner"],
                repo="Repo.With.Dots",
                full_name="Owner/Repo.With.Dots",
            ),
        ),
        (
            "git://github.com/foo/bar",
            dict(
                host="github.com",
                provider="github",
                namespace=["foo"],
                repo="bar",
                full_name="foo/bar",
            ),
        ),
        (
            "git+ssh://git@github.com/foo/bar.git",
            dict(
                host="github.com",
                provider="github",
                namespace=["foo"],
                repo="bar",
                full_name="foo/bar",
            ),
        ),
        # --- GitLab (SaaS + subgroups) ---
        (
            "https://gitlab.com/group/subgroup/repo",
            dict(
                host="gitlab.com",
                provider="gitlab",
                namespace=["group", "subgroup"],
                repo="repo",
                full_name="group/subgroup/repo",
            ),
        ),
        # --- GitLab (self-hosted) ---
        (
            "git@gitlab.example.org:team/tooling/repo.git",
            dict(
                host="gitlab.example.org",
                provider="gitlab",
                namespace=["team", "tooling"],
                repo="repo",
                full_name="team/tooling/repo",
            ),
        ),
        (
            "ssh://git@gitlab.internal.local/group/repo/",
            dict(
                host="gitlab.internal.local",
                provider="gitlab",
                namespace=["group"],
                repo="repo",
                full_name="group/repo",
            ),
        ),
        # --- Unknown/other providers (still parse cleanly) ---
        (
            "https://codeberg.org/foo/bar",
            dict(
                host="codeberg.org",
                provider="unknown",
                namespace=["foo"],
                repo="bar",
                full_name="foo/bar",
            ),
        ),
        (
            "git@github.enterprise.local:Group/Sub/Repo.git",
            dict(
                host="github.enterprise.local",
                provider="github",
                namespace=["Group", "Sub"],
                repo="Repo",
                full_name="Group/Sub/Repo",
            ),
        ),
        # --- Variants & edge-y but valid ---
        (
            "http://github.com/foo/bar",  # http (not https)
            dict(
                host="github.com",
                provider="github",
                namespace=["foo"],
                repo="bar",
                full_name="foo/bar",
            ),
        ),
        (
            "host:owner/repo",  # scp-like without explicit user
            dict(
                host="host",
                provider="unknown",
                namespace=["owner"],
                repo="repo",
                full_name="owner/repo",
            ),
        ),
        (
            "https://github.com//owner//repo.git",  # double slashes; should normalize
            dict(
                host="github.com",
                provider="github",
                namespace=["owner"],
                repo="repo",
                full_name="owner/repo",
            ),
        ),
        (
            "SSH://git@github.com/owner/repo",  # uppercase scheme
            dict(
                host="github.com",
                provider="github",
                namespace=["owner"],
                repo="repo",
                full_name="owner/repo",
            ),
        ),
    ],
    ids=[
        "https://github.com/torvalds/linux.git",
        "https://github.com/torvalds/linux",
        "torvalds/linux",
        "/torvalds/linux",
        "git@github.com:owner/repo.git",
        "ssh://git@github.com/Owner/Repo.With.Dots.git",
        "git://github.com/foo/bar",
        "git+ssh://git@github.com/foo/bar.git",
        "https://gitlab.com/group/subgroup/repo",
        "git@gitlab.example.org:team/tooling/repo.git",
        "ssh://git@gitlab.internal.local/group/repo/",
        "https://codeberg.org/foo/bar",
        "git@github.enterprise.local:Group/Sub/Repo.git",
        "http://github.com/foo/bar",
        "host:owner/repo",
        "https://github.com//owner//repo.git",
        "SSH://git@github.com/owner/repo",
    ],
)
def test_parse_git_remote_success(remote, expected) -> None:
    ref: RepoRef = parse_git_remote(remote)
    assert ref.original == remote
    assert ref.host == expected["host"]
    assert ref.provider == expected["provider"]
    assert ref.namespace == expected["namespace"]
    assert ref.repo == expected["repo"]
    assert ref.full_name == expected["full_name"]


@pytest.mark.parametrize(
    "bad_remote",
    [
        "https://github.com/owner",  # missing repo (only one path segment)
        "git@github.com:repo-only",  # missing namespace
        "ssh://",  # empty host/path
        "notaurl",  # not URL nor scp-like
        "https://gitlab.com/",  # missing path
        "",
        "   ",  # whitespace only
    ],
    ids=[
        "missing repo (only one path segment)",
        "missing namespace",
        "empty host/path",
        "not URL nor scp-like",
        "missing path",
        "Blank string",
        "whitespace string",
    ],
)
def test_parse_git_remote_errors(bad_remote) -> None:
    with pytest.raises(DevDoxGitException):
        parse_git_remote(bad_remote)
