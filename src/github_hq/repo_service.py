from __future__ import annotations

from pathlib import Path
from typing import Protocol

from .gitignore_template import create_basic_gitignore
from .models import CommandResult, GitStatusEntry
from .status_parser import parse_porcelain_status
from .url_validation import is_github_remote_url, normalize_github_remote_url


class RunnerProtocol(Protocol):
    def run(self, args: list[str], cwd: Path | None, timeout_seconds: int | None = None) -> CommandResult:
        ...


class RepoService:
    def __init__(self, runner: RunnerProtocol) -> None:
        self.runner = runner

    def git_version(self) -> CommandResult:
        return self.runner.run(["--version"], cwd=None)

    def is_repository(self, repo_path: Path) -> bool:
        return self.runner.run(["rev-parse", "--is-inside-work-tree"], cwd=repo_path).ok

    def init_repository(self, repo_path: Path) -> CommandResult:
        result = self.runner.run(["init"], cwd=repo_path)
        if result.ok:
            create_basic_gitignore(repo_path)
        return result

    def get_config(self, repo_path: Path, key: str, global_scope: bool = False) -> str:
        args = ["config"]
        if global_scope:
            args.append("--global")
        args.append(key)
        result = self.runner.run(args, cwd=repo_path if not global_scope else None)
        return result.stdout.strip() if result.ok else ""

    def set_identity(self, repo_path: Path, name: str, email: str, scope: str) -> list[CommandResult]:
        global_scope = scope == "global"
        prefix = ["config", "--global"] if global_scope else ["config"]
        cwd = None if global_scope else repo_path
        return [
            self.runner.run([*prefix, "user.name", name], cwd=cwd),
            self.runner.run([*prefix, "user.email", email], cwd=cwd),
        ]

    def get_origin_url(self, repo_path: Path) -> str:
        result = self.runner.run(["remote", "get-url", "origin"], cwd=repo_path)
        return result.stdout.strip() if result.ok else ""

    def configure_origin(self, repo_path: Path, url: str) -> CommandResult:
        normalized = normalize_github_remote_url(url)
        if not is_github_remote_url(normalized):
            return CommandResult(("git", "remote"), repo_path, 2, "", "不是有效的 GitHub 远程地址")
        current = self.runner.run(["remote", "get-url", "origin"], cwd=repo_path)
        if current.ok:
            return self.runner.run(["remote", "set-url", "origin", normalized], cwd=repo_path)
        return self.runner.run(["remote", "add", "origin", normalized], cwd=repo_path)

    def current_branch(self, repo_path: Path) -> str:
        result = self.runner.run(["branch", "--show-current"], cwd=repo_path)
        return result.stdout.strip() if result.ok else ""

    def list_branches(self, repo_path: Path) -> list[str]:
        result = self.runner.run(["branch", "--format", "%(refname:short)"], cwd=repo_path)
        if not result.ok:
            return []
        return [line.strip().lstrip("*").strip() for line in result.stdout.splitlines() if line.strip()]

    def branch_exists(self, repo_path: Path, branch: str) -> bool:
        result = self.runner.run(["branch", "--list", branch], cwd=repo_path)
        return bool(result.stdout.strip())

    def switch_branch(self, repo_path: Path, branch: str) -> CommandResult:
        return self.runner.run(["switch", branch], cwd=repo_path)

    def create_branch(self, repo_path: Path, branch: str) -> CommandResult:
        return self.runner.run(["switch", "-c", branch], cwd=repo_path)

    def merge_branch(self, repo_path: Path, branch: str) -> CommandResult:
        return self.runner.run(["merge", "--no-edit", branch], cwd=repo_path, timeout_seconds=300)

    def delete_branch(self, repo_path: Path, branch: str) -> CommandResult:
        return self.runner.run(["branch", "-d", branch], cwd=repo_path)

    def status_entries(self, repo_path: Path) -> list[GitStatusEntry]:
        result = self.runner.run(["status", "--porcelain=v1", "-z", "--untracked-files=all"], cwd=repo_path)
        return parse_porcelain_status(result.stdout) if result.ok else []

    def stage_all(self, repo_path: Path) -> CommandResult:
        return self.runner.run(["add", "-A"], cwd=repo_path)

    def stage_paths(self, repo_path: Path, paths: list[str]) -> CommandResult:
        return self.runner.run(["add", "-A", "--", *paths], cwd=repo_path)

    def commit(self, repo_path: Path, message: str) -> CommandResult:
        return self.runner.run(["commit", "-m", message], cwd=repo_path)

    def pull_rebase(self, repo_path: Path, branch: str) -> CommandResult:
        return self.runner.run(["pull", "--rebase", "origin", branch], cwd=repo_path, timeout_seconds=300)

    def push(self, repo_path: Path, branch: str) -> CommandResult:
        return self.runner.run(["push", "-u", "origin", branch], cwd=repo_path, timeout_seconds=300)

    def log_oneline(self, repo_path: Path) -> list[str]:
        result = self.runner.run(["log", "--oneline", "-50"], cwd=repo_path)
        return result.stdout.splitlines() if result.ok else []
