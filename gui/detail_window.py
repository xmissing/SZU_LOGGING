"""公告详情弹窗：展示单条公告的标题、元信息和正文。"""

import tkinter as tk
from tkinter import ttk, scrolledtext

from gui.theme import Colors, Fonts, apply_theme


class DetailWindow:
    """公告详情弹窗，使用卡片式布局和深色日志风格。"""

    def __init__(self, parent, values, content=""):
        self.win = tk.Toplevel(parent)
        self.win.title("公告详情")
        self.win.geometry("720x560")
        self.win.configure(bg=Colors.BG_MAIN)
        self.win.minsize(600, 400)
        self.win.transient(parent)

        # 居中显示
        self.win.update_idletasks()
        w, h = 720, 560
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.win.geometry(f"{w}x{h}+{x}+{y}")

        apply_theme(self.win)
        self._build_ui(values, content)

    def _build_ui(self, values, content):
        ann_id, title, author, pub_time, view_count = values

        # ---- 顶部标题栏 ----
        header = ttk.Frame(self.win, style="Card.TFrame")
        header.pack(fill="x", padx=16, pady=(16, 8))

        ttk.Label(
            header,
            text=title,
            style="Title.TLabel",
            wraplength=640,
        ).pack(anchor="w", padx=20, pady=(16, 6))

        # 元信息行
        meta_frame = ttk.Frame(header, style="Card.TFrame")
        meta_frame.pack(fill="x", padx=20, pady=(0, 14))

        meta_items = [
            ("发布人", author),
            ("发布时间", pub_time),
            ("浏览量", view_count),
            ("ID", ann_id),
        ]
        for i, (label, value) in enumerate(meta_items):
            if i > 0:
                ttk.Separator(meta_frame, orient="vertical").pack(
                    side="left", fill="y", padx=10
                )
            chip = ttk.Frame(meta_frame, style="Card.TFrame")
            chip.pack(side="left")
            ttk.Label(
                chip,
                text=label,
                style="Muted.TLabel",
            ).pack(side="left", padx=(0, 4))
            ttk.Label(
                chip,
                text=value or "—",
                style="Card.TLabel",
                font=Fonts.SMALL_BOLD,
                foreground=Colors.PRIMARY,
            ).pack(side="left")

        ttk.Separator(header, orient="horizontal").pack(
            fill="x", padx=20, pady=(0, 0)
        )

        # ---- 正文区 ----
        body_frame = ttk.Frame(self.win, style="Card.TFrame")
        body_frame.pack(fill="both", expand=True, padx=16, pady=8)

        ttk.Label(
            body_frame,
            text="  公告正文",
            style="Card.TLabel",
            font=Fonts.LABEL,
            foreground=Colors.TEXT_SECONDARY,
        ).pack(anchor="w", padx=16, pady=(12, 4))

        text_widget = scrolledtext.ScrolledText(
            body_frame,
            font=(Fonts.FAMILY, 11),
            wrap="word",
            bg=Colors.BG_INPUT,
            fg=Colors.TEXT_PRIMARY,
            relief="flat",
            padx=16,
            pady=12,
            selectbackground=Colors.BG_TREE_SEL,
            insertbackground=Colors.TEXT_PRIMARY,
        )
        text_widget.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        text_widget.insert("1.0", content or "完整内容请运行爬虫获取")
        text_widget.config(state="disabled")
