"""
Módulo de Envio de Alertas por E-mail - Antigravity PMO
Envia um relatório HTML formatado com as oportunidades de licitação encontradas.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Dict, Any

class NotificadorEmail:
    def __init__(self, smtp_server: str = "smtp.gmail.com", smtp_port: int = 587, 
                 email_remetente: str = "", senha_remetente: str = ""):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email_remetente = email_remetente
        self.senha_remetente = senha_remetente

    def _gerar_corpo_html(self, oportunidades: List[Dict[str, Any]]) -> str:
        linhas_tabela = ""
        for op in oportunidades:
            valor_fmt = f"R$ {op.get('Valor Estimado (R$)', 0):,.2f}"
            is_cuiaba = op.get('Prioritária (Cuiabá/VG)') == 'SIM'
            cor_cidade = "#28a745" if is_cuiaba else "#6c757d"
            
            linhas_tabela += f"""
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 12px; font-size: 13px; color: #64748b;">{op.get('Data Publicação', 'N/A')}</td>
                <td style="padding: 12px; font-weight: bold; color: {cor_cidade};">{op.get('Município', 'N/A')}</td>
                <td style="padding: 12px; font-size: 13px;"><span style="background: #e2e8f0; padding: 3px 8px; border-radius: 4px;">{op.get('Categoria', 'N/A')}</span></td>
                <td style="padding: 12px; font-size: 13px; color: #1e293b;"><b>{op.get('Órgão', 'N/A')}</b><br><small style="color: #64748b;">{op.get('Objeto', '')[:120]}...</small></td>
                <td style="padding: 12px; font-weight: bold; color: #0f172a; text-align: right; white-space: nowrap;">{valor_fmt}</td>
                <td style="padding: 12px; text-align: center;">
                    <a href="{op.get('Link PNCP', '#')}" style="background-color: #2563eb; color: white; padding: 6px 12px; border-radius: 6px; text-decoration: none; font-size: 12px; font-weight: 500;" target="_blank">Acessar Edital</a>
                </td>
            </tr>
            """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px;">
            <div style="max-width: 800px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                
                <!-- Cabeçalho -->
                <div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 30px; color: #ffffff;">
                    <h1 style="margin: 0 0 8px 0; font-size: 24px; font-weight: 700;">Radar de Obras & Licitações (MT)</h1>
                    <p style="margin: 0; font-size: 14px; opacity: 0.9;">Novas oportunidades de engenharia civil identificadas pelo monitor automático.</p>
                </div>

                <!-- Resumo -->
                <div style="padding: 20px 30px; background: #f1f5f9; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between;">
                    <span style="font-size: 14px; color: #475569;"><b>Total de Oportunidades:</b> {len(oportunidades)}</span>
                </div>

                <!-- Tabela -->
                <div style="padding: 20px 30px;">
                    <table style="width: 100%; border-collapse: collapse; text-align: left;">
                        <thead>
                            <tr style="background: #f8fafc; border-bottom: 2px solid #cbd5e1; color: #475569; font-size: 12px; text-transform: uppercase;">
                                <th style="padding: 10px;">Data</th>
                                <th style="padding: 10px;">Município</th>
                                <th style="padding: 10px;">Tipo</th>
                                <th style="padding: 10px;">Órgão / Objeto</th>
                                <th style="padding: 10px; text-align: right;">Valor Estimado</th>
                                <th style="padding: 10px; text-align: center;">Link</th>
                            </tr>
                        </thead>
                        <tbody>
                            {linhas_tabela}
                        </tbody>
                    </table>
                </div>

                <!-- Rodapé -->
                <div style="background: #f8fafc; padding: 20px 30px; border-top: 1px solid #e2e8f0; text-align: center; color: #94a3b8; font-size: 12px;">
                    <p style="margin: 0;">Monitor de Editais • Desenvolvido com Antigravity PMO</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html

    def enviar_alerta(self, destinatarios: List[str], oportunidades: List[Dict[str, Any]]) -> bool:
        if not oportunidades:
            print("[E-mail] Nenhuma oportunidade encontrada para envio.")
            return False

        if not self.email_remetente or not self.senha_remetente:
            print("[E-mail] Credenciais de e-mail não configuradas. Simulação de envio concluída.")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🚨 [Radar de Obras] {len(oportunidades)} Oportunidades Identificadas em MT"
        msg["From"] = self.email_remetente
        msg["To"] = ", ".join(destinatarios)

        corpo_html = self._gerar_corpo_html(oportunidades)
        msg.attach(MIMEText(corpo_html, "html"))

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_remetente, self.senha_remetente)
                server.sendmail(self.email_remetente, destinatarios, msg.as_string())
            print(f"[E-mail] Alerta enviado com sucesso para: {', '.join(destinatarios)}")
            return True
        except Exception as e:
            print(f"[E-mail] Erro ao enviar e-mail: {e}")
            return False
