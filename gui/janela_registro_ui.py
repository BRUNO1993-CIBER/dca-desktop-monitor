import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, List, Optional

from config.tema_cripto import (
    BG_DEEP, BG_SURFACE, BG_CARD, BG_INPUT,
    BORDER, BORDER_ACC,
    BTC_ORANGE, NEON_GREEN, NEON_RED, CYAN, YELLOW,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
)

FONT_MONO_TITLE = ("Consolas", 14, "bold")
FONT_MONO_LABEL = ("Consolas", 10, "bold")
FONT_MONO_INPUT = ("Consolas", 11)
FONT_MONO_SMALL = ("Consolas", 9)
FONT_MONO_BTN   = ("Consolas", 12, "bold")
FONT_MONO_BADGE = ("Consolas", 9, "bold")

WRAP_W = 210
WRAP_H = 34


class JanelaRegistroUI(ttk.Frame):

    def __init__(
        self,
        parent: Any,
        moedas_suportadas: List[str],
        on_moeda_changed: Callable,
        on_tipo_changed: Callable,
        on_calcular: Callable,
        on_salvar: Callable,
    ):
        super().__init__(parent)
        self._moedas           = moedas_suportadas
        self._on_moeda_changed = on_moeda_changed
        self._on_tipo_changed  = on_tipo_changed
        self._on_calcular      = on_calcular
        self._on_salvar        = on_salvar

        self.configure(style="Reg.TFrame")
        self._configurar_estilos()
        self._build_ui()

    def _configurar_estilos(self) -> None:
        s = ttk.Style()

        s.configure("Reg.TFrame",     background=BG_SURFACE)
        s.configure("RegCard.TFrame", background=BG_CARD)

        s.configure("Titulo.TLabel",
                    font=FONT_MONO_TITLE, background=BG_SURFACE, foreground=BTC_ORANGE)
        s.configure("Sub.TLabel",
                    font=FONT_MONO_SMALL, background=BG_SURFACE, foreground=TEXT_MUTED)
        s.configure("Padrao.TLabel",
                    font=FONT_MONO_LABEL, background=BG_CARD, foreground=TEXT_SECONDARY)
        s.configure("Info.TLabel",
                    font=FONT_MONO_SMALL, background=BG_CARD, foreground=TEXT_SECONDARY)
        s.configure("Destaque.TLabel",
                    font=FONT_MONO_BADGE, background=BG_CARD, foreground=CYAN)
        s.configure("Saldo.TLabel",
                    font=FONT_MONO_BADGE, background=BG_CARD, foreground=NEON_GREEN)
        s.configure("Travado.TLabel",
                    font=FONT_MONO_BADGE, background=BG_CARD, foreground=YELLOW)
        s.configure("Dica.TLabel",
                    font=FONT_MONO_SMALL, background=BG_CARD, foreground=CYAN)
        s.configure("Erro.TLabel",
                    font=FONT_MONO_SMALL, background=BG_CARD, foreground=NEON_RED)

        s.configure("Reg.TCombobox",
                    fieldbackground=BG_INPUT, background=BG_INPUT,
                    foreground=TEXT_PRIMARY, selectbackground=BG_INPUT,
                    selectforeground=BTC_ORANGE, bordercolor=BORDER,
                    arrowcolor=BTC_ORANGE, padding=8)
        s.map("Reg.TCombobox",
              fieldbackground=[("readonly", BG_INPUT), ("disabled", BG_DEEP)],
              foreground=[("disabled", TEXT_MUTED)],
              bordercolor=[("focus", BORDER_ACC)])

        s.configure("Reg.TEntry",
                    fieldbackground=BG_INPUT, foreground=TEXT_PRIMARY,
                    insertcolor=BTC_ORANGE, bordercolor=BORDER, padding=8)
        s.map("Reg.TEntry",
              bordercolor=[("focus", BORDER_ACC)],
              fieldbackground=[("disabled", BG_DEEP)],
              foreground=[("disabled", TEXT_MUTED)])

        s.configure("Reg.TButton",
                    font=FONT_MONO_BTN, foreground=BG_DEEP,
                    background=BTC_ORANGE, borderwidth=0,
                    focuscolor=BTC_ORANGE, padding=(0, 12))
        s.map("Reg.TButton",
              background=[("active", "#e8820f"), ("disabled", BORDER)],
              foreground=[("disabled", TEXT_MUTED)])

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        outer = tk.Frame(self, bg=BG_SURFACE)
        outer.grid(row=0, column=0, sticky="nsew")
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(1, weight=1)

        self._build_header(outer)
        self._build_card(outer)
        self._build_footer(outer)

    def _build_header(self, parent: tk.Frame) -> None:
        hdr = tk.Frame(parent, bg=BG_SURFACE)
        hdr.grid(row=0, column=0, sticky="ew", padx=40, pady=(30, 0))
        hdr.columnconfigure(1, weight=1)

        tk.Frame(hdr, bg=BTC_ORANGE, width=4).grid(
            row=0, column=0, rowspan=2, sticky="ns", padx=(0, 14))

        tk.Label(hdr, text="REGISTRAR OPERACAO",
                 font=FONT_MONO_TITLE, bg=BG_SURFACE, fg=BTC_ORANGE).grid(
            row=0, column=1, sticky="w")

        tk.Label(hdr, text="nova entrada no livro de ordens",
                 font=FONT_MONO_SMALL, bg=BG_SURFACE, fg=TEXT_MUTED).grid(
            row=1, column=1, sticky="w", pady=(2, 0))

        tk.Frame(parent, bg=BORDER, height=1).grid(
            row=0, column=0, sticky="ew", padx=40, pady=(78, 0))

    def _build_card(self, parent: tk.Frame) -> None:
        card = tk.Frame(parent, bg=BG_CARD,
                        highlightbackground=BORDER, highlightthickness=1)
        card.grid(row=1, column=0, sticky="n", padx=40, pady=24)
        card.columnconfigure(0, weight=1)

        tk.Frame(card, bg=BTC_ORANGE, height=3).grid(row=0, column=0, sticky="ew")

        inner = tk.Frame(card, bg=BG_CARD)
        inner.grid(row=1, column=0, padx=36, pady=28)

        self._build_form(inner)

    def _build_form(self, parent: tk.Frame) -> None:
        parent.columnconfigure(0, minsize=140)
        parent.columnconfigure(1, minsize=WRAP_W + 2)
        parent.columnconfigure(2, minsize=180)

        def section_bar(row, text):
            tk.Label(parent, text=text, font=FONT_MONO_BADGE,
                     bg=BG_INPUT, fg=BTC_ORANGE, padx=10, pady=4, anchor="w").grid(
                row=row, column=0, columnspan=3, sticky="ew", pady=(16, 10))

        def field_label(row, text):
            tk.Label(parent, text=text, font=FONT_MONO_LABEL,
                     bg=BG_CARD, fg=TEXT_SECONDARY, anchor="e", width=16).grid(
                row=row, column=0, sticky="e", pady=8, padx=(0, 14))

        def wrap(row, col):
            f = tk.Frame(parent, bg=BORDER, width=WRAP_W + 2, height=WRAP_H + 2)
            f.grid(row=row, column=col, sticky="w", pady=8)
            f.grid_propagate(False)
            f.pack_propagate(False)
            return f

        section_bar(0, "  ATIVO")

        field_label(1, "MOEDA")
        self._combo_moeda = ttk.Combobox(wrap(1, 1), values=self._moedas,
                                         font=FONT_MONO_INPUT, state="readonly",
                                         style="Reg.TCombobox")
        self._combo_moeda.pack(fill="both", expand=True)
        self._combo_moeda.bind("<<ComboboxSelected>>", self._on_moeda_changed)

        self._label_preco_atual = tk.Label(parent, text="", font=FONT_MONO_BADGE,
                                           bg=BG_CARD, fg=CYAN, anchor="w")
        self._label_preco_atual.grid(row=1, column=2, sticky="w", padx=(16, 0))

        section_bar(2, "  OPERACAO")

        field_label(3, "TIPO")
        self._combo_tipo = ttk.Combobox(wrap(3, 1), font=FONT_MONO_INPUT,
                                        state="disabled", style="Reg.TCombobox")
        self._combo_tipo.pack(fill="both", expand=True)
        self._combo_tipo.bind("<<ComboboxSelected>>", self._on_tipo_changed)

        self._label_saldo = tk.Label(parent, text="", font=FONT_MONO_BADGE,
                                     bg=BG_CARD, fg=NEON_GREEN, anchor="w")
        self._label_saldo.grid(row=3, column=2, sticky="w", padx=(16, 0))

        section_bar(4, "  VALORES")

        self._label_preco_titulo = tk.Label(parent, text="PRECO UNIT.",
                                            font=FONT_MONO_LABEL, bg=BG_CARD,
                                            fg=TEXT_SECONDARY, anchor="e", width=16)
        self._label_preco_titulo.grid(row=5, column=0, sticky="e", pady=8, padx=(0, 14))

        self._entry_preco = ttk.Entry(wrap(5, 1), font=FONT_MONO_INPUT,
                                      state="disabled", style="Reg.TEntry")
        self._entry_preco.pack(fill="both", expand=True)
        self._entry_preco.bind("<KeyRelease>", self._on_calcular)

        field_label(6, "VALOR (USDT)")
        self._entry_valor = ttk.Entry(wrap(6, 1), font=FONT_MONO_INPUT,
                                      state="disabled", style="Reg.TEntry")
        self._entry_valor.pack(fill="both", expand=True)
        self._entry_valor.bind("<KeyRelease>", self._on_calcular)

        self._label_quantidade = tk.Label(parent, text="", font=FONT_MONO_BADGE,
                                          bg=BG_CARD, fg=TEXT_SECONDARY, anchor="w")
        self._label_quantidade.grid(row=6, column=2, sticky="w", padx=(16, 0))

        self._label_ajuda = tk.Label(parent, text="", font=FONT_MONO_SMALL,
                                     bg=BG_CARD, fg=CYAN, justify="left", anchor="w")
        self._label_ajuda.grid(row=7, column=1, columnspan=2, sticky="w", pady=(4, 0))

        self._label_erro_saldo = tk.Label(parent, text="", font=FONT_MONO_SMALL,
                                          bg=BG_CARD, fg=NEON_RED, justify="left", anchor="w")
        self._label_erro_saldo.grid(row=8, column=1, columnspan=2, sticky="w", pady=(2, 4))

    def _build_footer(self, parent: tk.Frame) -> None:
        tk.Frame(parent, bg=BORDER, height=1).grid(
            row=2, column=0, sticky="ew", padx=40, pady=(0, 20))

        btn_wrap = tk.Frame(parent, bg=BG_SURFACE)
        btn_wrap.grid(row=3, column=0, pady=(0, 30))

        self._btn_salvar = ttk.Button(btn_wrap, text="CONFIRMAR OPERACAO",
                                      command=self._on_salvar, style="Reg.TButton",
                                      cursor="hand2", state="disabled")
        self._btn_salvar.pack(ipady=6, ipadx=40)

        self._label_status_btn = tk.Label(btn_wrap, text="preencha todos os campos",
                                          font=FONT_MONO_SMALL, bg=BG_SURFACE, fg=TEXT_MUTED)
        self._label_status_btn.pack(pady=(8, 0))

    def get_moeda(self) -> str:
        return self._combo_moeda.get()

    def get_tipo_label(self) -> str:
        return self._combo_tipo.get()

    def get_valor_str(self) -> str:
        return self._entry_valor.get()

    def get_preco_str(self) -> str:
        return self._entry_preco.get()

    def set_combo_tipo_values(self, values: list, state: str = "readonly") -> None:
        self._combo_tipo.config(values=values, state=state)

    def set_combo_tipo_state(self, state: str) -> None:
        self._combo_tipo.config(state=state)

    def set_combo_tipo_value(self, value: str) -> None:
        self._combo_tipo.set(value)

    def set_combo_moedas(self, moedas: list) -> None:
        self._moedas = moedas
        self._combo_moeda.config(values=moedas)

    def set_combo_moeda_value(self, value: str) -> None:
        self._combo_moeda.set(value)

    def set_entry_preco(self, value: str, state_before: str = "normal",
                        state_after: Optional[str] = None) -> None:
        self._entry_preco.config(state="normal")
        self._entry_preco.delete(0, tk.END)
        if value:
            self._entry_preco.insert(0, value)
        if state_after:
            self._entry_preco.config(state=state_after)

    def set_entry_valor(self, value: str) -> None:
        self._entry_valor.config(state="normal")
        self._entry_valor.delete(0, tk.END)
        if value:
            self._entry_valor.insert(0, value)

    def set_entry_preco_state(self, state: str) -> None:
        self._entry_preco.config(state=state)

    def set_entry_valor_state(self, state: str) -> None:
        self._entry_valor.config(state=state)

    def set_label_preco_atual(self, text: str) -> None:
        self._label_preco_atual.config(text=text)

    def set_label_preco_titulo(self, text: str) -> None:
        self._label_preco_titulo.config(text=text)

    def set_label_saldo(self, text: str, style: str = "Saldo.TLabel") -> None:
        cor = NEON_GREEN if "Saldo" in style else TEXT_SECONDARY
        self._label_saldo.config(text=text, fg=cor)

    def set_label_quantidade(self, text: str, style: str = "Info.TLabel") -> None:
        cor_map = {
            "Info.TLabel":     TEXT_SECONDARY,
            "Travado.TLabel":  YELLOW,
            "Erro.TLabel":     NEON_RED,
            "Saldo.TLabel":    NEON_GREEN,
            "Destaque.TLabel": CYAN,
        }
        self._label_quantidade.config(text=text, fg=cor_map.get(style, TEXT_SECONDARY))

    def set_label_ajuda(self, text: str) -> None:
        self._label_ajuda.config(text=text)

    def set_label_erro_saldo(self, text: str) -> None:
        self._label_erro_saldo.config(text=text)

    def set_btn_salvar_state(self, state: str) -> None:
        self._btn_salvar.config(state=state)
        if state == "normal":
            self._label_status_btn.config(text="pronto para registrar  OK", fg=NEON_GREEN)
        else:
            self._label_status_btn.config(text="preencha todos os campos", fg=TEXT_MUTED)

    def limpar_campos(self) -> None:
        self._combo_moeda.set("")
        self._combo_tipo.set("")
        self._combo_tipo.config(state="disabled")
        self._entry_preco.config(state="normal")
        self._entry_preco.delete(0, tk.END)
        self._entry_preco.config(state="disabled")
        self._entry_valor.config(state="normal")
        self._entry_valor.delete(0, tk.END)
        self._entry_valor.config(state="disabled")
        self._label_quantidade.config(text="", fg=TEXT_SECONDARY)
        self._label_preco_atual.config(text="")
        self._label_saldo.config(text="", fg=NEON_GREEN)
        self._label_ajuda.config(text="")
        self._label_erro_saldo.config(text="")
        self._label_preco_titulo.config(text="PRECO UNIT.")
        self._btn_salvar.config(state="disabled")
        self._label_status_btn.config(text="preencha todos os campos", fg=TEXT_MUTED)

    def atualizar_lista_moedas(self, novas_moedas: list) -> None:
        moeda_atual = self._combo_moeda.get()
        self.set_combo_moedas(novas_moedas)
        return moeda_atual