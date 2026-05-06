import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from decimal import Decimal, InvalidOperation, getcontext
from typing import Any, Callable, List, Optional
import logging

getcontext().prec = 18
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
        super().__init__(parent)
        self._data_manager  = data_manager
        self._price_manager = price_manager
        self._engine        = analysis_engine
        self._moedas        = moedas_suportadas
        self._on_change     = on_change or (lambda: None)
        self._qtd_max_travada: Optional[Decimal] = None

        self._configurar_estilos()
        self._build_ui()

    def _configurar_estilos(self):
        style = ttk.Style()
        style.configure("Titulo.TLabel", font=("Segoe UI", 16, "bold"))
        style.configure("Padrao.TLabel", font=("Segoe UI", 11))
        style.configure("Info.TLabel", font=("Segoe UI", 10), foreground="#666666")
        style.configure("Destaque.TLabel", font=("Segoe UI", 10, "bold"), foreground="#0052cc")
        style.configure("Saldo.TLabel", font=("Segoe UI", 10, "bold"), foreground="#2e7d32")
        style.configure("AlertaInfo.TLabel", font=("Segoe UI", 10, "bold"), foreground="#cc0000")
        style.configure("Dica.TLabel", font=("Segoe UI", 9, "italic"), foreground="#0052cc")
        style.configure("Max.TButton", font=("Segoe UI", 9, "bold"), foreground="#cc0000")
        style.configure("Accent.TButton", font=("Segoe UI", 12, "bold"))
        style.configure("Acao.TButton", font=("Segoe UI", 10))

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
        ttk.Button(
            btn_frame, text="💾 Salvar Operação", command=self._salvar, style="Accent.TButton", cursor="hand2"
        ).pack(ipady=5, ipadx=20)

    def _build_form(self, parent: ttk.Frame) -> None:
        container = ttk.Frame(parent)
        container.pack(anchor="n", pady=20)

        ttk.Label(container, text="Moeda:", style="Padrao.TLabel").grid(row=0, column=0, sticky="e", pady=10, padx=(0, 15))
        self._combo_moeda = ttk.Combobox(container, values=self._moedas, font=("Segoe UI", 11), state="readonly", width=22)
        self._combo_moeda.grid(row=0, column=1, sticky="w", pady=10)
        self._combo_moeda.bind("<<ComboboxSelected>>", self._ao_mudar_selecao)

        self._label_preco_atual = ttk.Label(container, text="", style="Destaque.TLabel")
        self._label_preco_atual.grid(row=0, column=2, sticky="w", padx=(15, 0))

        ttk.Label(container, text="Operação:", style="Padrao.TLabel").grid(row=1, column=0, sticky="e", pady=10, padx=(0, 15))
        self._combo_tipo = ttk.Combobox(container, values=["Compra", "Venda"], font=("Segoe UI", 11), state="readonly", width=22)
        self._combo_tipo.grid(row=1, column=1, sticky="w", pady=10)
        self._combo_tipo.set("Compra")
        self._combo_tipo.bind("<<ComboboxSelected>>", self._ao_mudar_selecao)

        self._label_saldo = ttk.Label(container, text="", style="Saldo.TLabel")
        self._label_saldo.grid(row=1, column=2, sticky="w", padx=(15, 0))

        ttk.Label(container, text="Preço Unitário:", style="Padrao.TLabel").grid(row=2, column=0, sticky="e", pady=10, padx=(0, 15))
        self._entry_preco = ttk.Entry(container, font=("Segoe UI", 11), width=24)
        self._entry_preco.grid(row=2, column=1, sticky="w", pady=10)
        self._entry_preco.bind("<KeyRelease>", self._calcular_quantidade)

        ttk.Button(
            container, text="Usar Preço Atual", command=self._usar_preco_atual, style="Acao.TButton", cursor="hand2"
        ).grid(row=2, column=2, sticky="w", padx=(15, 0), pady=10)

        ttk.Label(container, text="Valor (USDT):", style="Padrao.TLabel").grid(row=3, column=0, sticky="e", pady=10, padx=(0, 15))
        
        frame_valor = ttk.Frame(container)
        frame_valor.grid(row=3, column=1, sticky="w", pady=10)
        
        self._entry_valor = ttk.Entry(frame_valor, font=("Segoe UI", 11), width=16)
        self._entry_valor.pack(side="left", padx=(0, 5))
        self._entry_valor.bind("<KeyRelease>", self._calcular_quantidade)

        self._btn_max = ttk.Button(
            frame_valor, text="MAX (Vender Tudo)", command=self._vender_tudo, style="Max.TButton", cursor="hand2"
        )
        self._btn_max.pack_forget()

        self._label_quantidade = ttk.Label(container, text="", style="Info.TLabel")
        self._label_quantidade.grid(row=3, column=2, sticky="w", padx=(15, 0))

        self._label_ajuda = ttk.Label(container, text="", style="Dica.TLabel", justify="left")
        self._label_ajuda.grid(row=4, column=1, columnspan=2, sticky="w", pady=(0, 10))

    def _ao_mudar_selecao(self, event=None) -> None:
        self._qtd_max_travada = None
        self._label_ajuda.config(text="")
        
        tipo = self._combo_tipo.get()
        if tipo == "Venda":
            self._btn_max.pack(side="left")
        else:
            self._btn_max.pack_forget()

        self._ao_selecionar_moeda()
        self._atualizar_saldo_disponivel()

    def _vender_tudo(self) -> None:
        moeda = self._combo_moeda.get()
        if not moeda or moeda == "USDT":
            messagebox.showinfo("Aviso", "Selecione uma criptomoeda válida para vender.")
            return
            
        try:
            operacoes = self._data_manager.carregar_operacoes()
            portfolio = self._engine.calcular_portfolio(operacoes, self._price_manager.precos_cache)
            saldo_exato = Decimal(str(portfolio.get(moeda, {}).get("quantidade_final", 0)))

            if saldo_exato <= 0:
                messagebox.showwarning("Aviso", f"Você não possui saldo de {moeda} para vender.")
                return

            self._qtd_max_travada = saldo_exato

            preco_str = self._entry_preco.get()
            if preco_str:
                preco = Decimal(preco_str)
                valor_usdt_sugestao = saldo_exato * preco
                self._entry_valor.delete(0, tk.END)
                self._entry_valor.insert(0, f"{valor_usdt_sugestao:.4f}")

            self._calcular_quantidade()

        except Exception as e:
            logger.error(f"Erro ao calcular venda total: {e}")

    def _ao_selecionar_moeda(self, event=None) -> None:
        moeda = self._combo_moeda.get()
        if not moeda:
            return

        if moeda == "USDT":
            preco_brl = self._price_manager.preco_brl
            if preco_brl and preco_brl > 1.1:
                self._label_preco_atual.config(text=f"Cotação BRL: R${preco_brl:.4f}")
                taxa = f"{preco_brl:.4f}"
            else:
                self._label_preco_atual.config(text="Cotação BRL indisponível")
                taxa = "1.000000"
            self._entry_preco.config(state="normal")
            self._entry_preco.delete(0, tk.END)
            self._entry_preco.insert(0, taxa)
            self._btn_max.pack_forget()
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

    def _atualizar_saldo_disponivel(self, event=None) -> None:
        moeda = self._combo_moeda.get()
        operacao = self._combo_tipo.get()

        if operacao == "Venda" and moeda and moeda != "USDT":
            try:
                operacoes = self._data_manager.carregar_operacoes()
                portfolio = self._engine.calcular_portfolio(operacoes, self._price_manager.precos_cache)
                saldo = portfolio.get(moeda, {}).get("quantidade_final", 0)
                self._label_saldo.config(text=f"Saldo: {saldo:.8f} {moeda}")
            except Exception as e:
                self._label_saldo.config(text="")
        else:
            self._label_saldo.config(text="")

    def _calcular_quantidade(self, event=None) -> None:
        try:
            moeda = self._combo_moeda.get()
            valor_str = self._entry_valor.get()
            preco_str = self._entry_preco.get()

            if self._qtd_max_travada is not None and self._combo_tipo.get() == "Venda":
                self._label_quantidade.config(
                    text=f"🔒 TRAVADO: Será zerado exatas {self._qtd_max_travada:.8f} {moeda}.",
                    style="AlertaInfo.TLabel"
                )
                self._label_ajuda.config(
                    text="💡 Dica: Digite no campo 'Valor (USDT)' exatamente o que a corretora te pagou.\nO sistema cuidará de zerar a moeda sem deixar lixo."
                )
                return
            else:
                self._label_ajuda.config(text="")

            if valor_str and preco_str:
                valor = Decimal(valor_str)
                preco = Decimal(preco_str)
                
                if valor > 0 and preco > 0:
                    if moeda == "USDT":
                        qtd = valor
                        texto = f"= {float(qtd):.2f} USDT (taxa: R${float(preco):.4f})"
                    else:
                        qtd = valor / preco
                        texto = f"≈ {float(qtd):.8f} unidades"
                    
                    self._label_quantidade.config(text=texto, style="Info.TLabel")
                else:
                    self._label_quantidade.config(text="", style="Info.TLabel")
        except (ValueError, InvalidOperation, ZeroDivisionError):
            if self._qtd_max_travada is None:
                self._label_quantidade.config(text="", style="Info.TLabel")

    def _usar_preco_atual(self) -> None:
        moeda = self._combo_moeda.get()
        if moeda == "USDT":
            return self._ao_selecionar_moeda()

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
            moeda = self._combo_moeda.get().strip().upper()
            tipo  = self._combo_tipo.get().strip().lower()
            valor = Decimal(self._entry_valor.get())
            preco = Decimal(self._entry_preco.get())

            taxa_brl = self._price_manager.preco_brl or 0.0

            if moeda == "USDT":
                quantidade = valor
            elif tipo == "venda" and self._qtd_max_travada is not None:
                quantidade = self._qtd_max_travada
            else:
                quantidade = valor / preco

            if tipo == "compra" and moeda != "USDT":
                operacoes = self._data_manager.carregar_operacoes()
                validacao = self._engine.validar_saldo_suficiente(operacoes, float(valor))

                if not validacao["saldo_suficiente"]:
                    resposta = messagebox.askquestion(
                        "Saldo USDT Insuficiente",
                        f"Faltam USDT para essa compra.\nDeseja continuar mesmo assim?",
                        icon="warning",
                    )
                    if resposta == "no":
                        return

            data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            operacao  = [data_hora, moeda, tipo, float(valor), float(preco), float(quantidade), taxa_brl]

            if not self._data_manager.salvar_operacao(operacao):
                messagebox.showerror("Erro", "Não foi possível salvar a operação.")
                return

            if tipo == 'venda' and self._qtd_max_travada is not None:
                msg = f"Venda Total executada! Saldo zerado com sucesso."
            else:
                msg = f"{tipo.title()} registrada com sucesso!"

            messagebox.showinfo("Sucesso", msg)
            self._limpar()
            self._on_change()

        except Exception as e:
            logger.exception("Erro ao salvar operação")
            messagebox.showerror("Erro", f"Erro inesperado: {e}")

    def _limpar(self) -> None:
        self._qtd_max_travada = None
        self._combo_moeda.set("")
        self._combo_tipo.set("Compra")
        self._btn_max.pack_forget()
        self._entry_valor.delete(0, tk.END)
        self._entry_preco.config(state="normal")
        self._entry_preco.delete(0, tk.END)
        self._label_quantidade.config(text="")
        self._label_preco_atual.config(text="")
        self._label_saldo.config(text="")
        self._label_ajuda.config(text="")

    def atualizar_lista_moedas(self, novas_moedas: list) -> None:
        self._moedas = novas_moedas
        self._combo_moeda.config(values=self._moedas)