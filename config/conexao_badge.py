import platform
# pyrefly: ignore [missing-import]
import customtkinter as ctk

from config.tema_cripto import (
    BG_CARD, NEON_GREEN, NEON_RED, CYAN, YELLOW,
    TEXT_PRIMARY, TEXT_MUTED, BORDER,
)

_FONT_NAME      = "Segoe UI" if platform.system() == "Windows" else "Ubuntu"
_F_BADGE        = (_FONT_NAME, 11, "bold")
_SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

_ESTADOS = {
    "conectado":     ("Conectado 🛜",  NEON_GREEN, False),
    "sincronizando": ("Sincronizando", YELLOW,     True),
    "offline":       ("Offline ⚠",    NEON_RED,   False),
    "aguardando":    ("Aguardando...", TEXT_MUTED, False),
}

_COR_PARA_ESTADO = {
    NEON_GREEN: "conectado",
    CYAN:       "sincronizando",
    NEON_RED:   "offline",
    "#ff4d4d":  "offline",
    "#e3b341":  "offline",
}


class ConexaoBadge(ctk.CTkFrame):

    def __init__(self, parent, **kwargs):
        kwargs.setdefault("fg_color",      BG_CARD)
        kwargs.setdefault("border_color",  BORDER)
        kwargs.setdefault("border_width",  1)
        kwargs.setdefault("corner_radius", 8)
        super().__init__(parent, **kwargs)

        self._estado      = "aguardando"
        self._spinner_job = None
        self._spinner_idx = 0

        self._inner = ctk.CTkFrame(self, fg_color="transparent")
        self._inner.pack(expand=True, padx=(14, 14), pady=5)

        self._lbl_texto = ctk.CTkLabel(
            self._inner, text="Aguardando...", font=_F_BADGE,
            text_color=TEXT_MUTED, fg_color="transparent",
            width=80, anchor="center",
        )
        self._lbl_texto.pack(side="left")

        self._lbl_spinner = ctk.CTkLabel(
            self._inner, text="", font=_F_BADGE,
            text_color=YELLOW, fg_color="transparent", width=16,
        )
        self._lbl_spinner.pack(side="left", padx=(4, 0))

    def set_estado(self, estado: str):
        if estado not in _ESTADOS:
            return
        self._estado = estado
        texto, cor, animar = _ESTADOS[estado]
        self._lbl_texto.configure(text=texto, text_color=cor)
        if animar:
            self._start_spinner()
        else:
            self._stop_spinner()

    def set_status(self, mensagem: str, cor: str = TEXT_MUTED):
        if not mensagem:
            return
        estado_novo = _COR_PARA_ESTADO.get(cor)
        if estado_novo:
            self.set_estado(estado_novo)
        else:
            self._lbl_texto.configure(text=mensagem, text_color=cor)

    def set_countdown(self, segundos: int):
        pass

    @property
    def estado(self) -> str:
        return self._estado

    def _start_spinner(self):
        if self._spinner_job is not None:
            return
        self._spinner_idx = 0
        self._tick()

    def _stop_spinner(self):
        if self._spinner_job is not None:
            self.after_cancel(self._spinner_job)
            self._spinner_job = None
        self._lbl_spinner.configure(text="")

    def _tick(self):
        if self._estado != "sincronizando":
            self._stop_spinner()
            return
        frame = _SPINNER_FRAMES[self._spinner_idx % len(_SPINNER_FRAMES)]
        self._lbl_spinner.configure(text=frame, text_color=YELLOW)
        self._spinner_idx += 1
        self._spinner_job = self.after(100, self._tick)