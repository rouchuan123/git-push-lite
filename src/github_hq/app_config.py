from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class AppConfig:
    recent_folders: list[str] = field(default_factory=list)
    last_identity_scope: str = "repository"
    last_branch: str = "main"


def default_config_path() -> Path:
    appdata = os.environ.get("APPDATA")
    base = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
    return base / "GitHub HQ" / "config.json"


def load_config(path: Path | None = None) -> AppConfig:
    config_path = path or default_config_path()
    if not config_path.exists():
        return AppConfig()
    data = json.loads(config_path.read_text(encoding="utf-8"))
    return AppConfig(
        recent_folders=list(data.get("recent_folders", []))[:5],
        last_identity_scope=data.get("last_identity_scope", "repository"),
        last_branch=data.get("last_branch", "main"),
    )


def save_config(config: AppConfig, path: Path | None = None) -> None:
    config_path = path or default_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(asdict(config), ensure_ascii=False, indent=2), encoding="utf-8")


def add_recent_folder(config: AppConfig, folder: str) -> None:
    normalized = folder.replace("\\", "/")
    config.recent_folders = [item for item in config.recent_folders if item != normalized]
    config.recent_folders.insert(0, normalized)
    config.recent_folders = config.recent_folders[:5]
