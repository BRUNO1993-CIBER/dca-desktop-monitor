# tema_cripto.py


import tkinter as tk
from tkinter import ttk
from config.fontes import F_UI_NORMAL, F_UI_BOLD, F_UI_SMALL, F_UI_SMALL_BD

BG_DEEP    = "#0a0e1a"
BG_SURFACE = "#0d1117"
BG_CARD    = "#161b22"
BG_INPUT   = "#1c2128"

BORDER     = "#30363d"
BORDER_ACC = "#f7931a"

BTC_ORANGE = "#f7931a"
NEON_GREEN = "#00ff88"
NEON_RED   = "#ff4d4d"
CYAN       = "#58a6ff"
YELLOW     = "#e3b341"

TEXT_PRIMARY   = "#e6edf3"
TEXT_SECONDARY = "#8b949e"
TEXT_MUTED     = "#484f58"


def aplicar_tema(janela: tk.Misc) -> ttk.Style:
    # pyrefly: ignore [unexpected-keyword]
    janela.configure(bg=BG_DEEP)

    style = ttk.Style(janela)
    style.theme_use("alt")

    style.configure(".",
        background=BG_SURFACE,
        foreground=TEXT_PRIMARY,
        fieldbackground=BG_INPUT,
        bordercolor=BORDER,
        darkcolor=BG_CARD,
        lightcolor=BG_CARD,
        troughcolor=BG_INPUT,
        selectbackground=BTC_ORANGE,
        selectforeground=BG_DEEP,
        font=F_UI_NORMAL,
        relief="flat",
    )

    style.configure("TFrame", background=BG_SURFACE)
    style.configure("Card.TFrame", background=BG_CARD)

    style.configure("TNotebook",
        background=BG_DEEP,
        bordercolor=BORDER,
    )
    style.configure("TNotebook.Tab",
        background=BG_CARD,
        foreground=TEXT_SECONDARY,
        padding=[16, 6],
        font=F_UI_BOLD,
    )
    style.map("TNotebook.Tab",
        background=[("selected", BG_SURFACE), ("active", BG_INPUT)],
        foreground=[("selected", BTC_ORANGE), ("active", TEXT_PRIMARY)],
    )

    style.configure("TLabel", background=BG_SURFACE, foreground=TEXT_PRIMARY)

    style.configure("TButton",
        background=BTC_ORANGE,
        foreground=BG_DEEP,
        font=F_UI_BOLD,
        padding=[12, 6],
        relief="flat",
    )
    style.map("TButton",
        background=[("active", "#e8820f"), ("pressed", "#c96d0a"), ("disabled", BORDER)],
        foreground=[("disabled", TEXT_MUTED)],
    )

    style.configure("Secondary.TButton",
        background=BG_CARD,
        foreground=TEXT_PRIMARY,
        bordercolor=BORDER,
    )
    style.map("Secondary.TButton",
        background=[("active", BG_INPUT)],
        foreground=[("active", BTC_ORANGE)],
    )

    style.configure(
        "TCheckbutton",
        background=BG_SURFACE,
        foreground=TEXT_PRIMARY,
    )

    style.map(
        "TCheckbutton",
        background=[
            ("active", BG_INPUT),   
            ("selected", BG_SURFACE),
            ("!active", BG_SURFACE),
        ],
        foreground=[
            ("active", TEXT_PRIMARY),
            ("selected", TEXT_PRIMARY),
        ],
        indicatorcolor=[
            ("active", BTC_ORANGE),
            ("selected", BTC_ORANGE),
        ]
    )

    style.configure("TEntry",
        fieldbackground=BG_INPUT,
        foreground=TEXT_PRIMARY,
        bordercolor=BORDER,
        insertcolor=BTC_ORANGE,
    )
    style.map("TEntry",
        bordercolor=[("focus", BTC_ORANGE)],
    )

    style.configure("TCombobox",
        fieldbackground=BG_INPUT,
        background=BG_CARD,
        foreground=TEXT_PRIMARY,
        arrowcolor=BTC_ORANGE,
    )
    style.map("TCombobox",
        fieldbackground=[("readonly", BG_INPUT)],
        foreground=[("readonly", TEXT_PRIMARY)],
    )

    style.configure("Treeview",
        background=BG_CARD,
        foreground=TEXT_PRIMARY,
        fieldbackground=BG_CARD,
        rowheight=26,
        font=F_UI_SMALL,
    )
    style.configure("Treeview.Heading",
        background=BG_INPUT,
        foreground=BTC_ORANGE,
        font=F_UI_SMALL_BD,
    )
    style.map("Treeview",
        background=[("selected", "#1f2d1f")],
        foreground=[("selected", NEON_GREEN)],
    )

    style.configure("Horizontal.TProgressbar",
        troughcolor=BG_INPUT,
        background=BTC_ORANGE,
        darkcolor="#c96d0a",
    )

    style.configure("TScrollbar",
        background=BG_CARD,
        troughcolor=BG_INPUT,
        arrowcolor=TEXT_SECONDARY,
    )

    return style


def tag_cores_treeview(tree: ttk.Treeview):
    tree.tag_configure("positivo",  foreground=NEON_GREEN)
    tree.tag_configure("negativo",  foreground=NEON_RED)
    tree.tag_configure("neutro",    foreground=TEXT_SECONDARY)
    tree.tag_configure("destaque",  foreground=BTC_ORANGE, font=F_UI_SMALL_BD)
    tree.tag_configure("par",       background=BG_CARD)
    tree.tag_configure("impar",     background="#12171e")