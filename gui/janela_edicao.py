import platform
import tkinter as tk
from tkinter import ttk, messagebox
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Optional
import logging
import threading
from datetime import datetime

# pyrefly: ignore [missing-import]
import customtkinter as ctk

from config.carregar_json import _carregar_moedas_config
from config.tema_cripto import (
    BG_SURFACE, BG_CARD, BG_INPUT,
    BTC_ORANGE, NEON_GREEN, CYAN,
    TEXT_PRIMARY, TEXT_SECONDARY, BORDER,
    tag_cores_treeview,
)

logger = logging.getLogger(__name__)

_FONT         = "Segoe UI" if platform.system() == "Windows" else "Ubuntu"
_F_TITULO     = (_FONT, 18, "bold")
_F_STATUS     = (_FONT, 11)
_F_BADGE      = (_FONT, 11, "bold")
_F_SECAO      = (_FONT, 13, "bold")
_F_CARD_TITLE = (_FONT, 12, "bold")
_F_CARD_SUB   = (_FONT, 10)
_F_CARD_VAL   = (_FONT, 15, "bold")
_F_TREE       = (_FONT, 10)
_F_TREE_HEAD  = (_FONT, 10, "bold")


def _f(t: tuple) -> ctk.CTkFont:
    weight = "bold"   if "bold"   in t else "normal"
    slant  = "italic" if "italic" in t else "roman"
    return ctk.CTkFont(t[0], t[1], weight=weight, slant=slant)


