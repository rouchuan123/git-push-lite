import unittest

from github_hq.status_parser import (
    build_selection_tree,
    parse_porcelain_status,
    selected_paths,
    selection_marker,
    set_checked,
    toggle_node_selection,
)


class StatusParserTests(unittest.TestCase):
    def test_parses_modified_untracked_deleted_and_renamed(self):
        entries = parse_porcelain_status(
            " M src/main.py\n"
            "?? README.md\n"
            " D old.txt\n"
            "R  old_name.txt -> new_name.txt\n"
        )

        self.assertEqual([entry.path for entry in entries], ["src/main.py", "README.md", "old.txt", "new_name.txt"])
        self.assertEqual(entries[3].original_path, "old_name.txt")

    def test_parses_nul_porcelain_paths_as_real_paths(self):
        entries = parse_porcelain_status("?? 测试文件夹/文件.txt\0")

        self.assertEqual([entry.path for entry in entries], ["测试文件夹/文件.txt"])

    def test_decodes_quoted_non_ascii_paths(self):
        entries = parse_porcelain_status(
            '?? "\\346\\265\\213\\350\\257\\225\\346\\226\\207\\344\\273\\266\\345\\244\\271/'
            '\\346\\226\\207\\344\\273\\266.txt"\n'
        )

        self.assertEqual([entry.path for entry in entries], ["测试文件夹/文件.txt"])

    def test_folder_checkbox_selects_children(self):
        entries = parse_porcelain_status(" M src/main.py\n M src/git_runner.py\n?? README.md\n")
        tree = build_selection_tree(entries)
        src_node = next(child for child in tree.children if child.name == "src")

        set_checked(src_node, True)

        self.assertEqual(selected_paths(tree), ["src/git_runner.py", "src/main.py"])

    def test_mixed_folder_and_file_selection(self):
        entries = parse_porcelain_status(" M src/main.py\n M src/git_runner.py\n?? README.md\n")
        tree = build_selection_tree(entries)
        src_node = next(child for child in tree.children if child.name == "src")
        readme_node = next(child for child in tree.children if child.name == "README.md")

        set_checked(src_node, True)
        set_checked(readme_node, True)

        self.assertEqual(selected_paths(tree), ["README.md", "src/git_runner.py", "src/main.py"])

    def test_selection_marker_uses_readable_labels(self):
        tree = build_selection_tree(parse_porcelain_status(" M src/main.py\n"))
        src_node = tree.children[0]

        self.assertEqual(selection_marker(src_node), "☐ 未选")
        set_checked(src_node, True)
        self.assertEqual(selection_marker(src_node), "☑ 已选")
        src_node.partial = True
        self.assertEqual(selection_marker(src_node), "◩ 部分")

    def test_toggle_node_selection_selects_partial_folder(self):
        tree = build_selection_tree(parse_porcelain_status(" M src/main.py\n M src/git_runner.py\n"))
        src_node = tree.children[0]
        src_node.partial = True

        toggle_node_selection(src_node)

        self.assertEqual(selected_paths(tree), ["src/git_runner.py", "src/main.py"])


if __name__ == "__main__":
    unittest.main()
