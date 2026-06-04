import unittest

from github_hq.models import SelectionNode
from github_hq.ui import _should_open_node


class UiTreeStateTests(unittest.TestCase):
    def test_top_level_folders_open_on_first_render(self):
        node = SelectionNode(name="src", path="src", is_dir=True)

        self.assertTrue(_should_open_node(node, open_paths=None))

    def test_nested_folders_do_not_open_on_first_render(self):
        node = SelectionNode(name="github_hq", path="src/github_hq", is_dir=True)

        self.assertFalse(_should_open_node(node, open_paths=None))

    def test_existing_open_paths_are_preserved_on_rerender(self):
        open_node = SelectionNode(name="src", path="src", is_dir=True)
        closed_node = SelectionNode(name="docs", path="docs", is_dir=True)

        self.assertTrue(_should_open_node(open_node, open_paths={"src"}))
        self.assertFalse(_should_open_node(closed_node, open_paths={"src"}))

    def test_files_are_never_opened_as_folders(self):
        node = SelectionNode(name="main.py", path="src/main.py", is_dir=False)

        self.assertFalse(_should_open_node(node, open_paths={"src/main.py"}))


if __name__ == "__main__":
    unittest.main()
