"""
Executador Completo do Radar de Obras (Local & Nuvem)
1. Busca editais na API do PNCP
2. Atualiza a planilha Excel e o Painel Web HTML
3. Envia alerta por e-mail se configurado
"""

import os
from datetime import datetime, timedelta
from radar_obras import RadarLicitacoes
from exportar_dashboard_html import gerar_dashboard
from notificador_email import NotificadorEmail

def main():
    # 1. Configurar período (busca dos últimos 7 dias para varredura diária)
    dias_retroativos = int(os.getenv("DIAS_RETROATIVOS", "30"))
    hoje = datetime.now()
    inicio = hoje - timedelta(days=dias_retroativos)
    
    data_fim = hoje.strftime("%Y-%m-%d")
    data_ini = inicio.strftime("%Y-%m-%d")
    
    # 2. Executar o Radar
    radar = RadarLicitacoes(uf=os.getenv("UF_ESTADO", "MT"))
    oportunidades = radar.buscar_oportunidades(data_inicio=data_ini, data_fim=data_fim)
    
    if oportunidades:
        # Salvar Excel e Painel Web
        radar.exportar_para_excel(oportunidades, "oportunidades_obras_mt.xlsx")
        gerar_dashboard("oportunidades_obras_mt.xlsx", "radar_obras.html")
        
        # 3. Enviar E-mail (se as credenciais existirem)
        email_remetente = os.getenv("EMAIL_REMETENTE")
        senha_remetente = os.getenv("EMAIL_SENHA") # App Password
        email_destinatario = os.getenv("EMAIL_DESTINATARIO")
        
        if email_remetente and senha_remetente and email_destinatario:
            destinatarios = [e.strip() for e in email_destinatario.split(",")]
            notificador = NotificadorEmail(
                smtp_server=os.getenv("SMTP_SERVER", "smtp.gmail.com"),
                smtp_port=int(os.getenv("SMTP_PORT", "587")),
                email_remetente=email_remetente,
                senha_remetente=senha_remetente
            )
            notificador.enviar_alerta(destinatarios=destinatarios, oportunidades=oportunidades)
        else:
            print("[Info] E-mail não configurado ou rodando em modo visual. Arquivos locais e web atualizados com sucesso.")
    else:
        print("[Info] Nenhuma nova oportunidade encontrada no período.")

if __name__ == "__main__":
    main()
