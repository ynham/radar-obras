"""
Exportador de Dados e Atualizador do Sistema Web Radar Obras MT
Lê a planilha de oportunidades e atualiza o arquivo dados_obras.json consumido pela aplicação web,
incluindo status e métricas dos alimentadores ativos.
"""

import json
import os
import shutil
import pandas as pd

def gerar_dashboard(arquivo_excel="oportunidades_obras_mt.xlsx", arquivo_html="radar_obras.html"):
    if not os.path.exists(arquivo_excel):
        print(f"[Aviso] Arquivo {arquivo_excel} não encontrado.")
        return None
        
    df = pd.read_excel(arquivo_excel)
    dados = df.to_dict(orient="records")
    
    # Contabiliza alimentadores
    total_gov = len([d for d in dados if "Governo" in str(d.get("Origem", "")) or "PNCP" in str(d.get("Alimentador", ""))])
    total_sis = len([d for d in dados if "Sistema S" in str(d.get("Origem", "")) or "Sistema S" in str(d.get("Alimentador", ""))])
    total_alv = len([d for d in dados if "Privada" in str(d.get("Origem", "")) or "Alvará" in str(d.get("Alimentador", ""))])

    pacote = {
        "metadados": {
            "ultima_atualizacao": pd.Timestamp.now().strftime("%d/%m/%Y %H:%M"),
            "total_geral": len(dados),
            "alimentadores": [
                {
                    "id": "pncp",
                    "nome": "🏛️ PNCP / Compras.gov",
                    "tipo": "API Governamental Federal e Estadual",
                    "status": "Online & Monitorando",
                    "frequencia": "Diário (07:00)",
                    "total": total_gov,
                    "url_fonte": "https://pncp.gov.br",
                    "descricao": "Monitora licitações abertas de órgãos públicos em Mato Grosso via Lei 14.133."
                },
                {
                    "id": "sistema_s",
                    "nome": "🏢 Sistema S (Sesi, Senai, Sesc, Sebrae)",
                    "tipo": "Portais de Compras Paraestatais",
                    "status": "Online & Monitorando",
                    "frequencia": "Diário (07:00)",
                    "total": total_sis,
                    "url_fonte": "https://licitacoes.portaldaindustria.com.br",
                    "descricao": "Monitora editais de reformas, manutenção predial e climatização de escolas técnicas e clubes."
                },
                {
                    "id": "alvaras",
                    "nome": "🏗️ Diários Oficiais (Alvarás Cuiabá/VG)",
                    "tipo": "Atos de Aprovação de Projetos",
                    "status": "Online & Monitorando",
                    "frequencia": "Diário (07:00)",
                    "total": total_alv,
                    "url_fonte": "https://gazetamunicipal.cuiaba.mt.gov.br",
                    "descricao": "Monitora alvarás de construção e reformas comerciais privadas aprovadas pelas prefeituras."
                }
            ]
        },
        "oportunidades": dados
    }
    
    # Salva dados_obras.json com metadados dos alimentadores
    caminho_json = "dados_obras.json"
    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(pacote, f, ensure_ascii=False, indent=2)
        
    print(f"[OK] Base de dados atualizada: {caminho_json} ({len(dados)} oportunidades com status de 3 alimentadores)")
    
    # Garante que radar_obras.html e index.html estejam sincronizados com o sistema
    if os.path.exists("index.html") and arquivo_html != "index.html":
        shutil.copy("index.html", arquivo_html)
        print(f"[OK] Sistema web sincronizado com {arquivo_html}")
        
    return caminho_json

if __name__ == "__main__":
    gerar_dashboard()
