import unittest
from pathlib import Path

from github_hq.models import SelectionNode
from github_hq.ui import _selected_change_count, _status_summary


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


if __name__ == "__main__":
    unittest.main()
