/**
 * 包材下单页面 — 对齐 Python V2.3.2 完整工作流
 * 5环节折叠面板：物料比价 → 合同跟踪 → 通知厂家 → 生产进度 → 发货跟进
 * 状态计算：待比价 → 已比价 → 合同处理中 → 已签合同 → 已发货 → 已归档
 */
let packagingArchived = false;

async function loadPackagingPage(container) {
  packagingArchived = false;
  container.innerHTML = `
    <div class="page">
      <div class="page-header" style="display:flex;justify-content:flex-start;align-items:center;gap:12px">
        <!-- ⭐ 拖拽上传合同区域（放最前，紧凑高度，靠左排列） -->
        <div id="pkg-drop-zone" style="padding:6px 14px;border:2px dashed #2563EB;border-radius:8px;text-align:center;background:#F0F7FF;color:#1E3A8A;font-size:12px;cursor:pointer;flex-shrink:0;display:flex;align-items:center;gap:8px">
          <span style="font-size:18px">📄</span>
          <span style="font-weight:600;color:#1E40AF">拖拽合同到此处上传</span>
          <span style="color:#2563EB;text-decoration:underline" onclick="document.getElementById('pkg-contract-upload').click();event.stopPropagation()">（或点击选择）</span>
          <span id="pkg-upload-status" style="color:#059669;font-weight:600;margin-left:8px"></span>
        </div>
        <input type="file" id="pkg-contract-upload" style="display:none" accept=".docx">
        <button class="btn btn-primary btn-sm" onclick="packagingUploadContract()">📄 上传合同</button>
        <button class="btn btn-secondary btn-sm" onclick="showPackagingForm()">✚ 新增下单</button>
      </div>
      <div class="page-body">
        <div class="search-bar">
          <label>项目</label>
          <select class="select" id="pkg-project-filter"><option value="">全部</option></select>
          <label>厂家</label>
          <input class="input" id="pkg-factory-filter" placeholder="下单厂家" style="width:140px">
          <label>项目号</label>
          <input class="input" id="pkg-projectno-filter" placeholder="8位项目号" style="width:120px" maxlength="8">
          <button class="btn btn-primary btn-sm" onclick="loadPackagingData()">查询</button>
          <button class="btn btn-secondary btn-sm" onclick="clearPackagingFilters()">清除筛选</button>
        </div>
        <div class="stats-bar">
          <span class="stats-label" id="packaging-stats"></span>
          <div style="display:flex;gap:8px;margin-left:auto">
            <button class="btn btn-secondary btn-sm" onclick="togglePackagingArchive()">📁 归档</button>
            <button class="btn btn-secondary btn-sm" onclick="packagingExport()">📥 导出</button>
          </div>
        </div>
        <div class="table-container" id="packaging-table-container"></div>
      </div>
    </div>
  `;

  // 【重要】先绑定拖拽事件
  bindPackagingDropEvents();

  const projects = await window.electronAPI.db.getProjects();
  const sel = $('#pkg-project-filter');
  if (sel) sel.innerHTML = '<option value="">全部</option>' + projects.map(p => `<option>${Utils.escapeHtml(p)}</option>`).join('');
  await loadPackagingData();
}

// 绑定拖拽上传事件
function bindPackagingDropEvents() {
  const dropZone = document.getElementById('pkg-drop-zone');
  const fileInput = document.getElementById('pkg-contract-upload');
  if (!dropZone || !fileInput) return;

  // 拖拽悬停时高亮
  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.style.background = '#DBEAFE';
    dropZone.style.borderColor = '#1D4ED8';
  });
  dropZone.addEventListener('dragleave', () => {
    dropZone.style.background = '#F0F7FF';
    dropZone.style.borderColor = '#2563EB';
  });
  // 拖拽落下
  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.style.background = '#F0F7FF';
    dropZone.style.borderColor = '#2563EB';
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      handlePackagingContractFiles(files);
    }
  });
  // 点击区域也能选择文件
  dropZone.addEventListener('click', () => {
    fileInput.click();
  });
  fileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handlePackagingContractFiles(e.target.files);
    }
  });
}

