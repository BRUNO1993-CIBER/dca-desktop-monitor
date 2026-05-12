import os
import time
import random
import logging
import platform
import threading
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox

from backend.backend import DataManager, PriceManager
from config.tema_cripto import (
    BG_DEEP, BG_CARD, BG_INPUT,
    BTC_ORANGE, CYAN, TEXT_SECONDARY,
)
from config.carregar_json import _carregar_config

logger = logging.getLogger(__name__)

CONFIG = _carregar_config()
MOEDAS_SUPORTADAS = CONFIG["moedas"]
TIMEOUT_SEGUNDOS = CONFIG.get("splash_timeout", 30)

CANDLE_VERDE = "#1f7a4a"
CANDLE_VERMELHO = "#7a3030"
WICK_VERDE = "#2da668"
WICK_VERMELHO = "#a64545"
GRID_COR = "#161c2a"


class _AnimacaoCandles:
    LARGURA = 14
    ESPACO = 5
    INTERVALO = 600

    def __init__(self, canvas):
        self.canvas = canvas
        self.candles = []
        self.preco_y = 0
        self.largura = 0
        self.altura = 0
        self.max_candles = 0
        self._ativo = True
        self._after_id = None
        self.canvas.bind("<Configure>", self._on_resize)

    def _on_resize(self, evento):
        if evento.width < 50 or evento.height < 50:
            return
        primeira_vez = not self.candles
        self.largura = evento.width
        self.altura = evento.height
        self.max_candles = self.largura // (self.LARGURA + self.ESPACO) + 2
        if primeira_vez:
            self.preco_y = self.altura / 2
            self.candles = [self._novo_candle() for _ in range(self.max_candles)]
        else:
            while len(self.candles) < self.max_candles:
                self.candles.append(self._novo_candle())
            while len(self.candles) > self.max_candles:
                self.candles.pop(0)
        self._desenhar_grid()
        self._desenhar()
        if primeira_vez and self._after_id is None:
            self._tick()

    def _novo_candle(self):
        direcao = random.choice([-1, -1, 1, 1, 1, -1])
        corpo = random.uniform(8, 32) * direcao
        margem = 70
        novo_y = max(margem, min(self.altura - margem, self.preco_y + corpo))
        open_y = self.preco_y
        close_y = novo_y
        pavio_sup = min(open_y, close_y) - random.uniform(4, 22)
        pavio_inf = max(open_y, close_y) + random.uniform(4, 22)
        self.preco_y = novo_y
        return (open_y, close_y, pavio_sup, pavio_inf)

    def _desenhar_grid(self):
        self.canvas.delete("grid")
        for y in range(0, int(self.altura), 70):
            self.canvas.create_line(0, y, self.largura, y, fill=GRID_COR, tags="grid")
        for x in range(0, int(self.largura), 90):
            self.canvas.create_line(x, 0, x, self.altura, fill=GRID_COR, tags="grid")

    def _desenhar(self):
        self.canvas.delete("candle")
        self.canvas.delete("preco_linha")
        x = self.largura - len(self.candles) * (self.LARGURA + self.ESPACO)
        for open_y, close_y, pavio_sup, pavio_inf in self.candles:
            subiu = close_y < open_y
            cor_corpo = CANDLE_VERDE if subiu else CANDLE_VERMELHO
            cor_pavio = WICK_VERDE if subiu else WICK_VERMELHO
            cx = x + self.LARGURA // 2
            self.canvas.create_line(cx, pavio_sup, cx, pavio_inf,
                                    fill=cor_pavio, width=1, tags="candle")
            top = min(open_y, close_y)
            bot = max(open_y, close_y)
            if bot - top < 2:
                bot = top + 2
            self.canvas.create_rectangle(x, top, x + self.LARGURA, bot,
                                         fill=cor_corpo, outline=cor_corpo,
                                         tags="candle")
            x += self.LARGURA + self.ESPACO

        if self.candles:
            ultimo_y = self.candles[-1][1]
            self.canvas.create_line(0, ultimo_y, self.largura, ultimo_y,
                                    fill=BTC_ORANGE, width=1, dash=(4, 4),
                                    tags="preco_linha")

    def _tick(self):
        if not self._ativo:
            return
        if self.candles:
            self.candles.pop(0)
            self.candles.append(self._novo_candle())
            self._desenhar()
        self._after_id = self.canvas.after(self.INTERVALO, self._tick)

    def parar(self):
        self._ativo = False
        if self._after_id is not None:
            try:
                self.canvas.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None


