# Edição restrita a 'Data' e 'Taxa_BRL' por design intencional: qualquer alteração em Moeda,
# Operação, Valor ou Preço invalida cálculos derivados (quantidade, médias, P&L).
# A solução correta é excluir e reinserir — sem debt técnico de recálculo retroativo.

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

    # Todos os campos são somente-leitura; apenas 'Data' e 'Taxa_BRL' são editáveis.
    _CAMPOS_EDITAVEIS = {"Data", "Taxa_BRL"}

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
        self._op_original: Optional[dict] = None

        self._build_ui()
        self.after(100, self.atualizar)

    def _build_ui(self) -> None:
        self._build_header()
        self._build_treeview()
        self._build_form()
        self._build_obs()
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
        outer.pack(fill="x", padx=10, pady=(0, 4))

        tk.Label(
            outer, text="EDITAR TRANSAÇÃO ⬇",
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
            is_editavel = col in self._CAMPOS_EDITAVEIS
            label_fg = TEXT_PRIMARY if is_editavel else TEXT_SECONDARY

            tk.Label(
                form_frame, text=col,
                bg=BG_CARD, fg=label_fg,
                font=("Segoe UI", 9, "bold"),
            ).grid(row=0, column=i, padx=10, pady=(0, 4), sticky="w")

            entry = ttk.Entry(form_frame, width=22, style="Cripto.TEntry", font=("Segoe UI", 12), justify="center")

            entry.grid(row=1, column=i, padx=10, sticky="ew")
            self._campos[col] = entry

    def _build_obs(self) -> None:
        obs_frame = tk.Frame(self, bg=BG_CARD, highlightbackground=BORDER, highlightthickness=1)
        obs_frame.pack(fill="x", padx=10, pady=(0, 8))

        tk.Label(
            obs_frame,
            text="ATENÇÃO 🚨",
            bg=BG_CARD,
            fg=TEXT_PRIMARY,
            font=("Segoe UI", 14, "bold"),
            padx=6,
            pady=10
        ).pack(side=tk.LEFT, fill="y", anchor="center")

        tk.Frame(obs_frame, bg=BORDER, width=1)\
            .pack(side=tk.LEFT, fill="y", pady=6)

        primeira_linha = "SOMENTE A DATA E A TAXA BRL PODEM SER CORRIGIDAS AQUI."
        restante = (
            "Para ajustar moeda, valor, preço ou qualquer outro dado, exclua esta transação "
            "e a reinsira com as informações corretas — isso garante que todos os cálculos "
            "de quantidade, custo médio e P&L permaneçam precisos e consistentes."
        )

        obs_text = f"{primeira_linha}\n{restante}"

        tk.Label(
            obs_frame,
            text=obs_text,
            bg=BG_CARD,
            fg=TEXT_SECONDARY,
            font=("Segoe UI", 9),
            wraplength=800,
            justify="left",
            padx=6,
            pady=10
        ).pack(side=tk.LEFT, fill="x", expand=True)
            
    def _build_buttons(self) -> None:
        btn_frame = tk.Frame(self, bg=BG_SURFACE)
        btn_frame.pack(pady=(12, 10)) 

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
        # Bloqueia refresh automático de 60s enquanto usuário tem transação carregada
        if self._indice_editando is not None:
            return

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
            valores = []
            for h in self._data_manager.headers:
                v = op.get(h, "")
                if h == "Taxa_BRL" and v != "":
                    try:
                        v = f"{float(v):.2f}"
                    except (ValueError, TypeError):
                        pass
                valores.append(v)

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

        operacoes = self._data_manager.carregar_operacoes()
        self._op_original = operacoes[self._indice_editando]

        for col, valor in zip(self._data_manager.headers, valores):
            entry = self._campos[col]
            entry.config(state="normal")
            valor_fmt = f"{float(valor):.2f}" if col == "Taxa_BRL" and valor != "" else valor
            entry.insert(0, valor_fmt)
            if col not in self._CAMPOS_EDITAVEIS:
                entry.config(state="readonly")

    def _salvar_edicao(self) -> None:
        if self._indice_editando is None or self._op_original is None:
            messagebox.showwarning("Aviso", "Carregue uma transação.")
            return

        try:
            nova_data = self._campos["Data"].get().strip()
            if not nova_data:
                raise ValueError("Data vazia.")
            datetime.strptime(nova_data, "%Y-%m-%d %H:%M:%S")

            campo_taxa = self._campos.get("Taxa_BRL")
            taxa_brl = round(float(campo_taxa.get().strip() or 0), 2) if campo_taxa else self._op_original.get("Taxa_BRL", 0.0)

            if taxa_brl != 0 and taxa_brl <= 1.1:
                messagebox.showerror(
                    "Erro",
                    "Taxa BRL inválida.\nUse o valor real do dólar (ex: 5.87).\nValores entre 0 e 1.10 são ignorados nos cálculos."
                )
                return

            nova_op = {**self._op_original, "Data": nova_data, "Taxa_BRL": taxa_brl}

            if self._data_manager.atualizar_operacao(self._indice_editando, nova_op):
                messagebox.showinfo("Sucesso", "Transação atualizada com sucesso!")
                self._indice_editando = None
                self._op_original = None
                self._on_change()
                self.atualizar()

        except ValueError:
            messagebox.showerror(
                "Erro",
                "Dados inválidos.\nData: AAAA-MM-DD HH:MM:SS\nTaxa BRL: valor numérico"
            )

    def _excluir_transacao(self) -> None:
        if self._indice_editando is None:
            messagebox.showwarning("Aviso", "Carregue uma transação.")
            return

        if messagebox.askyesno("Confirmar", "Tem certeza que deseja excluir?"):
            if self._data_manager.excluir_operacao(self._indice_editando):
                messagebox.showinfo("Sucesso", "Excluído com sucesso!")
                self._indice_editando = None
                self._op_original = None
                self._on_change()
                self.atualizar()

    def _limpar_form(self) -> None:
        for entry in self._campos.values():
            entry.config(state="normal")
            entry.delete(0, tk.END)
        self._indice_editando = None
        self._op_original = None