import unittest
from pathlib import Path

from github_hq.models import SelectionNode
from github_hq.ui import GitHubHQApp, _selected_change_count, _status_summary


class DummyVar:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class UiSummaryTests(unittest.TestCase):
    def test_selected_change_count_counts_checked_files(self):
        root = SelectionNode(
            name="",
            path="",
            is_dir=True,
            children=[
                SelectionNode(name="README.md", path="README.md", is_dir=False, checked=True),
                SelectionNode(
                    name="src",
                    path="src",
                    is_dir=True,
                    children=[
                        SelectionNode(name="ui.py", path="src/ui.py", is_dir=False, checked=True),
                        SelectionNode(name="main.py", path="src/main.py", is_dir=False, checked=False),
                    ],
                ),
            ],
        )

        self.assertEqual(_selected_change_count(root), 2)

    def test_status_summary_for_empty_app_state(self):
        root = SelectionNode(name="", path="", is_dir=True)

        summary = _status_summary(
            repo_path=None,
            branch="",
            remote_url="",
            git_available=False,
            selection_root=root,
        )

        self.assertEqual(summary.repository, "未选择仓库")
        self.assertEqual(summary.branch, "未设置分支")
        self.assertEqual(summary.origin, "origin 未配置")
        self.assertEqual(summary.git, "Git 不可用")
        self.assertEqual(summary.selected, "未选择变更")

    def test_status_summary_for_ready_repository(self):
        root = SelectionNode(
            name="",
            path="",
            is_dir=True,
            children=[
                SelectionNode(name="README.md", path="README.md", is_dir=False, checked=True),
            ],
        )

        summary = _status_summary(
            repo_path=Path("D:/work/project"),
            branch="main",
            remote_url="git@github.com:owner/repo.git",
            git_available=True,
            selection_root=root,
        )

        self.assertEqual(summary.repository, "D:\\work\\project")
        self.assertEqual(summary.branch, "main")
        self.assertEqual(summary.origin, "origin 已配置")
        self.assertEqual(summary.git, "Git 可用")
        self.assertEqual(summary.selected, "1 个变更已选")

    def test_refresh_summary_updates_dashboard_variables(self):
        selection_root = SelectionNode(
            name="",
            path="",
            is_dir=True,
            children=[
                SelectionNode(name="README.md", path="README.md", is_dir=False, checked=True),
            ],
        )
        app = object.__new__(GitHubHQApp)
        app.repo_path = Path("D:/work/project")
        app.branch_var = DummyVar("main")
        app.remote_url_var = DummyVar("git@github.com:owner/repo.git")
        app.git_available = True
        app.selection_root = selection_root
        app.summary_repository_var = DummyVar()
        app.summary_branch_var = DummyVar()
        app.summary_origin_var = DummyVar()
        app.summary_git_var = DummyVar()
        app.summary_selected_var = DummyVar()

        expected = _status_summary(
            repo_path=app.repo_path,
            branch=app.branch_var.get(),
            remote_url=app.remote_url_var.get(),
            git_available=app.git_available,
            selection_root=app.selection_root,
        )

        app._refresh_summary()

        self.assertEqual(app.summary_repository_var.value, expected.repository)
        self.assertEqual(app.summary_branch_var.value, expected.branch)
        self.assertEqual(app.summary_origin_var.value, expected.origin)
        self.assertEqual(app.summary_git_var.value, expected.git)
        self.assertEqual(app.summary_selected_var.value, expected.selected)


if __name__ == "__main__":
    unittest.main()
