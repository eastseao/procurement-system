/**
 * 设置页面
 */
async function loadSettingsPage(container) {
  const settings = await window.electronAPI.db.getSettings();
  const version = await window.electronAPI.app.getVersion();
  const dataPath = await window.electronAPI.app.getDataPath();

  container.innerHTML = `
    <div class="page" style="overflow-y:auto">
      <div class="settings-section">
        <h3>外观设置</h3>
        <div class="settings-row">
          <div>
            <label>颜色主题</label>
            <div class="setting-desc">选择经典蓝或Win11风格</div>
          </div>
          <select class="select" id="set-color-theme">
            <option value="classic_blue">经典蓝</option>
            <option value="win11">Win11 原生</option>
          </select>
        </div>
        <div class="settings-row">
          <div>
            <label>明暗模式</label>
            <div class="setting-desc">选择浅色或深色模式</div>
          </div>
          <select class="select" id="set-theme">
            <option value="light">浅色模式</option>
            <option value="dark">深色模式</option>
          </select>
        </div>
      </div>

      <div class="settings-section">
        <h3>数据存储</h3>
        <div class="settings-row">
          <div>
            <label>数据存储位置</label>
            <div class="setting-desc" id="set-data-path-desc">${dataPath}</div>
          </div>
          <button class="btn btn-secondary btn-sm" onclick="_changeDataPath()">更改</button>
        </div>
        <div class="settings-row">
          <div>
            <label>从旧版导入数据</label>
            <div class="setting-desc">从 V2.x 版本的 procurement.db 导入已有数据</div>
          </div>
          <button class="btn btn-primary btn-sm" onclick="_importFromOldDB()">导入数据</button>
        </div>
      </div>

      <div class="settings-section">
        <h3>数据管理</h3>
        <div class="settings-row">
          <div>
            <label>导出所有数据</label>
            <div class="setting-desc">将所有表格数据导出为Excel文件</div>
          </div>
          <button class="btn btn-secondary btn-sm" onclick="exportAllData()">导出全部</button>
        </div>
      </div>

      <div class="settings-section">
        <h3>启动设置</h3>
        <div class="settings-row">
          <div>
            <label>系统托盘</label>
            <div class="setting-desc">关闭窗口时最小化到系统托盘</div>
          </div>
          <div class="checkbox-row">
            <input type="checkbox" id="set-tray">
          </div>
        </div>
        <div class="settings-row">
          <div>
            <label>开机自动启动</label>
            <div class="setting-desc">登录系统后自动启动采购助手</div>
          </div>
          <div class="checkbox-row">
            <input type="checkbox" id="set-autolaunch">
          </div>
        </div>
      </div>

      <div class="settings-section">
        <h3>系统信息</h3>
        <div class="settings-row">
          <label>版本号</label>
          <span>V${version}</span>
        </div>
        <div class="settings-row">
          <label>技术栈</label>
          <span>Electron + 原生 DOM</span>
        </div>
        <div class="settings-row">
          <label>数据库</label>
          <span>SQLite (sql.js)</span>
        </div>
      </div>

      <div class="settings-section">
        <h3>版本更新</h3>
        <div class="settings-row">
          <div>
            <label>检查更新</label>
            <div class="setting-desc">前往GitHub Releases查看新版本</div>
          </div>
          <button class="btn btn-primary btn-sm" onclick="checkUpdates()">检查更新</button>
        </div>
      </div>

      <div class="settings-section">
        <h3>关于作者</h3>
        <div class="author-card" id="author-card">
          <img class="author-avatar" id="author-avatar-img" alt="作者头像">
          <div class="author-info">
            <p class="author-name">EastSeaO</p>
            <p class="author-unit">北京同仁堂健康药业（青海）有限公司</p>
            <p class="author-business">采购部 · 包装采购业务</p>
            <button class="btn btn-primary btn-sm" style="margin-top:12px" onclick="_showAuthorDetail()">了解作者</button>
          </div>
        </div>
      </div>

      <!-- 作者详情弹窗 -->
      <div class="author-modal-overlay" id="author-modal-overlay" style="display:none">
        <div class="author-modal">
          <div class="author-modal-header">
            <span style="font-size:15px;font-weight:600">关于作者</span>
            <button class="author-modal-close" onclick="_closeAuthorDetail()">✕</button>
          </div>
          <div class="author-modal-body" id="author-modal-body"></div>
        </div>
      </div>

    </div>
  `;

  // ── 加载作者头像 ──
  try {
    const avatarPath = await window.electronAPI.file.getAssetPath('author-avatar.png');
    const imgEl = document.getElementById('author-avatar-img');
    if (imgEl) imgEl.src = avatarPath;
  } catch (e) {
    console.warn('加载作者头像失败:', e);
  }

  // ── 预加载 author2.0.md ──
  let authorMdContent = '';
  try {
    const mdPath = await window.electronAPI.file.getAssetPath('author2.0.md');
    authorMdContent = await window.electronAPI.file.read(mdPath);
  } catch (e) {
    authorMdContent = '作者信息加载失败';
  }

  // ── 将 md 内容挂到全局，供按钮调用 ──
  window.__authorMdContent = authorMdContent;

  // 设置当前值
  const colorTheme = settings.color_theme || 'classic_blue';
  const theme = settings.theme || 'light';
  const tray = settings.tray_enabled !== '0';

  const ctSel = $('#set-color-theme');
  if (ctSel) ctSel.value = colorTheme;
  const tSel = $('#set-theme');
  if (tSel) tSel.value = theme;
  const trayCb = $('#set-tray');
  if (trayCb) trayCb.checked = tray;

  // 开机启动状态
  const autoLaunchCb = $('#set-autolaunch');
  if (autoLaunchCb) {
    try {
      const autoLaunchInfo = await window.electronAPI.app.getAutoLaunch();
      autoLaunchCb.checked = !!autoLaunchInfo.openAtLogin;
    } catch (e) {
      autoLaunchCb.checked = false;
    }
  }

  // 监听变更
  ctSel?.addEventListener('change', () => {
    const val = ctSel.value;
    window.electronAPI.db.updateSetting('color_theme', val);
    applyTheme(val, AppState.mode);
    Utils.showToast('颜色主题已更新');
  });

  tSel?.addEventListener('change', () => {
    const val = tSel.value;
    window.electronAPI.db.updateSetting('theme', val);
    applyTheme(AppState.theme, val);
    Utils.showToast('明暗模式已切换');
  });

  trayCb?.addEventListener('change', () => {
    window.electronAPI.db.updateSetting('tray_enabled', trayCb.checked ? '1' : '0');
    Utils.showToast('设置已保存');
  });

  autoLaunchCb?.addEventListener('change', async () => {
    const result = await window.electronAPI.app.setAutoLaunch(autoLaunchCb.checked);
    if (result && result.success) {
      Utils.showToast('已' + (autoLaunchCb.checked ? '开启' : '关闭') + '开机启动');
    } else {
      Utils.showToast('设置失败: ' + (result.error || '未知错误'), 'error');
    }
  });
}

