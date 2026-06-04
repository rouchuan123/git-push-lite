from __future__ import annotations

from dataclasses import dataclass
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .app_config import AppConfig, add_recent_folder, load_config, save_config
from .git_runner import GitRunner
from .models import SelectionNode
from .repo_service import RepoService
from .status_parser import (
    build_selection_tree,
    refresh_parent_state,
    selected_paths,
    selection_marker,
    set_checked,
    toggle_node_selection,
)


def _should_open_node(node: SelectionNode, open_paths: set[str] | None) -> bool:
    if not node.is_dir:
        return False
    if open_paths is None:
        return "/" not in node.path
    return node.path in open_paths


@dataclass(frozen=True)
class StatusSummary:
    repository: str
    branch: str
    origin: str
    git: str
    selected: str


def _selected_change_count(selection_root: SelectionNode) -> int:
    return len(selected_paths(selection_root))


def _status_summary(
    repo_path: Path | None,
    branch: str,
    remote_url: str,
    git_available: bool,
    selection_root: SelectionNode,
) -> StatusSummary:
    repository = str(repo_path) if repo_path else "未选择仓库"
    branch_text = branch.strip() or "未设置分支"
    origin = "origin 已配置" if remote_url.strip() else "origin 未配置"
    git = "Git 可用" if git_available else "Git 不可用"
    selected_count = _selected_change_count(selection_root)
    selected = f"{selected_count} 个变更已选" if selected_count else "未选择变更"
    return StatusSummary(
        repository=repository,
        branch=branch_text,
        origin=origin,
        git=git,
        selected=selected,
    )


class GitHubHQApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("GitHub HQ")
        self.root.geometry("1100x760")
        self.config: AppConfig = load_config()
        self.repo_path: Path | None = None
        self.service = RepoService(GitRunner())
        self.selection_root = SelectionNode(name="", path="", is_dir=True)
        self.tree_nodes_by_id: dict[str, SelectionNode] = {}

        self.folder_var = tk.StringVar()
        self.branch_var = tk.StringVar(value=self.config.last_branch)
        self.name_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.identity_scope_var = tk.StringVar(value=self.config.last_identity_scope)
        self.remote_url_var = tk.StringVar()
        self.commit_message_var = tk.StringVar()
        self.status_var = tk.StringVar(value="请选择文件夹")
        self.git_available = False
        self.summary_repository_var = tk.StringVar(value="未选择仓库")
        self.summary_branch_var = tk.StringVar(value="未设置分支")
        self.summary_origin_var = tk.StringVar(value="origin 未配置")
        self.summary_git_var = tk.StringVar(value="Git 检测中")
        self.summary_selected_var = tk.StringVar(value="未选择变更")

        self._configure_styles()
        self._build_layout()
        self._refresh_recent_folders()
        self._check_git()

    def run(self) -> None:
        self.root.mainloop()

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        self.root.configure(bg="#f5f7fb")
        style.configure("App.TFrame", background="#f5f7fb")
        style.configure("Surface.TFrame", background="#ffffff")
        style.configure("Soft.TFrame", background="#f8fafc")
        style.configure("Card.TLabelframe", background="#ffffff", bordercolor="#d8e0ea", relief=tk.SOLID)
        style.configure(
            "Card.TLabelframe.Label",
            background="#ffffff",
            foreground="#1f2937",
            font=("Segoe UI", 10, "bold"),
        )
        style.configure("Title.TLabel", background="#f5f7fb", foreground="#111827", font=("Segoe UI", 18, "bold"))
        style.configure("Subtitle.TLabel", background="#f5f7fb", foreground="#64748b", font=("Segoe UI", 9))
        style.configure("SummaryTitle.TLabel", background="#ffffff", foreground="#64748b", font=("Segoe UI", 8))
        style.configure("SummaryValue.TLabel", background="#ffffff", foreground="#111827", font=("Segoe UI", 10, "bold"))
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), padding=(12, 7))
        style.configure("Secondary.TButton", padding=(10, 7))

    def _build_layout(self) -> None:
        main = ttk.Frame(self.root, style="App.TFrame", padding=14)
        main.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(main, style="App.TFrame")
        header.pack(fill=tk.X, pady=(0, 12))
        ttk.Label(header, text="GitHub HQ", style="Title.TLabel").pack(side=tk.LEFT)
        ttk.Label(
            header,
            text="轻量提交与推送工具",
            style="Subtitle.TLabel",
        ).pack(side=tk.LEFT, padx=(12, 0), pady=(8, 0))

        self._build_folder_section(main)
        self._build_summary_section(main)
        self._build_work_section(main)
        self._build_action_section(main)
        self._build_output_section(main)

    def _build_folder_section(self, parent: ttk.Frame) -> None:
        frame = ttk.Frame(parent, style="Surface.TFrame", padding=10)
        frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Entry(frame, textvariable=self.folder_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        ttk.Button(frame, text="选择文件夹", command=self._choose_folder, style="Secondary.TButton").pack(side=tk.LEFT)
        ttk.Label(frame, text=" 最近: ", background="#ffffff").pack(side=tk.LEFT)
        self.recent_combo = ttk.Combobox(frame, state="readonly", width=28)
        self.recent_combo.pack(side=tk.LEFT, padx=(0, 8))
        self.recent_combo.bind("<<ComboboxSelected>>", self._select_recent_folder)
        ttk.Button(frame, text="刷新", command=self._refresh_repository, style="Secondary.TButton").pack(side=tk.LEFT)

    def _build_summary_section(self, parent: ttk.Frame) -> None:
        frame = ttk.Frame(parent, style="App.TFrame")
        frame.pack(fill=tk.X, pady=(0, 10))
        cards = (
            ("仓库", self.summary_repository_var),
            ("分支", self.summary_branch_var),
            ("远程", self.summary_origin_var),
            ("Git", self.summary_git_var),
            ("选择", self.summary_selected_var),
        )
        for title, variable in cards:
            self._summary_card(frame, title, variable).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

    def _summary_card(self, parent: ttk.Frame, title: str, variable: tk.StringVar) -> ttk.Frame:
        card = ttk.Frame(parent, style="Surface.TFrame", padding=(10, 8))
        ttk.Label(card, text=title, style="SummaryTitle.TLabel").pack(anchor=tk.W)
        ttk.Label(card, textvariable=variable, style="SummaryValue.TLabel").pack(anchor=tk.W)
        return card

    def _build_work_section(self, parent: ttk.Frame) -> None:
        frame = ttk.Frame(parent, style="App.TFrame")
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        frame.columnconfigure(0, weight=3)
        frame.columnconfigure(1, weight=2)
        frame.rowconfigure(0, weight=1)

        self._build_change_section(frame)
        self._build_config_section(frame)

    def _build_config_section(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="身份 / 远程 / 分支", padding=10, style="Card.TLabelframe")
        frame.grid(row=0, column=1, sticky=tk.NSEW)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="用户名", background="#ffffff").grid(row=0, column=0, sticky=tk.W, pady=(0, 6))
        ttk.Entry(frame, textvariable=self.name_var).grid(row=0, column=1, sticky=tk.EW, pady=(0, 6))

        ttk.Label(frame, text="邮箱", background="#ffffff").grid(row=1, column=0, sticky=tk.W, pady=(0, 6))
        ttk.Entry(frame, textvariable=self.email_var).grid(row=1, column=1, sticky=tk.EW, pady=(0, 6))

        scope_frame = ttk.Frame(frame, style="Surface.TFrame")
        scope_frame.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(2, 10))
        ttk.Radiobutton(
            scope_frame,
            text="当前仓库",
            variable=self.identity_scope_var,
            value="repository",
        ).pack(side=tk.LEFT)
        ttk.Radiobutton(
            scope_frame,
            text="全局",
            variable=self.identity_scope_var,
            value="global",
        ).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(
            frame,
            text="保存身份",
            command=self._save_identity,
            style="Secondary.TButton",
        ).grid(row=3, column=0, columnspan=2, sticky=tk.EW, pady=(0, 14))

        ttk.Label(frame, text="origin", background="#ffffff").grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(0, 6))
        ttk.Entry(frame, textvariable=self.remote_url_var).grid(row=5, column=0, columnspan=2, sticky=tk.EW, pady=(0, 6))
        ttk.Button(
            frame,
            text="保存远程",
            command=self._save_origin,
            style="Secondary.TButton",
        ).grid(row=6, column=0, columnspan=2, sticky=tk.EW, pady=(0, 14))

        ttk.Label(frame, text="分支", background="#ffffff").grid(row=7, column=0, sticky=tk.W, pady=(0, 6))
        ttk.Entry(frame, textvariable=self.branch_var).grid(row=7, column=1, sticky=tk.EW, pady=(0, 6))

    def _build_change_section(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="变更选择", padding=10, style="Card.TLabelframe")
        frame.grid(row=0, column=0, sticky=tk.NSEW, padx=(0, 10))
        toolbar = ttk.Frame(frame)
        toolbar.pack(fill=tk.X, pady=(0, 6))
        ttk.Button(toolbar, text="全选", command=self._select_all_changes).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="清空", command=self._clear_change_selection).pack(side=tk.LEFT, padx=(6, 0))

        self.change_tree = ttk.Treeview(
            frame,
            columns=("state", "path"),
            show="tree headings",
            height=12,
            selectmode="none",
        )
        self.change_tree.heading("#0", text="名称")
        self.change_tree.heading("state", text="选择")
        self.change_tree.heading("path", text="路径")
        self.change_tree.column("#0", width=260, minwidth=180, stretch=True)
        self.change_tree.column("state", width=96, minwidth=88, stretch=False, anchor=tk.CENTER)
        self.change_tree.column("path", width=560, minwidth=260, stretch=True)
        self.change_tree.pack(fill=tk.BOTH, expand=True)
        self.change_tree.bind("<Button-1>", self._on_tree_click)

    def _build_action_section(self, parent: ttk.Frame) -> None:
        frame = ttk.Frame(parent, style="Surface.TFrame", padding=10)
        frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(frame, text="提交备注", background="#ffffff").pack(side=tk.LEFT)
        ttk.Entry(frame, textvariable=self.commit_message_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        self.commit_button = ttk.Button(frame, text="提交", command=self._commit, style="Secondary.TButton")
        self.push_button = ttk.Button(frame, text="推送", command=self._push, style="Secondary.TButton")
        self.pull_button = ttk.Button(frame, text="拉取远程更新", command=self._pull, style="Secondary.TButton")
        self.commit_push_button = ttk.Button(
            frame,
            text="提交并推送",
            command=self._commit_and_push,
            style="Primary.TButton",
        )
        for button in (self.commit_button, self.push_button, self.pull_button, self.commit_push_button):
            button.pack(side=tk.LEFT, padx=3)

    def _build_output_section(self, parent: ttk.Frame) -> None:
        frame = ttk.Frame(parent, style="App.TFrame")
        frame.pack(fill=tk.BOTH, expand=True)
        frame.columnconfigure(0, weight=3)
        frame.columnconfigure(1, weight=2)
        frame.rowconfigure(0, weight=1)

        output_frame = ttk.LabelFrame(frame, text="Git 输出", padding=10, style="Card.TLabelframe")
        output_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=(0, 10))
        self.output_text = tk.Text(
            output_frame,
            height=8,
            bg="#172033",
            fg="#e5edf7",
            insertbackground="#e5edf7",
            relief=tk.FLAT,
            padx=10,
            pady=8,
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)

        log_frame = ttk.LabelFrame(frame, text="最近提交", padding=10, style="Card.TLabelframe")
        log_frame.grid(row=0, column=1, sticky=tk.NSEW)
        self.log_list = tk.Listbox(log_frame, width=42, relief=tk.FLAT, highlightthickness=1)
        self.log_list.pack(fill=tk.BOTH, expand=True)
        self.log_list.bind("<Double-Button-1>", self._copy_selected_log)

    def _append_output(self, title: str, output: str = "") -> None:
        self.output_text.insert(tk.END, f"\n[{title}]\n")
        if output:
            self.output_text.insert(tk.END, output + "\n")
        self.output_text.see(tk.END)

    def _check_git(self) -> None:
        result = self.service.git_version()
        if result.ok:
            self.git_available = True
            self._append_output("Git 可用", result.stdout.strip())
            self._set_actions_enabled(True)
        else:
            self.git_available = False
            self.status_var.set("未检测到 Git，请安装 Git for Windows")
            self._append_output("Git 不可用", result.output)
            self._set_actions_enabled(False)
        self._refresh_summary()

    def _set_actions_enabled(self, enabled: bool) -> None:
        state = tk.NORMAL if enabled else tk.DISABLED
        for button in (self.commit_button, self.push_button, self.commit_push_button, self.pull_button):
            button.configure(state=state)

    def _choose_folder(self) -> None:
        folder = filedialog.askdirectory(title="选择仓库文件夹")
        if folder:
            self._load_folder(Path(folder))

    def _select_recent_folder(self, _event: object) -> None:
        value = self.recent_combo.get()
        if value:
            self._load_folder(Path(value))

    def _refresh_recent_folders(self) -> None:
        self.recent_combo["values"] = self.config.recent_folders

    def _refresh_summary(self) -> None:
        summary = _status_summary(
            repo_path=self.repo_path,
            branch=self.branch_var.get(),
            remote_url=self.remote_url_var.get(),
            git_available=self.git_available,
            selection_root=self.selection_root,
        )
        self.summary_repository_var.set(summary.repository)
        self.summary_branch_var.set(summary.branch)
        self.summary_origin_var.set(summary.origin)
        self.summary_git_var.set(summary.git)
        self.summary_selected_var.set(summary.selected)

    def _load_folder(self, folder: Path) -> None:
        self.repo_path = folder
        self.folder_var.set(str(folder))
        add_recent_folder(self.config, str(folder))
        save_config(self.config)
        self._refresh_recent_folders()
        self._refresh_repository()

    def _refresh_repository(self) -> None:
        if not self.repo_path:
            self.status_var.set("请选择文件夹")
            self._refresh_summary()
            return
        if not self.service.is_repository(self.repo_path):
            if messagebox.askyesno("初始化仓库", "当前文件夹还不是 Git 仓库，是否执行 git init？"):
                result = self.service.init_repository(self.repo_path)
                self._append_output("初始化仓库", result.output or "git init 完成")
            else:
                self.status_var.set("当前文件夹不是 Git 仓库")
                return

        branch = self.service.current_branch(self.repo_path) or self.branch_var.get()
        self.branch_var.set(branch or "main")
        self.name_var.set(self.service.get_config(self.repo_path, "user.name"))
        self.email_var.set(self.service.get_config(self.repo_path, "user.email"))
        self.remote_url_var.set(self.service.get_origin_url(self.repo_path))
        self.status_var.set(
            f"仓库: {self.repo_path} | 分支: {self.branch_var.get()} | origin: {self.remote_url_var.get() or '未配置'}"
        )
        self._refresh_changes()
        self._refresh_logs()
        self._refresh_summary()

    def _save_identity(self) -> None:
        if not self.repo_path:
            messagebox.showwarning("缺少仓库", "请先选择文件夹")
            return
        name = self.name_var.get().strip()
        email = self.email_var.get().strip()
        if not name or not email:
            messagebox.showwarning("缺少身份", "请填写用户名和邮箱")
            return
        results = self.service.set_identity(self.repo_path, name, email, self.identity_scope_var.get())
        self.config.last_identity_scope = self.identity_scope_var.get()
        save_config(self.config)
        self._append_output("保存身份", "\n".join(result.output for result in results if result.output) or "身份已保存")

    def _save_origin(self) -> None:
        if not self.repo_path:
            messagebox.showwarning("缺少仓库", "请先选择文件夹")
            return
        result = self.service.configure_origin(self.repo_path, self.remote_url_var.get())
        if result.ok:
            self._append_output("保存远程", "origin 已更新")
        else:
            messagebox.showerror("远程地址错误", result.output)
            self._append_output("保存远程失败", result.output)

    def _refresh_changes(self) -> None:
        if not self.repo_path:
            return
        entries = self.service.status_entries(self.repo_path)
        self.selection_root = build_selection_tree(entries)
        self._render_change_tree()

    def _render_change_tree(self) -> None:
        open_paths = self._current_open_paths() if self.change_tree.get_children() else None
        self.change_tree.delete(*self.change_tree.get_children())
        self.tree_nodes_by_id.clear()
        for child in self.selection_root.children:
            self._insert_tree_node("", child, open_paths)

    def _insert_tree_node(self, parent_id: str, node: SelectionNode, open_paths: set[str] | None) -> None:
        marker = selection_marker(node)
        item_id = self.change_tree.insert(
            parent_id,
            tk.END,
            text=node.name,
            values=(marker, node.path),
            open=_should_open_node(node, open_paths),
        )
        self.tree_nodes_by_id[item_id] = node
        for child in node.children:
            self._insert_tree_node(item_id, child, open_paths)

    def _current_open_paths(self) -> set[str]:
        paths: set[str] = set()
        for item_id, node in self.tree_nodes_by_id.items():
            if node.is_dir and self.change_tree.exists(item_id) and self.change_tree.item(item_id, "open"):
                paths.add(node.path)
        return paths

    def _select_all_changes(self) -> None:
        self._set_all_changes_checked(True)

    def _clear_change_selection(self) -> None:
        self._set_all_changes_checked(False)

    def _set_all_changes_checked(self, checked: bool) -> None:
        set_checked(self.selection_root, checked)
        refresh_parent_state(self.selection_root)
        self._render_change_tree()
        self._refresh_summary()

    def _refresh_logs(self) -> None:
        self.log_list.delete(0, tk.END)
        if not self.repo_path:
            return
        for line in self.service.log_oneline(self.repo_path):
            self.log_list.insert(tk.END, line)

    def _on_tree_click(self, event: tk.Event) -> str | None:
        region = self.change_tree.identify("region", event.x, event.y)
        if region in {"heading", "separator"}:
            return
        item_id = self.change_tree.identify_row(event.y)
        if not item_id:
            return
        element = self.change_tree.identify("element", event.x, event.y)
        if element == "Treeitem.indicator":
            return
        node = self.tree_nodes_by_id[item_id]
        toggle_node_selection(node)
        refresh_parent_state(self.selection_root)
        self._render_change_tree()
        self._refresh_summary()
        return "break"

    def _selected_paths(self) -> list[str]:
        return selected_paths(self.selection_root)

    def _ensure_branch(self) -> bool:
        if not self.repo_path:
            messagebox.showwarning("缺少仓库", "请先选择文件夹")
            return False
        branch = self.branch_var.get().strip()
        if not branch:
            messagebox.showwarning("缺少分支", "请填写分支名")
            return False
        self.config.last_branch = branch
        save_config(self.config)
        current = self.service.current_branch(self.repo_path)
        if current == branch:
            return True
        if self.service.branch_exists(self.repo_path, branch):
            result = self.service.switch_branch(self.repo_path, branch)
            self._append_output("切换分支", result.output or f"已切换到 {branch}")
            return result.ok
        if messagebox.askyesno("创建分支", f"分支 {branch} 不存在，是否创建并切换？"):
            result = self.service.create_branch(self.repo_path, branch)
            self._append_output("创建分支", result.output or f"已创建 {branch}")
            return result.ok
        return False

    def _commit(self) -> bool:
        if not self.repo_path:
            messagebox.showwarning("缺少仓库", "请先选择文件夹")
            return False
        if not self._ensure_branch():
            return False
        message = self.commit_message_var.get().strip()
        if not message:
            messagebox.showwarning("缺少备注", "请填写提交备注")
            return False
        paths = self._selected_paths()
        if not paths:
            messagebox.showwarning("未选择变更", "请勾选要提交的文件或文件夹")
            return False
        stage_result = self.service.stage_paths(self.repo_path, paths)
        self._append_output("添加变更", stage_result.output or "已添加选中变更")
        if not stage_result.ok:
            return False
        commit_result = self.service.commit(self.repo_path, message)
        self._append_output("创建提交", commit_result.output or "提交完成")
        self._refresh_repository()
        return commit_result.ok

    def _push(self) -> bool:
        if not self.repo_path:
            messagebox.showwarning("缺少仓库", "请先选择文件夹")
            return False
        if not self._ensure_branch():
            return False
        result = self.service.push(self.repo_path, self.branch_var.get().strip())
        self._append_output("推送", result.output or "推送完成")
        self._refresh_logs()
        if not result.ok:
            messagebox.showerror("推送失败", result.output)
        return result.ok

    def _commit_and_push(self) -> None:
        if self._commit():
            self._push()

    def _pull(self) -> None:
        if not self.repo_path:
            messagebox.showwarning("缺少仓库", "请先选择文件夹")
            return
        if not self._ensure_branch():
            return
        result = self.service.pull_rebase(self.repo_path, self.branch_var.get().strip())
        self._append_output("拉取远程更新", result.output or "拉取完成")
        if not result.ok:
            messagebox.showerror("拉取失败", result.output)
        self._refresh_repository()

    def _copy_selected_log(self, _event: object) -> None:
        selection = self.log_list.curselection()
        if selection:
            value = self.log_list.get(selection[0])
            self.root.clipboard_clear()
            self.root.clipboard_append(value)
            self._append_output("复制日志", value)
