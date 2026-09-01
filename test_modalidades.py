import requests

url = 'https://dadosabertos.compras.gov.br/modulo-contratacoes/1_consultarContratacoes_PNCP_14133'

# Testar várias modalidades: 6 (Pregão), 8 (Dispensa), 4 (Concorrência)
for modalidade, nome_mod in [(6, 'Pregão Eletrônico'), (8, 'Dispensa de Licitação'), (4, 'Concorrência')]:
    params = {
        'dataPublicacaoPncpInicial': '2024-05-01',
        'dataPublicacaoPncpFinal': '2024-08-31',
        'codigoModalidade': modalidade,
        'unidadeOrgaoUfSigla': 'MT',
        'pagina': 1,
        'tamanhoPagina': 10
    }
    r = requests.get(url, params=params, timeout=20)
    if r.status_code == 200:
        res = r.json()
        print(f"[{nome_mod}] Total em MT: {res.get('totalRegistros')}")
        for item in res.get('resultado', [])[:2]:
            print(f"  -> {item.get('objetoContratacao')[:80]}... (R$ {item.get('valorTotalEstimado')})")
    else:
        print(f"[{nome_mod}] Erro: {r.status_code}")
