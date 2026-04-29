import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable
from datetime import datetime
import logging
import math
import threading

from tema_cripto import (
    BG_DEEP, BG_CARD, BG_INPUT, BTC_ORANGE, NEON_GREEN, NEON_RED, CYAN, YELLOW,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, BORDER, tag_cores_treeview,
)

logger = logging.getLogger(__name__)

_CORES_ATIVOS = ["#f7931a", "#58a6ff", "#00ff88", "#e3b341", "#a371f7", "#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4", "#ff9ff3"]
_DIVERSIFICACAO = [(7, "🟢 Excelente", NEON_GREEN), (4, "🟡 Moderada", YELLOW), (2, "🟠 Baixa", BTC_ORANGE), (0, "🔴 Mínima", NEON_RED)]

class JanelaDistribuicao(ttk.Frame):
    def __init__(self, parent, data_manager, price_manager, analysis_engine, on_change: Optional[Callable] = None):
        super().__init__(parent)
        self._data_manager = data_manager
        self._price_manager = price_manager
        self._engine = analysis_engine
        self._cor_map = {}
        self._donut_dados = []
        self._usdt_pl_brl = {}
        self.display_currency = "USD"
        self.brl_toggle_var = tk.BooleanVar(value=False)
        self._build_ui()

    def _build_ui(self):
        self.pack(fill="both", expand=True, padx=10, pady=10)
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(0, 10))

        ttk.Button(toolbar, text="🔄 Atualizar Dashboard", command=self.atualizar, cursor="hand2").pack(side=tk.LEFT)
        ttk.Checkbutton(toolbar, text="Exibir em BRL", variable=self.brl_toggle_var, command=self.toggle_currency).pack(side=tk.LEFT, padx=15)

        self.lbl_ultima_atualizacao = ttk.Label(toolbar, text="", font=("Segoe UI", 9), foreground=TEXT_SECONDARY)
        self.lbl_ultima_atualizacao.pack(side=tk.RIGHT)

        cards_frame = ttk.Frame(self)
        cards_frame.pack(fill="x", pady=(0, 10))

        self._lbl_patrimonio = self._criar_card(cards_frame, "💼 Patrimônio Total", BTC_ORANGE)
        self._lbl_custo = self._criar_card(cards_frame, "📥 Custo Total (Investido)", CYAN)
        self._lbl_pl = self._criar_card(cards_frame, "📈 P/L Geral", NEON_GREEN)
        self._lbl_div = self._criar_card(cards_frame, "🎯 Diversificação", TEXT_SECONDARY)

        main_body = ttk.Frame(self)
        main_body.pack(fill="both", expand=True)
        main_body.columnconfigure(0, weight=2)
        main_body.columnconfigure(1, weight=1)
        main_body.rowconfigure(0, weight=2)
        main_body.rowconfigure(1, weight=3)

        donut_frame = ttk.LabelFrame(main_body, text=" Gráfico de Distribuição ", padding=10)
        donut_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=(0, 10))
        self._canvas = tk.Canvas(donut_frame, bg=BG_CARD, highlightthickness=0)
        self._canvas.pack(fill="both", expand=True)
        self._canvas.bind("<Configure>", lambda e: self._agendar_donut())

        aloc_frame = ttk.LabelFrame(main_body, text=" Resumo de Alocação ", padding=10)
        aloc_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=(0, 10))

        cols_aloc = ("Ativo", "Alocação (%)", "Quantidade")
        self._aloc_tree = ttk.Treeview(aloc_frame, columns=cols_aloc, show="headings", selectmode="browse")
        widths_aloc = {"Ativo": 70, "Alocação (%)": 90, "Quantidade": 100}
        for col in cols_aloc:
            self._aloc_tree.heading(col, text=col)
            self._aloc_tree.column(col, width=widths_aloc[col], anchor="center")

        tag_cores_treeview(self._aloc_tree)
        sb_aloc = ttk.Scrollbar(aloc_frame, orient="vertical", command=self._aloc_tree.yview)
        self._aloc_tree.configure(yscrollcommand=sb_aloc.set)
        sb_aloc.pack(side=tk.RIGHT, fill="y")
        self._aloc_tree.pack(fill="both", expand=True)

        detalhe_frame = ttk.LabelFrame(main_body, text=" Análise Detalhada de P&L ", padding=10)
        detalhe_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")

        cols_det = ("Ativo", "Posição", "Preço Médio", "Preço Mercado", "Custo Posição", "Valor Atual", "P/L N. Realizado", "P/L Realizado", "P/L Total", "Ganho %")
        self._det_tree = ttk.Treeview(detalhe_frame, columns=cols_det, show="headings", selectmode="browse")
        for col in cols_det:
            self._det_tree.heading(col, text=col)
            self._det_tree.column(col, anchor="center", width=110)

        tag_cores_treeview(self._det_tree)
        self._det_tree.tag_configure("lucro", foreground=NEON_GREEN, background=BG_CARD, font=("Segoe UI", 10, "bold"))
        self._det_tree.tag_configure("prejuizo", foreground=NEON_RED, background=BG_CARD, font=("Segoe UI", 10, "bold"))
        self._det_tree.tag_configure("lucro_alt", foreground=NEON_GREEN, background="#12171e", font=("Segoe UI", 10, "bold"))
        self._det_tree.tag_configure("prejuizo_alt", foreground=NEON_RED, background="#12171e", font=("Segoe UI", 10, "bold"))
        self._det_tree.tag_configure("linha_total", font=("Segoe UI", 11, "bold"), background=BG_INPUT, foreground=BTC_ORANGE)

        sb_det = ttk.Scrollbar(detalhe_frame, orient="vertical", command=self._det_tree.yview)
        self._det_tree.configure(yscrollcommand=sb_det.set)
        sb_det.pack(side=tk.RIGHT, fill="y")
        self._det_tree.pack(fill="both", expand=True)

    def _criar_card(self, parent, titulo, cor):
        frame = tk.Frame(parent, bg=BG_CARD, highlightbackground=BORDER, highlightthickness=1)
        frame.pack(side=tk.LEFT, fill="x", expand=True, padx=5, pady=2)
        tk.Label(frame, text=titulo, font=("Segoe UI", 9, "bold"), bg=BG_CARD, fg=TEXT_SECONDARY).pack(fill="x", pady=(8, 2))
        lbl = tk.Label(frame, text="--", font=("Segoe UI", 13, "bold"), bg=BG_CARD, fg=cor)
        lbl.pack(fill="x", pady=(0, 8))
        return lbl

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

    def _fmt_prc(self, val):
        if self.display_currency == "BRL":
            taxa = self._price_manager.preco_brl
            if taxa and taxa > 0:
                return f"R${val * taxa:,.4f}"
        return f"${val:,.4f}"

    def atualizar(self):
        self.lbl_ultima_atualizacao.config(text="🔄 Calculando...", foreground=CYAN)
        for t in (self._aloc_tree, self._det_tree):
            for row in t.get_children():
                t.delete(row)
        self._canvas.delete("all")
        threading.Thread(target=self._worker_atualizar, daemon=True).start()

    def _worker_atualizar(self):
        try:
            ops = self._data_manager.carregar_operacoes()
            if not ops:
                self.after(0, self._ui_vazia)
                return

            portfolio = self._engine.calcular_portfolio(ops, self._price_manager.precos_cache)
            usdt_pl = self._engine.calcular_pl_usdt_brl(ops, self._price_manager.preco_brl)
            dist = self._engine.calcular_distribuicao_portfolio(ops, self._price_manager.precos_cache)
            self.after(0, lambda: self._atualizar_ui(portfolio, usdt_pl, dist))
        except Exception as e:
            self.after(0, lambda: self.lbl_ultima_atualizacao.config(text="Erro", foreground=NEON_RED))
            self.after(0, lambda: messagebox.showerror("Erro", str(e)))

    def _ui_vazia(self):
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.lbl_ultima_atualizacao.config(text=f"Última atualização: {agora}", foreground=TEXT_SECONDARY)
        for lbl in (self._lbl_patrimonio, self._lbl_custo, self._lbl_pl, self._lbl_div):
            lbl.config(text="--", fg=TEXT_SECONDARY)
        self._det_tree.insert("", "end", values=("Nenhuma operação registrada.", *[""] * 9))

    def _atualizar_ui(self, portfolio, usdt_pl, dist):
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.lbl_ultima_atualizacao.config(text=f"Atualizado: {agora}", foreground=TEXT_SECONDARY)
        self._usdt_pl_brl = usdt_pl

        if "totais" in portfolio:
            totais = portfolio["totais"]
            v_atual = totais["valor_atual"]
            i_liq = totais["investido_liquido"]
            pl_geral = totais["realizado"] + totais["nao_realizado"]
            
            self._lbl_patrimonio.config(text=self._fmt_val(v_atual))
            self._lbl_custo.config(text=self._fmt_val(i_liq))
            self._lbl_pl.config(text=self._fmt_val(pl_geral), fg=NEON_GREEN if pl_geral >= 0 else NEON_RED)

        distribuicao = dist.get("distribuicao", {})
        if distribuicao:
            n_ativos = len(distribuicao)
            lbl_txt, cor_txt = next((lb, c) for minv, lb, c in _DIVERSIFICACAO if n_ativos >= minv)
            self._lbl_div.config(text=lbl_txt, fg=cor_txt)
            
            ord_dist = sorted(distribuicao.items(), key=lambda x: x[1]["percentual"], reverse=True)
            self._donut_dados = ord_dist
            self._cor_map = {m: _CORES_ATIVOS[i % len(_CORES_ATIVOS)] for i, (m, _) in enumerate(ord_dist)}
            
            for idx, (moeda, d) in enumerate(ord_dist):
                qtd_fmt = f"{d['quantidade']:.2f}" if moeda == "USDT" else f"{d['quantidade']:.6f}"
                tag = "par" if idx % 2 == 0 else "impar"
                self._aloc_tree.insert("", "end", values=(moeda, f"{d['percentual']:.2f}%", qtd_fmt), tags=(tag,))
            
            self._agendar_donut()
        else:
            self._lbl_div.config(text="--", fg=TEXT_SECONDARY)
            self._donut_dados = []

        moedas_dados = {m: d for m, d in portfolio.items() if m != "totais"}
        ord_port = sorted(moedas_dados.items(), key=lambda item: item[1].get("valor_atual_posicao", 0), reverse=True)

        tot_custo = tot_val = tot_pl_nr = tot_pl_r = 0

        for idx, (moeda, dados) in enumerate(ord_port):
            self._inserir_detalhe(moeda, dados, idx)
            tot_custo += dados.get("custo_posicao_final", 0)
            tot_val += dados.get("valor_atual_posicao", 0)
            tot_pl_nr += dados.get("lucro_nao_realizado", 0)
            tot_pl_r += dados.get("lucro_realizado", 0)

        tot_pl = tot_pl_nr + tot_pl_r
        pct_tot = (tot_pl_nr / tot_custo * 100) if tot_custo > 0.000001 else 0

        self._det_tree.insert("", "end", values=(
            "📊 TOTAL GERAL", "", "", "", self._fmt_val(tot_custo), self._fmt_val(tot_val),
            self._fmt_val(tot_pl_nr), self._fmt_val(tot_pl_r), self._fmt_val(tot_pl), f"{pct_tot:+.2f}%"
        ), tags=("linha_total",))

    def _inserir_detalhe(self, moeda, dados, idx):
        qtd, pmc, custo = dados.get("quantidade_final", 0), dados.get("pmc_final", 0), dados.get("custo_posicao_final", 0)
        p_mkt, v_atual = dados.get("preco_de_mercado", 0), dados.get("valor_atual_posicao", 0)
        pl_nr, pl_r, pl_tot = dados.get("lucro_nao_realizado", 0), dados.get("lucro_realizado", 0), dados.get("lucro_total", 0)
        str_pct = f"{(pl_nr / custo * 100):+.2f}%" if custo > 0.000001 else "0.00%"
        par = idx % 2 == 0

        if moeda == "USDT (Caixa)":
            taxa = self._price_manager.preco_brl or 1.0
            if self.display_currency == "BRL":
                v_at_f, p_mkt_f = f"R${qtd * taxa:,.2f}", f"R${taxa:,.4f}"
                pl = self._usdt_pl_brl
                if pl and pl.get("pmc_brl", 0) > 0:
                    pmc_f, custo_f = f"R${pl['pmc_brl']:,.4f}", f"R${pl['custo_posicao_brl']:,.2f}"
                    pl_nr_f, pl_r_f, pl_tot_f = f"R${pl['lucro_nao_realizado_brl']:+,.2f}", f"R${pl['lucro_realizado_brl']:+,.2f}", f"R${pl['lucro_total_brl']:+,.2f}"
                    pct_f = f"{(pl['lucro_nao_realizado_brl'] / pl['custo_posicao_brl'] * 100):+.2f}%" if pl["custo_posicao_brl"] > 0 else "0.00%"
                    pos = pl["lucro_total_brl"] >= 0
                else:
                    pmc_f = custo_f = pl_nr_f = pl_r_f = pl_tot_f = "N/A"
                    pct_f, pos = "0.00%", True
                valores = (moeda, f"{qtd:,.2f} USDT", pmc_f, p_mkt_f, custo_f, v_at_f, pl_nr_f, pl_r_f, pl_tot_f, pct_f)
            else:
                valores = (moeda, f"{qtd:,.2f} USDT", "N/A", self._fmt_prc(1.0), "N/A", self._fmt_val(v_atual), "N/A", "N/A", "N/A", "0.00%")
                pos = True
            tag = ("lucro" if pos else "prejuizo") if par else ("lucro_alt" if pos else "prejuizo_alt")
        else:
            valores = (moeda, f"{qtd:,.8f}", self._fmt_prc(pmc), self._fmt_prc(p_mkt), self._fmt_val(custo), self._fmt_val(v_atual), self._fmt_val(pl_nr), self._fmt_val(pl_r), self._fmt_val(pl_tot), str_pct)
            pos = pl_tot >= 0
            tag = ("lucro" if pos else "prejuizo") if par else ("lucro_alt" if pos else "prejuizo_alt")

        self._det_tree.insert("", "end", values=valores, tags=(tag,))

    def _agendar_donut(self):
        self.after(100, self._desenhar_donut)

    def _desenhar_donut(self):
        self._canvas.delete("all")
        if not self._donut_dados: return
        w, h = self._canvas.winfo_width(), self._canvas.winfo_height()
        if w < 50 or h < 50: return
        cx, cy, raio = w // 2, h // 2, min(w // 2, h // 2) - 2
        furo, inicio = int(raio * 0.55), -90.0

        for moeda, d in self._donut_dados:
            grau, cor = (d["percentual"] / 100) * 360, self._cor_map.get(moeda, TEXT_MUTED)
            self._canvas.create_arc(cx - raio, cy - raio, cx + raio, cy + raio, start=inicio, extent=grau, fill=cor, outline=BG_CARD, width=2)
            if d["percentual"] >= 3.0:
                ang_rad, raio_txt = math.radians(inicio + grau / 2), furo + (raio - furo) / 2
                self._canvas.create_text(cx + raio_txt * math.cos(ang_rad), cy - raio_txt * math.sin(ang_rad), text=moeda, font=("Segoe UI", 9, "bold"), fill=BG_DEEP)
            inicio += grau

        self._canvas.create_oval(cx - furo, cy - furo, cx + furo, cy + furo, fill=BG_CARD, outline=BG_CARD)
        self._canvas.create_text(cx, cy - 10, text=str(len(self._donut_dados)), font=("Segoe UI", 18, "bold"), fill=BTC_ORANGE)
        self._canvas.create_text(cx, cy + 12, text="ativos", font=("Segoe UI", 10), fill=TEXT_SECONDARY)

        leg_y = 15
        for moeda, d in self._donut_dados:
            self._canvas.create_rectangle(15, leg_y, 25, leg_y + 10, fill=self._cor_map.get(moeda, TEXT_MUTED), outline="")
            self._canvas.create_text(33, leg_y + 5, text=f"{moeda} {d['percentual']:.1f}%", font=("Segoe UI", 9, "bold"), fill=TEXT_PRIMARY, anchor="w")
            leg_y += 18
            if leg_y > h - 25: break