// 处理拖拽或选择上传的合同文件（调用合同解析逻辑）
async function handlePackagingContractFiles(fileList) {
  if (!fileList || fileList.length === 0) return;
  const statusEl = document.getElementById('pkg-upload-status');
  let uploaded = 0;
  let failed = 0;

  for (let i = 0; i < fileList.length; i++) {
    const f = fileList[i];
    try {
      // 先保存到临时位置，然后调用 parseContract 解析
      const reader = new FileReader();
      await new Promise((resolve, reject) => {
        reader.onload = async (e) => {
          try {
            const bytes = new Uint8Array(e.target.result);
            const fileName = `temp_pkg_${Date.now()}_${f.name}`;
            const result = await window.electronAPI.file.saveUploadedFile({
              fileName,
              data: Array.from(bytes),
            });
            if (result && result.success && result.path) {
              // 调用合同解析
              const parseResult = await window.electronAPI.file.parseContract(result.path);
              if (parseResult && parseResult.success) {
                const d = parseResult.data || {};

                // 清理金额
                const cleanAmount = (v) => {
                  if (!v) return 0;
                  const num = parseFloat(String(v).replace(/[^\d\.]/g, ''));
                  return isNaN(num) ? 0 : num;
                };

                const baseMaterial = d.product_name || d.material_name || '';
                const fullMaterialName = (baseMaterial + (d.spec ? ' ' + d.spec : '')).trim();

                let qty = d.quantity || '';
                if (typeof qty === 'string') {
                  const m2 = qty.match(/[\d\.]+/);
                  if (m2) qty = parseFloat(m2[0]) || '';
                }

                let expectedShipDate = '';
                if (d.delivery_date) {
                  const m3 = String(d.delivery_date).match(/(\d{4})\s*[年\-\/]\s*(\d{1,2})\s*[月\-\/]\s*(\d{1,2})/);
                  if (m3) expectedShipDate = `${m3[1]}-${m3[2].padStart(2,'0')}-${m3[3].padStart(2,'0')}`;
                }

                const record = {
                  material_name: fullMaterialName || (d.supplier ? `${d.supplier} 合同` : '合同导入记录'),
                  project_no: d.project_no || '',
                  order_quantity: String(qty || ''),
                  order_factory: d.supplier || '',
                  project: d.party_a || '',
                  compare_price: cleanAmount(d.unit_price),
                  contract_status: '待签批',
                  contract_remark: `合同编号:${d.contract_no || ''} | 金额:${d.total_amount || ''} | 付款:${d.payment_terms || ''}`,
                  compare_date: d.contract_date || '',
                  expected_ship_date: expectedShipDate,
                };

                await window.electronAPI.db.savePackagingOrder(record);
                uploaded++;
                resolve();
              } else {
                reject(new Error(parseResult?.error || '解析失败'));
              }
            } else {
              reject(new Error('保存失败'));
            }
          } catch (err) { reject(err); }
        };
        reader.onerror = () => reject(new Error('read error'));
        reader.readAsArrayBuffer(f);
      });
    } catch (e) {
      failed++;
    }
  }

  if (statusEl) {
    statusEl.textContent = `✅ 成功解析 ${uploaded} 个文件${failed ? `，${failed} 个失败` : ''}`;
    setTimeout(() => { statusEl.textContent = ''; }, 4000);
  }

  const fileInputEl = document.getElementById('pkg-contract-upload');
  if (fileInputEl) fileInputEl.value = '';

  loadPackagingData();
}

function computeStatus(o) {
  if (o.archived === 1) return { text: '已归档', cls: 'status-archived' };
  if (o.ship_date) return { text: '已发货', cls: 'status-shipped' };
  if (o.contract_status === '已签订') return { text: '已签合同', cls: 'status-contracted' };
  if (o.contract_status === '待签批' || o.contract_status === '已邮寄') return { text: '合同处理中', cls: 'status-contracting' };
  if (o.compare_price) return { text: '已比价', cls: 'status-compared' };
  return { text: '待比价', cls: 'status-pending' };
}

