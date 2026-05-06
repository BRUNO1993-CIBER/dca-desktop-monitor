# ============================================================
#  JanelaDistribuicao — Aba de Distribuição e P&L do Portfolio
# ============================================================
#  Gerencia a visualização analítica do portfólio.
#  Implementa arquitetura reativa com processamento off-thread
#  para cálculo de P&L, formatação dinâmica de moedas (USD/BRL)
#  e renderização de componentes visuais (Treeview, DonutChart).
# ============================================================

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

# Constantes de design e métricas de risco/diversificação
_CORES_ATIVOS   = ["#f7931a", "#58a6ff", "#00ff88", "#e3b341", "#a371f7", "#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4", "#ff9ff3"]
_DIVERSIFICACAO = [(7, "🟢 Excelente", NEON_GREEN), (4, "🟡 Moderada", YELLOW), (2, "🟠 Baixa", BTC_ORANGE), (0, "🔴 Mínima", NEON_RED)]


class JanelaDistribuicao(ttk.Frame):
    def __init__(self, parent, data_manager, price_manager, analysis_engine, on_change: Optional[Callable] = None):
        super().__init__(parent)
        # Injeção de dependências
        self._data_manager   = data_manager
        self._price_manager  = price_manager
        self._engine         = analysis_engine

        # Controle de estado de UI e Internacionalização/Moeda
        self._usdt_pl_brl     = {}
        self.display_currency = "USD"
        self.brl_toggle_var   = tk.BooleanVar(value=False)

        self._build_ui()

    # ----------------------------------------------------------
    #  UI BUILDER
    # ----------------------------------------------------------
    def _build_ui(self):
        """Constrói a árvore de componentes visuais (DOM-like) da janela."""
        self.pack(fill="both", expand=True, padx=10, pady=10)

        # ── Toolbar: Controles e Telemetria ───────────────────
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(10, 10))

        # Esquerda: Controles de Exibição
        ttk.Checkbutton(toolbar, text="Exibir em BRL", variable=self.brl_toggle_var, command=self.toggle_currency).pack(side=tk.LEFT, padx=5)

        # Direita: Agrupamento Lógico de Telemetria (Sync, Status, Hora, Countdown)
        sync_frame = ttk.Frame(toolbar)
        sync_frame.pack(side=tk.RIGHT, padx=(0, 5))

        # 1. Badge Live Sync
        badge_frame = tk.Frame(sync_frame, bg=BG_CARD, highlightbackground=BORDER, highlightthickness=1, padx=8, pady=2)
        badge_frame.pack(side=tk.LEFT, padx=(0, 10))
        tk.Label(badge_frame, text="🟢", font=("Segoe UI", 9), bg=BG_CARD, fg=NEON_GREEN).pack(side=tk.LEFT, padx=(0, 4))
        tk.Label(badge_frame, text="Live Sync", font=("Segoe UI", 9, "bold"), bg=BG_CARD, fg=TEXT_PRIMARY).pack(side=tk.LEFT)
        
        # 2. Label de Feedback Efêmero (Calculando / Concluído / Erro)
        self.lbl_status = ttk.Label(sync_frame, text="", font=("Segoe UI", 9), foreground=CYAN)
        self.lbl_status.pack(side=tk.LEFT, padx=(0, 8))

        # 3. Histórico: Última Atualização
        self.lbl_ultima_atualizacao = ttk.Label(sync_frame, text="", font=("Segoe UI", 9), foreground=TEXT_SECONDARY)
        self.lbl_ultima_atualizacao.pack(side=tk.LEFT)

        # 4. Countdown para a próxima sincronização
        self.lbl_countdown = ttk.Label(sync_frame, text="", font=("Segoe UI", 9), foreground=TEXT_SECONDARY)
        self.lbl_countdown.pack(side=tk.LEFT, padx=(4, 0))

        # ── Dashboard: Cards de Resumo ────────────────────────
        cards_frame = ttk.Frame(self)
        cards_frame.pack(fill="x", pady=(0, 6))

        self._lbl_patrimonio = self._criar_card(cards_frame, "💼 Patrimônio Total",        BTC_ORANGE)
        self._lbl_custo      = self._criar_card(cards_frame, "📥 Custo Total (Investido)", CYAN)
        self._lbl_pl         = self._criar_card(cards_frame, "📈 P/L Geral",               NEON_GREEN)
        self._lbl_div        = self._criar_card(cards_frame, "🎯 Diversificação",          TEXT_SECONDARY)

        # ── Corpo Principal: Gráficos e Tabelas ───────────────
        main_body = ttk.Frame(self)
        main_body.pack(fill="both", expand=True)
        main_body.columnconfigure(0, weight=1)
        main_body.rowconfigure(0, weight=2)
        main_body.rowconfigure(1, weight=3)

        # Componente de Gráfico de Rosca (Donut)
        donut_frame = ttk.LabelFrame(main_body, text=" Gráfico de Distribuição e Alocação ", padding=10)
        donut_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

        self.donut_chart = DonutChart(donut_frame)
        self.donut_chart.pack(fill="both", expand=True)

        # Contêiner da Análise Datagrid
        detalhe_frame = ttk.LabelFrame(main_body, text=" Análise Detalhada de P&L ", padding=10)
        detalhe_frame.grid(row=1, column=0, sticky="nsew")

        # Header flutuante de totais computados
        totais_frame = tk.Frame(detalhe_frame, bg=BG_INPUT, highlightbackground=BTC_ORANGE, highlightthickness=1)
        totais_frame.pack(fill="x", pady=(0, 8))

        tk.Label(totais_frame, text="TOTAL GERAL", font=("Segoe UI", 9, "bold"),
                 bg=BG_INPUT, fg=BTC_ORANGE).pack(side=tk.LEFT, padx=(12, 16), pady=6)

        # Função geradora de colunas do header de totais
        def _col(titulo, subtitulo, cor):
            f = tk.Frame(totais_frame, bg=BG_INPUT)
            f.pack(side=tk.LEFT, expand=True, fill="x", padx=8, pady=4)
            tk.Label(f, text=titulo,    font=("Segoe UI", 7, "bold"), bg=BG_INPUT, fg=TEXT_MUTED).pack()
            tk.Label(f, text=subtitulo, font=("Segoe UI", 7),         bg=BG_INPUT, fg=TEXT_MUTED).pack()
            lbl = tk.Label(f, text="--", font=("Segoe UI", 10, "bold"), bg=BG_INPUT, fg=cor)
            lbl.pack()
            return lbl

        self._tot_custo  = _col("CUSTO TOTAL",       "soma do investido",         TEXT_SECONDARY)
        self._tot_valor  = _col("VALOR ATUAL",       "preço mercado × posição",   BTC_ORANGE)
        self._tot_pl_nr  = _col("P/L NÃO REALIZADO", "ganho em aberto",           NEON_GREEN)
        self._tot_pl_r   = _col("P/L REALIZADO",     "lucro já sacado/vendido",   NEON_GREEN)
        self._tot_pl     = _col("P/L TOTAL",         "realizado + não realizado", NEON_GREEN)
        self._tot_pct    = _col("GANHO %",           "P/L NR ÷ custo total",      NEON_GREEN)
        self._tot_melhor = _col("🏆 MELHOR ATIVO",    "maior P/L total",           NEON_GREEN)
        self._tot_pior   = _col("💀 PIOR ATIVO",      "menor P/L total",           NEON_RED)

        # Datagrid (Treeview) de posições
        cols_det = ("Ativo", "Posição", "Preço Médio", "Preço Mercado", "Custo Posição",
                    "Valor Atual", "P/L N. Realizado", "P/L Realizado", "P/L Total", "Ganho %")
        self._det_tree = ttk.Treeview(detalhe_frame, columns=cols_det, show="headings", selectmode="browse")
        
        for col in cols_det:
            self._det_tree.heading(col, text=col)
            self._det_tree.column(col, anchor="center", width=110)

        # Applica formatação baseada em tags para o grid
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

    # ----------------------------------------------------------
    #  HELPERS E FORMATADORES
    # ----------------------------------------------------------
    def _criar_card(self, parent, titulo, cor):
        """Fábrica de cards para o dashboard superior."""
        frame = tk.Frame(parent, bg=BG_CARD, highlightbackground=BORDER, highlightthickness=1)
        frame.pack(side=tk.LEFT, fill="x", expand=True, padx=5, pady=2)
        tk.Label(frame, text=titulo, font=("Segoe UI", 9, "bold"), bg=BG_CARD, fg=TEXT_SECONDARY).pack(fill="x", pady=(8, 2))
        lbl = tk.Label(frame, text="--", font=("Segoe UI", 13, "bold"), bg=BG_CARD, fg=cor)
        lbl.pack(fill="x", pady=(0, 8))
        return lbl

    def _fmt_val(self, val):
        """Formatador de moedas fiduciárias dinâmico (Grandes Montantes)."""
        if self.display_currency == "BRL":
            taxa = self._price_manager.preco_brl
            if taxa and taxa > 0:
                return f"R${val * taxa:,.2f}"
        return f"${val:,.2f}"

    def _fmt_prc(self, val):
        """Formatador de precisão para cotações (Micro montantes)."""
        if self.display_currency == "BRL":
            taxa = self._price_manager.preco_brl
            if taxa and taxa > 0:
                return f"R${val * taxa:,.4f}"
        return f"${val:,.4f}"

    def _resetar_barra_totais(self):
        """Limpa os valores do header de totais."""
        for lbl in (self._tot_custo, self._tot_valor, self._tot_pl_nr,
                    self._tot_pl_r, self._tot_pl, self._tot_pct,
                    self._tot_melhor, self._tot_pior):
            lbl.config(text="--")

    # ----------------------------------------------------------
    #  EVENT HANDLERS
    # ----------------------------------------------------------
    def toggle_currency(self):
        """Alterna a flag de conversão cambial na camada de renderização."""
        self.display_currency = "BRL" if self.brl_toggle_var.get() else "USD"
        taxa = self._price_manager.preco_brl
        
        # Fallback caso não haja cache válido da taxa cambial
        if self.display_currency == "BRL" and (taxa is None or taxa <= 0):
            messagebox.showwarning("Aviso de Sistema", "Cotação do BRL indisponível. Revertendo para USD.")
            self.display_currency = "USD"
            self.brl_toggle_var.set(False)
            
        self.atualizar()

    # ----------------------------------------------------------
    #  WORKERS DE ATUALIZAÇÃO (ASYNC PIPELINE)
    # ----------------------------------------------------------
    def atualizar(self):
        """Entrypoint para o ciclo de atualização de dados. Despacha thread secundária."""
        self.set_status("🔄 Calculando P&L...", CYAN)
        threading.Thread(target=self._worker_atualizar, daemon=True).start()

    def _worker_atualizar(self):
        """Rotina off-thread para delegação de cálculos intensivos ao AnalysisEngine."""
        try:
            ops = self._data_manager.carregar_operacoes()
            if not ops:
                self.after(0, self._ui_vazia)
                return

            # Pipeline de processamento analítico
            portfolio = self._engine.calcular_portfolio(ops, self._price_manager.precos_cache)
            usdt_pl   = self._engine.calcular_pl_usdt_brl(ops, self._price_manager.preco_brl)
            dist      = self._engine.calcular_distribuicao_portfolio(ops, self._price_manager.precos_cache)
            
            # Delegação do payload formatado de volta para a Main Thread
            self.after(0, lambda: self._atualizar_ui(portfolio, usdt_pl, dist))
            
        except Exception as e:
            self.after(0, lambda: self.set_status("❌ Falha no processamento", NEON_RED))
            self.after(0, lambda: messagebox.showerror("Exceção do Engine", str(e)))

    # ----------------------------------------------------------
    #  RENDERIZAÇÃO CONDICIONAL DA UI
    # ----------------------------------------------------------
    def _ui_vazia(self):
        """Rotina de expurgo de dados visuais quando o modelo está vazio."""
        for row in self._det_tree.get_children():
            self._det_tree.delete(row)
            
        agora = datetime.now().strftime("%H:%M:%S")
        self.lbl_ultima_atualizacao.config(text=f"Última atualização: {agora}", foreground=TEXT_SECONDARY)
        self.set_status("", TEXT_SECONDARY)
        
        for lbl in (self._lbl_patrimonio, self._lbl_custo, self._lbl_pl, self._lbl_div):
            lbl.config(text="--", fg=TEXT_SECONDARY)
            
        self._resetar_barra_totais()
        self._det_tree.insert("", "end", values=("Nenhuma operação registrada.", *[""] * 9))
        self.donut_chart.limpar()

    def _atualizar_ui(self, portfolio, usdt_pl, dist):
        """Rotina de repopulação do DOM com o payload computado."""
        for row in self._det_tree.get_children():
            self._det_tree.delete(row)
            
        # Timestamp de persistência de status
        agora = datetime.now().strftime("%H:%M:%S")
        self.lbl_ultima_atualizacao.config(text=f"Última atualização: {agora}", foreground=TEXT_SECONDARY)
        
        # Feedback visual efêmero do processamento
        self.set_status("✅ Cálculo concluído", NEON_GREEN)
        self.after(2000, lambda: self.set_status("", TEXT_SECONDARY))
        
        self._usdt_pl_brl = usdt_pl

        # ── 1. Popula Dashboard ───────────────────────────────
        if "totais" in portfolio:
            totais   = portfolio["totais"]
            v_atual  = totais["valor_atual"]
            i_liq    = totais["investido_liquido"]
            pl_geral = totais["realizado"] + totais["nao_realizado"]

            self._lbl_patrimonio.config(text=self._fmt_val(v_atual))
            self._lbl_custo.config(text=self._fmt_val(i_liq))
            self._lbl_pl.config(text=self._fmt_val(pl_geral), fg=NEON_GREEN if pl_geral >= 0 else NEON_RED)

        # ── 2. Popula Componente de Distribuição ──────────────
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

        # ── 3. Popula Grid de Detalhes ────────────────────────
        moedas_dados = {m: d for m, d in portfolio.items() if m != "totais"}
        ord_port     = sorted(moedas_dados.items(), key=lambda item: item[1].get("valor_atual_posicao", 0), reverse=True)

        tot_custo = tot_val = tot_pl_nr = tot_pl_r = 0

        for idx, (moeda, dados) in enumerate(ord_port):
            self._inserir_detalhe(moeda, dados, idx)
            tot_custo += dados.get("custo_posicao_final", 0)
            tot_val   += dados.get("valor_atual_posicao", 0)
            tot_pl_nr += dados.get("lucro_nao_realizado", 0)
            tot_pl_r  += dados.get("lucro_realizado", 0)

        # ── 4. Atualiza Agregadores do Datagrid ───────────────
        tot_pl  = tot_pl_nr + tot_pl_r
        pct_tot = (tot_pl_nr / tot_custo * 100) if tot_custo > 0.000001 else 0
        cor_pl  = NEON_GREEN if tot_pl >= 0 else NEON_RED

        self._tot_custo.config(text=self._fmt_val(tot_custo))
        self._tot_valor.config(text=self._fmt_val(tot_val))
        self._tot_pl_nr.config(text=self._fmt_val(tot_pl_nr), fg=NEON_GREEN if tot_pl_nr >= 0 else NEON_RED)
        self._tot_pl_r.config(text=self._fmt_val(tot_pl_r),   fg=NEON_GREEN if tot_pl_r  >= 0 else NEON_RED)
        self._tot_pl.config(text=self._fmt_val(tot_pl),       fg=cor_pl)
        self._tot_pct.config(text=f"{pct_tot:+.2f}%",         fg=cor_pl)

        # Cálculo de outliers (Melhor/Pior performance)
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

            self._tot_melhor.config(text=f"{melhor[0]}  {self._fmt_val(m_pl)}  ({m_pct:+.1f}%)")
            self._tot_pior.config(text=f"{pior[0]}  {self._fmt_val(p_pl)}  ({p_pct:+.1f}%)")
        else:
            self._tot_melhor.config(text="--")
            self._tot_pior.config(text="--")

    # ----------------------------------------------------------
    #  INSERÇÃO NO DATAGRID
    # ----------------------------------------------------------
    def _inserir_detalhe(self, moeda, dados, idx):
        """Monta o registro (row) para ser inserido no Datagrid."""
        qtd     = dados.get("quantidade_final", 0)
        pmc     = dados.get("pmc_final", 0)
        custo   = dados.get("custo_posicao_final", 0)
        p_mkt   = dados.get("preco_de_mercado", 0)
        v_atual = dados.get("valor_atual_posicao", 0)
        pl_nr   = dados.get("lucro_nao_realizado", 0)
        pl_r    = dados.get("lucro_realizado", 0)
        pl_tot  = dados.get("lucro_total", 0)
        
        str_pct = f"{(pl_nr / custo * 100):+.2f}%" if custo > 0.000001 else "0.00%"
        par     = idx % 2 == 0 # Controle de zebrado do grid

        # Tratamento isolado para representação fiduciária do caixa (USDT)
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

    # ----------------------------------------------------------
    #  MODIFICADORES DE ESTADO DA UI
    # ----------------------------------------------------------
    def set_countdown(self, segundos: int) -> None:
        """Sincroniza o cronômetro do worker principal com a UI."""
        self.lbl_countdown.config(text=f"| próxima em {segundos}s" if segundos > 0 else "")

    def set_status(self, mensagem: str, cor: str = TEXT_SECONDARY) -> None:
        """Altera a flag de status principal da interface para refletir o core loop."""
        self.lbl_status.config(text=mensagem, foreground=cor)