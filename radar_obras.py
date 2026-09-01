"""
Radar de Obras e Licitações - Antigravity PMO
Motor de busca e monitoramento automático de editais de engenharia civil no PNCP (Compras.gov.br)
"""

import os
import re
import json
import time
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

API_URL = "https://dadosabertos.compras.gov.br/modulo-contratacoes/1_consultarContratacoes_PNCP_14133"

# Termos obrigatórios de Obras e Serviços de Engenharia
TERMOS_POSITIVOS = [
    r"\breforma\b", r"\breformas\b",
    r"\bobra\b", r"\bobras\b",
    r"\bconstrucao\b", r"\bconstrução\b",
    r"\bmanutencao predial\b", r"\bmanutenção predial\b",
    r"\bpavimentacao\b", r"\bpavimentação\b",
    r"\bservicos? de engenharia\b", r"\bserviços? de engenharia\b",
    r"\bexecucao de engenharia\b", r"\bexecução de engenharia\b",
    r"\badadequacao predial\b", r"\badequação predial\b",
    r"\binstalacao eletrica\b", r"\binstalação elétrica\b",
    r"\binstalacoes hidraulicas\b", r"\binstalações hidráulicas\b",
    r"\bcobertura metalica\b", r"\bcobertura metálica\b",
    r"\bpintura predial\b", r"\bpintura de fachada\b",
    r"\brecapeamento\b", r"\bdrenagem pluvial\b",
    r"\bclimatizacao\b", r"\bclimatização\b"
]

# Termos que anulam o resultado (falso positivo comum)
TERMOS_NEGATIVOS = [
    r"\baquisicao de\b", r"\baquisição de\b",  # Geralmente é compra de material avulso, não serviço de obra
    r"\bmerenda\b", r"\balimentacao\b", r"\balimentação\b",
    r"\bsoftware\b", r"\bcomputador\b", r"\bwebcam\b",
    r"\bveiculo\b", r"\bveículos\b", r"\bcombustivel\b", r"\bcombustível\b",
    r"\bmedicamento\b", r"\bmedicamentos\b", r"\bexames\b",
    r"\blimpeza e conservacao\b", r"\blimpeza e conservação\b", r"\brecepcionista\b",
    r"\bapoio administrativo\b", r"\bvigilancia\b", r"\bvigilância\b",
    r"\bpassagens aereas\b", r"\bpassagens aéreas\b"
]

