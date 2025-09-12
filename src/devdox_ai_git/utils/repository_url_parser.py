from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

from models_src.dto.repo import GitHosting

from devdox_ai_git.exceptions.base_exceptions import DevDoxGitException
from devdox_ai_git.exceptions.exception_constants import (
    MISSING_NAMESPACE__REPO,
    UNRECOGNIZED_GIT_FORMAT,
)


@dataclass(frozen=True)
class RepoRef:
    original: str
    host: str                 # e.g. github.com, gitlab.com, github.enterprise.local, or "" if unknown
    provider: str             # 'github' | 'gitlab' | 'unknown'
    namespace: list[str]      # ['owner'] or ['group','subgroup',...]
    repo: str                 # 'repo' (without .git)
    full_name: str            # 'owner/repo' or 'group/sub/repo'

_SCP_RE = re.compile(r'^(?:(?P<user>[^@]+)@)?(?P<host>[^:]+):(?P<path>.+)$')

def _provider_from_host(host: str) -> str:
    h = host.lower()
    if GitHosting.GITLAB.value in h:
        return GitHosting.GITLAB.value
    if GitHosting.GITHUB.value in h:
        return GitHosting.GITHUB.value

    return "unknown"  # keep enum stable

def _split_path(path: str) -> list[str]:
    parts = [p for p in path.strip("/").split("/") if p]
    if parts and parts[-1].endswith(".git"):
        parts[-1] = parts[-1][:-4]
    return parts

# Heuristic: treat "owner/repo" or "group/sub/repo" as a *shorthand*, not a filesystem path.
def _looks_like_bare_fullname(s: str) -> bool:
    if not s or "\\" in s:                            # avoid Windows-style paths
        return False
    if s.startswith(("/", "./", "../")):              # avoid POSIX paths
        return False
    if re.match(r"^[A-Za-z]:[\\/]", s):               # avoid "C:\..."
        return False
    return "/" in s and not (":" in s or "://" in s)  # must have '/', but no URL/scp markers

def parse_git_remote(remote: str) -> RepoRef:
    remote = remote.strip()

    # URL-like (https, ssh, git, git+ssh, etc.)
    parsed = urlparse(remote)
    if parsed.scheme and parsed.netloc:
        host = (parsed.hostname or parsed.netloc).lower()
        parts = _split_path(parsed.path)
    else:
        # scp-like "user@host:ns/repo(.git)"
        m = _SCP_RE.match(remote)
        if m:
            host = m.group("host").lower()
            parts = _split_path(m.group("path"))

        # NEW: allow a *single* leading slash shorthand like "/owner/repo"
        elif remote.startswith("/") and _looks_like_bare_fullname(remote[1:]):
            host = ""
            parts = _split_path(remote[1:])
            return RepoRef(
                original=remote,
                host=host,
                provider="unknown",
                namespace=parts[:-1],
                repo=parts[-1],
                full_name="/".join(parts),
            )

        # Bare shorthand like "owner/repo" or "group/sub/repo"
        elif _looks_like_bare_fullname(remote):
            host = ""
            parts = _split_path(remote)
            return RepoRef(
                original=remote,
                host=host,
                provider="unknown",
                namespace=parts[:-1],
                repo=parts[-1],
                full_name="/".join(parts),
            )
        else:
            raise DevDoxGitException(
                user_message=UNRECOGNIZED_GIT_FORMAT,
                log_message=UNRECOGNIZED_GIT_FORMAT,
                internal_context={
                    "remote": remote,
                },
            )

    if len(parts) < 2:
        raise DevDoxGitException(
            user_message=MISSING_NAMESPACE__REPO,
            log_message=MISSING_NAMESPACE__REPO,
            internal_context={
                "remote": remote,
            },
        )

    return RepoRef(
        original=remote,
        host=host,
        provider=_provider_from_host(host),
        namespace=parts[:-1],
        repo=parts[-1],
        full_name="/".join(parts),
    )