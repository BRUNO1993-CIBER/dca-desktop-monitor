import threading
import logging
import os
import platform
import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedTk

if platform.system() == "Windows":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

from backend.backend import AnalysisEngine, CCXT_AVAILABLE
from gui.janela_splash import JanelaSplash
from gui.janela_edicao import JanelaEdicao
from gui.janela_distribuicao import JanelaDistribuicao
from gui.janela_registro_logica import JanelaRegistro
from gui.janela_caixa import JanelaCaixa
from gui.janela_moedas import JanelaMoedas
from gui.janela_estrategia import JanelaEstrategia

from config.tema_cripto import (
    aplicar_tema,
    BG_CARD,
    BTC_ORANGE, NEON_GREEN, CYAN,
    TEXT_SECONDARY,
)

from config.carregar_json import _carregar_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

CONFIG = _carregar_config()
MOEDAS_SUPORTADAS = CONFIG["moedas"]


class PortfolioDCA:
    def __init__(self, janela, data_manager, price_manager):
        self.data_manager = data_manager
        self.price_manager = price_manager
        self.analysis_engine = AnalysisEngine()
        self._stop_updates = False

        self.janela = janela
        self.janela.title("Portfolio CRIPTO — Dashboard Interativo")
        self.janela.protocol("WM_DELETE_WINDOW", self._on_closing)

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

        tk.Frame(self.janela, bg=BTC_ORANGE, height=1).pack(side=tk.BOTTOM, fill=tk.X)

        status_frame = tk.Frame(self.janela, bg=BG_CARD, pady=4)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        tk.Label(
            status_frame, text="Dev by Bruno Machado",
            bg=BG_CARD, fg=TEXT_SECONDARY,
            font=("Segoe UI", 9, "italic"), padx=10,
        ).pack(side=tk.RIGHT)

        self.notebook = ttk.Notebook(self.janela)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=15)

        self.aba_distribuicao = JanelaDistribuicao(self.notebook, self.data_manager, self.price_manager, self.analysis_engine)
        self.aba_caixa        = JanelaCaixa(self.notebook, self.data_manager, self.price_manager, self.analysis_engine)
        self.aba_registro     = JanelaRegistro(self.notebook, self.data_manager, self.price_manager, self.analysis_engine, MOEDAS_SUPORTADAS, self.atualizar_todas_as_analises)
        self.aba_edicao       = JanelaEdicao(self.notebook, self.data_manager, self.price_manager, self.analysis_engine, self.atualizar_todas_as_analises)

        self.aba_moedas = JanelaMoedas(
            self.notebook,
            on_moedas_alteradas=self._ao_alterar_moedas,
            price_manager=self.price_manager,
        )

        self.aba_estrategia = JanelaEstrategia(self.notebook)

        self.notebook.add(self.aba_distribuicao, text="📈  Dashboard Geral")
        self.notebook.add(self.aba_caixa,        text="💰  Caixa (USDT)")
        self.notebook.add(self.aba_registro,     text="✏️  Registrar Operação")
        self.notebook.add(self.aba_edicao,       text="⚙️  Histórico e Edição")
        self.notebook.add(self.aba_moedas,       text="🪙  Gerenciar Moedas")
        self.notebook.add(self.aba_estrategia,   text="🧠  Tese Institucional")

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
        self._after_id = None
        self._tick_countdown()

    def _tick_countdown(self):
        if not self._countdown_ativo:
            return
        if self._countdown > 0:
            self.aba_distribuicao.set_countdown(self._countdown)
            self._countdown -= 1
            self._after_id = self.janela.after(1000, self._tick_countdown)
        else:
            self.aba_distribuicao.set_countdown(0)
            self._after_id = None
            if CCXT_AVAILABLE:
                self.atualizar_todas_as_analises()

    def _reiniciar_countdown(self):
        if self._after_id is not None:
            self.janela.after_cancel(self._after_id)
            self._after_id = None
        self._countdown = CONFIG["intervalo_atualizacao"]
        self._tick_countdown()

    def atualizar_todas_as_analises(self) -> None:
        def worker():
            try:
                self._atualizar_status("⟳ Atualizando preços na Binance...", CYAN)
                sucesso = self.price_manager.atualizar_precos(MOEDAS_SUPORTADAS)
                if not sucesso:                          
                    raise ConnectionError("Sem resposta da Binance")
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

    def _on_closing(self) -> None:
        self._countdown_ativo = False
        self._stop_updates = True
        self.janela.destroy()


if __name__ == "__main__":
    root_principal = ThemedTk(theme="arc")
    root_principal.withdraw()

    def criar_app(data_mgr, price_mgr):
        root_principal.app = PortfolioDCA(
            janela=root_principal,
            data_manager=data_mgr,
            price_manager=price_mgr,
        )

    JanelaSplash(root_principal, criar_app_callback=criar_app)
    root_principal.mainloop()