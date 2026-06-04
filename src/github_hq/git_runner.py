from __future__ import annotations

import subprocess
from pathlib import Path

from .models import CommandResult


class GitRunner:
    def __init__(self, executable: str = "git", timeout_seconds: int = 120) -> None:
        self.executable = executable
        self.timeout_seconds = timeout_seconds

    def run(self, args: list[str], cwd: Path | None, timeout_seconds: int | None = None) -> CommandResult:
        command = [self.executable, *args]
        try:
            completed = subprocess.run(
                command,
                cwd=str(cwd) if cwd else None,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_seconds or self.timeout_seconds,
                check=False,
            )
            return CommandResult(
                args=tuple(command),
                cwd=cwd,
                returncode=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
            )
        except FileNotFoundError as exc:
            return CommandResult(tuple(command), cwd, 127, "", str(exc))
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout if isinstance(exc.stdout, str) else ""
            stderr = exc.stderr if isinstance(exc.stderr, str) else ""
            return CommandResult(tuple(command), cwd, 124, stdout, stderr or "命令执行超时")
