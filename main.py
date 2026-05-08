# portifolio_dca.py — Portfolio CRIPTO | Entrypoint, splash screen e controller principal.
# Countdown de atualização automática gerenciado via janela.after (main thread),
# evitando race conditions com tkinter. Network/cálculo em daemon threads separados.

import threading
import time
import logging
import os
import platform
import tkinter as tk
from tkinter import ttk, messagebox
from ttkthemes import ThemedTk
from concurrent.futures import ThreadPoolExecutor
import json

if platform.system() == "Windows":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

from backend.backend import DataManager, PriceManager, AnalysisEngine, CCXT_AVAILABLE
from gui.janela_edicao import JanelaEdicao
from gui.janela_distribuicao import JanelaDistribuicao
from gui.janela_registro import JanelaRegistro
from gui.janela_caixa import JanelaCaixa
from gui.janela_moedas import JanelaMoedas
from gui.janela_estrategia import JanelaEstrategia

from config.tema_cripto import (
    aplicar_tema,
    BG_DEEP, BG_CARD, BG_INPUT,
    BTC_ORANGE, NEON_GREEN, CYAN,
    TEXT_SECONDARY,
)

from config.carregar_json import _carregar_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

CONFIG = _carregar_config()
MOEDAS_SUPORTADAS = CONFIG["moedas"]

class InicializadorSplash:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Portfolio CRIPTO")
        self.root.resizable(False, False)
        self.root.withdraw()
        self.root.configure(bg=BG_DEEP)

        self.sucesso = False
        self.data_manager = None
        self.price_manager = None
        self._start_time = time.time()
        self._status_msg = "Iniciando sistema..."

        self._carregando = False

        self._construir_interface()
        self._maximizar_e_mostrar()

        self._executor = ThreadPoolExecutor(max_workers=1)
        self._future = self._executor.submit(self._carregar_dados)
        self.root.after(100, self._checar_thread)

    def _maximizar_e_mostrar(self):
        self.root.update_idletasks()
        try:
            self.root.state("zoomed")
        except Exception:
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
        self.root.configure(bg=BG_DEEP)

        base_dir = os.path.dirname(os.path.abspath(__file__))

        caminho_bg = os.path.join(base_dir, "img", "912512.png")
        try:
            if os.path.exists(caminho_bg):
                self.bg_image = tk.PhotoImage(file=caminho_bg)
                bg_label = tk.Label(self.root, image=self.bg_image)
                bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception as e:
            logger.warning(f"Fundo splash: {e}")

        container = tk.Frame(
            self.root,
            bg=BG_CARD,
            highlightbackground=BTC_ORANGE,
            highlightthickness=2,
            padx=48,
            pady=36,
        )
        container.place(relx=0.5, rely=0.5, anchor="center")

        caminho_png = os.path.join(base_dir, "img", "favicon.png")
        try:
            if os.path.exists(caminho_png):
                self._icone = tk.PhotoImage(file=caminho_png).subsample(2, 2)
                tk.Label(container, image=self._icone, bg=BG_CARD).pack(pady=(0, 12))
        except Exception:
            pass

        tk.Label(
            container, text="Portfolio CRIPTO",
            font=("Segoe UI", 22, "bold"),
            bg=BG_CARD, fg=BTC_ORANGE,
        ).pack()

        tk.Label(
            container, text="Carregando dados necessários...",
            font=("Segoe UI", 10, "italic"),
            bg=BG_CARD, fg=TEXT_SECONDARY,
        ).pack(pady=(4, 18))

        self.lbl_status = tk.Label(
            container, text="Iniciando...",
            font=("Segoe UI", 11, "bold"),
            bg=BG_CARD, fg=CYAN,
        )
        self.lbl_status.pack(pady=(8, 6))

        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Splash.Horizontal.TProgressbar",
            troughcolor=BG_INPUT,
            background=BTC_ORANGE,
            bordercolor=BG_CARD,
            lightcolor=BTC_ORANGE,
            darkcolor="#c96d0a",
        )
        self.progresso = ttk.Progressbar(
            container, mode="indeterminate", length=360,
            style="Splash.Horizontal.TProgressbar",
        )
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
            raise

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
            messagebox.showerror("Timeout", "Tempo limite de 20s excedido. ERRO!")
            self._encerrar()
        else:
            self.root.after(50, self._checar_thread)

    def _fade_out(self):
        alpha = self.root.attributes("-alpha")
        if alpha > 0:
            self.root.attributes("-alpha", max(0.0, alpha - 0.15))
            self.root.after(30, self._fade_out)
        else:
            self._encerrar()

    def _encerrar(self):
            try:
                if self.progresso.winfo_exists():
                    self.progresso.stop()
            except Exception:
                pass
                
            self.root.destroy()
            self.root.quit()

