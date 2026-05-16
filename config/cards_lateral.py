import platform
# pyrefly: ignore [missing-import]
import customtkinter as ctk
from config.tema_cripto import (
    BG_CARD, BG_DEEP, BTC_ORANGE, NEON_GREEN, NEON_RED, CYAN,
    TEXT_SECONDARY, TEXT_MUTED, BORDER,
)

_FONT_NAME  = "Segoe UI" if platform.system() == "Windows" else "Ubuntu"
_F_TITLE    = (_FONT_NAME, 10, "bold")
_F_SUBTITLE = (_FONT_NAME, 9)
_F_VALUE    = (_FONT_NAME, 12, "bold")
_F_VALUE_SM = (_FONT_NAME, 10, "bold")

_ITEMS_DEF = [
    ("patrimonio", "💼 Patrimônio Total",  "preço mercado × posição",    BTC_ORANGE),
    ("custo",      "📥 Custo Total",       "soma do investido",           CYAN),
    ("pl_nr",      "📈 P/L Não Realizado", "ganho em aberto",             NEON_GREEN),
    ("pl_r",       "💰 P/L Realizado",     "lucro já sacado/vendido",     NEON_GREEN),
    ("pl",         "🏁 P/L Total",         "realizado + não realizado",   NEON_GREEN),
    ("pct",        "📊 Ganho %",           "P/L NR ÷ custo total",        NEON_GREEN),
    ("retorno",    "📉 Retorno Total %",   "P/L total ÷ custo total",     NEON_GREEN),
    ("div",        "🎯 Diversificação",    "ativos distintos",             TEXT_SECONDARY),
    ("melhor",     "🏆 Melhor Ativo",      "maior P/L total",              NEON_GREEN),
    ("pior",       "💀 Pior Ativo",        "menor P/L total",              NEON_RED),
]

_ROW_COLORS = [BG_DEEP, BG_CARD]


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
            bg = _ROW_COLORS[idx % 2]
            self._labels[key] = self._criar_item(titulo, subtitulo, cor_val, bg, key in ("melhor", "pior"))

    def _criar_item(self, titulo: str, subtitulo: str, cor_val: str, bg: str, small: bool) -> ctk.CTkLabel:
        row = ctk.CTkFrame(self, fg_color=bg, corner_radius=0)
        row.pack(fill="x")
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=0)

        ctk.CTkLabel(
            row, text=titulo, font=_F_TITLE,
            text_color=TEXT_SECONDARY, fg_color="transparent", anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=(10, 4), pady=(6, 0))

        lbl = ctk.CTkLabel(
            row, text="--",
            font=_F_VALUE_SM if small else _F_VALUE,
            text_color=cor_val, fg_color="transparent", anchor="e",
        )
        lbl.grid(row=0, column=1, sticky="e", padx=(4, 10), pady=(6, 0))

        ctk.CTkLabel(
            row, text=subtitulo, font=_F_SUBTITLE,
            text_color=TEXT_MUTED, fg_color="transparent", anchor="w",
        ).grid(row=1, column=0, columnspan=2, sticky="w", padx=(10, 10), pady=(0, 6))

        self._bind_scroll_rec(row)
        return lbl

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