const STATUS_STYLES = {
  'status-archived': 'color:#9CA3AF',
  'status-shipped': 'color:#2563EB',
  'status-contracted': 'color:#16A34A',
  'status-contracting': 'color:#F59E0B',
  'status-compared': 'color:#6B7280',
  'status-pending': 'color:#EF4444',
};

async function loadPackagingData() {
  const data = await window.electronAPI.db.getPackagingOrders({ archived: packagingArchived ? 1 : 0, keyword: '' });
  const projectFilter = $('#pkg-project-filter')?.value || '';
  const factoryFilter = ($('#pkg-factory-filter')?.value || '').toLowerCase();
  const projectNoFilter = ($('#pkg-projectno-filter')?.value || '').trim();

  let filtered = data.filter(o => packagingArchived ? o.archived === 1 : o.archived !== 1);
  if (projectFilter) filtered = filtered.filter(o => o.project === projectFilter || (o.project||'').includes(projectFilter));
  if (factoryFilter) filtered = filtered.filter(o => (o.order_factory||'').toLowerCase().includes(factoryFilter));
  if (projectNoFilter) filtered = filtered.filter(o => (o.project_no||'').includes(projectNoFilter));

  const totalActive = data.filter(o => o.archived !== 1).length;
  const totalArchived = data.filter(o => o.archived === 1).length;
  $('#packaging-stats').innerHTML = `共 <strong>${filtered.length}</strong> 条记录 | 当前显示：${packagingArchived ? '已归档' : '进行中'}（${packagingArchived ? totalArchived : totalActive}）`;

  $('#packaging-table-container').innerHTML = `
    <style>
      #pkg-table tbody tr:hover { background: var(--hover-row, #F0F5FF); }
      #pkg-table tbody tr:nth-child(even) { background: var(--even-row, #FAFBFC); }
      #pkg-table tbody tr:nth-child(even):hover { background: var(--hover-row, #F0F5FF); }
    </style>
    <table class="data-table" id="pkg-table">
      <thead><tr>
        <th>物料名称</th><th>项目号</th><th>下单数量</th><th>下单厂家</th>
        <th>所属项目</th><th>比价单价</th><th>合同状态</th><th>通知日期</th>
        <th>预计发货</th><th>发货日期</th><th>预计到货</th><th>状态</th><th>操作</th>
      </tr></thead>
      <tbody>
        ${filtered.map((o, i) => {
          const st = computeStatus(o);
          const style = STATUS_STYLES[st.cls] || '';
          const archivedStyle = o.archived === 1 ? 'color:#9CA3AF;opacity:0.7' : '';
          return `
          <tr class="${o.archived===1?'archived':''} ${i%2===0?'':'odd'}" data-id="${o.id}" style="${archivedStyle}">
            <td>${Utils.escapeHtml(o.material_name)}</td>
            <td style="text-align:center">${Utils.escapeHtml(o.project_no||'')}</td>
            <td style="text-align:center">${Utils.escapeHtml(o.order_quantity||'')}</td>
            <td style="text-align:center">${Utils.escapeHtml(o.order_factory||'')}</td>
            <td style="text-align:center">${Utils.escapeHtml(o.project||'')}</td>
            <td style="text-align:center">${Utils.formatMoney(o.compare_price)}</td>
            <td style="text-align:center">${Utils.escapeHtml(o.contract_status||'—')}</td>
            <td style="text-align:center">${Utils.escapeHtml(o.notify_date||'')}</td>
            <td style="text-align:center">${Utils.escapeHtml(o.expected_ship_date||'')}</td>
            <td style="text-align:center">${Utils.escapeHtml(o.ship_date||'')}</td>
            <td style="text-align:center">${Utils.escapeHtml(o.expected_arrival||'')}</td>
            <td style="text-align:center;${style}">${st.text}</td>
            <td class="cell-action">
              <span onclick="showPackagingForm(${o.id})">编辑</span>
              <span onclick="copyPackagingOrder(${o.id})">复制</span>
              ${!packagingArchived ? `<span onclick="archivePackagingOrder(${o.id})">归档</span>` : ''}
              <span class="danger" onclick="deletePackagingOrder(${o.id})">删除</span>
            </td>
          </tr>`;
        }).join('')}
      </tbody>
    </table>
  `;

  const table = $('#pkg-table');
  table?.addEventListener('contextmenu', (e) => {
    e.preventDefault();
    const row = e.target.closest('tr[data-id]');
    if (!row) return;
    const id = parseInt(row.dataset.id);
    showContextMenu(e.clientX, e.clientY, [
      { label: '编辑', action: () => showPackagingForm(id) },
      { label: '复制', action: () => copyPackagingOrder(id) },
      packagingArchived ? null : { label: '归档', action: () => archivePackagingOrder(id) },
      '-',
      { label: '删除', action: () => deletePackagingOrder(id), danger: true },
    ].filter(Boolean));
  });
}

