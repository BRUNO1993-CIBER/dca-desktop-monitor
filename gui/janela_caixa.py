import platform
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
# pyrefly: ignore [missing-import]
import customtkinter as ctk

_FONT = "Segoe UI" if platform.system() == "Windows" else "Ubuntu"
_F_STATUS     = (_FONT, 11)
_F_BADGE      = (_FONT, 11, "bold")
_F_SECAO      = (_FONT, 12, "bold")
_F_CARD_TITLE = (_FONT, 11, "bold")
_F_CARD_SUB   = (_FONT, 10)
_F_CARD_VAL   = (_FONT, 14, "bold")
_F_TREE       = (_FONT, 10)
_F_TREE_HEAD  = (_FONT, 10, "bold")

BG_DEEP        = "#0a0e1a"
BG_SURFACE     = "#0d1117"
BG_CARD        = "#161b22"
BG_INPUT       = "#1c2128"
BORDER         = "#30363d"
BORDER_ACC     = "#f7931a"
BTC_ORANGE     = "#f7931a"
NEON_GREEN     = "#00ff88"
NEON_RED       = "#ff4d4d"
CYAN           = "#58a6ff"
YELLOW         = "#e3b341"
TEXT_PRIMARY   = "#e6edf3"
TEXT_SECONDARY = "#8b949e"
TEXT_MUTED     = "#484f58"


