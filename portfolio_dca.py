# portfolio_dca.py — Bruno Machado
# Orquestrador principal. Instancia dependencias, monta o notebook e coordena ciclos de atualizacao.

import threading
import time
import logging
import os
import platform
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
        self.janela = ThemedTk(theme="arc")
        self.janela.withdraw()
        self.janela.title("Portfolio DCA - Análise e Registro de Operações")
        self.janela.minsize(1100, 700)

        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
            caminho_icone_ico = os.path.join(base_dir, "img", "favicon.ico")
            
            caminho_icone_png = os.path.join(base_dir, "img", "favicon.png")

            if platform.system() == "Windows":
                if os.path.exists(caminho_icone_ico):
                    self.janela.iconbitmap(default=caminho_icone_ico)
            else:
                if os.path.exists(caminho_icone_png):
                    icone_img = tk.PhotoImage(file=caminho_icone_png)
                    self.janela.iconphoto(True, icone_img)
                else:
                    logger.info("Aviso: Para exibir o ícone no Linux, salve uma cópia como favicon.png na pasta img/")
        except Exception as e:
            logger.warning(f"Erro ignorado ao tentar carregar o ícone: {e}")


        style = ttk.Style(self.janela)
        style.configure(".", font=("Segoe UI", 10)) 
        style.configure("TNotebook.Tab", padding=[15, 5], font=("Segoe UI", 10, "bold"))

        self.notebook = ttk.Notebook(self.janela)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=15)
        
        self.aba_registro = JanelaRegistro(
            parent=self.notebook,
            data_manager=self.data_manager,
            price_manager=self.price_manager,
            analysis_engine=AnalysisEngine,
            moedas_suportadas=self.MOEDAS,
            on_change=self.atualizar_todas_as_analises,
        )
        
        self.aba_analise = JanelaAnalise(
            parent=self.notebook,
            data_manager=self.data_manager,
            price_manager=self.price_manager,
            analysis_engine=AnalysisEngine
        )
        
        self.aba_distribuicao = JanelaDistribuicao(
            parent=self.notebook,
            data_manager=self.data_manager,
            price_manager=self.price_manager,
            analysis_engine=AnalysisEngine
        )
        
        self.aba_historico = JanelaHistorico(
            parent=self.notebook,
            data_manager=self.data_manager,
            price_manager=self.price_manager,
            analysis_engine=AnalysisEngine
        )
        
        self.aba_edicao = JanelaEdicao(
            parent=self.notebook,
            data_manager=self.data_manager,
            price_manager=self.price_manager,
            analysis_engine=AnalysisEngine,
            on_change=self.atualizar_todas_as_analises,
        )

        self.notebook.add(self.aba_registro,     text="✏️ Registrar Operação")
        self.notebook.add(self.aba_analise,      text="📈 Análise Detalhada")
        self.notebook.add(self.aba_distribuicao, text="📊 Distribuição")
        self.notebook.add(self.aba_historico,    text="🕒 Histórico de Operações")
        self.notebook.add(self.aba_edicao,       text="⚙️ Editar Transação")

        status_frame = ttk.Frame(self.janela, relief="sunken", padding=(5, 2))
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self._status = ttk.Label(status_frame, text="Pronto", foreground="gray")
        self._status.pack(side=tk.LEFT)

        self._assinatura = ttk.Label(
            status_frame, 
            text="Dev by Bruno Machado", 
            foreground="gray", 
            font=("Segoe UI", 9, "italic")
        )
        self._assinatura.pack(side=tk.RIGHT, padx=10)

        def _mostrar_maximizada():
            self.janela.deiconify()
            try:
                self.janela.state("zoomed")
            except:
                self.janela.attributes("-zoomed", True)

        self.janela.after(1, _mostrar_maximizada)

    def _atualizar_abas_seguro(self):
        """Atualiza a parte gráfica de todas as abas de forma linear e segura"""
        try:
            self.aba_distribuicao.atualizar()
            self.aba_historico.atualizar()
            self.aba_edicao.atualizar()
            self.aba_analise.atualizar_analise()
            self._atualizar_status("Pronto")
        except Exception as e:
            logger.error(f"Erro ao desenhar atualização nas abas: {e}")
            self._atualizar_status("Erro ao atualizar interface.")

    def atualizar_todas_as_analises(self) -> None:
        def worker():
            try:
                self._atualizar_status("🔄 Atualizando preços na Binance...")
                self.price_manager.atualizar_precos(self.MOEDAS)
                
                self._atualizar_status("⚙️ Calculando portfólio...")
                
                self.janela.after(0, self._atualizar_abas_seguro)
                
            except Exception as e:
                logger.error(f"Erro na requisição de atualização: {e}")
                self._atualizar_status("⚠️ Erro de conexão com a API")

        threading.Thread(target=worker, daemon=True).start()

    def _iniciar_atualizacoes_automaticas(self) -> None:
        def worker():
            while not self._stop_updates:
                time.sleep(60) 
                
                if self._stop_updates:
                    break
                    
                if CCXT_AVAILABLE:
                    logger.info("Iniciando ciclo automático de atualização...")
                    self.atualizar_todas_as_analises()

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
            logger.info("Aplicativo iniciado com sucesso.")
            self.janela.mainloop()
        except Exception as e:
            logger.error(f"Erro fatal durante execução: {e}")
            messagebox.showerror("Erro Fatal", f"O programa foi interrompido:\n{e}")
        finally:
            self._stop_updates = True


if __name__ == "__main__":
    print("Iniciando o Monitor de Portfólio DCA...")
    try:
        app = PortfolioDCA()
        app.executar()
    except Exception as e:
        print(f"Erro crítico ao iniciar aplicação: {e}")
        input("Pressione Enter para sair...")