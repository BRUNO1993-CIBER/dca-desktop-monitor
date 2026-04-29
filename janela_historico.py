import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import logging
from typing import Any

from tema_cripto import (
    BG_SURFACE, BG_CARD, BG_INPUT,
    BTC_ORANGE, NEON_GREEN, NEON_RED,
    TEXT_PRIMARY, TEXT_SECONDARY, BORDER,
    tag_cores_treeview,
)

logger = logging.getLogger(__name__)


class JanelaHistorico(ttk.Frame):

    def __init__(self, parent: Any, data_manager: Any, price_manager: Any, analysis_engine: Any):
        super().__init__(parent, padding="10")

        self._data_manager = data_manager
        self._price_manager = price_manager
        self._analysis_engine = analysis_engine

        self._build_ui()

    def _build_ui(self) -> None:
        self._build_toolbar()
        self._build_treeview()

    def _build_toolbar(self) -> None:
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(0, 8))

        ttk.Button(
            toolbar,
            text="📂 Carregar Histórico",
            command=self.atualizar,
            cursor="hand2",
        ).pack(side=tk.LEFT)

    def _build_treeview(self) -> None:
        colunas = ("Data", "Moeda", "Operação", "Valor USDT", "Preço", "Quantidade")

        container = ttk.Frame(self, style="Card.TFrame")
        container.pack(fill="both", expand=True)

        self._tree = ttk.Treeview(
            container,
            columns=colunas,
            show="headings",
            height=15,
            style="Treeview",
        )

        scrollbar = ttk.Scrollbar(
            container,
            orient="vertical",
            command=self._tree.yview,
        )
        self._tree.configure(yscrollcommand=scrollbar.set)

        larguras = {
            "Data":       160,
            "Moeda":       90,
            "Operação":   110,
            "Valor USDT": 130,
            "Preço":      140,
            "Quantidade": 150,
        }

        for col in colunas:
            self._tree.heading(col, text=col, anchor=tk.CENTER)
            self._tree.column(col, width=larguras[col], anchor=tk.CENTER, stretch=True)

        tag_cores_treeview(self._tree)

        self._tree.tag_configure("compra",
            foreground=NEON_GREEN,
            background=BG_CARD,
            font=("Segoe UI", 9),
        )
        self._tree.tag_configure("venda",
            foreground=NEON_RED,
            background=BG_CARD,
            font=("Segoe UI", 9),
        )
        self._tree.tag_configure("compra_alt",
            foreground=NEON_GREEN,
            background="#12171e",
            font=("Segoe UI", 9),
        )
        self._tree.tag_configure("venda_alt",
            foreground=NEON_RED,
            background="#12171e",
            font=("Segoe UI", 9),
        )

        scrollbar.pack(side=tk.RIGHT, fill="y")
        self._tree.pack(side=tk.LEFT, fill="both", expand=True)

    def atualizar(self) -> None:
        self._limpar_tree()

        try:
            operacoes = self._data_manager.carregar_operacoes()
        except Exception as e:
            logger.error(f"Erro ao carregar operações: {e}")
            messagebox.showerror("Erro", f"Não foi possível carregar o histórico:\n{e}")
            return

        if not operacoes:
            return

        operacoes_ordenadas = sorted(operacoes, key=lambda x: x["Data"], reverse=True)

        for idx, op in enumerate(operacoes_ordenadas):
            self._inserir_linha(op, idx)

    def _limpar_tree(self) -> None:
        for item in self._tree.get_children():
            self._tree.delete(item)

    def _inserir_linha(self, op: dict, idx: int) -> None:
        try:
            data_fmt = datetime.strptime(
                op["Data"], "%Y-%m-%d %H:%M:%S"
            ).strftime("%d/%m/%Y %H:%M")

            tipo = op["Operacao"]
            par = idx % 2 == 0

            if tipo == "compra":
                tag = "compra" if par else "compra_alt"
            else:
                tag = "venda" if par else "venda_alt"

            self._tree.insert(
                "",
                "end",
                values=(
                    data_fmt,
                    op["Moeda"],
                    tipo.title(),
                    f"${float(op['Valor_USDT']):.2f}",
                    f"${float(op['Preco']):.4f}",
                    f"{float(op['Quantidade']):.6f}",
                ),
                tags=(tag,),
            )
        except Exception as e:
            logger.warning(f"Linha ignorada: {op} — {e}")