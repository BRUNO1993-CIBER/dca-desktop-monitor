import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import threading

from tema_cripto import (
    BG_CARD, BG_INPUT, BTC_ORANGE, NEON_GREEN, NEON_RED, CYAN,
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

    def _build_ui(self):
        self.pack(fill="both", expand=True, padx=15, pady=15)

        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(10, 10))

        ttk.Button(toolbar, text="🔄 Atualizar Caixa", command=self.atualizar, cursor="hand2").pack(side=tk.LEFT)
        ttk.Checkbutton(
            toolbar, text="Exibir em BRL", variable=self.brl_toggle_var, command=self.toggle_currency
        ).pack(side=tk.LEFT, padx=15)

        self.lbl_status = ttk.Label(toolbar, text="", font=("Segoe UI", 9), foreground=TEXT_SECONDARY)
        self.lbl_status.pack(side=tk.RIGHT)

        header_frame = tk.Frame(self, bg=BG_CARD, highlightbackground=BORDER, highlightthickness=1)
        header_frame.pack(fill="x", pady=(0, 10))
        
        self.lbl_saldo = tk.Label(header_frame, text="Saldo Atual: --", font=("Segoe UI", 16, "bold"), bg=BG_CARD, fg=NEON_GREEN, pady=15)
        self.lbl_saldo.pack()
        tk.Frame(self, bg=BTC_ORANGE, height=1).pack(fill="x", pady=(0, 10))

        tree_frame = ttk.LabelFrame(self, text=" Histórico de Movimentações (Extrato) ", padding=10)
        tree_frame.pack(fill="both", expand=True)

        cols = ("Data", "Descrição", "Saldo Atualizado")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="none")
        self.tree.heading("Data", text="Data", anchor="center")
        self.tree.heading("Descrição", text="Descrição", anchor="center")
        self.tree.heading("Saldo Atualizado", text="Saldo Atualizado", anchor="center")
        
        self.tree.column("Data", width=160, anchor="center")
        self.tree.column("Descrição", width=400, anchor="center")
        self.tree.column("Saldo Atualizado", width=160, anchor="center")

        tag_cores_treeview(self.tree)
        self.tree.tag_configure("positivo", foreground=NEON_GREEN, background=BG_CARD)
        self.tree.tag_configure("negativo", foreground=NEON_RED, background=BG_CARD)
        self.tree.tag_configure("positivo_alt", foreground=NEON_GREEN, background="#12171e")
        self.tree.tag_configure("negativo_alt", foreground=NEON_RED, background="#12171e")

        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill="y")
        self.tree.pack(fill="both", expand=True)

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
                return f"R${val * taxa:,.2f}"
        return f"${val:,.2f}"

    def atualizar(self):
        self.lbl_status.config(text="🔄 Calculando...", foreground=CYAN)
        for row in self.tree.get_children():
            self.tree.delete(row)
        threading.Thread(target=self._worker_atualizar, daemon=True).start()

    def _worker_atualizar(self):
        try:
            ops = self._data_manager.carregar_operacoes()
            info = self._engine.calcular_saldo_usdt(ops)
            self.after(0, lambda: self._atualizar_ui(info))
        except Exception as e:
            self.after(0, lambda: self.lbl_status.config(text="Erro", foreground=NEON_RED))
            self.after(0, lambda: messagebox.showerror("Erro", f"Erro ao carregar saldo:\n{e}"))

    def _atualizar_ui(self, info):
        s_atual = info["saldo_atual"]
        hist = info["historico"]
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        self.lbl_status.config(text=f"Atualizado: {agora}", foreground=TEXT_SECONDARY)
        
        c_saldo = NEON_GREEN if s_atual >= 0 else NEON_RED
        self.lbl_saldo.config(text=f"Saldo Atual do Caixa: {self._fmt_val(s_atual)}", fg=c_saldo)

        if not hist:
            self.tree.insert("", "end", values=("", "Nenhuma movimentação de caixa registrada.", ""))
            return

        for idx, mov in enumerate(reversed(hist)):
            d = datetime.strptime(mov["data"], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")
            par = idx % 2 == 0
            
            if mov["saldo_apos"] >= 0:
                tag = "positivo" if par else "positivo_alt"
            else:
                tag = "negativo" if par else "negativo_alt"
                
            self.tree.insert("", "end", values=(d, mov["descricao"], self._fmt_val(mov['saldo_apos'])), tags=(tag,))