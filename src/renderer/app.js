/**
 * 采购管理系统 V3.0.0 - 主应用逻辑
 * Electron + 原生 DOM 架构
 */

// ── 全局状态 ──
const AppState = {
  currentPage: 'dashboard',
  sidebarCollapsed: false,
  isMaximized: false,
  theme: 'classic_blue',
  mode: 'light',
  settings: {},
  dataCache: {},
};

// ═══════════════════════════════════════════════════════
// 导航配置
// ═══════════════════════════════════════════════════════
const NAV_ITEMS = [
  { key: 'dashboard',  label: '看板', icon: 'dashboard' },
  { key: 'packaging',  label: '下单', icon: 'packaging' },
  { key: 'plan',       label: '计划', icon: 'plan' },
  { key: 'quotation',  label: '报价', icon: 'quotation' },
  { key: 'compare',    label: '比价', icon: 'compare' },
  { key: 'contract',   label: '合同', icon: 'contract' },
  { key: 'supplier',   label: '厂家', icon: 'supplier' },
  { key: 'query',      label: '台账', icon: 'query' },
  { key: 'product_bom', label: 'BOM',  icon: 'product_bom' },
  { key: 'collection', label: '应付', icon: 'collection' },
  { key: 'purchase',   label: '垫付', icon: 'purchase' },
  { key: 'travel',     label: '差旅', icon: 'travel' },
  { key: 'memo',       label: '备忘', icon: 'memo' },
];

const PAGE_TITLES = {
  dashboard: '看板', packaging: '下单', plan: '计划', quotation: '报价',
  compare: '比价', contract: '合同', supplier: '厂家', query: '台账',
  product_bom: 'BOM', collection: '催款', purchase: '垫付', travel: '差旅',
  memo: '备忘', settings: '设置',
};

