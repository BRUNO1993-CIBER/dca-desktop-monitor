import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Optional

from config.tema_cripto import (
    BG_CARD, BG_DEEP, BTC_ORANGE, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED
)

class DonutChart(ttk.Frame):
    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.leg_frame = ttk.Frame(self)
        self.leg_frame.pack(side=tk.LEFT, fill="y", padx=(0, 10))

        self.canvas = tk.Canvas(self, bg=BG_CARD, highlightthickness=0)
        self.canvas.pack(side=tk.RIGHT, fill="both", expand=True)
        
        cols = ("Ativo", "Alocação (%)", "Quantidade")

        style = ttk.Style()
        style.configure("Donut.Treeview")
        style.map("Donut.Treeview",
            background=[('selected', '#2c5d8f')],
            foreground=[('selected', 'white')]
        )

        self.tree = ttk.Treeview(
            self.leg_frame,
            columns=cols,
            show="headings",
            selectmode="browse",
            style="Donut.Treeview"
        )

        self.tree.heading("Ativo", text="Ativo")
        self.tree.heading("Alocação (%)", text="%")
        self.tree.heading("Quantidade", text="Quantidade")

        self.tree.column("Ativo", width=90, anchor="w")
        self.tree.column("Alocação (%)", width=70, anchor="center")
        self.tree.column("Quantidade", width=100, anchor="center")

        sb = ttk.Scrollbar(self.leg_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill="y")
        self.tree.pack(side=tk.LEFT, fill="both", expand=True)
        
        self._dados: List[tuple] = []
        self._cor_map: Dict[str, str] = {}
        self._draw_job: Optional[str] = None
        
        self.canvas.bind("<Configure>", self._on_resize)

    def atualizar_dados(self, dados: List[tuple], cor_map: Dict[str, str]) -> None:
        self._dados = dados
        self._cor_map = cor_map
        self._atualizar_tabela()
        self._agendar_desenho()

    def limpar(self) -> None:
        self._dados = []
        self.canvas.delete("all")
        for row in self.tree.get_children():
            self.tree.delete(row)

    def _atualizar_tabela(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)
            
        for moeda, d in self._dados:
            percentual = d.get("percentual", 0)
            qtd = d.get("quantidade", 0)
            qtd_str = f"{qtd:,.2f}" if moeda.upper() == "USDT" else f"{qtd:,.6f}"
            cor = self._cor_map.get(moeda, TEXT_PRIMARY)
            
            moeda_display = f"■  {moeda}"
            
            self.tree.insert("", "end", values=(moeda_display, f"{percentual:.2f}%", qtd_str), tags=(moeda,))
            self.tree.tag_configure(moeda, foreground=cor, font=("Segoe UI", 9, "bold"))

    def _on_resize(self, event: tk.Event) -> None:
        self._agendar_desenho()

    def _agendar_desenho(self) -> None:
        if self._draw_job is not None:
            self.canvas.after_cancel(self._draw_job)
        self._draw_job = self.canvas.after(100, self._desenhar)

    def _desenhar(self) -> None:
        self.canvas.delete("all")
        if not self._dados:
            return

        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if w < 50 or h < 50:
            return

        pad_x = 30
        pad_y = 40
        y_base = h - pad_y

        max_pct = max((d.get("percentual", 0) for _, d in self._dados), default=1)
        max_pct = max_pct * 1.15 if max_pct > 0 else 1

        n_ativos = len(self._dados)
        slot_width = (w - 2 * pad_x) / n_ativos
        bar_width = min(slot_width * 0.7, 60)

        self.canvas.create_line(pad_x, y_base, w - pad_x, y_base, fill=TEXT_SECONDARY, width=1)

        for i, (moeda, d) in enumerate(self._dados):
            pct = d.get("percentual", 0)
            cor = self._cor_map.get(moeda, TEXT_MUTED)

            cx = pad_x + (i * slot_width) + (slot_width / 2)
            x1 = cx - (bar_width / 2)
            x2 = cx + (bar_width / 2)

            bar_h = (pct / max_pct) * (h - 2 * pad_y)
            y1 = y_base - bar_h
            y2 = y_base

            if bar_h > 0:
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, 
                    fill=cor, outline=BG_CARD, width=1.5
                )

            if slot_width >= 25:
                self.canvas.create_text(
                    cx, y2 + 15, 
                    text=moeda, 
                    fill=TEXT_SECONDARY, 
                    font=("Segoe UI", 9, "bold")
                )
                
                if pct > 0:
                    self.canvas.create_text(
                        cx, y1 - 12, 
                        text=f"{pct:.1f}%", 
                        fill=TEXT_PRIMARY, 
                        font=("Segoe UI", 9, "bold")
                    )