import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox
from typing import Any, Optional, Callable
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

_CORES_ATIVOS = [
    "#1565C0", "#AD1457", "#2E7D32", "#E65100", "#4527A0",
    "#00695C", "#F9A825", "#6A1B9A", "#0277BD", "#558B2F",
]

_DIVERSIFICACAO = [
    (7, "🟢 Bem diversificado",          "#2E7D32"),
    (4, "🟢 Moderadamente diversificado", "#388E3C"),
    (2, "🟡 Pouco diversificado",         "#F57F17"),
    (0, "🔴 Concentrado",                 "#C62828"),
]

_TAGS = {
    "titulo":    {"font": ("Consolas", 14, "bold"), "foreground": "#1A237E"},
    "subtitulo": {"font": ("Consolas", 11, "bold"), "foreground": "#1976D2"},
    "moeda":     {"font": ("Consolas", 11, "bold"), "foreground": "#4A148C"},
    "percentual":{"font": ("Consolas", 11, "bold"), "foreground": "#BF360C"},
    "valor":     {"font": ("Consolas", 11),          "foreground": "#0D47A1"},
    "total":     {"font": ("Consolas", 12, "bold"), "foreground": "#E65100"},
    "positivo":  {"font": ("Consolas", 11, "bold"), "foreground": "#2E7D32"},
    "negativo":  {"font": ("Consolas", 11, "bold"), "foreground": "#C62828"},
    "aviso":     {"font": ("Consolas", 10, "bold"), "foreground": "#E65100"},
    "erro":      {"font": ("Consolas", 10, "bold"), "foreground": "#B71C1C"},
    "dim":       {"font": ("Consolas", 10),          "foreground": "#757575"},
}

# Largura mínima e máxima em caracteres para o painel de texto
_LARGURA_MIN = 44
_LARGURA_MAX = 90


