# =============================================================================
# janela_edicao.py
# =============================================================================
#
# POR QUE ESTA ABA É A MAIS IMPORTANTE DA ARQUITETURA?
# ─────────────────────────────────────────────────────────────────────────────
# JanelaHistorico só LÊ dados — ela nunca precisa avisar ninguém.
# JanelaEdicao ESCREVE dados — depois de salvar ou excluir, todas as outras
# abas precisam se atualizar (distribuição, histórico, análise).
#
# O problema: como a aba avisa o orquestrador sem conhecê-lo?
#
# SOLUÇÃO: CALLBACK INJETADO (on_change)
# ─────────────────────────────────────────────────────────────────────────────
# O orquestrador passa uma função no construtor:
#
#   JanelaEdicao(parent, data_manager, price_manager, engine,
#                on_change=self.atualizar_todas_as_analises)
#
# A aba guarda essa função e chama quando muda algo:
#
#   self._on_change()   ← dispara o ciclo de atualização no orquestrador
#
# A aba não sabe O QUE acontece depois — só avisa que algo mudou.
# O orquestrador decide quem atualiza e em que ordem.
#
# FLUXO COMPLETO:
#
#   Usuário clica "Salvar" ou "Excluir"
#       │
#       ├── JanelaEdicao escreve no data_manager
#       ├── JanelaEdicao chama self._on_change()
#       │       │
#       │       └── PortfolioDCA.atualizar_todas_as_analises()
#       │               ├── aba_distribuicao.atualizar()
#       │               ├── aba_historico.atualizar()
#       │               ├── aba_edicao.atualizar()      ← a própria aba!
#       │               └── aba_analise.atualizar_analise()
#       │
#       └── Tela inteira reflete o novo estado
#
# =============================================================================

import tkinter as tk
from tkinter import ttk, messagebox
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Optional
import logging

logger = logging.getLogger(__name__)


