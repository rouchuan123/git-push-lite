import tempfile
import unittest
from pathlib import Path

from github_hq.gitignore_template import create_basic_gitignore


class GitignoreTemplateTests(unittest.TestCase):
    def test_creates_gitignore_when_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            created = create_basic_gitignore(repo)

            self.assertTrue(created)
            self.assertIn(".env", (repo / ".gitignore").read_text(encoding="utf-8"))

    def test_does_not_overwrite_existing_gitignore(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            gitignore = repo / ".gitignore"
            gitignore.write_text("custom\n", encoding="utf-8")

            created = create_basic_gitignore(repo)

            self.assertFalse(created)
            self.assertEqual(gitignore.read_text(encoding="utf-8"), "custom\n")


if __name__ == "__main__":
    unittest.main()
