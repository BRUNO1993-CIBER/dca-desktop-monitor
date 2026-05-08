import tkinter as tk
from tkinter import ttk
from config.tema_cripto import (
    BG_DEEP, BG_CARD, BTC_ORANGE,
    CYAN, TEXT_SECONDARY, NEON_GREEN
)

YELLOW     = "#fbbf24"
WHITE      = "#f0f4ff"
BG_SECTION = "#1a2235"

MOEDAS = {
    "BTC": {
        "nome":  "Bitcoin",
        "tipo":  "L1 — Reserva Soberana",
        "criador":        "Satoshi Nakamoto",
        "lancamento":     "Janeiro de 2009",
        "missao":         "Dinheiro eletrônico descentralizado, sem intermediários, resistente à censura.",
        "consenso":       "Proof of Work (SHA-256)",
        "tps":            "~7 TPS nativos / ~1.000.000+ TPS via Lightning Network",
        "tempo_bloco":    "~10 minutos",
        "linguagem_sc":   "Bitcoin Script (não-Turing completo) + Taproot / Schnorr",
        "camada":         "L1 Base — Settlement final e imutável",
        "supply_max":     "21.000.000 BTC (hard cap imutável por protocolo)",
        "supply_circ":    "~19.850.000 BTC (Maio/2026) — ~94% do total já emitido",
        "emissao":        "Deflacionário — recompensa de bloco reduz 50% a cada ~4 anos (Halving)",
        "queima":         "Não há burn formal — escassez garantida pelo código-fonte",
        "inflacao_anual": "~0.4% a.a. pós-Halving de Abril/2024",
        "ranking_mcap":   "#1 global — dominância ~55% (Maio/2026)",
        "pares_liquidos": "BTC/USDT · BTC/USDC · BTC/ETH · BTC/BRL",
        "risco_reg":      "BAIXO — Commodity (CFTC/EUA). ETFs à vista aprovados em +20 países.",
        "descentralizacao":"MUITO ALTA — Hash rate distribuído em +100 países. Nenhum ator >25%.",
        "concentracao":   "Top 10 endereços: ~5% do supply (excluindo wallets de Satoshi)",
        "auditorias":     "Open-source desde 2009. Revisão contínua pela comunidade global.",
        "devs_ativos":    "~1.200 contribuidores (Bitcoin Core, BDK, LDK, Rust-Bitcoin)",
        "ecossistema":    "Lightning Network · Ordinals · Runes · Taproot Assets · BitVM · Fedimint",
        "parcerias_inst": "BlackRock (IBIT) · Fidelity (FBTC) · MicroStrategy (+500k BTC) · El Salvador (moeda legal)",
        "casos_uso":      "Reserva de valor institucional · Pagamentos P2P · Colateral DeFi · Remessas globais",
        "ath":            "~$126.000 (OUTUBRO/2026)",
        "maior_queda":    "-83% (Dez/2017→Dez/2018) · -77% (Nov/2021→Nov/2022)",
        "eventos_chave":  "Halving #4 (Abr/2024) · ETFs aprovados EUA (Jan/2024) · ATH $109k (Jan/2025)",
        "roadmap":        "BitVM (smart contracts sem fork) · Silent Payments (privacidade) · Escalabilidade via Lightning.",
    },
    "ETH": {
        "nome":  "Ethereum",
        "tipo":  "L1 — Camada de Liquidação Global",
        "criador":        "Vitalik Buterin · Gavin Wood · Joseph Lubin",
        "lancamento":     "Julho de 2015",
        "missao":         "Plataforma global de contratos inteligentes para a nova economia financeira descentralizada.",
        "consenso":       "Proof of Stake (Casper FFG + LMD-GHOST) desde Set/2022",
        "tps":            "~30 TPS (L1) · >500.000 TPS agregados via L2s (Arbitrum, Base, Optimism)",
        "tempo_bloco":    "~12 segundos",
        "linguagem_sc":   "Solidity · Vyper · Huff · Yul",
        "camada":         "L1 Settlement — Backbone de todas as redes L2 EVM-compatíveis",
        "supply_max":     "Sem limite fixo — modelo ultra-sound money (deflacionário em alta demanda)",
        "supply_circ":    "~120.500.000 ETH (Maio/2026) — rede em deflação líquida",
        "emissao":        "EIP-1559: Base Fee queimada por bloco. >4M ETH queimados desde 2021.",
        "queima":         "Automática — Base Fee destruída em cada transação desde Ago/2021",
        "inflacao_anual": "~-0.2% a.a. (deflação líquida com uso intenso de L2s)",
        "ranking_mcap":   "#2 global — dominância ~17% (Maio/2026)",
        "pares_liquidos": "ETH/USDT · ETH/BTC · ETH/USDC · ETH/BNB",
        "risco_reg":      "BAIXO — Reconhecido como commodity pelo CFTC pós-The Merge. ETFs aprovados EUA (Mai/2024).",
        "descentralizacao":"ALTA — >1.100.000 validadores ativos. Nenhum operador >8% do stake.",
        "concentracao":   "Top 10 wallets: ~22% (inclui contratos Lido, ETH Foundation, Coinbase)",
        "auditorias":     "Trail of Bits · OpenZeppelin · Consensys Diligence · Certora · Sigma Prime",
        "devs_ativos":    "~4.500 devs/mês — maior ecossistema de desenvolvimento em blockchain",
        "ecossistema":    "Uniswap · Aave · Lido · EigenLayer · Arbitrum · Base · Optimism · MakerDAO · ENS",
        "parcerias_inst": "BlackRock (BUIDL Fund) · JPMorgan (Onyx) · Franklin Templeton · SWIFT (CCIP pilot)",
        "casos_uso":      "DeFi · RWA Tokenization · NFTs · Restaking · Settlement L2s · Stablecoins institucionais",
        "ath":            "~$4.946 (Agosto/2025)",
        "maior_queda":    "-94% (Jan/2018→Dez/2018)",
        "eventos_chave":  "The Merge PoW→PoS (Set/2022) · EIP-4844/Cancun-Deneb (Mar/2024) · ETFs EUA (Mai/2024) · Pectra (2025)",
        "roadmap":        "The Surge (Danksharding) · The Scourge (anti-MEV) · The Verge (Verkle Trees) · The Purge.",
    },
    "SOL": {
        "nome":  "Solana",
        "tipo":  "L1 — Monolítica de Alto Desempenho",
        "criador":        "Anatoly Yakovenko · Raj Gokal (Solana Labs)",
        "lancamento":     "Março de 2020",
        "missao":         "Blockchain monolítica ultrarrápida para aplicações de consumidor em massa sem fricção de pontes.",
        "consenso":       "Proof of History (PoH) + Tower BFT (variante de PoS)",
        "tps":            "~5.000–8.000 TPS prático · Firedancer: >1.000.000 TPS em testes de rede (2025)",
        "tempo_bloco":    "~400 milissegundos",
        "linguagem_sc":   "Rust · C · C++ (runtime Sealevel — execução paralela nativa)",
        "camada":         "L1 Monolítica — sem L2s, escalabilidade horizontal nativa",
        "supply_max":     "Sem limite fixo",
        "supply_circ":    "~475.000.000 SOL (Maio/2026)",
        "emissao":        "Inflacionária decrescente — iniciou 8% a.a., reduz 15%/ano até ~1.5% a.a.",
        "queima":         "50% das taxas de transação queimadas por protocolo",
        "inflacao_anual": "~4% a.a. (2026)",
        "ranking_mcap":   "#5 global (Maio/2026)",
        "pares_liquidos": "SOL/USDT · SOL/USDC · SOL/BTC · SOL/ETH",
        "risco_reg":      "MÉDIO — Histórico FTX superado. Não classificado como security nos EUA (2025).",
        "descentralizacao":"MÉDIA — ~2.000 validadores ativos. Requisito de hardware limita descentralização.",
        "concentracao":   "Top 10 wallets: ~33% (Solana Foundation + VCs iniciais)",
        "auditorias":     "Neodyme · Halborn · OtterSec — auditorias frequentes no ecossistema",
        "devs_ativos":    "~2.500 devs/mês — 3° maior ecossistema de desenvolvimento",
        "ecossistema":    "Jupiter · Raydium · Marinade · Jito · Drift · Tensor · Helius · Pyth Network",
        "parcerias_inst": "Visa (pagamentos USDC on-chain) · Shopify · Google Cloud · Stripe",
        "casos_uso":      "DeFi HFT · Pagamentos de consumidor · NFTs/Gaming · Memecoins · AI on-chain",
        "ath":            "~$295 (Janeiro/2025)",
        "maior_queda":    "-97% (Jan/2018→Dez/2018) · -95% (Nov/2021→Dez/2022 — colapso FTX)",
        "eventos_chave":  "Colapso FTX (Nov/2022) · Firedancer validator lançado (2025) · SOL ETFs aprovados (2025)",
        "roadmap":        "Firedancer (1M TPS) · Attestation Layer · Compressão de estado · AI on-chain nativo.",
    },
    "LINK": {
        "nome":  "Chainlink",
        "tipo":  "Middleware — Oracle Network",
        "criador":        "Sergey Nazarov · Steve Ellis (Chainlink Labs)",
        "lancamento":     "Setembro de 2017",
        "missao":         "Infraestrutura descentralizada de oráculos — conectar blockchains a dados do mundo real.",
        "consenso":       "Não possui blockchain própria — rede de oráculos off-chain com agregação on-chain",
        "tps":            "Não aplicável — serviço de dados, não de transações",
        "tempo_bloco":    "Não aplicável",
        "linguagem_sc":   "Solidity (contratos on-chain) · Go / Node.js (nós de oráculo)",
        "camada":         "Middleware — agnóstico de rede (EVM, Solana, Cosmos, etc.)",
        "supply_max":     "1.000.000.000 LINK (fixo)",
        "supply_circ":    "~638.000.000 LINK (Maio/2026)",
        "emissao":        "Fixo — sem inflação de protocolo. Novos tokens apenas via alocação inicial.",
        "queima":         "Sem mecanismo de burn nativo",
        "inflacao_anual": "~0% (supply fixo)",
        "ranking_mcap":   "#14–#18 global (Maio/2026)",
        "pares_liquidos": "LINK/USDT · LINK/BTC · LINK/ETH · LINK/BNB",
        "risco_reg":      "BAIXO — Classificado como utility token. Sem processo SEC.",
        "descentralizacao":"ALTA — rede de centenas de nós operadores independentes",
        "concentracao":   "Top 10 wallets: ~40% (inclui Chainlink Labs e fundações)",
        "auditorias":     "Trail of Bits · Mixbytes · Sigma Prime",
        "devs_ativos":    "~500 contribuidores — foco em integrações e novos feeds",
        "ecossistema":    "CCIP · Data Feeds · VRF · Automation · Functions · DECO · Proof of Reserve",
        "parcerias_inst": "SWIFT · DTCC · ANZ Bank · Fidelity · BNY Mellon · Google Cloud · AWS",
        "casos_uso":      "Price feeds DeFi · RWA tokenization · Cross-chain (CCIP) · Seguros paramétricos · Loterias on-chain (VRF)",
        "ath":            "~$52,88 (Maio/2021)",
        "maior_queda":    "-91% (Jan/2018→Dez/2018)",
        "eventos_chave":  "Integração SWIFT (2023) · CCIP mainnet (2023) · Staking v0.2 (2024) · Integração DTCC (2024–2025)",
        "roadmap":        "CCIP v2 (velocidade e custo) · Staking expansão · DECO (privacidade) · Interoperabilidade com TradFi.",
    },
    "BNB": {
        "nome":  "BNB (Binance Coin)",
        "tipo":  "CEX Token / L1",
        "criador":        "Changpeng Zhao (CZ) — Binance",
        "lancamento":     "Julho de 2017",
        "missao":         "Token utilitário do ecossistema Binance — taxas, staking e combustível da BNB Chain.",
        "consenso":       "Proof of Staked Authority (PoSA) — 21 validadores ativos na BNB Chain",
        "tps":            "~2.000 TPS (BNB Smart Chain) · ~100M TPS teórico (opBNB L2)",
        "tempo_bloco":    "~3 segundos (BSC)",
        "linguagem_sc":   "Solidity (EVM-compatível)",
        "camada":         "CEX Token + L1 (BNB Smart Chain) + L2 (opBNB) + Greenfield (storage)",
        "supply_max":     "200.000.000 BNB (original) — meta de redução a ~100M via burns",
        "supply_circ":    "~142.000.000 BNB (Maio/2026)",
        "emissao":        "Deflacionário — Auto-Burn trimestral baseado em volume e preço de mercado",
        "queima":         "Auto-Burn trimestral + Real-Time Burn (BEP-95) — >50M BNB queimados desde 2017",
        "inflacao_anual": "Deflação de ~2–4% a.a. via burns contínuos",
        "ranking_mcap":   "#3–#4 global (Maio/2026)",
        "pares_liquidos": "BNB/USDT · BNB/BTC · BNB/ETH · BNB/USDC",
        "risco_reg":      "MÉDIO-ALTO — Acordo SEC/DOJ EUA (2023). CZ cumpriu pena. Operações sob novo compliance.",
        "descentralizacao":"BAIXA — 21 validadores, altamente relacionados à Binance",
        "concentracao":   "Top 10 wallets: ~60% (Binance + CZ + fundações)",
        "auditorias":     "CertiK · PeckShield — auditorias frequentes na BSC",
        "devs_ativos":    "~1.000 devs/mês no ecossistema BNB Chain",
        "ecossistema":    "PancakeSwap · Venus · Lista · opBNB · BNB Greenfield · BNB Beacon Chain",
        "parcerias_inst": "Binance (maior exchange do mundo) · Circle (USDC) · TradingView · Chainlink",
        "casos_uso":      "Desconto de taxas Binance · Gas da BNB Chain · Launchpad · Pagamentos · GameFi",
        "ath":            "~$793 (Dezembro/2024)",
        "maior_queda":    "-92% (Jan/2018→Dez/2018) · -68% (Nov/2021→Nov/2022)",
        "eventos_chave":  "CZ preso/liberado EUA (2023–2024) · ATH $793 (Dez/2024) · opBNB L2 lançado (2023)",
        "roadmap":        "opBNB (escalabilidade L2) · BNB Greenfield (armazenamento descentralizado) · Web3 móvel.",
    },
    "UNI": {
        "nome":  "Uniswap",
        "tipo":  "DEX — Automated Market Maker",
        "criador":        "Hayden Adams (Uniswap Labs)",
        "lancamento":     "Novembro de 2018 (protocolo) · Setembro de 2020 (token UNI)",
        "missao":         "Protocolo de liquidez automatizada descentralizado — a engrenagem do comércio on-chain.",
        "consenso":       "Não possui blockchain própria — contratos on-chain multi-chain",
        "tps":            "Limitado pela chain hospedeira (Ethereum L1 + L2s)",
        "tempo_bloco":    "Não aplicável",
        "linguagem_sc":   "Solidity",
        "camada":         "Aplicação DeFi — Ethereum, Arbitrum, Base, Optimism, Polygon, BNB Chain",
        "supply_max":     "1.000.000.000 UNI",
        "supply_circ":    "~753.000.000 UNI (Maio/2026)",
        "emissao":        "Distribuição gradual via governança — sem inflação nova após suprimento inicial",
        "queima":         "Sem burn nativo de protocolo (Fee Switch debatido em governança)",
        "inflacao_anual": "~2% a.a. (desbloqueios remanescentes de vesting)",
        "ranking_mcap":   "#20–#30 global (Maio/2026)",
        "pares_liquidos": "UNI/USDT · UNI/ETH · UNI/BTC · UNI/USDC",
        "risco_reg":      "MÉDIO — Uniswap Labs recebeu Wells Notice da SEC (2024). Processo em andamento.",
        "descentralizacao":"ALTA — contratos imutáveis. Governança via UNI token.",
        "concentracao":   "Top 10 wallets: ~43% (Uniswap Labs + VCs a16z, Paradigm + fundação)",
        "auditorias":     "Trail of Bits · ABDK · OpenZeppelin",
        "devs_ativos":    "~300 contribuidores — foco em V4 e Unichain",
        "ecossistema":    "Uniswap V4 (Hooks) · Unichain (L2 própria) · Uniswap X (aggregator) · LP NFTs",
        "parcerias_inst": "a16z · Paradigm · Coinbase (Base integração nativa)",
        "casos_uso":      "Swap descentralizado · Provimento de liquidez · Price discovery · Roteamento multi-hop",
        "ath":            "~$44,97 (Maio/2021)",
        "maior_queda":    "-95% (Mai/2021→Jun/2022)",
        "eventos_chave":  "Lançamento V3 (2021) · Wells Notice SEC (2024) · V4 + Unichain lançados (2024–2025)",
        "roadmap":        "Uniswap V4 com Hooks · Unichain (L2 própria) · Uniswap X (melhor execução de ordens).",
    },
    "NEAR": {
        "nome":  "NEAR Protocol",
        "tipo":  "L1 — Chain Abstraction",
        "criador":        "Illia Polosukhin · Alexander Skidanov (NEAR Foundation)",
        "lancamento":     "Outubro de 2020",
        "missao":         "Tornar blockchain invisível ao usuário — abstração total de complexidade técnica e criptográfica.",
        "consenso":       "Nightshade Sharding + Proof of Stake (Doomslug BFT)",
        "tps":            "~100.000 TPS teórico (sharding dinâmico) · ~7.000 TPS prático (Maio/2026)",
        "tempo_bloco":    "~1 segundo (finalidade em ~2 segundos)",
        "linguagem_sc":   "Rust · AssemblyScript (WebAssembly)",
        "camada":         "L1 com sharding nativo — host de agentes AI on-chain",
        "supply_max":     "Sem limite fixo",
        "supply_circ":    "~1.110.000.000 NEAR (Maio/2026)",
        "emissao":        "Inflacionário — 5% a.a. (validadores) com queima de 70% das fees",
        "queima":         "70% das taxas de transação queimadas por protocolo",
        "inflacao_anual": "~3–4% a.a. líquido",
        "ranking_mcap":   "#25–#35 global (Maio/2026)",
        "pares_liquidos": "NEAR/USDT · NEAR/BTC · NEAR/ETH",
        "risco_reg":      "BAIXO — Sem processos regulatórios conhecidos. Foundation suíça.",
        "descentralizacao":"MÉDIA-ALTA — ~300 validadores. Sharding aumenta participação.",
        "concentracao":   "Top 10 wallets: ~38% (NEAR Foundation + VCs iniciais)",
        "auditorias":     "Halborn · Blocksec",
        "devs_ativos":    "~800 devs/mês — crescimento impulsionado por AI agents",
        "ecossistema":    "Aurora (EVM layer) · Ref Finance · Chain Signatures · NEAR AI · Octopus Network",
        "parcerias_inst": "Google Cloud · Pagoda · Proximity Labs · OpenAI (parceria de pesquisa)",
        "casos_uso":      "AI agents on-chain · Chain Abstraction · Aplicações multichain sem bridges · Identidade digital",
        "ath":            "~$20,42 (Janeiro/2022)",
        "maior_queda":    "-97% (Jan/2022→Dez/2022)",
        "eventos_chave":  "Mainnet Phase 2 (2021) · Chain Abstraction lançado (2023) · NEAR AI agents (2024–2025)",
        "roadmap":        "Chain Signatures (multichain nativo) · NEAR AI (agentes autônomos) · Stateless validation.",
    },
    "SUI": {
        "nome":  "Sui",
        "tipo":  "L1 — Execução Paralela (Move VM)",
        "criador":        "Evan Cheng · Adeniyi Abiodun · Sam Blackshear (Mysten Labs / ex-Meta/Diem)",
        "lancamento":     "Maio de 2023",
        "missao":         "Blockchain de nova geração com execução paralela nativa para gaming e apps de consumo em massa.",
        "consenso":       "Proof of Stake (Mysticeti BFT — confirmação sub-segundo)",
        "tps":            "~297.000 TPS teórico · ~12.000 TPS prático (Maio/2026)",
        "tempo_bloco":    "~480 milissegundos (finalidade)",
        "linguagem_sc":   "Move (derivado do Diem/Libra da Meta) — modelo de objetos, não contas",
        "camada":         "L1 independente — compatibilidade EVM via bridge, não nativa",
        "supply_max":     "10.000.000.000 SUI",
        "supply_circ":    "~3.100.000.000 SUI (Maio/2026) — desbloqueios de VC em andamento",
        "emissao":        "Inflacionário — recompensas de staking com desbloqueios contínuos de investidores",
        "queima":         "Sem mecanismo de burn nativo",
        "inflacao_anual": "~8–12% a.a. (impacto dos desbloqueios de VCs — risco estrutural significativo)",
        "ranking_mcap":   "#18–#25 global (Maio/2026)",
        "pares_liquidos": "SUI/USDT · SUI/BTC · SUI/ETH · SUI/USDC",
        "risco_reg":      "BAIXO-MÉDIO — Sem processos. Alta concentração de VC é risco estrutural.",
        "descentralizacao":"BAIXA-MÉDIA — ~100 validadores. Alta concentração institucional.",
        "concentracao":   "Top 10 wallets: ~52% (Mysten Labs + a16z + FTX estate + Binance Labs)",
        "auditorias":     "Trail of Bits · Zellic",
        "devs_ativos":    "~600 devs/mês — crescimento em gaming e NFTs",
        "ecossistema":    "Cetus (DEX) · Turbos · Scallop (lending) · Mysten Labs apps · Sui Name Service",
        "parcerias_inst": "a16z · Coinbase Ventures · Binance Labs",
        "casos_uso":      "Gaming on-chain · NFTs de alto throughput · DeFi paralelo · Ativos digitais corporativos",
        "ath":            "~$5,35 (Janeiro/2025)",
        "maior_queda":    "-78% (Jan/2025→Abr/2026 — pressão de desbloqueios VC)",
        "eventos_chave":  "Mainnet lançamento (Mai/2023) · ATH $5,35 (Jan/2025) · Pressão desbloqueios VC (2025–2026)",
        "roadmap":        "Mysticeti v2 (latência sub-200ms) · zkLogin expansão · Integração apps móveis em massa.",
    },
    "USDC": {
        "nome":  "USD Coin",
        "tipo":  "Stablecoin — Lastreada em USD",
        "criador":        "Circle Internet Financial · Coinbase (Consórcio Centre — dissolvido 2023)",
        "lancamento":     "Setembro de 2018",
        "missao":         "Representação digital 1:1 do dólar americano — transparente, regulamentada e auditada.",
        "consenso":       "Não possui blockchain própria — token ERC-20 / nativo em múltiplas chains",
        "tps":            "Limitado pela chain hospedeira",
        "tempo_bloco":    "Não aplicável",
        "linguagem_sc":   "Solidity (EVM) · nativo em Solana, Avalanche, Base, Arbitrum, Stellar",
        "camada":         "Token multi-chain — Ethereum, Solana, Avalanche, Base, Arbitrum, Polygon, Sui",
        "supply_max":     "Elástico — emitido e resgatado 1:1 com USD real",
        "supply_circ":    "~$62.000.000.000 USDC em circulação (Maio/2026)",
        "emissao":        "Controlada por Circle — emitido via parceiros autorizados",
        "queima":         "Queimado automaticamente no resgate para USD fiat",
        "inflacao_anual": "Não aplicável — preço indexado em $1.00",
        "ranking_mcap":   "#2 stablecoin global (atrás do USDT)",
        "pares_liquidos": "USDC/USDT · USDC/BTC · USDC/ETH — referência de liquidez em DeFi institucional",
        "risco_reg":      "MUITO BAIXO — Regulamentado nos EUA (Money Transmitter). Reservas auditadas mensalmente pela Deloitte.",
        "descentralizacao":"BAIXA — Centralizado (Circle controla emissão e blacklist de endereços)",
        "concentracao":   "Concentração por endereço irrelevante — 1 USDC = 1 USD por protocolo",
        "auditorias":     "Deloitte (reservas mensais) · Grant Thornton (histórico)",
        "devs_ativos":    "Time Circle + comunidade de integradores externos",
        "ecossistema":    "Nativo em 15+ blockchains · CCTP (Cross-Chain Transfer Protocol) · Compound · Aave · Curve",
        "parcerias_inst": "BlackRock (gestão das reservas) · Coinbase · Visa · Stripe · Google Pay",
        "casos_uso":      "Preservação de capital em DeFi · Colateral institucional · Pagamentos corporativos · Remessas",
        "ath":            "Não aplicável — stablecoin com paridade $1.00",
        "maior_queda":    "Despeg mínimo a $0,87 durante crise SVB (Mar/2023) — recuperação em 72h",
        "eventos_chave":  "Lançamento (2018) · Despeg SVB (Mar/2023) · BlackRock reserves (2023) · CCTP multichain (2023–2024)",
        "roadmap":        "CCTP v2 (transferências instantâneas cross-chain) · Integração TradFi · Expansão multi-chain.",
    },
    "USDT": {
        "nome":  "Tether",
        "tipo":  "Stablecoin — Maior Liquidez Global",
        "criador":        "Tether Limited (afiliada à Bitfinex) · Giancarlo Devasini · Jean-Louis van der Velde",
        "lancamento":     "Outubro de 2014 (originalmente 'Realcoin')",
        "missao":         "Dólar digital de máxima liquidez — presente em todas as corretoras e cadeias do mundo.",
        "consenso":       "Não possui blockchain própria — token em +14 blockchains",
        "tps":            "Limitado pela chain hospedeira",
        "tempo_bloco":    "Não aplicável",
        "linguagem_sc":   "Nativo em Tron (TRC-20), Ethereum (ERC-20), Solana, BSC, Avalanche e outras",
        "camada":         "Token multi-chain — Tron detém ~45% do volume, Ethereum ~35%",
        "supply_max":     "Elástico — emitido e resgatado conforme demanda de mercado",
        "supply_circ":    "~$148.000.000.000 USDT em circulação (Maio/2026)",
        "emissao":        "Controlada pela Tether Limited — emissão opaca comparada ao USDC",
        "queima":         "Queimado no resgate para USD — processo menos transparente que concorrentes",
        "inflacao_anual": "Não aplicável — preço indexado em $1.00",
        "ranking_mcap":   "#1 stablecoin global · #3 crypto geral (Maio/2026)",
        "pares_liquidos": "Par de referência de liquidez em 99% das exchanges globais",
        "risco_reg":      "MÉDIO-ALTO — Sem auditoria completa das reservas. Acordo CFTC $41M (2021). Operações offshore.",
        "descentralizacao":"MUITO BAIXA — Centralizado (Tether Limited controla emissão e pode congelar endereços)",
        "concentracao":   "Reservas não auditadas de forma independente e integral",
        "auditorias":     "BDO Italia (attestations trimestrais) — auditoria completa nunca realizada",
        "devs_ativos":    "Time Tether Limited — proprietário fechado",
        "ecossistema":    "Binance · OKX · Bybit · KuCoin · Tron · Ethereum · Solana · Arbitrum",
        "parcerias_inst": "Bitfinex · Exchanges offshore · Mercados emergentes (Sul Global, LATAM, SEA)",
        "casos_uso":      "Par de liquidez primário em corretoras · Remessas Sul Global · Hedge USD em economias inflacionárias",
        "ath":            "Não aplicável — stablecoin com paridade $1.00",
        "maior_queda":    "Despeg histórico a $0.96 (Out/2018) — liquidez profunda mitiga riscos sistêmicos",
        "eventos_chave":  "Lançamento (2014) · Acordo CFTC $41M (2021) · Supply passa $100B (2023) · $148B (Maio/2026)",
        "roadmap":        "Expansão para novas chains · XAUT (ouro tokenizado) · Crescimento em mercados emergentes.",
    },
}

