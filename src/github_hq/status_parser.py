from __future__ import annotations

from .models import GitStatusEntry, SelectionNode


def parse_porcelain_status(output: str) -> list[GitStatusEntry]:
    if "\0" in output:
        return _parse_nul_porcelain_status(output)

    entries: list[GitStatusEntry] = []
    for raw_line in output.splitlines():
        if not raw_line:
            continue
        index_status = raw_line[0]
        worktree_status = raw_line[1]
        path_text = raw_line[3:]
        original_path = None
        path = path_text
        if " -> " in path_text:
            original_path, path = path_text.split(" -> ", 1)
            original_path = _normalize_path(original_path)
        path = _normalize_path(path)
        entries.append(
            GitStatusEntry(
                path=path,
                index_status=index_status,
                worktree_status=worktree_status,
                original_path=original_path,
            )
        )
    return entries


def _parse_nul_porcelain_status(output: str) -> list[GitStatusEntry]:
    entries: list[GitStatusEntry] = []
    records = [record for record in output.split("\0") if record]
    index = 0
    while index < len(records):
        record = records[index]
        if len(record) < 4:
            index += 1
            continue
        index_status = record[0]
        worktree_status = record[1]
        path = _normalize_path(record[3:])
        original_path = None
        if (index_status in {"R", "C"} or worktree_status in {"R", "C"}) and index + 1 < len(records):
            original_path = _normalize_path(records[index + 1])
            index += 1
        entries.append(
            GitStatusEntry(
                path=path,
                index_status=index_status,
                worktree_status=worktree_status,
                original_path=original_path,
            )
        )
        index += 1
    return entries


def _normalize_path(path: str) -> str:
    return _decode_git_path(path).replace("\\", "/")


def _decode_git_path(path: str) -> str:
    if len(path) < 2 or not path.startswith('"') or not path.endswith('"'):
        return path
    return _decode_c_quoted_path(path[1:-1])


def _decode_c_quoted_path(path: str) -> str:
    output = bytearray()
    index = 0
    while index < len(path):
        char = path[index]
        if char != "\\":
            output.extend(char.encode("utf-8"))
            index += 1
            continue

        index += 1
        if index >= len(path):
            output.extend(b"\\")
            break

        escaped = path[index]
        if escaped in "01234567":
            digits = [escaped]
            index += 1
            while index < len(path) and len(digits) < 3 and path[index] in "01234567":
                digits.append(path[index])
                index += 1
            output.append(int("".join(digits), 8))
            continue

        replacements = {
            "a": b"\a",
            "b": b"\b",
            "f": b"\f",
            "n": b"\n",
            "r": b"\r",
            "t": b"\t",
            "v": b"\v",
            "\\": b"\\",
            '"': b'"',
        }
        output.extend(replacements.get(escaped, escaped.encode("utf-8")))
        index += 1
    return output.decode("utf-8", errors="replace")


def build_selection_tree(entries: list[GitStatusEntry]) -> SelectionNode:
    root = SelectionNode(name="", path="", is_dir=True)
    for entry in sorted(entries, key=lambda item: item.path):
        parts = entry.path.split("/")
        current = root
        prefix: list[str] = []
        for part in parts[:-1]:
            prefix.append(part)
            child_path = "/".join(prefix)
            child = _find_child(current, part, is_dir=True)
            if child is None:
                child = SelectionNode(name=part, path=child_path, is_dir=True)
                current.children.append(child)
            current = child
        current.children.append(SelectionNode(name=parts[-1], path=entry.path, is_dir=False))
    return root


def set_checked(node: SelectionNode, checked: bool) -> None:
    node.checked = checked
    node.partial = False
    for child in node.children:
        set_checked(child, checked)


def refresh_parent_state(node: SelectionNode) -> None:
    for child in node.children:
        refresh_parent_state(child)
    if not node.children:
        return
    checked_count = sum(1 for child in node.children if child.checked and not child.partial)
    partial_count = sum(1 for child in node.children if child.partial)
    if checked_count == len(node.children) and partial_count == 0:
        node.checked = True
        node.partial = False
    elif checked_count == 0 and partial_count == 0:
        node.checked = False
        node.partial = False
    else:
        node.checked = False
        node.partial = True


def selected_paths(node: SelectionNode) -> list[str]:
    paths: list[str] = []
    _collect_selected_leaf_paths(node, paths)
    return sorted(paths)


def selection_marker(node: SelectionNode) -> str:
    if node.partial:
        return "◩ 部分"
    if node.checked:
        return "☑ 已选"
    return "☐ 未选"


def toggle_node_selection(node: SelectionNode) -> None:
    set_checked(node, not node.checked or node.partial)


def _collect_selected_leaf_paths(node: SelectionNode, paths: list[str]) -> None:
    if not node.is_dir and node.checked:
        paths.append(node.path)
        return
    for child in node.children:
        _collect_selected_leaf_paths(child, paths)


def _find_child(node: SelectionNode, name: str, is_dir: bool) -> SelectionNode | None:
    for child in node.children:
        if child.name == name and child.is_dir == is_dir:
            return child
    return None
