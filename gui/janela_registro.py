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
        super().__init__(parent)
        self._data_manager     = data_manager
        self._price_manager    = price_manager
        self._engine           = analysis_engine
        self._moedas           = moedas_suportadas
        self._on_change        = on_change or (lambda: None)
        
        self._configurar_estilos()
        self._build_ui()

    def _configurar_estilos(self):
        style = ttk.Style()
        
        fonte_titulo = ("Segoe UI", 16, "bold")
        fonte_label = ("Segoe UI", 11)
        fonte_info = ("Segoe UI", 10)
        
        style.configure("Titulo.TLabel", font=fonte_titulo)
        style.configure("Padrao.TLabel", font=fonte_label)
        style.configure("Info.TLabel", font=fonte_info, foreground="#666666")
        style.configure("Destaque.TLabel", foreground="#0052cc", font=("Segoe UI", 10, "bold"))
        style.configure("Alerta.TLabel", font=("Segoe UI", 10, "bold"), foreground="#cc0000")
        
        style.configure("Accent.TButton", font=("Segoe UI", 12, "bold"))
        style.configure("Acao.TButton", font=("Segoe UI", 10))

    def atualizar(self) -> None:
        self._atualizar_interface_venda()

    def _build_ui(self) -> None:
        main_container = ttk.Frame(self, padding="30 20 30 20")
        main_container.pack(fill="both", expand=True)

        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill="x", pady=(0, 20))
        ttk.Label(
            header_frame, 
            text="Registrar Nova Operação", 
            style="Titulo.TLabel"
        ).pack(side="left")

        form_frame = ttk.LabelFrame(main_container, text="Detalhes da Transação", padding="20 20 20 20")
        form_frame.pack(fill="both", expand=True, pady=10)
        
        self._build_form(form_frame)

        btn_frame = ttk.Frame(main_container)
        btn_frame.pack(fill="x", pady=(30, 10))
        
        ttk.Button(
            btn_frame, 
            text="💾 Salvar Operação", 
            command=self._salvar,
            style="Accent.TButton", 
            cursor="hand2",
        ).pack(ipady=5, ipadx=20) 

    def _build_form(self, parent: ttk.Frame) -> None:

            container = ttk.Frame(parent)
            container.pack(anchor="n", pady=20)

            ttk.Label(container, text="Moeda:", style="Padrao.TLabel").grid(
                row=0, column=0, sticky="e", pady=10, padx=(0, 15))
            
            self._combo_moeda = ttk.Combobox(
                container, values=self._moedas, font=("Segoe UI", 11), state="readonly", width=22)
            self._combo_moeda.grid(row=0, column=1, sticky="w", pady=10)
            self._combo_moeda.bind("<<ComboboxSelected>>", self._ao_mudar_selecao)

            self._label_preco_atual = ttk.Label(container, text="", style="Destaque.TLabel")
            self._label_preco_atual.grid(row=0, column=2, sticky="w", padx=(15, 0))

            ttk.Label(container, text="Operação:", style="Padrao.TLabel").grid(
                row=1, column=0, sticky="e", pady=10, padx=(0, 15))
                
            self._combo_tipo = ttk.Combobox(
                container, values=["Compra", "Venda"], font=("Segoe UI", 11), state="readonly", width=22)
            self._combo_tipo.grid(row=1, column=1, sticky="w", pady=10)
            self._combo_tipo.set("Compra")
            self._combo_tipo.bind("<<ComboboxSelected>>", self._ao_mudar_selecao)

            ttk.Label(container, text="Valor (USDT):", style="Padrao.TLabel").grid(
                row=2, column=0, sticky="e", pady=10, padx=(0, 15))
                
            self._entry_valor = ttk.Entry(container, font=("Segoe UI", 11), width=24)
            self._entry_valor.grid(row=2, column=1, sticky="w", pady=10)
            self._entry_valor.bind("<KeyRelease>", self._calcular_quantidade)

            self._label_quantidade = ttk.Label(container, text="", style="Info.TLabel")
            self._label_quantidade.grid(row=2, column=2, sticky="w", padx=(15, 0))

            ttk.Label(container, text="Preço Unitário:", style="Padrao.TLabel").grid(
                row=3, column=0, sticky="e", pady=10, padx=(0, 15))
                
            self._entry_preco = ttk.Entry(container, font=("Segoe UI", 11), width=24)
            self._entry_preco.grid(row=3, column=1, sticky="w", pady=10)
            self._entry_preco.bind("<KeyRelease>", self._calcular_quantidade)

            ttk.Button(
                container, text="Usar Preço Atual", 
                command=self._usar_preco_atual,
                style="Acao.TButton", cursor="hand2",
            ).grid(row=3, column=2, sticky="w", padx=(15, 0), pady=10)

            self._frame_venda = ttk.Frame(container)
            self._frame_venda.grid(row=4, column=0, columnspan=3, pady=(15, 0))

            self._label_saldo_venda = ttk.Label(
                self._frame_venda, text="", style="Destaque.TLabel")
            self._label_saldo_venda.grid(row=0, column=0, sticky="w")

            self._btn_vender_tudo = ttk.Button(
                self._frame_venda, text="Vender Tudo", 
                command=self._vender_tudo, style="Acao.TButton", cursor="hand2")
            self._btn_vender_tudo.grid(row=0, column=1, sticky="w", padx=(15, 0))

            self._frame_venda.grid_remove()

    def _ao_mudar_selecao(self, event=None) -> None:
        self._ao_selecionar_moeda()
        self._atualizar_interface_venda()

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
            self._entry_preco.config(state="normal")
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
                
                self._frame_venda.grid() 
            except Exception as e:
                logger.error(f"Erro ao buscar saldo para venda: {e}")
                self._frame_venda.grid_remove()
        else:
            self._frame_venda.grid_remove()

    def _vender_tudo(self) -> None:
        moeda = self._combo_moeda.get()
        if not moeda or moeda == "USDT":
            messagebox.showwarning("Ação inválida", "Selecione uma criptomoeda para vender.")
            return

        operacoes = self._data_manager.carregar_operacoes()
        portfolio = self._engine.calcular_portfolio(
            operacoes, self._price_manager.precos_cache)

        saldo = portfolio.get(moeda, {}).get("quantidade_final", 0)
        if saldo < 1e-9:
            messagebox.showinfo("Saldo Insuficiente", f"Você não possui saldo de {moeda} para vender.")
            return

        preco_atual = self._price_manager.get_preco(moeda)
        if not preco_atual or preco_atual <= 0:
            messagebox.showerror("Erro", f"Não foi possível obter o preço atual de {moeda}.")
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
            moeda = self._combo_moeda.get()
            if valor > 0 and preco > 0:
                if moeda == "USDT":
                    qtd   = valor
                    texto = f"= {qtd:.2f} USDT (taxa: R${preco:.4f})"
                else:
                    qtd   = valor / preco
                    texto = f"≈ {qtd:.6f} unidades"
                self._label_quantidade.config(text=texto)
            else:
                self._label_quantidade.config(text="")
        except (ValueError, ZeroDivisionError):
            self._label_quantidade.config(text="")

    def _usar_preco_atual(self) -> None:
        moeda = self._combo_moeda.get()
        if moeda == "USDT":
            preco_brl = self._price_manager.preco_brl
            if preco_brl and preco_brl > 1.1:
                taxa = f"{preco_brl:.4f}"
            else:
                messagebox.showwarning("Aviso", "Cotação BRL indisponível. Atualize os preços primeiro.")
                taxa = "1.000000"
            self._entry_preco.config(state="normal")
            self._entry_preco.delete(0, tk.END)
            self._entry_preco.insert(0, taxa)
            self._entry_preco.config(state="normal")
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
                
            taxa_brl  = self._price_manager.preco_brl or 0.0

            if moeda == 'USDT':
                quantidade = valor          
            else:
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
                         float(preco), float(quantidade), taxa_brl]
                         

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
        self._combo_moeda.set('')
        self._combo_tipo.set('Compra')
        self._entry_valor.delete(0, tk.END)
        self._entry_preco.config(state="normal")
        self._entry_preco.delete(0, tk.END)
        self._label_quantidade.config(text="")
        self._label_preco_atual.config(text="")
        self._frame_venda.grid_remove() 


    def atualizar_lista_moedas(self, novas_moedas: list) -> None:
            """Atualiza o Combobox com a nova lista de moedas em tempo real."""
            self._moedas = novas_moedas
            self._combo_moeda.config(values=self._moedas)
            
            moeda_atual = self._combo_moeda.get()
            if moeda_atual and moeda_atual not in self._moedas:
                self._combo_moeda.set('')
                self._label_preco_atual.config(text="")
                self._label_quantidade.config(text="")