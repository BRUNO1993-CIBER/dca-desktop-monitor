import tkinter as tk
from typing import List, Dict, Optional
# pyrefly: ignore [missing-import]
import customtkinter as ctk

from config.tema_cripto import (
    BG_CARD, BG_DEEP, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, BORDER
)

_FONT       = ("Segoe UI", 11, "bold")
_FONT_HEAD  = ("Segoe UI", 11, "bold")
_SEL_BG     = "#1A3A5C"
_SEL_GLOW   = "#4A9EFF"
_HOVER_BG   = "#1E2D3D"
_COL_MIN    = (90, 60, 100)


def _hex_to_rgb(h: str):
    h = h.lstrip("#")
    if len(h) != 6:
        return (128, 128, 128)
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _rgb_to_hex(r, g, b) -> str:
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"


def _lighten(hex_color: str, factor: float = 0.35) -> str:
    try:
        r, g, b = _hex_to_rgb(hex_color)
        r = min(255, int(r + (255 - r) * factor))
        g = min(255, int(g + (255 - g) * factor))
        b = min(255, int(b + (255 - b) * factor))
        return _rgb_to_hex(r, g, b)
    except Exception:
        return hex_color


def _alpha_blend(hex_color: str, hex_bg: str, alpha: float) -> str:
    try:
        fr, fg, fb = _hex_to_rgb(hex_color)
        br, bg_, bb = _hex_to_rgb(hex_bg)
        r = int(fr * alpha + br * (1 - alpha))
        g = int(fg * alpha + bg_ * (1 - alpha))
        b = int(fb * alpha + bb * (1 - alpha))
        return _rgb_to_hex(r, g, b)
    except Exception:
        return hex_color


