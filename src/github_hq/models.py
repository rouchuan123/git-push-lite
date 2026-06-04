from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class CommandResult:
    args: tuple[str, ...]
    cwd: Path | None
    returncode: int
    stdout: str = ""
    stderr: str = ""

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    @property
    def output(self) -> str:
        return "\n".join(part for part in (self.stdout.strip(), self.stderr.strip()) if part)


@dataclass(frozen=True)
class GitStatusEntry:
    path: str
    index_status: str
    worktree_status: str
    original_path: str | None = None

    @property
    def is_deleted(self) -> bool:
        return self.index_status == "D" or self.worktree_status == "D"

    @property
    def display_status(self) -> str:
        if self.index_status == "?" and self.worktree_status == "?":
            return "未跟踪"
        if self.is_deleted:
            return "删除"
        if self.original_path:
            return "重命名"
        return "修改"


@dataclass
class SelectionNode:
    name: str
    path: str
    is_dir: bool
    checked: bool = False
    partial: bool = False
    children: list["SelectionNode"] = field(default_factory=list)
