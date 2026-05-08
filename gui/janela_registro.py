import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from decimal import Decimal, InvalidOperation, getcontext
from enum import Enum
from typing import Any, Callable, List, Optional
import logging

getcontext().prec = 18
logger = logging.getLogger(__name__)


class TipoOperacao(Enum):
    COMPRA      = "compra"
    VENDA       = "venda"
    VENDA_TOTAL = "venda_total"

    @property
    def label(self) -> str:
        return {
            "COMPRA":      "Compra",
            "VENDA":       "Venda",
            "VENDA_TOTAL": "Venda Total (MAX)",
        }[self.name]

    @property
    def csv_value(self) -> str:
        return {
            "COMPRA":      "compra",
            "VENDA":       "venda",
            "VENDA_TOTAL": "venda",
        }[self.name]

    @classmethod
    def from_label(cls, label: str) -> "TipoOperacao":
        for membro in cls:
            if membro.label == label:
                return membro
        raise KeyError(f"TipoOperacao desconhecido: {label!r}")

    @classmethod
    def labels_crypto(cls) -> list:
        return [m.label for m in cls]

    @classmethod
    def labels_usdt(cls) -> list:
        return [cls.COMPRA.label, cls.VENDA.label]


class JanelaRegistro(ttk.Frame):

    def __init__(
        self,
        parent: Any,
        data_manager: Any,
        price_manager: Any,
        analysis_engine: Any,
        moedas_suportadas: List[str],
        on_change: Optional[Callable] = None,
    ):
        super().__init__(parent)
        self._data_manager     = data_manager
        self._price_manager    = price_manager
        self._engine           = analysis_engine
        self._moedas           = moedas_suportadas
        self._on_change        = on_change or (lambda: None)
        self._qtd_max_travada: Optional[Decimal] = None

        self._configurar_estilos()
        self._build_ui()

    def _configurar_estilos(self):
        style = ttk.Style()
        style.configure("Titulo.TLabel",   font=("Segoe UI", 16, "bold"))
        style.configure("Padrao.TLabel",   font=("Segoe UI", 11))
        style.configure("Info.TLabel",     font=("Segoe UI", 10),          foreground="#666666")
        style.configure("Destaque.TLabel", font=("Segoe UI", 10, "bold"),  foreground="#0052cc")
        style.configure("Saldo.TLabel",    font=("Segoe UI", 10, "bold"),  foreground="#2e7d32")
        style.configure("Travado.TLabel",  font=("Segoe UI", 10, "bold"),  foreground="#cc0000")
        style.configure("Dica.TLabel",     font=("Segoe UI", 9, "italic"), foreground="#0052cc")
        style.configure("Erro.TLabel",     font=("Segoe UI", 9, "bold"),   foreground="#cc0000")
        style.configure("Accent.TButton",  font=("Segoe UI", 12, "bold"))

    def _eh_stablecoin(self, moeda: str) -> bool:
        return moeda in ("USDT", "USDC")

    def atualizar(self) -> None:
        self._atualizar_saldo_disponivel()

    def _build_ui(self) -> None:
        main = ttk.Frame(self, padding="30 20 30 20")
        main.pack(fill="both", expand=True)

        header = ttk.Frame(main)
        header.pack(fill="x", pady=(0, 20))
        ttk.Label(header, text="Registrar Nova Operação", style="Titulo.TLabel").pack(side="left")

        form_frame = ttk.LabelFrame(main, text="Detalhes da Transação", padding="20 20 20 20")
        form_frame.pack(fill="both", expand=True, pady=10)
        self._build_form(form_frame)

        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill="x", pady=(30, 10))
        self._btn_salvar = ttk.Button(
            btn_frame,
            text="💾 Salvar Operação",
            command=self._salvar,
            style="Accent.TButton",
            cursor="hand2",
            state="disabled",
        )
        self._btn_salvar.pack(ipady=5, ipadx=20)

    def _build_form(self, parent: ttk.Frame) -> None:
        container = ttk.Frame(parent)
        container.pack(anchor="n", pady=20)

        ttk.Label(container, text="Moeda:", style="Padrao.TLabel").grid(
            row=0, column=0, sticky="e", pady=10, padx=(0, 15))
        self._combo_moeda = ttk.Combobox(
            container, values=self._moedas, font=("Segoe UI", 11), state="readonly", width=22)
        self._combo_moeda.grid(row=0, column=1, sticky="w", pady=10)
        self._combo_moeda.bind("<<ComboboxSelected>>", self._ao_mudar_moeda)

        self._label_preco_atual = ttk.Label(container, text="", style="Destaque.TLabel")
        self._label_preco_atual.grid(row=0, column=2, sticky="w", padx=(15, 0))

        ttk.Label(container, text="Operação:", style="Padrao.TLabel").grid(
            row=1, column=0, sticky="e", pady=10, padx=(0, 15))
        self._combo_tipo = ttk.Combobox(
            container, font=("Segoe UI", 11), state="disabled", width=22)
        self._combo_tipo.grid(row=1, column=1, sticky="w", pady=10)
        self._combo_tipo.bind("<<ComboboxSelected>>", self._ao_mudar_tipo)

        self._label_saldo = ttk.Label(container, text="", style="Saldo.TLabel")
        self._label_saldo.grid(row=1, column=2, sticky="w", padx=(15, 0))

        self._label_preco_titulo = ttk.Label(container, text="Preço Unitário:", style="Padrao.TLabel")
        self._label_preco_titulo.grid(row=2, column=0, sticky="e", pady=10, padx=(0, 15))
        self._entry_preco = ttk.Entry(container, font=("Segoe UI", 11), width=24, state="disabled")
        self._entry_preco.grid(row=2, column=1, sticky="w", pady=10)
        self._entry_preco.bind("<KeyRelease>", self._calcular_quantidade)

        ttk.Label(container, text="Valor (USDT):", style="Padrao.TLabel").grid(
            row=3, column=0, sticky="e", pady=10, padx=(0, 15))
        self._entry_valor = ttk.Entry(container, font=("Segoe UI", 11), width=24, state="disabled")
        self._entry_valor.grid(row=3, column=1, sticky="w", pady=10)
        self._entry_valor.bind("<KeyRelease>", self._calcular_quantidade)

        self._label_quantidade = ttk.Label(container, text="", style="Info.TLabel")
        self._label_quantidade.grid(row=3, column=2, sticky="w", padx=(15, 0))

        self._label_ajuda = ttk.Label(container, text="", style="Dica.TLabel", justify="left")
        self._label_ajuda.grid(row=4, column=1, columnspan=2, sticky="w", pady=(0, 4))

        self._label_erro_saldo = ttk.Label(container, text="", style="Erro.TLabel", justify="left")
        self._label_erro_saldo.grid(row=5, column=1, columnspan=2, sticky="w", pady=(0, 5))

    def _ao_mudar_moeda(self, event=None) -> None:
        self._qtd_max_travada = None
        self._combo_tipo.set("")
        self._combo_tipo.config(state="disabled")
        self._entry_preco.config(state="normal")
        self._entry_preco.delete(0, tk.END)
        self._entry_preco.config(state="disabled")
        self._entry_valor.config(state="normal")
        self._entry_valor.delete(0, tk.END)
        self._entry_valor.config(state="disabled")
        self._label_quantidade.config(text="", style="Info.TLabel")
        self._label_saldo.config(text="")
        self._label_ajuda.config(text="")
        self._label_erro_saldo.config(text="")
        self._btn_salvar.config(state="disabled")
        self._label_preco_titulo.config(text="Preço Unitário:")

        moeda = self._combo_moeda.get()
        if not moeda:
            return

        if self._eh_stablecoin(moeda):
            self._combo_tipo.config(values=TipoOperacao.labels_usdt(), state="readonly")
            preco_brl = self._price_manager.preco_brl
            if preco_brl and preco_brl > 1.1:
                taxa = f"{preco_brl:.4f}"
                self._label_preco_atual.config(text=f"Cotação BRL: R${preco_brl:.4f}")
            else:
                taxa = "1.000000"
                self._label_preco_atual.config(text="Cotação BRL indisponível")
            self._label_preco_titulo.config(text="Taxa BRL:")
            self._label_ajuda.config(
                text=f"💡 {moeda} equivale a $1,00 USD. Informe a cotação do dólar em reais.")
            self._entry_preco.config(state="normal")
            self._entry_preco.insert(0, taxa)
        else:
            self._combo_tipo.config(values=TipoOperacao.labels_crypto(), state="readonly")
            preco = self._price_manager.get_preco(moeda)
            self._entry_preco.config(state="normal")
            if preco:
                self._label_preco_atual.config(text=f"Atual: ${preco:.4f}")
                self._entry_preco.insert(0, f"{preco:.6f}")
            else:
                self._label_preco_atual.config(text="Preço indisponível")

    def _ao_mudar_tipo(self, event=None) -> None:
        self._qtd_max_travada = None
        self._entry_valor.config(state="normal")
        self._entry_valor.delete(0, tk.END)
        self._label_quantidade.config(text="", style="Info.TLabel")
        self._label_erro_saldo.config(text="")
        self._btn_salvar.config(state="disabled")

        moeda = self._combo_moeda.get()
        if not self._eh_stablecoin(moeda):
            self._label_ajuda.config(text="")

        self._atualizar_saldo_disponivel()
        self._verificar_venda_total()

    def _verificar_venda_total(self) -> None:
        tipo_label = self._combo_tipo.get()
        if not tipo_label:
            return
        tipo  = TipoOperacao.from_label(tipo_label)
        moeda = self._combo_moeda.get()

        if tipo is not TipoOperacao.VENDA_TOTAL or not moeda or self._eh_stablecoin(moeda):
            self._calcular_quantidade()
            return

        try:
            operacoes   = self._data_manager.carregar_operacoes()
            portfolio   = self._engine.calcular_portfolio(
                operacoes, self._price_manager.precos_cache)
            saldo_exato = Decimal(str(portfolio.get(moeda, {}).get("quantidade_final", 0)))

            if saldo_exato <= 0:
                messagebox.showwarning("Aviso", f"Você não possui saldo de {moeda} para vender.")
                self._combo_tipo.set(TipoOperacao.VENDA.label)
                self._calcular_quantidade()
                return

            self._qtd_max_travada = saldo_exato

            preco_str = self._entry_preco.get()
            if preco_str:
                try:
                    preco          = Decimal(preco_str)
                    valor_sugerido = saldo_exato * preco
                    self._entry_valor.delete(0, tk.END)
                    self._entry_valor.insert(0, f"{valor_sugerido:.4f}")
                except InvalidOperation:
                    pass

            self._calcular_quantidade()

        except Exception as e:
            logger.error(f"Erro ao processar venda total: {e}")

    def _atualizar_saldo_disponivel(self) -> None:
        moeda      = self._combo_moeda.get()
        tipo_label = self._combo_tipo.get()
        if not tipo_label:
            self._label_saldo.config(text="")
            return
        tipo = TipoOperacao.from_label(tipo_label)

        if tipo in (TipoOperacao.VENDA, TipoOperacao.VENDA_TOTAL) and moeda and not self._eh_stablecoin(moeda):
            try:
                operacoes = self._data_manager.carregar_operacoes()
                portfolio = self._engine.calcular_portfolio(
                    operacoes, self._price_manager.precos_cache)
                saldo = portfolio.get(moeda, {}).get("quantidade_final", 0)
                self._label_saldo.config(text=f"Saldo: {saldo:.8f} {moeda}")
            except Exception:
                self._label_saldo.config(text="")
        else:
            self._label_saldo.config(text="")

    def _calcular_quantidade(self, event=None) -> None:
        try:
            moeda      = self._combo_moeda.get()
            tipo_label = self._combo_tipo.get()
            if not tipo_label:
                self._label_quantidade.config(text="", style="Info.TLabel")
                self._btn_salvar.config(state="disabled")
                return

            tipo      = TipoOperacao.from_label(tipo_label)
            valor_str = self._entry_valor.get()
            preco_str = self._entry_preco.get()

            if tipo is TipoOperacao.VENDA_TOTAL and self._qtd_max_travada is not None:
                self._label_quantidade.config(
                    text=f"🔒 {self._qtd_max_travada:.8f} {moeda} serão zerados exatamente.",
                    style="Travado.TLabel")
                self._label_ajuda.config(
                    text="💡 Digite no campo Valor (USDT) o que a corretora te pagou após a taxa.")
                self._verificar_estado_botao()
                return

            if not self._eh_stablecoin(moeda):
                self._label_ajuda.config(text="")

            if not valor_str or not preco_str:
                self._label_quantidade.config(text="", style="Info.TLabel")
                self._btn_salvar.config(state="disabled")
                return

            valor = Decimal(valor_str)
            preco = Decimal(preco_str)

            if valor > 0 and preco > 0:
                if self._eh_stablecoin(moeda):
                    qtd   = valor
                    texto = f"= {float(qtd):.2f} {moeda}  (taxa R${float(preco):.4f}/USD)"
                else:
                    qtd   = valor / preco
                    texto = f"≈ {float(qtd):.8f} unidades"
                self._label_quantidade.config(text=texto, style="Info.TLabel")
                self._verificar_saldo_inline(tipo, moeda, valor)
            else:
                self._label_quantidade.config(text="", style="Info.TLabel")
                self._btn_salvar.config(state="disabled")

        except (InvalidOperation, ZeroDivisionError):
            self._label_quantidade.config(text="", style="Info.TLabel")
            self._btn_salvar.config(state="disabled")

    def _verificar_saldo_inline(self, tipo: TipoOperacao, moeda: str, valor: Decimal) -> None:
        if tipo is not TipoOperacao.VENDA or self._eh_stablecoin(moeda):
            self._label_erro_saldo.config(text="")
            self._verificar_estado_botao()
            return
        try:
            operacoes = self._data_manager.carregar_operacoes()
            portfolio = self._engine.calcular_portfolio(
                operacoes, self._price_manager.precos_cache)
            saldo = Decimal(str(portfolio.get(moeda, {}).get("quantidade_final", 0)))
            preco_str = self._entry_preco.get()
            preco     = Decimal(preco_str) if preco_str else Decimal("0")
            if preco > 0:
                qtd_solicitada = valor / preco
                if qtd_solicitada > saldo:
                    falta = qtd_solicitada - saldo
                    self._label_erro_saldo.config(
                        text=f"⚠ Saldo insuficiente! Faltam {float(falta):.8f} {moeda}")
                    self._btn_salvar.config(state="disabled")
                    return
            self._label_erro_saldo.config(text="")
            self._verificar_estado_botao()
        except Exception:
            self._label_erro_saldo.config(text="")
            self._verificar_estado_botao()

    def _verificar_estado_botao(self) -> None:
        try:
            valor = Decimal(self._entry_valor.get())
            preco = Decimal(self._entry_preco.get())
            if valor > 0 and preco > 0:
                self._btn_salvar.config(state="normal")
            else:
                self._btn_salvar.config(state="disabled")
        except InvalidOperation:
            self._btn_salvar.config(state="disabled")

    def _validar(self) -> list:
        erros = []
        if not self._combo_moeda.get():
            erros.append("Selecione uma moeda")
        if not self._combo_tipo.get():
            erros.append("Selecione o tipo de operação")
        try:
            if Decimal(self._entry_valor.get()) <= 0:
                erros.append("Valor deve ser maior que zero")
        except InvalidOperation:
            erros.append("Valor deve ser um número válido")
        try:
            if Decimal(self._entry_preco.get()) <= 0:
                erros.append("Preço deve ser maior que zero")
        except InvalidOperation:
            erros.append("Preço deve ser um número válido")
        return erros

    def _salvar(self) -> None:
        erros = self._validar()
        if erros:
            messagebox.showerror("Erro de Validação", "\n".join(erros))
            return

        try:
            moeda    = self._combo_moeda.get().strip().upper()
            tipo     = TipoOperacao.from_label(self._combo_tipo.get())
            tipo_csv = tipo.csv_value
            valor    = Decimal(self._entry_valor.get())
            preco    = Decimal(self._entry_preco.get())
            taxa_brl = self._price_manager.preco_brl or 0.0

            if self._eh_stablecoin(moeda):
                quantidade = valor
            elif tipo is TipoOperacao.VENDA_TOTAL and self._qtd_max_travada is not None:
                quantidade = self._qtd_max_travada
            else:
                quantidade = valor / preco

            if tipo is TipoOperacao.COMPRA and not self._eh_stablecoin(moeda):
                operacoes = self._data_manager.carregar_operacoes()
                validacao = self._engine.validar_saldo_suficiente(operacoes, float(valor))
                if not validacao["saldo_suficiente"]:
                    saldo_atual = validacao["saldo_atual"]
                    faltam      = abs(validacao["diferenca"])
                    resposta    = messagebox.askquestion(
                        "Saldo USDT Insuficiente",
                        f"Saldo atual: ${saldo_atual:,.2f} USDT\n"
                        f"Valor da compra: ${float(valor):,.2f} USDT\n"
                        f"Faltam: ${faltam:,.2f} USDT\n\n"
                        f"Deseja continuar mesmo assim?",
                        icon="warning",
                    )
                    if resposta == "no":
                        return

            data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            operacao  = [data_hora, moeda, tipo_csv, float(valor),
                         float(preco), float(quantidade), taxa_brl]

            if not self._data_manager.salvar_operacao(operacao):
                messagebox.showerror("Erro", "Não foi possível salvar a operação.")
                return

            if tipo is TipoOperacao.VENDA_TOTAL:
                msg = f"Venda Total executada! Saldo de {moeda} zerado com sucesso."
            elif self._eh_stablecoin(moeda):
                msg = f"{'Depósito' if tipo_csv == 'compra' else 'Saque'} de ${valor:,.2f} {moeda} registrado!"
            else:
                msg = f"{tipo_csv.title()} de {moeda} registrada com sucesso!"

            messagebox.showinfo("Sucesso", msg)
            self._limpar()
            self._on_change()

        except Exception as e:
            logger.exception("Erro ao salvar operação")
            messagebox.showerror("Erro", f"Erro inesperado: {e}")

    def _limpar(self) -> None:
        self._qtd_max_travada = None
        self._combo_moeda.set("")
        self._combo_tipo.set("")
        self._combo_tipo.config(state="disabled")
        self._entry_preco.config(state="normal")
        self._entry_preco.delete(0, tk.END)
        self._entry_preco.config(state="disabled")
        self._entry_valor.config(state="normal")
        self._entry_valor.delete(0, tk.END)
        self._entry_valor.config(state="disabled")
        self._label_quantidade.config(text="", style="Info.TLabel")
        self._label_preco_atual.config(text="")
        self._label_saldo.config(text="")
        self._label_ajuda.config(text="")
        self._label_erro_saldo.config(text="")
        self._label_preco_titulo.config(text="Preço Unitário:")
        self._btn_salvar.config(state="disabled")

    def atualizar_lista_moedas(self, novas_moedas: list) -> None:
        self._moedas = novas_moedas
        self._combo_moeda.config(values=self._moedas)
        moeda_atual = self._combo_moeda.get()
        if moeda_atual and moeda_atual not in self._moedas:
            self._limpar()