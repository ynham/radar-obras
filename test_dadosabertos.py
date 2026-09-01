import requests
import json

url = 'https://dadosabertos.compras.gov.br/modulo-contratacoes/1_consultarContratacoes_PNCP_14133'

params = {
    'dataPublicacaoPncpInicial': '2024-08-01',
    'dataPublicacaoPncpFinal': '2024-08-31',
    'codigoModalidade': 8, # Dispensa de Licitação
    'unidadeOrgaoUfSigla': 'MT',
    'pagina': 1,
    'tamanhoPagina': 10
}

r = requests.get(url, params=params, timeout=20)
print(f"Status Code: {r.status_code}")

if r.status_code == 200:
    res = r.json()
    print(f"Total de registros encontrados: {res.get('totalRegistros')}")
    for item in res.get('resultado', [])[:5]:
        print("-" * 50)
        print(f"Órgão: {item.get('orgaoEntidadeRazaoSocial')} ({item.get('unidadeOrgaoMunicipioNome')}/MT)")
        print(f"Objeto: {item.get('objetoContratacao')}")
        print(f"Valor Estimado: R$ {item.get('valorTotalEstimado')}")
        print(f"Link PNCP: https://pncp.gov.br/app/editais/{item.get('orgaoEntidadeCnpj')}/{item.get('anoContratacaoPncp')}/{item.get('numeroSequencialPncp')}")
else:
    print(f"Erro: {r.text}")
