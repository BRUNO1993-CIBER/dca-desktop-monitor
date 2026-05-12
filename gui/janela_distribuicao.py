import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable
from datetime import datetime
import threading

from config.donut_chart import DonutChart
from config.tema_cripto import (
    BG_DEEP, BG_CARD, BG_INPUT, BTC_ORANGE, NEON_GREEN, NEON_RED, CYAN, YELLOW,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, BORDER, tag_cores_treeview,
)

_CORES_ATIVOS   = ["#f7931a", "#58a6ff", "#00ff88", "#e3b341", "#a371f7", "#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4", "#ff9ff3"]
_DIVERSIFICACAO = [(7, "🟢 Excelente", NEON_GREEN), (4, "🟡 Moderada", YELLOW), (2, "🟠 Baixa", BTC_ORANGE), (0, "🔴 Mínima", NEON_RED)]


class JanelaDistribuicao(ttk.Frame):
    def __init__(self, parent, data_manager, price_manager, analysis_engine, on_change: Optional[Callable] = None):
        super().__init__(parent)
        self._data_manager   = data_manager
        self._price_manager  = price_manager
        self._engine         = analysis_engine

        self._usdt_pl_brl     = {}
        self.display_currency = "USD"
        self.brl_toggle_var   = tk.BooleanVar(value=False)

        self._build_ui()

    def _build_ui(self):
        self.pack(fill="both", expand=True, padx=10, pady=10)

        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(10, 10))

        ttk.Checkbutton(toolbar, text="Exibir em BRL", variable=self.brl_toggle_var, command=self.toggle_currency).pack(side=tk.LEFT, padx=5)

        sync_frame = ttk.Frame(toolbar)
        sync_frame.pack(side=tk.RIGHT, padx=(0, 5))

        badge_frame = tk.Frame(sync_frame, bg=BG_CARD, highlightbackground=BORDER, highlightthickness=1, padx=8, pady=2)
        badge_frame.pack(side=tk.LEFT, padx=(0, 10))
        tk.Label(badge_frame, text="🟢", font=("Segoe UI", 9), bg=BG_CARD, fg=NEON_GREEN).pack(side=tk.LEFT, padx=(0, 4))
        tk.Label(badge_frame, text="Sincronizado c/ Binance", font=("Segoe UI", 9, "bold"), bg=BG_CARD, fg=TEXT_PRIMARY).pack(side=tk.LEFT)

        self.lbl_status = ttk.Label(sync_frame, text="", font=("Segoe UI", 9), foreground=CYAN)
        self.lbl_status.pack(side=tk.LEFT, padx=(0, 8))

        self.lbl_ultima_atualizacao = ttk.Label(sync_frame, text="", font=("Segoe UI", 9), foreground=TEXT_SECONDARY)
        self.lbl_ultima_atualizacao.pack(side=tk.LEFT)

        self.lbl_countdown = ttk.Label(sync_frame, text="", font=("Segoe UI", 9), foreground=TEXT_SECONDARY)
        self.lbl_countdown.pack(side=tk.LEFT, padx=(4, 0))

        cards_outer = ttk.Frame(self)
        cards_outer.pack(fill="x", pady=(0, 6))

        for col in range(5):
            cards_outer.columnconfigure(col, weight=1)

        def _card(row, col, titulo, subtitulo, cor):
            frame = tk.Frame(cards_outer, bg=BG_CARD, highlightbackground=BORDER, highlightthickness=1)
            frame.grid(row=row, column=col, sticky="nsew", padx=5, pady=2)
            tk.Label(frame, text=titulo,    font=("Segoe UI", 9, "bold"), bg=BG_CARD, fg=TEXT_SECONDARY).pack(fill="x", pady=(8, 0))
            tk.Label(frame, text=subtitulo, font=("Segoe UI", 7),         bg=BG_CARD, fg=TEXT_MUTED).pack(fill="x")
            lbl = tk.Label(frame, text="--", font=("Segoe UI", 13, "bold"), bg=BG_CARD, fg=cor)
            lbl.pack(fill="x", pady=(2, 8))
            return lbl

        self._lbl_patrimonio = _card(0, 0, "💼 Patrimônio Total",  "preço mercado × posição",   BTC_ORANGE)
        self._lbl_custo      = _card(0, 1, "📥 Custo Total",       "soma do investido",          CYAN)
        self._lbl_pl_nr      = _card(0, 2, "📈 P/L Não Realizado", "ganho em aberto",            NEON_GREEN)
        self._lbl_pl_r       = _card(0, 3, "💰 P/L Realizado",     "lucro já sacado/vendido",    NEON_GREEN)
        self._lbl_pl         = _card(0, 4, "🏁 P/L Total",         "realizado + não realizado",  NEON_GREEN)

        self._lbl_pct        = _card(1, 0, "📊 Ganho %",           "P/L NR ÷ custo total",       NEON_GREEN)
        self._lbl_retorno    = _card(1, 1, "📉 Retorno Total %",   "P/L total ÷ custo total",    NEON_GREEN)
        self._lbl_div        = _card(1, 2, "🎯 Diversificação",    "ativos distintos",            TEXT_SECONDARY)
        self._lbl_melhor     = _card(1, 3, "🏆 Melhor Ativo",      "maior P/L total",             NEON_GREEN)
        self._lbl_pior       = _card(1, 4, "💀 Pior Ativo",        "menor P/L total",             NEON_RED)

        main_body = ttk.Frame(self)
        main_body.pack(fill="both", expand=True)
        main_body.columnconfigure(0, weight=1)
        main_body.rowconfigure(0, weight=2)
        main_body.rowconfigure(1, weight=3)

        donut_frame = ttk.LabelFrame(main_body, text=" Gráfico de Distribuição e Alocação ", padding=10)
        donut_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

        self.donut_chart = DonutChart(donut_frame)
        self.donut_chart.pack(fill="both", expand=True)

        detalhe_frame = ttk.LabelFrame(main_body, text=" Análise Detalhada de P&L ", padding=10)
        detalhe_frame.grid(row=1, column=0, sticky="nsew")

        cols_det = ("Ativo", "Posição", "Preço Médio", "Preço Mercado", "Custo Posição",
                    "Valor Atual", "P/L N. Realizado", "P/L Realizado", "P/L Total", "Ganho %")
        self._det_tree = ttk.Treeview(detalhe_frame, columns=cols_det, show="headings", selectmode="browse")

        for col in cols_det:
            self._det_tree.heading(col, text=col)
            self._det_tree.column(col, anchor="center", width=110)

        tag_cores_treeview(self._det_tree)
        self._det_tree.tag_configure("lucro",        foreground=NEON_GREEN, background=BG_CARD,   font=("Segoe UI", 10, "bold"))
        self._det_tree.tag_configure("prejuizo",     foreground=NEON_RED,   background=BG_CARD,   font=("Segoe UI", 10, "bold"))
        self._det_tree.tag_configure("lucro_alt",    foreground=NEON_GREEN, background="#12171e", font=("Segoe UI", 10, "bold"))
        self._det_tree.tag_configure("prejuizo_alt", foreground=NEON_RED,   background="#12171e", font=("Segoe UI", 10, "bold"))

        style = ttk.Style()
        style.map("Treeview", background=[('selected', '#2c5d8f')], foreground=[('selected', 'white')])

        sb_det = ttk.Scrollbar(detalhe_frame, orient="vertical", command=self._det_tree.yview)
        self._det_tree.configure(yscrollcommand=sb_det.set)
        sb_det.pack(side=tk.RIGHT, fill="y")
        self._det_tree.pack(fill="both", expand=True)

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

    def _resetar_cards(self):
        for lbl in (self._lbl_patrimonio, self._lbl_custo, self._lbl_pl_nr,
                    self._lbl_pl_r, self._lbl_pl, self._lbl_pct, self._lbl_retorno,
                    self._lbl_div, self._lbl_melhor, self._lbl_pior):
            lbl.config(text="--")

    def toggle_currency(self):
        self.display_currency = "BRL" if self.brl_toggle_var.get() else "USD"
        taxa = self._price_manager.preco_brl

        if self.display_currency == "BRL" and (taxa is None or taxa <= 0):
            messagebox.showwarning("Aviso de Sistema", "Cotação do BRL indisponível. Revertendo para USD.")
            self.display_currency = "USD"
            self.brl_toggle_var.set(False)

        self.atualizar()

    def atualizar(self):
        self.set_status("🔄 Calculando P&L...", CYAN)
        threading.Thread(target=self._worker_atualizar, daemon=True).start()

    def _worker_atualizar(self):
        try:
            ops = self._data_manager.carregar_operacoes()
            if not ops:
                self.after(0, self._ui_vazia)
                return

            portfolio = self._engine.calcular_portfolio(ops, self._price_manager.precos_cache)
            usdt_pl   = self._engine.calcular_pl_usdt_brl(ops, self._price_manager.preco_brl)
            dist      = self._engine.calcular_distribuicao_portfolio(ops, self._price_manager.precos_cache)

            self.after(0, lambda: self._atualizar_ui(portfolio, usdt_pl, dist))

        except Exception as e:
            self.after(0, lambda: self.set_status("❌ Falha no processamento", NEON_RED))
            self.after(0, lambda: messagebox.showerror("Exceção do Engine", str(e)))

    def _ui_vazia(self):
        for row in self._det_tree.get_children():
            self._det_tree.delete(row)

        agora = datetime.now().strftime("%H:%M:%S")
        self.lbl_ultima_atualizacao.config(text=f"Última atualização: {agora}", foreground=TEXT_SECONDARY)
        self.set_status("", TEXT_SECONDARY)
        self._resetar_cards()
        self._det_tree.insert("", "end", values=("Nenhuma operação registrada.", *[""] * 9))
        self.donut_chart.limpar()

    def _atualizar_ui(self, portfolio, usdt_pl, dist):
        for row in self._det_tree.get_children():
            self._det_tree.delete(row)

        agora = datetime.now().strftime("%H:%M:%S")
        self.lbl_ultima_atualizacao.config(text=f"Última atualização: {agora}", foreground=TEXT_SECONDARY)
        self.set_status("✅ Cálculo concluído", NEON_GREEN)
        self.after(2000, lambda: self.set_status("", TEXT_SECONDARY))

        self._usdt_pl_brl = usdt_pl

        distribuicao = dist.get("distribuicao", {})
        if distribuicao:
            n_ativos = len(distribuicao)
            lbl_txt, cor_txt = next((lb, c) for minv, lb, c in _DIVERSIFICACAO if n_ativos >= minv)
            self._lbl_div.config(text=lbl_txt, fg=cor_txt)

            ord_dist = sorted(distribuicao.items(), key=lambda x: x[1]["percentual"], reverse=True)
            cor_map  = {m: _CORES_ATIVOS[i % len(_CORES_ATIVOS)] for i, (m, _) in enumerate(ord_dist)}
            self.donut_chart.atualizar_dados(ord_dist, cor_map)
        else:
            self._lbl_div.config(text="--", fg=TEXT_SECONDARY)
            self.donut_chart.limpar()

        moedas_dados = {m: d for m, d in portfolio.items() if m != "totais"}
        ord_port     = sorted(moedas_dados.items(), key=lambda item: item[1].get("valor_atual_posicao", 0), reverse=True)

        tot_custo = tot_val = tot_pl_nr = tot_pl_r = 0

        for idx, (moeda, dados) in enumerate(ord_port):
            self._inserir_detalhe(moeda, dados, idx)
            tot_custo += dados.get("custo_posicao_final", 0)
            tot_val   += dados.get("valor_atual_posicao", 0)
            tot_pl_nr += dados.get("lucro_nao_realizado", 0)
            tot_pl_r  += dados.get("lucro_realizado", 0)

        tot_pl      = tot_pl_nr + tot_pl_r
        pct_nr      = (tot_pl_nr / tot_custo * 100) if tot_custo > 0.000001 else 0
        pct_total   = (tot_pl    / tot_custo * 100) if tot_custo > 0.000001 else 0
        cor_pl      = NEON_GREEN if tot_pl    >= 0 else NEON_RED
        cor_nr      = NEON_GREEN if tot_pl_nr >= 0 else NEON_RED
        cor_r       = NEON_GREEN if tot_pl_r  >= 0 else NEON_RED
        cor_retorno = NEON_GREEN if pct_total >= 0 else NEON_RED

        self._lbl_patrimonio.config(text=self._fmt_val(tot_val))
        self._lbl_custo.config(text=self._fmt_val(tot_custo))
        self._lbl_pl_nr.config(text=self._fmt_val(tot_pl_nr), fg=cor_nr)
        self._lbl_pl_r.config(text=self._fmt_val(tot_pl_r),   fg=cor_r)
        self._lbl_pl.config(text=self._fmt_val(tot_pl),       fg=cor_pl)
        self._lbl_pct.config(text=f"{pct_nr:+.2f}%",          fg=cor_nr)
        self._lbl_retorno.config(text=f"{pct_total:+.2f}%",   fg=cor_retorno)

        moedas_validas = [
            (m, d) for m, d in ord_port
            if m != "USDT (Caixa)" and d.get("lucro_total") is not None
        ]

        if moedas_validas:
            melhor = max(moedas_validas, key=lambda x: x[1].get("lucro_total", 0))
            pior   = min(moedas_validas, key=lambda x: x[1].get("lucro_total", 0))

            def _pct_ativo(d):
                c = d.get("custo_posicao_final", 0)
                return (d.get("lucro_nao_realizado", 0) / c * 100) if c > 0.000001 else 0

            m_pl  = melhor[1].get("lucro_total", 0)
            m_pct = _pct_ativo(melhor[1])
            p_pl  = pior[1].get("lucro_total", 0)
            p_pct = _pct_ativo(pior[1])

            self._lbl_melhor.config(text=f"{melhor[0]}  {self._fmt_val(m_pl)}  ({m_pct:+.1f}%)")
            self._lbl_pior.config(text=f"{pior[0]}  {self._fmt_val(p_pl)}  ({p_pct:+.1f}%)")
        else:
            self._lbl_melhor.config(text="--")
            self._lbl_pior.config(text="--")

    def _inserir_detalhe(self, moeda, dados, idx):
        qtd     = dados.get("quantidade_final", 0)
        pmc     = dados.get("pmc_final", 0)
        custo   = dados.get("custo_posicao_final", 0)
        p_mkt   = dados.get("preco_de_mercado", 0)
        v_atual = dados.get("valor_atual_posicao", 0)
        pl_nr   = dados.get("lucro_nao_realizado", 0)
        pl_r    = dados.get("lucro_realizado", 0)
        pl_tot  = dados.get("lucro_total", 0)

        str_pct = f"{(pl_nr / custo * 100):+.2f}%" if custo > 0.000001 else "0.00%"
        par     = idx % 2 == 0

        if moeda == "USDT (Caixa)":
            taxa = self._price_manager.preco_brl or 1.0
            if self.display_currency == "BRL":
                v_at_f  = f"R${qtd * taxa:,.2f}"
                p_mkt_f = f"R${taxa:,.4f}"
                pl      = self._usdt_pl_brl

                if pl and pl.get("pmc_brl", 0) > 0:
                    pmc_f    = f"R${pl['pmc_brl']:,.4f}"
                    custo_f  = f"R${pl['custo_posicao_brl']:,.2f}"
                    pl_nr_f  = f"R${pl['lucro_nao_realizado_brl']:+,.2f}"
                    pl_r_f   = f"R${pl['lucro_realizado_brl']:+,.2f}"
                    pl_tot_f = f"R${pl['lucro_total_brl']:+,.2f}"
                    pct_f    = f"{(pl['lucro_nao_realizado_brl'] / pl['custo_posicao_brl'] * 100):+.2f}%" if pl["custo_posicao_brl"] > 0 else "0.00%"
                    pos      = pl["lucro_total_brl"] >= 0
                else:
                    pmc_f = custo_f = pl_nr_f = pl_r_f = pl_tot_f = "N/A"
                    pct_f, pos = "0.00%", True

                valores = (moeda, f"{qtd:,.2f} USDT", pmc_f, p_mkt_f, custo_f, v_at_f, pl_nr_f, pl_r_f, pl_tot_f, pct_f)
            else:
                valores = (moeda, f"{qtd:,.2f} USDT", "N/A", self._fmt_prc(1.0), "N/A",
                           self._fmt_val(v_atual), "N/A", "N/A", "N/A", "0.00%")
                pos = True

            tag = ("lucro" if pos else "prejuizo") if par else ("lucro_alt" if pos else "prejuizo_alt")

        else:
            valores = (moeda, f"{qtd:,.8f}", self._fmt_prc(pmc), self._fmt_prc(p_mkt),
                       self._fmt_val(custo), self._fmt_val(v_atual),
                       self._fmt_val(pl_nr), self._fmt_val(pl_r), self._fmt_val(pl_tot), str_pct)

            pos = pl_tot >= 0
            tag = ("lucro" if pos else "prejuizo") if par else ("lucro_alt" if pos else "prejuizo_alt")

        self._det_tree.insert("", "end", values=valores, tags=(tag,))

    def set_countdown(self, segundos: int) -> None:
        self.lbl_countdown.config(text=f"| próxima em {segundos}s" if segundos > 0 else "")

    def set_status(self, mensagem: str, cor: str = TEXT_SECONDARY) -> None:
        self.lbl_status.config(text=mensagem, foreground=cor)