class JanelaDistribuicao(ttk.Frame):

    def __init__(self, parent, data_manager, price_manager, analysis_engine,
                 on_change: Optional[Callable] = None):
        super().__init__(parent, padding=10)
        self._data_manager  = data_manager
        self._price_manager = price_manager
        self._engine        = analysis_engine
        self._on_change     = on_change or (lambda: None)
        self._cor_map: dict[str, str] = {}
        self._resize_job: Optional[str] = None
        self._build_ui()

    # ─────────────────────────── BUILD ────────────────────────────

    def _build_ui(self) -> None:
        self._build_toolbar()

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, padx=5, pady=(5, 0))
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        self._build_text_panel(body)
        self._build_right_panel(body)

    def _build_toolbar(self) -> None:
        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=10, pady=(5, 0))

        ttk.Button(bar, text="🔄 Atualizar", command=self.atualizar,
                   style="Accent.TButton", cursor="hand2").pack(side=tk.LEFT)
        ttk.Button(bar, text="💰 Histórico USDT", command=self._popup_saldo_usdt,
                   cursor="hand2").pack(side=tk.LEFT, padx=(8, 0))

        self._saldo_label = ttk.Label(bar, text="", font=("Arial", 10, "bold"),
                                      foreground="#2E7D32")
        self._saldo_label.pack(side=tk.RIGHT)

    def _build_text_panel(self, parent) -> None:
        container = ttk.Frame(parent)
        container.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        self._text = tk.Text(
            container, wrap="word", font=("Consolas", 11),
            relief="flat", padx=20, pady=15, bg="#F8F9FA",
            cursor="arrow", state="disabled",
        )
        sb = ttk.Scrollbar(container, orient="vertical", command=self._text.yview)
        self._text.configure(yscrollcommand=sb.set)

        for tag, opts in _TAGS.items():
            self._text.tag_configure(tag, **opts)

        sb.pack(side=tk.RIGHT, fill="y")
        self._text.pack(side=tk.LEFT, fill="both", expand=True)

        # ── Redesenha ao redimensionar (debounce 200 ms) ──────────
        self._text.bind("<Configure>", self._agendar_atualizar)

    def _build_right_panel(self, parent) -> None:
        right = ttk.Frame(parent)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(0, weight=2)
        right.rowconfigure(1, weight=3)
        right.columnconfigure(0, weight=1)

        donut_frame = ttk.LabelFrame(right, text="  Alocação  ", padding=8)
        donut_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 5))

        self._canvas = tk.Canvas(donut_frame, bg="#F8F9FA", highlightthickness=0)
        self._canvas.pack(fill="both", expand=True)

        pl_frame = ttk.LabelFrame(right, text="  P&L por Ativo  ", padding=8)
        pl_frame.grid(row=1, column=0, sticky="nsew")

        cols = ("Ativo", "Médio", "Atual", "P&L %", "P&L $")
        self._pl_tree = ttk.Treeview(pl_frame, columns=cols, show="headings",
                                     height=8, selectmode="none")

        widths = {"Ativo": 52, "Médio": 78, "Atual": 78, "P&L %": 68, "P&L $": 82}
        for col in cols:
            self._pl_tree.heading(col, text=col)
            self._pl_tree.column(col, width=widths[col], anchor="center",
                                 minwidth=widths[col])

        self._pl_tree.tag_configure("ganho",  background="#E8F5E9", foreground="#1B5E20")
        self._pl_tree.tag_configure("perda",  background="#FFEBEE", foreground="#B71C1C")
        self._pl_tree.tag_configure("neutro", background="#F5F5F5", foreground="#424242")

        sb_pl = ttk.Scrollbar(pl_frame, orient="vertical", command=self._pl_tree.yview)
        self._pl_tree.configure(yscrollcommand=sb_pl.set)
        sb_pl.pack(side=tk.RIGHT, fill="y")
        self._pl_tree.pack(fill="both", expand=True)

    # ─────────────────────── RESPONSIVIDADE ───────────────────────

    def _agendar_atualizar(self, event=None) -> None:
        """Debounce: cancela o job anterior e agenda novo em 200 ms."""
        if self._resize_job:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(200, self._atualizar_se_dados)

    def _atualizar_se_dados(self) -> None:
        """Redesenha apenas se já há conteúdo renderizado."""
        if self._text.get("1.0", "end-1c").strip():
            self.atualizar()

    def _chars_por_linha(self) -> int:
        """
        Calcula quantos caracteres Consolas 11 cabem na largura atual
        do widget de texto, descontando os paddings internos.
        """
        largura_px = self._text.winfo_width()
        if largura_px < 50:          # widget ainda não renderizado
            return 52
        padding_total = 40           # padx=20 dos dois lados
        disponivel   = largura_px - padding_total
        char_px = tkfont.Font(family="Consolas", size=11).measure("M")
        if char_px == 0:
            return 52
        chars = disponivel // char_px
        return max(_LARGURA_MIN, min(_LARGURA_MAX, chars))

    # ─────────────────────── CONTEÚDO ─────────────────────────────

    def atualizar(self) -> None:
        self._escrever(self._montar_conteudo)

    def _montar_conteudo(self, w: "TextWriter") -> None:
        try:
            operacoes = self._data_manager.carregar_operacoes()
        except Exception as e:
            w.linha(f"❌ Erro ao carregar dados: {e}", "erro")
            return

        if not operacoes:
            w.centralizado("📊 Nenhuma operação registrada ainda.", "dim")
            w.linha("")
            w.centralizado("Registre operações na aba ✍️ Registrar.", "dim")
            self._limpar_paineis_direita()
            return

        saldo_info      = self._engine.calcular_saldo_usdt(operacoes)
        saldo_usdt      = saldo_info["saldo_atual"]
        resultado       = self._engine.calcular_distribuicao_portfolio(
            operacoes, self._price_manager.precos_cache
        )
        distribuicao    = resultado["distribuicao"]
        total_cripto    = resultado["total_investido"]
        total_portfolio = total_cripto + saldo_usdt
        preco_brl       = self._price_manager.preco_brl

        self._atualizar_saldo_label(saldo_usdt, preco_brl)

        # ── largura dinâmica ──────────────────────────────────────
        L = w.largura   # alias curto; TextWriter já calculou ao ser criado

        def brl(v: float) -> str:
            return f"  (≈ R$ {v * preco_brl:,.2f})" if preco_brl > 0 else ""

        w.linha("  PORTFÓLIO CRIPTO  ⤵", "titulo")
        w.linha("")

        # ── resumo financeiro ────────────────────────────────────
        w.par([("   🪙 Cripto  : ", "dim"),
               (f"${total_cripto:>12,.2f}{brl(total_cripto)}", "valor")])
        cor_s = "positivo" if saldo_usdt >= 0 else "negativo"
        w.par([("   💼 Caixa   : ", "dim"),
               (f"${saldo_usdt:>12,.2f}{brl(saldo_usdt)}", cor_s)])
        if saldo_usdt < 0:
            w.centralizado("⚠️  Saldo negativo!", "aviso")
        w.sep("─")
        w.par([("   📊 Total   : ", "dim"),
               (f"${total_portfolio:>12,.2f}{brl(total_portfolio)}", "total")])
        w.linha("")

        if not distribuicao:
            w.centralizado("Nenhuma posição em cripto.", "dim")
            self._limpar_paineis_direita()
            return

        ordenados = sorted(distribuicao.items(),
                           key=lambda x: x[1]["percentual"], reverse=True)

        self._cor_map = {
            m: _CORES_ATIVOS[i % len(_CORES_ATIVOS)]
            for i, (m, _) in enumerate(ordenados)
        }

        # ── tabela de posições ────────────────────────────────────
        # Colunas: ATIVO | % | USD | QTD
        # As duas últimas se expandem proporcionalmente ao espaço disponível.
        # Largura reservada para colunas fixas: ativo(8) + %(10) = 18 chars + margens
        col_ativo = 8
        col_pct   = 10
        restante  = max(20, L - col_ativo - col_pct - 6)   # 6 = margens/espaços
        col_usd   = restante // 2
        col_qtd   = restante - col_usd

        w.sep("─")
        w.par([
            (f"  {'ATIVO':<{col_ativo}}", "subtitulo"),
            (f"{'%':>{col_pct}}   ",      "subtitulo"),
            (f"{'USD':>{col_usd}}   ",    "subtitulo"),
            (f"{'QTD':>{col_qtd}}",       "subtitulo"),
        ])
        w.sep("─")

        for moeda, dados in ordenados:
            pct = dados["percentual"]
            val = dados["valor_atual"]
            qtd = dados["quantidade"]
            fmt_qtd = f"{qtd:>{col_qtd}.2f}" if moeda == "USDT" else f"{qtd:>{col_qtd}.6f}"

            cor_ponto = self._cor_map.get(moeda, "#333")
            tmp = f"_dot_{moeda}"
            self._text.tag_configure(tmp, foreground=cor_ponto,
                                     font=("Consolas", 13, "bold"))
            self._text.insert(tk.END, "  ● ", tmp)

            w.par([
                (f"{moeda:<{col_ativo}}", "moeda"),
                (f"{pct:>{col_pct}.2f}%   ", "percentual"),
                (f"${val:>{col_usd},.2f}   ", "valor"),
                (fmt_qtd, "dim"),
            ], _no_newline=True)
            self._text.insert(tk.END, "\n")

        w.sep("─")
        w.linha("")

        # ── barra de alocação ─────────────────────────────────────
        w.linha("  📊 ALOCAÇÃO", "subtitulo")
        w.linha("")
        max_pct    = ordenados[0][1]["percentual"]
        barra_max  = max(10, L - 20)   # chars disponíveis para a barra
        for moeda, dados in ordenados:
            pct   = dados["percentual"]
            n_bar = int((pct / max_pct) * barra_max)
            barra = "█" * n_bar
            w.par([
                (f"  {moeda:<6} ", "moeda"),
                (f"{barra:<{barra_max}} ", "valor"),
                (f"{pct:>6.2f}%", "percentual"),
            ])

        w.linha("")
        w.sep("─")

        # ── diversificação ────────────────────────────────────────
        n = len(distribuicao)
        label_div, cor_div = next(
            (lb, cor) for minv, lb, cor in _DIVERSIFICACAO if n >= minv
        )
        w.par([("   • Ativos : ", "dim"), (str(n), "valor")])
        w.par([("   • Maior  : ", "dim"),
               (f"{ordenados[0][0]}  ({ordenados[0][1]['percentual']:.2f}%)", "moeda")])
        if len(ordenados) > 1:
            w.par([("   • Menor  : ", "dim"),
                   (f"{ordenados[-1][0]}  ({ordenados[-1][1]['percentual']:.2f}%)", "moeda")])
        w.linha("")
        w.par([("   • Status : ", "dim"), (label_div, None)], cor_override=cor_div)
        w.linha("")

        self._desenhar_donut(ordenados)
        self._atualizar_pl(operacoes, distribuicao)

    # ─────────────────────── PAINEL DIREITO ───────────────────────

    def _desenhar_donut(self, ordenados: list) -> None:
        self._canvas.update_idletasks()
        self._canvas.delete("all")

        w = self._canvas.winfo_width()
        h = self._canvas.winfo_height()

        if w < 10 or h < 10:
            self._canvas.after(100, lambda: self._desenhar_donut(ordenados))
            return

        cx, cy = w // 2, h // 2
        raio   = min(cx, cy) - 18
        furo   = int(raio * 0.52)
        inicio = -90.0

        for moeda, dados in ordenados:
            grau = (dados["percentual"] / 100) * 360
            cor  = self._cor_map.get(moeda, "#999")
            self._canvas.create_arc(
                cx - raio, cy - raio, cx + raio, cy + raio,
                start=inicio, extent=grau,
                fill=cor, outline="#F8F9FA", width=2,
            )
            inicio += grau

        self._canvas.create_oval(
            cx - furo, cy - furo, cx + furo, cy + furo,
            fill="#F8F9FA", outline="#F8F9FA",
        )
        self._canvas.create_text(cx, cy - 10, text=str(len(ordenados)),
                                 font=("Arial", 16, "bold"), fill="#1A237E")
        self._canvas.create_text(cx, cy + 10, text="ativos",
                                 font=("Arial", 9), fill="#757575")

        leg_x, leg_y = 8, 8
        for moeda, dados in ordenados:
            cor = self._cor_map.get(moeda, "#999")
            self._canvas.create_rectangle(leg_x, leg_y, leg_x + 10, leg_y + 10,
                                          fill=cor, outline="")
            self._canvas.create_text(leg_x + 14, leg_y + 5,
                                     text=f"{moeda} {dados['percentual']:.1f}%",
                                     font=("Arial", 8), fill="#333", anchor="w")
            leg_y += 14
            if leg_y > h - 20:
                break

    def _atualizar_pl(self, operacoes: list, distribuicao: dict) -> None:
        for row in self._pl_tree.get_children():
            self._pl_tree.delete(row)

        portfolio = self._engine.calcular_portfolio(
            operacoes, self._price_manager.precos_cache
        )

        for moeda, _ in sorted(distribuicao.items(),
                                key=lambda x: x[1]["percentual"], reverse=True):
            if moeda == "USDT":
                continue

            dados_port  = portfolio.get(moeda, {})
            preco_medio = dados_port.get("pmc_final", 0)
            preco_atual = self._price_manager.get_preco(moeda) or 0

            if preco_medio <= 0 or preco_atual <= 0:
                self._pl_tree.insert("", "end",
                                     values=(moeda, "—", "—", "—", "—"),
                                     tags=("neutro",))
                continue

            var_pct = ((preco_atual - preco_medio) / preco_medio) * 100
            qtd     = dados_port.get("quantidade_final", 0)
            pl_usd  = (preco_atual - preco_medio) * qtd
            sinal   = "+" if var_pct >= 0 else ""
            tag     = "ganho" if var_pct > 0 else ("perda" if var_pct < 0 else "neutro")

            self._pl_tree.insert("", "end", values=(
                moeda,
                f"${preco_medio:,.2f}",
                f"${preco_atual:,.2f}",
                f"{sinal}{var_pct:.2f}%",
                f"{sinal}${abs(pl_usd):,.2f}",
            ), tags=(tag,))

    def _limpar_paineis_direita(self) -> None:
        self._canvas.delete("all")
        for row in self._pl_tree.get_children():
            self._pl_tree.delete(row)

    # ─────────────────────── AUXILIARES ───────────────────────────

    def _atualizar_saldo_label(self, saldo: float, preco_brl: float) -> None:
        texto = f"Saldo:  ${saldo:,.2f} USDT"
        if preco_brl > 0:
            texto += f"  (≈ R$ {saldo * preco_brl:,.2f})"
        self._saldo_label.config(
            text=texto,
            foreground="#2E7D32" if saldo >= 0 else "#C62828",
        )

    def _popup_saldo_usdt(self) -> None:
        try:
            operacoes   = self._data_manager.carregar_operacoes()
            if not operacoes:
                messagebox.showinfo("Saldo USDT", "Nenhuma operação registrada ainda.")
                return
            saldo_info  = self._engine.calcular_saldo_usdt(operacoes)
            saldo_atual = saldo_info["saldo_atual"]
            historico   = saldo_info["historico"]
            preco_brl   = self._price_manager.preco_brl
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar saldo:\n{e}")
            return

        popup = tk.Toplevel(self)
        popup.title("💰 Histórico de Saldo USDT")
        popup.geometry("620x440")
        popup.resizable(False, False)

        header = ttk.Frame(popup, padding=15)
        header.pack(fill="x")

        texto = f"💰  Saldo atual:  ${saldo_atual:,.2f} USDT"
        if preco_brl > 0:
            texto += f"   (≈ R$ {saldo_atual * preco_brl:,.2f})"

        ttk.Label(header, text=texto, font=("Arial", 13, "bold"),
                  foreground="#2E7D32" if saldo_atual >= 0 else "#C62828").pack()

        ttk.Separator(popup).pack(fill="x", padx=15)

        txt = tk.Text(popup, wrap="word", font=("Consolas", 10), bg="#F8F9FA",
                      relief="flat", padx=15, pady=10)
        sb  = ttk.Scrollbar(popup, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill="y", padx=(0, 5), pady=10)
        txt.pack(fill="both", expand=True, padx=(10, 0), pady=10)

        txt.tag_configure("data",  foreground="#1565C0", font=("Consolas", 10, "bold"))
        txt.tag_configure("saldo", foreground="#2E7D32", font=("Consolas", 10))

        if historico:
            for mov in reversed(historico):
                d = datetime.strptime(
                    mov["data"], "%Y-%m-%d %H:%M:%S"
                ).strftime("%d/%m/%Y %H:%M")
                txt.insert(tk.END, f"[{d}]  ", "data")
                txt.insert(tk.END, mov["descricao"] + "\n")
                txt.insert(tk.END,
                            f"   └─ saldo: ${mov['saldo_apos']:,.2f} USDT\n\n", "saldo")
        else:
            txt.insert(tk.END, "Nenhuma movimentação registrada ainda.")

        txt.config(state="disabled")

    def _escrever(self, func: Callable) -> None:
        self._text.config(state="normal")
        self._text.delete("1.0", tk.END)
        try:
            func(TextWriter(self._text, self._chars_por_linha()))
        except Exception as e:
            logger.error(f"Erro ao renderizar distribuição: {e}")
            self._text.insert(tk.END, f"❌ Erro ao renderizar: {e}")
        finally:
            self._text.config(state="disabled")


