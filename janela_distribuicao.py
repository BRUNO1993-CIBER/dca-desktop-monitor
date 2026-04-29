import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable
from datetime import datetime
import logging
import math

from tema_cripto import (
    BG_DEEP, BG_SURFACE, BG_CARD, BG_INPUT,
    BTC_ORANGE, NEON_GREEN, NEON_RED, CYAN, YELLOW,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, BORDER,
    tag_cores_treeview,
)

logger = logging.getLogger(__name__)

_CORES_ATIVOS = [
    "#f7931a", "#58a6ff", "#00ff88", "#e3b341", "#a371f7",
    "#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4", "#ff9ff3",
]

_DIVERSIFICACAO = [
    (7, "🟢 Excelente", NEON_GREEN),
    (4, "🟡 Moderada",  YELLOW),
    (2, "🟠 Baixa",     BTC_ORANGE),
    (0, "🔴 Mínima",    NEON_RED),
]


class JanelaDistribuicao(ttk.Frame):

    def __init__(self, parent, data_manager, price_manager, analysis_engine,
                 on_change: Optional[Callable] = None):
        super().__init__(parent)
        self._data_manager = data_manager
        self._price_manager = price_manager
        self._engine = analysis_engine
        self._on_change = on_change or (lambda: None)
        self._cor_map: dict[str, str] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        self.pack(fill="both", expand=True, padx=15, pady=15)

        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(0, 12))

        ttk.Button(toolbar, text="🔄 Atualizar Tudo", command=self.atualizar,
                   cursor="hand2").pack(side=tk.LEFT)
        ttk.Button(toolbar, text="📜 Extrato do Caixa", command=self._popup_saldo_usdt,
                   style="Secondary.TButton", cursor="hand2").pack(side=tk.LEFT, padx=(10, 0))

        resumo_frame = ttk.Frame(self)
        resumo_frame.pack(fill="x", pady=(0, 12))

        self._lbl_cripto = self._criar_card(resumo_frame, "🪙 Ativos (Cripto)", CYAN)
        self._lbl_caixa  = self._criar_card(resumo_frame, "💰 Caixa (USDT)",    NEON_GREEN)
        self._lbl_total  = self._criar_card(resumo_frame, "💼 Patrimônio Total", BTC_ORANGE)
        self._lbl_status = self._criar_card(resumo_frame, "🎯 Diversificação",   TEXT_SECONDARY)

        main_body = ttk.Frame(self)
        main_body.pack(fill="both", expand=True)
        main_body.columnconfigure(0, weight=1)
        main_body.columnconfigure(1, weight=1)
        main_body.rowconfigure(0, weight=4)
        main_body.rowconfigure(1, weight=3)

        donut_frame = ttk.LabelFrame(main_body, text=" Gráfico de Distribuição ", padding=10)
        donut_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=(0, 10))
        self._canvas = tk.Canvas(donut_frame, bg=BG_CARD, highlightthickness=0)
        self._canvas.pack(fill="both", expand=True)
        self._canvas.bind("<Configure>", lambda e: self._agendar_donut())
        self._donut_dados = []

        aloc_frame = ttk.LabelFrame(main_body, text=" 📊 Alocação da Carteira ", padding=10)
        aloc_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=(0, 10))

        cols_aloc = ("Ativo", "Alocação (%)", "Valor Total", "Quantidade")
        self._aloc_tree = ttk.Treeview(aloc_frame, columns=cols_aloc, show="headings", selectmode="none")
        widths_aloc = {"Ativo": 80, "Alocação (%)": 100, "Valor Total": 180, "Quantidade": 120}
        for col in cols_aloc:
            self._aloc_tree.heading(col, text=col)
            self._aloc_tree.column(col, width=widths_aloc[col], anchor="center")

        tag_cores_treeview(self._aloc_tree)

        sb_aloc = ttk.Scrollbar(aloc_frame, orient="vertical", command=self._aloc_tree.yview)
        self._aloc_tree.configure(yscrollcommand=sb_aloc.set)
        sb_aloc.pack(side=tk.RIGHT, fill="y")
        self._aloc_tree.pack(fill="both", expand=True)

        pl_frame = ttk.LabelFrame(main_body, text=" 📉 Lucro / Prejuízo (P&L) ", padding=10)
        pl_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")

        cols_pl = ("Ativo", "Preço Médio", "Preço Atual", "Variação (%)", "Resultado ($)")
        self._pl_tree = ttk.Treeview(pl_frame, columns=cols_pl, show="headings", selectmode="none")
        widths_pl = {"Ativo": 120, "Preço Médio": 160, "Preço Atual": 160, "Variação (%)": 160, "Resultado ($)": 160}
        for col in cols_pl:
            self._pl_tree.heading(col, text=col)
            self._pl_tree.column(col, width=widths_pl[col], anchor="center")

        tag_cores_treeview(self._pl_tree)
        self._pl_tree.tag_configure("ganho",  foreground=NEON_GREEN, background=BG_CARD,   font=("Segoe UI", 9, "bold"))
        self._pl_tree.tag_configure("perda",  foreground=NEON_RED,   background=BG_CARD,   font=("Segoe UI", 9, "bold"))
        self._pl_tree.tag_configure("neutro", foreground=TEXT_SECONDARY, background=BG_CARD)
        self._pl_tree.tag_configure("ganho_alt", foreground=NEON_GREEN, background="#12171e", font=("Segoe UI", 9, "bold"))
        self._pl_tree.tag_configure("perda_alt", foreground=NEON_RED,   background="#12171e", font=("Segoe UI", 9, "bold"))

        sb_pl = ttk.Scrollbar(pl_frame, orient="vertical", command=self._pl_tree.yview)
        self._pl_tree.configure(yscrollcommand=sb_pl.set)
        sb_pl.pack(side=tk.RIGHT, fill="y")
        self._pl_tree.pack(fill="both", expand=True)

    def _criar_card(self, parent: tk.Widget, titulo: str, cor: str) -> ttk.Label:
        frame = tk.Frame(parent, bg=BG_CARD, highlightbackground=BORDER, highlightthickness=1)
        frame.pack(side=tk.LEFT, fill="x", expand=True, padx=5, pady=2)
        tk.Label(frame, text=titulo, font=("Segoe UI", 9, "bold"),
                 bg=BG_CARD, fg=TEXT_SECONDARY, anchor="center").pack(fill="x", pady=(8, 2))
        lbl = tk.Label(frame, text="--", font=("Segoe UI", 12, "bold"),
                       bg=BG_CARD, fg=cor, anchor="center")
        lbl.pack(fill="x", pady=(0, 8))
        return lbl

    def _formatar_moeda(self, valor_usd: float, preco_brl: float) -> str:
        base = f"${valor_usd:,.2f}"
        if preco_brl > 0:
            base += f"  (R$ {valor_usd * preco_brl:,.2f})"
        return base

    def atualizar(self) -> None:
        try:
            operacoes = self._data_manager.carregar_operacoes()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar dados: {e}")
            return

        for row in self._aloc_tree.get_children():
            self._aloc_tree.delete(row)
        for row in self._pl_tree.get_children():
            self._pl_tree.delete(row)
        self._canvas.delete("all")

        if not operacoes:
            for lbl in (self._lbl_cripto, self._lbl_caixa, self._lbl_total):
                lbl.config(text="--")
            self._lbl_status.config(text="--", fg=TEXT_SECONDARY)
            return

        saldo_info   = self._engine.calcular_saldo_usdt(operacoes)
        saldo_usdt   = saldo_info["saldo_atual"]
        resultado    = self._engine.calcular_distribuicao_portfolio(operacoes, self._price_manager.precos_cache)
        distribuicao = resultado["distribuicao"]
        total_cripto = resultado["total_investido"]
        total_port   = total_cripto + saldo_usdt
        preco_brl    = self._price_manager.preco_brl

        self._lbl_cripto.config(text=self._formatar_moeda(total_cripto, preco_brl))
        self._lbl_caixa.config(
            text=self._formatar_moeda(saldo_usdt, preco_brl),
            fg=NEON_GREEN if saldo_usdt >= 0 else NEON_RED,
        )
        self._lbl_total.config(text=self._formatar_moeda(total_port, preco_brl))

        if not distribuicao:
            self._lbl_status.config(text="--", fg=TEXT_SECONDARY)
            self._donut_dados = []
            return

        ordenados = sorted(distribuicao.items(), key=lambda x: x[1]["percentual"], reverse=True)
        self._cor_map = {m: _CORES_ATIVOS[i % len(_CORES_ATIVOS)] for i, (m, _) in enumerate(ordenados)}

        n_ativos = len(distribuicao)
        label_div, cor_div = next((lb, cor) for minv, lb, cor in _DIVERSIFICACAO if n_ativos >= minv)
        self._lbl_status.config(text=label_div, fg=cor_div)

        for idx, (moeda, dados) in enumerate(ordenados):
            pct     = dados["percentual"]
            val     = dados["valor_atual"]
            qtd     = dados["quantidade"]
            fmt_qtd = f"{qtd:.2f}" if moeda == "USDT" else f"{qtd:.6f}"
            tag     = "par" if idx % 2 == 0 else "impar"
            self._aloc_tree.insert("", "end",
                values=(moeda, f"{pct:.2f}%", self._formatar_moeda(val, preco_brl), fmt_qtd),
                tags=(tag,),
            )

        self._donut_dados = ordenados
        self._agendar_donut()
        self._atualizar_pl(operacoes, distribuicao)

    def _agendar_donut(self) -> None:
        self.after(100, self._desenhar_donut)

    def _desenhar_donut(self) -> None:
        self._canvas.delete("all")
        if not self._donut_dados:
            return

        w = self._canvas.winfo_width()
        h = self._canvas.winfo_height()
        if w < 50 or h < 50:
            return

        cx, cy = w // 2, h // 2
        raio   = min(cx, cy) - 2
        furo   = int(raio * 0.55)
        inicio = -90.0

        for moeda, dados in self._donut_dados:
            grau = (dados["percentual"] / 100) * 360
            cor  = self._cor_map.get(moeda, TEXT_MUTED)

            self._canvas.create_arc(
                cx - raio, cy - raio, cx + raio, cy + raio,
                start=inicio, extent=grau, fill=cor, outline=BG_CARD, width=2,
            )

            if dados["percentual"] >= 3.0:
                ang_rad   = math.radians(inicio + grau / 2)
                raio_txt  = furo + (raio - furo) / 2
                self._canvas.create_text(
                    cx + raio_txt * math.cos(ang_rad),
                    cy - raio_txt * math.sin(ang_rad),
                    text=moeda, font=("Segoe UI", 9, "bold"), fill=BG_DEEP,
                )

            inicio += grau

        self._canvas.create_oval(cx - furo, cy - furo, cx + furo, cy + furo,
                                 fill=BG_CARD, outline=BG_CARD)
        self._canvas.create_text(cx, cy - 10, text=str(len(self._donut_dados)),
                                 font=("Segoe UI", 18, "bold"), fill=BTC_ORANGE)
        self._canvas.create_text(cx, cy + 12, text="ativos",
                                 font=("Segoe UI", 10), fill=TEXT_SECONDARY)

        leg_x, leg_y = 15, 15
        for moeda, dados in self._donut_dados:
            cor = self._cor_map.get(moeda, TEXT_MUTED)
            self._canvas.create_rectangle(leg_x, leg_y, leg_x + 10, leg_y + 10,
                                          fill=cor, outline="")
            self._canvas.create_text(leg_x + 18, leg_y + 5,
                                     text=f"{moeda} {dados['percentual']:.1f}%",
                                     font=("Segoe UI", 9, "bold"),
                                     fill=TEXT_PRIMARY, anchor="w")
            leg_y += 18
            if leg_y > h - 25:
                break

    def _atualizar_pl(self, operacoes: list, distribuicao: dict) -> None:
        portfolio = self._engine.calcular_portfolio(operacoes, self._price_manager.precos_cache)
        preco_brl = self._price_manager.preco_brl

        ordenados = sorted(distribuicao.items(), key=lambda x: x[1]["percentual"], reverse=True)

        for idx, (moeda, _) in enumerate(ordenados):
            if moeda == "USDT":
                continue

            dados_port  = portfolio.get(moeda, {})
            preco_medio = dados_port.get("pmc_final", 0)
            preco_atual = self._price_manager.get_preco(moeda) or 0

            if preco_medio <= 0 or preco_atual <= 0:
                self._pl_tree.insert("", "end",
                    values=(moeda, "—", "—", "—", "—"),
                    tags=("neutro",),
                )
                continue

            var_pct = ((preco_atual - preco_medio) / preco_medio) * 100
            qtd     = dados_port.get("quantidade_final", 0)
            pl_usd  = (preco_atual - preco_medio) * qtd
            sinal   = "+" if pl_usd >= 0 else "-"

            txt_var = f"{sinal}{abs(var_pct):.2f}%"
            txt_resultado = f"{sinal}${abs(pl_usd):,.2f}"
            if preco_brl > 0:
                txt_resultado += f"  (R$ {abs(pl_usd * preco_brl):,.2f})"

            txt_pm = f"${preco_medio:,.2f}"
            txt_pa = f"${preco_atual:,.2f}"
            if preco_brl > 0:
                txt_pm += f"  (R$ {preco_medio * preco_brl:,.2f})"
                txt_pa += f"  (R$ {preco_atual * preco_brl:,.2f})"

            par = idx % 2 == 0
            if var_pct > 0:
                tag = "ganho" if par else "ganho_alt"
            elif var_pct < 0:
                tag = "perda" if par else "perda_alt"
            else:
                tag = "neutro"

            self._pl_tree.insert("", "end",
                values=(moeda, txt_pm, txt_pa, txt_var, txt_resultado),
                tags=(tag,),
            )

    def _popup_saldo_usdt(self) -> None:
        try:
            operacoes  = self._data_manager.carregar_operacoes()
            saldo_info = self._engine.calcular_saldo_usdt(operacoes)
            saldo_atual = saldo_info["saldo_atual"]
            historico   = saldo_info["historico"]
            preco_brl   = self._price_manager.preco_brl
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar saldo:\n{e}")
            return

        popup = tk.Toplevel(self)
        popup.title("📜 Extrato do Caixa USDT")
        popup.configure(bg=BG_DEEP)

        def _maximizar():
            try:
                popup.state("zoomed")
            except Exception:
                popup.attributes("-zoomed", True)

        popup.after(1, _maximizar)

        header = tk.Frame(popup, bg=BG_CARD, pady=12)
        header.pack(fill="x")

        cor_saldo = NEON_GREEN if saldo_atual >= 0 else NEON_RED
        texto_saldo = f"💰 Saldo Atual: ${saldo_atual:,.2f}"
        if preco_brl > 0:
            texto_saldo += f"  (R$ {saldo_atual * preco_brl:,.2f})"

        tk.Label(header, text=texto_saldo, font=("Segoe UI", 14, "bold"),
                 bg=BG_CARD, fg=cor_saldo).pack()

        tk.Frame(popup, bg=BTC_ORANGE, height=1).pack(fill="x")

        cols = ("Data", "Descrição", "Saldo Atualizado")
        tree = ttk.Treeview(popup, columns=cols, show="headings", height=12)
        tree.heading("Data",             text="Data",             anchor="center")
        tree.heading("Descrição",        text="Descrição",        anchor="center")
        tree.heading("Saldo Atualizado", text="Saldo Atualizado", anchor="center")
        tree.column("Data",             width=160, anchor="center")
        tree.column("Descrição",        width=380, anchor="center")
        tree.column("Saldo Atualizado", width=160, anchor="center")

        tag_cores_treeview(tree)
        tree.tag_configure("positivo", foreground=NEON_GREEN, background=BG_CARD)
        tree.tag_configure("negativo", foreground=NEON_RED,   background=BG_CARD)

        sb = ttk.Scrollbar(popup, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill="y")
        tree.pack(fill="both", expand=True, padx=15, pady=(10, 15))

        for idx, mov in enumerate(reversed(historico)):
            d   = datetime.strptime(mov["data"], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")
            tag = "positivo" if mov["saldo_apos"] >= 0 else "negativo"
            tree.insert("", "end",
                values=(d, mov["descricao"], f"${mov['saldo_apos']:,.2f}"),
                tags=(tag,),
            )