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

# Termos que anulam o resultado (falso positivo comum / fora do escopo de engenharia civil)
TERMOS_NEGATIVOS = [
    r"limpeza", r"faxina", r"copeir[ao]", r"recepcionista", r"porteiro",
    r"vigil[âa]ncia", r"seguran[çc]a armada", r"portaria", r"apoio administrativo",
    r"outsourcing", r"impressora", r"impress[ãa]o", r"software", r"computador", r"webcam", r"telefonia",
    r"correios", r"encomenda", r"transporte de correspond[êe]ncia", r"servi[çc]os postais",
    r"mudan[çc]a", r"embalamento", r"transporte de bens", r"loca[çc][ãa]o de tenda", r"palco",
    r"sonoriza[çc][ãa]o", r"ilumina[çc][ãa]o c[êe]nica", r"evento", r"coffee break", r"buffet",
    r"prensa hidr[áa]ulica", r"armamento", r"ve[íi]culo", r"combust[íi]vel", r"pneu",
    r"reforma agr[áa]ria", r"reforma de pneu", r"reforma de estofado", r"reforma de m[óo]veis",
    r"tape[çc]aria", r"estofado", r"mobili[áa]rio", r"porta girat[óo]ria", r"detector de metais",
    r"consumo estimado de energia", r"fatura de energia", r"tarifa de energia",
    r"aquisi[çc][ãa]o de cabos", r"aquisi[çc][ãa]o de ferramentas", r"fornecimento de ferramentas",
    r"ferramentas e equipamentos", r"cortador manual", r"tijolo, material",
    r"materiais para dispensa", r"materiais diversos de constru[çc][ãa]o",
    r"fornecimento de materiais de expediente", r"licen[çc]a de software",
    r"material de consumo", r"alimentos", r"medicamento", r"merenda", r"farmac[êe]utic",
    r"esta[çc][õo]es de rede completas"
]

class RadarLicitacoes:
    def __init__(self, uf: str = "MT", cidades_prioritarias: Optional[List[str]] = None):
        self.uf = uf.upper()
        self.cidades_prioritarias = [c.upper() for c in (cidades_prioritarias or ["CUIABÁ", "CUIABA", "VÁRZEA GRANDE", "VARZEA GRANDE"])]

    def _classificar_objeto(self, objeto: str, orgao: str = "") -> Optional[str]:
        if not objeto:
            return None
            
        texto = objeto.lower()
        texto_orgao = orgao.lower() if orgao else ""
        
        # 1. Checa se contém termos negativos explícitos no objeto ou no órgão
        for neg in TERMOS_NEGATIVOS:
            if re.search(neg, texto) or re.search(neg, texto_orgao):
                return None

        # 2. Rejeita compra pura de materiais sem serviço/mão de obra de engenharia
        if re.search(r"\baquisi[çc][ãa]o de\b|\bfornecimento de materiais\b|\bcompra de\b", texto):
            if not re.search(r"\bexecu[çc][ãa]o\b|\bservi[çc]os? de engenharia\b|\bobra\b|\breforma\b|\bm[ãa]o de obra\b", texto):
                return None
                    
        # 3. Categorização rigorosa de CONSTRUÇÃO CIVIL E ENGENHARIA
        if re.search(r"\bexecu[çc][ãa]o de reforma\b|\breforma predial\b|\breforma de edif[íi]cio\b|\breforma da sede\b|\bcobertura da sede\b|\bcobertura met[áa]lica\b|\badequa[çc][ãa]o predial\b|\breforma e adequa[çc][ãa]o\b|\breforma de pisos\b|\bengenharia civil\b", texto):
            return "Reforma / Adequação Predial"
        elif re.search(r"\bexecu[çc][ãa]o de obra\b|\bconstru[çc][ãa]o civil\b|\bconstru[çc][ãa]o de\b", texto):
            return "Construção Civil"
        elif re.search(r"\bmanuten[çc][ãa]o predial\b|\bconserva[çc][ãa]o predial\b|\brepara[çc][ãa]o do telhado\b|\bpintura predial\b", texto):
            return "Manutenção Predial"
        elif re.search(r"\bpavimenta[çc][ãa]o\b|\brecapeamento\b|\bdrenagem pluvial\b|\breconforma[çc][ãa]o de plataforma\b", texto):
            return "Pavimentação / Infraestrutura"
        elif re.search(r"\bpo[çc]o tubular\b|\brede el[ée]trica\b|\binstala[çc][ãa]o el[ée]trica\b|\bclimatiza[çc][ãa]o predial\b|\bsistema de ar-condicionado\b", texto):
            return "Instalações / Climatização"
        elif re.search(r"\bservi[çc]os? de engenharia\b|\bservi[çc]os? comuns? de engenharia\b|\bprojeto executivo de engenharia\b|\bprojeto b[áa]sico de engenharia\b|\bprojeto de arquitetura\b|\blaudo t[ée]cnico e art\b|\bfiscaliza[çc][ãa]o de obras\b|\bseguran[çc]a contra inc[êe]ndio\b", texto):
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
                    orgao = item.get("orgaoEntidadeRazaoSocial") or ""
                    categoria = self._classificar_objeto(objeto, orgao)
                    
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
                            "Origem": "🏛️ Governo / PNCP",
                            "Alimentador": "PNCP / Compras.gov (Governo)"
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