# ═══════════════════════════════════════════════════════════════════
#  TextWriter  –  helper para escrita formatada no tk.Text
# ═══════════════════════════════════════════════════════════════════

class TextWriter:
    """
    Wraps um tk.Text e expõe helpers de escrita formatada.

    Parâmetros
    ----------
    widget  : o tk.Text alvo
    largura : número de caracteres por linha (calculado pelo chamador)
    """

    def __init__(self, widget: tk.Text, largura: int = 52):
        self._w    = widget
        self.largura = largura   # acessível externamente como `w.largura`

    # ── primitivas ──────────────────────────────────────────────

    def linha(self, texto: str = "", tag: Optional[str] = None) -> None:
        self._w.insert(tk.END, texto + "\n", tag or "")

    def par(self, partes: list, cor_override: Optional[str] = None,
            _no_newline: bool = False) -> None:
        for texto, tag in partes:
            if cor_override:
                tmp = f"_tmp_{abs(hash(texto))}"
                self._w.tag_configure(tmp, foreground=cor_override,
                                      font=("Consolas", 11, "bold"))
                self._w.insert(tk.END, texto, tmp)
            else:
                self._w.insert(tk.END, texto, tag or "")
        if not _no_newline:
            self._w.insert(tk.END, "\n")

    def sep(self, char: str = "─") -> None:
        """Separador que ocupa toda a largura dinâmica do painel."""
        self._w.insert(tk.END, "  " + char * self.largura + "\n", "dim")

    def centralizado(self, texto: str, tag: Optional[str] = None) -> None:
        self._w.insert(tk.END, texto.center(self.largura + 4) + "\n", tag or "")