import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Dict, List
import threading
import time
import logging
from decimal import Decimal, InvalidOperation
from ttkthemes import ThemedTk

from backend import DataManager, PriceManager, AnalysisEngine, CCXT_AVAILABLE
from janela_de_analise import JanelaAnalise

logger = logging.getLogger(__name__)


class PortfolioDCA:
    def __init__(self):
        self.moedas_suportadas = ["BTC", "ETH", "SOL", "XRP" "LINK", "SUI", "NEAR", "UNI", "USDT"]
        self.data_manager = DataManager()
        self.price_manager = PriceManager('binance')
        self._stop_updates = False
        self.display_currency = 'USD'

        self.criar_interface()
        self.iniciar_atualizacoes_automaticas()
        self.janela.after(1000, self.atualizar_todas_as_analises)

    def criar_interface(self):
        self.janela = ThemedTk(theme="plastik")
        self.janela.withdraw()

        self.janela.title("Portfólio DCA - Análise e Registro de Operações")
        self.janela.minsize(1100, 700)

        largura_janela = 1400
        altura_janela = 800
        tela_largura = self.janela.winfo_screenwidth()
        tela_altura = self.janela.winfo_screenheight()
        x = (tela_largura // 2) - (largura_janela // 2)
        y = (tela_altura // 2) - (altura_janela // 2)

        self.janela.geometry(f"{largura_janela}x{altura_janela}+{x}+{y}")

        self.notebook = ttk.Notebook(self.janela)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.criar_aba_registro_operacao()
        self.criar_aba_portfolio()
        self.criar_aba_distribuicao()
        self.criar_aba_historico()
        self.criar_aba_edicao()

        self.status_label = ttk.Label(self.janela, text="Pronto", anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 5))

        self.janela.after(1, self.janela.deiconify)

    def criar_aba_edicao(self):
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="✏️ Editar Transação")

        self.tree_edicao = ttk.Treeview(
            frame, columns=self.data_manager.headers, show="headings", height=15
        )
        for col in self.data_manager.headers:
            self.tree_edicao.heading(col, text=col)
            self.tree_edicao.column(col, width=120, anchor="center")
        self.tree_edicao.pack(fill="both", expand=True, padx=10, pady=10)

        form_frame = ttk.Frame(frame)
        form_frame.pack(fill="x", padx=10, pady=5)

        self.edicao_campos = {}
        for i, col in enumerate(self.data_manager.headers):
            ttk.Label(form_frame, text=col, font=("Arial", 10, "bold")).grid(row=0, column=i, padx=5, pady=2)
            entry = ttk.Entry(form_frame, width=22, font=("Arial", 10))
            entry.grid(row=1, column=i, padx=5)
            self.edicao_campos[col] = entry

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="📥 Carregar Selecionada", command=self._carregar_transacao,
                   style="Accent.TButton", cursor="hand2").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="💾 Salvar Alterações", command=self._salvar_transacao_editada,
                   cursor="hand2").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ Excluir Selecionada", command=self._excluir_transacao,
                   cursor="hand2").pack(side=tk.LEFT, padx=5)

        self._atualizar_lista_edicao()

    def atualizar_distribuicao(self):
        self.distribuicao_text.delete(1.0, tk.END)
        try:
            operacoes = self.data_manager.carregar_operacoes()
            if not operacoes:
                self.distribuicao_text.insert(tk.END, "📊 Nenhuma operação registrada ainda.\n\n")
                self.distribuicao_text.insert(tk.END, "Registre suas operações na aba '✍️ Registrar Operação' para ver a distribuição do seu portfólio!")
                return

            saldo_info = AnalysisEngine.calcular_saldo_usdt(operacoes)
            saldo_atual = saldo_info['saldo_atual']

            preco_brl = self.price_manager.preco_brl
            saldo_em_brl = saldo_atual * preco_brl

            texto_saldo = f"Saldo: ${saldo_atual:,.2f} USDT"
            if preco_brl > 0:
                texto_saldo += f" (≈ R$ {saldo_em_brl:,.2f})"

            self.saldo_usdt_label.config(text=texto_saldo)

            resultado_distribuicao = AnalysisEngine.calcular_distribuicao_portfolio(operacoes, self.price_manager.precos_cache)
            self._exibir_distribuicao(resultado_distribuicao, saldo_info)

        except Exception as e:
            logger.error(f"Erro ao calcular distribuição: {e}")
            self.distribuicao_text.insert(tk.END, f"❌ Erro ao processar dados: {e}")

    def ao_mudar_selecao_formulario(self, event=None):
        self.ao_selecionar_moeda(event)
        self._atualizar_interface_venda(event)

    def _atualizar_interface_venda(self, event=None):
        moeda = self.combo_moeda.get()
        operacao = self.combo_tipo.get()

        if operacao == 'Venda' and moeda and moeda != 'USDT':
            try:
                operacoes = self.data_manager.carregar_operacoes()
                portfolio = AnalysisEngine.calcular_portfolio(operacoes, self.price_manager.precos_cache)

                saldo_moeda = 0.0
                if moeda in portfolio:
                    saldo_moeda = portfolio[moeda].get('quantidade_final', 0)

                self.label_saldo_venda.config(text=f"Saldo disponível: {saldo_moeda:.8f} {moeda}")
                self.label_saldo_venda.grid()
                self.btn_vender_tudo.grid()
            except Exception as e:
                logger.error(f"Erro ao buscar saldo para venda: {e}")
                self.label_saldo_venda.grid_remove()
                self.btn_vender_tudo.grid_remove()
        else:
            self.label_saldo_venda.grid_remove()
            self.btn_vender_tudo.grid_remove()

    def vender_tudo(self):
        moeda = self.combo_moeda.get()
        if not moeda or moeda == 'USDT':
            messagebox.showwarning("Ação inválida", "Selecione uma criptomoeda para vender.")
            return

        operacoes = self.data_manager.carregar_operacoes()
        portfolio = AnalysisEngine.calcular_portfolio(operacoes, self.price_manager.precos_cache)

        saldo_a_vender = 0.0
        if moeda in portfolio:
            saldo_a_vender = portfolio[moeda].get('quantidade_final', 0)

        if saldo_a_vender < 1e-9:
            messagebox.showinfo("Saldo Insuficiente", f"Você não possui saldo de {moeda} para vender.")
            return

        preco_atual = self.price_manager.get_preco(moeda)
        if not preco_atual or preco_atual <= 0:
            messagebox.showerror("Erro", f"Não foi possível obter o preço atual de {moeda}.")
            return

        valor_total_usdt = saldo_a_vender * preco_atual

        self.entry_valor.delete(0, tk.END)
        self.entry_valor.insert(0, f"{valor_total_usdt:.4f}")

        self.entry_preco.delete(0, tk.END)
        self.entry_preco.insert(0, f"{preco_atual:.6f}")

        self.calcular_quantidade()

    def _limpar_formulario_edicao(self):
        for header, entry in self.edicao_campos.items():
            entry.config(state='normal')
            entry.delete(0, tk.END)
        if hasattr(self, 'indice_editando'):
            del self.indice_editando

    def _excluir_transacao(self):
        if not hasattr(self, "indice_editando"):
            messagebox.showwarning("Seleção necessária", "Primeiro, carregue uma transação para excluir.")
            return

        confirm = messagebox.askyesno(
            "Confirmar Exclusão",
            "Tem certeza que deseja excluir esta transação?\nEsta ação não pode ser desfeita."
        )
        if not confirm:
            return

        if self.data_manager.excluir_operacao(self.indice_editando):
            messagebox.showinfo("Sucesso", "Transação excluída com sucesso!")
            self._limpar_formulario_edicao()
            self.atualizar_todas_as_analises()
        else:
            messagebox.showerror("Erro", "Não foi possível excluir a transação.")

    def _atualizar_lista_edicao(self):
        for item in self.tree_edicao.get_children():
            self.tree_edicao.delete(item)

        operacoes = self.data_manager.carregar_operacoes()
        for i, op in enumerate(operacoes):
            valores = [op[h] for h in self.data_manager.headers]
            self.tree_edicao.insert("", "end", iid=i, values=valores)

    def _carregar_transacao(self):
        item_selecionado = self.tree_edicao.selection()
        if not item_selecionado:
            messagebox.showwarning("Seleção necessária", "Selecione uma transação para editar.")
            return

        self._limpar_formulario_edicao()

        item = item_selecionado[0]
        indice = int(self.tree_edicao.index(item))
        valores = self.tree_edicao.item(item, "values")

        for h, v in zip(self.data_manager.headers, valores):
            entry = self.edicao_campos[h]
            entry.insert(0, v)
            if h in ['Moeda', 'Operacao', 'Quantidade']:
                entry.config(state='readonly')

        self.indice_editando = indice

    def _salvar_transacao_editada(self):
        if not hasattr(self, "indice_editando"):
            messagebox.showwarning("Nenhuma edição", "Nenhuma transação carregada para editar.")
            return

        try:
            data = self.edicao_campos['Data'].get()
            valor_usdt_str = self.edicao_campos['Valor_USDT'].get()
            preco_str = self.edicao_campos['Preco'].get()

            valor_usdt = Decimal(valor_usdt_str)
            preco = Decimal(preco_str)

            if valor_usdt <= 0 or preco <= 0:
                messagebox.showerror("Erro de Validação", "Valor USDT e Preço devem ser maiores que zero.")
                return

            nova_quantidade = valor_usdt / preco

            nova_op = {
                'Data': data,
                'Moeda': self.edicao_campos['Moeda'].get(),
                'Operacao': self.edicao_campos['Operacao'].get(),
                'Valor_USDT': float(valor_usdt),
                'Preco': float(preco),
                'Quantidade': float(nova_quantidade)
            }

            if self.data_manager.atualizar_operacao(self.indice_editando, nova_op):
                messagebox.showinfo("Sucesso", "Transação atualizada com sucesso!")
                self._limpar_formulario_edicao()
                self.atualizar_todas_as_analises()
            else:
                messagebox.showerror("Erro", "Não foi possível atualizar a transação.")

        except InvalidOperation:
            messagebox.showerror("Erro de Validação", "Valor USDT e Preço devem ser números válidos.")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro inesperado: {e}")

    def criar_aba_registro_operacao(self):
        frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(frame, text="✍️ Registrar Operação")

        ttk.Label(frame, text="Registrar Nova Operação", font=("Arial", 16, "bold")).pack(pady=(0, 20))

        form_frame = ttk.Frame(frame)
        form_frame.pack(pady=10)

        self._criar_campos_formulario(form_frame)

        style = ttk.Style()
        style.configure("Accent.TButton", font=("Arial", 12, "bold"))

        ttk.Button(frame, text="💾 Salvar Operação", command=self.salvar_operacao,
                   style="Accent.TButton", padding=(20, 10), cursor="hand2").pack(pady=30)

    def _criar_campos_formulario(self, parent):
        ttk.Label(parent, text="Moeda:", font=("Arial", 11)).grid(row=0, column=0, sticky='w', pady=5)
        self.combo_moeda = ttk.Combobox(parent, values=self.moedas_suportadas, width=20, font=("Arial", 11))
        self.combo_moeda.grid(row=0, column=1, pady=5, padx=10)
        self.combo_moeda.bind('<<ComboboxSelected>>', self.ao_mudar_selecao_formulario)

        self.preco_atual_label = ttk.Label(parent, text="", font=("Arial", 10), foreground='blue')
        self.preco_atual_label.grid(row=0, column=2, padx=10)

        ttk.Label(parent, text="Operação:", font=("Arial", 11)).grid(row=1, column=0, sticky='w', pady=5)
        self.combo_tipo = ttk.Combobox(parent, values=["Compra", "Venda"], width=20, font=("Arial", 11))
        self.combo_tipo.grid(row=1, column=1, pady=5, padx=10)
        self.combo_tipo.set("Compra")
        self.combo_tipo.bind('<<ComboboxSelected>>', self.ao_mudar_selecao_formulario)

        ttk.Label(parent, text="Valor (USDT):", font=("Arial", 11)).grid(row=2, column=0, sticky='w', pady=5)
        self.entry_valor = ttk.Entry(parent, width=22, font=("Arial", 11))
        self.entry_valor.grid(row=2, column=1, pady=5, padx=10)
        self.entry_valor.bind('<KeyRelease>', self.calcular_quantidade)

        self.quantidade_label = ttk.Label(parent, text="", font=("Arial", 10), foreground='gray')
        self.quantidade_label.grid(row=2, column=2, padx=10)

        ttk.Label(parent, text="Preço Unitário:", font=("Arial", 11)).grid(row=3, column=0, sticky='w', pady=5)
        self.entry_preco = ttk.Entry(parent, width=22, font=("Arial", 11))
        self.entry_preco.grid(row=3, column=1, pady=5, padx=10)
        self.entry_preco.bind('<KeyRelease>', self.calcular_quantidade)

        ttk.Button(parent, text="Usar Preço Atual", command=self.usar_preco_atual,
                   cursor="hand2").grid(row=3, column=2, pady=5, padx=10, sticky='w')

        self.label_saldo_venda = ttk.Label(parent, text="", font=("Arial", 10, "bold"), foreground='darkblue')
        self.label_saldo_venda.grid(row=4, column=0, columnspan=2, sticky='w', padx=5, pady=(10, 0))
        self.btn_vender_tudo = ttk.Button(parent, text="Vender Tudo", command=self.vender_tudo, cursor="hand2")
        self.btn_vender_tudo.grid(row=4, column=2, pady=(10, 0), padx=10, sticky='w')

        self.label_saldo_venda.grid_remove()
        self.btn_vender_tudo.grid_remove()

    def criar_aba_distribuicao(self):
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="🥧 Distribuição")

        control_frame = ttk.Frame(frame)
        control_frame.pack(fill='x', padx=10, pady=10)

        ttk.Button(control_frame, text="🔄 Atualizar Distribuição", command=self.atualizar_distribuicao,
                   style="Accent.TButton", cursor="hand2").pack(side=tk.LEFT)
        ttk.Button(control_frame, text="💰 Saldo USDT", command=self.mostrar_saldo_usdt,
                   cursor="hand2").pack(side=tk.LEFT, padx=(10, 0))

        self.saldo_usdt_label = ttk.Label(control_frame, text="", font=("Arial", 10, "bold"), foreground='#2E7D32')
        self.saldo_usdt_label.pack(side=tk.RIGHT)

        self.distribuicao_text = tk.Text(frame, wrap='word', font=("Consolas", 11),
                                         relief='flat', padx=15, pady=15, bg="#fafafa")
        self.distribuicao_text.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        self.distribuicao_text.tag_configure("titulo", font=("Consolas", 14, "bold"), foreground="#2E7D32")
        self.distribuicao_text.tag_configure("subtitulo", font=("Consolas", 12, "bold"), foreground="#1976D2")
        self.distribuicao_text.tag_configure("moeda", font=("Consolas", 11, "bold"), foreground="#5D4037")
        self.distribuicao_text.tag_configure("percentual", font=("Consolas", 11, "bold"), foreground="#D84315")
        self.distribuicao_text.tag_configure("valor", foreground="#1565C0")
        self.distribuicao_text.tag_configure("total", font=("Consolas", 12, "bold"), foreground="#E65100")
        self.distribuicao_text.tag_configure("usdt_info", font=("Consolas", 11, "bold"), foreground="#2E7D32")
        self.distribuicao_text.tag_configure("erro", foreground="red", font=("Consolas", 10, "bold"))

    def criar_aba_historico(self):
        frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(frame, text="📋 Histórico de Operações")

        controls = ttk.Frame(frame)
        controls.pack(fill='x', pady=(0, 10))

        ttk.Button(controls, text="📂 Carregar Histórico", command=self.carregar_historico,
                   style="Accent.TButton").pack(side=tk.LEFT)

        cols = ('Data', 'Moeda', 'Operação', 'Valor USDT', 'Preço', 'Quantidade')
        self.tree = ttk.Treeview(frame, columns=cols, show='headings', height=15)

        for col in cols:
            self.tree.heading(col, text=col)
            width = 150 if col != 'Quantidade' else 120
            self.tree.column(col, width=width, anchor=tk.CENTER)

        self.tree.pack(fill='both', expand=True)
        self.tree.tag_configure('compra', background='#e8f5e8')
        self.tree.tag_configure('venda', background='#ffe8e8')

    def mostrar_saldo_usdt(self):
        try:
            operacoes = self.data_manager.carregar_operacoes()
            if not operacoes:
                messagebox.showinfo("Saldo USDT", "Nenhuma operação registrada ainda.")
                return

            saldo_info = AnalysisEngine.calcular_saldo_usdt(operacoes)
            historico = saldo_info['historico']
            saldo_atual = saldo_info['saldo_atual']

            janela_saldo = tk.Toplevel(self.janela)
            janela_saldo.title("💰 Histórico Saldo USDT")
            janela_saldo.geometry("600x400")

            frame_saldo = ttk.Frame(janela_saldo, padding=10)
            frame_saldo.pack(fill='x', padx=10, pady=10)

            preco_brl = self.price_manager.preco_brl
            saldo_em_brl = saldo_atual * preco_brl

            texto_saldo_popup = f"💰 Saldo Atual: ${saldo_atual:,.2f} USDT"
            if preco_brl > 0:
                texto_saldo_popup += f"\n(≈ R$ {saldo_em_brl:,.2f})"

            ttk.Label(frame_saldo, text=texto_saldo_popup, font=("Arial", 14, "bold"),
                      foreground='#2E7D32').pack()

            text_historico = tk.Text(janela_saldo, wrap='word', font=("Consolas", 10), bg='#fafafa')
            text_historico.pack(fill='both', expand=True, padx=10, pady=(0, 10))

            if historico:
                text_historico.insert(tk.END, "📋 HISTÓRICO DE MOVIMENTAÇÕES:\n")
                text_historico.insert(tk.END, "=" * 60 + "\n\n")

                for mov in reversed(historico):
                    data_formatada = datetime.strptime(mov['data'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')
                    text_historico.insert(tk.END, f"[{data_formatada}] ")
                    text_historico.insert(tk.END, mov['descricao'])
                    text_historico.insert(tk.END, f"\n   └─ Saldo após: ${mov['saldo_apos']:,.2f} USDT\n\n")
            else:
                text_historico.insert(tk.END, "Nenhuma movimentação registrada ainda.")

        except Exception as e:
            logger.error(f"Erro ao mostrar saldo USDT: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar histórico: {e}")

    def _exibir_distribuicao(self, resultado: Dict, saldo_info: Dict = None):
        self.distribuicao_text.delete(1.0, tk.END)
        distribuicao = resultado['distribuicao']
        total_investido = resultado['total_investido']

        saldo_usdt = saldo_info['saldo_atual'] if saldo_info else 0
        valor_total_portfolio = total_investido + saldo_usdt

        preco_brl = self.price_manager.preco_brl

        def converter_para_brl(valor_usdt):
            if preco_brl > 0:
                return f" (≈ R$ {valor_usdt * preco_brl:,.2f})"
            return ""

        if saldo_info:
            self.distribuicao_text.insert(tk.END, "💰 INFORMAÇÕES USDT:\n", "usdt_info")
            texto_caixa_usdt = f"   Saldo disponível (Caixa): ${saldo_usdt:,.2f} USDT"
            if preco_brl > 0:
                texto_caixa_usdt += f" (≈ R$ {saldo_usdt * preco_brl:,.2f})"
            self.distribuicao_text.insert(tk.END, texto_caixa_usdt + "\n", "valor")
            if saldo_usdt < 0:
                self.distribuicao_text.insert(tk.END, "   ⚠️  ATENÇÃO: Saldo negativo!\n", "erro")
            self.distribuicao_text.insert(tk.END, "\n")

        if not distribuicao and saldo_usdt <= 0:
            self.distribuicao_text.insert(tk.END, "📊 Nenhuma posição ativa encontrada.")
            return

        self.distribuicao_text.insert(tk.END, "=" * 70 + "\n")
        self.distribuicao_text.insert(tk.END, "🥧 DISTRIBUIÇÃO DO PORTFÓLIO\n", "titulo")
        self.distribuicao_text.insert(tk.END, "=" * 70 + "\n\n")

        self.distribuicao_text.insert(tk.END, f"   Total Investido (Cripto): ${total_investido:,.2f}{converter_para_brl(total_investido)}\n")
        self.distribuicao_text.insert(tk.END, f"   Saldo em Caixa (USDT):   ${saldo_usdt:,.2f}{converter_para_brl(saldo_usdt)}\n")
        self.distribuicao_text.insert(tk.END, f"💰 Valor Total do Portfólio: ${valor_total_portfolio:,.2f}{converter_para_brl(valor_total_portfolio)}\n\n", "total")

        moedas_ordenadas = sorted(distribuicao.items(), key=lambda x: x[1]['percentual'], reverse=True)

        self.distribuicao_text.insert(tk.END, "📋 DISTRIBUIÇÃO POR ATIVO:\n", "subtitulo")
        self.distribuicao_text.insert(tk.END, "-" * 70 + "\n")
        self.distribuicao_text.insert(tk.END, f"{'ATIVO':<8} {'PERCENTUAL':<12} {'VALOR ATUAL ($)':<18} {'QUANTIDADE':<15}\n")
        self.distribuicao_text.insert(tk.END, "-" * 70 + "\n")

        for moeda, dados in moedas_ordenadas:
            percentual = dados['percentual']
            valor_atual = dados['valor_atual']
            quantidade = dados['quantidade']

            self.distribuicao_text.insert(tk.END, f"{moeda:<8}", "moeda")
            self.distribuicao_text.insert(tk.END, f"{percentual:>7.2f}%    ", "percentual")
            self.distribuicao_text.insert(tk.END, f"${valor_atual:>13,.2f}    ", "valor")
            linha_quantidade = f"{quantidade:>10.2f}" if moeda == 'USDT' else f"{quantidade:>10.6f}"
            self.distribuicao_text.insert(tk.END, linha_quantidade + "\n")

        self.distribuicao_text.insert(tk.END, "-" * 70 + "\n\n")

        self.distribuicao_text.insert(tk.END, "📊 GRÁFICO DE BARRAS:\n", "subtitulo")
        self.distribuicao_text.insert(tk.END, "-" * 50 + "\n")

        for moeda, dados in moedas_ordenadas:
            percentual = dados['percentual']
            barra = "█" * int((percentual / 100) * 40)
            self.distribuicao_text.insert(tk.END, f"{moeda:<6}", "moeda")
            self.distribuicao_text.insert(tk.END, f" [{barra:<40}] ", "valor")
            self.distribuicao_text.insert(tk.END, f"{percentual:>6.2f}%\n", "percentual")

        self.distribuicao_text.insert(tk.END, "\n")
        self.distribuicao_text.insert(tk.END, "📈 RESUMO:\n", "subtitulo")
        self.distribuicao_text.insert(tk.END, f"   • Número de ativos diferentes: {len(distribuicao)}\n")

        if moedas_ordenadas:
            self.distribuicao_text.insert(tk.END, f"   • Maior concentração: {moedas_ordenadas[0][0]} ({moedas_ordenadas[0][1]['percentual']:.2f}%)\n", "moeda")
            if len(moedas_ordenadas) > 1:
                self.distribuicao_text.insert(tk.END, f"   • Menor concentração: {moedas_ordenadas[-1][0]} ({moedas_ordenadas[-1][1]['percentual']:.2f}%)\n", "moeda")

        if len(distribuicao) == 1:
            diversificacao = "🔴 Portfólio 100% alocado em um ativo"
        elif len(distribuicao) <= 3:
            diversificacao = "🟡 Portfólio pouco diversificado"
        elif len(distribuicao) <= 6:
            diversificacao = "🟢 Portfólio moderadamente diversificado"
        else:
            diversificacao = "🟢 Portfólio bem diversificado"

        self.distribuicao_text.insert(tk.END, f"   • Status: {diversificacao}\n\n")

    def salvar_operacao(self):
        erros = self._validar_campos_operacao()
        if erros:
            messagebox.showerror("Erro de Validação", "\n".join(erros))
            return

        try:
            moeda = self.combo_moeda.get().strip().upper()
            tipo = self.combo_tipo.get().strip().lower()
            valor = Decimal(self.entry_valor.get())
            preco = Decimal(self.entry_preco.get())

            if preco <= 0:
                raise InvalidOperation("Preço inválido")

            quantidade = valor / preco

            if tipo == 'compra' and moeda != 'USDT':
                operacoes = self.data_manager.carregar_operacoes()
                validacao = AnalysisEngine.validar_saldo_suficiente(operacoes, float(valor))

                if not validacao['saldo_suficiente']:
                    saldo_atual = validacao['saldo_atual']
                    faltam = abs(validacao['diferenca'])

                    resposta = messagebox.askquestion(
                        "Saldo USDT Insuficiente",
                        f"Saldo atual: ${saldo_atual:,.2f} USDT\n"
                        f"Valor da compra: ${float(valor):,.2f} USDT\n"
                        f"Faltam: ${faltam:,.2f} USDT\n\n"
                        f"Deseja continuar mesmo assim?",
                        icon='warning'
                    )

                    if resposta == 'no':
                        return

            data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            operacao = [data_hora, moeda, tipo, float(valor), float(preco), float(quantidade)]

            if not self.data_manager.salvar_operacao(operacao):
                messagebox.showerror("Erro", "Não foi possível salvar a operação.")
                return

            if moeda == 'USDT':
                acao = "Depósito" if tipo == 'compra' else "Saque"
                mensagem = f"{acao} de ${valor:,.2f} USDT registrado!"
            else:
                mensagem = f"{tipo.title()} de {moeda} registrada! Saldo USDT atualizado."

            messagebox.showinfo("Sucesso", mensagem)
            self._limpar_formulario()
            self.atualizar_todas_as_analises()

        except InvalidOperation:
            messagebox.showerror("Erro de Validação", "Valor e preço devem ser números válidos e maiores que zero.")
        except Exception as e:
            logger.exception("Erro ao salvar operação")
            messagebox.showerror("Erro", f"Erro inesperado: {e}")

    def _validar_campos_operacao(self) -> List[str]:
        erros = []
        if not self.combo_moeda.get():
            erros.append("Selecione uma moeda")
        if not self.combo_tipo.get():
            erros.append("Selecione o tipo de operação")
        try:
            if float(self.entry_valor.get()) <= 0:
                erros.append("Valor deve ser maior que zero")
        except ValueError:
            erros.append("Valor deve ser um número válido")
        try:
            if float(self.entry_preco.get()) <= 0:
                erros.append("Preço deve ser maior que zero")
        except ValueError:
            erros.append("Preço deve ser um número válido")
        return erros

    def _limpar_formulario(self):
        self.entry_valor.delete(0, tk.END)
        self.entry_preco.config(state='normal')
        self.entry_preco.delete(0, tk.END)
        self.quantidade_label.config(text="")
        self.preco_atual_label.config(text="")

    def carregar_historico(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            operacoes = self.data_manager.carregar_operacoes()
            if not operacoes:
                return

            operacoes.sort(key=lambda x: x['Data'], reverse=True)
            for op in operacoes:
                try:
                    data_formatada = datetime.strptime(op['Data'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')
                    tag = ('compra',) if op['Operacao'] == 'compra' else ('venda',)
                    self.tree.insert('', 'end', values=(
                        data_formatada, op['Moeda'], op['Operacao'].title(),
                        f"${float(op['Valor_USDT']):.2f}", f"${float(op['Preco']):.4f}",
                        f"{float(op['Quantidade']):.6f}"
                    ), tags=tag)
                except Exception as e:
                    logger.warning(f"Erro ao processar operação: {e}")
        except Exception as e:
            logger.error(f"Erro ao carregar histórico: {e}")
            messagebox.showerror("Erro", f"Não foi possível carregar o histórico: {e}")

    def ao_selecionar_moeda(self, event=None):
        moeda = self.combo_moeda.get()

        if moeda == "USDT":
            self.preco_atual_label.config(text="Stablecoin: $1.00")
            self.entry_preco.config(state='normal')
            self.entry_preco.delete(0, tk.END)
            self.entry_preco.insert(0, "1.000000")
            self.entry_preco.config(state='disabled')
            self.calcular_quantidade()
            return

        self.entry_preco.config(state='normal')
        preco = self.price_manager.get_preco(moeda)
        if preco:
            self.preco_atual_label.config(text=f"Atual: ${preco:.4f}")
            self.entry_preco.delete(0, tk.END)
            self.entry_preco.insert(0, f"{preco:.6f}")
            self.calcular_quantidade()
        else:
            self.preco_atual_label.config(text="Preço indisponível")

    def calcular_quantidade(self, event=None):
        try:
            valor = float(self.entry_valor.get())
            preco = float(self.entry_preco.get())
            if valor > 0 and preco > 0:
                quantidade = valor / preco
                moeda = self.combo_moeda.get()
                if moeda == "USDT":
                    self.quantidade_label.config(text=f"= {quantidade:.2f} USDT")
                else:
                    self.quantidade_label.config(text=f"≈ {quantidade:.6f} unidades")
            else:
                self.quantidade_label.config(text="")
        except (ValueError, ZeroDivisionError):
            self.quantidade_label.config(text="")

    def usar_preco_atual(self):
        moeda = self.combo_moeda.get()

        if moeda == "USDT":
            self.entry_preco.config(state='normal')
            self.entry_preco.delete(0, tk.END)
            self.entry_preco.insert(0, "1.000000")
            self.entry_preco.config(state='disabled')
            self.calcular_quantidade()
            return

        self.entry_preco.config(state='normal')
        preco = self.price_manager.get_preco(moeda)
        if preco:
            self.entry_preco.delete(0, tk.END)
            self.entry_preco.insert(0, f"{preco:.6f}")
            self.calcular_quantidade()
        else:
            messagebox.showwarning("Aviso", "Preço não disponível.")

    def atualizar_todas_as_analises(self):
        def worker():
            try:
                self.atualizar_status("Atualizando preços...")
                self.price_manager.atualizar_precos(self.moedas_suportadas)
                self.atualizar_status("Calculando análises...")
                self.janela.after(0, self.atualizar_distribuicao)
                self.janela.after(100, self.carregar_historico)
                self.janela.after(200, self._atualizar_lista_edicao)
                self.janela.after(300, self.aba_analise.atualizar_analise)
                self.atualizar_status("Análises atualizadas!")
            except Exception as e:
                logger.error(f"Erro na atualização: {e}")
                self.atualizar_status(f"Erro: {e}")

        threading.Thread(target=worker, daemon=True).start()

    def criar_aba_portfolio(self):
        self.aba_analise = JanelaAnalise(self.notebook, self.data_manager, self.price_manager, AnalysisEngine)
        self.notebook.add(self.aba_analise, text="📊 Análise Detalhada")

    def iniciar_atualizacoes_automaticas(self):
        def worker():
            while not self._stop_updates:
                try:
                    if CCXT_AVAILABLE:
                        self.price_manager.atualizar_precos(self.moedas_suportadas)
                    time.sleep(60)
                except Exception as e:
                    logger.error(f"Erro na atualização automática: {e}")
                    time.sleep(60)

        threading.Thread(target=worker, daemon=True).start()

    def atualizar_status(self, mensagem: str):
        def update():
            self.status_label.config(text=mensagem)
            self.janela.update_idletasks()

        if threading.current_thread() is threading.main_thread():
            update()
        else:
            self.janela.after(0, update)

    def on_closing(self):
        self._stop_updates = True
        self.janela.destroy()

    def executar(self):
        try:
            self.janela.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.carregar_historico()
            logger.info("Aplicação iniciada com sucesso")
            self.janela.mainloop()
        except Exception as e:
            logger.error(f"Erro durante execução: {e}")
            messagebox.showerror("Erro Fatal", f"Erro durante execução: {e}")
        finally:
            self._stop_updates = True


if __name__ == "__main__":
    print("🚀 Iniciando o Monitor de Portfólio DCA...")
    try:
        app = PortfolioDCA()
        app.executar()
    except Exception as e:
        print(f"❌ Erro ao iniciar aplicação: {e}")
        input("Pressione Enter para sair...")