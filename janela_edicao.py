import tkinter as tk
from tkinter import ttk, messagebox
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Optional
import logging

from tema_cripto import (
    aplicar_tema,
    BG_DEEP, BG_SURFACE, BG_CARD, BG_INPUT,
    BTC_ORANGE, NEON_GREEN, NEON_RED, CYAN,
    TEXT_PRIMARY, TEXT_SECONDARY, BORDER,
    tag_cores_treeview,
)

logger = logging.getLogger(__name__)

# FIX 3: estilo configurado uma única vez por processo, não por instância
_ESTILO_CONFIGURADO = False

def _garantir_estilo():
    global _ESTILO_CONFIGURADO
    if _ESTILO_CONFIGURADO:
        return
    style = ttk.Style()
    style.configure(
        "Cripto.TEntry",
        fieldbackground=BG_INPUT,
        foreground=TEXT_PRIMARY,
        insertcolor=BTC_ORANGE,
        bordercolor=BORDER,
        relief="solid",
    )
    style.map("Cripto.TEntry",
        bordercolor=[("focus", BTC_ORANGE)],
        fieldbackground=[("readonly", BG_CARD)],
        foreground=[("readonly", TEXT_SECONDARY)],
    )
    _ESTILO_CONFIGURADO = True


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
        self.configure(style="TFrame")

        self._data_manager = data_manager
        self._price_manager = price_manager
        self._analysis_engine = analysis_engine
        self._on_change = on_change or (lambda: None)
        self._indice_editando: Optional[int] = None
        self._dados_carregados = False  # FIX 4: controle de lazy load

        self._build_ui()

        # FIX 1: adiar o carregamento dos dados para depois que a janela aparecer
        self.after_idle(self._carregar_dados_iniciais)

    def _build_ui(self) -> None:
        self._build_treeview()
        self._build_form()
        self._build_buttons()

    def _build_treeview(self) -> None:
        container = tk.Frame(self, bg=BG_SURFACE)
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

        tag_cores_treeview(self._tree)

        scrollbar.pack(side=tk.RIGHT, fill="y")
        self._tree.pack(side=tk.LEFT, fill="both", expand=True)

    def _build_form(self) -> None:
        outer = tk.Frame(self, bg=BG_CARD, highlightbackground=BORDER, highlightthickness=1)
        outer.pack(fill="x", padx=10, pady=(0, 8))

        tk.Label(
            outer, text="EDITAR TRANSAÇÃO",
            bg=BG_CARD, fg=BTC_ORANGE,
            font=("Segoe UI", 9, "bold"),
            padx=12, pady=6,
        ).pack(anchor="w")

        tk.Frame(outer, bg=BORDER, height=1).pack(fill="x")

        form_frame = tk.Frame(outer, bg=BG_CARD, padx=12, pady=10)
        form_frame.pack(fill="x")

        self._campos: dict[str, ttk.Entry] = {}

        # FIX 3: chama função global em vez de recriar o Style aqui
        _garantir_estilo()

        for i, col in enumerate(self._data_manager.headers):
            tk.Label(
                form_frame, text=col,
                bg=BG_CARD, fg=TEXT_SECONDARY,
                font=("Segoe UI", 9, "bold"),
            ).grid(row=0, column=i, padx=6, pady=(0, 4), sticky="w")

            entry = ttk.Entry(form_frame, width=18, style="Cripto.TEntry", font=("Segoe UI", 10))
            entry.grid(row=1, column=i, padx=6, sticky="ew")
            self._campos[col] = entry

    def _build_buttons(self) -> None:
        btn_frame = tk.Frame(self, bg=BG_SURFACE)
        btn_frame.pack(pady=10)

        ttk.Button(
            btn_frame,
            text="📥  Carregar Selecionada",
            command=self._carregar_transacao,
            cursor="hand2",
        ).pack(side=tk.LEFT, padx=6)

        ttk.Button(
            btn_frame,
            text="💾  Salvar Alterações",
            command=self._salvar_edicao,
            cursor="hand2",
        ).pack(side=tk.LEFT, padx=6)

        ttk.Button(
            btn_frame,
            text="🗑️  Excluir Selecionada",
            command=self._excluir_transacao,
            style="Danger.TButton",
            cursor="hand2",
        ).pack(side=tk.LEFT, padx=6)

    # FIX 1: chamado via after_idle — janela já está visível quando executa
    def _carregar_dados_iniciais(self) -> None:
        if not self._dados_carregados:
            self._recarregar_tree()
            self._dados_carregados = True

    def atualizar(self) -> None:
        self._limpar_form()
        self._recarregar_tree()

    def _carregar_transacao(self) -> None:
        selecao = self._tree.selection()
        if not selecao:
            messagebox.showwarning("Seleção necessária", "Selecione uma transação para editar.")
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
            messagebox.showwarning("Nenhuma edição", "Nenhuma transação carregada para editar.")
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
                messagebox.showerror("Erro de Validação", "Valor USDT e Preço devem ser maiores que zero.")
                return

            moeda = self._campos["Moeda"].get()
            nova_quantidade = valor_usdt if moeda == "USDT" else valor_usdt / preco

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
            messagebox.showerror("Erro de Validação", "Valor USDT e Preço devem ser números válidos.")
        except Exception as e:
            logger.exception("Erro inesperado ao salvar edição")
            messagebox.showerror("Erro", f"Ocorreu um erro inesperado:\n{e}")

    def _excluir_transacao(self) -> None:
        if self._indice_editando is None:
            messagebox.showwarning("Seleção necessária", "Primeiro, carregue uma transação para excluir.")
            return

        if not messagebox.askyesno(
            "Confirmar Exclusão",
            "Tem certeza que deseja excluir esta transação?\nEsta ação não pode ser desfeita.",
        ):
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
            tag = "par" if i % 2 == 0 else "impar"
            # FIX 2: "end" em vez de 0 — evita re-indexação O(n²)
            self._tree.insert("", "end", iid=i, values=valores, tags=(tag,))