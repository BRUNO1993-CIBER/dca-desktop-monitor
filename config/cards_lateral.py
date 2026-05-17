import platform
import tkinter as tk
# pyrefly: ignore [missing-import]
import customtkinter as ctk
from config.tema_cripto import (
    BG_CARD, BTC_ORANGE, NEON_GREEN, NEON_RED, CYAN,
    TEXT_SECONDARY, TEXT_MUTED, BORDER,
)

_FONT_NAME  = "Segoe UI" if platform.system() == "Windows" else "Ubuntu"
_F_TITLE    = (_FONT_NAME, 10, "bold")
_F_SUBTITLE = (_FONT_NAME, 9)
_F_VALUE    = (_FONT_NAME, 12, "bold")
_F_VALUE_SM = (_FONT_NAME, 10, "bold")

_ACCENT_W   = 3
_SEP_H      = 1


def _lighten(hex_color: str, factor: float = 0.07) -> str:
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return hex_color
    r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    r = min(255, int(r + (255 - r) * factor))
    g = min(255, int(g + (255 - g) * factor))
    b = min(255, int(b + (255 - b) * factor))
    return f"#{r:02x}{g:02x}{b:02x}"


_BG_ROW     = _lighten(BG_CARD, 0.07)
_BG_ROW_HOV = _lighten(BG_CARD, 0.16)

_ITEMS_DEF = [
    ("patrimonio", "💼 Patrimônio Total",  "preço mercado × posição",  BTC_ORANGE),
    ("custo",      "📥 Custo Total",       "soma do investido",         CYAN),
    ("pl_nr",      "📈 P/L Não Realizado", "ganho em aberto",           NEON_GREEN),
    ("pl_r",       "💰 P/L Realizado",     "lucro já sacado/vendido",   NEON_GREEN),
    ("pl",         "🏁 P/L Total",         "realizado + não realizado", NEON_GREEN),
    ("pct",        "📊 Ganho %",           "P/L NR ÷ custo total",      NEON_GREEN),
    ("retorno",    "📉 Retorno Total %",   "P/L total ÷ custo total",   NEON_GREEN),
    ("div",        "🎯 Diversificação",    "ativos distintos",           TEXT_SECONDARY),
    ("melhor",     "🏆 Melhor Ativo",      "maior P/L total",            NEON_GREEN),
    ("pior",       "💀 Pior Ativo",        "menor P/L total",            NEON_RED),
]


def _sep(parent: tk.Widget) -> None:
    c = tk.Canvas(parent, height=_SEP_H, bg=BTC_ORANGE,
                  highlightthickness=0, bd=0)
    c.pack(fill="x")


def _footer(parent: tk.Widget) -> None:
    """Canvas decorativo com símbolo ₿ watermark e linhas de grade."""
    c = tk.Canvas(parent, height=90, bg=BG_CARD,
                  highlightthickness=0, bd=0)
    c.pack(fill="x", pady=(4, 0))

    def _draw(event=None):
        c.delete("all")
        w = c.winfo_width() or 260
        h = 90

        for i in range(1, 4):
            y = int(h * i / 4)
            c.create_line(0, y, w, y, fill=BORDER, width=1, dash=(2, 8))

        c.create_text(
            w // 2, h // 2 - 1,
            text="₿",
            font=(_FONT_NAME, 52, "bold"),
            fill=_lighten(BG_CARD, 0.18),
            anchor="center",
        )

        c.create_line(0, h - 1, w, h - 1, fill=BTC_ORANGE, width=1)

    c.bind("<Configure>", lambda e: _draw())
    c.after(50, _draw)


