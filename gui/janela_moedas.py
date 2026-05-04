# gui/janela_moedas.py — Gerenciamento de Moedas | Add, remover, reordenar e salvar em config.json.

import json
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from config.tema_cripto import (
    BG_DEEP, BG_CARD, BG_INPUT,
    BTC_ORANGE, NEON_GREEN, CYAN,
    TEXT_SECONDARY,
)
from config.carregar_json import _get_config_path

logger = logging.getLogger(__name__)


TEXT_PRIMARY  = "#e8eaf6"
RED_ALERT     = "#ff4d4d"
YELLOW_WARN   = "#e3b341"
BORDER_SUBTLE = "#2a2d3e"


class JanelaMoedas(tk.Frame):


    def __init__(self, parent, on_moedas_alteradas=None):
        super().__init__(parent, bg=BG_DEEP)
        self._on_moedas_alteradas = on_moedas_alteradas
        self._moedas: list[str] = []
        self._alterado = False

        self._construir_interface()
        self._carregar_moedas()



    def _construir_interface(self):
        header = tk.Frame(self, bg=BG_DEEP)
        header.pack(fill="x", padx=24, pady=(20, 0))

        tk.Label(
            header,
            text="⚙  Gerenciar Moedas",
            font=("Segoe UI", 16, "bold"),
            bg=BG_DEEP, fg=BTC_ORANGE,
        ).pack(side="left")

        self._lbl_status = tk.Label(
            header, text="",
            font=("Segoe UI", 10, "italic"),
            bg=BG_DEEP, fg=NEON_GREEN,
        )
        self._lbl_status.pack(side="right", padx=8)

        tk.Frame(self, bg=BTC_ORANGE, height=1).pack(fill="x", padx=24, pady=(8, 16))

        corpo = tk.Frame(self, bg=BG_DEEP)
        corpo.pack(fill="both", expand=True, padx=24, pady=0)
        corpo.columnconfigure(0, weight=3)
        corpo.columnconfigure(1, weight=0)
        corpo.columnconfigure(2, weight=2)
        corpo.rowconfigure(0, weight=1)

        self._construir_painel_lista(corpo)
        self._construir_painel_controles(corpo)
        self._construir_painel_add(corpo)

        self._construir_rodape()

    def _construir_painel_lista(self, parent):
        card = tk.Frame(parent, bg=BG_CARD,
                        highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=0)
        card.rowconfigure(1, weight=1)
        card.columnconfigure(0, weight=1)

        tk.Label(
            card, text="Moedas Ativas",
            font=("Segoe UI", 11, "bold"),
            bg=BG_CARD, fg=TEXT_PRIMARY, pady=10,
        ).grid(row=0, column=0, columnspan=2, sticky="ew")

        tk.Frame(card, bg=BORDER_SUBTLE, height=1).grid(
            row=0, column=0, columnspan=2, sticky="ew", pady=(36, 0)
        )

        lista_frame = tk.Frame(card, bg=BG_CARD)
        lista_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        lista_frame.rowconfigure(0, weight=1)
        lista_frame.columnconfigure(0, weight=1)

        scrollbar = ttk.Scrollbar(lista_frame, orient="vertical")
        self._listbox = tk.Listbox(
            lista_frame,
            yscrollcommand=scrollbar.set,
            bg=BG_INPUT, fg=TEXT_PRIMARY,
            selectbackground=BTC_ORANGE, selectforeground="#000",
            font=("Segoe UI", 12, "bold"),
            relief="flat", bd=0,
            activestyle="none",
            highlightthickness=0,
        )
        scrollbar.config(command=self._listbox.yview)
        self._listbox.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self._lbl_total = tk.Label(
            card, text="",
            font=("Segoe UI", 9),
            bg=BG_CARD, fg=TEXT_SECONDARY, pady=6,
        )
        self._lbl_total.grid(row=2, column=0, sticky="ew")

    def _construir_painel_controles(self, parent):
        """Botões de reordenar e remover (coluna central)."""
        card = tk.Frame(parent, bg=BG_DEEP)
        card.grid(row=0, column=1, sticky="ns", padx=6)

        tk.Frame(card, bg=BG_DEEP).pack(expand=True, fill="both")

        botoes = [
            ("▲  Subir",    self._mover_cima,   CYAN),
            ("▼  Descer",   self._mover_baixo,   CYAN),
            ("⤒  Topo",     self._mover_topo,    CYAN),
            ("⤓  Fim",      self._mover_fim,     CYAN),
            ("",            None,                None),  
            ("✕  Remover",  self._remover_moeda, RED_ALERT),
        ]

        for txt, cmd, cor in botoes:
            if cmd is None:
                tk.Frame(card, bg=BG_DEEP, height=14).pack()
                continue
            btn = tk.Button(
                card, text=txt,
                font=("Segoe UI", 9, "bold"),
                bg=BG_CARD, fg=cor,
                activebackground=BTC_ORANGE, activeforeground="#000",
                relief="flat", bd=0, cursor="hand2",
                padx=14, pady=7,
                command=cmd,
            )
            btn.pack(fill="x", pady=2)
            btn.bind("<Enter>", lambda e, b=btn, c=cor: b.config(bg=c, fg="#000"))
            btn.bind("<Leave>", lambda e, b=btn, c=cor: b.config(bg=BG_CARD, fg=c))

        tk.Frame(card, bg=BG_DEEP).pack(expand=True, fill="both")

    def _construir_painel_add(self, parent):
        card = tk.Frame(parent, bg=BG_CARD,
                        highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        card.grid(row=0, column=2, sticky="nsew", padx=(6, 0))

        tk.Label(
            card, text="Adicionar Moeda",
            font=("Segoe UI", 11, "bold"),
            bg=BG_CARD, fg=TEXT_PRIMARY, pady=10,
        ).pack(fill="x")

        tk.Frame(card, bg=BORDER_SUBTLE, height=1).pack(fill="x")

        inner = tk.Frame(card, bg=BG_CARD, padx=20, pady=20)
        inner.pack(fill="both", expand=True)

        tk.Label(
            inner, text="Símbolo da moeda:",
            font=("Segoe UI", 10),
            bg=BG_CARD, fg=TEXT_SECONDARY, anchor="w",
        ).pack(fill="x", pady=(0, 4))

        entry_frame = tk.Frame(inner, bg=BTC_ORANGE, padx=1, pady=1)
        entry_frame.pack(fill="x")

        self._entry_nova = tk.Entry(
            entry_frame,
            font=("Segoe UI", 14, "bold"),
            bg=BG_INPUT, fg=BTC_ORANGE,
            insertbackground=BTC_ORANGE,
            relief="flat", bd=4,
            justify="center",
        )
        self._entry_nova.pack(fill="x")
        self._entry_nova.bind("<Return>", lambda _: self._adicionar_moeda())

        tk.Label(
            inner, text='Ex: "BTC", "ETH", "SOL"',
            font=("Segoe UI", 8, "italic"),
            bg=BG_CARD, fg=TEXT_SECONDARY,
        ).pack(pady=(4, 16))

        tk.Label(
            inner, text="Inserir na posição:",
            font=("Segoe UI", 10),
            bg=BG_CARD, fg=TEXT_SECONDARY, anchor="w",
        ).pack(fill="x", pady=(0, 4))

        self._var_posicao = tk.StringVar(value="Final da lista")
        self._combo_posicao = ttk.Combobox(
            inner,
            textvariable=self._var_posicao,
            state="readonly",
            font=("Segoe UI", 10),
        )
        self._combo_posicao.pack(fill="x", pady=(0, 20))

        btn_add = tk.Button(
            inner, text="＋  Adicionar",
            font=("Segoe UI", 11, "bold"),
            bg=NEON_GREEN, fg="#000",
            activebackground=BTC_ORANGE, activeforeground="#000",
            relief="flat", bd=0, cursor="hand2",
            pady=10,
            command=self._adicionar_moeda,
        )
        btn_add.pack(fill="x")

        tk.Frame(inner, bg=BG_CARD).pack(expand=True, fill="both")
        tk.Label(
            inner,
            text="💡 Apenas moedas disponíveis\nna exchange configurada.",
            font=("Segoe UI", 9, "italic"),
            bg=BG_CARD, fg=TEXT_SECONDARY,
            justify="left",
        ).pack(anchor="w", pady=(16, 0))

    def _construir_rodape(self):
        rodape = tk.Frame(self, bg=BG_DEEP, pady=12)
        rodape.pack(fill="x", padx=24)

        self._btn_salvar = tk.Button(
            rodape,
            text="💾  Salvar e Aplicar",
            font=("Segoe UI", 11, "bold"),
            bg=BTC_ORANGE, fg="#000",
            activebackground=NEON_GREEN, activeforeground="#000",
            relief="flat", bd=0, cursor="hand2",
            padx=24, pady=10,
            command=self._salvar_e_aplicar,
            state="disabled",
        )
        self._btn_salvar.pack(side="right")

        tk.Button(
            rodape,
            text="↺  Descartar alterações",
            font=("Segoe UI", 10),
            bg=BG_CARD, fg=TEXT_SECONDARY,
            activebackground=YELLOW_WARN, activeforeground="#000",
            relief="flat", bd=0, cursor="hand2",
            padx=16, pady=10,
            command=self._descartar,
        ).pack(side="right", padx=(0, 8))


    def _carregar_moedas(self):
        try:
            with _get_config_path().open("r", encoding="utf-8") as f:
                data = json.load(f)
            self._moedas = list(data.get("moedas", []))
        except Exception as e:
            logger.warning(f"Erro ao carregar moedas: {e}")
            self._moedas = []

        self._sync_listbox()
        self._sync_combo_posicao()
        self._marcar_alterado(False)
        self._set_status("Configuração carregada.", CYAN, autoapagar=True)

    def _salvar_e_aplicar(self):
        if not self._moedas:
            messagebox.showwarning("Atenção", "A lista de moedas não pode ficar vazia!")
            return

        try:
            path = _get_config_path()
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            data["moedas"] = self._moedas

            with path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            self._marcar_alterado(False)
            self._set_status(f"✓ Salvo! {len(self._moedas)} moedas ativas.", NEON_GREEN)

            if callable(self._on_moedas_alteradas):
                self._on_moedas_alteradas(list(self._moedas))

        except Exception as e:
            logger.error(f"Erro ao salvar config: {e}")
            messagebox.showerror("Erro", f"Não foi possível salvar:\n{e}")

    def _descartar(self):
        if self._alterado:
            if not messagebox.askyesno("Descartar", "Descartar todas as alterações não salvas?"):
                return
        self._carregar_moedas()

    def _adicionar_moeda(self):
        simbolo = self._entry_nova.get().strip().upper()
        if not simbolo:
            self._set_status("Digite o símbolo da moeda.", YELLOW_WARN, autoapagar=True)
            return
        if simbolo in self._moedas:
            self._set_status(f"{simbolo} já está na lista.", YELLOW_WARN, autoapagar=True)
            return

        pos_txt = self._var_posicao.get()
        if pos_txt == "Final da lista" or pos_txt == "":
            self._moedas.append(simbolo)
            idx = len(self._moedas) - 1
        elif pos_txt == "Início da lista":
            self._moedas.insert(0, simbolo)
            idx = 0
        else:
            try:
                ref = pos_txt.split(" ", 1)[1]
                idx = self._moedas.index(ref) + 1
            except (ValueError, IndexError):
                idx = len(self._moedas)
            self._moedas.insert(idx, simbolo)

        self._entry_nova.delete(0, "end")
        self._sync_listbox()
        self._sync_combo_posicao()
        self._listbox.selection_clear(0, "end")
        self._listbox.selection_set(idx)
        self._listbox.see(idx)
        self._marcar_alterado(True)
        self._set_status(f"＋ {simbolo} adicionado.", NEON_GREEN, autoapagar=True)

    def _remover_moeda(self):
        sel = self._listbox.curselection()
        if not sel:
            self._set_status("Selecione uma moeda para remover.", YELLOW_WARN, autoapagar=True)
            return
        idx = sel[0]
        moeda = self._moedas[idx]
        if not messagebox.askyesno("Remover", f"Remover {moeda} da lista?"):
            return
        self._moedas.pop(idx)
        self._sync_listbox()
        self._sync_combo_posicao()
        novo_idx = min(idx, len(self._moedas) - 1)
        if novo_idx >= 0:
            self._listbox.selection_set(novo_idx)
        self._marcar_alterado(True)
        self._set_status(f"✕ {moeda} removida.", RED_ALERT, autoapagar=True)

    def _mover_cima(self):
        self._mover(-1)

    def _mover_baixo(self):
        self._mover(1)

    def _mover(self, delta: int):
        sel = self._listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        novo = idx + delta
        if novo < 0 or novo >= len(self._moedas):
            return
        self._moedas[idx], self._moedas[novo] = self._moedas[novo], self._moedas[idx]
        self._sync_listbox()
        self._listbox.selection_set(novo)
        self._listbox.see(novo)
        self._marcar_alterado(True)

    def _mover_topo(self):
        sel = self._listbox.curselection()
        if not sel or sel[0] == 0:
            return
        idx = sel[0]
        self._moedas.insert(0, self._moedas.pop(idx))
        self._sync_listbox()
        self._listbox.selection_set(0)
        self._listbox.see(0)
        self._marcar_alterado(True)

    def _mover_fim(self):
        sel = self._listbox.curselection()
        if not sel or sel[0] == len(self._moedas) - 1:
            return
        idx = sel[0]
        self._moedas.append(self._moedas.pop(idx))
        self._sync_listbox()
        fim = len(self._moedas) - 1
        self._listbox.selection_set(fim)
        self._listbox.see(fim)
        self._marcar_alterado(True)

    def _sync_listbox(self):
        self._listbox.delete(0, "end")
        for i, m in enumerate(self._moedas, 1):
            self._listbox.insert("end", f"  {i:>2}.  {m}")
        self._lbl_total.config(text=f"{len(self._moedas)} moeda(s) ativa(s)")

    def _sync_combo_posicao(self):
        opcoes = ["Início da lista"] + [f"Após {m}" for m in self._moedas] + ["Final da lista"]
        self._combo_posicao["values"] = opcoes
        self._var_posicao.set("Final da lista")

    def _marcar_alterado(self, estado: bool):
        self._alterado = estado
        self._btn_salvar.config(state="normal" if estado else "disabled")

    def _set_status(self, msg: str, cor: str = TEXT_SECONDARY, autoapagar: bool = False):
        self._lbl_status.config(text=msg, fg=cor)
        if autoapagar:
            self.after(3000, lambda: self._lbl_status.config(text=""))