class DonutChart(ctk.CTkFrame):
    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self._selected:    Optional[str] = None
        self._scroll_fn                  = None
        self._hovered_row: Optional[str] = None

        self.leg_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.leg_frame.pack(side=tk.LEFT, fill="y", padx=(0, 10))

        self._build_tabela()

        self.canvas = tk.Canvas(self, bg=BG_CARD, highlightthickness=0)
        self.canvas.pack(side=tk.RIGHT, fill="both", expand=True)

        self._dados:       List[tuple]    = []
        self._cor_map:     Dict[str, str] = {}
        self._draw_job:    Optional[str]  = None
        self._row_widgets: List           = []

        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Motion>",    self._on_canvas_motion)
        self.canvas.bind("<Button-1>",  self._on_canvas_click)
        self.canvas.bind("<Leave>",     self._on_canvas_leave)

    def _build_tabela(self):
        header = ctk.CTkFrame(self.leg_frame, fg_color=BG_DEEP, corner_radius=6)
        header.pack(fill="x", padx=(0, 28), pady=(0, 2))

        for i in range(3):
            header.columnconfigure(i, weight=1, uniform="leg_col", minsize=_COL_MIN[i])

        labels = ("ATIVO", "%", "QUANTIDADE")

        for col, txt in enumerate(labels):
            pad_x_val = (16, 12) if col == 1 else 6
            ctk.CTkLabel(
                header,
                text=txt,
                font=_FONT_HEAD,
                text_color=TEXT_SECONDARY,
                fg_color="transparent",
                anchor="w",
            ).grid(row=0, column=col, sticky="w", padx=pad_x_val, pady=3)

        self._scroll_frame = ctk.CTkScrollableFrame(
            self.leg_frame,
            fg_color=BG_CARD,
            scrollbar_button_color=BORDER,
            scrollbar_button_hover_color=TEXT_MUTED,
            corner_radius=6,
            width=300,
        )
        self._scroll_frame.pack(fill="both", expand=True, padx=(0, 16))

        self._bind_scroll(self._scroll_frame)

    def _bind_scroll(self, frame: ctk.CTkScrollableFrame):
        canvas = frame._parent_canvas

        def _scroll(event):
            if event.num == 4 or event.delta > 0:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5 or event.delta < 0:
                canvas.yview_scroll(1, "units")

        for widget in (frame, canvas):
            widget.bind("<Button-4>",   _scroll, add="+")
            widget.bind("<Button-5>",   _scroll, add="+")
            widget.bind("<MouseWheel>", _scroll, add="+")

        self._scroll_fn = _scroll

    def _bind_scroll_row(self, widget):
        if self._scroll_fn is None:
            return
        widget.bind("<Button-4>",   self._scroll_fn, add="+")
        widget.bind("<Button-5>",   self._scroll_fn, add="+")
        widget.bind("<MouseWheel>", self._scroll_fn, add="+")
        for child in widget.winfo_children():
            self._bind_scroll_row(child)

    def atualizar_dados(self, dados: List[tuple], cor_map: Dict[str, str]) -> None:
        self._dados   = dados
        self._cor_map = cor_map
        if self._selected and self._selected not in dict(dados):
            self._selected = None
        self._atualizar_tabela()
        self._agendar_desenho()

    def limpar(self) -> None:
        self._dados       = []
        self._selected    = None
        self._hovered_row = None
        for w in self._row_widgets:
            w.destroy()
        self._row_widgets.clear()
        self.canvas.delete("all")

    def _atualizar_tabela(self) -> None:
        for idx, (moeda, d) in enumerate(self._dados):
            percentual = d.get("percentual", 0)
            qtd        = d.get("quantidade", 0)
            qtd_str    = f"{qtd:,.2f}" if moeda.upper() == "USDT" else f"{qtd:,.6f}"
            cor        = self._cor_map.get(moeda, TEXT_PRIMARY)
            bg_normal  = BG_CARD if idx % 2 == 0 else BG_DEEP

            if idx < len(self._row_widgets):
                row = self._row_widgets[idx]
                row._moeda     = moeda
                row._bg_normal = bg_normal
                row.lbl_nome.configure(text=f"■  {moeda.upper()}", text_color=cor)
                row.lbl_pct.configure(text=f"{percentual:.2f}%")
                row.lbl_qtd.configure(text=qtd_str)
            else:
                row = ctk.CTkFrame(
                    self._scroll_frame,
                    fg_color=bg_normal,
                    corner_radius=0,
                    cursor="hand2",
                )
                row.pack(fill="x", pady=0)

                for i in range(3):
                    row.columnconfigure(i, weight=1, uniform="leg_col", minsize=_COL_MIN[i])

                row._moeda     = moeda
                row._bg_normal = bg_normal

                row.lbl_nome = ctk.CTkLabel(
                    row, text=f"■  {moeda.upper()}", font=_FONT,
                    text_color=cor, fg_color="transparent", anchor="w", cursor="hand2",
                )
                row.lbl_nome.grid(row=0, column=0, sticky="ew", padx=6, pady=3)

                row.lbl_pct = ctk.CTkLabel(
                    row, text=f"{percentual:.2f}   %", font=_FONT,
                    text_color=TEXT_PRIMARY, fg_color="transparent", anchor="w", cursor="hand2",
                )
                row.lbl_pct.grid(row=0, column=1, sticky="ew", padx=(16, 12), pady=3)

                row.lbl_qtd = ctk.CTkLabel(
                    row, text=qtd_str, font=_FONT,
                    text_color=TEXT_MUTED, fg_color="transparent", anchor="w", cursor="hand2",
                )
                row.lbl_qtd.grid(row=0, column=2, sticky="ew", padx=6, pady=3)

                row.bind("<Button-1>", lambda e, r=row: self._toggle_selecao(r._moeda))

                for widget in (row, row.lbl_nome, row.lbl_pct, row.lbl_qtd):
                    widget.bind("<Enter>", lambda e, r=row: self._hover_row(r._moeda, True))
                    widget.bind("<Leave>", lambda e, r=row: self._hover_row(r._moeda, False))

                self._bind_scroll_row(row)
                self._row_widgets.append(row)

            if moeda == self._selected:
                row.configure(fg_color=_SEL_BG)
            elif moeda == self._hovered_row:
                row.configure(fg_color=_HOVER_BG)
            else:
                row.configure(fg_color=bg_normal)

        while len(self._row_widgets) > len(self._dados):
            w = self._row_widgets.pop()
            w.destroy()

    def _toggle_selecao(self, moeda: str) -> None:
        self._selected = None if self._selected == moeda else moeda
        self._aplicar_selecao()
        self._agendar_desenho()

    def _hover_row(self, moeda: str, entering: bool) -> None:
        if entering:
            self._hovered_row = moeda
        else:
            if self._hovered_row == moeda:
                self._hovered_row = None
        self._aplicar_selecao()
        self._agendar_desenho()

    def _aplicar_selecao(self) -> None:
        for row in self._row_widgets:
            if row._moeda == self._selected:
                row.configure(fg_color=_SEL_BG)
            elif row._moeda == self._hovered_row:
                row.configure(fg_color=_HOVER_BG)
            else:
                row.configure(fg_color=row._bg_normal)

    def _on_resize(self, event: tk.Event) -> None:
        self._agendar_desenho()

    def _get_bar_rects(self):
        if not self._dados:
            return []

        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if w < 50 or h < 50:
            return []

        pad_x  = 40
        pad_y  = 44
        y_base = h - pad_y
        area_h = h - 2 * pad_y

        max_pct = max((d.get("percentual", 0) for _, d in self._dados), default=1)
        max_pct = (max_pct * 1.18) if max_pct > 0 else 1

        n_ativos   = len(self._dados)
        slot_width = (w - 2 * pad_x) / max(n_ativos, 1)
        bar_width  = min(slot_width * 0.68, 56)

        rects = []
        for i, (moeda, d) in enumerate(self._dados):
            pct = d.get("percentual", 0)
            cx  = pad_x + (i * slot_width) + (slot_width / 2)
            x1  = cx - bar_width / 2
            x2  = cx + bar_width / 2
            bar_h = (pct / max_pct) * area_h
            y1  = y_base - bar_h
            y2  = y_base
            rects.append((moeda, x1, y1, x2, y2))

        return rects

    def _on_canvas_motion(self, event):
        rects   = self._get_bar_rects()
        hovered = None
        for moeda, x1, y1, x2, y2 in rects:
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                hovered = moeda
                break

        if hovered != self._hovered_row:
            self._hovered_row = hovered
            self._aplicar_selecao()
            self._agendar_desenho()

        self.canvas.config(cursor="hand2" if hovered else "")

    def _on_canvas_leave(self, event):
        if self._hovered_row is not None:
            self._hovered_row = None
            self._aplicar_selecao()
            self._agendar_desenho()
        self.canvas.config(cursor="")

    def _on_canvas_click(self, event):
        rects   = self._get_bar_rects()
        clicked = None
        for moeda, x1, y1, x2, y2 in rects:
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                clicked = moeda
                break

        if clicked:
            self._toggle_selecao(clicked)
        else:
            if self._selected is not None:
                self._selected = None
                self._aplicar_selecao()
                self._agendar_desenho()

    def _agendar_desenho(self) -> None:
        if self._draw_job is not None:
            self.canvas.after_cancel(self._draw_job)
        self._draw_job = self.canvas.after(30, self._desenhar)

    def _barra_arredondada(self, x1: float, y1: float, x2: float, y2: float,
                            r: float, cor: str) -> None:
        if y2 - y1 < 2:
            return
        r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))

        self.canvas.create_rectangle(x1, y1 + r, x2, y2, fill=cor, outline="")

        if r > 0:
            self.canvas.create_rectangle(x1 + r, y1, x2 - r, y1 + r + 1,
                                         fill=cor, outline="")
            self.canvas.create_arc(x1, y1, x1 + 2 * r, y1 + 2 * r,
                                   start=90, extent=90,
                                   fill=cor, outline="", style="pieslice")
            self.canvas.create_arc(x2 - 2 * r, y1, x2, y1 + 2 * r,
                                   start=0, extent=90,
                                   fill=cor, outline="", style="pieslice")

    def _desenhar(self) -> None:
        self.canvas.delete("all")
        if not self._dados:
            return

        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if w < 50 or h < 50:
            return

        pad_x  = 40
        pad_y  = 44
        y_base = h - pad_y
        area_h = h - 2 * pad_y

        max_pct = max((d.get("percentual", 0) for _, d in self._dados), default=1)
        max_pct = (max_pct * 1.18) if max_pct > 0 else 1

        n_ativos   = len(self._dados)
        slot_width = (w - 2 * pad_x) / max(n_ativos, 1)
        bar_width  = min(slot_width * 0.68, 56)
        radius     = min(bar_width * 0.28, 9)

        n_grid = 4
        for i in range(1, n_grid + 1):
            gy      = y_base - (i / n_grid) * area_h
            pct_lbl = (i / n_grid) * max_pct
            self.canvas.create_line(
                pad_x, gy, w - pad_x, gy,
                fill=BORDER, width=1, dash=(3, 7),
            )
            self.canvas.create_text(
                pad_x - 6, gy,
                text=f"{pct_lbl:.0f}%",
                fill=TEXT_MUTED,
                font=("Segoe UI", 8),
                anchor="e",
            )

        self.canvas.create_line(
            pad_x, y_base, w - pad_x, y_base,
            fill=TEXT_SECONDARY, width=1,
        )

        for i, (moeda, d) in enumerate(self._dados):
            pct      = d.get("percentual", 0)
            cor_base = self._cor_map.get(moeda, TEXT_MUTED)

            if self._selected is not None:
                if self._selected == moeda:
                    cor = cor_base
                else:
                    cor = _alpha_blend(cor_base, BG_CARD, 0.25)
            else:
                if self._hovered_row is not None and self._hovered_row != moeda:
                    cor = _alpha_blend(cor_base, BG_CARD, 0.4)
                elif self._hovered_row == moeda:
                    cor = _lighten(cor_base, 0.2)
                else:
                    cor = cor_base

            cx    = pad_x + (i * slot_width) + (slot_width / 2)
            x1    = cx - bar_width / 2
            x2    = cx + bar_width / 2
            bar_h = (pct / max_pct) * area_h
            y1    = y_base - bar_h
            y2    = y_base

            if bar_h > 0:
                self._barra_arredondada(x1, y1, x2, y2, radius, cor)

            if slot_width >= 25:
                txt_color_moeda = TEXT_SECONDARY
                txt_color_pct   = TEXT_PRIMARY

                if self._selected is not None and self._selected != moeda:
                    txt_color_moeda = TEXT_MUTED
                    txt_color_pct   = TEXT_MUTED
                elif self._hovered_row is not None and self._hovered_row != moeda and self._selected is None:
                    txt_color_moeda = TEXT_MUTED
                    txt_color_pct   = TEXT_MUTED

                self.canvas.create_text(
                    cx, y2 + 16,
                    text=moeda.upper(),
                    fill=txt_color_moeda,
                    font=("Segoe UI", 9, "bold"),
                )

                if pct > 0:
                    self.canvas.create_text(
                        cx, y1 - 12,
                        text=f"{pct:.1f}%",
                        fill=txt_color_pct,
                        font=("Segoe UI", 9, "bold"),
                    )