function clearPackagingFilters() {
  const s = $('#pkg-project-filter'); if (s) s.value = '';
  const f = $('#pkg-factory-filter'); if (f) f.value = '';
  const p = $('#pkg-projectno-filter'); if (p) p.value = '';
  loadPackagingData();
}

function togglePackagingArchive() {
  packagingArchived = !packagingArchived;
  loadPackagingData();
}

/* ── 5环节折叠面板表单 ── */
function showPackagingForm(id = null) {
  const panels = [
    { key: 'compare',   title: '① 物料比价', icon: '⚖️',  fields: `
      <div class="form-row"><label>比价单价</label><input class="input" id="pf-compare-price" type="number" step="0.01" style="width:120px">
      <label>比价日期</label><input class="input" id="pf-compare-date" type="date" style="width:150px"></div>
      <div class="form-row"><label>比价备注</label><textarea class="textarea" id="pf-compare-remark" rows="2" style="width:100%"></textarea></div>` },
    { key: 'contract',  title: '② 合同跟踪', icon: '📝',  fields: `
      <div class="form-row"><label>合同状态</label>
        <select class="select" id="pf-contract-status" style="width:150px">
          <option value="">请选择</option><option value="待签批">待签批</option><option value="已签订">已签订</option><option value="已邮寄">已邮寄</option>
        </select></div>
      <div class="form-row"><label>合同备注</label><textarea class="textarea" id="pf-contract-remark" rows="2" style="width:100%"></textarea></div>` },
    { key: 'notify',    title: '③ 通知厂家', icon: '📢',  fields: `
      <div class="form-row"><label>通知日期</label><input class="input" id="pf-notify-date" type="date" style="width:150px">
      <label>沟通货期</label><input class="input" id="pf-expected-delivery-date" type="date" style="width:150px"></div>
      <div class="form-row"><label>通知备注</label><textarea class="textarea" id="pf-notify-remark" rows="2" style="width:100%"></textarea></div>` },
    { key: 'production',title: '④ 生产进度', icon: '🏭',  fields: `
      <div class="form-row"><label>生产周期</label><input class="input" id="pf-production-cycle" placeholder="如：15天" style="width:150px">
      <label>预定发货</label><input class="input" id="pf-expected-ship-date" type="date" style="width:150px"></div>
      <div class="form-row"><label>生产备注</label><textarea class="textarea" id="pf-production-remark" rows="2" style="width:100%"></textarea></div>` },
    { key: 'ship',      title: '⑤ 发货跟进', icon: '🚚',  fields: `
      <div class="form-row"><label>发货日期</label><input class="input" id="pf-ship-date" type="date" style="width:150px">
      <label>预计到货</label><input class="input" id="pf-expected-arrival" type="date" style="width:150px"></div>
      <div class="form-row"><label>运输方式</label>
        <select class="select" id="pf-ship-method" style="width:120px">
          <option value="">请选择</option><option value="快递">快递</option><option value="物流">物流</option><option value="自提">自提</option><option value="其他">其他</option>
        </select>
      <label>物流单号</label><input class="input" id="pf-tracking-no" style="width:200px"></div>
      <div class="form-row"><label>通知库房</label>
        <select class="select" id="pf-notify-warehouse" style="width:80px">
          <option value="0">否</option><option value="1">是</option>
        </select></div>` },
  ];

  const panelsHtml = panels.map(p => `
    <div class="panel-section" id="panel-${p.key}">
      <div class="panel-header" onclick="togglePanel('${p.key}')" style="cursor:pointer;display:flex;align-items:center;gap:6px;padding:8px 0;border-bottom:1px solid var(--border-color,#E5E7EB);margin-top:8px">
        <span class="panel-toggle" id="toggle-${p.key}">▼</span>
        <span>${p.icon} ${p.title}</span>
      </div>
      <div class="panel-body" id="body-${p.key}" style="padding:8px 0">
        ${p.fields}
      </div>
    </div>
  `).join('');

  Modal.show(id ? '编辑下单' : '新增下单', `
    <div style="font-size:12px;color:#6B7280;margin-bottom:8px">基本信息</div>
    <div class="form-row">
      <label>物料名称 <span style="color:red">*</span></label><input class="input" id="pf-material-name" style="flex:1">
      <label>项目号</label><input class="input" id="pf-project-no" style="width:150px" maxlength="8">
    </div>
    <div class="form-row">
      <label>下单数量</label><input class="input" id="pf-order-quantity" style="width:100px">
      <label>下单厂家</label><input class="input" id="pf-order-factory" style="width:200px">
      <label>所属项目</label><input class="input" id="pf-project" style="width:150px">
    </div>
    ${panelsHtml}
  `, `
    <button class="btn btn-secondary" onclick="Modal.hide()">取消</button>
    ${id ? `<button class="btn btn-danger" onclick="confirmAndArchive(${id})" style="margin-right:8px">确认到货并归档</button>` : ''}
    <button class="btn btn-primary" onclick="savePackagingOrder(${id||'null'})">保存</button>
  `, { width: '600px' });

  // 加载已有数据
  if (id) {
    (async () => {
      const allData = await window.electronAPI.db.getPackagingOrders({ archived: 0, keyword: '' });
      const item = allData.find(o => o.id === id);
      if (!item) return;
      $('#pf-material-name').value = item.material_name || '';
      $('#pf-project-no').value = item.project_no || '';
      $('#pf-order-quantity').value = item.order_quantity || '';
      $('#pf-order-factory').value = item.order_factory || '';
      $('#pf-project').value = item.project || '';
      $('#pf-compare-price').value = item.compare_price || '';
      $('#pf-compare-date').value = item.compare_date || '';
      $('#pf-compare-remark').value = item.compare_remark || '';
      $('#pf-contract-status').value = item.contract_status || '';
      $('#pf-contract-remark').value = item.contract_remark || '';
      $('#pf-notify-date').value = item.notify_date || '';
      $('#pf-expected-delivery-date').value = item.expected_delivery_date || '';
      $('#pf-notify-remark').value = item.notify_remark || '';
      $('#pf-production-cycle').value = item.production_cycle || '';
      $('#pf-expected-ship-date').value = item.expected_ship_date || '';
      $('#pf-production-remark').value = item.production_remark || '';
      $('#pf-ship-date').value = item.ship_date || '';
      $('#pf-expected-arrival').value = item.expected_arrival || '';
      $('#pf-ship-method').value = item.ship_method || '';
      $('#pf-tracking-no').value = item.tracking_no || '';
      $('#pf-notify-warehouse').value = item.notify_warehouse || 0;

      // 根据合同状态决定哪些面板展开
      const st = item.contract_status;
      if (!st || !item.compare_price) collapsePanel('contract');
      if (st !== '待签批' && st !== '已签订' && st !== '已邮寄') collapsePanel('contract');
      if (!item.notify_date) collapsePanel('notify');
      if (!item.production_cycle && !item.expected_ship_date) collapsePanel('production');
      if (!item.ship_date && !item.expected_arrival) collapsePanel('ship');
    })();
  }
}

