"""
Gerador de Painel Interativo HTML para o Radar de Obras
Gera um arquivo .html visual e interativo para abrir direto no navegador.
"""

import json
import pandas as pd

def gerar_dashboard(arquivo_excel="oportunidades_obras_mt.xlsx", arquivo_html="radar_obras.html"):
    df = pd.read_excel(arquivo_excel)
    
    # Prepara dados para JSON
    dados = df.to_dict(orient="records")
    
    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Radar de Obras & Licitações | Antigravity PMO</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    <style>
        body {{
            background-color: #f4f6f9;
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            color: #333;
        }}
        .header-box {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 30px 20px;
            border-radius: 12px;
            margin-bottom: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .card-stat {{
            border-radius: 10px;
            border: none;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            transition: transform 0.2s;
        }}
        .card-stat:hover {{
            transform: translateY(-3px);
        }}
        .badge-cuiaba {{
            background-color: #28a745;
            color: white;
            font-weight: 600;
        }}
        .badge-cat {{
            background-color: #e9ecef;
            color: #495057;
            font-size: 0.85rem;
            border: 1px solid #ced4da;
        }}
        .table-container {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 15px rgba(0,0,0,0.05);
        }}
        .btn-pncp {{
            background-color: #0d6efd;
            color: white;
            border-radius: 6px;
            font-size: 0.85rem;
            padding: 5px 12px;
            text-decoration: none;
        }}
        .btn-pncp:hover {{
            background-color: #0b5ed7;
            color: white;
        }}
    </style>
</head>
<body>
<div class="container-fluid py-4 px-md-5">
    
    <!-- Cabeçalho -->
    <div class="header-box d-flex justify-content-between align-items-center flex-wrap">
        <div>
            <h2 class="fw-bold mb-1"><i class="bi bi-radar"></i> Radar de Obras & Licitações (MT)</h2>
            <p class="mb-0 text-white-50">Painel Estratégico de Monitoramento de Editais e Contratações de Engenharia</p>
        </div>
        <div class="text-end mt-2 mt-md-0">
            <span class="badge bg-light text-dark px-3 py-2 fs-6"><i class="bi bi-building"></i> Construtora Familiar</span>
        </div>
    </div>

    <!-- Estatísticas Rápidas -->
    <div class="row g-3 mb-4">
        <div class="col-md-3">
            <div class="card card-stat p-3 bg-white">
                <div class="text-muted small fw-bold">TOTAL DE OPORTUNIDADES</div>
                <div class="fs-3 fw-bold text-primary" id="totalOportunidades">{len(dados)}</div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card card-stat p-3 bg-white">
                <div class="text-muted small fw-bold">REGIÃO CUIABÁ / VG</div>
                <div class="fs-3 fw-bold text-success" id="totalCuiaba">{len([d for d in dados if d.get('Prioritária (Cuiabá/VG)') == 'SIM'])}</div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card card-stat p-3 bg-white">
                <div class="text-muted small fw-bold">ATÉ R$ 120 MIL (PEQUENO PORTE)</div>
                <div class="fs-3 fw-bold text-warning" id="totalPequenoPorte">{len([d for d in dados if d.get('Valor Estimado (R$)', 0) <= 120000])}</div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card card-stat p-3 bg-white">
                <div class="text-muted small fw-bold">VALOR TOTAL MAPEADO</div>
                <div class="fs-3 fw-bold text-dark">R$ {sum([d.get('Valor Estimado (R$)', 0) for d in dados]):,.2f}</div>
            </div>
        </div>
    </div>

    <!-- Filtros -->
    <div class="card p-3 mb-4 border-0 shadow-sm">
        <div class="row g-2 align-items-center">
            <div class="col-md-4">
                <div class="input-group">
                    <span class="input-group-text bg-white"><i class="bi bi-search"></i></span>
                    <input type="text" id="filtroTexto" class="form-control" placeholder="Buscar por palavra no objeto ou órgão..." onkeyup="filtrarTabela()">
                </div>
            </div>
            <div class="col-md-3">
                <select id="filtroRegiao" class="form-select" onchange="filtrarTabela()">
                    <option value="">Todas as Regiões</option>
                    <option value="SIM">Apenas Cuiabá / Várzea Grande</option>
                    <option value="NÃO">Apenas Interior MT</option>
                </select>
            </div>
            <div class="col-md-3">
                <select id="filtroCategoria" class="form-select" onchange="filtrarTabela()">
                    <option value="">Todas as Categorias</option>
                    <option value="Reforma">Reformas / Adequações</option>
                    <option value="Construção">Construção Civil</option>
                    <option value="Manutenção">Manutenção Predial</option>
                    <option value="Instalações">Instalações / Climatização</option>
                </select>
            </div>
            <div class="col-md-2">
                <select id="filtroPorte" class="form-select" onchange="filtrarTabela()">
                    <option value="">Todos os Valores</option>
                    <option value="120000">Até R$ 120k (Ideal)</option>
                    <option value="300000">Até R$ 300k</option>
                </select>
            </div>
        </div>
    </div>

    <!-- Tabela de Oportunidades -->
    <div class="table-container">
        <div class="table-responsive">
            <table class="table table-hover align-middle mb-0" id="tabelaObras">
                <thead class="table-light">
                    <tr>
                        <th>Data</th>
                        <th>Município</th>
                        <th>Categoria</th>
                        <th>Órgão</th>
                        <th>Objeto do Edital</th>
                        <th class="text-end">Valor Estimado</th>
                        <th class="text-center">Ação</th>
                    </tr>
                </thead>
                <tbody id="corpoTabela">
                </tbody>
            </table>
        </div>
    </div>

