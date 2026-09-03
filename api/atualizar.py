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
            ini = hoje - timedelta(days=365)
            ops_gov = radar_gov.buscar_oportunidades(data_inicio=ini.strftime("%Y-%m-%d"), data_fim=hoje.strftime("%Y-%m-%d"))
            
            for i, item in enumerate(ops_gov):
                item["_id"] = f"pncp_{item.get('Processo', str(i)).replace('/', '_').replace('.', '_').replace('-', '_')}"
                item["Origem"] = "🏛️ Governo / PNCP"
                item["Alimentador"] = "PNCP / Compras.gov (Governo)"
            
            todas = ops_gov
            todas.sort(key=lambda x: str(x.get("Data Publicação", "")), reverse=True)
            total_gov = len(todas)


            resposta = {
                "sucesso": True,
                "mensagem": "Varredura executada com sucesso!",
                "metadados": {
                    "ultima_atualizacao": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "total_geral": len(todas),
                    "alimentadores": [
                        {
                            "id": "pncp",
                            "nome": "🏛️ Portal Nacional de Contratações Públicas (PNCP)",
                            "tipo": "API Oficial Federal, Estadual e Municipal (100% Real)",
                            "status": "Online & Monitorando",
                            "frequencia": "Atualização Diária",
                            "total": total_gov,
                            "url_fonte": "https://pncp.gov.br"
                        }
                    ]
                },
                "oportunidades": todas
            }

            self.wfile.write(json.dumps(resposta, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.wfile.write(json.dumps({"sucesso": False, "erro": str(e)}).encode('utf-8'))