function togglePanel(key) {
  const body = $(`#body-${key}`);
  const toggle = $(`#toggle-${key}`);
  if (!body) return;
  if (body.style.display === 'none') {
    body.style.display = '';
    if (toggle) toggle.textContent = '▼';
  } else {
    body.style.display = 'none';
    if (toggle) toggle.textContent = '▶';
  }
}

function collapsePanel(key) {
  const body = $(`#body-${key}`);
  const toggle = $(`#toggle-${key}`);
  if (body) body.style.display = 'none';
  if (toggle) toggle.textContent = '▶';
}

async function savePackagingOrder(id) {
  const materialName = $('#pf-material-name')?.value?.trim();
  if (!materialName) { Utils.showToast('请输入物料名称', 'warning'); return; }

  const data = {
    material_name: materialName,
    project_no: $('#pf-project-no')?.value || '',
    order_quantity: $('#pf-order-quantity')?.value || '',
    order_factory: $('#pf-order-factory')?.value || '',
    project: $('#pf-project')?.value || '',
    compare_price: parseFloat($('#pf-compare-price')?.value) || 0,
    compare_date: $('#pf-compare-date')?.value || '',
    compare_remark: $('#pf-compare-remark')?.value || '',
    contract_status: $('#pf-contract-status')?.value || '',
    contract_remark: $('#pf-contract-remark')?.value || '',
    notify_date: $('#pf-notify-date')?.value || '',
    expected_delivery_date: $('#pf-expected-delivery-date')?.value || '',
    notify_remark: $('#pf-notify-remark')?.value || '',
    production_cycle: $('#pf-production-cycle')?.value || '',
    expected_ship_date: $('#pf-expected-ship-date')?.value || '',
    production_remark: $('#pf-production-remark')?.value || '',
    ship_date: $('#pf-ship-date')?.value || '',
    expected_arrival: $('#pf-expected-arrival')?.value || '',
    ship_method: $('#pf-ship-method')?.value || '',
    tracking_no: $('#pf-tracking-no')?.value || '',
    notify_warehouse: parseInt($('#pf-notify-warehouse')?.value) || 0,
  };

  if (id) {
    await window.electronAPI.db.updatePackagingOrder(id, data);
  } else {
    await window.electronAPI.db.savePackagingOrder(data);
  }
  Modal.hide();
  Utils.showToast(id ? '修改成功' : '新增成功');
  loadPackagingData();
}

