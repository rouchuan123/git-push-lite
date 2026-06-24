import unittest

from github_hq.ui import (
    _change_tree_row_count,
    _layout_section_order,
    _output_text_row_count,
    _settings_section_tabs,
    _work_section_column_weights,
    _change_tree_column_widths,
)


class UiLayoutTests(unittest.TestCase):
    def test_action_row_is_before_expandable_work_area(self):
        sections = _layout_section_order()

        self.assertLess(sections.index("action"), sections.index("work"))

    def test_change_section_uses_two_thirds_of_original_width_weight(self):
        change_weight, config_weight = _work_section_column_weights()

        self.assertEqual(change_weight, 2)
        self.assertEqual(config_weight, 2)

    def test_change_tree_columns_are_compact_enough_for_windowed_mode(self):
        widths = _change_tree_column_widths()

        self.assertEqual(widths["name"], 180)
        self.assertEqual(widths["path"], 360)

    def test_change_and_output_sections_use_compact_row_counts(self):
        self.assertEqual(_change_tree_row_count(), 8)
        self.assertEqual(_output_text_row_count(), 6)

    def test_settings_are_split_into_compact_tabs(self):
        self.assertEqual(_settings_section_tabs(), ("身份 / 远程", "分支管理"))


if __name__ == "__main__":
    unittest.main()
