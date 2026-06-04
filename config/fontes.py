import platform
# pyrefly: ignore [missing-import]
import customtkinter as ctk

# ── famílias ──────────────────────────────────────────────────────────────────
MONO = "Courier New" if platform.system() == "Windows" else "Monospace"
UI   = "Segoe UI"    if platform.system() == "Windows" else "Ubuntu"


# ── escala DPI (Windows) ──────────────────────────────────────────────────────
def _dpi_scale() -> float:
    if platform.system() != "Windows":
        return 1.0
    try:
        import ctypes
        dpi = ctypes.windll.user32.GetDpiForSystem()
        return dpi / 96.0
    except Exception:
        return 1.0


_SCALE = _dpi_scale()


def _s(n: int) -> int:
    """Retorna o tamanho de fonte escalonado para o DPI atual (mínimo 8)."""
    return max(8, round(n * _SCALE))


# ── fontes mono (corpo do app) ────────────────────────────────────────────────
F_TITULO       = (MONO, _s(18), "bold")
F_SECAO        = (MONO, _s(13), "bold")
F_CARD_TITLE   = (MONO, _s(12), "bold")
F_CARD_VAL     = (MONO, _s(15), "bold")
F_CARD_DISPLAY = (MONO, _s(34), "bold")   # valor jumbo (ex.: saldo caixa)
F_CARD_SUB     = (MONO, _s(10))
F_STATUS       = (MONO, _s(11))
F_BADGE        = (MONO, _s(11), "bold")
F_TREE         = (MONO, _s(11))
F_TREE_HEAD    = (MONO, _s(11), "bold")

# ── cards sidebar (painel lateral compacto) ───────────────────────────────────
F_LATERAL_TITLE  = (MONO, _s(12), "bold")
F_LATERAL_SUB    = (MONO, _s(10))
F_LATERAL_VAL    = (MONO, _s(14), "bold")
F_LATERAL_VAL_SM = (MONO, _s(12), "bold")
F_LATERAL_BTC    = (MONO, _s(36), "bold")   # símbolo ₿ decorativo

# ── splash ────────────────────────────────────────────────────────────────────
F_SPLASH_TITLE  = (MONO, _s(22), "bold")
F_SPLASH_SUB    = (MONO, _s(10), "italic")
F_SPLASH_MICRO  = (MONO, _s(8))
F_SPLASH_STAT   = (MONO, _s(11), "bold")
F_SPLASH_HASH   = (MONO, _s(10))

# ── ui (estilos ttk + canvas) ─────────────────────────────────────────────────
F_UI_NORMAL   = (UI, _s(10))
F_UI_BOLD     = (UI, _s(10), "bold")
F_UI_SMALL    = (UI, _s(9))
F_UI_SMALL_BD = (UI, _s(9),  "bold")
F_UI_BTC      = (UI, _s(28), "bold")   # símbolo ₿ no canvas da splash


def _f(t: tuple) -> ctk.CTkFont:
    """Converte uma tupla de fonte para ctk.CTkFont."""
    weight = "bold"   if "bold"   in t else "normal"
    slant  = "italic" if "italic" in t else "roman"
    return ctk.CTkFont(t[0], t[1], weight=weight, slant=slant)