class JanelaEdicao(ttk.Frame):
    """
    Aba de edição e exclusão de transações existentes.

    Responsabilidades:
      - Listar todas as transações numa Treeview
      - Permitir carregar uma transação nos campos de edição
      - Validar e salvar alterações (recalcula quantidade automaticamente)
      - Excluir transações com confirmação
      - Notificar o orquestrador via on_change após qualquer escrita
    """

    # Campos que não podem ser alterados pelo usuário (integridade da operação)
    _CAMPOS_READONLY = {"Moeda", "Operacao", "Quantidade"}

    # ------------------------------------------------------------------
    # CONSTRUÇÃO
    # ------------------------------------------------------------------

    def __init__(
        self,
        parent: Any,
        data_manager: Any,
        price_manager: Any,
        analysis_engine: Any,
        on_change: Optional[Callable] = None,
    ):
        """
        Parameters
        ----------
        parent          : widget pai (ttk.Notebook do PortfolioDCA)
        data_manager    : instância de DataManager
        price_manager   : instância de PriceManager (não usado diretamente,
                          mantido para assinatura uniforme entre abas)
        analysis_engine : classe AnalysisEngine (idem)
        on_change       : callable sem argumentos chamado após qualquer
                          escrita no data_manager. Normalmente aponta para
                          PortfolioDCA.atualizar_todas_as_analises.
                          Se None, a aba funciona normalmente mas nenhuma
                          outra aba será notificada — útil em testes.
        """
        super().__init__(parent, padding=10)

        self._data_manager = data_manager
        self._price_manager = price_manager
        self._analysis_engine = analysis_engine
        self._on_change = on_change or (lambda: None)

        # Índice da transação atualmente carregada nos campos de edição.
        # None significa "nenhuma transação selecionada".
        self._indice_editando: Optional[int] = None

        self._build_ui()

    def _build_ui(self) -> None:
        self._build_treeview()
        self._build_form()
        self._build_buttons()

    def _build_treeview(self) -> None:
        """Lista de todas as transações — fonte de seleção para edição."""
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
        """
        Campos de edição gerados dinamicamente a partir dos headers.

        self._campos é um dict { nome_coluna: ttk.Entry }
        Mantemos a referência pra poder ler, limpar e travar cada campo.
        """
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
        """Barra de ações — carregar, salvar, excluir."""
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

    # ------------------------------------------------------------------
    # API PÚBLICA
    # ------------------------------------------------------------------

    def atualizar(self) -> None:
        """
        Recarrega a lista de transações da Treeview.

        Chamado pelo orquestrador após qualquer mudança nos dados,
        inclusive as que a própria aba gerou (via _on_change).
        Também limpa o formulário para evitar editar um índice stale.
        """
        self._limpar_form()
        self._recarregar_tree()

    # ------------------------------------------------------------------
    # AÇÕES DOS BOTÕES
    # ------------------------------------------------------------------

    def _carregar_transacao(self) -> None:
        """
        Copia os valores da linha selecionada para os campos de edição.

        Campos readonly (Moeda, Operacao, Quantidade) são travados para
        evitar edições que quebrariam a integridade dos cálculos.
        Quantidade é recalculada automaticamente ao salvar.
        """
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
        """
        Valida os campos editáveis, reconstrói a operação e persiste.

        REGRA DE NEGÓCIO: Quantidade não é campo livre — é sempre
        recalculada como Valor_USDT / Preco. Isso garante consistência
        interna dos dados independente do que o usuário digitar.

        Após salvar com sucesso: limpa o form e dispara _on_change,
        que aciona o ciclo de atualização de todas as abas.
        """
        if self._indice_editando is None:
            messagebox.showwarning(
                "Nenhuma edição", "Nenhuma transação carregada para editar."
            )
            return

        try:
            data        = self._campos["Data"].get().strip()
            valor_str   = self._campos["Valor_USDT"].get().strip()
            preco_str   = self._campos["Preco"].get().strip()

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

            # Quantidade recalculada — nunca vem do campo (que é readonly)
            nova_quantidade = valor_usdt / preco

            nova_op = {
                "Data":       data,
                "Moeda":      self._campos["Moeda"].get(),
                "Operacao":   self._campos["Operacao"].get(),
                "Valor_USDT": float(valor_usdt),
                "Preco":      float(preco),
                "Quantidade": float(nova_quantidade),
            }

            if not self._data_manager.atualizar_operacao(self._indice_editando, nova_op):
                messagebox.showerror("Erro", "Não foi possível atualizar a transação.")
                return

            messagebox.showinfo("Sucesso", "Transação atualizada com sucesso!")
            self._limpar_form()

            # Avisa o orquestrador — ele decide quem e quando atualiza
            self._on_change()

        except InvalidOperation:
            messagebox.showerror(
                "Erro de Validação", "Valor USDT e Preço devem ser números válidos."
            )
        except Exception as e:
            logger.exception("Erro inesperado ao salvar edição")
            messagebox.showerror("Erro", f"Ocorreu um erro inesperado:\n{e}")

    def _excluir_transacao(self) -> None:
        """
        Exclui a transação carregada após confirmação do usuário.

        Segue o mesmo padrão de _salvar_edicao: escreve, limpa, notifica.
        A confirmação via messagebox é obrigatória — exclusão é irreversível.
        """
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

        # Mesmo padrão: escrevi → notifico → orquestrador propaga
        self._on_change()

    # ------------------------------------------------------------------
    # MÉTODOS PRIVADOS DE SUPORTE
    # ------------------------------------------------------------------

    def _limpar_form(self) -> None:
        """
        Reseta todos os campos e descarta o índice em edição.

        Sempre habilita os campos antes de limpar — alguns podem estar
        em estado 'readonly' de uma seleção anterior.
        """
        for entry in self._campos.values():
            entry.config(state="normal")
            entry.delete(0, tk.END)

        self._indice_editando = None

    def _recarregar_tree(self) -> None:
        """Limpa e repopula a Treeview com os dados atuais."""
        for item in self._tree.get_children():
            self._tree.delete(item)

        operacoes = self._data_manager.carregar_operacoes()
        for i, op in enumerate(operacoes):
            valores = [op[h] for h in self._data_manager.headers]
            self._tree.insert("", "end", iid=i, values=valores)


