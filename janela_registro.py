import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, List, Optional
import logging

logger = logging.getLogger(__name__)


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
        super().__init__(parent, padding="20")
        self._data_manager     = data_manager
        self._price_manager    = price_manager
        self._engine           = analysis_engine
        self._moedas           = moedas_suportadas
        self._on_change        = on_change or (lambda: None)
        self._build_ui()

    def atualizar(self) -> None:
        self._atualizar_interface_venda()

    def _build_ui(self) -> None:
        ttk.Label(self, text="Registrar Nova Operação",
                  font=("Arial", 16, "bold")).pack(pady=(0, 20))

        form = ttk.Frame(self)
        form.pack(pady=10)
        self._build_form(form)

        style = ttk.Style()
        style.configure("Accent.TButton", font=("Arial", 12, "bold"))

        ttk.Button(
            self, text="💾 Salvar Operação", command=self._salvar,
            style="Accent.TButton", padding=(20, 10), cursor="hand2",
        ).pack(pady=30)

    def _build_form(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Moeda:", font=("Arial", 11)).grid(
            row=0, column=0, sticky="w", pady=5)
        self._combo_moeda = ttk.Combobox(
            parent, values=self._moedas, width=20, font=("Arial", 11))
        self._combo_moeda.grid(row=0, column=1, pady=5, padx=10)
        self._combo_moeda.bind("<<ComboboxSelected>>", self._ao_mudar_selecao)

        self._label_preco_atual = ttk.Label(
            parent, text="", font=("Arial", 10), foreground="blue")
        self._label_preco_atual.grid(row=0, column=2, padx=10)

        ttk.Label(parent, text="Operação:", font=("Arial", 11)).grid(
            row=1, column=0, sticky="w", pady=5)
        self._combo_tipo = ttk.Combobox(
            parent, values=["Compra", "Venda"], width=20, font=("Arial", 11))
        self._combo_tipo.grid(row=1, column=1, pady=5, padx=10)
        self._combo_tipo.set("Compra")
        self._combo_tipo.bind("<<ComboboxSelected>>", self._ao_mudar_selecao)

        ttk.Label(parent, text="Valor (USDT):", font=("Arial", 11)).grid(
            row=2, column=0, sticky="w", pady=5)
        self._entry_valor = ttk.Entry(parent, width=22, font=("Arial", 11))
        self._entry_valor.grid(row=2, column=1, pady=5, padx=10)
        self._entry_valor.bind("<KeyRelease>", self._calcular_quantidade)

        self._label_quantidade = ttk.Label(
            parent, text="", font=("Arial", 10), foreground="gray")
        self._label_quantidade.grid(row=2, column=2, padx=10)

        ttk.Label(parent, text="Preço Unitário:", font=("Arial", 11)).grid(
            row=3, column=0, sticky="w", pady=5)
        self._entry_preco = ttk.Entry(parent, width=22, font=("Arial", 11))
        self._entry_preco.grid(row=3, column=1, pady=5, padx=10)
        self._entry_preco.bind("<KeyRelease>", self._calcular_quantidade)

        ttk.Button(
            parent, text="Usar Preço Atual", command=self._usar_preco_atual,
            cursor="hand2",
        ).grid(row=3, column=2, pady=5, padx=10, sticky="w")

        self._label_saldo_venda = ttk.Label(
            parent, text="", font=("Arial", 10, "bold"), foreground="darkblue")
        self._label_saldo_venda.grid(
            row=4, column=0, columnspan=2, sticky="w", padx=5, pady=(10, 0))

        self._btn_vender_tudo = ttk.Button(
            parent, text="Vender Tudo", command=self._vender_tudo, cursor="hand2")
        self._btn_vender_tudo.grid(row=4, column=2, pady=(10, 0), padx=10, sticky="w")

        self._label_saldo_venda.grid_remove()
        self._btn_vender_tudo.grid_remove()

    def _ao_mudar_selecao(self, event=None) -> None:
        self._ao_selecionar_moeda()
        self._atualizar_interface_venda()

    def _ao_selecionar_moeda(self, event=None) -> None:
        moeda = self._combo_moeda.get()
        if not moeda:
            return

        if moeda == "USDT":
            self._label_preco_atual.config(text="Stablecoin: $1.00")
            self._entry_preco.config(state="normal")
            self._entry_preco.delete(0, tk.END)
            self._entry_preco.insert(0, "1.000000")
            self._entry_preco.config(state="disabled")
            self._calcular_quantidade()
            return

        self._entry_preco.config(state="normal")
        preco = self._price_manager.get_preco(moeda)
        if preco:
            self._label_preco_atual.config(text=f"Atual: ${preco:.4f}")
            self._entry_preco.delete(0, tk.END)
            self._entry_preco.insert(0, f"{preco:.6f}")
            self._calcular_quantidade()
        else:
            self._label_preco_atual.config(text="Preço indisponível")

    def _atualizar_interface_venda(self, event=None) -> None:
        moeda    = self._combo_moeda.get()
        operacao = self._combo_tipo.get()

        if operacao == "Venda" and moeda and moeda != "USDT":
            try:
                operacoes   = self._data_manager.carregar_operacoes()
                portfolio   = self._engine.calcular_portfolio(
                    operacoes, self._price_manager.precos_cache)
                saldo_moeda = 0.0
                if moeda in portfolio:
                    saldo_moeda = portfolio[moeda].get("quantidade_final", 0)
                self._label_saldo_venda.config(
                    text=f"Saldo disponível: {saldo_moeda:.8f} {moeda}")
                self._label_saldo_venda.grid()
                self._btn_vender_tudo.grid()
            except Exception as e:
                logger.error(f"Erro ao buscar saldo para venda: {e}")
                self._label_saldo_venda.grid_remove()
                self._btn_vender_tudo.grid_remove()
        else:
            self._label_saldo_venda.grid_remove()
            self._btn_vender_tudo.grid_remove()

    def _vender_tudo(self) -> None:
        moeda = self._combo_moeda.get()
        if not moeda or moeda == "USDT":
            messagebox.showwarning("Ação inválida",
                                   "Selecione uma criptomoeda para vender.")
            return

        operacoes = self._data_manager.carregar_operacoes()
        portfolio = self._engine.calcular_portfolio(
            operacoes, self._price_manager.precos_cache)

        saldo = portfolio.get(moeda, {}).get("quantidade_final", 0)
        if saldo < 1e-9:
            messagebox.showinfo("Saldo Insuficiente",
                                f"Você não possui saldo de {moeda} para vender.")
            return

        preco_atual = self._price_manager.get_preco(moeda)
        if not preco_atual or preco_atual <= 0:
            messagebox.showerror("Erro",
                                 f"Não foi possível obter o preço atual de {moeda}.")
            return

        self._entry_valor.delete(0, tk.END)
        self._entry_valor.insert(0, f"{saldo * preco_atual:.4f}")
        self._entry_preco.config(state="normal")
        self._entry_preco.delete(0, tk.END)
        self._entry_preco.insert(0, f"{preco_atual:.6f}")
        self._calcular_quantidade()

    def _calcular_quantidade(self, event=None) -> None:
        try:
            valor = float(self._entry_valor.get())
            preco = float(self._entry_preco.get())
            if valor > 0 and preco > 0:
                qtd   = valor / preco
                moeda = self._combo_moeda.get()
                texto = f"= {qtd:.2f} USDT" if moeda == "USDT" else f"≈ {qtd:.6f} unidades"
                self._label_quantidade.config(text=texto)
            else:
                self._label_quantidade.config(text="")
        except (ValueError, ZeroDivisionError):
            self._label_quantidade.config(text="")

    def _usar_preco_atual(self) -> None:
        moeda = self._combo_moeda.get()
        if moeda == "USDT":
            self._entry_preco.config(state="normal")
            self._entry_preco.delete(0, tk.END)
            self._entry_preco.insert(0, "1.000000")
            self._entry_preco.config(state="disabled")
            self._calcular_quantidade()
            return

        self._entry_preco.config(state="normal")
        preco = self._price_manager.get_preco(moeda)
        if preco:
            self._entry_preco.delete(0, tk.END)
            self._entry_preco.insert(0, f"{preco:.6f}")
            self._calcular_quantidade()
        else:
            messagebox.showwarning("Aviso", "Preço não disponível.")

    def _validar(self) -> list:
        erros = []
        if not self._combo_moeda.get():
            erros.append("Selecione uma moeda")
        if not self._combo_tipo.get():
            erros.append("Selecione o tipo de operação")
        try:
            if float(self._entry_valor.get()) <= 0:
                erros.append("Valor deve ser maior que zero")
        except ValueError:
            erros.append("Valor deve ser um número válido")
        try:
            if float(self._entry_preco.get()) <= 0:
                erros.append("Preço deve ser maior que zero")
        except ValueError:
            erros.append("Preço deve ser um número válido")
        return erros

    def _salvar(self) -> None:
        erros = self._validar()
        if erros:
            messagebox.showerror("Erro de Validação", "\n".join(erros))
            return

        try:
            moeda    = self._combo_moeda.get().strip().upper()
            tipo     = self._combo_tipo.get().strip().lower()
            valor    = Decimal(self._entry_valor.get())
            preco    = Decimal(self._entry_preco.get())

            if preco <= 0:
                raise InvalidOperation("Preço inválido")

            quantidade = valor / preco

            if tipo == "compra" and moeda != "USDT":
                operacoes = self._data_manager.carregar_operacoes()
                validacao = self._engine.validar_saldo_suficiente(
                    operacoes, float(valor))

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
            operacao  = [data_hora, moeda, tipo, float(valor),
                         float(preco), float(quantidade)]

            if not self._data_manager.salvar_operacao(operacao):
                messagebox.showerror("Erro", "Não foi possível salvar a operação.")
                return

            if moeda == "USDT":
                msg = f"{'Depósito' if tipo == 'compra' else 'Saque'} de ${valor:,.2f} USDT registrado!"
            else:
                msg = f"{tipo.title()} de {moeda} registrada! Saldo USDT atualizado."

            messagebox.showinfo("Sucesso", msg)
            self._limpar()
            self._on_change()

        except InvalidOperation:
            messagebox.showerror("Erro de Validação",
                                 "Valor e preço devem ser números válidos e maiores que zero.")
        except Exception as e:
            logger.exception("Erro ao salvar operação")
            messagebox.showerror("Erro", f"Erro inesperado: {e}")

    def _limpar(self) -> None:
        self._entry_valor.delete(0, tk.END)
        self._entry_preco.config(state="normal")
        self._entry_preco.delete(0, tk.END)
        self._label_quantidade.config(text="")
        self._label_preco_atual.config(text="")
        self._label_saldo_venda.grid_remove()
        self._btn_vender_tudo.grid_remove()