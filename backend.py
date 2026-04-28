from pathlib import Path
import csv
import os
from typing import Dict, List
from collections import defaultdict
import logging
from decimal import Decimal, InvalidOperation
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    import ccxt
    CCXT_AVAILABLE = True
except ImportError:
    CCXT_AVAILABLE = False
    logger.warning("A biblioteca 'ccxt' não está instalizada. Os preços das moedas não serão atualizados.")
    print("Para instalar, execute: pip install ccxt")

class DataManager:
    def __init__(self, arquivo_csv: str = "meu_diario_operacoes.csv"):
        raiz_projeto = Path(__file__).parent.resolve()
        self.arquivo_csv = raiz_projeto / arquivo_csv
        self.headers = ['Data', 'Moeda', 'Operacao', 'Valor_USDT', 'Preco', 'Quantidade', 'Taxa_BRL']

    def criar_arquivo_se_necessario(self):
        if not os.path.exists(self.arquivo_csv):
            try:
                with open(self.arquivo_csv, 'w', newline='', encoding='utf-8') as f:
                    csv.writer(f).writerow(self.headers)
                logger.info(f"Arquivo {self.arquivo_csv} criado com sucesso")
            except Exception as e:
                logger.error(f"Erro ao criar arquivo: {e}")
                raise

    def carregar_operacoes(self) -> List[Dict]:
        operacoes_validas = []
        try:
            with open(self.arquivo_csv, mode='r', encoding='utf-8') as arquivo_csv:
                reader = csv.DictReader(arquivo_csv)
                for numero_linha, linha in enumerate(reader, start=2):
                    try:
                        campos_obrigatorios = ['Data', 'Moeda', 'Operacao', 'Quantidade', 'Valor_USDT']
                        for campo in campos_obrigatorios:
                            if campo not in linha or not linha[campo]:
                                raise ValueError(f"Campo obrigatório '{campo}' ausente ou vazio.")
                        linha['Quantidade'] = float(linha['Quantidade'])
                        linha['Valor_USDT'] = float(linha['Valor_USDT'])
                        linha['Taxa_BRL']   = float(linha.get('Taxa_BRL') or 0) 
                        if linha['Operacao'].lower() not in ['compra', 'venda']:
                            raise ValueError(f"Operação inválida: {linha['Operacao']}")
                        operacoes_validas.append(linha)
                    except Exception as e:
                        logger.warning(f"Linha {numero_linha} inválida e ignorada no arquivo '{self.arquivo_csv}'. Erro: {e}. Conteúdo: {linha}")
                        continue
        except FileNotFoundError:
            return []
        except Exception as e:
            logger.error(f"Ocorreu um erro inesperado ao ler o arquivo '{self.arquivo_csv}': {e}")
            return []
        return operacoes_validas

    def excluir_operacao(self, indice: int) -> bool:
        try:
            operacoes = self.carregar_operacoes()
            if indice < 0 or indice >= len(operacoes):
                return False
            del operacoes[indice]
            with open(self.arquivo_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.headers)
                writer.writeheader()
                writer.writerows(operacoes)
            return True
        except Exception as e:
            logger.error(f"Erro ao excluir operação: {e}")
            return False

    def atualizar_operacao(self, indice: int, nova_operacao: Dict) -> bool:
        try:
            operacoes = self.carregar_operacoes()
            if indice < 0 or indice >= len(operacoes):
                return False
            operacoes[indice] = nova_operacao
            with open(self.arquivo_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.headers)
                writer.writeheader()
                writer.writerows(operacoes)
            return True
        except Exception as e:
            logger.error(f"Erro ao atualizar operação: {e}")
            return False

    def _validar_operacao(self, op: Dict) -> Dict | None:
        try:
            return {
                'Data': op['Data'],
                'Moeda': op['Moeda'].upper().strip(),
                'Operacao': op['Operacao'].lower().strip(),
                'Valor_USDT': float(op['Valor_USDT']),
                'Preco': float(op['Preco']),
                'Quantidade': float(op['Quantidade'])
            }
        except (ValueError, KeyError) as e:
            logger.warning(f"Dados inválidos na operação: {e}")
            return None

    def salvar_operacao(self, operacao: List) -> bool:
        try:
            self.criar_arquivo_se_necessario()
            with open(self.arquivo_csv, 'a', newline='', encoding='utf-8') as f:
                csv.writer(f).writerow(operacao)
            logger.info("Operação salva com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar operação: {e}")
            return False


