import platform
# pyrefly: ignore [missing-import]
import customtkinter as ctk
from typing import Callable, List, Optional

_FONT_NAME = "Courier New" if platform.system() == "Windows" else "Monospace"
_F_TREE    = (_FONT_NAME, 11)
_F_ARROW   = (_FONT_NAME, 10)
_IS_LINUX  = platform.system() == "Linux"

class ComboCustom(ctk.CTkFrame):

    def __init__(
        self,
        parent,
        values: List[str] = [],
        width: int = 223,
        height: int = 36,
        fg_color: str = "#1e1e1e",
        text_color: str = "#ffffff",
        border_color: str = "#444",
        button_color: str = "#f7931a",
        button_hover_color: str = "#e8820f",
        dropdown_fg_color: str = "#1a1a2e",
        dropdown_hover_color: str = "#1E2D3D",
        command: Optional[Callable] = None,
        state: str = "readonly",
        **kw,
    ):
        super().__init__(parent, fg_color=fg_color,
                         border_color=border_color, border_width=1,
                         corner_radius=5, width=width, height=height, **kw)
        self.pack_propagate(False)

        self._values             = list(values)
        self._current            = ""
        self._command            = command
        self._state              = state
        self._width              = width
        self._height             = height
        self._fg_color           = fg_color
        self._text_color         = text_color
        self._button_color       = button_color
        self._button_hover_color = button_hover_color
        self._dropdown_fg_color  = dropdown_fg_color
        self._dropdown_hover     = dropdown_hover_color
        self._dropdown: Optional[ctk.CTkToplevel] = None

        self._lbl = ctk.CTkButton(
            self, text="", font=_F_TREE,
            fg_color="transparent", hover_color=dropdown_hover_color,
            text_color=text_color, anchor="center", corner_radius=4,
            command=self._toggle,
        )
        self._lbl.pack(side="left", fill="both", expand=True, padx=(8, 0))

        self._btn = ctk.CTkButton(
            self, text="▾", font=_F_ARROW, width=32,
            fg_color=button_color, hover_color=button_hover_color,
            text_color="#1a1a1a", corner_radius=4, command=self._toggle,
        )
        self._btn.pack(side="right", fill="y", padx=2, pady=2)

    def _toggle(self):
        if self._state == "disabled":
            return
        if self._dropdown and self._dropdown.winfo_exists():
            self._close()
        else:
            self._open()

    def _open(self):
        self._dropdown = ctk.CTkToplevel()
        self._dropdown.overrideredirect(True)
        self._dropdown.attributes("-topmost", True)

        self.update_idletasks()
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        h = min(len(self._values) * 36, 216)
        self._dropdown.geometry(f"{self._width}x{h}+{x}+{y}")
        self._dropdown.configure(fg_color=self._dropdown_fg_color)

        scroll = ctk.CTkScrollableFrame(
            self._dropdown,
            fg_color=self._dropdown_fg_color,
            scrollbar_button_color=self._button_color,
            scrollbar_button_hover_color=self._button_hover_color,
            corner_radius=0,
        )
        scroll.pack(fill="both", expand=True)

        for v in self._values:
            btn = ctk.CTkButton(
                scroll, text=v, font=_F_TREE, anchor="center",
                fg_color="transparent", hover_color=self._dropdown_hover,
                text_color=self._text_color, height=34, corner_radius=0,
                command=lambda val=v: self._select(val),
            )
            btn.pack(fill="x", padx=2, pady=1)

        self._bind_scroll(scroll)
        self._bind_outside_click()

    def _bind_scroll(self, scroll_frame: ctk.CTkScrollableFrame):
        def _scroll(delta):
            scroll_frame._parent_canvas.yview_scroll(delta, "units")

        def _on_wheel(e):
            if _IS_LINUX:
                if e.num == 4:
                    _scroll(-1)
                elif e.num == 5:
                    _scroll(1)
            else:
                _scroll(-1 if e.delta > 0 else 1)

        targets = [scroll_frame, scroll_frame._parent_canvas]
        for child in scroll_frame.winfo_children():
            targets.append(child)

        for w in targets:
            if _IS_LINUX:
                w.bind("<Button-4>", _on_wheel, add="+")
                w.bind("<Button-5>", _on_wheel, add="+")
            else:
                w.bind("<MouseWheel>", _on_wheel, add="+")

    def _bind_outside_click(self):
        root = self.winfo_toplevel()

        def _check_click(e):
            if not (self._dropdown and self._dropdown.winfo_exists()):
                return
            w = e.widget.winfo_containing(e.x_root, e.y_root)
            if w is None:
                self._close()
                return
            inside_dropdown = str(w).startswith(str(self._dropdown))
            inside_self     = str(w).startswith(str(self))
            if not inside_dropdown and not inside_self:
                self._close()

        root.bind("<Button-1>", _check_click, add="+")
        self._dropdown.bind("<Destroy>",
                            lambda e: root.unbind("<Button-1>"), add="+")

    def _close(self):
        if self._dropdown and self._dropdown.winfo_exists():
            self._dropdown.destroy()
        self._dropdown = None

    def _select(self, value: str):
        self._current = value
        self._lbl.configure(text=value)
        self._close()
        if self._command:
            self._command(value)

    def get(self) -> str:
        return self._current

    def set(self, value: str):
        self._current = value
        self._lbl.configure(text=value)

    def configure(self, **kw):
        if "values" in kw:
            self._values = list(kw.pop("values"))
        if "state" in kw:
            self._state = kw.pop("state")
            s = "normal" if self._state != "disabled" else "disabled"
            self._lbl.configure(state=s)
            self._btn.configure(state=s)
        if "command" in kw:
            self._command = kw.pop("command")
        if kw:
            super().configure(**kw)

    def bind(self, sequence=None, func=None, add=None):
        self._lbl.bind(sequence, func, add)