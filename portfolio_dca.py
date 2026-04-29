import threading
import time
import logging
import os
import platform
import tkinter as tk
from tkinter import ttk, messagebox
from ttkthemes import ThemedTk
from concurrent.futures import ThreadPoolExecutor

if platform.system() == "Windows":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

from backend import DataManager, PriceManager, AnalysisEngine, CCXT_AVAILABLE
from janela_de_analise import JanelaAnalise
from janela_historico import JanelaHistorico
from janela_edicao import JanelaEdicao
from janela_distribuicao import JanelaDistribuicao
from janela_registro import JanelaRegistro

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

MOEDAS_SUPORTADAS = ["BTC", "ETH", "SOL", "XRP", "LINK", "SUI", "NEAR", "UNI", "USDT"]

class InicializadorSplash:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Portfolio DCA - Iniciando...")
        self.root.resizable(False, False)
        self.root.withdraw()
            
        self.sucesso = False
        self.data_manager = None
        self.price_manager = None
        self._start_time = time.time()
        self._status_msg = "Iniciando sistema..."
        
        self._construir_interface()
        self._maximizar_e_mostrar()
        
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._future = self._executor.submit(self._carregar_dados)
        self.root.after(100, self._checar_thread)

    def _maximizar_e_mostrar(self):
        self.root.update_idletasks()
        try:
            self.root.state("zoomed")
        except:
            self.root.attributes("-zoomed", True)
        
        self.root.deiconify()

        base_dir = os.path.dirname(os.path.abspath(__file__))
        caminho_ico = os.path.join(base_dir, "img", "favicon.ico")
        caminho_png = os.path.join(base_dir, "img", "favicon.png")
        
        try:
            if platform.system() == "Windows" and os.path.exists(caminho_ico):
                self.root.iconbitmap(caminho_ico)
            if os.path.exists(caminho_png):
                icone_img = tk.PhotoImage(file=caminho_png)
                self.root.iconphoto(True, icone_img)
        except Exception:
            pass

    def _construir_interface(self):
            self.root.configure(bg="#f8f9fa")
            
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
            caminho_bg = os.path.join(base_dir, "img", "988124.png")
            try:
                if os.path.exists(caminho_bg):
                    self.bg_image = tk.PhotoImage(file=caminho_bg)
                    bg_label = tk.Label(self.root, image=self.bg_image)
                    bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            except Exception as e:
                logger.warning(f"Não foi possível carregar o fundo da splash: {e}")

            container = tk.Frame(self.root, bg="#ffffff", highlightbackground="#dee2e6", highlightthickness=2, padx=40, pady=30)
            container.place(relx=0.5, rely=0.5, anchor="center")

            caminho_png = os.path.join(base_dir, "img", "favicon.png")
            
            try:
                if os.path.exists(caminho_png):
                    self._icone = tk.PhotoImage(file=caminho_png).subsample(2, 2)
                    tk.Label(container, image=self._icone, bg="#ffffff").pack(pady=(0, 15))
            except Exception:
                pass 

            tk.Label(container, text="Portfolio DCA", font=("Segoe UI", 20, "bold"), bg="#ffffff", fg="#212529").pack()
            tk.Label(container, text="Carregando dados necessários...", font=("Segoe UI", 10, "italic"), bg="#ffffff", fg="#6c757d").pack(pady=(5, 20))
            
            self.lbl_status = tk.Label(container, text="Iniciando...", font=("Segoe UI", 11, "bold"), bg="#ffffff", fg="#0d6efd")
            self.lbl_status.pack(pady=(10, 5))
            
            self.progresso = ttk.Progressbar(container, mode="indeterminate", length=350)
            self.progresso.pack()
            self.progresso.start(15)

    def _carregar_dados(self):
        try:
            time.sleep(0.5)
            self._status_msg = "Lendo banco de dados local..."
            data_mgr = DataManager()
            
            time.sleep(0.5)
            self._status_msg = "Estabelecendo conexão com a Binance..."
            price_mgr = PriceManager("binance")
            
            self._status_msg = "Buscando cotações ao vivo. Aguarde..."
            price_mgr.atualizar_precos(MOEDAS_SUPORTADAS)
            
            self._status_msg = "Preparando a interface visual..."
            time.sleep(0.5)
            return data_mgr, price_mgr
        except Exception as e:
            logger.error(f"{e}")
            raise e

    def _checar_thread(self):
        self.lbl_status.config(text=self._status_msg)
        if self._future.done():
            try:
                self.data_manager, self.price_manager = self._future.result()
                self.sucesso = True
                self._fade_out()
            except Exception as e:
                messagebox.showerror("Erro", f"{e}")
                self._encerrar()
        elif time.time() - self._start_time > 20:
            messagebox.showerror("Timeout", "Tempo limite de 20s excedido.")
            self._encerrar()
        else:
            self.root.after(50, self._checar_thread)

    def _fade_out(self):
        alpha = self.root.attributes("-alpha")
        if alpha > 0:
            alpha -= 0.15
            self.root.attributes("-alpha", alpha)
            self.root.after(30, self._fade_out)
        else:
            self._encerrar()

    def _encerrar(self):
        self.root.destroy()
        self.root.quit()