class PriceManager:
    def __init__(self, exchange_name: str = 'binance'):
        self.exchange = None
        self.precos_cache = {}
        self.ultima_atualizacao = None
        self.preco_brl = 0.0
        self.setup_exchange(exchange_name)

    def setup_exchange(self, exchange_name: str):
        if not CCXT_AVAILABLE:
            return
        try:
            if exchange_name.lower() == 'binance':
                self.exchange = ccxt.binance({
                    'rateLimit': 1200,
                    'enableRateLimit': True,
                    'timeout': 10000
                })
            logger.info(f"Exchange {exchange_name} configurada com sucesso")
        except Exception as e:
            logger.error(f"Erro ao configurar exchange {exchange_name}: {e}")

    def atualizar_precos(self, moedas: List[str]) -> bool:
        if not self.exchange:
            return False
        todos_sucesso = True
        for moeda in moedas:
            if moeda == 'USDT':
                self.precos_cache['USDT'] = 1.0
                continue
            try:
                ticker = self.exchange.fetch_ticker(f'{moeda}/USDT')
                last_price = ticker.get('last')
                if last_price is not None:
                    self.precos_cache[moeda] = float(last_price)
                else:
                    logger.warning(f"Preço 'last' ausente no ticker de {moeda}, mantendo o preço antigo em cache se existir.")
                    todos_sucesso = False
            except Exception as e:
                logger.warning(f"Falha na comunicação ao buscar preço de {moeda}: {e}")
                todos_sucesso = False
        try:
            ticker_brl = self.exchange.fetch_ticker('USDT/BRL')
            last_price_brl = ticker_brl.get('last')
            if last_price_brl is not None:
                self.preco_brl = float(last_price_brl)
                logger.info(f"Preço USDT/BRL atualizado: R$ {self.preco_brl:.2f}")
            else:
                logger.warning("Preço 'last' ausente no ticker de USDT/BRL.")
                todos_sucesso = False
        except Exception as e:
            logger.warning(f"Falha na comunicação ao buscar preço de USDT/BRL: {e}")
            todos_sucesso = False
        if todos_sucesso:
            self.ultima_atualizacao = datetime.now()
            logger.info("Todos os preços foram atualizados com sucesso.")
        return todos_sucesso

    def get_preco(self, moeda: str) -> float | None:
        return self.precos_cache.get(moeda)


