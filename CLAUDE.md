# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

```bash
# Activate virtual environment first
source venv/bin/activate   # Linux/macOS
# .\venv\Scripts\activate  # Windows

# Run the app (no console window on Windows due to .pyw extension)
python main.pyw
```

The app requires internet access to fetch live prices from Binance via CCXT. It degrades gracefully if CCXT is missing (prices won't update, but the rest of the UI still loads).

There are no tests or linting commands configured in this project.

## Dependencies

```bash
pip install -r requirements.txt
# requirements.txt: ccxt, ttkthemes, customtkinter
```

## Architecture

The app is a desktop DCA (Dollar-Cost Averaging) portfolio tracker for crypto, built with Tkinter + CustomTkinter. Data is stored locally in `db/meu_diario_operacoes.csv`.

### Startup flow

`main.pyw` → creates a `ThemedTk` (hidden) → spawns `JanelaSplash` → background thread instantiates `DataManager` + `PriceManager` and fetches prices → splash fades out → `PortfolioDCA` is built and the main window is shown.

### Layer separation

| Layer | Location | Responsibility |
|---|---|---|
| **Backend** | `backend/backend.py` | `DataManager` (CSV CRUD), `PriceManager` (Binance via CCXT), `AnalysisEngine` (portfolio math) |
| **Config** | `config/` | `config.json` (coins, interval, timeout), `tema_cripto.py` (color constants + ttk styles), `carregar_json.py` (config loader), `donut_chart.py` (canvas widget) |
| **GUI** | `gui/` | One `ctk.CTkFrame` subclass per tab, mounted into a `ttk.Notebook` |
| **Entry point** | `main.pyw` | `PortfolioDCA` class wires all tabs to shared managers and drives the auto-refresh countdown |

### Key classes

- **`DataManager`** — reads/writes `db/meu_diario_operacoes.csv`. CSV columns: `Data, Moeda, Operacao, Valor_USDT, Preco, Quantidade, Taxa_BRL`.
- **`PriceManager`** — wraps CCXT Binance, caches prices in `precos_cache` dict, also tracks `preco_brl` (USDT/BRL rate).
- **`AnalysisEngine`** — pure static methods; uses `Decimal` for all money math. Key methods: `calcular_portfolio`, `calcular_saldo_usdt`, `calcular_pl_usdt_brl`, `calcular_distribuicao_portfolio`.
- **`PortfolioDCA`** — main controller; runs auto-refresh on a countdown timer using `janela.after()`. Price fetches run in a daemon thread; UI updates are marshalled back via `janela.after(0, ...)`.
- **`JanelaRegistro`** — split into `JanelaRegistroUI` (pure layout, `gui/janela_registro_ui.py`) and `JanelaRegistroLogica` (business logic, `gui/janela_registro_logica.py`). Logic class inherits from UI class.

### GUI tabs (notebook order)

1. `JanelaDistribuicao` — Dashboard with donut chart, summary cards, and per-asset detail table. Has USD/BRL toggle.
2. `JanelaCaixa` — USDT cash position and P/L in BRL.
3. `JanelaRegistro` — Register buy/sell operations.
4. `JanelaEdicao` — Transaction history with edit/delete.
5. `JanelaMoedas` — Add/remove tracked coins (persisted to `config.json`).
6. `JanelaEstrategia` — Static institutional thesis text.

### Configuration

`config/config.json` controls which coins are tracked (`moedas`), the exchange (`binance`), auto-refresh interval in seconds (`intervalo_atualizacao`), and splash screen timeout (`splash_timeout`). Changes to the coin list from the UI are written back to this file by `JanelaMoedas`.

### Thread safety

All background work (price fetching) runs in daemon threads. Any resulting UI update must go through `janela.after(0, callback)` — never update Tkinter widgets from a non-main thread directly.

### Fonts

`janela_distribuicao.py` and other GUI files select `"Segoe UI"` on Windows and `"Ubuntu"` on Linux using `platform.system()`. Keep this pattern when adding new windows.
