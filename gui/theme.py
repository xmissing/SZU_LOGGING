"""UI 主题与样式定义：颜色、字体、ttk Style 统一管理。"""

import tkinter.ttk as ttk


# ==================== 色彩常量 ====================
class Colors:
    # 背景
    BG_MAIN = "#EEF1F6"          # 主背景
    BG_CARD = "#FFFFFF"          # 卡片背景
    BG_INPUT = "#F7F8FA"         # 输入框背景
    BG_LOG = "#1E1E2E"           # 日志区深色背景
    BG_TREE_HEADER = "#E8EDF3"   # 表头背景
    BG_TREE_ALT = "#F5F7FA"      # 斑马纹交替行
    BG_TREE_SEL = "#D6E4F0"      # 选中行
    BG_TREE_HOVER = "#EDF2F8"    # 悬停行

    # 文字
    TEXT_PRIMARY = "#1A2332"     # 主文字
    TEXT_SECONDARY = "#6B7B8D"   # 次要文字
    TEXT_LOG = "#CDD6E0"         # 日志文字
    TEXT_LOG_TIME = "#8B95A5"    # 日志时间戳
    TEXT_PLACEHOLDER = "#A0AEC0"

    # 主色
    PRIMARY = "#4F6BED"          # 主按钮 / 标题强调
    PRIMARY_HOVER = "#3D5BD9"
    PRIMARY_LIGHT = "#E8EEFD"

    # 功能色
    SUCCESS = "#22C55E"
    WARNING = "#F59E0B"
    DANGER = "#EF4444"
    ORANGE = "#F97316"
    TEAL = "#14B8A6"

    # 边框
    BORDER = "#E2E8F0"
    BORDER_FOCUS = "#4F6BED"


# ==================== 字体常量 ====================
class Fonts:
    FAMILY = "微软雅黑"
    MONO = "Consolas"

    TITLE = (FAMILY, 16, "bold")
    SUBTITLE = (FAMILY, 13, "bold")
    BODY = (FAMILY, 10)
    BODY_BOLD = (FAMILY, 10, "bold")
    SMALL = (FAMILY, 9)
    SMALL_BOLD = (FAMILY, 9, "bold")
    LABEL = (FAMILY, 9, "bold")
    BUTTON = (FAMILY, 10, "bold")
    LOG = (MONO, 9)
    TREE = (FAMILY, 9)


# ==================== ttk 样式注册 ====================
def apply_theme(root):
    """在给定 root 上注册所有自定义 ttk 样式。"""
    style = ttk.Style()
    style.theme_use("clam")

    # ---- 通用 Frame ----
    style.configure("Card.TFrame", background=Colors.BG_CARD)
    style.configure("Bg.TFrame", background=Colors.BG_MAIN)

    # ---- LabelFrame ----
    style.configure(
        "Section.TLabelframe",
        background=Colors.BG_CARD,
        foreground=Colors.TEXT_PRIMARY,
        borderwidth=1,
        relief="solid",
    )
    style.configure(
        "Section.TLabelframe.Label",
        background=Colors.BG_CARD,
        foreground=Colors.PRIMARY,
        font=Fonts.SUBTITLE,
    )

    # ---- Label ----
    style.configure("Title.TLabel", background=Colors.BG_CARD, foreground=Colors.TEXT_PRIMARY, font=Fonts.TITLE)
    style.configure("Card.TLabel", background=Colors.BG_CARD, foreground=Colors.TEXT_PRIMARY, font=Fonts.BODY)
    style.configure("Muted.TLabel", background=Colors.BG_CARD, foreground=Colors.TEXT_SECONDARY, font=Fonts.SMALL)
    style.configure("Status.TLabel", background=Colors.BG_CARD, foreground=Colors.TEXT_SECONDARY, font=Fonts.SMALL_BOLD)
    style.configure("Section.TLabel", background=Colors.BG_MAIN, foreground=Colors.TEXT_PRIMARY, font=Fonts.SUBTITLE)

    # ---- Entry ----
    style.configure(
        "Custom.TEntry",
        fieldbackground=Colors.BG_INPUT,
        foreground=Colors.TEXT_PRIMARY,
        borderwidth=1,
        relief="solid",
        padding=(8, 5),
    )
    style.map(
        "Custom.TEntry",
        bordercolor=[("focus", Colors.BORDER_FOCUS)],
    )

    # ---- Button ----
    style.configure(
        "Primary.TButton",
        background=Colors.PRIMARY,
        foreground="white",
        font=Fonts.BUTTON,
        borderwidth=0,
        padding=(16, 8),
    )
    style.map(
        "Primary.TButton",
        background=[("pressed", Colors.PRIMARY_HOVER), ("active", Colors.PRIMARY_HOVER)],
    )

    style.configure(
        "Danger.TButton",
        background=Colors.DANGER,
        foreground="white",
        font=Fonts.BUTTON,
        borderwidth=0,
        padding=(16, 8),
    )
    style.map(
        "Danger.TButton",
        background=[("pressed", "#DC2626"), ("active", "#DC2626")],
    )

    style.configure(
        "Warning.TButton",
        background=Colors.ORANGE,
        foreground="white",
        font=Fonts.BUTTON,
        borderwidth=0,
        padding=(16, 8),
    )
    style.map(
        "Warning.TButton",
        background=[("pressed", "#EA580C"), ("active", "#EA580C")],
    )

    # ---- Checkbutton ----
    style.configure(
        "Card.TCheckbutton",
        background=Colors.BG_CARD,
        foreground=Colors.TEXT_PRIMARY,
        font=Fonts.BODY,
    )
    style.map(
        "Card.TCheckbutton",
        background=[("active", Colors.BG_CARD)],
    )

    # ---- Treeview ----
    style.configure(
        "Treeview",
        background=Colors.BG_CARD,
        foreground=Colors.TEXT_PRIMARY,
        fieldbackground=Colors.BG_CARD,
        rowheight=30,
        font=Fonts.TREE,
        borderwidth=0,
    )
    style.map(
        "Treeview",
        background=[("selected", Colors.BG_TREE_SEL)],
        foreground=[("selected", Colors.TEXT_PRIMARY)],
    )

    style.configure(
        "Treeview.Heading",
        background=Colors.BG_TREE_HEADER,
        foreground=Colors.TEXT_PRIMARY,
        font=Fonts.SMALL_BOLD,
        relief="flat",
        borderwidth=0,
        padding=(6, 6),
    )
    style.map(
        "Treeview.Heading",
        background=[("active", "#D5DDE9")],
    )

    # ---- Scrollbar ----
    style.configure(
        "Vertical.TScrollbar",
        background=Colors.BORDER,
        troughcolor=Colors.BG_MAIN,
        borderwidth=0,
        arrowsize=14,
    )
    style.map(
        "Vertical.TScrollbar",
        background=[("active", "#C5CED9")],
    )

    # ---- Separator ----
    style.configure("TSeparator", background=Colors.BORDER)

    return style