class AnalysisEngine:
    @staticmethod
    def calcular_portfolio(operacoes: List[Dict], precos_atuais: Dict[str, float]) -> Dict:
        if not operacoes:
            return {}
        saldo_info_usdt = AnalysisEngine.calcular_saldo_usdt(operacoes)
        saldo_caixa_usdt = saldo_info_usdt['saldo_atual']
        ops_por_moeda = defaultdict(list)
        for op in sorted(operacoes, key=lambda x: x['Data']):
            if op['Moeda'] == 'USDT':
                continue
            ops_por_moeda[op['Moeda']].append(op)
        resultado = {}
        totais = {
            'investido_liquido': 0,
            'realizado': 0,
            'nao_realizado': 0,
            'valor_atual': 0
        }
        for moeda, ops in ops_por_moeda.items():
            analise_moeda = AnalysisEngine._analisar_moeda(ops, precos_atuais.get(moeda, 0))
            if analise_moeda.get('valor_atual_posicao', 0) > 0.01 or abs(analise_moeda.get('lucro_realizado', 0)) > 0.01:
                resultado[moeda] = analise_moeda
                totais['investido_liquido'] += analise_moeda['custo_posicao_final']
                totais['realizado'] += analise_moeda['lucro_realizado']
                totais['nao_realizado'] += analise_moeda['lucro_nao_realizado']
                totais['valor_atual'] += analise_moeda['valor_atual_posicao']
        totais['valor_atual'] += saldo_caixa_usdt
        if saldo_caixa_usdt > 0.01:
            resultado['USDT (Caixa)'] = {
                'quantidade_final': saldo_caixa_usdt,
                'valor_atual_posicao': saldo_caixa_usdt,
                'operacoes': [], 'lucro_realizado': 0, 'lucro_nao_realizado': 0, 'lucro_total': 0
            }
        resultado['totais'] = totais
        return resultado

    @staticmethod
    def calcular_saldo_usdt(operacoes: List[Dict]) -> Dict:
        saldo_usdt = Decimal('0')
        historico_movimentacao = []
        for op in sorted(operacoes, key=lambda x: x['Data']):
            valor_usdt = Decimal(str(op['Valor_USDT']))
            moeda = op['Moeda']
            tipo = op['Operacao']
            if moeda == 'USDT':
                if tipo == 'compra':
                    saldo_usdt += valor_usdt
                    historico_movimentacao.append({
                        'data': op['Data'], 'tipo': 'deposito_usdt', 'valor': float(valor_usdt),
                        'saldo_apos': float(saldo_usdt), 'descricao': f"Depósito de ${float(valor_usdt):,.2f} USDT"
                    })
                elif tipo == 'venda':
                    saldo_usdt -= valor_usdt
                    historico_movimentacao.append({
                        'data': op['Data'], 'tipo': 'saque_usdt', 'valor': float(valor_usdt),
                        'saldo_apos': float(saldo_usdt), 'descricao': f"Saque de ${float(valor_usdt):,.2f} USDT"
                    })
            else:
                if tipo == 'compra':
                    saldo_usdt -= valor_usdt
                    historico_movimentacao.append({
                        'data': op['Data'], 'tipo': 'compra_crypto', 'moeda': moeda, 'valor': float(valor_usdt),
                        'saldo_apos': float(saldo_usdt), 'descricao': f"Compra {moeda}: -${float(valor_usdt):,.2f} USDT"
                    })
                elif tipo == 'venda':
                    saldo_usdt += valor_usdt
                    historico_movimentacao.append({
                        'data': op['Data'], 'tipo': 'venda_crypto', 'moeda': moeda, 'valor': float(valor_usdt),
                        'saldo_apos': float(saldo_usdt), 'descricao': f"Venda {moeda}: +${float(valor_usdt):,.2f} USDT"
                    })
        return {
            'saldo_atual': float(saldo_usdt),
            'historico': historico_movimentacao
        }

    @staticmethod
    def validar_saldo_suficiente(operacoes: List[Dict], nova_compra_valor: float) -> Dict:
        saldo_info = AnalysisEngine.calcular_saldo_usdt(operacoes)
        saldo_atual = saldo_info['saldo_atual']
        return {
            'saldo_suficiente': saldo_atual >= nova_compra_valor,
            'saldo_atual': saldo_atual,
            'valor_necessario': nova_compra_valor,
            'diferenca': saldo_atual - nova_compra_valor
        }

    @staticmethod
    def calcular_distribuicao_portfolio(operacoes: List[Dict], precos_atuais: Dict[str, float]) -> Dict:
        if not operacoes:
            return {'distribuicao': {}, 'total_valor_portfolio': 0}
        saldo_info = AnalysisEngine.calcular_saldo_usdt(operacoes)
        saldo_usdt = saldo_info['saldo_atual']
        ops_por_moeda = defaultdict(list)
        for op in sorted(operacoes, key=lambda x: x['Data']):
            if op['Moeda'] == 'USDT':
                continue
            ops_por_moeda[op['Moeda']].append(op)
        distribuicao = {}
        total_valor_crypto = 0
        for moeda, ops in ops_por_moeda.items():
            analise = AnalysisEngine._analisar_moeda(ops, precos_atuais.get(moeda, 0))
            quantidade_final = analise.get('quantidade_final', 0)
            valor_de_mercado = analise.get('valor_atual_posicao', 0)
            if valor_de_mercado > 0.01:
                distribuicao[moeda] = {
                    'valor_atual': valor_de_mercado,
                    'quantidade': quantidade_final
                }
                total_valor_crypto += valor_de_mercado
        valor_total_portfolio = total_valor_crypto + saldo_usdt
        if saldo_usdt > 0.01:
            distribuicao['USDT'] = {
                'valor_atual': saldo_usdt,
                'quantidade': saldo_usdt
            }
        for moeda in distribuicao:
            if valor_total_portfolio > 0:
                distribuicao[moeda]['percentual'] = (distribuicao[moeda]['valor_atual'] / valor_total_portfolio) * 100
            else:
                distribuicao[moeda]['percentual'] = 0
        return {
            'distribuicao': distribuicao,
            'total_investido': total_valor_crypto
        }

    @staticmethod
    def _analisar_moeda(ops: List[Dict], preco_atual: float) -> Dict:
        custo_total = Decimal('0')
        quantidade_total = Decimal('0')
        lucro_realizado = Decimal('0')
        pmc = Decimal('0')
        operacoes_processadas = []
        for op in ops:
            valor = Decimal(str(op['Valor_USDT']))
            preco = Decimal(str(op['Preco']))
            qtd = Decimal(str(op['Quantidade']))
            if op['Operacao'] == 'compra':
                custo_total += valor
                quantidade_total += qtd
                pmc = custo_total / quantidade_total if quantidade_total > 0 else Decimal('0')
                operacoes_processadas.append({
                    'tipo': 'compra', 'data': op['Data'], 'quantidade': float(qtd),
                    'preco': float(preco), 'valor': float(valor), 'pmc_apos': float(pmc)
                })
            elif op['Operacao'] == 'venda':
                if quantidade_total <= 0 or pmc <= 0:
                    operacoes_processadas.append({
                        'tipo': 'venda', 'data': op['Data'], 'quantidade': float(qtd),
                        'preco': float(preco), 'valor': float(valor), 'erro': 'Venda sem posição prévia'
                    })
                    continue
                custo_da_venda = qtd * pmc
                lucro_venda = valor - custo_da_venda
                lucro_realizado += lucro_venda
                custo_total -= custo_da_venda
                quantidade_total -= qtd
                operacoes_processadas.append({
                    'tipo': 'venda', 'data': op['Data'], 'quantidade': float(qtd),
                    'preco': float(preco), 'valor': float(valor), 'lucro': float(lucro_venda)
                })
        qtd_final = float(quantidade_total)
        custo_final = float(custo_total) if quantidade_total > Decimal('1e-9') else 0
        valor_atual = qtd_final * preco_atual if preco_atual > 0 else 0
        lucro_nao_realizado = valor_atual - custo_final if qtd_final > 1e-9 else 0
        return {
            'operacoes': operacoes_processadas, 'quantidade_final': qtd_final,
            'pmc_final': float(pmc), 'custo_posicao_final': custo_final,
            'valor_atual_posicao': valor_atual, 'lucro_realizado': float(lucro_realizado),
            'lucro_nao_realizado': lucro_nao_realizado, 'lucro_total': float(lucro_realizado) + lucro_nao_realizado,
            'preco_de_mercado': preco_atual
        }


    @staticmethod
    def calcular_pl_usdt_brl(operacoes: List[Dict], preco_brl_atual: float) -> Dict | None:
        if preco_brl_atual <= 0:
            return None

        custo_brl       = Decimal('0')
        quantidade_usdt = Decimal('0')
        lucro_realizado = Decimal('0')
        pmc_brl         = Decimal('0')
        ops_com_taxa    = 0

        for op in sorted(operacoes, key=lambda x: x['Data']):
            taxa_brl = Decimal(str(op.get('Taxa_BRL') or 0))
            tipo     = op['Operacao']
            moeda    = op['Moeda']
            valor    = Decimal(str(op['Valor_USDT']))

            if taxa_brl <= Decimal('1.1'):
                continue  

            ops_com_taxa += 1

            if moeda == 'USDT':
                qtd = Decimal(str(op['Quantidade']))
                if tipo == 'compra':
                    custo_brl       += qtd * taxa_brl
                    quantidade_usdt += qtd
                    pmc_brl = custo_brl / quantidade_usdt if quantidade_usdt > 0 else Decimal('0')
                elif tipo == 'venda' and quantidade_usdt > 0 and pmc_brl > 0:
                    custo_venda      = qtd * pmc_brl
                    lucro_realizado += (qtd * taxa_brl) - custo_venda
                    custo_brl       -= custo_venda
                    quantidade_usdt -= qtd
            else:
                if tipo == 'venda':
                    custo_brl       += valor * taxa_brl
                    quantidade_usdt += valor
                    pmc_brl = custo_brl / quantidade_usdt if quantidade_usdt > 0 else Decimal('0')
                elif tipo == 'compra' and quantidade_usdt > 0 and pmc_brl > 0:
                    custo_venda      = valor * pmc_brl
                    lucro_realizado += (valor * taxa_brl) - custo_venda
                    custo_brl       -= custo_venda
                    quantidade_usdt -= valor

        if ops_com_taxa == 0 or quantidade_usdt <= Decimal('1e-9'):
            return None

        qtd_final   = float(quantidade_usdt)
        custo_final = float(custo_brl)
        valor_atual = qtd_final * preco_brl_atual
        pl_nao_real = valor_atual - custo_final

        return {
            'quantidade_usdt':         qtd_final,
            'pmc_brl':                 float(pmc_brl),
            'custo_posicao_brl':       custo_final,
            'valor_atual_brl':         valor_atual,
            'lucro_nao_realizado_brl': pl_nao_real,
            'lucro_realizado_brl':     float(lucro_realizado),
            'lucro_total_brl':         pl_nao_real + float(lucro_realizado),
            'preco_brl_atual':         preco_brl_atual,
        }