// ── 更改数据存储位置 ──
async function _changeDataPath() {
  const result = await window.electronAPI.dialog.openFile({
    title: '选择数据存储目录（请选择文件夹）',
    properties: ['openDirectory'],
  });
  if (result.canceled || !result.filePaths || result.filePaths.length === 0) return;
  const newPath = result.filePaths[0];
  const setResult = await window.electronAPI.app.setDataPath(newPath);
  if (setResult.success) {
    Utils.showToast('数据存储位置已更改，请重启应用生效');
    const descEl = $('#set-data-path-desc');
    if (descEl) descEl.textContent = setResult.path;
  } else {
    Utils.showToast('更改失败: ' + (setResult.error || '未知错误'), 'error');
  }
}

// ── 从旧版导入数据 ──
async function _importFromOldDB() {
  const result = await window.electronAPI.dialog.openFile({
    title: '选择旧版数据库文件',
    filters: [{ name: '数据库文件', extensions: ['db'] }],
    properties: ['openFile'],
  });
  if (result.canceled || !result.filePaths || result.filePaths.length === 0) return;

  const oldPath = result.filePaths[0];
  Utils.showToast('正在导入数据，请稍候...');

  try {
    const importResult = await window.electronAPI.db.importFromOld(oldPath);
    if (importResult.success) {
      const s = importResult.stats;
      const msg = [
        `供应商: ${s.suppliers || 0} 条`,
        `合同供应商: ${s.contractSuppliers || 0} 条`,
        `备忘录: ${s.memos || 0} 条`,
        `催款记录: ${s.collections || 0} 条`,
        `采购计划: ${s.plans || 0} 条`,
        `包材下单: ${s.packaging || 0} 条`,
        `采购垫付: ${s.purchase || 0} 条`,
        `差旅: ${s.travel || 0} 条`,
        `成品BOM: ${s.bom || 0} 条`,
        `三方比价: ${s.thirdParty || 0} 条`,
      ].join('\n');
      Utils.showToast('数据导入成功！\n' + msg);
    } else {
      Utils.showToast('导入失败: ' + (importResult.error || '未知错误'), 'error');
    }
  } catch (e) {
    Utils.showToast('导入失败: ' + e.message, 'error');
  }
}