async function confirmAndArchive(id) {
  const item = await window.electronAPI.db.getPackagingOrder(id);
  if (!item) return;
  if (!item.ship_date) {
    Utils.showToast('请先填写发货日期再确认归档', 'warning');
    return;
  }
  const ok = await Utils.showConfirm('确认到货并归档', '确认货物已到货并归档该记录？');
  if (!ok) return;
  await window.electronAPI.db.updatePackagingOrder(id, { ...item, archived: 1 });
  Modal.hide();
  Utils.showToast('已确认到货并归档');
  loadPackagingData();
}

async function copyPackagingOrder(id) {
  const item = await window.electronAPI.db.getPackagingOrder(id);
  if (!item) return;
  await window.electronAPI.db.savePackagingOrder({
    ...item, id: undefined, compare_date: new Date().toISOString().slice(0, 10),
    ship_date: '', contract_status: '', contract_remark: '', notify_remark: '',
    production_remark: '', tracking_no: '', notify_warehouse: 0,
  });
  Utils.showToast('已复制');
  loadPackagingData();
}

async function archivePackagingOrder(id) {
  const ok = await Utils.showConfirm('确认归档', '确定要归档该记录吗？');
  if (!ok) return;
  await window.electronAPI.db.archivePackagingOrder(id);
  Utils.showToast('已归档');
  loadPackagingData();
}

async function deletePackagingOrder(id) {
  const ok = await Utils.showConfirm('确认删除', '确定要删除该下单记录吗？此操作不可恢复。');
  if (!ok) return;
  await window.electronAPI.db.deletePackagingOrder(id);
  Utils.showToast('删除成功');
  loadPackagingData();
}

