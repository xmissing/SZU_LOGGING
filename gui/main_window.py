"""主窗口：配置面板、运行日志、公告列表，整合爬虫核心。"""

import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime

from config import Config
from core.crawler import SzuCrawler
from gui.detail_window import DetailWindow
from gui.theme import Colors, Fonts, apply_theme


class MainWindow:
    """应用主窗口，负责 UI 布局与用户交互。"""

    def __init__(self):
        Config.load_settings()

        self.root = tk.Tk()
        self.root.title("深圳大学公告监控系统")
        self.root.geometry("1180x800")
        self.root.minsize(1000, 700)
        self.root.configure(bg=Colors.BG_MAIN)
        apply_theme(self.root)

        self.data_cache = []
        self.content_cache = {}

        self._build_header()
        self._build_config_card()
        self._build_action_bar()
        self._build_log_card()
        self._build_tree_card()
        self._build_status_bar()

        self._restore_config_fields()
        self._load_sample()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ==================================================================
    #  UI 构建
    # ==================================================================
    def _build_header(self):
        """顶部标题栏。"""
        bar = ttk.Frame(self.root, style="Bg.TFrame")
        bar.pack(fill="x", padx=16, pady=(16, 0))

        # 左侧：图标 + 标题
        left = ttk.Frame(bar, style="Bg.TFrame")
        left.pack(side="left")

        icon_label = tk.Label(
            left,
            text="\U0001F4CB",
            font=(Fonts.FAMILY, 24),
            bg=Colors.BG_MAIN,
            fg=Colors.PRIMARY,
        )
        icon_label.pack(side="left", padx=(0, 10))

        title_box = ttk.Frame(left, style="Bg.TFrame")
        title_box.pack(side="left")
        tk.Label(
            title_box,
            text="深圳大学公告监控系统",
            font=Fonts.TITLE,
            bg=Colors.BG_MAIN,
            fg=Colors.TEXT_PRIMARY,
        ).pack(anchor="w")
        tk.Label(
            title_box,
            text="SZU Board Monitor  ·  自动抓取  ·  去重存储  ·  邮件通知",
            font=Fonts.SMALL,
            bg=Colors.BG_MAIN,
            fg=Colors.TEXT_SECONDARY,
        ).pack(anchor="w")

    # ------------------------------------------------------------------
    def _build_config_card(self):
        """配置区域——卡片式。"""
        card = ttk.Frame(self.root, style="Card.TFrame")
        card.pack(fill="x", padx=16, pady=(12, 6))

        # 卡片内边距容器
        inner = ttk.Frame(card, style="Card.TFrame")
        inner.pack(fill="x", padx=20, pady=16)

        # ---- 区域标题 ----
        header_row = ttk.Frame(inner, style="Card.TFrame")
        header_row.pack(fill="x", pady=(0, 12))
        tk.Label(
            header_row,
            text="\u2699\ufe0f  基本配置",
            font=Fonts.SUBTITLE,
            bg=Colors.BG_CARD,
            fg=Colors.PRIMARY,
        ).pack(side="left")

        # ---- 账号 / 密码 / 关键词 ----
        row1 = ttk.Frame(inner, style="Card.TFrame")
        row1.pack(fill="x", pady=(0, 10))

        self._add_label_entry(row1, "账号 *", "account_entry", width=18)
        self._add_label_entry(row1, "密码 *", "password_entry", width=18, show="*")
        self._add_label_entry(row1, "关键词 *", "keyword_entry", width=18)

        # ---- 数据库 ----
        row2 = ttk.Frame(inner, style="Card.TFrame")
        row2.pack(fill="x", pady=(0, 10))

        self.db_var = tk.IntVar()
        ttk.Checkbutton(
            row2,
            text="启用数据库",
            variable=self.db_var,
            style="Card.TCheckbutton",
            command=self._toggle_db,
        ).pack(side="left", padx=(0, 16))
        self._add_label_entry(row2, "主机", "db_host", width=12, default="localhost")
        self._add_label_entry(row2, "用户", "db_user", width=10, default="root")
        self._add_label_entry(row2, "密码", "db_pass", width=10, show="*")
        self._add_label_entry(row2, "库名", "db_name", width=10, default="szu_board")

        # ---- 邮件 ----
        row3 = ttk.Frame(inner, style="Card.TFrame")
        row3.pack(fill="x")

        self.email_var = tk.IntVar()
        ttk.Checkbutton(
            row3,
            text="启用邮件",
            variable=self.email_var,
            style="Card.TCheckbutton",
            command=self._toggle_email,
        ).pack(side="left", padx=(0, 16))
        self._add_label_entry(row3, "发件人", "sender_entry", width=16)
        self._add_label_entry(row3, "授权码", "sender_pass", width=14, show="*")
        self._add_label_entry(row3, "收件人", "receiver_entry", width=16)

        self._toggle_db()
        self._toggle_email()

    # ------------------------------------------------------------------
    def _build_action_bar(self):
        """操作按钮行。"""
        bar = ttk.Frame(self.root, style="Bg.TFrame")
        bar.pack(fill="x", padx=16, pady=(0, 8))

        self.run_btn = ttk.Button(
            bar, text="\U0001F680  运行爬虫", style="Primary.TButton",
            command=self._run_crawler,
        )
        self.run_btn.pack(side="left", padx=(0, 8))

        self.clear_btn = ttk.Button(
            bar, text="\U0001F9F9  清空数据", style="Warning.TButton",
            command=self._clear_data,
        )
        self.clear_btn.pack(side="left", padx=(0, 16))

        # 状态指示
        self.status_dot = tk.Label(
            bar, text="\u25CF", font=(Fonts.FAMILY, 14),
            bg=Colors.BG_MAIN, fg=Colors.TEXT_SECONDARY,
        )
        self.status_dot.pack(side="left", padx=(0, 6))
        self.status_label = tk.Label(
            bar, text="就绪",
            font=Fonts.SMALL_BOLD,
            bg=Colors.BG_MAIN, fg=Colors.TEXT_SECONDARY,
        )
        self.status_label.pack(side="left")

    # ------------------------------------------------------------------
    def _build_log_card(self):
        """运行日志——深色风格。"""
        card = ttk.Frame(self.root, style="Card.TFrame")
        card.pack(fill="x", padx=16, pady=(0, 6))

        header = ttk.Frame(card, style="Card.TFrame")
        header.pack(fill="x", padx=20, pady=(12, 0))
        tk.Label(
            header,
            text="\U0001F4DD  运行日志",
            font=Fonts.SUBTITLE,
            bg=Colors.BG_CARD,
            fg=Colors.PRIMARY,
        ).pack(side="left")

        self.log_text = scrolledtext.ScrolledText(
            card,
            height=7,
            font=Fonts.LOG,
            bg=Colors.BG_LOG,
            fg=Colors.TEXT_LOG,
            relief="flat",
            padx=14,
            pady=10,
            insertbackground=Colors.TEXT_LOG,
            selectbackground=Colors.PRIMARY,
            wrap="word",
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=Colors.BORDER,
            highlightcolor=Colors.BORDER,
        )
        self.log_text.pack(fill="x", padx=20, pady=(8, 16))

        # 配置 tag 颜色
        self.log_text.tag_config("time", foreground=Colors.TEXT_LOG_TIME)
        self.log_text.tag_config("error", foreground=Colors.DANGER)
        self.log_text.tag_config("success", foreground=Colors.SUCCESS)

    # ------------------------------------------------------------------
    def _build_tree_card(self):
        """公告列表——表格区域。"""
        card = ttk.Frame(self.root, style="Card.TFrame")
        card.pack(fill="both", expand=True, padx=16, pady=(0, 6))

        header = ttk.Frame(card, style="Card.TFrame")
        header.pack(fill="x", padx=20, pady=(12, 0))
        tk.Label(
            header,
            text="\U0001F4F0  公告列表",
            font=Fonts.SUBTITLE,
            bg=Colors.BG_CARD,
            fg=Colors.PRIMARY,
        ).pack(side="left")
        tk.Label(
            header,
            text="双击行查看详情",
            font=Fonts.SMALL,
            bg=Colors.BG_CARD,
            fg=Colors.TEXT_SECONDARY,
        ).pack(side="left", padx=(12, 0))

        tree_frame = ttk.Frame(card, style="Card.TFrame")
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(8, 16))

        columns = ("ID", "标题", "发布人", "发布时间", "浏览量")
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", height=12,
        )

        col_widths = {"ID": 130, "标题": 520, "发布人": 130, "发布时间": 150, "浏览量": 80}
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths.get(col, 150), anchor="w")

        # 斑马纹
        self.tree.tag_configure("evenrow", background=Colors.BG_CARD)
        self.tree.tag_configure("oddrow", background=Colors.BG_TREE_ALT)
        self.tree.tag_configure("hover", background=Colors.BG_TREE_HOVER)

        scrollbar = ttk.Scrollbar(
            tree_frame, orient="vertical", command=self.tree.yview,
            style="Vertical.TScrollbar",
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<Double-Button-1>", self._show_detail)
        self.tree.bind("<Motion>", self._on_tree_hover)
        self.tree.bind("<Leave>", self._on_tree_leave)

    # ------------------------------------------------------------------
    def _build_status_bar(self):
        """底部状态栏。"""
        bar = ttk.Frame(self.root, style="Card.TFrame")
        bar.pack(fill="x", padx=16, pady=(0, 16))

        self.count_label = tk.Label(
            bar,
            text="共 0 条公告",
            font=Fonts.SMALL,
            bg=Colors.BG_CARD,
            fg=Colors.TEXT_SECONDARY,
        )
        self.count_label.pack(side="left", padx=20, pady=8)

        tk.Label(
            bar,
            text=datetime.now().strftime("%Y-%m-%d"),
            font=Fonts.SMALL,
            bg=Colors.BG_CARD,
            fg=Colors.TEXT_SECONDARY,
        ).pack(side="right", padx=20, pady=8)

    # ==================================================================
    #  辅助方法
    # ==================================================================
    def _add_label_entry(self, parent, label_text, attr_name, width=15, show="", default=""):
        """在 parent 中添加 [Label + Entry] 组合并注册为实例属性。"""
        ttk.Label(
            parent, text=label_text, style="Card.TLabel",
            font=Fonts.LABEL,
        ).pack(side="left", padx=(0, 4))
        entry = ttk.Entry(parent, width=width, style="Custom.TEntry", show=show or "")
        entry.pack(side="left", padx=(0, 16))
        if default:
            entry.insert(0, default)
        setattr(self, attr_name, entry)

    def _toggle_db(self):
        state = "normal" if self.db_var.get() else "disabled"
        for w in [self.db_host, self.db_user, self.db_pass, self.db_name]:
            w.config(state=state)

    def _toggle_email(self):
        state = "normal" if self.email_var.get() else "disabled"
        for w in [self.sender_entry, self.sender_pass, self.receiver_entry]:
            w.config(state=state)

    def _restore_config_fields(self):
        """从 Config 恢复上次保存的配置到输入框。"""
        if Config.ACCOUNT:
            self.account_entry.insert(0, Config.ACCOUNT)
        if Config.QUOTES:
            self.keyword_entry.insert(0, Config.QUOTES)
        if Config.MYSQL_ENABLED:
            self.db_var.set(1)
            self.db_host.delete(0, "end")
            self.db_host.insert(0, Config.MYSQL_HOST)
            self.db_user.delete(0, "end")
            self.db_user.insert(0, Config.MYSQL_USER)
            self.db_name.delete(0, "end")
            self.db_name.insert(0, Config.MYSQL_DATABASE)
        if Config.EMAIL_ENABLED:
            self.email_var.set(1)
            self.sender_entry.delete(0, "end")
            self.sender_entry.insert(0, Config.SENDER_EMAIL)
            self.receiver_entry.delete(0, "end")
            self.receiver_entry.insert(0, Config.RECEIVER_EMAIL)
        self._toggle_db()
        self._toggle_email()

    def _update_count(self):
        count = len(self.tree.get_children())
        self.count_label.config(text=f"共 {count} 条公告")

    # ==================================================================
    #  日志
    # ==================================================================
    def log(self, message, tag=""):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] ", "time")
        self.log_text.insert("end", f"{message}\n", tag)
        self.log_text.see("end")
        self.root.update()

    # ==================================================================
    #  Treeview 交互
    # ==================================================================
    def _on_tree_hover(self, event):
        for item in self.tree.get_children():
            tags = list(self.tree.item(item, "tags"))
            if "hover" in tags:
                tags.remove("hover")
                self.tree.item(item, tags=tags)
        item = self.tree.identify_row(event.y)
        if item:
            tags = list(self.tree.item(item, "tags"))
            if "hover" not in tags:
                tags.append("hover")
                self.tree.item(item, tags=tags)

    def _on_tree_leave(self, _event):
        for item in self.tree.get_children():
            tags = list(self.tree.item(item, "tags"))
            if "hover" in tags:
                tags.remove("hover")
                self.tree.item(item, tags=tags)

    def _insert_tree_row(self, values):
        """插入一行并自动交替背景色。"""
        count = len(self.tree.get_children())
        tag = "oddrow" if count % 2 else "evenrow"
        self.tree.insert("", "end", values=values, tags=(tag,))

    # ==================================================================
    #  操作
    # ==================================================================
    def _load_sample(self):
        sample = [
            ("view.asp?id=580705", "【示例】关于组织参加2026年大学生AI+信息素养大赛的通知", "计划财务部", "2026-08-31", "1247"),
            ("view.asp?id=580706", "【示例】图书馆2026年秋季学期信息素养培训安排", "图书馆", "2026-09-01", "856"),
        ]
        self.data_cache = sample
        for item in sample:
            self._insert_tree_row(item)
        self._update_count()
        self.log("已加载示例数据，点击「运行爬虫」获取真实数据")

    def _clear_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.data_cache = []
        self.content_cache = {}
        self._update_count()
        self.log("已清空数据")

    def _show_detail(self, _event):
        selection = self.tree.selection()
        if not selection:
            return
        values = self.tree.item(selection[0], "values")
        content = self.content_cache.get(values[0], "")
        DetailWindow(self.root, values, content)

    def _set_status(self, text, color):
        self.status_label.config(text=text, fg=color)
        self.status_dot.config(fg=color)

    # ==================================================================
    #  运行爬虫
    # ==================================================================
    def _run_crawler(self):
        account = self.account_entry.get().strip()
        password = self.password_entry.get().strip()
        keyword = self.keyword_entry.get().strip()

        if not account or not password or not keyword:
            messagebox.showwarning("提示", "账号、密码和关键词为必填项！")
            return

        Config.ACCOUNT = account
        Config.PASSWORD = password
        Config.QUOTES = keyword
        Config.MYSQL_ENABLED = bool(self.db_var.get())
        Config.MYSQL_HOST = self.db_host.get().strip() or "localhost"
        Config.MYSQL_USER = self.db_user.get().strip() or "root"
        Config.MYSQL_PASSWORD = self.db_pass.get().strip()
        Config.MYSQL_DATABASE = self.db_name.get().strip() or "szu_board"
        Config.EMAIL_ENABLED = bool(self.email_var.get())
        Config.SENDER_EMAIL = self.sender_entry.get().strip()
        Config.SENDER_PASSWORD = self.sender_pass.get().strip()
        Config.RECEIVER_EMAIL = self.receiver_entry.get().strip()
        Config.save_settings()

        self.run_btn.config(state="disabled")
        self._set_status("运行中...", Colors.WARNING)
        self.log("=" * 56)
        self.log("开始运行爬虫...")

        threading.Thread(target=self._crawler_thread, daemon=True).start()

    def _crawler_thread(self):
        def callback(msg):
            self.root.after(0, lambda m=msg: self.log(m))

        try:
            crawler = SzuCrawler(Config, callback)
            results = crawler.run()

            if results:
                self.root.after(0, self._clear_data)
                for item in results:
                    values = (
                        item.get("announcement_id", ""),
                        item.get("title", "")[:50],
                        item.get("author", ""),
                        item.get("publish_time", ""),
                        item.get("view_count", ""),
                    )
                    self.root.after(0, lambda v=values: self._insert_tree_row(v))
                    self.content_cache[item.get("announcement_id", "")] = item.get("content", "")

                self.data_cache = [
                    (d.get("announcement_id", ""), d.get("title", ""),
                     d.get("author", ""), d.get("publish_time", ""),
                     d.get("view_count", ""))
                    for d in results
                ]
                self.root.after(0, self._update_count)
                self.root.after(0, lambda: self.log(f"共获取 {len(results)} 条新公告", "success"))
            else:
                self.root.after(0, lambda: self.log("没有新公告"))

        except Exception as e:
            self.root.after(0, lambda: self.log(f"运行出错：{e}", "error"))
            import traceback
            traceback.print_exc()

        self.root.after(0, lambda: self.run_btn.config(state="normal"))
        self.root.after(0, lambda: self._set_status("完成", Colors.SUCCESS))
        self.root.after(0, lambda: self.log("=" * 56))

    # ==================================================================
    #  生命周期
    # ==================================================================
    def _on_close(self):
        self.root.destroy()

    def run(self):
        self.root.mainloop()
