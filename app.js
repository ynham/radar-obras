/* ==========================================================================
   RADAR OBRAS MT - APP.JS
   Motor de Inteligência, Filtros Dinâmicos, CRM Kanban e Cálculos de Obras
   ========================================================================== */

// Estado Global da Aplicação
const AppState = {
  dados: [],
  filtrados: [],
  visualizacao: 'grid', // 'grid' | 'table'
  abaAtiva: 'radar',    // 'radar' | 'kanban' | 'charts' | 'calculator'
  tema: localStorage.getItem('radar_tema') || 'light',
  favoritos: JSON.parse(localStorage.getItem('radar_favs') || '[]'),
  anotacoes: JSON.parse(localStorage.getItem('radar_notes') || '{}'),
  kanban: JSON.parse(localStorage.getItem('radar_kanban') || '{}'),
  charts: {}
};

// Formatação Moeda Brasileira
function formatarMoeda(valor) {
  if (isNaN(valor) || valor === null || valor === undefined) return 'R$ 0,00';
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor);
}

// Inicialização Principal
document.addEventListener('DOMContentLoaded', async () => {
  aplicarTema(AppState.tema);
  configurarEventosUI();
  await carregarDados();
  atualizarKPIs();
  renderizarAbaAtual();
});

// Configura Listeners de Navegação e Filtros
function configurarEventosUI() {
  // Alternar Tema
  document.getElementById('btnTema').addEventListener('click', () => {
    AppState.tema = AppState.tema === 'light' ? 'dark' : 'light';
    localStorage.setItem('radar_tema', AppState.tema);
    aplicarTema(AppState.tema);
    if (AppState.abaAtiva === 'charts') renderizarGraficos();
  });

  // Alternar Abas
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      AppState.abaAtiva = btn.getAttribute('data-tab');
      renderizarAbaAtual();
    });
  });

  // Filtros em Tempo Real
  document.getElementById('filtroTexto').addEventListener('input', debounce(aplicarFiltros, 250));
  document.getElementById('filtroRegiao').addEventListener('change', aplicarFiltros);
  document.getElementById('filtroCategoria').addEventListener('change', aplicarFiltros);
  document.getElementById('filtroPorte').addEventListener('change', aplicarFiltros);
  document.getElementById('filtroOrdenacao').addEventListener('change', aplicarFiltros);

  // Alternar Grid / Tabela
  document.getElementById('btnViewGrid').addEventListener('click', () => {
    AppState.visualizacao = 'grid';
    document.getElementById('btnViewGrid').classList.add('active');
    document.getElementById('btnViewTable').classList.remove('active');
    renderizarRadar();
  });

  document.getElementById('btnViewTable').addEventListener('click', () => {
    AppState.visualizacao = 'table';
    document.getElementById('btnViewTable').classList.add('active');
    document.getElementById('btnViewGrid').classList.remove('active');
    renderizarRadar();
  });

  // Exportar Excel
  document.getElementById('btnExportar').addEventListener('click', exportarParaCSV);

  // Modal Fechar
  document.getElementById('btnFecharModal').addEventListener('click', fecharModal);
  document.getElementById('modalBackdrop').addEventListener('click', (e) => {
    if (e.target.id === 'modalBackdrop') fecharModal();
  });
}

function aplicarTema(tema) {
  document.documentElement.setAttribute('data-theme', tema);
  const icon = document.getElementById('iconTema');
  if (icon) {
    icon.className = tema === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-stars-fill';
  }
}

// Carregar Dados da Base (JSON com Fallback Local)
async function carregarDados() {
  try {
    const res = await fetch('./dados_obras.json');
    if (!res.ok) throw new Error('Não foi possível carregar dados_obras.json');
    AppState.dados = await res.json();
  } catch (err) {
    console.warn('Carregamento via fetch local falhou (possível file:// protocol). Usando fallback.', err);
    if (window.DADOS_FALLBACK && Array.isArray(window.DADOS_FALLBACK)) {
      AppState.dados = window.DADOS_FALLBACK;
    } else {
      AppState.dados = [];
    }
  }

  // Gera IDs únicos para cada edital
  AppState.dados.forEach((item, index) => {
    item._id = `edital_${index}_${(item.Processo || '').replace(/[^a-zA-Z0-9]/g, '')}`;
    // Se não tiver status no kanban, define como 'novas'
    if (!AppState.kanban[item._id]) {
      AppState.kanban[item._id] = 'novas';
    }
  });

  AppState.filtrados = [...AppState.dados];
}

