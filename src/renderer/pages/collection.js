/**
 * 催款记录页面 - 对齐 V2.3.2
 * 按钮：新增/导出/导入
 * 搜索：模糊搜索 + 日期范围 + 查询/重置
 * 表格：供应商名称/联系人/微信/催款日期/应付金额/通知内勤/通知经理/操作
 * 表单分节：📋 基本信息 / 💰 催款信息 / 📢 通知状态 / 📝 备注
 */
let collectionData = [];

async function loadCollectionPage(container) {
  container.innerHTML = `
    <div class="page">
      <div class="page-header">
    
        <div style="display:flex;gap:8px">
          <button class="btn btn-primary btn-sm" onclick="showCollectionForm()">✚ 新增</button>
          <button class="btn btn-secondary btn-sm" onclick="collectionExport()">📥 导出</button>
          <button class="btn btn-secondary btn-sm" onclick="collectionImport()">📤 导入</button>
        </div>
      </div>
      <div class="page-body">
        <div class="search-bar">
          <label>模糊搜索</label>
          <input class="input" id="col-keyword" placeholder="供应商/联系人/微信" style="width:220px">
          <label>开始日期</label>
          <input class="input" id="col-start-date" type="date" style="width:140px">
          <label>结束日期</label>
          <input class="input" id="col-end-date" type="date" style="width:140px">
          <button class="btn btn-primary btn-sm" onclick="loadCollectionData()">查询</button>
          <button class="btn btn-secondary btn-sm" onclick="document.getElementById('col-keyword').value='';document.getElementById('col-start-date').value='';document.getElementById('col-end-date').value='';loadCollectionData()">重置</button>
        </div>
        <div class="stats-bar"><span class="stats-label" id="col-stats"></span></div>
        <div class="table-container" id="col-table-container"></div>
      </div>
    </div>
  `;
  await loadCollectionData();
}

async function loadCollectionData() {
  const keyword = $('#col-keyword')?.value || '';
  const startDate = $('#col-start-date')?.value || '';
  const endDate = $('#col-end-date')?.value || '';
  const data = await window.electronAPI.db.getCollections(keyword, startDate, endDate);
  collectionData = data;
  $('#col-stats').innerHTML = `共 <strong>${data.length}</strong> 条记录`;

  $('#col-table-container').innerHTML = `
    <table class="data-table" id="col-table">
      <thead><tr>
        <th>供应商名称</th><th>联系人</th><th>微信</th><th>催款日期</th>
        <th>应付金额</th><th>通知内勤</th><th>通知经理</th><th>操作</th>
      </tr></thead>
      <tbody>
        ${data.map(c => `
          <tr data-id="${c.id}">
            <td>${Utils.escapeHtml(c.supplier_name)}</td>
            <td>${Utils.escapeHtml(c.contact_person||'')}</td>
            <td>${Utils.escapeHtml(c.wechat||'')}</td>
            <td>${Utils.escapeHtml(c.reminder_date||'')}</td>
            <td>${Utils.formatMoney(c.amount_due)}</td>
            <td>${c.notify_internal ? '是' : '否'}</td>
            <td>${c.notify_manager ? '是' : '否'}</td>
            <td class="cell-action">
              <span onclick="showCollectionForm(${c.id})">编辑</span>
              <span onclick="copyCollection(${c.id})">复制</span>
              <span class="danger" onclick="deleteCollection(${c.id})">删除</span>
            </td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;

  // 右键菜单
  const table = $('#col-table');
  table?.addEventListener('contextmenu', (e) => {
    e.preventDefault();
    const row = e.target.closest('tr[data-id]');
    if (!row) return;
    const id = parseInt(row.dataset.id);
    showContextMenu(e.clientX, e.clientY, [
      { label: '编辑', action: () => showCollectionForm(id) },
      { label: '复制', action: () => copyCollection(id) },
      '-',
      { label: '删除', action: () => deleteCollection(id), danger: true },
    ]);
  });
}

function showCollectionForm(id = null) {
  Modal.show(id ? '编辑催款' : '新增催款', `
    <h4 style="margin-bottom:8px">📋 基本信息</h4>
    <div class="supplier-form-grid">
      <div class="form-group"><label>供应商名称</label><input class="input" id="cf-supplier" style="width:100%"></div>
      <div class="form-group"><label>联系人</label><input class="input" id="cf-contact" style="width:100%"></div>
      <div class="form-group"><label>微信</label><input class="input" id="cf-wechat" style="width:100%"></div>
    </div>
    <h4 style="margin:12px 0 8px">💰 催款信息</h4>
    <div class="supplier-form-grid">
      <div class="form-group"><label>催款日期</label><input class="input" id="cf-date" type="date" style="width:100%"></div>
      <div class="form-group"><label>应付金额</label><input class="input" id="cf-amount" type="number" step="0.01" style="width:100%"></div>
    </div>
    <h4 style="margin:12px 0 8px">📢 通知状态</h4>
    <div style="display:flex;gap:24px;margin-bottom:8px">
      <label style="display:flex;align-items:center;gap:6px;cursor:pointer"><input type="checkbox" id="cf-notify-internal"><span>通知内勤</span></label>
      <label style="display:flex;align-items:center;gap:6px;cursor:pointer"><input type="checkbox" id="cf-notify-manager"><span>通知经理</span></label>
    </div>
    <h4 style="margin:12px 0 8px">📝 备注</h4>
    <div class="form-group"><label>备注</label><textarea class="textarea" id="cf-remark" rows="2" style="width:100%"></textarea></div>
  `, `
    <button class="btn btn-secondary" onclick="Modal.hide()">取消</button>
    <button class="btn btn-primary" onclick="saveCollection(${id||'null'})">保存</button>
  `);

  if (id) {
    (async () => {
      const c = await window.electronAPI.db.getCollection(id);
      if (c) {
        $('#cf-supplier').value = c.supplier_name || '';
        $('#cf-contact').value = c.contact_person || '';
        $('#cf-wechat').value = c.wechat || '';
        $('#cf-date').value = c.reminder_date || '';
        $('#cf-amount').value = c.amount_due || '';
        $('#cf-notify-internal').checked = c.notify_internal == 1;
        $('#cf-notify-manager').checked = c.notify_manager == 1;
        $('#cf-remark').value = c.remark || '';
      }
    })();
  }
}