class RadarLicitacoes:
    def __init__(self, uf: str = "MT", cidades_prioritarias: Optional[List[str]] = None):
        self.uf = uf.upper()
        self.cidades_prioritarias = [c.upper() for c in (cidades_prioritarias or ["CUIABÁ", "CUIABA", "VÁRZEA GRANDE", "VARZEA GRANDE"])]

    def _classificar_objeto(self, objeto: str) -> Optional[str]:
        if not objeto:
            return None
            
        texto = objeto.lower()
        
        # 1. Checa se é claramente falso positivo
        for neg in TERMOS_NEGATIVOS:
            if re.search(neg, texto):
                # Se for "aquisição de material", só aceita se falar expressamente em obra/reforma contratada
                if not (re.search(r"\bexecucao de obra\b", texto) or re.search(r"\bexecução de obra\b", texto) or re.search(r"\bservicos? de reforma\b", texto) or re.search(r"\bserviços? de reforma\b", texto)):
                    return None
                    
        # 2. Categoriza por tipo de obra
        if re.search(r"\breforma\b|\badequacao predial\b|\badequação predial\b", texto):
            return "Reforma / Adequação Predial"
        elif re.search(r"\bconstrucao\b|\bconstrução\b|\bexecucao de obra\b|\bexecução de obra\b", texto):
            return "Construção Civil"
        elif re.search(r"\bmanutencao predial\b|\bmanutenção predial\b|\bconservacao predial\b|\bconservação predial\b", texto):
            return "Manutenção Predial"
        elif re.search(r"\bpavimentacao\b|\bpavimentação\b|\brecapeamento\b|\bdrenagem\b", texto):
            return "Pavimentação / Infraestrutura"
        elif re.search(r"\beletrica\b|\belétrica\b|\bclimatizacao\b|\bclimatização\b|\bhidraulica\b|\bhidráulica\b", texto):
            return "Instalações / Climatização"
        elif re.search(r"\bservicos? de engenharia\b|\bserviços? de engenharia\b", texto):
            return "Serviços de Engenharia Geral"
            
        return None

    def _fazer_requisicao(self, params: dict, max_tentativas: int = 3) -> Optional[dict]:
        for tentativa in range(max_tentativas):
            try:
                resp = requests.get(API_URL, params=params, timeout=45)
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 400:
                    return None
            except Exception:
                time.sleep(2)
        return None

    def buscar_oportunidades(self, data_inicio: str, data_fim: str, modalidades: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        if modalidades is None:
            modalidades = [6, 8, 4]  # Pregão (6), Dispensa (8), Concorrência (4)
            
        oportunidades = []
        
        print(f"\n=======================================================")
        print(f"  RADAR DE OBRAS - Antigravity PMO ({self.uf})")
        print(f"  Período: {data_inicio} até {data_fim}")
        print(f"=======================================================\n")
        
        for mod in modalidades:
            nome_mod = {8: "Dispensa de Licitação", 6: "Pregão Eletrônico", 4: "Concorrência"}.get(mod, f"Modalidade {mod}")
            print(f"-> Varrendo {nome_mod}...")
            
            pagina = 1
            total_mod = 0
            
            while True:
                params = {
                    "dataPublicacaoPncpInicial": data_inicio,
                    "dataPublicacaoPncpFinal": data_fim,
                    "codigoModalidade": mod,
                    "unidadeOrgaoUfSigla": self.uf,
                    "pagina": pagina,
                    "tamanhoPagina": 100
                }
                
                data = self._fazer_requisicao(params)
                if not data:
                    break
                    
                resultados = data.get("resultado", [])
                if not resultados:
                    break
                    
                for item in resultados:
                    objeto = item.get("objetoCompra") or item.get("objetoContratacao") or ""
                    categoria = self._classificar_objeto(objeto)
                    
                    if categoria:
                        municipio = (item.get("unidadeOrgaoMunicipioNome") or "N/A").strip().upper()
                        is_prioritaria = any(cid in municipio for cid in self.cidades_prioritarias)
                        
                        cnpj = item.get("orgaoEntidadeCnpj") or ""
                        ano = item.get("anoCompraPncp") or ""
                        seq = item.get("sequencialCompraPncp") or ""
                        link_pncp = f"https://pncp.gov.br/app/editais/{cnpj}/{ano}/{seq}" if cnpj and ano and seq else "https://pncp.gov.br"
                        
                        valor = item.get("valorTotalEstimado") or 0.0
                        
                        oportunidades.append({
                            "Categoria": categoria,
                            "Município": municipio,
                            "Prioritária (Cuiabá/VG)": "SIM" if is_prioritaria else "NÃO",
                            "Valor Estimado (R$)": valor,
                            "Modalidade": item.get("modalidadeNome") or nome_mod,
                            "Data Publicação": (item.get("dataPublicacaoPncp") or "")[:10],
                            "Encerramento Proposta": (item.get("dataEncerramentoPropostaPncp") or "")[:16].replace("T", " "),
                            "Órgão": item.get("orgaoEntidadeRazaoSocial") or "N/A",
                            "Objeto": objeto.strip(),
                            "Processo": item.get("processo") or "N/A",
                            "Link PNCP": link_pncp,
                            "Origem": "🏛️ Governo / PNCP"
                        })
                        total_mod += 1
                        
                total_paginas = data.get("totalPaginas", 1)
                if pagina >= total_paginas:
                    break
                pagina += 1
                
            print(f"   [OK] {total_mod} oportunidades reais de engenharia identificadas.")
                    
        print(f"\n[Concluído] Total de oportunidades qualificadas: {len(oportunidades)}")
        return oportunidades

    def exportar_para_excel(self, oportunidades: List[Dict[str, Any]], arquivo_saida: str = "oportunidades_obras_mt.xlsx"):
        if not oportunidades:
            print("[Aviso] Nenhuma oportunidade qualificada para exportar.")
            return None
            
        df = pd.DataFrame(oportunidades)
        # Ordenar por Prioritária (Cuiabá/VG primeiro), Categoria e Valor
        df = df.sort_values(by=["Prioritária (Cuiabá/VG)", "Data Publicação"], ascending=[False, False])
        
        with pd.ExcelWriter(arquivo_saida, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Oportunidades_Qualificadas')
            
        print(f"[OK] Planilha gerada com sucesso: {arquivo_saida}")
        return arquivo_saida


if __name__ == "__main__":
    radar = RadarLicitacoes(uf="MT")
    # Busca de 2024 inteira
    resultados = radar.buscar_oportunidades(data_inicio="2024-01-01", data_fim="2024-08-31")
    
    if resultados:
        radar.exportar_para_excel(resultados, "oportunidades_obras_mt.xlsx")
        print("\n--- OPORTUNIDADES QUALIFICADAS DE ENGENHARIA CIVIL ---")
        for op in resultados[:5]:
            print(f"\n[{op['Categoria']}] {op['Município']} - R$ {op['Valor Estimado (R$)']:,.2f}")
            print(f"Órgão: {op['Órgão']} ({op['Modalidade']})")
            print(f"Objeto: {op['Objeto'][:140]}...")
            print(f"Link PNCP: {op['Link PNCP']}")
