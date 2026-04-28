# =============================================================================
# janela_historico.py
# =============================================================================
#
# PADRÃO ARQUITETURAL USADO AQUI
# ─────────────────────────────────────────────────────────────────────────────
# Esta aba segue o padrão "Frame Subclassado com Injeção de Dependência".
#
# REGRAS DO PADRÃO:
#
#   1. A classe herda de ttk.Frame — ela É um frame, não cria janela própria.
#      O notebook do pai simplesmente faz: notebook.add(JanelaHistorico(...))
#
#   2. As dependências (data_manager, price_manager, analysis_engine) são
#      INJETADAS pelo construtor. A aba nunca instancia nada por conta própria.
#      Isso permite trocar implementações, mockar em testes, etc.
#
#   3. A aba expõe UM método público: atualizar()
#      O orquestrador (PortfolioDCA) chama esse método quando quiser
#      que a aba se redesenhe. A aba não sabe nada sobre o orquestrador.
#
#   4. A aba nunca chama código de outra aba diretamente.
#      Se precisar avisar que algo mudou (ex: salvou um dado), usa um
#      callback injetado — veja janela_edicao.py como exemplo com on_change.
#
#   5. Toda construção de widgets fica em _build_ui(), chamado no __init__.
#      Mantém o construtor limpo e facilita entender o que a classe faz.
#
# FLUXO DE DADOS:
#
#   PortfolioDCA
#       │
#       ├── instancia JanelaHistorico(parent, data_manager, price_manager, engine)
#       │
#       └── quando dados mudam, chama: aba_historico.atualizar()
#               │
#               └── JanelaHistorico lê do data_manager e redesenha a Treeview
#
# =============================================================================

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import logging
from typing import Any

logger = logging.getLogger(__name__)


class JanelaHistorico(ttk.Frame):
    """
    Aba de histórico de operações.

    Responsabilidade única: exibir a lista de operações registradas,
    ordenadas da mais recente para a mais antiga, com cores por tipo.

    Não escreve dados. Não conhece outras abas. Não chama callbacks.
    """

    # ------------------------------------------------------------------
    # CONSTRUÇÃO
    # ------------------------------------------------------------------

    def __init__(
        self,
        parent: Any,
        data_manager: Any,
        price_manager: Any,
        analysis_engine: Any,
    ):
        """
        Parameters
        ----------
        parent          : widget pai (o ttk.Notebook do PortfolioDCA)
        data_manager    : instância de DataManager  — leitura/escrita de ops
        price_manager   : instância de PriceManager — preços em cache
        analysis_engine : classe AnalysisEngine     — cálculos de portfólio

        Nota: price_manager e analysis_engine não são usados aqui agora,
        mas são recebidos para manter a assinatura uniforme entre todas as
        abas. Se amanhã precisar mostrar valor atual de cada posição no
        histórico, já está disponível sem mudar a interface.
        """
        super().__init__(parent, padding="10")

        # Guarda as dependências como atributos privados.
        # Prefixo _ = uso interno da classe, não parte da API pública.
        self._data_manager = data_manager
        self._price_manager = price_manager
        self._analysis_engine = analysis_engine

        # Constrói todos os widgets.
        self._build_ui()

    def _build_ui(self) -> None:
        """
        Monta o layout da aba.

        Separar a construção de widgets do __init__ tem duas vantagens:
          - __init__ fica legível (só inicialização de estado)
          - _build_ui pode ser testada ou chamada isoladamente se necessário
        """
        self._build_toolbar()
        self._build_treeview()

    def _build_toolbar(self) -> None:
        """Barra superior com o botão de atualização manual."""
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(0, 8))

        ttk.Button(
            toolbar,
            text="📂 Carregar Histórico",
            command=self.atualizar,      # método público, documentado abaixo
            style="Accent.TButton",
            cursor="hand2",
        ).pack(side=tk.LEFT)

    def _build_treeview(self) -> None:
        """
        Tabela principal de operações + scrollbar vertical.

        A Treeview é guardada em self._tree para que atualizar() possa
        limpar e repovoar sem precisar recriar os widgets.
        """
        colunas = ("Data", "Moeda", "Operação", "Valor USDT", "Preço", "Quantidade")

        # Frame intermediário para agrupar tree + scrollbar
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)

        self._tree = ttk.Treeview(
            container,
            columns=colunas,
            show="headings",
            height=15,
        )

        scrollbar = ttk.Scrollbar(
            container,
            orient="vertical",
            command=self._tree.yview,
        )
        self._tree.configure(yscrollcommand=scrollbar.set)

        # Configuração das colunas — largura e alinhamento
        larguras = {
            "Data": 140,
            "Moeda": 80,
            "Operação": 100,
            "Valor USDT": 120,
            "Preço": 130,
            "Quantidade": 140,
        }
        for col in colunas:
            self._tree.heading(col, text=col)
            self._tree.column(col, width=larguras[col], anchor=tk.CENTER)

        # Tags de cor: compra = fundo verde-claro, venda = vermelho-claro
        self._tree.tag_configure("compra", background="#e8f5e8")
        self._tree.tag_configure("venda", background="#ffe8e8")

        # Pack: tree ocupa tudo, scrollbar fica na direita
        scrollbar.pack(side=tk.RIGHT, fill="y")
        self._tree.pack(side=tk.LEFT, fill="both", expand=True)

    # ------------------------------------------------------------------
    # API PÚBLICA — chamada pelo orquestrador
    # ------------------------------------------------------------------

    def atualizar(self) -> None:
        print("atualizando historico")
        """
        Recarrega e exibe todas as operações do data_manager.

        Este é o único método que o PortfolioDCA precisa conhecer.
        Chamado:
          - automaticamente a cada ciclo de atualização
          - manualmente pelo botão "📂 Carregar Histórico"
        """
        self._limpar_tree()

        try:
            operacoes = self._data_manager.carregar_operacoes()
        except Exception as e:
            logger.error(f"Erro ao carregar operações: {e}")
            messagebox.showerror("Erro", f"Não foi possível carregar o histórico:\n{e}")
            return

        if not operacoes:
            return

        # Ordena da mais recente para a mais antiga antes de exibir
        operacoes_ordenadas = sorted(operacoes, key=lambda x: x["Data"], reverse=True)

        for op in operacoes_ordenadas:
            self._inserir_linha(op)

    # ------------------------------------------------------------------
    # MÉTODOS PRIVADOS — detalhes de implementação
    # ------------------------------------------------------------------

    def _limpar_tree(self) -> None:
        """Remove todas as linhas da Treeview."""
        for item in self._tree.get_children():
            self._tree.delete(item)

    def _inserir_linha(self, op: dict) -> None:
        """
        Formata e insere uma operação como linha na Treeview.

        Erros de formatação em uma linha específica são logados mas não
        interrompem a exibição das demais — comportamento tolerante a falhas.
        """
        try:
            data_fmt = datetime.strptime(
                op["Data"], "%Y-%m-%d %H:%M:%S"
            ).strftime("%d/%m/%Y %H:%M")

            tipo = op["Operacao"]
            tag = ("compra",) if tipo == "compra" else ("venda",)

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
                tags=tag,
            )
        except Exception as e:
            logger.warning(f"Linha ignorada por erro de formatação: {op} — {e}")