class PortfolioDCA:
    def __init__(self, data_manager, price_manager):
        self.data_manager = data_manager
        self.price_manager = price_manager
        self._stop_updates = False

        self.janela = ThemedTk(theme="arc")
        self.janela.title("Portfolio DCA - Análise e Registro de Operações")
        
        self._criar_interface()
        self._preencher_dados_iniciais()
        self._iniciar_atualizacoes_automaticas()

    def _criar_interface(self) -> None:
        self.janela.minsize(1100, 700)

        base_dir = os.path.dirname(os.path.abspath(__file__))
        caminho_ico = os.path.join(base_dir, "img", "favicon.ico")
        caminho_png = os.path.join(base_dir, "img", "favicon.png")

        try:
            if platform.system() == "Windows" and os.path.exists(caminho_ico):
                self.janela.iconbitmap(caminho_ico)
            if os.path.exists(caminho_png):
                icone_img = tk.PhotoImage(file=caminho_png)
                self.janela.iconphoto(True, icone_img)
        except Exception:
            pass

        style = ttk.Style(self.janela)
        style.configure(".", font=("Segoe UI", 10)) 
        style.configure("TNotebook.Tab", padding=[15, 5], font=("Segoe UI", 10, "bold"))

        self.notebook = ttk.Notebook(self.janela)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=15)
        
        self.aba_registro = JanelaRegistro(
            parent=self.notebook, data_manager=self.data_manager, price_manager=self.price_manager,
            analysis_engine=AnalysisEngine, moedas_suportadas=MOEDAS_SUPORTADAS, on_change=self.atualizar_todas_as_analises
        )
        self.aba_analise = JanelaAnalise(
            parent=self.notebook, data_manager=self.data_manager, price_manager=self.price_manager, analysis_engine=AnalysisEngine
        )
        self.aba_distribuicao = JanelaDistribuicao(
            parent=self.notebook, data_manager=self.data_manager, price_manager=self.price_manager, analysis_engine=AnalysisEngine
        )
        self.aba_historico = JanelaHistorico(
            parent=self.notebook, data_manager=self.data_manager, price_manager=self.price_manager, analysis_engine=AnalysisEngine
        )
        self.aba_edicao = JanelaEdicao(
            parent=self.notebook, data_manager=self.data_manager, price_manager=self.price_manager, analysis_engine=AnalysisEngine,
            on_change=self.atualizar_todas_as_analises
        )

        self.notebook.add(self.aba_registro, text="✏️ Registrar Operação")
        self.notebook.add(self.aba_analise, text="📈 Análise Detalhada")
        self.notebook.add(self.aba_distribuicao, text="📊 Distribuição")
        self.notebook.add(self.aba_historico, text="🕒 Histórico de Operações")
        self.notebook.add(self.aba_edicao, text="⚙️ Editar Transação")

        status_frame = ttk.Frame(self.janela, relief="sunken", padding=(5, 2))
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self._status = ttk.Label(status_frame, text="Pronto", foreground="gray")
        self._status.pack(side=tk.LEFT)

        self._assinatura = ttk.Label(status_frame, text="Dev by Bruno Machado", foreground="gray", font=("Segoe UI", 9, "italic"))
        self._assinatura.pack(side=tk.RIGHT, padx=10)

        try:
            self.janela.state("zoomed")
        except:
            self.janela.attributes("-zoomed", True)

    def _preencher_dados_iniciais(self):
        self.aba_historico.atualizar()
        self.aba_analise.atualizar_analise()
        self.aba_distribuicao.atualizar()

    def _atualizar_abas_seguro(self):
        try:
            self.aba_distribuicao.atualizar()
            self.aba_historico.atualizar()
            self.aba_edicao.atualizar()
            self.aba_analise.atualizar_analise()
            self._atualizar_status("Pronto")
        except Exception:
            self._atualizar_status("Erro ao atualizar interface.")

    def atualizar_todas_as_analises(self) -> None:
        def worker():
            try:
                self._atualizar_status("🔄 Atualizando preços na Binance...")
                self.price_manager.atualizar_precos(MOEDAS_SUPORTADAS)
                self._atualizar_status("⚙️ Calculando portfólio...")
                self.janela.after(0, self._atualizar_abas_seguro)
            except Exception:
                self._atualizar_status("⚠️ Erro de conexão com a API")
        threading.Thread(target=worker, daemon=True).start()

    def _iniciar_atualizacoes_automaticas(self) -> None:
        def worker():
            while not self._stop_updates:
                time.sleep(60) 
                if self._stop_updates: break
                if CCXT_AVAILABLE:
                    self.atualizar_todas_as_analises()
        threading.Thread(target=worker, daemon=True).start()

    def _atualizar_status(self, mensagem: str) -> None:
        def _update():
            if hasattr(self, '_status'):
                self._status.config(text=mensagem)
                self.janela.update_idletasks()
        if threading.current_thread() is threading.main_thread():
            _update()
        else:
            self.janela.after(0, _update)

    def executar(self) -> None:
        try:
            self.janela.protocol("WM_DELETE_WINDOW", self._on_closing)
            self.janela.mainloop()
        finally:
            self._stop_updates = True

    def _on_closing(self) -> None:
        self._stop_updates = True
        self.janela.destroy()

if __name__ == "__main__":
    splash = InicializadorSplash()
    splash.root.mainloop() 
    
    if splash.sucesso:
        app = PortfolioDCA(data_manager=splash.data_manager, price_manager=splash.price_manager)
        app.executar()