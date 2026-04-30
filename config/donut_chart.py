"""
Módulo: donut_chart.py
Descrição: Componente customizado de gráfico Donut (Rosca) para Tkinter.
Possui gerenciamento autônomo de redimensionamento (debounce) para evitar flickering.
"""

import tkinter as tk
import math
from typing import List, Dict, Any, Optional

# Importações de tema (ajuste o path conforme o seu projeto)
from config.tema_cripto import (
    BG_CARD, BG_DEEP, BTC_ORANGE, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED
)

class DonutChart(tk.Canvas):
    def __init__(self, parent: tk.Widget, **kwargs):
        """
        Inicializa o componente do Gráfico Donut.
        :param parent: O widget pai (ex: um Frame ou LabelFrame).
        """
        # Configuração base do Canvas sem bordas
        super().__init__(parent, bg=BG_CARD, highlightthickness=0, **kwargs)
        
        # Estado interno dos dados
        self._dados: List[tuple] = []
        self._cor_map: Dict[str, str] = {}
        
        # Controle para o Debounce (evita milhares de redesenhos ao redimensionar a tela)
        self._draw_job: Optional[str] = None
        
        # Ouve o evento de redimensionamento da própria tela
        self.bind("<Configure>", self._on_resize)

    def atualizar_dados(self, dados: List[tuple], cor_map: Dict[str, str]) -> None:
        """
        Atualiza os dados do gráfico e agenda o redesenho.
        :param dados: Lista de tuplas contendo (moeda, dicionario_com_percentual).
        :param cor_map: Dicionário mapeando a moeda para sua respectiva cor hexadecimal.
        """
        self._dados = dados
        self._cor_map = cor_map
        self._agendar_desenho()

    def limpar(self) -> None:
        """Limpa visualmente o canvas e zera os dados."""
        self._dados = []
        self.delete("all")

    def _on_resize(self, event: tk.Event) -> None:
        """Handler engatilhado quando o Canvas muda de tamanho."""
        self._agendar_desenho()

    def _agendar_desenho(self) -> None:
        """
        Implementa a lógica de Debounce.
        Cancela o desenho pendente (se houver) e agenda um novo. Isso resolve o problema de flickering.
        """
        if self._draw_job is not None:
            self.after_cancel(self._draw_job)
        self._draw_job = self.after(100, self._desenhar)

    def _desenhar(self) -> None:
        """Lógica matemática e de renderização do Gráfico Donut."""
        self.delete("all")
        if not self._dados:
            return

        w, h = self.winfo_width(), self.winfo_height()
        if w < 50 or h < 50:
            return

        # Constantes dimensionais
        cx, cy = w // 2, h // 2
        raio = min(cx, cy) - 2
        furo = int(raio * 0.55)
        inicio = -90.0

        # Desenhar arcos (Fatias da Rosca)
        for moeda, d in self._dados:
            percentual = d.get("percentual", 0)
            grau = (percentual / 100) * 360
            cor = self._cor_map.get(moeda, TEXT_MUTED)
            
            self.create_arc(
                cx - raio, cy - raio, cx + raio, cy + raio,
                start=inicio, extent=grau, fill=cor, outline=BG_CARD, width=2
            )

            # Labels sobre os arcos (Apenas para fatias maiores que 3%)
            if percentual >= 3.0:
                self._desenhar_label_arco(cx, cy, raio, furo, inicio, grau, moeda)

            inicio += grau

        # Desenhar o "furo" da rosca (Centro)
        self.create_oval(cx - furo, cy - furo, cx + furo, cy + furo, fill=BG_CARD, outline=BG_CARD)
        
        # Textos Centrais
        self.create_text(cx, cy - 10, text=str(len(self._dados)), font=("Segoe UI", 18, "bold"), fill=BTC_ORANGE)
        self.create_text(cx, cy + 12, text="ativos", font=("Segoe UI", 10), fill=TEXT_SECONDARY)

        # Desenhar a Legenda Lateral
        self._desenhar_legenda(h)

    def _desenhar_label_arco(self, cx: int, cy: int, raio: int, furo: int, inicio: float, grau: float, texto: str) -> None:
        """Calcula a geometria e rotaciona o texto em cima da fatia do donut."""
        ang_rad = math.radians(inicio + grau / 2)
        raio_txt = furo + (raio - furo) / 2
        tx = cx + raio_txt * math.cos(ang_rad)
        ty = cy - raio_txt * math.sin(ang_rad)

        angulo_texto = math.degrees(math.atan2(-(ty - cy), tx - cx))
        if angulo_texto < -90:
            angulo_texto += 180
        elif angulo_texto > 90:
            angulo_texto -= 180

        self.create_text(tx, ty, text=texto, font=("Segoe UI", 9, "bold"), fill=BG_DEEP, angle=angulo_texto)

    def _desenhar_legenda(self, max_height: int) -> None:
        """Desenha a legenda no canto superior esquerdo."""
        leg_y = 15
        for moeda, d in self._dados:
            cor = self._cor_map.get(moeda, TEXT_MUTED)
            percentual = d.get("percentual", 0)
            
            self.create_rectangle(15, leg_y, 25, leg_y + 10, fill=cor, outline="")
            self.create_text(33, leg_y + 5, text=f"{moeda} {percentual:.1f}%", font=("Segoe UI", 9, "bold"), fill=TEXT_PRIMARY, anchor="w")
            
            leg_y += 18
            if leg_y > max_height - 25:
                break