SECOES = [
    ("🧬  IDENTIDADE",   ["criador", "lancamento", "missao"]),
    ("⚙️  TECNOLOGIA",   ["consenso", "tps", "tempo_bloco", "linguagem_sc", "camada"]),
    ("💰  TOKENOMICS",   ["supply_max", "supply_circ", "emissao", "queima", "inflacao_anual"]),
    ("📈  MERCADO",      ["ranking_mcap", "pares_liquidos"]),
    ("🛡️  RISCO",       ["risco_reg", "descentralizacao", "concentracao", "auditorias"]),
    ("🌐  ECOSSISTEMA",  ["devs_ativos", "ecossistema", "parcerias_inst", "casos_uso"]),
    ("📜  HISTÓRICO",    ["ath", "maior_queda", "eventos_chave", "roadmap"]),
]

COR_TIPO = {
    "L1 — Reserva Soberana":                    BTC_ORANGE,
    "L1 — Camada de Liquidação Global":         CYAN,
    "L1 — Monolítica de Alto Desempenho":       NEON_GREEN,
    "Middleware — Oracle Network":               "#a855f7",
    "CEX Token / L1":                            YELLOW,
    "DEX — Automated Market Maker":              "#fb923c",
    "L1 — Chain Abstraction":                    "#f472b6",
    "L1 — Execução Paralela (Move VM)":         "#38bdf8",
    "Stablecoin — Lastreada em USD":             "#4ade80",
    "Stablecoin — Maior Liquidez Global":        "#4ade80",
}


