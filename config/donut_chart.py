import tkinter as tk
from typing import List, Dict, Optional
# pyrefly: ignore [missing-import]
import customtkinter as ctk

from config.tema_cripto import (
    BG_CARD, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, BORDER
)


def _hex_to_rgb(h: str):
    h = h.lstrip("#")
    if len(h) != 6:
        return (128, 128, 128)
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _rgb_to_hex(r, g, b) -> str:
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"


def _lighten(hex_color: str, factor: float = 0.2) -> str:
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


_GRADIENT_STEPS = 24


class DonutChart(ctk.CTkFrame):
    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self._selected:    Optional[str] = None
        self._hovered_row: Optional[str] = None

        self.canvas = tk.Canvas(self, bg=BG_CARD, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self._dados:    List[tuple]    = []
        self._cor_map:  Dict[str, str] = {}
        self._draw_job: Optional[str]  = None

        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Motion>",    self._on_canvas_motion)
        self.canvas.bind("<Button-1>",  self._on_canvas_click)
        self.canvas.bind("<Leave>",     self._on_canvas_leave)

    def atualizar_dados(self, dados: List[tuple], cor_map: Dict[str, str]) -> None:
        self._dados   = dados
        self._cor_map = cor_map
        if self._selected and self._selected not in dict(dados):
            self._selected = None
        self._agendar_desenho()

    def limpar(self) -> None:
        self._dados       = []
        self._selected    = None
        self._hovered_row = None
        self.canvas.delete("all")

    def _toggle_selecao(self, moeda: str) -> None:
        self._selected = None if self._selected == moeda else moeda
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
            pct   = d.get("percentual", 0)
            cx    = pad_x + (i * slot_width) + (slot_width / 2)
            x1    = cx - bar_width / 2
            x2    = cx + bar_width / 2
            bar_h = (pct / max_pct) * area_h
            y1    = y_base - bar_h
            y2    = y_base
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
            self._agendar_desenho()

        self.canvas.config(cursor="hand2" if hovered else "")

    def _on_canvas_leave(self, event):
        if self._hovered_row is not None:
            self._hovered_row = None
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
                self._agendar_desenho()

    def _on_resize(self, event: tk.Event) -> None:
        self._agendar_desenho()

    def _agendar_desenho(self) -> None:
        if self._draw_job is not None:
            self.canvas.after_cancel(self._draw_job)
        self._draw_job = self.canvas.after(30, self._desenhar)

    # ── item 3: gradiente vertical, topo=cor_base, base=60% alpha ──────────
    def _barra_gradiente(self, x1: float, y1: float, x2: float, y2: float,
                          cor_base: str) -> None:
        height = y2 - y1
        if height < 1:
            return
        steps    = _GRADIENT_STEPS
        step_h   = height / steps
        for i in range(steps):
            t     = i / max(steps - 1, 1)        # 0.0 no topo → 1.0 na base
            alpha = 1.0 - t * 0.40               # 100% topo, 60% base
            cor   = _alpha_blend(cor_base, BG_CARD, alpha)
            sy1   = y1 + i * step_h
            sy2   = sy1 + step_h + 0.5           # leve overlap p/ sem gaps
            self.canvas.create_rectangle(x1, sy1, x2, sy2, fill=cor, outline="")

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

        # ── item 4: grid sólido, cor blendada bem sutil ─────────────────────
        grid_color = _alpha_blend(BORDER, BG_CARD, 0.30)

        n_grid = 4
        for i in range(1, n_grid + 1):
            gy      = y_base - (i / n_grid) * area_h
            pct_lbl = (i / n_grid) * max_pct
            self.canvas.create_line(
                pad_x, gy, w - pad_x, gy,
                fill=grid_color, width=1,
            )
            self.canvas.create_text(
                pad_x - 6, gy,
                text=f"{pct_lbl:.0f}%",
                fill=TEXT_MUTED,
                font=("Segoe UI", 8),
                anchor="e",
            )

        # eixo base
        axis_color = _alpha_blend(TEXT_SECONDARY, BG_CARD, 0.35)
        self.canvas.create_line(
            pad_x, y_base, w - pad_x, y_base,
            fill=axis_color, width=1,
        )

        for i, (moeda, d) in enumerate(self._dados):
            pct      = d.get("percentual", 0)
            cor_base = self._cor_map.get(moeda, TEXT_MUTED)

            is_selected = self._selected    == moeda
            is_hovered  = self._hovered_row == moeda

            # cor da barra conforme estado
            if self._selected is not None:
                cor = cor_base if is_selected else _alpha_blend(cor_base, BG_CARD, 0.18)
            elif self._hovered_row is not None:
                cor = _lighten(cor_base, 0.22) if is_hovered else _alpha_blend(cor_base, BG_CARD, 0.32)
            else:
                cor = cor_base

            cx    = pad_x + (i * slot_width) + (slot_width / 2)
            x1    = cx - bar_width / 2
            x2    = cx + bar_width / 2
            bar_h = (pct / max_pct) * area_h
            y1    = y_base - bar_h
            y2    = y_base

            if bar_h > 0:
                # ── item 1: barra reta (sem arredondamento) + gradiente ────
                self._barra_gradiente(x1, y1, x2, y2, cor)

                # ── item 5: linha de acento no topo ao selecionar ──────────
                if is_selected:
                    self.canvas.create_line(
                        x1, y1, x2, y1,
                        fill=cor_base, width=2,
                    )
                elif is_hovered and self._selected is None:
                    self.canvas.create_line(
                        x1, y1, x2, y1,
                        fill=_lighten(cor_base, 0.35), width=1,
                    )

            if slot_width >= 25:
                # ── item 6: label fixo no pad inferior (não segue a barra) ─
                if self._selected is not None and not is_selected:
                    txt_moeda = _alpha_blend(TEXT_MUTED, BG_CARD, 0.45)
                    txt_pct   = _alpha_blend(TEXT_MUTED, BG_CARD, 0.45)
                elif self._hovered_row is not None and not is_hovered and self._selected is None:
                    txt_moeda = _alpha_blend(TEXT_MUTED, BG_CARD, 0.45)
                    txt_pct   = _alpha_blend(TEXT_MUTED, BG_CARD, 0.45)
                else:
                    txt_moeda = TEXT_SECONDARY
                    txt_pct   = TEXT_PRIMARY

                self.canvas.create_text(
                    cx, y_base + 16,
                    text=moeda.upper(),
                    fill=txt_moeda,
                    font=("Segoe UI", 9, "bold"),
                )

                if pct > 0:
                    self.canvas.create_text(
                        cx, y1 - 10,
                        text=f"{pct:.1f}%",
                        fill=txt_pct,
                        font=("Segoe UI", 9, "bold"),
                    )