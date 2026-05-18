import platform
import tkinter as tk
from tkinter import messagebox
# pyrefly: ignore [missing-import]
import customtkinter as ctk

_FONT = "Courier New" if platform.system() == "Windows" else "Monospace"

BG_CARD      = "#161b22"
BTC_ORANGE   = "#f7931a"
NEON_GREEN   = "#00ff88"
BORDER       = "#30363d"
TEXT_PRIMARY = "#e6edf3"


class BRLToggle(ctk.CTkFrame):
    """
    Botão "Exibir em BRL" reutilizável.

    Uso:
        toggle = BRLToggle(parent, price_manager=pm, on_change=minha_funcao)
        toggle.pack(...)

        # minha_funcao recebe "BRL" ou "USD"
        def minha_funcao(currency):
            self.display_currency = currency
            self.atualizar()

    Atributos públicos:
        .display_currency  ->  "USD" ou "BRL"
        .var               ->  BooleanVar (estado do checkbox)
    """

    def __init__(self, parent, price_manager, on_change=None, **kwargs):
        kwargs.setdefault("fg_color", "transparent")
        kwargs.setdefault("corner_radius", 0)
        super().__init__(parent, **kwargs)

        self._price_manager   = price_manager
        self._on_change       = on_change
        self.display_currency = "USD"
        self.var              = tk.BooleanVar(value=False)

        self._build()

    def _build(self):
        frame = ctk.CTkFrame(
            self,
            fg_color=BG_CARD,
            corner_radius=8,
            border_width=1,
            border_color=BORDER,
        )
        frame.pack(anchor="e")

        ctk.CTkLabel(
            frame,
            text="Exibir em BRL",
            font=ctk.CTkFont(_FONT, 11, "bold"),
            text_color=TEXT_PRIMARY,
            cursor="hand2",
        ).pack(side=tk.LEFT, padx=(8, 4), pady=5)

        ctk.CTkCheckBox(
            frame,
            text="",
            variable=self.var,
            command=self._on_toggle,
            checkbox_width=18,
            checkbox_height=18,
            fg_color=BTC_ORANGE,
            hover_color=NEON_GREEN,
            border_color=BORDER,
            corner_radius=4,
            width=0,
            cursor="hand2",
        ).pack(side=tk.LEFT, padx=(0, 8), pady=5)

    def _on_toggle(self):
        if self.var.get():
            taxa = self._price_manager.preco_brl
            if taxa is None or taxa <= 0:
                messagebox.showwarning("Aviso", "Cotação do BRL indisponível. Exibindo USD.")
                self.var.set(False)
                self.display_currency = "USD"
            else:
                self.display_currency = "BRL"
        else:
            self.display_currency = "USD"

        if self._on_change:
            self._on_change(self.display_currency)