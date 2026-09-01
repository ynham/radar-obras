import requests
import json

url = 'https://dadosabertos.compras.gov.br/modulo-contratacoes/1_consultarContratacoes_PNCP_14133'

params = {
    'dataPublicacaoPncpInicial': '2024-05-01',
    'dataPublicacaoPncpFinal': '2024-08-31',
    'codigoModalidade': 6, # Pregão
    'unidadeOrgaoUfSigla': 'MT',
    'pagina': 1,
    'tamanhoPagina': 10
}

r = requests.get(url, params=params, timeout=20)
if r.status_code == 200:
    res = r.json()
    items = res.get('resultado', [])
    if items:
        print("Campos disponíveis no primeiro registro:")
        print(json.dumps(items[0], indent=2, ensure_ascii=False))
