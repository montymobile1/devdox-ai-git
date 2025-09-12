import pytest

from src.devdox_ai_git.utils.repository_url_parser import RepoRef, parse_git_remote


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
                provider="codeberg.org",
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
                provider="host",
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
)
def test_parse_git_remote_success(remote, expected):
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
        "https://gitlab.com/",  # no path
        "",
        "   ",  # whitespace only
    ],
)
def test_parse_git_remote_errors(bad_remote):
    with pytest.raises(ValueError):
        parse_git_remote(bad_remote)
