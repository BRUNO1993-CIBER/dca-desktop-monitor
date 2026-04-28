import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class JanelaAnalise(ttk.Frame):
    def __init__(self, parent, data_manager, price_manager, analysis_engine):
        super().__init__(parent)
        self.data_manager = data_manager
        self.price_manager = price_manager
        self.analysis_engine = analysis_engine
        self.display_currency = 'USD'

        self._criar_interface()

    def _criar_interface(self):
        control_frame = ttk.Frame(self, padding=(5, 5))
        control_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(
            control_frame, text="🔄 Atualizar Análise",
            command=self.atualizar_analise,
            style="Accent.TButton",
            cursor="hand2"
        ).pack(side=tk.LEFT)

        self.brl_toggle_var = tk.BooleanVar()
        ttk.Checkbutton(
            control_frame, text="Exibir em BRL",
            variable=self.brl_toggle_var,
            command=self.toggle_currency,
            style="Switch.TCheckbutton"
        ).pack(side=tk.LEFT, padx=15)

        self.ultima_atualizacao_label = ttk.Label(control_frame, text="", font=("Arial", 9))
        self.ultima_atualizacao_label.pack(side=tk.RIGHT)

        summary_frame = ttk.Frame(self, padding=10)
        summary_frame.pack(fill='x')
        self._criar_labels_resumo(summary_frame)

        self.cols_analise = (
            'Ativo', 'Posição', 'Preço Médio', 'Preço Mercado',
            'Custo Posição', 'Valor Atual', 'P/L N. Realizado',
            'P/L Realizado', 'P/L Total', 'Ganho %'
        )
        self.tree = ttk.Treeview(self, columns=self.cols_analise, show='headings')

        for col in self.cols_analise:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor='center', width=135)

        self.tree.tag_configure('lucro', foreground='green')
        self.tree.tag_configure('prejuizo', foreground='red')
        self.tree.tag_configure('linha_total', font=("Arial", 10, "bold"), background='#2a2a2a')

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side='left', fill='both', expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side='right', fill='y', pady=10)

    def _criar_labels_resumo(self, parent):
        font_titulo = ("Arial", 11, "bold")
        font_valor = ("Arial", 11)

        self.resumo_valor_atual = ttk.Label(parent, text="Valor de Mercado Atual: $0.00", font=font_valor)
        self.resumo_custo_total = ttk.Label(parent, text="Custo Total (Posições Abertas): $0.00", font=font_valor)
        self.resumo_pl_geral = ttk.Label(parent, text="P/L GERAL: $0.00", font=font_titulo)

        self.resumo_valor_atual.grid(row=0, column=0, padx=10, sticky='w')
        self.resumo_custo_total.grid(row=1, column=0, padx=10, sticky='w')
        self.resumo_pl_geral.grid(row=0, column=1, rowspan=2, padx=20, sticky='w')

    def atualizar_analise(self):
        def worker():
            try:
                operacoes = self.data_manager.carregar_operacoes()

                if not operacoes:
                    self.after(0, self._limpar_e_mostrar_vazio)
                    return

                resultado = self.analysis_engine.calcular_portfolio(
                    operacoes, self.price_manager.precos_cache
                )
                resultado['_usdt_pl_brl'] = self.analysis_engine.calcular_pl_usdt_brl(
                    operacoes, self.price_manager.preco_brl
                )
                agora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                self.after(0, lambda: self.ultima_atualizacao_label.config(text=f"Última atualização: {agora}"))
                self.after(0, lambda: self.exibir_resultado_analise(resultado))

            except Exception as e:
                logger.error(f"Erro na análise: {e}")
                self.after(0, lambda: self.ultima_atualizacao_label.config(text="Erro ao atualizar"))
                self.after(0, lambda: messagebox.showerror("Erro de Análise", f"Ocorreu um erro ao processar os dados: {e}"))

        self.ultima_atualizacao_label.config(text="🔄 Atualizando...")
        for item in self.tree.get_children():
            self.tree.delete(item)

        threading.Thread(target=worker, daemon=True).start()

    def _limpar_e_mostrar_vazio(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.tree.insert('', 'end', values=("Nenhuma operação registrada ainda.", *[""] * 9))

    def exibir_resultado_analise(self, resultado):
        if not resultado:
            return

        if 'totais' in resultado:
            self.exibir_resumo_geral_labels(resultado['totais'])

        moedas_dados = {m: d for m, d in resultado.items() if m not in ('totais', '_usdt_pl_brl')}
        self._usdt_pl_brl = resultado.get('_usdt_pl_brl') 
        moedas_ordenadas = sorted(
            moedas_dados.items(),
            key=lambda item: item[1].get('valor_atual_posicao', 0),
            reverse=True
        )

        total_custo = total_valor_atual = total_pl_nao_realizado = total_pl_realizado = 0

        for moeda, dados in moedas_ordenadas:
            self.inserir_linha_analise(moeda, dados)
            total_custo += dados.get('custo_posicao_final', 0)
            total_valor_atual += dados.get('valor_atual_posicao', 0)
            total_pl_nao_realizado += dados.get('lucro_nao_realizado', 0)
            total_pl_realizado += dados.get('lucro_realizado', 0)

        total_pl_total = total_pl_nao_realizado + total_pl_realizado
        porcentagem_total = (total_pl_nao_realizado / total_custo * 100) if total_custo > 0.000001 else 0

        valores_total = (
            "📊 TOTAL GERAL", "", "", "",
            self.formatar_valor_monetario(total_custo),
            self.formatar_valor_monetario(total_valor_atual),
            self.formatar_valor_monetario(total_pl_nao_realizado),
            self.formatar_valor_monetario(total_pl_realizado),
            self.formatar_valor_monetario(total_pl_total),
            f"{porcentagem_total:+.2f}%"
        )

        tag_pl = 'lucro' if total_pl_total >= 0 else 'prejuizo'
        self.tree.insert('', 'end', values=valores_total, tags=(tag_pl, 'linha_total'))

    def exibir_resumo_geral_labels(self, totais):
        valor_atual = totais['valor_atual']
        investido_liquido = totais['investido_liquido']
        total_geral = totais['realizado'] + totais['nao_realizado']

        cor_pl = 'green' if total_geral >= 0 else 'red'

        self.resumo_valor_atual.config(text=f"Valor de Mercado Atual: {self.formatar_valor_monetario(valor_atual)}")
        self.resumo_custo_total.config(text=f"Custo Total (Posições Abertas): {self.formatar_valor_monetario(investido_liquido)}")
        self.resumo_pl_geral.config(text=f"P/L GERAL: {self.formatar_valor_monetario(total_geral)}", foreground=cor_pl)

    def inserir_linha_analise(self, moeda, dados):
        quantidade = dados.get('quantidade_final', 0)
        pmc = dados.get('pmc_final', 0)
        custo = dados.get('custo_posicao_final', 0)
        preco_mercado = dados.get('preco_de_mercado', 0)
        valor_atual = dados.get('valor_atual_posicao', 0)
        pl_n_realizado = dados.get('lucro_nao_realizado', 0)
        pl_realizado = dados.get('lucro_realizado', 0)
        pl_total = dados.get('lucro_total', 0)

        str_porcentagem = f"{(pl_n_realizado / custo * 100):+.2f}%" if custo > 0.000001 else "0.00%"

        if moeda == 'USDT (Caixa)':
            pl = getattr(self, '_usdt_pl_brl', None)
            if self.display_currency == 'BRL' and pl:
                taxa_brl = self.price_manager.preco_brl
                pmc_fmt  = f"R${pl['pmc_brl']:,.4f}"
                mkt_fmt  = f"R${taxa_brl:,.4f}"
                custo    = f"R${pl['custo_posicao_brl']:,.2f}"
                val_at   = f"R${pl['valor_atual_brl']:,.2f}"
                pl_nr    = f"R${pl['lucro_nao_realizado_brl']:+,.2f}"
                pl_re    = f"R${pl['lucro_realizado_brl']:+,.2f}"
                pl_tot   = f"R${pl['lucro_total_brl']:+,.2f}"
                pct      = f"{(pl['lucro_nao_realizado_brl'] / pl['custo_posicao_brl'] * 100):+.2f}%" if pl['custo_posicao_brl'] > 0 else "0.00%"
                tag      = 'lucro' if pl['lucro_total_brl'] >= 0 else 'prejuizo'
                valores  = (moeda, f"{quantidade:,.2f} USDT", pmc_fmt, mkt_fmt, custo, val_at, pl_nr, pl_re, pl_tot, pct)
            else:
                valores = (
                    moeda, f"{quantidade:,.2f} USDT", "N/A", "N/A",
                    self.formatar_preco(1.0), self.formatar_valor_monetario(valor_atual),
                    "N/A", "N/A", "N/A", "0.00%"
                )
                tag = ''
        else:
            valores = (
                moeda, f"{quantidade:,.8f}",
                self.formatar_preco(pmc), self.formatar_preco(preco_mercado),
                self.formatar_valor_monetario(custo), self.formatar_valor_monetario(valor_atual),
                self.formatar_valor_monetario(pl_n_realizado), self.formatar_valor_monetario(pl_realizado),
                self.formatar_valor_monetario(pl_total), str_porcentagem
            )
            tag = 'lucro' if pl_total >= 0 else 'prejuizo'

        self.tree.insert('', 'end', values=valores, tags=(tag,))

    def toggle_currency(self):
        self.display_currency = 'BRL' if self.brl_toggle_var.get() else 'USD'

        taxa_brl = self.price_manager.preco_brl
        if self.display_currency == 'BRL' and (taxa_brl is None or taxa_brl <= 0):
            messagebox.showwarning("Cotação Indisponível", "Não foi possível obter a cotação do BRL. Exibindo em USD.")
            self.display_currency = 'USD'
            self.brl_toggle_var.set(False)

        self.atualizar_analise()

    def formatar_valor_monetario(self, valor_usd):
        if self.display_currency == 'BRL':
            taxa_brl = self.price_manager.preco_brl
            if taxa_brl and taxa_brl > 0:
                return f"R${valor_usd * taxa_brl:,.2f}"
        return f"${valor_usd:,.2f}"

    def formatar_preco(self, preco_usd):
        if self.display_currency == 'BRL':
            taxa_brl = self.price_manager.preco_brl
            if taxa_brl and taxa_brl > 0:
                return f"R${preco_usd * taxa_brl:,.4f}"
        return f"${preco_usd:,.4f}"