// Atualizar Indicadores no Topo
function atualizarKPIs() {
  const total = AppState.dados.length;
  const cuiabaVG = AppState.dados.filter(d => d['Prioritária (Cuiabá/VG)'] === 'SIM').length;
  const pequenoPorte = AppState.dados.filter(d => (d['Valor Estimado (R$)'] || 0) <= 120000 && (d['Valor Estimado (R$)'] || 0) > 0).length;
  const volumeTotal = AppState.dados.reduce((acc, curr) => acc + (curr['Valor Estimado (R$)'] || 0), 0);

  document.getElementById('kpiTotal').textContent = total;
  document.getElementById('kpiCuiaba').textContent = cuiabaVG;
  document.getElementById('kpiPequenoPorte').textContent = pequenoPorte;
  document.getElementById('kpiVolume').textContent = formatarMoeda(volumeTotal);

  document.getElementById('badgeTotalAba').textContent = total;
  
  // Atualizar badge do funil (obras em análise/orçamento)
  const ativasNoFunil = Object.values(AppState.kanban).filter(st => ['analise', 'orcamento', 'proposta'].includes(st)).length;
  document.getElementById('badgeFunilAba').textContent = ativasNoFunil;
}

// Renderizar Conforme a Aba Ativa
function renderizarAbaAtual() {
  document.getElementById('tabRadar').style.display = AppState.abaAtiva === 'radar' ? 'block' : 'none';
  document.getElementById('tabKanban').style.display = AppState.abaAtiva === 'kanban' ? 'block' : 'none';
  document.getElementById('tabCharts').style.display = AppState.abaAtiva === 'charts' ? 'block' : 'none';
  document.getElementById('tabCalculator').style.display = AppState.abaAtiva === 'calculator' ? 'block' : 'none';

  if (AppState.abaAtiva === 'radar') renderizarRadar();
  if (AppState.abaAtiva === 'kanban') renderizarKanban();
  if (AppState.abaAtiva === 'charts') renderizarGraficos();
  if (AppState.abaAtiva === 'calculator') popularCalculadora();
}

// Filtros do Radar
function aplicarFiltros() {
  const busca = (document.getElementById('filtroTexto').value || '').toLowerCase();
  const regiao = document.getElementById('filtroRegiao').value;
  const categoria = document.getElementById('filtroCategoria').value.toLowerCase();
  const porte = parseFloat(document.getElementById('filtroPorte').value) || 0;
  const ordenacao = document.getElementById('filtroOrdenacao').value;

  AppState.filtrados = AppState.dados.filter(item => {
    const matchBusca = !busca || 
      (item['Objeto'] && item['Objeto'].toLowerCase().includes(busca)) ||
      (item['Órgão'] && item['Órgão'].toLowerCase().includes(busca)) ||
      (item['Município'] && item['Município'].toLowerCase().includes(busca)) ||
      (item['Processo'] && String(item['Processo']).toLowerCase().includes(busca));

    const matchRegiao = !regiao || item['Prioritária (Cuiabá/VG)'] === regiao;
    const matchCategoria = !categoria || (item['Categoria'] && item['Categoria'].toLowerCase().includes(categoria));
    
    let matchPorte = true;
    const val = item['Valor Estimado (R$)'] || 0;
    if (porte === 120000) matchPorte = val <= 120000 && val > 0;
    if (porte === 500000) matchPorte = val > 120000 && val <= 500000;
    if (porte === 1000000) matchPorte = val > 500000;

    return matchBusca && matchRegiao && matchCategoria && matchPorte;
  });

  // Ordenação
  if (ordenacao === 'maior_valor') {
    AppState.filtrados.sort((a, b) => (b['Valor Estimado (R$)'] || 0) - (a['Valor Estimado (R$)'] || 0));
  } else if (ordenacao === 'menor_valor') {
    AppState.filtrados.sort((a, b) => (a['Valor Estimado (R$)'] || 0) - (b['Valor Estimado (R$)'] || 0));
  } else {
    // data_recente
    AppState.filtrados.sort((a, b) => new Date(b['Data Publicação'] || 0) - new Date(a['Data Publicação'] || 0));
  }

  renderizarRadar();
}

