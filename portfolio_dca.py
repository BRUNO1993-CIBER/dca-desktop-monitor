# portfolio_dca.py — Bruno Machado
# Orquestrador principal. Instancia dependencias, monta o notebook e coordena ciclos de atualizacao.

import threading
import time
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from ttkthemes import ThemedTk

from backend import DataManager, PriceManager, AnalysisEngine, CCXT_AVAILABLE
from janela_de_analise import JanelaAnalise
from janela_historico import JanelaHistorico
from janela_edicao import JanelaEdicao
from janela_distribuicao import JanelaDistribuicao
from janela_registro import JanelaRegistro

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class PortfolioDCA:

    MOEDAS = ["BTC", "ETH", "SOL", "XRP", "LINK", "SUI", "NEAR", "UNI", "USDT"]

    def __init__(self):
        self.data_manager  = DataManager()
        self.price_manager = PriceManager("binance")
        self._stop_updates = False

        self._criar_interface()
        self._iniciar_atualizacoes_automaticas()
        self.janela.after(1000, self.atualizar_todas_as_analises)

    def _criar_interface(self) -> None:
        self.janela = ThemedTk(theme="plastik")
        self.janela.withdraw()
        self.janela.title("Portfolio DCA - Analise e Registro de Operacoes")
        self.janela.minsize(1100, 700)

        self.notebook = ttk.Notebook(self.janela)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        deps = (self.data_manager, self.price_manager, AnalysisEngine)

        self.aba_registro = JanelaRegistro(
            self.notebook, *deps,
            moedas_suportadas=self.MOEDAS,
            on_change=self.atualizar_todas_as_analises,
        )
        self.aba_analise      = JanelaAnalise(self.notebook, *deps)
        self.aba_distribuicao = JanelaDistribuicao(self.notebook, *deps)
        self.aba_historico    = JanelaHistorico(self.notebook, *deps)
        self.aba_edicao       = JanelaEdicao(
            self.notebook, *deps,
            on_change=self.atualizar_todas_as_analises,
        )

        self.notebook.add(self.aba_registro,     text="Registrar Operacao")
        self.notebook.add(self.aba_analise,      text="Analise Detalhada")
        self.notebook.add(self.aba_distribuicao, text="Distribuicao")
        self.notebook.add(self.aba_historico,    text="Historico de Operacoes")
        self.notebook.add(self.aba_edicao,       text="Editar Transacao")

        self._status = ttk.Label(self.janela, text="Pronto", anchor=tk.W)
        self._status.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 5))

        def _mostrar_maximizada():
            self.janela.deiconify()
            try:
                self.janela.state("zoomed")
            except:
                self.janela.attributes("-zoomed", True)

        self.janela.after(1, _mostrar_maximizada)

    def atualizar_todas_as_analises(self) -> None:
        def worker():
            try:
                self._atualizar_status("Atualizando precos...")
                self.price_manager.atualizar_precos(self.MOEDAS)
                self._atualizar_status("Calculando analises...")
                self.janela.after(0,   self.aba_distribuicao.atualizar)
                self.janela.after(100, self.aba_historico.atualizar)
                self.janela.after(200, self.aba_edicao.atualizar)
                self.janela.after(300, self.aba_analise.atualizar_analise)
                self._atualizar_status("Pronto")
            except Exception as e:
                logger.error(f"Erro na atualizacao: {e}")
                self._atualizar_status(f"Erro: {e}")

        threading.Thread(target=worker, daemon=True).start()

    def _iniciar_atualizacoes_automaticas(self) -> None:
        def worker():
            while not self._stop_updates:
                try:
                    if CCXT_AVAILABLE:
                        self.price_manager.atualizar_precos(self.MOEDAS)
                except Exception as e:
                    logger.error(f"Erro na atualizacao automatica: {e}")
                finally:
                    time.sleep(60)

        threading.Thread(target=worker, daemon=True).start()

    def _atualizar_status(self, mensagem: str) -> None:
        def _update():
            self._status.config(text=mensagem)
            self.janela.update_idletasks()

        if threading.current_thread() is threading.main_thread():
            _update()
        else:
            self.janela.after(0, _update)

    def _on_closing(self) -> None:
        self._stop_updates = True
        self.janela.destroy()

    def executar(self) -> None:
        try:
            self.janela.protocol("WM_DELETE_WINDOW", self._on_closing)
            self.aba_historico.atualizar()
            logger.info("Aplicacao iniciada com sucesso")
            self.janela.mainloop()
        except Exception as e:
            logger.error(f"Erro durante execucao: {e}")
            messagebox.showerror("Erro Fatal", f"Erro durante execucao: {e}")
        finally:
            self._stop_updates = True


if __name__ == "__main__":
    print("Iniciando o Monitor de Portfolio DCA...")
    try:
        app = PortfolioDCA()
        app.executar()
    except Exception as e:
        print(f"Erro ao iniciar aplicacao: {e}")
        input("Pressione Enter para sair...")