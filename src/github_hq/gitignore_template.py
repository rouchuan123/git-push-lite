from __future__ import annotations

from pathlib import Path


BASIC_GITIGNORE = """# GitHub HQ basic ignores
.env
.venv/
venv/
__pycache__/
*.pyc
node_modules/
dist/
build/
.DS_Store
Thumbs.db
"""


def create_basic_gitignore(repo_path: Path) -> bool:
    gitignore_path = repo_path / ".gitignore"
    if gitignore_path.exists():
        return False
    gitignore_path.write_text(BASIC_GITIGNORE, encoding="utf-8")
    return True
