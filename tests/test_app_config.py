import tempfile
import unittest
from pathlib import Path

from github_hq.app_config import AppConfig, add_recent_folder, load_config, save_config


class AppConfigTests(unittest.TestCase):
    def test_saves_and_loads_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.json"
            save_config(AppConfig(recent_folders=["C:/repo"], last_identity_scope="global", last_branch="main"), path)

            loaded = load_config(path)

        self.assertEqual(loaded.recent_folders, ["C:/repo"])
        self.assertEqual(loaded.last_identity_scope, "global")
        self.assertEqual(loaded.last_branch, "main")

    def test_recent_folders_keep_latest_five(self):
        config = AppConfig()
        for index in range(7):
            add_recent_folder(config, f"C:/repo-{index}")

        self.assertEqual(config.recent_folders, ["C:/repo-6", "C:/repo-5", "C:/repo-4", "C:/repo-3", "C:/repo-2"])


if __name__ == "__main__":
    unittest.main()
