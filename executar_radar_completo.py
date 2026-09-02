"""
Executador Completo do Radar Multissource de Obras (Local & Nuvem)
1. Varre editais governamentais na API do PNCP (Compras.gov)
2. Varre licitações do Sistema S (SESI, SENAI, SESC, SENAC, SEBRAE MT)
3. Varre alvarás de obras e reformas privadas aprovadas em Cuiabá e Várzea Grande
4. Atualiza a planilha Excel, base JSON e o Painel Web
5. Envia alerta por e-mail se configurado
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from radar_obras import RadarLicitacoes
from radar_sistema_s import RadarSistemaS
from radar_alvaras_mt import RadarAlvarasMT
from exportar_dashboard_html import gerar_dashboard
from notificador_email import NotificadorEmail

def main():
    todas_oportunidades = []
    
    # 1. Varredura Governamental (PNCP)
    dias_retroativos = int(os.getenv("DIAS_RETROATIVOS", "240"))
    hoje = datetime.now()
    inicio = hoje - timedelta(days=dias_retroativos)
    
    data_fim = hoje.strftime("%Y-%m-%d")
    data_ini = inicio.strftime("%Y-%m-%d")
    
    print(f"\n>>> 1. Varrendo PNCP (Governo) de {data_ini} até {data_fim}...")
    radar_gov = RadarLicitacoes(uf=os.getenv("UF_ESTADO", "MT"))
    ops_gov = radar_gov.buscar_oportunidades(data_inicio=data_ini, data_fim=data_fim)
    todas_oportunidades.extend(ops_gov)
    
    # 2. Varredura do Sistema S (Sesi / Senai / Sesc / Sebrae MT)
    print("\n>>> 2. Varrendo Sistema S (Mato Grosso)...")
    radar_s = RadarSistemaS(uf=os.getenv("UF_ESTADO", "MT"))
    ops_sistema_s = radar_s.buscar_oportunidades()
    todas_oportunidades.extend(ops_sistema_s)
    
    # 3. Varredura de Obras Privadas (Alvarás Cuiabá e Várzea Grande)
    print("\n>>> 3. Varrendo Obras Privadas (Alvarás Cuiabá / VG)...")
    radar_alv = RadarAlvarasMT()
    ops_alvaras = radar_alv.buscar_oportunidades()
    todas_oportunidades.extend(ops_alvaras)
    
    # Ordenar por data mais recente
    todas_oportunidades.sort(key=lambda x: str(x.get("Data Publicação", "")), reverse=True)
    
    print(f"\n=======================================================")
    print(f"  TOTAL DE OPORTUNIDADES CONSOLIDADAS: {len(todas_oportunidades)}")
    print(f"  - Governo / PNCP: {len(ops_gov)}")
    print(f"  - Sistema S: {len(ops_sistema_s)}")
    print(f"  - Obras Privadas (Alvarás): {len(ops_alvaras)}")
    print(f"=======================================================\n")
    
    if todas_oportunidades:
        # Salvar Excel
        df = pd.DataFrame(todas_oportunidades)
        arquivo_excel = "oportunidades_obras_mt.xlsx"
        df.to_excel(arquivo_excel, index=False)
        print(f"[OK] Planilha consolidada gerada: {arquivo_excel}")
        
        # Gerar JSON e Sincronizar Sistema Web
        gerar_dashboard(arquivo_excel, "radar_obras.html")
        
        # 4. Enviar E-mail (se configurado)
        email_remetente = os.getenv("EMAIL_REMETENTE")
        senha_remetente = os.getenv("EMAIL_SENHA")
        email_destinatario = os.getenv("EMAIL_DESTINATARIO")
        
        if email_remetente and senha_remetente and email_destinatario:
            destinatarios = [e.strip() for e in email_destinatario.split(",")]
            notificador = NotificadorEmail(
                smtp_server=os.getenv("SMTP_SERVER", "smtp.gmail.com"),
                smtp_port=int(os.getenv("SMTP_PORT", "587")),
                email_remetente=email_remetente,
                senha_remetente=senha_remetente
            )
            notificador.enviar_alerta(destinatarios=destinatarios, oportunidades=todas_oportunidades)
        else:
            print("[Info] E-mail não configurado ou rodando em modo silencioso.")

if __name__ == "__main__":
    main()
