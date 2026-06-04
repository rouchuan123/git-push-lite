from __future__ import annotations

import re

HTTPS_GITHUB_RE = re.compile(r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?/?$")
SSH_GITHUB_RE = re.compile(r"^git@github\.com:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?/?$")


def normalize_github_remote_url(url: str) -> str:
    return url.strip().rstrip("/")


def is_github_remote_url(url: str) -> bool:
    normalized = normalize_github_remote_url(url)
    return bool(HTTPS_GITHUB_RE.match(normalized) or SSH_GITHUB_RE.match(normalized))