class JanelaEdicao(ctk.CTkFrame):

    _CAMPOS_EDITAVEIS = {"Data", "Taxa_BRL", "Operacao"}

    def __init__(
        self,
        parent: Any,
        data_manager: Any,
        price_manager: Any,
        analysis_engine: Any,
        on_change: Optional[Callable] = None,
    ):
        super().__init__(parent, fg_color=BG_SURFACE)

        self._data_manager    = data_manager
        self._price_manager   = price_manager
        self._analysis_engine = analysis_engine
        self._on_change       = on_change or (lambda: None)
        self._indice_editando: Optional[int] = None
        self._dados_carregados = False
        self._mapa_indices: dict = {}
        self._op_original: Optional[dict] = None
        self._carregando = False

        self._build_ui()
        self.after(100, self.atualizar)

    def _build_ui(self) -> None:
        self._build_header()
        self._build_treeview()
        self._build_form()
        self._build_obs()
        self._build_buttons()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color=BG_SURFACE)
        header.pack(fill="x", padx=10, pady=(14, 5))

        ctk.CTkLabel(
            header,
            text="Filtrar moeda:",
            font=_f(_F_CARD_SUB),
            text_color=TEXT_SECONDARY,
            fg_color=BG_SURFACE,
        ).pack(side="left", padx=(0, 4))

        self._filtro_moeda = ctk.StringVar(value="Todas")
        moedas = _carregar_moedas_config()

        self._cb_filtro = ctk.CTkComboBox(
            header,
            variable=self._filtro_moeda,
            values=moedas,
            state="readonly",
            width=130,
            font=_f(_F_CARD_SUB),
            fg_color=BG_INPUT,
            border_color=BORDER,
            button_color=BTC_ORANGE,
            dropdown_fg_color=BG_CARD,
            text_color=TEXT_PRIMARY,
            command=lambda _: self.atualizar(),
        )
        self._cb_filtro.pack(side="left", padx=(0, 16))

        self.lbl_status = ctk.CTkLabel(
            header,
            text="",
            font=_f(_F_BADGE),
            text_color=CYAN,
            fg_color=BG_SURFACE,
        )
        self.lbl_status.pack(side="left")

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

        scrollbar.pack(side="right", fill="y")
        self._tree.pack(side="left", fill="both", expand=True)

    def _build_form(self) -> None:
        outer = ctk.CTkFrame(self, fg_color=BG_CARD, border_color=BORDER, border_width=1)
        outer.pack(fill="x", padx=10, pady=(0, 4))

        ctk.CTkLabel(
            outer,
            text="EDITAR TRANSAÇÃO ⬇",
            font=_f(_F_CARD_TITLE),
            text_color=BTC_ORANGE,
            fg_color=BG_CARD,
        ).pack(anchor="w", padx=12, pady=(6, 0))

        ctk.CTkFrame(outer, fg_color=BORDER, height=1).pack(fill="x")

        center = ctk.CTkFrame(outer, fg_color=BG_CARD)
        center.pack(fill="x", expand=True)

        form = ctk.CTkFrame(center, fg_color=BG_CARD)
        form.pack(anchor="center", pady=15)

        self._campos: dict = {}

        for i, col in enumerate(self._data_manager.headers):
            is_edit  = col in self._CAMPOS_EDITAVEIS
            lbl_cor  = TEXT_PRIMARY if is_edit else TEXT_SECONDARY

            ctk.CTkLabel(
                form,
                text=col,
                font=_f(_F_TREE_HEAD),
                text_color=lbl_cor,
                fg_color=BG_CARD,
            ).grid(row=0, column=i, padx=10, pady=(0, 4), sticky="w")

            if col == "Operacao":
                widget = ctk.CTkComboBox(
                    form,
                    values=["compra", "venda"],
                    state="readonly",
                    width=160,
                    font=_f(_F_CARD_VAL),
                    fg_color=BG_INPUT,
                    border_color=BORDER,
                    button_color=BTC_ORANGE,
                    dropdown_fg_color=BG_CARD,
                    text_color=TEXT_PRIMARY,
                )
            else:
                widget = ctk.CTkEntry(
                    form,
                    width=160,
                    font=_f(_F_CARD_VAL),
                    fg_color=BG_INPUT,
                    text_color=TEXT_PRIMARY,
                    border_color=BORDER,
                    border_width=1,
                    justify="center",
                )

            widget.grid(row=1, column=i, padx=10, sticky="ew")
            self._campos[col] = widget

    def _build_obs(self) -> None:
        obs = ctk.CTkFrame(self, fg_color=BG_CARD, border_color=BORDER, border_width=1)
        obs.pack(fill="x", padx=10, pady=(0, 4))

        primeira = "🚨  SOMENTE A DATA, A TAXA BRL E A OPERACAO PODEM SER CORRIGIDAS AQUI."
        restante = (
            "Para ajustar moeda, valor, preço ou qualquer outro dado, exclua esta transação "
            "e a reinsira com as informações corretas — isso garante que todos os cálculos "
            "de quantidade, custo médio e P&L permaneçam precisos e consistentes."
        )

        ctk.CTkLabel(
            obs,
            text=f"{primeira}\n{restante}",
            font=_f(_F_CARD_SUB),
            text_color=TEXT_SECONDARY,
            fg_color=BG_CARD,
            wraplength=900,
            justify="left",
        ).pack(fill="x", padx=10, pady=5)

    def _build_buttons(self) -> None:
        btn_frame = ctk.CTkFrame(self, fg_color=BG_SURFACE)
        btn_frame.pack(pady=(12, 10))

        self.btn_load = ctk.CTkButton(
            btn_frame,
            text="📥  Carregar Selecionada",
            font=_f(_F_CARD_TITLE),
            fg_color=BG_CARD,
            text_color=CYAN,
            hover_color=CYAN,
            border_width=0,
            cursor="hand2",
            height=38,
            command=self._carregar_transacao,
        )
        self.btn_load.pack(side="left", padx=6)

        self.btn_save = ctk.CTkButton(
            btn_frame,
            text="💾  Salvar Alterações",
            font=_f(_F_CARD_TITLE),
            fg_color=NEON_GREEN,
            text_color="#000",
            hover_color=BTC_ORANGE,
            border_width=0,
            cursor="hand2",
            height=38,
            command=self._salvar_edicao,
        )
        self.btn_save.pack(side="left", padx=6)

        self.btn_delete = ctk.CTkButton(
            btn_frame,
            text="🗑️  Excluir Selecionada",
            font=_f(_F_CARD_TITLE),
            fg_color="#3a1a1a",
            text_color="#ff4d4d",
            hover_color="#ff4d4d",
            border_width=0,
            cursor="hand2",
            height=38,
            command=self._excluir_transacao,
        )
        self.btn_delete.pack(side="left", padx=6)

    def atualizar(self) -> None:
        if self._indice_editando is not None:
            return
        if self._carregando:
            return

        self._carregando = True
        self.lbl_status.configure(text="🔄 Carregando histórico...")
        self.btn_load.configure(state="disabled")
        self.btn_save.configure(state="disabled")
        self.btn_delete.configure(state="disabled")

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
            self._carregando = False
            self.after(0, lambda: self.lbl_status.configure(text="⚠️ Erro ao carregar", text_color="red"))
            logger.error(f"Erro no histórico: {e}")

    def _renderizar_tree(self, ops_com_indice: list) -> None:
        self._carregando = False
        self._mapa_indices.clear()

        moeda_sel = self._filtro_moeda.get()
        if moeda_sel != "Todas":
            ops_com_indice = [
                (orig_idx, op) for orig_idx, op in ops_com_indice
                if op.get("Moeda", "").upper() == moeda_sel.upper()
            ]

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

        self.lbl_status.configure(text="")
        self.btn_load.configure(state="normal")
        self.btn_save.configure(state="normal")
        self.btn_delete.configure(state="normal")
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
            widget = self._campos[col]
            is_edit = col in self._CAMPOS_EDITAVEIS

            if isinstance(widget, ctk.CTkComboBox):
                widget.configure(state="readonly")
                widget.set(valor)
            else:
                widget.configure(state="normal")
                valor_fmt = f"{float(valor):.2f}" if col == "Taxa_BRL" and valor != "" else valor
                widget.delete(0, "end")
                widget.insert(0, valor_fmt)
                if not is_edit:
                    widget.configure(state="readonly")

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

            nova_operacao = self._campos["Operacao"].get().strip()
            if not nova_operacao:
                messagebox.showerror("Erro", "Selecione uma operação (compra ou venda).")
                return

            nova_op = {
                **self._op_original,
                "Data": nova_data,
                "Taxa_BRL": taxa_brl,
                "Operacao": nova_operacao,
            }

            if self._data_manager.atualizar_operacao(self._indice_editando, nova_op):
                messagebox.showinfo("Sucesso", "Transação atualizada com sucesso!")
                self._indice_editando = None
                self._op_original     = None
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
                self._op_original     = None
                self._on_change()
                self.atualizar()

    def _limpar_form(self) -> None:
        for col, widget in self._campos.items():
            if isinstance(widget, ctk.CTkComboBox):
                widget.configure(state="readonly")
                widget.set("")
            else:
                widget.configure(state="normal")
                widget.delete(0, "end")
        self._indice_editando = None
        self._op_original     = None