class JanelaCaixa(ctk.CTkFrame):
    def __init__(self, parent, data_manager, price_manager, analysis_engine):
        super().__init__(parent, fg_color=BG_DEEP, corner_radius=0)
        self._data_manager = data_manager
        self._price_manager = price_manager
        self._engine = analysis_engine
        self.display_currency = "USD"
        self.brl_toggle_var = tk.BooleanVar(value=False)
        self._cards = {}
        self._build_ui()
        self._bind_tab_select(parent)

    def _bind_tab_select(self, notebook):
        try:
            notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        except Exception:
            pass

    def _on_tab_changed(self, event):
        notebook = event.widget
        try:
            selected = notebook.select()
            if notebook.nametowidget(selected) is self:
                self.atualizar()
        except Exception:
            pass

    def _build_ui(self):
        self.pack(fill="both", expand=True)

        hero = ctk.CTkFrame(self, fg_color=BG_SURFACE, corner_radius=0)
        hero.pack(fill="x")

        accent_top = ctk.CTkFrame(hero, fg_color=BTC_ORANGE, height=2, corner_radius=0)
        accent_top.pack(fill="x")
        accent_top.pack_propagate(False)

        inner_hero = ctk.CTkFrame(hero, fg_color=BG_SURFACE, corner_radius=0)
        inner_hero.pack(fill="x", padx=30, pady=(18, 16))

        left = ctk.CTkFrame(inner_hero, fg_color=BG_SURFACE, corner_radius=0)
        left.pack(side=tk.LEFT, fill="both", expand=True)

        ctk.CTkLabel(
            left,
            text="CAIXA  ·  USDT",
            font=ctk.CTkFont(_FONT, 11, "bold"),
            text_color=TEXT_SECONDARY,
            anchor="w",
        ).pack(anchor="w")

        self.lbl_saldo = ctk.CTkLabel(
            left,
            text="Carregando...",
            font=ctk.CTkFont(_FONT, 34, "bold"),
            text_color=NEON_GREEN,
            anchor="w",
        )
        self.lbl_saldo.pack(anchor="w", pady=(4, 0))

        right = ctk.CTkFrame(inner_hero, fg_color=BG_SURFACE, corner_radius=0)
        right.pack(side=tk.RIGHT, anchor="center")

        toggle_frame = ctk.CTkFrame(
            right,
            fg_color=BG_CARD,
            corner_radius=8,
            border_width=1,
            border_color=BORDER,
        )
        toggle_frame.pack(anchor="e")

        ctk.CTkLabel(
            toggle_frame,
            text="Exibir em BRL",
            font=ctk.CTkFont(*_F_BADGE),
            text_color=TEXT_PRIMARY,
        ).pack(side=tk.LEFT, padx=(14, 6), pady=10)

        ctk.CTkCheckBox(
            toggle_frame,
            text="",
            variable=self.brl_toggle_var,
            command=self.toggle_currency,
            checkbox_width=20,
            checkbox_height=20,
            fg_color=BTC_ORANGE,
            hover_color=NEON_GREEN,
            border_color=BORDER,
            corner_radius=4,
            width=0,
        ).pack(side=tk.LEFT, padx=(0, 14), pady=10)

        self.lbl_status = ctk.CTkLabel(
            right,
            text="",
            font=ctk.CTkFont(_FONT, 11, "normal"),
            text_color=TEXT_SECONDARY,
            anchor="e",
        )
        self.lbl_status.pack(anchor="e", pady=(8, 0))

        accent_mid = ctk.CTkFrame(self, fg_color=BTC_ORANGE, height=2, corner_radius=0)
        accent_mid.pack(fill="x")
        accent_mid.pack_propagate(False)

        cards_frame = ctk.CTkFrame(self, fg_color=BG_DEEP, corner_radius=0)
        cards_frame.pack(fill="x", padx=30, pady=(20, 6))

        card_defs = [
            ("depositos", "↓  Depósitos USDT", NEON_GREEN),
            ("saques",    "↑  Saques USDT",    NEON_RED),
            ("compras",   "🛒  Compras Cripto", BTC_ORANGE),
            ("vendas",    "💱  Vendas Cripto",  CYAN),
        ]
        for key, label, cor in card_defs:
            card = self._make_card(cards_frame, label, "--", cor)
            card.pack(side=tk.LEFT, padx=(0, 12), fill="x", expand=True)
            self._cards[key] = card

        table_outer = ctk.CTkFrame(self, fg_color=BG_DEEP, corner_radius=0)
        table_outer.pack(fill="both", expand=True, padx=30, pady=(4, 10))

        sec_header = ctk.CTkFrame(table_outer, fg_color=BG_DEEP, corner_radius=0)
        sec_header.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            sec_header,
            text="EXTRATO DE MOVIMENTAÇÕES",
            font=ctk.CTkFont(*_F_SECAO),
            text_color=TEXT_SECONDARY,
        ).pack(side=tk.LEFT)

        sep = ctk.CTkFrame(sec_header, fg_color=BORDER, height=1, corner_radius=0)
        sep.pack(side=tk.LEFT, fill="x", expand=True, padx=(14, 0))

        tree_border = tk.Frame(table_outer, bg=BORDER, padx=1, pady=1)
        tree_border.pack(fill="both", expand=True)

        tree_container = tk.Frame(tree_border, bg=BG_CARD)
        tree_container.pack(fill="both", expand=True)

        style = ttk.Style()
        style.configure(
            "Caixa.Treeview",
            background=BG_CARD,
            fieldbackground=BG_CARD,
            foreground=TEXT_PRIMARY,
            rowheight=36,
            borderwidth=0,
            relief="flat",
            font=_F_TREE,
        )
        style.configure(
            "Caixa.Treeview.Heading",
            background=BG_INPUT,
            foreground=TEXT_SECONDARY,
            font=_F_TREE_HEAD,
            relief="flat",
            borderwidth=0,
        )
        style.map("Caixa.Treeview", background=[("selected", BTC_ORANGE)])
        style.layout("Caixa.Treeview", [("Treeview.treearea", {"sticky": "nswe"})])

        cols = ("Data", "Tipo", "Descrição", "Saldo Atualizado")
        self.tree = ttk.Treeview(
            tree_container,
            columns=cols,
            show="headings",
            selectmode="none",
            style="Caixa.Treeview",
        )

        self.tree.heading("Data",             text="DATA",             anchor="center")
        self.tree.heading("Tipo",             text="TIPO",             anchor="center")
        self.tree.heading("Descrição",        text="DESCRIÇÃO",        anchor="w")
        self.tree.heading("Saldo Atualizado", text="SALDO ATUALIZADO", anchor="center")

        self.tree.column("Data",             width=165, anchor="center", stretch=False)
        self.tree.column("Tipo",             width=155, anchor="center", stretch=False)
        self.tree.column("Descrição",        width=400, anchor="w",      stretch=True)
        self.tree.column("Saldo Atualizado", width=185, anchor="center", stretch=False)

        self.tree.tag_configure("deposito",     foreground=NEON_GREEN,     background=BG_CARD)
        self.tree.tag_configure("deposito_alt", foreground=NEON_GREEN,     background=BG_INPUT)
        self.tree.tag_configure("saque",        foreground=NEON_RED,       background=BG_CARD)
        self.tree.tag_configure("saque_alt",    foreground=NEON_RED,       background=BG_INPUT)
        self.tree.tag_configure("compra",       foreground=BTC_ORANGE,     background=BG_CARD)
        self.tree.tag_configure("compra_alt",   foreground=BTC_ORANGE,     background=BG_INPUT)
        self.tree.tag_configure("venda",        foreground=CYAN,           background=BG_CARD)
        self.tree.tag_configure("venda_alt",    foreground=CYAN,           background=BG_INPUT)
        self.tree.tag_configure("vazio",        foreground=TEXT_SECONDARY, background=BG_CARD)

        sb = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill="y")
        self.tree.pack(fill="both", expand=True)

        footer_sep = ctk.CTkFrame(self, fg_color=BORDER, height=1, corner_radius=0)
        footer_sep.pack(fill="x", side=tk.BOTTOM)
        footer_sep.pack_propagate(False)

        ctk.CTkLabel(
            self,
            text="Atualização automática ao acessar a aba",
            font=ctk.CTkFont(_FONT, 11, "normal"),
            text_color=TEXT_MUTED,
        ).pack(side=tk.BOTTOM, pady=6)

    def _make_card(self, parent, titulo, valor, cor):
        frame = ctk.CTkFrame(
            parent,
            fg_color=BG_CARD,
            corner_radius=8,
            border_width=1,
            border_color=cor,
        )
        ctk.CTkLabel(
            frame,
            text=titulo,
            font=ctk.CTkFont(*_F_CARD_TITLE),
            text_color=TEXT_SECONDARY,
            anchor="w",
        ).pack(anchor="w", padx=18, pady=(14, 2))

        lbl = ctk.CTkLabel(
            frame,
            text=valor,
            font=ctk.CTkFont(*_F_CARD_VAL),
            text_color=cor,
            anchor="w",
        )
        lbl.pack(anchor="w", padx=18, pady=(0, 14))
        frame._value_label = lbl
        return frame

    def _set_card(self, key, valor):
        try:
            self._cards[key]._value_label.configure(text=valor)
        except Exception:
            pass

    def toggle_currency(self):
        self.display_currency = "BRL" if self.brl_toggle_var.get() else "USD"
        taxa = self._price_manager.preco_brl
        if self.display_currency == "BRL" and (taxa is None or taxa <= 0):
            messagebox.showwarning("Aviso", "Cotação do BRL indisponível. Exibindo USD.")
            self.display_currency = "USD"
            self.brl_toggle_var.set(False)
        self.atualizar()

    def _fmt_val(self, val):
        if self.display_currency == "BRL":
            taxa = self._price_manager.preco_brl
            if taxa and taxa > 0:
                return f"R$ {val * taxa:,.2f}"
        return f"$ {val:,.2f}"

    def atualizar(self):
        self.lbl_status.configure(text="⟳  calculando...", text_color=CYAN)
        for row in self.tree.get_children():
            self.tree.delete(row)
        threading.Thread(target=self._worker_atualizar, daemon=True).start()

    def _worker_atualizar(self):
        try:
            ops  = self._data_manager.carregar_operacoes()
            info = self._engine.calcular_saldo_usdt(ops)
            self.after(0, lambda: self._atualizar_ui(info))
        except Exception as e:
            self.after(0, lambda: self.lbl_status.configure(text="✕ erro", text_color=NEON_RED))
            self.after(0, lambda: messagebox.showerror("Erro", f"Erro ao carregar saldo:\n{e}"))

    def _atualizar_ui(self, info):
        s_atual = info["saldo_atual"]
        hist    = info["historico"]
        agora   = datetime.now().strftime("%d/%m  %H:%M:%S")

        cor_saldo = NEON_GREEN if s_atual >= 0 else NEON_RED
        self.lbl_saldo.configure(text=self._fmt_val(s_atual), text_color=cor_saldo)
        self.lbl_status.configure(text=f"✓ atualizado  {agora}", text_color=TEXT_SECONDARY)

        depositos = sum(m["valor"] for m in hist if m.get("tipo") == "deposito_usdt") if hist else 0
        saques    = sum(m["valor"] for m in hist if m.get("tipo") == "saque_usdt")    if hist else 0
        compras   = sum(m["valor"] for m in hist if m.get("tipo") == "compra_crypto") if hist else 0
        vendas    = sum(m["valor"] for m in hist if m.get("tipo") == "venda_crypto")  if hist else 0

        self._set_card("depositos", self._fmt_val(depositos))
        self._set_card("saques",    self._fmt_val(saques))
        self._set_card("compras",   self._fmt_val(compras))
        self._set_card("vendas",    self._fmt_val(vendas))

        if not hist:
            self.tree.insert("", "end",
                             values=("—", "—", "Nenhuma movimentação registrada.", "—"),
                             tags=("vazio",))
            return

        TIPO_MAP = {
            "deposito_usdt": ("Depósito USDT", "deposito", "deposito_alt"),
            "saque_usdt":    ("Saque USDT",    "saque",    "saque_alt"),
            "compra_crypto": ("Compra Cripto", "compra",   "compra_alt"),
            "venda_crypto":  ("Venda Cripto",  "venda",    "venda_alt"),
        }

        for idx, mov in enumerate(reversed(hist)):
            d     = datetime.strptime(mov["data"], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y  %H:%M")
            tipo  = mov.get("tipo", "")
            label, tag_par, tag_imp = TIPO_MAP.get(tipo, (tipo, "deposito", "deposito_alt"))
            tag   = tag_par if idx % 2 == 0 else tag_imp
            self.tree.insert(
                "", "end",
                values=(d, label, mov["descricao"], self._fmt_val(mov["saldo_apos"])),
                tags=(tag,),
            )