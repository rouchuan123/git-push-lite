import unittest
from pathlib import Path

from github_hq.models import CommandResult
from github_hq.repo_service import RepoService


class FakeRunner:
    def __init__(self):
        self.calls = []
        self.results = []

    def queue(self, result):
        self.results.append(result)

    def run(self, args, cwd, timeout_seconds=None):
        self.calls.append((list(args), cwd))
        if self.results:
            return self.results.pop(0)
        return CommandResult(tuple(["git", *args]), cwd, 0, "", "")


class RepoServiceTests(unittest.TestCase):
    def test_configures_origin_by_adding_missing_remote(self):
        runner = FakeRunner()
        runner.queue(CommandResult(("git", "remote", "get-url", "origin"), Path("C:/repo"), 2, "", "missing"))
        service = RepoService(runner)

        service.configure_origin(Path("C:/repo"), "https://github.com/octo/repo.git")

        self.assertEqual(runner.calls[-1][0], ["remote", "add", "origin", "https://github.com/octo/repo.git"])

    def test_stages_selected_paths(self):
        runner = FakeRunner()
        service = RepoService(runner)

        service.stage_paths(Path("C:/repo"), ["README.md", "src/main.py"])

        self.assertEqual(runner.calls[0][0], ["add", "-A", "--", "README.md", "src/main.py"])

    def test_commits_with_message(self):
        runner = FakeRunner()
        service = RepoService(runner)

        service.commit(Path("C:/repo"), "第一次提交")

        self.assertEqual(runner.calls[0][0], ["commit", "-m", "第一次提交"])

    def test_pushes_with_upstream(self):
        runner = FakeRunner()
        service = RepoService(runner)

        service.push(Path("C:/repo"), "main")

        self.assertEqual(runner.calls[0][0], ["push", "-u", "origin", "main"])

    def test_status_entries_request_all_untracked_files(self):
        runner = FakeRunner()
        service = RepoService(runner)

        service.status_entries(Path("C:/repo"))

        self.assertEqual(runner.calls[0][0], ["status", "--porcelain=v1", "-z", "--untracked-files=all"])

    def test_lists_local_branches_with_current_marker_removed(self):
        runner = FakeRunner()
        runner.queue(CommandResult(("git", "branch", "--format", "%(refname:short)"), Path("C:/repo"), 0, "  main\n* feature/login\n  release\n", ""))
        service = RepoService(runner)

        branches = service.list_branches(Path("C:/repo"))

        self.assertEqual(branches, ["main", "feature/login", "release"])
        self.assertEqual(runner.calls[0][0], ["branch", "--format", "%(refname:short)"])

    def test_merges_selected_branch_into_current_branch(self):
        runner = FakeRunner()
        service = RepoService(runner)

        service.merge_branch(Path("C:/repo"), "feature/login")

        self.assertEqual(runner.calls[0][0], ["merge", "--no-edit", "feature/login"])

    def test_deletes_branch_safely(self):
        runner = FakeRunner()
        service = RepoService(runner)

        service.delete_branch(Path("C:/repo"), "feature/login")

        self.assertEqual(runner.calls[0][0], ["branch", "-d", "feature/login"])


if __name__ == "__main__":
    unittest.main()
