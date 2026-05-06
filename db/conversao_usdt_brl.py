import csv
import requests
from datetime import datetime
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

ARQUIVO_ENTRADA = BASE_DIR / "db" / "meu_diario_operacoes.csv"
ARQUIVO_SAIDA = BASE_DIR / "db" / "operacoes_corrigidas.csv"

def buscar_cotacao_binance(data_str):
    try:
        dt = datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S")
        timestamp_ms = int(dt.timestamp() * 1000)
        
        url = f"https://api.binance.com/api/v3/klines?symbol=USDTBRL&interval=1d&startTime={timestamp_ms}&limit=1"
        resposta = requests.get(url)
        dados = resposta.json()
        
        if dados and isinstance(dados, list) and len(dados) > 0:
            preco_abertura = float(dados[0][1])
            return round(preco_abertura, 4)
    except Exception:
        return None
    
    return None

def processar_csv():
    linhas_corrigidas = []
    
    with open(ARQUIVO_ENTRADA, mode='r', encoding='utf-8') as file:
        leitor = csv.DictReader(file)
        cabecalho = leitor.fieldnames
        
        for linha in leitor:
            taxa_atual = float(linha.get('Taxa_BRL', 0))
            
            if taxa_atual == 0.0:
                data_op = linha['Data']
                nova_taxa = buscar_cotacao_binance(data_op)
                
                if nova_taxa:
                    linha['Taxa_BRL'] = str(nova_taxa)
                
                time.sleep(0.5)
            
            linhas_corrigidas.append(linha)
            
    with open(ARQUIVO_SAIDA, mode='w', encoding='utf-8', newline='') as file:
        escritor = csv.DictWriter(file, fieldnames=cabecalho)
        escritor.writeheader()
        escritor.writerows(linhas_corrigidas)

if __name__ == "__main__":
    processar_csv()