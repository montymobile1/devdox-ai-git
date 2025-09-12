from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class RepoRef:
    original: str
    host: str                 # e.g. github.com, gitlab.com, github.enterprise.local
    provider: str             # 'github' | 'gitlab' | 'unknown'
    namespace: list[str]      # ['owner'] or ['group','subgroup',...]
    repo: str                 # 'repo' (without .git)
    full_name: str            # 'owner/repo' or 'group/sub/repo'

_SCP_RE = re.compile(r'^(?:(?P<user>[^@]+)@)?(?P<host>[^:]+):(?P<path>.+)$')

def _provider_from_host(host: str) -> str:
    h = host.lower()
    # Order matters: check 'gitlab' first so 'gitlab.example.com' doesn't get caught by 'github'
    if "gitlab" in h:
        return "gitlab"
    if "github" in h:  # supports github.com and GitHub Enterprise (any host containing 'github')
        return "github"
    return h

def _split_path(path: str) -> list[str]:
    parts = [p for p in path.strip("/").split("/") if p]
    if parts:
        last = parts[-1]
        if last.endswith(".git"):
            last = last[:-4]
        parts[-1] = last
    return parts

def parse_git_remote(remote: str) -> RepoRef:
    # Try URL-ish forms first (https, ssh, git, git+ssh, etc.)
    parsed = urlparse(remote)
    if parsed.scheme and parsed.netloc:
        # Use hostname to strip any 'user@' and any ':port'
        host = (parsed.hostname or parsed.netloc).lower()
        parts = _split_path(parsed.path)
    else:
        # Handle scp-like SSH: [user@]host:namespace/repo(.git)
        m = _SCP_RE.match(remote.strip())
        if not m:
            raise ValueError(f"Unrecognized git remote format: {remote}")
        host = m.group("host").lower()
        parts = _split_path(m.group("path"))

    if len(parts) < 2:
        raise ValueError(f"Remote is missing namespace/repo: {remote}")

    namespace, repo = parts[:-1], parts[-1]
    return RepoRef(
        original=remote,
        host=host,
        provider=_provider_from_host(host),
        namespace=namespace,
        repo=repo,
        full_name="/".join(parts),
    )