// SVG 图标
const ICONS = {
  dashboard: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>`,
  packaging: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>`,
  plan: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>`,
  quotation: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>`,
  compare: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>`,
  contract: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg>`,
  supplier: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
  query: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>`,
  product_bom: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>`,
  collection: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>`,
  purchase: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>`,
  travel: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>`,
  memo: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="8" y1="13" x2="16" y2="13"/></svg>`,
  settings: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`,
};

// ═══════════════════════════════════════════════════════
// DOM 引用缓存
// ═══════════════════════════════════════════════════════
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

// ═══════════════════════════════════════════════════════
// 工具函数
// ═══════════════════════════════════════════════════════
const Utils = {
  formatMoney(val) {
    if (val == null || isNaN(val)) return '¥0.00';
    return '¥' + Number(val).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  },
  formatDate(dateStr) {
    if (!dateStr) return '';
    return dateStr.slice(0, 10);
  },
  debounce(fn, delay = 300) {
    let timer;
    return function (...args) {
      clearTimeout(timer);
      timer = setTimeout(() => fn.apply(this, args), delay);
    };
  },
  escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  },
  showToast(msg, type = 'success') {
    const container = $('#toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = msg;
    container.appendChild(toast);
    setTimeout(() => { toast.remove(); }, 3000);
  },
  showConfirm(title, message) {
    return new Promise((resolve) => {
      const overlay = $('#modal-overlay');
      $('#modal-title').textContent = title;
      $('#modal-body').innerHTML = `<p style="padding:20px;text-align:center">${message}</p>`;
      $('#modal-footer').innerHTML = `
        <button class="btn btn-secondary" id="modal-cancel">取消</button>
        <button class="btn btn-primary" id="modal-confirm">确认</button>
      `;
      overlay.classList.remove('hidden');
      $('#modal-cancel').onclick = () => { overlay.classList.add('hidden'); resolve(false); };
      $('#modal-confirm').onclick = () => { overlay.classList.add('hidden'); resolve(true); };
    });
  },
  /**
   * 派发数据变更事件 - 用于通知看板等监听页面刷新
   * @param {string} source - 来源页面 key，如 'collection'、'purchase'、'travel'、'memo'
   */
  notifyDataChanged(source) {
    try {
      const ev = new CustomEvent('dataChanged', { detail: { source: source, time: Date.now() } });
      window.dispatchEvent(ev);
    } catch (e) {
      // 某些环境不支持 CustomEvent，直接重试
      try {
        const ev = document.createEvent('Event');
        ev.initEvent('dataChanged', true, true);
        ev.detail = { source: source, time: Date.now() };
        window.dispatchEvent(ev);
      } catch (err) { /* 静默失败 */ }
    }
  },
};

// ═══════════════════════════════════════════════════════
// 弹窗管理
// ═══════════════════════════════════════════════════════
const Modal = {
  show(title, bodyHtml, footerHtml = '') {
    $('#modal-title').textContent = title;
    $('#modal-body').innerHTML = bodyHtml;
    $('#modal-footer').innerHTML = footerHtml;
    $('#modal-overlay').classList.remove('hidden');
  },
  hide() {
    $('#modal-overlay').classList.add('hidden');
  },
  setFooter(html) {
    $('#modal-footer').innerHTML = html;
  },
};

$('#modal-close').addEventListener('click', () => Modal.hide());
$('#modal-overlay').addEventListener('click', (e) => {
  if (e.target === $('#modal-overlay')) Modal.hide();
});

// ═══════════════════════════════════════════════════════
// 右键菜单
// ═══════════════════════════════════════════════════════
let contextMenuCallback = null;

function showContextMenu(x, y, items) {
  const menu = $('#context-menu');
  menu.innerHTML = '';
  items.forEach((item, i) => {
    if (item === '-') {
      menu.appendChild(document.createElement('div')).className = 'context-menu-separator';
      return;
    }
    const div = document.createElement('div');
    div.className = `context-menu-item${item.danger ? ' danger' : ''}`;
    div.textContent = item.label;
    div.onclick = () => { menu.classList.add('hidden'); item.action(); };
    menu.appendChild(div);
  });
  menu.style.left = x + 'px';
  menu.style.top = y + 'px';
  menu.classList.remove('hidden');
}

document.addEventListener('click', () => {
  $('#context-menu').classList.add('hidden');
});

// ═══════════════════════════════════════════════════════
// 主题管理
// ═══════════════════════════════════════════════════════
function applyTheme(theme, mode) {
  document.body.className = '';
  const cls = theme === 'win11' ? `theme-win11-${mode}` : `theme-${mode}`;
  document.body.classList.add(cls);
  AppState.theme = theme;
  AppState.mode = mode;
}

// ═══════════════════════════════════════════════════════
// 窗口控制
// ═══════════════════════════════════════════════════════
$('#btn-minimize').addEventListener('click', () => window.electronAPI.window.minimize());
$('#btn-maximize').addEventListener('click', async () => {
  await window.electronAPI.window.maximize();
  AppState.isMaximized = !AppState.isMaximized;
  $('#btn-maximize').textContent = AppState.isMaximized ? '❐' : '□';
});
$('#btn-close').addEventListener('click', () => window.electronAPI.window.close());

// ═══════════════════════════════════════════════════════
// 侧边栏
// ═══════════════════════════════════════════════════════
function buildSidebar() {
  const navArea = $('#nav-area');
  navArea.innerHTML = '';

  NAV_ITEMS.forEach(item => {
    const div = document.createElement('div');
    div.className = 'nav-item';
    div.dataset.page = item.key;
    div.innerHTML = ICONS[item.icon] + `<span>${item.label}</span>`;
    div.addEventListener('click', () => switchPage(item.key));
    navArea.appendChild(div);
  });

  // 设置按钮（底部静态按钮）
  const settingsBtn = $('#nav-bottom .nav-item[data-page="settings"]');
  if (settingsBtn) {
    settingsBtn.addEventListener('click', () => switchPage('settings'));
  }
}

$('#btn-collapse').addEventListener('click', () => {
  AppState.sidebarCollapsed = !AppState.sidebarCollapsed;
  const sidebar = $('#sidebar');
  const divider = $('#divider');
  if (AppState.sidebarCollapsed) {
    sidebar.classList.add('collapsed');
    divider.classList.add('hidden');
    $('#btn-collapse').innerHTML = `<svg width="16" height="16" viewBox="0 0 16 16"><rect x="2" y="2" width="12" height="12" rx="2" fill="none" stroke="currentColor" stroke-width="1.5"/><line x1="10" y1="4" x2="10" y2="12" stroke="currentColor" stroke-width="1.5"/></svg>`;
  } else {
    sidebar.classList.remove('collapsed');
    divider.classList.remove('hidden');
    $('#btn-collapse').innerHTML = `<svg width="16" height="16" viewBox="0 0 16 16"><rect x="2" y="2" width="12" height="12" rx="2" fill="none" stroke="currentColor" stroke-width="1.5"/><line x1="6" y1="4" x2="6" y2="12" stroke="currentColor" stroke-width="1.5"/></svg>`;
  }
  // 保存状态
  window.electronAPI.db.updateSetting('sidebar_collapsed', AppState.sidebarCollapsed ? '1' : '0');
});

// ═══════════════════════════════════════════════════════
// 页面切换
// ═══════════════════════════════════════════════════════

// 已加载的页面脚本缓存
const loadedPageScripts = {};

// 页面名 -> 函数名映射
const PAGE_LOADERS = {
  dashboard:   'loadDashboardPage',
  packaging:   'loadPackagingPage',
  plan:        'loadPlanPage',
  quotation:   'loadQuotationPage',
  compare:     'loadComparePage',
  contract:    'loadContractPage',
  supplier:    'loadSupplierPage',
  query:       'loadQueryPage',
  product_bom: 'loadProductBomPage',
  collection:  'loadCollectionPage',
  purchase:    'loadPurchasePage',
  travel:      'loadTravelPage',
  memo:        'loadMemoPage',
  settings:    'loadSettingsPage',
};

function loadPageScript(pageName) {
  return new Promise((resolve) => {
    if (loadedPageScripts[pageName]) {
      resolve();
      return;
    }
    const script = document.createElement('script');
    script.src = `pages/${pageName}.js`;
    script.onload = () => {
      loadedPageScripts[pageName] = true;
      resolve();
    };
    script.onerror = (err) => {
      console.error(`Failed to load page script: ${pageName}`, err);
      resolve();
    };
    document.head.appendChild(script);
  });
}

async function switchPage(key) {
  AppState.currentPage = key;
  $('#page-title').textContent = PAGE_TITLES[key] || '采购助手';

  // 更新侧边栏选中状态
  $$('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.page === key);
  });

  // 先加载页面脚本（如果尚未加载），再渲染页面
  const container = $('#page-content');
  container.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:200px;color:var(--text-secondary)">加载中...</div>`;

  const loaderName = PAGE_LOADERS[key];
  if (!loaderName) {
    console.error(`No loader for page: ${key}`);
    return;
  }

  await loadPageScript(key);

  // 调用对应的页面加载函数
  const loaderFn = window[loaderName];
  if (typeof loaderFn === 'function') {
    try {
      loaderFn(container);
    } catch (e) {
      console.error(`Error loading page ${key}:`, e);
      container.innerHTML = `<div class="page"><div class="page-body" style="text-align:center;padding:40px;color:var(--text-secondary)">页面加载出错: ${e.message}</div></div>`;
    }
  } else {
    console.error(`Page loader ${loaderName} not found`);
    container.innerHTML = `<div class="page"><div class="page-body" style="text-align:center;padding:40px;color:var(--text-secondary)">页面脚本加载失败，请重试</div></div>`;
  }
}

