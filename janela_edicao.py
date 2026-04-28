# janela_edicao.py

import tkinter as tk
from tkinter import ttk, messagebox
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Optional
import logging

logger = logging.getLogger(__name__)


class JanelaEdicao(ttk.Frame):

    _CAMPOS_READONLY = {"Moeda", "Operacao", "Quantidade"}

    def __init__(
        self,
        parent: Any,
        data_manager: Any,
        price_manager: Any,
        analysis_engine: Any,
        on_change: Optional[Callable] = None,
    ):

        super().__init__(parent, padding=10)

        self._data_manager = data_manager
        self._price_manager = price_manager
        self._analysis_engine = analysis_engine
        self._on_change = on_change or (lambda: None)

        self._indice_editando: Optional[int] = None

        self._build_ui()

    def _build_ui(self) -> None:
        self._build_treeview()
        self._build_form()
        self._build_buttons()

    def _build_treeview(self) -> None:
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        self._tree = ttk.Treeview(
            container,
            columns=self._data_manager.headers,
            show="headings",
            height=12,
        )

        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)

        for col in self._data_manager.headers:
            self._tree.heading(col, text=col)
            self._tree.column(col, width=130, anchor="center")

        scrollbar.pack(side=tk.RIGHT, fill="y")
        self._tree.pack(side=tk.LEFT, fill="both", expand=True)

    def _build_form(self) -> None:

        form_frame = ttk.Frame(self)
        form_frame.pack(fill="x", padx=10, pady=5)

        self._campos: dict[str, ttk.Entry] = {}

        for i, col in enumerate(self._data_manager.headers):
            ttk.Label(
                form_frame, text=col, font=("Arial", 10, "bold")
            ).grid(row=0, column=i, padx=5, pady=2)

            entry = ttk.Entry(form_frame, width=22, font=("Arial", 10))
            entry.grid(row=1, column=i, padx=5)
            self._campos[col] = entry

    def _build_buttons(self) -> None:
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)

        ttk.Button(
            btn_frame,
            text="📥 Carregar Selecionada",
            command=self._carregar_transacao,
            style="Accent.TButton",
            cursor="hand2",
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="💾 Salvar Alterações",
            command=self._salvar_edicao,
            cursor="hand2",
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="🗑️ Excluir Selecionada",
            command=self._excluir_transacao,
            cursor="hand2",
        ).pack(side=tk.LEFT, padx=5)


    def atualizar(self) -> None:

        self._limpar_form()
        self._recarregar_tree()


    def _carregar_transacao(self) -> None:

        selecao = self._tree.selection()
        if not selecao:
            messagebox.showwarning(
                "Seleção necessária", "Selecione uma transação para editar."
            )
            return

        self._limpar_form()

        item = selecao[0]
        self._indice_editando = int(self._tree.index(item))
        valores = self._tree.item(item, "values")

        for col, valor in zip(self._data_manager.headers, valores):
            entry = self._campos[col]
            entry.config(state="normal")
            entry.insert(0, valor)
            if col in self._CAMPOS_READONLY:
                entry.config(state="readonly")

    def _salvar_edicao(self) -> None:

        if self._indice_editando is None:
            messagebox.showwarning(
                "Nenhuma edição", "Nenhuma transação carregada para editar."
            )
            return

        try:
            data      = self._campos["Data"].get().strip()
            valor_str = self._campos["Valor_USDT"].get().strip()
            preco_str = self._campos["Preco"].get().strip()

            if not data:
                messagebox.showerror("Erro de Validação", "O campo Data não pode estar vazio.")
                return

            valor_usdt = Decimal(valor_str)
            preco      = Decimal(preco_str)

            if valor_usdt <= 0 or preco <= 0:
                messagebox.showerror(
                    "Erro de Validação",
                    "Valor USDT e Preço devem ser maiores que zero."
                )
                return

            moeda = self._campos["Moeda"].get()

            if moeda == 'USDT':
                nova_quantidade = valor_usdt
            else:
                nova_quantidade = valor_usdt / preco

            campo_taxa = self._campos.get("Taxa_BRL")
            taxa_brl   = float(campo_taxa.get() or 0) if campo_taxa else 0.0

            nova_op = {
                "Data":       data,
                "Moeda":      moeda,
                "Operacao":   self._campos["Operacao"].get(),
                "Valor_USDT": float(valor_usdt),
                "Preco":      float(preco),
                "Quantidade": float(nova_quantidade),
                "Taxa_BRL":   taxa_brl,
            }

            if not self._data_manager.atualizar_operacao(self._indice_editando, nova_op):
                messagebox.showerror("Erro", "Não foi possível atualizar a transação.")
                return

            messagebox.showinfo("Sucesso", "Transação atualizada com sucesso!")
            self._limpar_form()
            self._on_change()

        except InvalidOperation:
            messagebox.showerror(
                "Erro de Validação", "Valor USDT e Preço devem ser números válidos."
            )
        except Exception as e:
            logger.exception("Erro inesperado ao salvar edição")
            messagebox.showerror("Erro", f"Ocorreu um erro inesperado:\n{e}")

    def _excluir_transacao(self) -> None:

        if self._indice_editando is None:
            messagebox.showwarning(
                "Seleção necessária",
                "Primeiro, carregue uma transação para excluir."
            )
            return

        confirmado = messagebox.askyesno(
            "Confirmar Exclusão",
            "Tem certeza que deseja excluir esta transação?\nEsta ação não pode ser desfeita."
        )
        if not confirmado:
            return

        if not self._data_manager.excluir_operacao(self._indice_editando):
            messagebox.showerror("Erro", "Não foi possível excluir a transação.")
            return

        messagebox.showinfo("Sucesso", "Transação excluída com sucesso!")
        self._limpar_form()

        self._on_change()

    def _limpar_form(self) -> None:

        for entry in self._campos.values():
            entry.config(state="normal")
            entry.delete(0, tk.END)

        self._indice_editando = None

    def _recarregar_tree(self) -> None:
        for item in self._tree.get_children():
            self._tree.delete(item)

        operacoes = self._data_manager.carregar_operacoes()
        for i, op in enumerate(operacoes):
            valores = [op[h] for h in self._data_manager.headers]
            self._tree.insert("", 0, iid=i, values=valores)  


