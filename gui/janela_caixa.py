import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import threading

from config.tema_cripto import (
    BG_CARD, BG_INPUT, BG_DEEP, BTC_ORANGE, NEON_GREEN, NEON_RED, CYAN,
    TEXT_PRIMARY, TEXT_SECONDARY, BORDER, tag_cores_treeview
)


class JanelaCaixa(ttk.Frame):
    def __init__(self, parent, data_manager, price_manager, analysis_engine):
        super().__init__(parent)
        self._data_manager = data_manager
        self._price_manager = price_manager
        self._engine = analysis_engine
        self.display_currency = "USD"
        self.brl_toggle_var = tk.BooleanVar(value=False)
        self._build_ui()
        self._bind_tab_select(parent)

    # ── auto-refresh ao selecionar a aba ─────────────────────────────────────
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

    # ── interface ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.pack(fill="both", expand=True)

        # ── faixa hero com saldo ─────────────────────────────────────────────
        hero = tk.Frame(self, bg=BG_DEEP)
        hero.pack(fill="x")

        tk.Frame(hero, bg=BTC_ORANGE, height=2).pack(fill="x")

        inner_hero = tk.Frame(hero, bg=BG_DEEP)
        inner_hero.pack(fill="x", padx=30, pady=(18, 16))

        left = tk.Frame(inner_hero, bg=BG_DEEP)
        left.pack(side=tk.LEFT, fill="both", expand=True)

        tk.Label(
            left, text="CAIXA  ·  USDT",
            font=("Segoe UI", 9, "bold"),
            bg=BG_DEEP, fg=TEXT_SECONDARY, anchor="w",
        ).pack(anchor="w")

        self.lbl_saldo = tk.Label(
            left, text="Carregando...",
            font=("Segoe UI", 28, "bold"),
            bg=BG_DEEP, fg=NEON_GREEN, anchor="w",
        )
        self.lbl_saldo.pack(anchor="w", pady=(2, 0))

        right = tk.Frame(inner_hero, bg=BG_DEEP)
        right.pack(side=tk.RIGHT, anchor="center")

        toggle_frame = tk.Frame(
            right, bg=BG_CARD, padx=14, pady=8,
            highlightbackground=BORDER, highlightthickness=1,
        )
        toggle_frame.pack(anchor="e")

        tk.Label(
            toggle_frame, text="Exibir em BRL",
            font=("Segoe UI", 10),
            bg=BG_CARD, fg=TEXT_PRIMARY,
        ).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Checkbutton(
            toggle_frame,
            variable=self.brl_toggle_var,
            command=self.toggle_currency,
            cursor="hand2",
        ).pack(side=tk.LEFT)

        self.lbl_status = tk.Label(
            right, text="",
            font=("Segoe UI", 8, "italic"),
            bg=BG_DEEP, fg=TEXT_SECONDARY, anchor="e",
        )
        self.lbl_status.pack(anchor="e", pady=(6, 0))

        tk.Frame(self, bg=BTC_ORANGE, height=2).pack(fill="x")

        # ── 4 cards de resumo ────────────────────────────────────────────────
        cards_frame = tk.Frame(self, bg=BG_DEEP)
        cards_frame.pack(fill="x", padx=30, pady=(18, 4))

        self._cards = {}
        card_defs = [
            ("depositos", "↓  Depósitos USDT",  NEON_GREEN),
            ("saques",    "↑  Saques USDT",     NEON_RED),
            ("compras",   "🛒  Compras Cripto",  BTC_ORANGE),
            ("vendas",    "💱  Vendas Cripto",   CYAN),
        ]
        for key, label, cor in card_defs:
            c = self._make_card(cards_frame, label, "--", cor)
            c.pack(side=tk.LEFT, padx=(0, 12), fill="x", expand=True)
            self._cards[key] = c

        # ── tabela extrato ───────────────────────────────────────────────────
        table_outer = tk.Frame(self, bg=BG_DEEP, padx=30, pady=10)
        table_outer.pack(fill="both", expand=True)

        sec_header = tk.Frame(table_outer, bg=BG_DEEP)
        sec_header.pack(fill="x", pady=(0, 8))

        tk.Label(
            sec_header, text="EXTRATO DE MOVIMENTAÇÕES",
            font=("Segoe UI", 9, "bold"),
            bg=BG_DEEP, fg=TEXT_SECONDARY,
        ).pack(side=tk.LEFT)

        tk.Frame(sec_header, bg=BORDER, height=1).pack(
            side=tk.LEFT, fill="x", expand=True, padx=(12, 0), pady=6,
        )

        tree_container = tk.Frame(
            table_outer, bg=BG_CARD,
            highlightbackground=BORDER, highlightthickness=1,
        )
        tree_container.pack(fill="both", expand=True)

        style = ttk.Style()
        style.configure(
            "Caixa.Treeview",
            background=BG_CARD,
            fieldbackground=BG_CARD,
            foreground=TEXT_PRIMARY,
            rowheight=32,
            borderwidth=0,
            relief="flat",
            font=("Segoe UI", 10),
        )
        style.configure(
            "Caixa.Treeview.Heading",
            background=BG_INPUT,
            foreground=TEXT_SECONDARY,
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            borderwidth=0,
        )
        style.map("Caixa.Treeview", background=[("selected", BTC_ORANGE)])
        style.layout("Caixa.Treeview", [("Treeview.treearea", {"sticky": "nswe"})])

        cols = ("Data", "Tipo", "Descrição", "Saldo Atualizado")
        self.tree = ttk.Treeview(
            tree_container, columns=cols, show="headings",
            selectmode="none", style="Caixa.Treeview",
        )

        self.tree.heading("Data",             text="DATA",             anchor="center")
        self.tree.heading("Tipo",             text="TIPO",             anchor="center")
        self.tree.heading("Descrição",        text="DESCRIÇÃO",        anchor="w")
        self.tree.heading("Saldo Atualizado", text="SALDO ATUALIZADO", anchor="center")

        self.tree.column("Data",             width=155, anchor="center", stretch=False)
        self.tree.column("Tipo",             width=140, anchor="center", stretch=False)
        self.tree.column("Descrição",        width=380, anchor="w",      stretch=True)
        self.tree.column("Saldo Atualizado", width=175, anchor="center", stretch=False)

        self.tree.tag_configure("deposito",     foreground=NEON_GREEN,  background=BG_CARD)
        self.tree.tag_configure("deposito_alt", foreground=NEON_GREEN,  background="#12171e")
        self.tree.tag_configure("saque",        foreground=NEON_RED,    background=BG_CARD)
        self.tree.tag_configure("saque_alt",    foreground=NEON_RED,    background="#12171e")
        self.tree.tag_configure("compra",       foreground=BTC_ORANGE,  background=BG_CARD)
        self.tree.tag_configure("compra_alt",   foreground=BTC_ORANGE,  background="#12171e")
        self.tree.tag_configure("venda",        foreground=CYAN,        background=BG_CARD)
        self.tree.tag_configure("venda_alt",    foreground=CYAN,        background="#12171e")
        self.tree.tag_configure("vazio",        foreground=TEXT_SECONDARY, background=BG_CARD)

        sb = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill="y")
        self.tree.pack(fill="both", expand=True)

        # rodapé
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", side=tk.BOTTOM)
        tk.Label(
            self, text="Atualização automática ao acessar a aba",
            font=("Segoe UI", 8, "italic"),
            bg=BG_DEEP, fg=TEXT_SECONDARY, pady=5,
        ).pack(side=tk.BOTTOM)

    # ── card helper ──────────────────────────────────────────────────────────
    def _make_card(self, parent, titulo, valor, cor):
        frame = tk.Frame(
            parent, bg=BG_CARD,
            highlightbackground=cor, highlightthickness=1,
            padx=18, pady=12,
        )
        tk.Label(
            frame, text=titulo,
            font=("Segoe UI", 8, "bold"),
            bg=BG_CARD, fg=TEXT_SECONDARY,
        ).pack(anchor="w")
        lbl = tk.Label(
            frame, text=valor,
            font=("Segoe UI", 15, "bold"),
            bg=BG_CARD, fg=cor,
        )
        lbl.pack(anchor="w", pady=(2, 0))
        frame._value_label = lbl
        return frame

    def _set_card(self, key, valor):
        try:
            self._cards[key]._value_label.config(text=valor)
        except Exception:
            pass

    # ── moeda ─────────────────────────────────────────────────────────────────
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

    # ── dados ─────────────────────────────────────────────────────────────────
    def atualizar(self):
        self.lbl_status.config(text="⟳  calculando...", foreground=CYAN)
        for row in self.tree.get_children():
            self.tree.delete(row)
        threading.Thread(target=self._worker_atualizar, daemon=True).start()

    def _worker_atualizar(self):
        try:
            ops  = self._data_manager.carregar_operacoes()
            info = self._engine.calcular_saldo_usdt(ops)
            self.after(0, lambda: self._atualizar_ui(info))
        except Exception as e:
            self.after(0, lambda: self.lbl_status.config(text="✕ erro", foreground=NEON_RED))
            self.after(0, lambda: messagebox.showerror("Erro", f"Erro ao carregar saldo:\n{e}"))

    def _atualizar_ui(self, info):
        s_atual = info["saldo_atual"]
        hist    = info["historico"]
        agora   = datetime.now().strftime("%d/%m  %H:%M:%S")

        cor_saldo = NEON_GREEN if s_atual >= 0 else NEON_RED
        self.lbl_saldo.config(text=self._fmt_val(s_atual), fg=cor_saldo)
        self.lbl_status.config(text=f"✓ atualizado  {agora}", foreground=TEXT_SECONDARY)

        # ── cards com tipos reais do backend ─────────────────────────────────
        depositos = sum(m["valor"] for m in hist if m.get("tipo") == "deposito_usdt") if hist else 0
        saques    = sum(m["valor"] for m in hist if m.get("tipo") == "saque_usdt")    if hist else 0
        compras   = sum(m["valor"] for m in hist if m.get("tipo") == "compra_crypto") if hist else 0
        vendas    = sum(m["valor"] for m in hist if m.get("tipo") == "venda_crypto")  if hist else 0

        self._set_card("depositos", self._fmt_val(depositos))
        self._set_card("saques",    self._fmt_val(saques))
        self._set_card("compras",   self._fmt_val(compras))
        self._set_card("vendas",    self._fmt_val(vendas))

        # ── extrato ───────────────────────────────────────────────────────────
        if not hist:
            self.tree.insert("", "end",
                             values=("—", "—", "Nenhuma movimentação registrada.", "—"),
                             tags=("vazio",))
            return

        # mapa tipo -> (label legível, tag par, tag ímpar)
        TIPO_MAP = {
            "deposito_usdt": ("Depósito USDT",  "deposito", "deposito_alt"),
            "saque_usdt":    ("Saque USDT",     "saque",    "saque_alt"),
            "compra_crypto": ("Compra Cripto",  "compra",   "compra_alt"),
            "venda_crypto":  ("Venda Cripto",   "venda",    "venda_alt"),
        }

        for idx, mov in enumerate(reversed(hist)):
            d    = datetime.strptime(mov["data"], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y  %H:%M")
            tipo = mov.get("tipo", "")
            label, tag_par, tag_imp = TIPO_MAP.get(tipo, (tipo, "deposito", "deposito_alt"))
            tag  = tag_par if idx % 2 == 0 else tag_imp
            self.tree.insert(
                "", "end",
                values=(d, label, mov["descricao"], self._fmt_val(mov["saldo_apos"])),
                tags=(tag,),
            )