// Renderizar Lista de Editais (Grid ou Tabela)
function renderizarRadar() {
  const containerGrid = document.getElementById('gridOportunidades');
  const containerTable = document.getElementById('wrapperTabela');
  const tbody = document.getElementById('corpoTabela');
  const vazioMsg = document.getElementById('msgVazio');

  if (AppState.filtrados.length === 0) {
    containerGrid.style.display = 'none';
    containerTable.style.display = 'none';
    vazioMsg.style.display = 'block';
    return;
  }

  vazioMsg.style.display = 'none';

  if (AppState.visualizacao === 'grid') {
    containerGrid.style.display = 'grid';
    containerTable.style.display = 'none';
    containerGrid.innerHTML = AppState.filtrados.map(item => criarCardEdital(item)).join('');
  } else {
    containerGrid.style.display = 'none';
    containerTable.style.display = 'block';
    tbody.innerHTML = AppState.filtrados.map(item => criarLinhaTabela(item)).join('');
  }
}

// Criação do Card de Edital
function criarCardEdital(item) {
  const isCuiaba = item['Prioritária (Cuiabá/VG)'] === 'SIM';
  const isFav = AppState.favoritos.includes(item._id);
  const temNotas = !!AppState.anotacoes[item._id];
  const statusKanban = AppState.kanban[item._id] || 'novas';

  return `
    <div class="tender-card" id="card_${item._id}">
      <div class="card-top">
        <div class="card-badges">
          <span class="badge ${isCuiaba ? 'badge-cuiaba' : 'badge-interior'}">
            <i class="bi bi-geo-alt-fill"></i> ${item['Município'] || 'MT'}
          </span>
          <span class="badge badge-cat">${item['Categoria'] || 'Geral'}</span>
          <span class="badge badge-dispensa">${item['Modalidade'] || 'Edital'}</span>
        </div>
        <button class="btn-fav ${isFav ? 'active' : ''}" onclick="toggleFavorito('${item._id}')" title="Marcar como Favorito">
          <i class="bi ${isFav ? 'bi-star-fill' : 'bi-star'}"></i>
        </button>
      </div>

      <div class="card-orgao">${item['Órgão'] || 'Órgão Público'}</div>
      <div class="card-objeto" title="${item['Objeto'] || ''}">
        ${item['Objeto'] || 'Objeto não informado'}
      </div>

      <div class="card-meta">
        <div>
          <div class="meta-valor-label">Valor Estimado</div>
          <div class="meta-valor">${formatarMoeda(item['Valor Estimado (R$)'])}</div>
        </div>
        <div class="meta-date">
          <i class="bi bi-calendar3"></i> ${item['Data Publicação'] || 'N/A'}<br>
          <small class="text-muted">Proc: ${item['Processo'] || '-'}</small>
        </div>
      </div>

      <div class="card-actions">
        <a href="${item['Link PNCP'] || '#'}" target="_blank" rel="noopener noreferrer" class="btn-edital">
          <i class="bi bi-box-arrow-up-right"></i> PNCP
        </a>
        
        <button class="btn-card-action" onclick="abrirModalAnotacoes('${item._id}')" title="Anotações da Construtora">
          <i class="bi ${temNotas ? 'bi-pencil-square text-primary' : 'bi-pencil'}"></i>
        </button>

        <button class="btn-card-action" onclick="compartilharWhatsApp('${item._id}')" title="Compartilhar no WhatsApp">
          <i class="bi bi-whatsapp text-success"></i>
        </button>

        <select class="select-filter" style="min-width: 120px; font-size: 0.78rem; padding: 6px 10px;" onchange="alterarStatusKanban('${item._id}', this.value)">
          <option value="novas" ${statusKanban === 'novas' ? 'selected' : ''}>📥 Nova</option>
          <option value="analise" ${statusKanban === 'analise' ? 'selected' : ''}>🔍 Análise</option>
          <option value="orcamento" ${statusKanban === 'orcamento' ? 'selected' : ''}>📊 Orçamento</option>
          <option value="proposta" ${statusKanban === 'proposta' ? 'selected' : ''}>💼 Proposta</option>
          <option value="ganha" ${statusKanban === 'ganha' ? 'selected' : ''}>🏆 Ganha</option>
          <option value="descartada" ${statusKanban === 'descartada' ? 'selected' : ''}>❌ Descartar</option>
        </select>
      </div>
    </div>
  `;
}

