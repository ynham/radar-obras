import requests
import json
from datetime import datetime, timedelta

# Configurações de busca
# Data atual fictícia/sistema ou dos últimos 15 dias
data_fim = datetime.now()
data_ini = data_fim - timedelta(days=15)

data_inicial_str = data_ini.strftime("%Y%m%d")
data_final_str = data_fim.strftime("%Y%m%d")

print(f"Buscando publicações no PNCP de {data_inicial_str} até {data_final_str}...")

# Endpoint de consulta pública do PNCP
url = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"

params = {
    "dataInicial": data_inicial_str,
    "dataFinal": data_final_str,
    "uf": "MT",
    "pagina": 1,
    "tamanhoPagina": 20
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json"
}

try:
    response = requests.get(url, params=params, headers=headers, timeout=30)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        total_registros = data.get("totalRegistros", 0)
        print(f"Total de contratações encontradas em MT: {total_registros}")
        
        items = data.get("data", [])
        print(f"Exibindo os primeiros {len(items)} itens:")
        for idx, item in enumerate(items[:5], 1):
            objeto = item.get("objeto", "Sem descrição")
            orgao = item.get("orgaoEntidade", {}).get("razaoSocial", "Órgão desconhecido")
            modalidade = item.get("modalidadeNome", "Modalidade N/A")
            valor = item.get("valorTotalEstimado", 0.0)
            municipio = item.get("unidadeOrgao", {}).get("municipioNome", "N/A")
            
            print(f"\n[{idx}] {orgao} ({municipio}/MT)")
            print(f"    Modalidade: {modalidade} | Valor Estimado: R$ {valor:,.2f}" if valor else f"    Modalidade: {modalidade}")
            print(f"    Objeto: {objeto[:120]}...")
    else:
        print(f"Erro na requisição: {response.text[:300]}")
except Exception as e:
    print(f"Exceção ocorrida: {e}")
