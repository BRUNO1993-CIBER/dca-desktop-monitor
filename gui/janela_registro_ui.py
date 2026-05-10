import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, List, Optional
from decimal import Decimal

from backend.tipo_operacao import TipoOperacao


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
        self._moedas = moedas_suportadas
        self._on_moeda_changed = on_moeda_changed
        self._on_tipo_changed = on_tipo_changed
        self._on_calcular = on_calcular
        self._on_salvar = on_salvar

        self._configurar_estilos()
        self._build_ui()

    def _configurar_estilos(self) -> None:
        style = ttk.Style()
        style.configure("Titulo.TLabel",   font=("Segoe UI", 16, "bold"))
        style.configure("Padrao.TLabel",   font=("Segoe UI", 11))
        style.configure("Info.TLabel",     font=("Segoe UI", 10),          foreground="#666666")
        style.configure("Destaque.TLabel", font=("Segoe UI", 10, "bold"),  foreground="#0052cc")
        style.configure("Saldo.TLabel",    font=("Segoe UI", 10, "bold"),  foreground="#2e7d32")
        style.configure("Travado.TLabel",  font=("Segoe UI", 10, "bold"),  foreground="#cc0000")
        style.configure("Dica.TLabel",     font=("Segoe UI", 9, "italic"), foreground="#0052cc")
        style.configure("Erro.TLabel",     font=("Segoe UI", 9, "bold"),   foreground="#cc0000")
        style.configure("Accent.TButton",  font=("Segoe UI", 12, "bold"))

    def _build_ui(self) -> None:
        main = ttk.Frame(self, padding="30 20 30 20")
        main.pack(fill="both", expand=True)

        header = ttk.Frame(main)
        header.pack(fill="x", pady=(0, 20))
        ttk.Label(header, text="Registrar Nova Operação", style="Titulo.TLabel").pack(side="left")

        form_frame = ttk.LabelFrame(main, text="Detalhes da Transação", padding="20 20 20 20")
        form_frame.pack(fill="both", expand=True, pady=10)
        self._build_form(form_frame)

        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill="x", pady=(30, 10))
        self._btn_salvar = ttk.Button(
            btn_frame,
            text="💾 Salvar Operação",
            command=self._on_salvar,
            style="Accent.TButton",
            cursor="hand2",
            state="disabled",
        )
        self._btn_salvar.pack(ipady=5, ipadx=20)

    def _build_form(self, parent: ttk.Frame) -> None:
        container = ttk.Frame(parent)
        container.pack(anchor="n", pady=20)

        ttk.Label(container, text="Moeda:", style="Padrao.TLabel").grid(
            row=0, column=0, sticky="e", pady=10, padx=(0, 15))
        self._combo_moeda = ttk.Combobox(
            container, values=self._moedas, font=("Segoe UI", 11), state="readonly", width=22)
        self._combo_moeda.grid(row=0, column=1, sticky="w", pady=10)
        self._combo_moeda.bind("<<ComboboxSelected>>", self._on_moeda_changed)

        self._label_preco_atual = ttk.Label(container, text="", style="Destaque.TLabel")
        self._label_preco_atual.grid(row=0, column=2, sticky="w", padx=(15, 0))

        ttk.Label(container, text="Operação:", style="Padrao.TLabel").grid(
            row=1, column=0, sticky="e", pady=10, padx=(0, 15))
        self._combo_tipo = ttk.Combobox(
            container, font=("Segoe UI", 11), state="disabled", width=22)
        self._combo_tipo.grid(row=1, column=1, sticky="w", pady=10)
        self._combo_tipo.bind("<<ComboboxSelected>>", self._on_tipo_changed)

        self._label_saldo = ttk.Label(container, text="", style="Saldo.TLabel")
        self._label_saldo.grid(row=1, column=2, sticky="w", padx=(15, 0))

        self._label_preco_titulo = ttk.Label(container, text="Preço Unitário:", style="Padrao.TLabel")
        self._label_preco_titulo.grid(row=2, column=0, sticky="e", pady=10, padx=(0, 15))
        self._entry_preco = ttk.Entry(container, font=("Segoe UI", 11), width=24, state="disabled")
        self._entry_preco.grid(row=2, column=1, sticky="w", pady=10)
        self._entry_preco.bind("<KeyRelease>", self._on_calcular)

        ttk.Label(container, text="Valor (USDT):", style="Padrao.TLabel").grid(
            row=3, column=0, sticky="e", pady=10, padx=(0, 15))
        self._entry_valor = ttk.Entry(container, font=("Segoe UI", 11), width=24, state="disabled")
        self._entry_valor.grid(row=3, column=1, sticky="w", pady=10)
        self._entry_valor.bind("<KeyRelease>", self._on_calcular)

        self._label_quantidade = ttk.Label(container, text="", style="Info.TLabel")
        self._label_quantidade.grid(row=3, column=2, sticky="w", padx=(15, 0))

        self._label_ajuda = ttk.Label(container, text="", style="Dica.TLabel", justify="left")
        self._label_ajuda.grid(row=4, column=1, columnspan=2, sticky="w", pady=(0, 4))

        self._label_erro_saldo = ttk.Label(container, text="", style="Erro.TLabel", justify="left")
        self._label_erro_saldo.grid(row=5, column=1, columnspan=2, sticky="w", pady=(0, 5))

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

    def set_entry_preco(self, value: str, state_before: str = "normal", state_after: Optional[str] = None) -> None:
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
        self._label_saldo.config(text=text, style=style)

    def set_label_quantidade(self, text: str, style: str = "Info.TLabel") -> None:
        self._label_quantidade.config(text=text, style=style)

    def set_label_ajuda(self, text: str) -> None:
        self._label_ajuda.config(text=text)

    def set_label_erro_saldo(self, text: str) -> None:
        self._label_erro_saldo.config(text=text)

    def set_btn_salvar_state(self, state: str) -> None:
        self._btn_salvar.config(state=state)

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
        self._label_quantidade.config(text="", style="Info.TLabel")
        self._label_preco_atual.config(text="")
        self._label_saldo.config(text="")
        self._label_ajuda.config(text="")
        self._label_erro_saldo.config(text="")
        self._label_preco_titulo.config(text="Preço Unitário:")
        self._btn_salvar.config(state="disabled")

    def atualizar_lista_moedas(self, novas_moedas: list) -> None:
        moeda_atual = self._combo_moeda.get()
        self.set_combo_moedas(novas_moedas)
        return moeda_atual