// Criação da Linha da Tabela
function criarLinhaTabela(item) {
  const isCuiaba = item['Prioritária (Cuiabá/VG)'] === 'SIM';
  const isFav = AppState.favoritos.includes(item._id);

  return `
    <tr>
      <td style="width: 40px; text-align: center;">
        <button class="btn-fav ${isFav ? 'active' : ''}" onclick="toggleFavorito('${item._id}')">
          <i class="bi ${isFav ? 'bi-star-fill' : 'bi-star'}"></i>
        </button>
      </td>
      <td style="white-space: nowrap; font-size: 0.8rem; color: var(--text-muted);">${item['Data Publicação'] || 'N/A'}</td>
      <td>
        <span class="badge ${isCuiaba ? 'badge-cuiaba' : 'badge-interior'}">${item['Município'] || 'MT'}</span>
      </td>
      <td><span class="badge badge-cat">${item['Categoria'] || 'Geral'}</span></td>
      <td>
        <strong style="color: var(--primary); font-size: 0.82rem;">${item['Órgão'] || ''}</strong><br>
        <small style="color: var(--text-muted);">${(item['Objeto'] || '').substring(0, 140)}...</small>
      </td>
      <td style="text-align: right; font-weight: 700; white-space: nowrap; color: var(--text-main);">
        ${formatarMoeda(item['Valor Estimado (R$)'])}
      </td>
      <td style="text-align: center; white-space: nowrap;">
        <a href="${item['Link PNCP'] || '#'}" target="_blank" class="btn-edital" style="display: inline-flex; padding: 5px 10px; font-size: 0.78rem;">
          <i class="bi bi-box-arrow-up-right"></i> Ver
        </a>
      </td>
    </tr>
  `;
}

// ==========================================================================
// Módulo do Funil Comercial (Kanban)
// ==========================================================================

function renderizarKanban() {
  const colunas = {
    novas: document.getElementById('colNovas'),
    analise: document.getElementById('colAnalise'),
    orcamento: document.getElementById('colOrcamento'),
    proposta: document.getElementById('colProposta'),
    ganha: document.getElementById('colGanha')
  };

  // Limpa cards das colunas
  Object.values(colunas).forEach(col => col.innerHTML = '');

  const contadores = { novas: 0, analise: 0, orcamento: 0, proposta: 0, ganha: 0 };

  AppState.dados.forEach(item => {
    const status = AppState.kanban[item._id] || 'novas';
    if (status === 'descartada') return; // Oculta da visão rápida do funil

    if (colunas[status]) {
      contadores[status]++;
      const nota = AppState.anotacoes[item._id];
      const cardEl = document.createElement('div');
      cardEl.className = 'kanban-card';
      cardEl.innerHTML = `
        <div class="kanban-card-title">${item['Órgão'] || 'Órgão'}</div>
        <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 6px;">${item['Município']} • ${item['Categoria']}</div>
        <div class="kanban-card-val">${formatarMoeda(item['Valor Estimado (R$)'])}</div>
        ${nota ? `<div class="kanban-notes-preview"><i class="bi bi-chat-text"></i> ${nota}</div>` : ''}
        <div style="display: flex; justify-content: space-between; margin-top: 10px; gap: 4px;">
          <a href="${item['Link PNCP']}" target="_blank" style="font-size: 0.75rem; color: var(--primary); text-decoration: none;">
            <i class="bi bi-box-arrow-up-right"></i> PNCP
          </a>
          <button class="btn-icon" style="width: 24px; height: 24px; font-size: 11px;" onclick="abrirModalAnotacoes('${item._id}')">
            <i class="bi bi-pencil"></i>
          </button>
        </div>
      `;
      colunas[status].appendChild(cardEl);
    }
  });

  // Atualizar Contadores de cada coluna
  document.getElementById('cntNovas').textContent = contadores.novas;
  document.getElementById('cntAnalise').textContent = contadores.analise;
  document.getElementById('cntOrcamento').textContent = contadores.orcamento;
  document.getElementById('cntProposta').textContent = contadores.proposta;
  document.getElementById('cntGanha').textContent = contadores.ganha;
}