// ── 作者详情弹窗 ──
function _showAuthorDetail() {
  const overlay = document.getElementById('author-modal-overlay');
  const body = document.getElementById('author-modal-body');
  if (!overlay || !body) return;

  // 将 Markdown 简单转换为 HTML
  const md = window.__authorMdContent || '';
  const html = _simpleMdToHtml(md);
  body.innerHTML = html;
  overlay.style.display = 'flex';
}

function _closeAuthorDetail() {
  const overlay = document.getElementById('author-modal-overlay');
  if (overlay) overlay.style.display = 'none';
}

function _simpleMdToHtml(md) {
  let html = md
    .replace(/^>\s+(.+)$/gm, '<blockquote>$1</blockquote>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>');
  html = '<p>' + html + '</p>';
  return html;
}

async function exportAllData() {
  const result = await window.electronAPI.dialog.saveFile({
    defaultPath: `采购管理系统数据_${new Date().toISOString().slice(0,10)}.xlsx`,
    filters: [{ name: 'Excel文件', extensions: ['xlsx'] }],
  });
  if (!result.canceled && result.filePath) {
    try {
      const sheets = {};
      sheets['供应商'] = await window.electronAPI.db.getSuppliers('', '', '');
      sheets['催款记录'] = await window.electronAPI.db.getCollections('');
      sheets['备忘录'] = await window.electronAPI.db.getMemos('', '', '');
      sheets['物料台账'] = await window.electronAPI.db.getMaterialLedger({});
      sheets['包材下单'] = await window.electronAPI.db.getPackagingOrders({});
      sheets['成品BOM'] = await window.electronAPI.db.getProductBOM({});
      sheets['采购计划'] = await window.electronAPI.db.getPlanRecords(0);

      const XLSX = require('xlsx');
      const workbook = XLSX.utils.book_new();
      Object.entries(sheets).forEach(([name, data]) => {
        if (data.length > 0) {
          const ws = XLSX.utils.json_to_sheet(data);
          XLSX.utils.book_append_sheet(workbook, ws, name);
        }
      });
      XLSX.writeFile(workbook, result.filePath);
      Utils.showToast('导出成功');
    } catch (e) {
      // 回退到逐个导出
      const data = [];
      const collections = await window.electronAPI.db.getCollections('');
      data.push(...collections.map(c => ({ ...c, _table: '催款记录' })));
      const memos = await window.electronAPI.db.getMemos('', '', '');
      data.push(...memos.map(m => ({ ...m, _table: '备忘录' })));
      await window.electronAPI.db.exportToXLSX('all_data', data, result.filePath);
      Utils.showToast('导出成功');
    }
  }
}
