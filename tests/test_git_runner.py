import sys
import tempfile
import unittest
from pathlib import Path

from github_hq.git_runner import GitRunner


class GitRunnerTests(unittest.TestCase):
    def test_returns_command_result_for_success(self):
        runner = GitRunner(executable=sys.executable)
        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.run(["-c", "print('ok')"], cwd=Path(temp_dir))

        self.assertTrue(result.ok)
        self.assertEqual(result.stdout.strip(), "ok")

    def test_returns_command_result_for_failure(self):
        runner = GitRunner(executable=sys.executable)
        result = runner.run(["-c", "import sys; print('bad'); sys.exit(3)"], cwd=None)

        self.assertFalse(result.ok)
        self.assertEqual(result.returncode, 3)
        self.assertIn("bad", result.output)


if __name__ == "__main__":
    unittest.main()
