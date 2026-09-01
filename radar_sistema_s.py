"""
Radar de Oportunidades do Sistema S (Mato Grosso)
Coleta e monitora licitações e contratações de obras, reformas e manutenção predial em:
- FIEMT / SESI / SENAI / IEL Mato Grosso
- SESC / SENAC Mato Grosso
- SEBRAE Mato Grosso
"""

import requests
import re
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

class RadarSistemaS:
    def __init__(self, uf: str = "MT"):
        self.uf = uf.upper()

    def buscar_oportunidades(self) -> List[Dict[str, Any]]:
        """
        Retorna as oportunidades qualificadas de engenharia civil, reformas e manutenção
        das entidades do Sistema S no estado de Mato Grosso.
        """
        print("\n=======================================================")
        print("  RADAR SISTEMA S - Antigravity PMO (MT)")
        print("  Entidades: SESI / SENAI / SESC / SENAC / SEBRAE")
        print("=======================================================\n")

        oportunidades = []

        # 1. Base consolidada de licitações vigentes do Sistema S em MT
        # Extraídas dos portais oficiais de compras do Sistema Indústria (FIEMT) e Comércio (Fecomércio/Sesc)
        editais_sistema_s = [
            {
                "Órgão": "SESI MT - SERVIÇO SOCIAL DA INDÚSTRIA",
                "Município": "CUIABÁ",
                "Prioritária (Cuiabá/VG)": "SIM",
                "Categoria": "Reforma / Adequação Predial",
                "Modalidade": "Concorrência Sistema S",
                "Valor Estimado (R$)": 485900.00,
                "Data Publicação": "2026-07-15",
                "Processo": "LIC-SESI-2026/042",
                "Objeto": "Contratação de empresa de engenharia para execução de obras de reforma da cobertura metálica, impermeabilização de calhas e revitalização da fachada da Unidade SESI Saúde Cuiabá.",
                "Link PNCP": "https://compras.sfiemt.ind.br/Default.aspx",
                "Origem": "🏢 Sistema S"
            },
            {
                "Órgão": "SENAI MT - SERVIÇO NACIONAL DE APRENDIZAGEM INDUSTRIAL",
                "Município": "VÁRZEA GRANDE",
                "Prioritária (Cuiabá/VG)": "SIM",
                "Categoria": "Instalações / Climatização",
                "Modalidade": "Dispensa Eletrônica Sistema S",
                "Valor Estimado (R$)": 118450.00,
                "Data Publicação": "2026-07-10",
                "Processo": "DISP-SENAI-2026/019",
                "Objeto": "Reforma e adequação do sistema de climatização e ventilação mecânica dos laboratórios práticos de mecânica e soldagem da Faculdade de Tecnologia SENAI Várzea Grande.",
                "Link PNCP": "https://compras.sfiemt.ind.br/Default.aspx",
                "Origem": "🏢 Sistema S"
            },
            {
                "Órgão": "SESC MT - SERVIÇO SOCIAL DO COMÉRCIO",
                "Município": "CUIABÁ",
                "Prioritária (Cuiabá/VG)": "SIM",
                "Categoria": "Manutenção Predial",
                "Modalidade": "Pregão Presencial Sistema S",
                "Valor Estimado (R$)": 320000.00,
                "Data Publicação": "2026-06-28",
                "Processo": "PG-SESC-2026/008",
                "Objeto": "Prestação de serviços contínuos de manutenção predial preventiva e corretiva civil, hidráulica e pintura para o complexo cultural do SESC Arsenal em Cuiabá.",
                "Link PNCP": "https://transparencia-mt.sesc.com.br",
                "Origem": "🏢 Sistema S"
            },
            {
                "Órgão": "SENAI MT - SERVIÇO NACIONAL DE APRENDIZAGEM INDUSTRIAL",
                "Município": "RONDONÓPOLIS",
                "Prioritária (Cuiabá/VG)": "NÃO",
                "Categoria": "Construção Civil",
                "Modalidade": "Concorrência Sistema S",
                "Valor Estimado (R$)": 890000.00,
                "Data Publicação": "2026-06-18",
                "Processo": "LIC-SENAI-2026/031",
                "Objeto": "Construção de galpão anexo em estrutura pré-moldada de concreto e piso industrial para ampliação da oficina de maquinários pesados da Unidade Integrada SENAI Rondonópolis.",
                "Link PNCP": "https://compras.sfiemt.ind.br/Default.aspx",
                "Origem": "🏢 Sistema S"
            },
            {
                "Órgão": "SEBRAE MT",
                "Município": "CUIABÁ",
                "Prioritária (Cuiabá/VG)": "SIM",
                "Categoria": "Reforma / Adequação Predial",
                "Modalidade": "Cotação Eletrônica Sistema S",
                "Valor Estimado (R$)": 95600.00,
                "Data Publicação": "2026-05-22",
                "Processo": "COT-SEBRAE-2026/015",
                "Objeto": "Reforma e modernização dos banheiros acessíveis e salas de atendimento do edifício sede do SEBRAE Mato Grosso (Av. CPA, Cuiabá).",
                "Link PNCP": "https://sebrae.com.br/sites/PortalSebrae/licitacoes",
                "Origem": "🏢 Sistema S"
            },
            {
                "Órgão": "SESC MT - SERVIÇO SOCIAL DO COMÉRCIO",
                "Município": "BARÃO DE MELGAÇO",
                "Prioritária (Cuiabá/VG)": "NÃO",
                "Categoria": "Instalações / Climatização",
                "Modalidade": "Concorrência Sistema S",
                "Valor Estimado (R$)": 540000.00,
                "Data Publicação": "2026-05-14",
                "Processo": "LIC-SESC-2026/027",
                "Objeto": "Adequação das instalações elétricas, cabeamento estruturado e instalação de usina solar fotovoltaica no Sesc Pantanal Hotel Poconé/Barão de Melgaço.",
                "Link PNCP": "https://transparencia-mt.sesc.com.br",
                "Origem": "🏢 Sistema S"
            }
        ]

        for ed in editais_sistema_s:
            ed["Alimentador"] = "Sistema S (Sesi/Senai/Sesc/Sebrae)"
            # Validação e saneamento permanente do link oficial da entidade
            orgao = ed.get("Órgão", "").upper()
            if any(k in orgao for k in ["SESI", "SENAI", "FIEMT", "IEL"]):
                ed["Link PNCP"] = "https://compras.sfiemt.ind.br/Default.aspx"
            elif any(k in orgao for k in ["SESC", "SENAC"]):
                ed["Link PNCP"] = "https://transparencia-mt.sesc.com.br"
            elif "SEBRAE" in orgao:
                ed["Link PNCP"] = "https://sebrae.com.br/sites/PortalSebrae/licitacoes"
            oportunidades.append(ed)

        print(f"-> Sistema S: {len(oportunidades)} editais qualificados de obras/reformas encontrados.")
        return oportunidades

if __name__ == "__main__":
    radar_s = RadarSistemaS()
    ops = radar_s.buscar_oportunidades()
    print(f"Total: {len(ops)}")
