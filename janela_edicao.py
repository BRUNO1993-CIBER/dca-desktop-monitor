import tkinter as tk
from tkinter import ttk, messagebox
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Optional
import logging
import threading
from datetime import datetime

from tema_cripto import (
    BG_SURFACE, BG_CARD, BG_INPUT,
    BTC_ORANGE, NEON_GREEN, CYAN,
    TEXT_PRIMARY, TEXT_SECONDARY, BORDER,
    tag_cores_treeview,
)

logger = logging.getLogger(__name__)

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
        self._dados_carregados = False
        self._mapa_indices = {}

        self._build_ui()
        self.after(100, self.atualizar)

    def _build_ui(self) -> None:
        self._build_header()
        self._build_treeview()
        self._build_form()
        self._build_buttons()

    def _build_header(self) -> None:
        header_frame = tk.Frame(self, bg=BG_SURFACE)
        header_frame.pack(fill="x", padx=10, pady=(0, 5))

        self.lbl_status = tk.Label(
            header_frame, text="",
            bg=BG_SURFACE, fg=CYAN,
            font=("Segoe UI", 10, "bold")
        )
        self.lbl_status.pack(side=tk.LEFT)

    def _build_treeview(self) -> None:
        container = tk.Frame(self, bg=BG_SURFACE)
        container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self._tree = ttk.Treeview(
            container,
            columns=self._data_manager.headers,
            show="headings",
            height=10,
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

        center_container = tk.Frame(outer, bg=BG_CARD)
        center_container.pack(fill="x", expand=True)

        form_frame = tk.Frame(center_container, bg=BG_CARD, pady=15)
        form_frame.pack(anchor="center")

        self._campos = {}
        _garantir_estilo()

        for i, col in enumerate(self._data_manager.headers):
            tk.Label(
                form_frame, text=col,
                bg=BG_CARD, fg=TEXT_SECONDARY,
                font=("Segoe UI", 9, "bold"),
            ).grid(row=0, column=i, padx=10, pady=(0, 4), sticky="w")

            entry = ttk.Entry(form_frame, width=16, style="Cripto.TEntry", font=("Segoe UI", 10), justify="center")
            entry.grid(row=1, column=i, padx=10, sticky="ew")
            self._campos[col] = entry

    def _build_buttons(self) -> None:
        btn_frame = tk.Frame(self, bg=BG_SURFACE)
        btn_frame.pack(pady=10)

        self.btn_load = ttk.Button(
            btn_frame, text="📥  Carregar Selecionada",
            command=self._carregar_transacao, cursor="hand2"
        )
        self.btn_load.pack(side=tk.LEFT, padx=6)

        self.btn_save = ttk.Button(
            btn_frame, text="💾  Salvar Alterações",
            command=self._salvar_edicao, cursor="hand2"
        )
        self.btn_save.pack(side=tk.LEFT, padx=6)

        self.btn_delete = ttk.Button(
            btn_frame, text="🗑️  Excluir Selecionada",
            command=self._excluir_transacao, style="Danger.TButton", cursor="hand2"
        )
        self.btn_delete.pack(side=tk.LEFT, padx=6)

    def atualizar(self) -> None:
        self.lbl_status.config(text="🔄 Carregando histórico...")
        self.btn_load.config(state="disabled")
        self.btn_save.config(state="disabled")
        self.btn_delete.config(state="disabled")
        
        for item in self._tree.get_children():
            self._tree.delete(item)
            
        threading.Thread(target=self._worker_carregar_dados, daemon=True).start()

    def _worker_carregar_dados(self) -> None:
        try:
            operacoes = self._data_manager.carregar_operacoes()
            ops_com_indice = list(enumerate(operacoes))

            def get_data_segura(op):
                try:
                    return datetime.strptime(op[1]["Data"], "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    return datetime.min

            ops_com_indice.sort(key=get_data_segura, reverse=True)

            self.after(0, lambda: self._renderizar_tree(ops_com_indice))
        except Exception as e:
            self.after(0, lambda: self.lbl_status.config(text="⚠️ Erro ao carregar", fg="red"))
            logger.error(f"Erro no histórico: {e}")

    def _renderizar_tree(self, ops_com_indice: list) -> None:
        self._mapa_indices.clear()
        
        for visual_idx, (orig_idx, op) in enumerate(ops_com_indice):
            valores = [op.get(h, "") for h in self._data_manager.headers]
            tag = "par" if visual_idx % 2 == 0 else "impar"
            
            item_id = self._tree.insert("", "end", values=valores, tags=(tag,))
            self._mapa_indices[item_id] = orig_idx

        self.lbl_status.config(text="")
        self.btn_load.config(state="normal")
        self.btn_save.config(state="normal")
        self.btn_delete.config(state="normal")
        self._limpar_form()

    def _carregar_transacao(self) -> None:
        selecao = self._tree.selection()
        if not selecao:
            messagebox.showwarning("Aviso", "Selecione uma transação.")
            return

        self._limpar_form()
        item = selecao[0]
        self._indice_editando = self._mapa_indices.get(item)
        valores = self._tree.item(item, "values")

        for col, valor in zip(self._data_manager.headers, valores):
            entry = self._campos[col]
            entry.config(state="normal")
            entry.insert(0, valor)
            if col in self._CAMPOS_READONLY:
                entry.config(state="readonly")

    def _salvar_edicao(self) -> None:
        if self._indice_editando is None:
            messagebox.showwarning("Aviso", "Carregue uma transação.")
            return

        try:
            data = self._campos["Data"].get().strip()
            valor_usdt = Decimal(self._campos["Valor_USDT"].get().strip())
            preco = Decimal(self._campos["Preco"].get().strip())

            if not data or valor_usdt <= 0 or preco <= 0:
                raise ValueError

            moeda = self._campos["Moeda"].get()
            nova_quantidade = valor_usdt if moeda == "USDT" else valor_usdt / preco
            campo_taxa = self._campos.get("Taxa_BRL")
            taxa_brl = float(campo_taxa.get() or 0) if campo_taxa else 0.0

            nova_op = {
                "Data": data,
                "Moeda": moeda,
                "Operacao": self._campos["Operacao"].get(),
                "Valor_USDT": float(valor_usdt),
                "Preco": float(preco),
                "Quantidade": float(nova_quantidade),
                "Taxa_BRL": taxa_brl,
            }

            if self._data_manager.atualizar_operacao(self._indice_editando, nova_op):
                messagebox.showinfo("Sucesso", "Atualizado com sucesso!")
                self._on_change()
                self.atualizar()

        except (InvalidOperation, ValueError):
            messagebox.showerror("Erro", "Valores numéricos inválidos ou dados vazios.")

    def _excluir_transacao(self) -> None:
        if self._indice_editando is None:
            messagebox.showwarning("Aviso", "Carregue uma transação.")
            return

        if messagebox.askyesno("Confirmar", "Tem certeza que deseja excluir?"):
            if self._data_manager.excluir_operacao(self._indice_editando):
                messagebox.showinfo("Sucesso", "Excluído com sucesso!")
                self._on_change()
                self.atualizar()

    def _limpar_form(self) -> None:
        for entry in self._campos.values():
            entry.config(state="normal")
            entry.delete(0, tk.END)
        self._indice_editando = None