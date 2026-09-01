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

// Resolução Segura de Links Oficiais (Prevenção Total contra Erro 404)
function obterLinkSeguro(item) {
  if (!item) return 'https://pncp.gov.br';
  const link = (item['Link PNCP'] || item['LinkOficial'] || '').trim();

  // Se já for um link HTTP válido que não seja placeholder antigo
  if (link.startsWith('http') && !link.includes('lic-0') && !link.includes('alvara-') && !link.includes('example.com')) {
    return link;
  }

  // Fallback canônico oficial garantido por entidade e alimentador
  const orgao = (item['Órgão'] || item['Requerente'] || '').toUpperCase();
  const origem = (item['Origem'] || item['Alimentador'] || '').toUpperCase();

  if (orgao.includes('SESI') || orgao.includes('SENAI') || orgao.includes('FIEMT') || orgao.includes('IEL')) {
    return 'https://compras.sfiemt.ind.br/Default.aspx';
  }
  if (orgao.includes('SESC') || orgao.includes('SENAC')) {
    return 'https://transparencia-mt.sesc.com.br';
  }
  if (orgao.includes('SEBRAE')) {
    return 'https://sebrae.com.br/sites/PortalSebrae/licitacoes';
  }
  if (origem.includes('PRIVADA') || origem.includes('ALVARÁ')) {
    const mun = (item['Município'] || '').toUpperCase();
    if (mun.includes('VÁRZEA') || mun.includes('VARZEA')) {
      return 'https://diariomunicipal.org/mt/amm/';
    }
    return 'https://gazetamunicipal.cuiaba.mt.gov.br/';
  }

  // Governo / PNCP
  const proc = (item['Processo'] || '').trim();
  if (proc) {
    return `https://pncp.gov.br/app/editais?q=${encodeURIComponent(proc)}&uf=MT`;
  }
  return 'https://pncp.gov.br';
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
  document.getElementById('filtroAlimentador').addEventListener('change', aplicarFiltros);
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

// Carregar Dados da Base (JSON com Metadados de Alimentadores e Fallback)
async function carregarDados() {
  let payload = null;
  try {
    const res = await fetch('./dados_obras.json');
    if (!res.ok) throw new Error('Não foi possível carregar dados_obras.json');
    payload = await res.json();
  } catch (err) {
    console.warn('Carregamento via fetch local falhou (possível file:// protocol). Usando fallback.', err);
    if (window.DADOS_FALLBACK) {
      payload = window.DADOS_FALLBACK;
    } else {
      payload = [];
    }
  }

  if (Array.isArray(payload)) {
    AppState.dados = payload;
    AppState.metadados = {};
  } else if (payload && payload.oportunidades) {
    AppState.dados = payload.oportunidades;
    AppState.metadados = payload.metadados || {};
  } else {
    AppState.dados = [];
    AppState.metadados = {};
  }

  // Atualizar data da última varredura no cabeçalho se disponível
  const txtData = document.getElementById('txtUltimaVarredura');
  if (txtData && AppState.metadados.ultima_atualizacao) {
    txtData.textContent = `Última Varredura: ${AppState.metadados.ultima_atualizacao}`;
  }

  // Gera IDs únicos para cada edital
  AppState.dados.forEach((item, index) => {
    item._id = `edital_${index}_${(item.Processo || '').replace(/[^a-zA-Z0-9]/g, '')}`;
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
  const privadasSistemas = AppState.dados.filter(d => (d['Origem'] || '').includes('Sistema S') || (d['Origem'] || '').includes('Privada')).length;
  const volumeTotal = AppState.dados.reduce((acc, curr) => acc + (curr['Valor Estimado (R$)'] || 0), 0);

  document.getElementById('kpiTotal').textContent = total;
  document.getElementById('kpiCuiaba').textContent = cuiabaVG;
  document.getElementById('kpiPrivadasSistemas').textContent = privadasSistemas;
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
  const tabFeeders = document.getElementById('tabFeeders');
  if (tabFeeders) tabFeeders.style.display = AppState.abaAtiva === 'feeders' ? 'block' : 'none';

  if (AppState.abaAtiva === 'radar') renderizarRadar();
  if (AppState.abaAtiva === 'kanban') renderizarKanban();
  if (AppState.abaAtiva === 'charts') renderizarGraficos();
  if (AppState.abaAtiva === 'calculator') popularCalculadora();
  if (AppState.abaAtiva === 'feeders') renderizarAlimentadores();
}

// Filtros do Radar
function aplicarFiltros() {
  const busca = (document.getElementById('filtroTexto').value || '').toLowerCase();
  const alimentador = document.getElementById('filtroAlimentador').value;
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

    const matchAlimentador = !alimentador || 
      (item['Alimentador'] && item['Alimentador'].toLowerCase().includes(alimentador.toLowerCase())) ||
      (item['Origem'] && item['Origem'].toLowerCase().includes(alimentador.toLowerCase()));

    const matchRegiao = !regiao || item['Prioritária (Cuiabá/VG)'] === regiao;
    const matchCategoria = !categoria || (item['Categoria'] && item['Categoria'].toLowerCase().includes(categoria));
    
    let matchPorte = true;
    const val = item['Valor Estimado (R$)'] || 0;
    if (porte === 120000) matchPorte = val <= 120000 && val > 0;
    if (porte === 500000) matchPorte = val > 120000 && val <= 500000;
    if (porte === 1000000) matchPorte = val > 500000;

    return matchBusca && matchAlimentador && matchRegiao && matchCategoria && matchPorte;
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
  const origem = item['Origem'] || '🏛️ Governo / PNCP';

  let badgeOrigemClass = 'badge-origem-gov';
  let labelLink = 'PNCP';
  if (origem.includes('Sistema S')) {
    badgeOrigemClass = 'badge-origem-sistemas';
    labelLink = 'Edital S';
  } else if (origem.includes('Privada')) {
    badgeOrigemClass = 'badge-origem-privada';
    labelLink = 'Alvará';
  }

  return `
    <div class="tender-card" id="card_${item._id}">
      <div class="card-top">
        <div class="card-badges">
          <span class="badge ${badgeOrigemClass}">${origem}</span>
          <span class="badge ${isCuiaba ? 'badge-cuiaba' : 'badge-interior'}">
            <i class="bi bi-geo-alt-fill"></i> ${item['Município'] || 'MT'}
          </span>
          <span class="badge badge-cat">${item['Categoria'] || 'Geral'}</span>
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
        <a href="${obterLinkSeguro(item)}" target="_blank" rel="noopener noreferrer" class="btn-edital">
          <i class="bi bi-box-arrow-up-right"></i> ${labelLink}
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
  const origem = item['Origem'] || '🏛️ Governo / PNCP';

  let badgeOrigemClass = 'badge-origem-gov';
  let labelLink = 'PNCP';
  if (origem.includes('Sistema S')) {
    badgeOrigemClass = 'badge-origem-sistemas';
    labelLink = 'Edital S';
  } else if (origem.includes('Privada')) {
    badgeOrigemClass = 'badge-origem-privada';
    labelLink = 'Alvará';
  }

  return `
    <tr>
      <td style="width: 40px; text-align: center;">
        <button class="btn-fav ${isFav ? 'active' : ''}" onclick="toggleFavorito('${item._id}')">
          <i class="bi ${isFav ? 'bi-star-fill' : 'bi-star'}"></i>
        </button>
      </td>
      <td style="white-space: nowrap; font-size: 0.8rem; color: var(--text-muted);">${item['Data Publicação'] || 'N/A'}</td>
      <td>
        <span class="badge ${badgeOrigemClass}">${origem}</span><br>
        <span class="badge ${isCuiaba ? 'badge-cuiaba' : 'badge-interior'}" style="margin-top: 4px;">${item['Município'] || 'MT'}</span>
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
        <a href="${obterLinkSeguro(item)}" target="_blank" rel="noopener noreferrer" class="btn-edital" style="display: inline-flex; padding: 5px 10px; font-size: 0.78rem;">
          <i class="bi bi-box-arrow-up-right"></i> ${labelLink}
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
        <div style="display: flex; justify-content: space-between; margin-top: 10px; gap: 4px; align-items: center;">
          <a href="${obterLinkSeguro(item)}" target="_blank" rel="noopener noreferrer" style="font-size: 0.75rem; color: var(--primary); text-decoration: none; font-weight: 600;">
            <i class="bi bi-box-arrow-up-right"></i> ${item['Origem']?.includes('Sistema S') ? 'Edital S' : (item['Origem']?.includes('Privada') ? 'Diário' : 'PNCP')}
          </a>
          <button class="btn-icon" style="width: 24px; height: 24px; font-size: 11px;" onclick="abrirModalAnotacoes('${item._id}')" title="Anotações internas">
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

  const modalLink = document.getElementById('modalLinkEdital');
  if (modalLink) {
    modalLink.href = obterLinkSeguro(itemAtualModal);
    const label = itemAtualModal['Origem']?.includes('Sistema S') ? 'Portal de Compras S' : (itemAtualModal['Origem']?.includes('Privada') ? 'Diário Oficial' : 'Edital PNCP');
    modalLink.innerHTML = `<i class="bi bi-box-arrow-up-right"></i> ${label}`;
  }

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
    `📌 *Origem:* ${item['Origem'] || 'Governo'}\n` +
    `📍 *Local:* ${item['Município']}\n` +
    `🏢 *Contratante/Requerente:* ${item['Órgão']}\n` +
    `💰 *Valor Estimado:* ${formatarMoeda(item['Valor Estimado (R$)'])}\n` +
    `🏷️ *Categoria:* ${item['Categoria']}\n\n` +
    `📋 *Descrição:* ${item['Objeto']}\n\n` +
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

  const headers = ['Origem', 'Alimentador', 'Data Publicação', 'Município', 'Categoria', 'Modalidade', 'Contratante / Órgão', 'Valor Estimado (R$)', 'Processo', 'Objeto', 'Link Oficial'];
  const linhas = [headers.join(';')];

  AppState.filtrados.forEach(item => {
    const linha = [
      `"${item['Origem'] || ''}"`,
      `"${item['Alimentador'] || ''}"`,
      `"${item['Data Publicação'] || ''}"`,
      `"${item['Município'] || ''}"`,
      `"${item['Categoria'] || ''}"`,
      `"${item['Modalidade'] || ''}"`,
      `"${(item['Órgão'] || '').replace(/"/g, '""')}"`,
      `"${item['Valor Estimado (R$)'] || 0}"`,
      `"${item['Processo'] || ''}"`,
      `"${(item['Objeto'] || '').replace(/"/g, '""').replace(/[\r\n]+/g, ' ')}"`,
      `"${obterLinkSeguro(item)}"`
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

// ==========================================================================
// Central de Alimentadores (Feeders Hub)
// ==========================================================================

function renderizarAlimentadores() {
  const grid = document.getElementById('gridFeeders');
  if (!grid) return;

  const totalGov = AppState.dados.filter(d => (d['Origem'] || '').includes('Governo') || (d['Alimentador'] || '').includes('PNCP')).length;
  const totalSis = AppState.dados.filter(d => (d['Origem'] || '').includes('Sistema S') || (d['Alimentador'] || '').includes('Sistema S')).length;
  const totalAlv = AppState.dados.filter(d => (d['Origem'] || '').includes('Privada') || (d['Alimentador'] || '').includes('Alvará')).length;

  const alimentadores = [
    {
      id: 'pncp',
      classe: 'card-pncp',
      nome: '🏛️ PNCP / Compras.gov (Governo)',
      tipo: 'API Oficial Federal e Estadual',
      status: 'Online & Monitorando',
      frequencia: 'Diário às 07:00 (Automático)',
      total: totalGov,
      url: 'https://pncp.gov.br',
      filtroValor: 'PNCP',
      descricao: 'Alimentador que consulta a API nacional de Compras Públicas (Lei 14.133/2021) capturando editais de Mato Grosso de prefeituras, órgãos federais e autarquias.'
    },
    {
      id: 'sistema_s',
      classe: 'card-sistema-s',
      nome: '🏢 Sistema S (Sesi / Senai / Sesc / Sebrae)',
      tipo: 'Portais de Compras da Indústria e Comércio',
      status: 'Online & Monitorando',
      frequencia: 'Diário às 07:00 (Automático)',
      total: totalSis,
      url: 'https://licitacoes.portaldaindustria.com.br',
      filtroValor: 'Sistema S',
      descricao: 'Alimentador que monitora os portais de compras do Sistema FIEMT (Sesi/Senai), Fecomércio (Sesc/Senac) e Sebrae-MT em busca de reformas, climatização e manutenção predial.'
    },
    {
      id: 'alvaras',
      classe: 'card-alvaras',
      nome: '🏗️ Diários Oficiais (Alvarás Cuiabá/VG)',
      tipo: 'Atos de Aprovação de Projetos (SMADUS/AMM)',
      status: 'Online & Monitorando',
      frequencia: 'Diário às 07:00 (Automático)',
      total: totalAlv,
      url: 'https://gazetamunicipal.cuiaba.mt.gov.br',
      filtroValor: 'Diário Oficial',
      descricao: 'Alimentador que monitora as concessões de alvarás de construção e reformas comerciais na Gazeta Municipal de Cuiabá e Diário Oficial de Várzea Grande, descobrindo a obra antes de começar.'
    }
  ];

  grid.innerHTML = alimentadores.map(alv => `
    <div class="feeder-card ${alv.classe}">
      <div>
        <div class="feeder-top">
          <div>
            <div class="feeder-title">${alv.nome}</div>
            <div class="feeder-type">${alv.tipo}</div>
          </div>
          <span class="status-badge">
            <span class="status-dot"></span> ${alv.status}
          </span>
        </div>

        <p class="feeder-desc">${alv.descricao}</p>
      </div>

      <div>
        <div class="feeder-metrics">
          <div>
            <div class="feeder-metric-label">Frequência</div>
            <div style="font-size: 0.85rem; font-weight: 600; margin-top: 4px; color: var(--text-main);">
              <i class="bi bi-clock-history"></i> ${alv.frequencia}
            </div>
          </div>
          <div>
            <div class="feeder-metric-label">Oportunidades Ativas</div>
            <div class="feeder-metric-value" style="margin-top: 2px;">${alv.total}</div>
          </div>
        </div>

        <div class="feeder-actions">
          <button class="btn-primary" style="flex: 1; padding: 8px 12px; font-size: 0.8rem;" onclick="selecionarAlimentador('${alv.filtroValor}')">
            <i class="bi bi-funnel"></i> Filtrar Obras deste Alimentador
          </button>
          <a href="${alv.url}" target="_blank" rel="noopener noreferrer" class="btn-edital" style="padding: 8px 12px; font-size: 0.8rem;" title="Abrir Fonte Oficial">
            <i class="bi bi-box-arrow-up-right"></i>
          </a>
        </div>
      </div>
    </div>
  `).join('');
}

function selecionarAlimentador(nomeAlimentador) {
  // Define o valor do select de filtro
  const select = document.getElementById('filtroAlimentador');
  if (select) select.value = nomeAlimentador;

  // Alterna para a aba Radar
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('tabNavRadar').classList.add('active');
  AppState.abaAtiva = 'radar';
  renderizarAbaAtual();
  aplicarFiltros();
}

async function dispararVarreduraCompleta() {
  const btnNav = document.getElementById('btnSyncNav');
  const iconNav = document.getElementById('iconSyncNav');
  const btnFeeders = document.getElementById('btnSyncFeeders');

  // Ativa animação de carregamento nos botões
  if (btnNav) btnNav.disabled = true;
  if (iconNav) iconNav.classList.add('spin');
  if (btnFeeders) {
    btnFeeders.disabled = true;
    btnFeeders.innerHTML = '<i class="bi bi-arrow-repeat spin"></i> Varrendo Alimentadores...';
  }

  mostrarToast('🔄 Conectando aos alimentadores (PNCP, Sistema S e Alvarás) e varrendo novas obras...', 'info');

  try {
    // 1. Chama o endpoint serverless /api/atualizar no Vercel
    const res = await fetch('/api/atualizar', { method: 'POST' });
    if (res.ok) {
      const data = await res.json();
      if (data.oportunidades && data.oportunidades.length > 0) {
        AppState.dados = data.oportunidades;
        AppState.metadados = data.metadados || {};
      }
    } else {
      await carregarDados();
    }
  } catch (err) {
    console.warn('API serverless indisponível ou offline. Recarregando base local.', err);
    await carregarDados();
  }

  // Atualiza IDs e estado
  AppState.dados.forEach((item, index) => {
    item._id = `edital_${index}_${(item.Processo || '').replace(/[^a-zA-Z0-9]/g, '')}`;
    if (!AppState.kanban[item._id]) AppState.kanban[item._id] = 'novas';
  });

  AppState.filtrados = [...AppState.dados];
  atualizarKPIs();
  renderizarAbaAtual();
  if (AppState.abaAtiva === 'feeders') renderizarAlimentadores();

  // Restaura botões
  if (btnNav) btnNav.disabled = false;
  if (iconNav) iconNav.classList.remove('spin');
  if (btnFeeders) {
    btnFeeders.innerHTML = '<i class="bi bi-check-circle"></i> Alimentadores Atualizados!';
    setTimeout(() => {
      btnFeeders.innerHTML = '<i class="bi bi-arrow-repeat"></i> Atualizar Alimentadores';
      btnFeeders.disabled = false;
    }, 2500);
  }

  mostrarToast(`✅ Varredura concluída! ${AppState.dados.length} oportunidades ativas consolidadas.`, 'success');
}

function atualizarDadosFeeders() {
  return dispararVarreduraCompleta();
}

function mostrarToast(mensagem, tipo = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${tipo === 'success' ? 'toast-success' : 'toast-info'}`;
  toast.innerHTML = `
    <i class="bi ${tipo === 'success' ? 'bi-check-circle-fill' : 'bi-info-circle-fill'}" style="font-size: 1.1rem; color: ${tipo === 'success' ? 'var(--emerald)' : 'var(--primary)'};"></i>
    <div>${mensagem}</div>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 400);
  }, 4500);
}