function alterarStatusKanban(id, novoStatus) {
  AppState.kanban[id] = novoStatus;
  localStorage.setItem('radar_kanban', JSON.stringify(AppState.kanban));
  atualizarKPIs();
  if (AppState.abaAtiva === 'kanban') renderizarKanban();
}

// ==========================================================================
// Modal de Anotações Internas
// ==========================================================================

let itemAtualModal = null;

function abrirModalAnotacoes(id) {
  itemAtualModal = AppState.dados.find(d => d._id === id);
  if (!itemAtualModal) return;

  document.getElementById('modalOrgao').textContent = itemAtualModal['Órgão'] || 'Edital';
  document.getElementById('modalObjeto').textContent = itemAtualModal['Objeto'] || '';
  document.getElementById('modalValor').textContent = formatarMoeda(itemAtualModal['Valor Estimado (R$)']);
  document.getElementById('textareaNotas').value = AppState.anotacoes[id] || '';

  document.getElementById('modalBackdrop').classList.add('show');
}

function fecharModal() {
  document.getElementById('modalBackdrop').classList.remove('show');
}

document.getElementById('btnSalvarNotas').addEventListener('click', () => {
  if (!itemAtualModal) return;
  const texto = document.getElementById('textareaNotas').value.trim();
  if (texto) {
    AppState.anotacoes[itemAtualModal._id] = texto;
  } else {
    delete AppState.anotacoes[itemAtualModal._id];
  }
  localStorage.setItem('radar_notes', JSON.stringify(AppState.anotacoes));
  fecharModal();
  renderizarAbaAtual();
});

// ==========================================================================
// Favoritos & Compartilhamento WhatsApp
// ==========================================================================

function toggleFavorito(id) {
  const index = AppState.favoritos.indexOf(id);
  if (index > -1) {
    AppState.favoritos.splice(index, 1);
  } else {
    AppState.favoritos.push(id);
  }
  localStorage.setItem('radar_favs', JSON.stringify(AppState.favoritos));
  renderizarRadar();
}

function compartilharWhatsApp(id) {
  const item = AppState.dados.find(d => d._id === id);
  if (!item) return;

  const texto = `🏗️ *OPORTUNIDADE DE OBRA (MT)*\n\n` +
    `📍 *Local:* ${item['Município']}\n` +
    `🏢 *Órgão:* ${item['Órgão']}\n` +
    `💰 *Valor:* ${formatarMoeda(item['Valor Estimado (R$)'])}\n` +
    `🏷️ *Categoria:* ${item['Categoria']}\n\n` +
    `📋 *Objeto:* ${item['Objeto']}\n\n` +
    `🔗 *Link Oficial:* ${item['Link PNCP']}`;

  const url = `https://api.whatsapp.com/send?text=${encodeURIComponent(texto)}`;
  window.open(url, '_blank');
}

// ==========================================================================
// Gráficos e Métricas com Chart.js
// ==========================================================================

