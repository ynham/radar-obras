"""
Exportador de Dados e Atualizador do Sistema Web Radar Obras MT
Lê a planilha de oportunidades e atualiza o arquivo dados_obras.json consumido pela aplicação web.
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
    
    # Converte para JSON amigável para o frontend
    dados = df.to_dict(orient="records")
    
    # Salva dados_obras.json
    caminho_json = "dados_obras.json"
    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
        
    print(f"[OK] Base de dados atualizada: {caminho_json} ({len(dados)} oportunidades)")
    
    # Garante que radar_obras.html e index.html estejam sincronizados com o sistema
    if os.path.exists("index.html") and arquivo_html != "index.html":
        shutil.copy("index.html", arquivo_html)
        print(f"[OK] Sistema web sincronizado com {arquivo_html}")
        
    return caminho_json

if __name__ == "__main__":
    gerar_dashboard()
