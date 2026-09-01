# 🏗️ Radar de Obras & Licitações (Mato Grosso) - Antigravity PMO

Sistema inteligente de monitoramento, filtragem e alerta automático de editais de engenharia civil e reformas no **PNCP / Compras.gov.br**.

---

## 🌟 Funcionalidades
1. **Varredura Automática:** Robô na nuvem que pesquisa diariamente editais no estado de MT.
2. **Filtro Especializado:** Identifica reformas, construções, manutenção predial, pavimentação e instalações elétricas/climatização.
3. **Alertas por E-mail:** Envia diariamente um e-mail formatado em HTML com as novas oportunidades encontradas.
4. **Painel Web Online:** Dashboard interativo acessível pelo celular ou computador em qualquer lugar (via GitHub Pages).

---

## 🚀 Como Colocar 100% Online (Passo a Passo)

### 1. Criar um Repositório no GitHub
1. Acesse [github.com](https://github.com) e crie um novo repositório chamado `radar-obras` (pode ser **Público** ou **Privado**).
2. Suba todos os arquivos desta pasta `radar_licitacoes` para lá.

### 2. Configurar os E-mails para o Alerta (Secrets do GitHub)
No seu repositório no GitHub:
1. Vá em **Settings** > **Secrets and variables** > **Actions**.
2. Clique em **New repository secret** e adicione 3 variáveis:
   * `EMAIL_REMETENTE`: Seu e-mail do Gmail que vai enviar o alerta (ex: `seugmail@gmail.com`).
   * `EMAIL_SENHA`: Senha de aplicativo do Gmail (*App Password* de 16 letras gerada na sua conta Google).
   * `EMAIL_DESTINATARIO`: E-mail(s) que vão receber os alertas (ex: `voce@email.com, namorada@email.com`).

### 3. Ativar o Site Online (GitHub Pages)
1. No repositório, vá em **Settings** > **Pages**.
2. Em **Source**, selecione **Deploy from a branch** e escolha a branch `gh-pages` (ou `main`).
3. O GitHub vai te dar um link online (ex: `https://seu-usuario.github.io/radar-obras/`) que você e sua namorada podem acessar direto do celular a qualquer hora!

---

## 💻 Como Rodar Localmente (no seu computador)
Caso queira rodar um teste no seu próprio PC:
```bash
pip install -r requirements.txt
python radar_obras.py
```
O arquivo `radar_obras.html` será gerado/atualizado na pasta.