function renderizarGraficos() {
  if (typeof Chart === 'undefined') return;

  const isDark = AppState.tema === 'dark';
  const textColor = isDark ? '#9ca3af' : '#64748b';

  // 1. Gráfico de Categorias
  const catCounts = {};
  AppState.dados.forEach(d => {
    const c = d['Categoria'] || 'Outros';
    catCounts[c] = (catCounts[c] || 0) + 1;
  });

  const ctxCat = document.getElementById('chartCategorias').getContext('2d');
  if (AppState.charts.categorias) AppState.charts.categorias.destroy();
  AppState.charts.categorias = new Chart(ctxCat, {
    type: 'doughnut',
    data: {
      labels: Object.keys(catCounts),
      datasets: [{
        data: Object.values(catCounts),
        backgroundColor: ['#2563eb', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4'],
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'bottom', labels: { color: textColor, font: { family: 'Inter', size: 11 } } }
      }
    }
  });

  // 2. Gráfico de Top Cidades
  const cityCounts = {};
  AppState.dados.forEach(d => {
    const m = d['Município'] || 'Não especificado';
    cityCounts[m] = (cityCounts[m] || 0) + 1;
  });

  const topCities = Object.entries(cityCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6);

  const ctxCity = document.getElementById('chartCidades').getContext('2d');
  if (AppState.charts.cidades) AppState.charts.cidades.destroy();
  AppState.charts.cidades = new Chart(ctxCity, {
    type: 'bar',
    data: {
      labels: topCities.map(c => c[0]),
      datasets: [{
        label: 'Editais',
        data: topCities.map(c => c[1]),
        backgroundColor: '#3b82f6',
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      scales: {
        y: { ticks: { color: textColor }, grid: { color: isDark ? '#1f2937' : '#f1f5f9' } },
        x: { ticks: { color: textColor }, grid: { display: false } }
      },
      plugins: {
        legend: { display: false }
      }
    }
  });
}

// ==========================================================================
// Calculadora de Viabilidade / BDI
// ==========================================================================

function popularCalculadora() {
  const select = document.getElementById('calcSelectObra');
  select.innerHTML = '<option value="">-- Selecione uma obra para carregar o valor estimado --</option>' +
    AppState.dados.map(d => `<option value="${d['Valor Estimado (R$)'] || 0}">${d['Município']} - ${formatarMoeda(d['Valor Estimado (R$)'])} (${(d['Objeto'] || '').substring(0, 50)}...)</option>`).join('');

  select.onchange = () => {
    if (select.value) {
      document.getElementById('calcValorEdital').value = select.value;
      recalcularBDI();
    }
  };

  ['calcValorEdital', 'calcCustoDireto', 'calcBDI'].forEach(id => {
    document.getElementById(id).addEventListener('input', recalcularBDI);
  });
}

function recalcularBDI() {
  const valorEdital = parseFloat(document.getElementById('calcValorEdital').value) || 0;
  const custoDireto = parseFloat(document.getElementById('calcCustoDireto').value) || (valorEdital * 0.75);
  const bdiPercent = parseFloat(document.getElementById('calcBDI').value) || 25;

  const precoProposta = custoDireto * (1 + (bdiPercent / 100));
  const margemBruta = precoProposta - custoDireto;
  const descontoEdital = valorEdital > 0 ? ((valorEdital - precoProposta) / valorEdital) * 100 : 0;

  document.getElementById('resPrecoProposta').textContent = formatarMoeda(precoProposta);
  document.getElementById('resMargemBruta').textContent = formatarMoeda(margemBruta);
  document.getElementById('resDescontoEdital').textContent = `${descontoEdital.toFixed(1)}% abaixo do teto`;
}

// ==========================================================================
// Exportar para CSV / Excel
// ==========================================================================

function exportarParaCSV() {
  if (!AppState.filtrados.length) return alert('Nenhum edital na lista para exportar.');

  const headers = ['Data Publicação', 'Município', 'Categoria', 'Modalidade', 'Órgão', 'Valor Estimado (R$)', 'Processo', 'Objeto', 'Link PNCP'];
  const linhas = [headers.join(';')];

  AppState.filtrados.forEach(item => {
    const linha = [
      `"${item['Data Publicação'] || ''}"`,
      `"${item['Município'] || ''}"`,
      `"${item['Categoria'] || ''}"`,
      `"${item['Modalidade'] || ''}"`,
      `"${(item['Órgão'] || '').replace(/"/g, '""')}"`,
      `"${item['Valor Estimado (R$)'] || 0}"`,
      `"${item['Processo'] || ''}"`,
      `"${(item['Objeto'] || '').replace(/"/g, '""')}"`,
      `"${item['Link PNCP'] || ''}"`
    ];
    linhas.push(linha.join(';'));
  });

  const blob = new Blob(['\uFEFF' + linhas.join('\r\n')], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', `radar_obras_mt_${new Date().toISOString().slice(0, 10)}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// Utilitário de Debounce
function debounce(fn, delay) {
  let timer;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}