class JanelaEstrategia(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_DEEP)
        self._criar_interface()

    def _criar_interface(self):
        topo = tk.Frame(self, bg=BG_CARD)
        topo.pack(fill="x", padx=20, pady=(20, 0))

        tk.Label(
            topo,
            text="📊 ANÁLISE FUNDAMENTAL DE ATIVOS DIGITAIS",
            font=("Segoe UI", 15, "bold"),
            bg=BG_CARD, fg=BTC_ORANGE, pady=8
        ).pack(fill="x")

        tk.Label(
            topo,
            text="Maio de 2026  ·  Identidade · Tecnologia · Tokenomics · Mercado · Risco · Ecossistema · Histórico",
            font=("Segoe UI", 9, "italic"),
            bg=BG_CARD, fg=TEXT_SECONDARY, pady=4
        ).pack(fill="x")

        tk.Frame(topo, bg=CYAN, height=2).pack(fill="x", padx=10, pady=(4, 0))

        area = tk.Frame(self, bg=BG_DEEP)
        area.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        canvas = tk.Canvas(area, bg=BG_DEEP, highlightthickness=0)
        scrollbar = ttk.Scrollbar(area, orient="vertical", command=canvas.yview)

        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        interior = tk.Frame(canvas, bg=BG_DEEP)
        janela_id = canvas.create_window((0, 0), window=interior, anchor="nw")

        def _ajustar_largura(event):
            canvas.itemconfig(janela_id, width=event.width)

        def _ajustar_scroll(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        canvas.bind("<Configure>", _ajustar_largura)
        interior.bind("<Configure>", _ajustar_scroll)
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        for simbolo, dados in MOEDAS.items():
            self._criar_card(interior, simbolo, dados)

    def _criar_card(self, parent, simbolo, dados):
        cor = COR_TIPO.get(dados["tipo"], CYAN)

        card = tk.Frame(parent, bg=BG_SECTION, highlightthickness=1, highlightbackground=cor)
        card.pack(fill="x", padx=10, pady=8)

        header = tk.Frame(card, bg=BG_SECTION)
        header.pack(fill="x", padx=15, pady=(10, 5))

        tk.Label(
            header, text=simbolo,
            font=("Segoe UI", 14, "bold"), bg=BG_SECTION, fg=cor
        ).pack(side="left")

        tk.Label(
            header, text=f"  {dados['nome']}",
            font=("Segoe UI", 11), bg=BG_SECTION, fg=WHITE
        ).pack(side="left")

        tk.Label(
            header, text=f"  [{dados['tipo']}]",
            font=("Segoe UI", 9, "italic"), bg=BG_SECTION, fg=cor
        ).pack(side="left")

        tk.Frame(card, bg=cor, height=1).pack(fill="x", padx=15)

        corpo = tk.Frame(card, bg=BG_SECTION)
        corpo.pack(fill="x", padx=15, pady=(6, 12))

        for titulo_sec, campos in SECOES:
            sec = tk.Frame(corpo, bg=BG_SECTION)
            sec.pack(fill="x", pady=(8, 2))

            tk.Label(
                sec, text=titulo_sec,
                font=("Segoe UI", 9, "bold"), bg=BG_SECTION, fg=cor
            ).pack(anchor="w")

            for campo in campos:
                valor = dados.get(campo)
                if not valor:
                    continue
                linha = tk.Frame(sec, bg=BG_SECTION)
                linha.pack(fill="x", padx=8, pady=1)

                tk.Label(
                    linha,
                    text=campo.replace("_", " ").upper() + ":",
                    font=("Segoe UI", 8, "bold"),
                    bg=BG_SECTION, fg=TEXT_SECONDARY,
                    width=20, anchor="w"
                ).pack(side="left")

                tk.Label(
                    linha,
                    text=valor,
                    font=("Segoe UI", 9),
                    bg=BG_SECTION, fg=WHITE,
                    anchor="w", justify="left",
                    wraplength=0
                ).pack(side="left", fill="x", expand=True)