async function saveCollection(id) {
  const data = {
    supplier_name: $('#cf-supplier').value,
    contact_person: $('#cf-contact').value,
    wechat: $('#cf-wechat').value,
    reminder_date: $('#cf-date').value,
    amount_due: parseFloat($('#cf-amount').value) || 0,
    notify_internal: $('#cf-notify-internal').checked ? 1 : 0,
    notify_manager: $('#cf-notify-manager').checked ? 1 : 0,
    remark: $('#cf-remark').value,
  };
  if (id) {
    await window.electronAPI.db.updateCollection(id, data);
  } else {
    await window.electronAPI.db.saveCollection(data);
  }
  Modal.hide();
  Utils.showToast('保存成功');
  loadCollectionData();
  Utils.notifyDataChanged('collection');
}

async function deleteCollection(id) {
  const ok = await Utils.showConfirm('确认删除', '确定要删除该催款记录吗？');
  if (ok) {
    await window.electronAPI.db.deleteCollection(id);
    Utils.showToast('删除成功');
    loadCollectionData();
    Utils.notifyDataChanged('collection');
  }
}

async function copyCollection(id) {
  const c = await window.electronAPI.db.getCollection(id);
  if (c) {
    const text = `${c.supplier_name} | ${c.contact_person} | ${c.wechat} | ${c.reminder_date} | ${Utils.formatMoney(c.amount_due)}`;
    await navigator.clipboard.writeText(text);
    Utils.showToast('已复制到剪贴板');
  }
}

async function collectionExport() {
  const today = new Date().toISOString().slice(0, 10);
  const result = await window.electronAPI.dialog.saveFile({
    filters: [{ name: 'Excel文件', extensions: ['xlsx'] }],
    defaultPath: `催款记录_${today}.xlsx`,
  });
  if (!result.canceled && result.filePath) {
    const flat = collectionData.map(c => ({
      supplier_name: c.supplier_name, contact_person: c.contact_person,
      wechat: c.wechat, reminder_date: c.reminder_date,
      amount_due: c.amount_due,
      notify_internal: c.notify_internal ? '是' : '否',
      notify_manager: c.notify_manager ? '是' : '否',
      remark: c.remark,
    }));
    const columnMap = {
      supplier_name: '供应商名称', contact_person: '联系人',
      wechat: '微信', reminder_date: '催款日期',
      amount_due: '应付金额', notify_internal: '通知内勤',
      notify_manager: '通知经理', remark: '备注',
    };
    await window.electronAPI.db.exportToXLSX('催款记录', flat, result.filePath, columnMap);
    Utils.showToast('导出成功');
  }
}

async function collectionImport() {
  const result = await window.electronAPI.dialog.openFile({ filters: [{ name: 'Excel文件', extensions: ['xlsx', 'xls'] }] });
  if (!result.canceled) {
    const parseResult = await window.electronAPI.parse.xlsxRead(result.filePaths[0]);
    if (parseResult.success) {
      const sheet = Object.values(parseResult.data)[0];
      if (sheet && sheet.length > 1) {
        const headers = sheet[0];
        const mapField = (row, names) => { for (const n of names) { const idx = headers.findIndex(h => h && h.includes(n)); if (idx >= 0) return row[idx]; } return ''; };
        for (let i = 1; i < sheet.length; i++) {
          const row = sheet[i];
          if (!row[0] && !row[1]) continue;
          let amount_due = parseFloat(mapField(row, ['应付金额', '金额']));
          if (isNaN(amount_due)) amount_due = 0;
          await window.electronAPI.db.saveCollection({
            supplier_name: mapField(row, ['供应商', '供应商名称']),
            contact_person: mapField(row, ['联系人']),
            wechat: mapField(row, ['微信']),
            reminder_date: mapField(row, ['催款日期', '催款时间', '日期', '时间']),
            amount_due,
            notify_internal: mapField(row, ['通知内勤']) === '是' ? 1 : 0,
            notify_manager: mapField(row, ['通知经理']) === '是' ? 1 : 0,
            remark: mapField(row, ['备注']),
          });
        }
        Utils.showToast('导入成功');
        loadCollectionData();
        Utils.notifyDataChanged('collection');
      }
    }
  }
}