class PainelCards(ctk.CTkScrollableFrame):

    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            fg_color="transparent",
            scrollbar_button_color=BORDER,
            scrollbar_button_hover_color=TEXT_MUTED,
            **kwargs,
        )
        self._labels: dict[str, ctk.CTkLabel] = {}
        self._build()

    def _build(self) -> None:
        for idx, (key, titulo, subtitulo, cor_val) in enumerate(_ITEMS_DEF):
            self._labels[key] = self._criar_item(titulo, subtitulo, cor_val, key in ("melhor", "pior"))
            if idx < len(_ITEMS_DEF) - 1:
                _sep(self)
        _footer(self)

    def _criar_item(self, titulo: str, subtitulo: str, cor_val: str, small: bool) -> ctk.CTkLabel:
        outer = ctk.CTkFrame(self, fg_color=_BG_ROW, corner_radius=0, cursor="hand2")
        outer.pack(fill="x")

        outer.columnconfigure(0, minsize=_ACCENT_W, weight=0)
        outer.columnconfigure(1, weight=1)
        outer.columnconfigure(2, weight=0)

        tk.Frame(outer, bg=BTC_ORANGE, width=_ACCENT_W).grid(
            row=0, column=0, rowspan=2, sticky="nsew",
        )

        ctk.CTkLabel(
            outer, text=titulo, font=_F_TITLE,
            text_color=TEXT_SECONDARY, fg_color="transparent", anchor="w", cursor ="hand2",
        ).grid(row=0, column=1, sticky="w", padx=(10, 4), pady=(6, 0))

        lbl = ctk.CTkLabel(
            outer, text="--",
            font=_F_VALUE_SM if small else _F_VALUE,
            text_color=cor_val, fg_color="transparent", anchor="e", cursor="hand2",
        )
        lbl.grid(row=0, column=2, sticky="e", padx=(4, 10), pady=(6, 0))

        ctk.CTkLabel(
            outer, text=subtitulo, font=_F_SUBTITLE,
            text_color=TEXT_MUTED, fg_color="transparent", anchor="w", cursor="hand2",
        ).grid(row=1, column=1, columnspan=2, sticky="w", padx=(10, 10), pady=(0, 6))

        self._bind_hover(outer)
        self._bind_scroll_rec(outer)
        return lbl

    def _bind_hover(self, outer: ctk.CTkFrame) -> None:
        def _enter(e): outer.configure(fg_color=_BG_ROW_HOV)
        def _leave(e): outer.configure(fg_color=_BG_ROW)
        for w in (outer, *outer.winfo_children()):
            w.bind("<Enter>", _enter, add="+")
            w.bind("<Leave>", _leave, add="+")

    def _on_scroll(self, event) -> None:
        if event.num == 4 or event.delta > 0:
            self._parent_canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self._parent_canvas.yview_scroll(1, "units")

    def _bind_scroll_rec(self, widget) -> None:
        widget.bind("<Button-4>",   self._on_scroll, add="+")
        widget.bind("<Button-5>",   self._on_scroll, add="+")
        widget.bind("<MouseWheel>", self._on_scroll, add="+")
        for child in widget.winfo_children():
            self._bind_scroll_rec(child)

    @property
    def lbl_patrimonio(self) -> ctk.CTkLabel: return self._labels["patrimonio"]
    @property
    def lbl_custo(self)      -> ctk.CTkLabel: return self._labels["custo"]
    @property
    def lbl_pl_nr(self)      -> ctk.CTkLabel: return self._labels["pl_nr"]
    @property
    def lbl_pl_r(self)       -> ctk.CTkLabel: return self._labels["pl_r"]
    @property
    def lbl_pl(self)         -> ctk.CTkLabel: return self._labels["pl"]
    @property
    def lbl_pct(self)        -> ctk.CTkLabel: return self._labels["pct"]
    @property
    def lbl_retorno(self)    -> ctk.CTkLabel: return self._labels["retorno"]
    @property
    def lbl_div(self)        -> ctk.CTkLabel: return self._labels["div"]
    @property
    def lbl_melhor(self)     -> ctk.CTkLabel: return self._labels["melhor"]
    @property
    def lbl_pior(self)       -> ctk.CTkLabel: return self._labels["pior"]