async function packagingUploadContract() {
  const result = await window.electronAPI.dialog.openFile({
    filters: [{ name: 'Word文档', extensions: ['docx'] }],
    properties: ['openFile'],
  });
  if (result.canceled || !result.filePaths?.length) return;
  const filePath = result.filePaths[0];
  Utils.showToast('正在解析合同...', 'warning');

  try {
    const parseResult = await window.electronAPI.file.parseContract(filePath);
    if (!parseResult.success) {
      Utils.showToast('合同解析失败：' + (parseResult.error || '未知错误'), 'error');
      return;
    }
    const d = parseResult.data || {};

    // 清理金额中的非数字字符（¥ , 元等）
    const cleanAmount = (v) => {
      if (!v) return 0;
      const num = parseFloat(String(v).replace(/[^\d\.]/g, ''));
      return isNaN(num) ? 0 : num;
    };

    // 从产品信息 / 规格组合材料名
    const baseMaterial = d.product_name || d.material_name || '';
    const fullMaterialName = (baseMaterial + (d.spec ? ' ' + d.spec : '')).trim();

    // 提取数字数量（去除单位）
    let qty = d.quantity || '';
    if (typeof qty === 'string') {
      const m = qty.match(/[\d\.]/);
      if (m) qty = parseFloat(qty.match(/[\d\.]+/)[0]) || '';
    }

    // 解析供货日期
    let expectedShipDate = '';
    if (d.delivery_date) {
      const m = String(d.delivery_date).match(/(\d{4})\s*[年\-\/]\s*(\d{1,2})\s*[月\-\/]\s*(\d{1,2})/);
      if (m) expectedShipDate = `${m[1]}-${m[2].padStart(2,'0')}-${m[3].padStart(2,'0')}`;
    }

    const record = {
      material_name: fullMaterialName,
      project_no: d.project_no || '',
      order_quantity: String(qty || ''),
      order_factory: d.supplier || '',
      project: d.party_a || '',
      compare_price: cleanAmount(d.unit_price),
      contract_status: '待签批',
      contract_remark: `合同编号:${d.contract_no || ''} | 金额:${d.total_amount || ''} | 付款:${d.payment_terms || ''}`,
      compare_date: d.contract_date || '',
      expected_ship_date: expectedShipDate,
    };

    if (!record.material_name) {
      // 若无法提取到物料名，仍创建一条带供应商信息的记录
      record.material_name = d.supplier ? `${d.supplier} 合同` : '合同导入记录';
    }

    await window.electronAPI.db.savePackagingOrder(record);
    const infoItems = [record.material_name, d.supplier ? `厂家:${d.supplier}` : '', d.total_amount ? `金额:${d.total_amount}` : ''].filter(Boolean);
    Utils.showToast(`合同解析成功：${infoItems.join(' / ')}`);
    loadPackagingData();
  } catch (e) {
    Utils.showToast('合同解析异常：' + e.message, 'error');
  }
}

async function packagingExport() {
  const result = await window.electronAPI.dialog.saveFile({
    filters: [{ name: 'Excel文件', extensions: ['xlsx'] }],
    defaultPath: `物料下单_${new Date().toISOString().slice(0,10).replace(/-/g,'')}.xlsx`,
  });
  if (!result.canceled && result.filePath) {
    const data = await window.electronAPI.db.getPackagingOrders({ archived: 0, keyword: '' });
    const rows = data.map(o => ({
      '物料名称': o.material_name, '项目号': o.project_no, '下单数量': o.order_quantity,
      '下单厂家': o.order_factory, '所属项目': o.project, '比价单价': o.compare_price,
      '合同状态': o.contract_status, '通知日期': o.notify_date,
      '预计发货': o.expected_ship_date, '发货日期': o.ship_date,
      '预计到货': o.expected_arrival, '比价日期': o.compare_date,
      '比价备注': o.compare_remark, '合同备注': o.contract_remark,
      '沟通货期': o.expected_delivery_date, '通知备注': o.notify_remark,
      '生产周期': o.production_cycle, '生产备注': o.production_remark,
      '运输方式': o.ship_method, '物流单号': o.tracking_no,
    }));
    await window.electronAPI.db.exportToXLSX('物料下单', rows, result.filePath);
    Utils.showToast('导出成功');
  }
}