class PortfolioDCA:
    def __init__(self, data_manager, price_manager):
        self.data_manager = data_manager
        self.price_manager = price_manager
        self._stop_updates = False

        self.janela = ThemedTk(theme="arc")
        self.janela.title("Portfolio CRIPTO — Dashboard Interativo")

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

        aplicar_tema(self.janela)

        self.notebook = ttk.Notebook(self.janela)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=15)

        self.aba_distribuicao = JanelaDistribuicao(self.notebook, self.data_manager, self.price_manager, AnalysisEngine)
        self.aba_caixa        = JanelaCaixa(self.notebook, self.data_manager, self.price_manager, AnalysisEngine)
        self.aba_registro     = JanelaRegistro(self.notebook, self.data_manager, self.price_manager, AnalysisEngine, MOEDAS_SUPORTADAS, self.atualizar_todas_as_analises)
        self.aba_edicao       = JanelaEdicao(self.notebook, self.data_manager, self.price_manager, AnalysisEngine, self.atualizar_todas_as_analises)

        self.aba_moedas = JanelaMoedas(
            self.notebook, 
            on_moedas_alteradas=self._ao_alterar_moedas, 
            price_manager=self.price_manager
        )

        self.aba_estrategia = JanelaEstrategia(self.notebook)

        self.notebook.add(self.aba_distribuicao, text="📈  Dashboard Geral")
        self.notebook.add(self.aba_caixa,        text="💰  Caixa (USDT)")
        self.notebook.add(self.aba_registro,     text="✏️  Registrar Operação")
        self.notebook.add(self.aba_edicao,       text="⚙️  Histórico e Edição")
        self.notebook.add(self.aba_moedas,       text="🪙  Gerenciar Moedas")
        self.notebook.add(self.aba_estrategia,   text="🧠  Tese Institucional")

        status_frame = tk.Frame(self.janela, bg=BG_CARD, pady=4)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        tk.Frame(self.janela, bg=BTC_ORANGE, height=1).pack(
            side=tk.BOTTOM, fill=tk.X, before=status_frame
        )

        tk.Label(
            status_frame, text="Dev by Bruno Machado",
            bg=BG_CARD, fg=TEXT_SECONDARY,
            font=("Segoe UI", 9, "italic"), padx=10,
        ).pack(side=tk.RIGHT)

        try:
            self.janela.state("zoomed")
        except Exception:
            self.janela.attributes("-zoomed", True)

    def _preencher_dados_iniciais(self):
        self.aba_caixa.atualizar()
        self.aba_distribuicao.atualizar()
        self.aba_edicao.atualizar()

    def _iniciar_atualizacoes_automaticas(self) -> None:
        self._countdown_ativo = True
        self._countdown = CONFIG["intervalo_atualizacao"]
        self._tick_countdown()

    def _tick_countdown(self):
        if not self._countdown_ativo:
            return
        if self._countdown > 0:
            self.aba_distribuicao.set_countdown(self._countdown)  
            self._countdown -= 1
            self.janela.after(1000, self._tick_countdown)
        else:
            self.aba_distribuicao.set_countdown(0)
            if CCXT_AVAILABLE:
                self.atualizar_todas_as_analises()

    def _reiniciar_countdown(self):
        self._countdown = CONFIG["intervalo_atualizacao"]
        self._tick_countdown()

    def atualizar_todas_as_analises(self) -> None:
        def worker():
            try:
                self._atualizar_status("⟳ Atualizando preços na Binance...", CYAN)
                self.price_manager.atualizar_precos(MOEDAS_SUPORTADAS)
                self._atualizar_status("⚙ Calculando portfólio...", CYAN)
                self.janela.after(0, self._atualizar_abas_seguro)
            except Exception:
                self._atualizar_status("✕ Erro de conexão com a API", "#ff4d4d")
                self.janela.after(0, self._reiniciar_countdown)

        threading.Thread(target=worker, daemon=True).start()

    def _atualizar_abas_seguro(self):
        try:
            self.aba_distribuicao.atualizar()
            self.aba_caixa.atualizar()
            self._atualizar_status("✓ Atualizado!", NEON_GREEN)
        except Exception:
            self._atualizar_status("⚠ Erro ao atualizar interface.", "#e3b341")
        finally:
            self._reiniciar_countdown()

    def _ao_alterar_moedas(self, novas_moedas: list) -> None:

            global MOEDAS_SUPORTADAS
            MOEDAS_SUPORTADAS = novas_moedas

            self.aba_registro.atualizar_lista_moedas(novas_moedas)

            self._atualizar_status("🪙 Novas moedas salvas! Buscando preços...", CYAN)
            
            self.atualizar_todas_as_analises()
            
    def _atualizar_status(self, mensagem: str, cor: str = TEXT_SECONDARY) -> None:
        def _update():
            self.aba_distribuicao.set_status(mensagem, cor)
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
        self._countdown_ativo = False
        self._stop_updates = True
        self.janela.destroy()


if __name__ == "__main__":
    splash = InicializadorSplash()
    splash.root.mainloop()

    if splash.sucesso:
        app = PortfolioDCA(
            data_manager=splash.data_manager,
            price_manager=splash.price_manager,
        )
        app.executar()