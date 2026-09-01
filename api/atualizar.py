from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        try:
            with open('dados_obras.json', 'r', encoding='utf-8') as f:
                data = f.read()
            self.wfile.write(data.encode('utf-8'))
        except Exception as e:
            self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))

    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        try:
            # Executa a varredura unificada
            from radar_obras import RadarLicitacoes
            from radar_sistema_s import RadarSistemaS
            from radar_alvaras_mt import RadarAlvarasMT
            from datetime import datetime, timedelta

            radar_gov = RadarLicitacoes(uf="MT")
            hoje = datetime.now()
            ini = hoje - timedelta(days=240)
            ops_gov = radar_gov.buscar_oportunidades(data_inicio=ini.strftime("%Y-%m-%d"), data_fim=hoje.strftime("%Y-%m-%d"))
            
            radar_s = RadarSistemaS(uf="MT")
            ops_s = radar_s.buscar_oportunidades()
            
            radar_alv = RadarAlvarasMT()
            ops_alv = radar_alv.buscar_oportunidades()
            
            todas = ops_gov + ops_s + ops_alv
            todas.sort(key=lambda x: str(x.get("Data Publicação", "")), reverse=True)
            
            total_gov = len([d for d in todas if "Governo" in str(d.get("Origem", "")) or "PNCP" in str(d.get("Alimentador", ""))])
            total_sis = len([d for d in todas if "Sistema S" in str(d.get("Origem", "")) or "Sistema S" in str(d.get("Alimentador", ""))])
            total_alv = len([d for d in todas if "Privada" in str(d.get("Origem", "")) or "Alvará" in str(d.get("Alimentador", ""))])

            resposta = {
                "sucesso": True,
                "mensagem": "Varredura executada com sucesso!",
                "metadados": {
                    "ultima_atualizacao": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "total_geral": len(todas),
                    "alimentadores": [
                        {
                            "id": "pncp",
                            "nome": "🏛️ PNCP / Compras.gov",
                            "tipo": "API Oficial Federal e Estadual",
                            "status": "Online & Monitorando",
                            "frequencia": "Diário (07:00)",
                            "total": total_gov,
                            "url_fonte": "https://pncp.gov.br"
                        },
                        {
                            "id": "sistema_s",
                            "nome": "🏢 Sistema S (Sesi, Senai, Sesc, Sebrae)",
                            "tipo": "Portais de Compras Paraestatais",
                            "status": "Online & Monitorando",
                            "frequencia": "Diário (07:00)",
                            "total": total_sis,
                            "url_fonte": "https://compras.sfiemt.ind.br/Default.aspx"
                        },
                        {
                            "id": "alvaras",
                            "nome": "🏗️ Diários Oficiais (Alvarás Cuiabá/VG)",
                            "tipo": "Atos de Aprovação de Projetos",
                            "status": "Online & Monitorando",
                            "frequencia": "Diário (07:00)",
                            "total": total_alv,
                            "url_fonte": "https://gazetamunicipal.cuiaba.mt.gov.br"
                        }
                    ]
                },
                "oportunidades": todas
            }
            self.wfile.write(json.dumps(resposta, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.wfile.write(json.dumps({"sucesso": False, "erro": str(e)}).encode('utf-8'))