</div>

<script>
    const dadosObras = {json.dumps(dados, ensure_ascii=False)};

    function formatarMoeda(valor) {{
        return new Intl.NumberFormat('pt-BR', {{ style: 'currency', currency: 'BRL' }}).format(valor);
    }}

    function renderizarTabela(lista) {{
        const tbody = document.getElementById('corpoTabela');
        tbody.innerHTML = '';

        if (lista.length === 0) {{
            tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-muted">Nenhum edital encontrado com os filtros atuais.</td></tr>';
            return;
        }}

        lista.forEach(item => {{
            const tr = document.createElement('tr');
            
            const isPrioritaria = item['Prioritária (Cuiabá/VG)'] === 'SIM';
            const badgeRegiao = isPrioritaria 
                ? `<span class="badge badge-cuiaba"><i class="bi bi-geo-alt-fill"></i> ${{item['Município']}}</span>` 
                : `<span class="badge bg-secondary">${{item['Município']}}</span>`;

            tr.innerHTML = `
                <td style="white-space: nowrap;"><small class="text-muted">${{item['Data Publicação'] || 'N/A'}}</small></td>
                <td>${{badgeRegiao}}</td>
                <td><span class="badge badge-cat">${{item['Categoria']}}</span></td>
                <td><strong>${{item['Órgão']}}</strong></td>
                <td><small>${{item['Objeto']}}</small></td>
                <td class="text-end fw-bold text-primary" style="white-space: nowrap;">${{formatarMoeda(item['Valor Estimado (R$)'] || 0)}}</td>
                <td class="text-center">
                    <a href="${{item['Link PNCP']}}" target="_blank" class="btn btn-pncp">
                        <i class="bi bi-box-arrow-up-right"></i> Ver Edital
                    </a>
                </td>
            `;
            tbody.appendChild(tr);
        }});
    }}

    function filtrarTabela() {{
        const busca = document.getElementById('filtroTexto').value.toLowerCase();
        const regiao = document.getElementById('filtroRegiao').value;
        const categoria = document.getElementById('filtroCategoria').value.toLowerCase();
        const porte = parseFloat(document.getElementById('filtroPorte').value) || 0;

        const filtrados = dadosObras.filter(item => {{
            const matchTexto = !busca || 
                (item['Objeto'] && item['Objeto'].toLowerCase().includes(busca)) ||
                (item['Órgão'] && item['Órgão'].toLowerCase().includes(busca)) ||
                (item['Município'] && item['Município'].toLowerCase().includes(busca));

            const matchRegiao = !regiao || item['Prioritária (Cuiabá/VG)'] === regiao;
            const matchCategoria = !categoria || (item['Categoria'] && item['Categoria'].toLowerCase().includes(categoria));
            const matchPorte = !porte || (item['Valor Estimado (R$)'] <= porte);

            return matchTexto && matchRegiao && matchCategoria && matchPorte;
        }});

        renderizarTabela(filtrados);
    }}

    // Inicialização
    renderizarTabela(dadosObras);
</script>
</body>
</html>
"""

    with open(arquivo_html, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"[OK] Dashboard interativo gerado: {arquivo_html}")
    return arquivo_html

if __name__ == "__main__":
    gerar_dashboard()