// ═══════════════════════════════════════════════════════
// 版本检查
// ═══════════════════════════════════════════════════════
async function checkUpdates() {
  try {
    const result = await window.electronAPI.app.checkUpdates();
    if (result.hasUpdate) {
      $('#update-subtitle').textContent = `采购助手 V${result.latestVersion} 已发布`;
      $('#update-current-ver').textContent = `当前版本：V${result.currentVersion}`;
      $('#update-latest-ver').textContent = `最新版本：V${result.latestVersion}`;
      $('#update-notes').textContent = result.releaseNotes || '暂无更新说明';
      $('#update-dialog').classList.remove('hidden');

      $('#update-later').onclick = () => $('#update-dialog').classList.add('hidden');
      $('#update-download').onclick = () => {
        if (result.downloadUrl) {
          window.electronAPI.shell.openExternal(result.downloadUrl);
        }
        $('#update-dialog').classList.add('hidden');
      };
    }
  } catch (e) { /* 静默失败 */ }
}

// ═══════════════════════════════════════════════════════
// 初始化
// ═══════════════════════════════════════════════════════
async function init() {
  // 加载设置
  try {
    AppState.settings = await window.electronAPI.db.getSettings() || {};
  } catch (e) {
    AppState.settings = {};
  }

  // 应用主题
  const theme = AppState.settings.color_theme || 'classic_blue';
  const mode = AppState.settings.theme || 'light';
  applyTheme(theme, mode);

  // 恢复侧边栏状态
  if (AppState.settings.sidebar_collapsed === '1') {
    AppState.sidebarCollapsed = true;
    $('#sidebar').classList.add('collapsed');
    $('#divider').classList.add('hidden');
  }

  // 构建侧边栏
  buildSidebar();

  // 加载默认页面
  switchPage('dashboard');

  // 延迟检查更新
  setTimeout(checkUpdates, 3000);
}

// 启动
document.addEventListener('DOMContentLoaded', init);