class JanelaSplash:
    def __init__(self, root_pai, criar_app_callback):
        self.root_pai = root_pai
        self.criar_app_callback = criar_app_callback

        self.sucesso = False
        self.data_manager = None
        self.price_manager = None
        self._erro = None
        self._start_time = time.time()
        self._status_msg = "Iniciando sistema..."
        self._animacao = None
        self._app_construida = False

        ctk.set_appearance_mode("dark")

        self.splash = ctk.CTkToplevel(root_pai)
        self.splash.title("Portfolio CRIPTO")
        self.splash.configure(fg_color=BG_DEEP)
        self.splash.attributes("-alpha", 1.0)

        self._maximizar()
        self._aplicar_icone()
        self._construir_interface()

        threading.Thread(target=self._carregar_dados, daemon=True).start()
        self.splash.after(100, self._checar_progresso)

    def _maximizar(self):
        self.splash.update_idletasks()
        try:
            self.splash.state("zoomed")
        except Exception:
            try:
                self.splash.attributes("-zoomed", True)
            except Exception:
                w = self.splash.winfo_screenwidth()
                h = self.splash.winfo_screenheight()
                self.splash.geometry(f"{w}x{h}+0+0")

    def _aplicar_icone(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        caminho_ico = os.path.join(base_dir, "img", "favicon.ico")
        caminho_png = os.path.join(base_dir, "img", "favicon.png")
        try:
            if platform.system() == "Windows" and os.path.exists(caminho_ico):
                self.splash.iconbitmap(caminho_ico)
            if os.path.exists(caminho_png):
                img = tk.PhotoImage(file=caminho_png)
                self.splash.iconphoto(True, img)
        except Exception as e:
            logger.warning(f"Falha ao aplicar icone: {e}")

    def _construir_interface(self):
        self.canvas = tk.Canvas(self.splash, bg=BG_DEEP,
                                highlightthickness=0, bd=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self._animacao = _AnimacaoCandles(self.canvas)

        self.card = ctk.CTkFrame(
            self.splash,
            fg_color=BG_CARD,
            border_color=BTC_ORANGE,
            border_width=2,
            corner_radius=18,
        )
        self.card.place(relx=0.5, rely=0.5, anchor="center")

        inner = ctk.CTkFrame(self.card, fg_color="transparent")
        inner.pack(padx=56, pady=44)

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        caminho_png = os.path.join(base_dir, "img", "favicon.png")
        try:
            if os.path.exists(caminho_png):
                self._icone_img = tk.PhotoImage(file=caminho_png).subsample(2, 2)
                tk.Label(inner, image=self._icone_img, bg=BG_CARD,
                         bd=0, highlightthickness=0).pack(pady=(0, 14))
        except Exception:
            pass

        ctk.CTkLabel(
            inner, text="Portfolio CRIPTO",
            font=("Segoe UI", 26, "bold"),
            text_color=BTC_ORANGE,
            fg_color="transparent",
        ).pack()

        ctk.CTkLabel(
            inner, text="Carregando dados de mercado",
            font=("Segoe UI", 11, "italic"),
            text_color=TEXT_SECONDARY,
            fg_color="transparent",
        ).pack(pady=(2, 22))

        self.lbl_status = ctk.CTkLabel(
            inner, text=self._status_msg,
            font=("Segoe UI", 12, "bold"),
            text_color=CYAN,
            fg_color="transparent",
        )
        self.lbl_status.pack(pady=(6, 12))

        self.progresso = ctk.CTkProgressBar(
            inner, mode="indeterminate",
            width=380, height=8,
            progress_color=BTC_ORANGE,
            fg_color=BG_INPUT,
            corner_radius=4,
        )
        self.progresso.pack(pady=(4, 0))
        self.progresso.start()

    def _carregar_dados(self):
        try:
            self._status_msg = "Lendo banco de dados local..."
            data_mgr = DataManager()

            self._status_msg = "Estabelecendo conexão com a Binance..."
            price_mgr = PriceManager("binance")

            self._status_msg = "Buscando cotações ao vivo..."
            price_mgr.atualizar_precos(MOEDAS_SUPORTADAS)

            self._status_msg = "Preparando interface..."
            self.data_manager = data_mgr
            self.price_manager = price_mgr
            self.sucesso = True
        except Exception as e:
            logger.exception("Falha durante carga inicial")
            self._erro = str(e)

    def _checar_progresso(self):
        try:
            self.lbl_status.configure(text=self._status_msg)
        except Exception:
            pass

        if self.sucesso and not self._app_construida:
            try:
                self.criar_app_callback(self.data_manager, self.price_manager)
                self._app_construida = True
            except Exception as e:
                logger.exception("Falha ao construir aplicacao")
                messagebox.showerror("Erro", f"Falha ao construir app: {e}")
                self._encerrar(sucesso=False)
                return
            self._fade_out()
            return

        if self._erro is not None:
            messagebox.showerror("Erro", self._erro)
            self._encerrar(sucesso=False)
            return

        if time.time() - self._start_time > TIMEOUT_SEGUNDOS:
            messagebox.showerror("Timeout",
                                 f"Tempo limite de {TIMEOUT_SEGUNDOS}s excedido.")
            self._encerrar(sucesso=False)
            return

        self.splash.after(80, self._checar_progresso)

    def _fade_out(self):
        try:
            alpha = float(self.splash.attributes("-alpha"))
        except Exception:
            alpha = 1.0
        if alpha > 0.05:
            self.splash.attributes("-alpha", max(0.0, alpha - 0.12))
            self.splash.after(25, self._fade_out)
        else:
            self._encerrar(sucesso=True)

    def _encerrar(self, sucesso):
        try:
            if self._animacao is not None:
                self._animacao.parar()
        except Exception:
            pass
        try:
            self.progresso.stop()
        except Exception:
            pass
        try:
            self.splash.destroy()
        except Exception:
            pass
        if sucesso:
            self.root_pai.deiconify()
        else:
            self.root_pai.destroy()