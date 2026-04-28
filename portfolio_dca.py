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
from janela_historico import JanelaHistorico
from janela_edicao import JanelaEdicao
from janela_distribuicao import JanelaDistribuicao

logger = logging.getLogger(__name__)


class PortfolioDCA:
    def __init__(self):
        self.moedas_suportadas = ["BTC", "ETH", "SOL", "XRP", "LINK", "SUI", "NEAR", "UNI", "USDT"]
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

        self.notebook = ttk.Notebook(self.janela)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.criar_aba_registro_operacao()
        self.criar_aba_portfolio()

        self.aba_distribuicao = JanelaDistribuicao(
            self.notebook, self.data_manager, self.price_manager, AnalysisEngine
        )
        self.notebook.add(self.aba_distribuicao, text="🥧 Distribuição")

        self.aba_edicao = JanelaEdicao(
            self.notebook,
            self.data_manager,
            self.price_manager,
            AnalysisEngine,
            on_change=self.atualizar_todas_as_analises,
        )
        self.notebook.add(self.aba_edicao, text="✏️ Editar Transação")

        self.aba_historico = JanelaHistorico(
            self.notebook,
            self.data_manager,
            self.price_manager,
            AnalysisEngine,
        )
        self.notebook.add(self.aba_historico, text="📋 Histórico de Operações")

        self.status_label = ttk.Label(self.janela, text="Pronto", anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 5))

        def mostrar_maximizada():
            self.janela.deiconify()
            try:
                self.janela.state('zoomed')  # Windows
            except:
                self.janela.attributes('-zoomed', True)  # fallback Linux

        self.janela.after(1, mostrar_maximizada)

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
                self.janela.after(0, self.aba_distribuicao.atualizar)
                self.janela.after(100, self.aba_historico.atualizar)   
                self.janela.after(200, self.aba_edicao.atualizar)
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
            self.janela.after(100, self.aba_historico.atualizar)
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