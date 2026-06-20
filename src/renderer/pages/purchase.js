/**
 * 采购垫付页面 - 对齐 V2.3.2
 * 按钮：查看归档/返回列表 + 新增垫付 + 导出Excel + 导入xlsx
 * 统计：总记录数/垫付总金额/未报销金额/未开票数
 * 筛选：报销状态下拉 + 开票状态下拉 + 项目下拉 + 刷新
 * 表格：日期/项目/经手人/支付方式/物料摘要/合计(¥)/开票/报销/操作
 * 操作列：编辑/归档/删除（正常）/ 查看/删除（归档）
 */
let purchaseArchived = false;
let purchaseFilteredData = [];

async function loadPurchasePage(container) {
  purchaseArchived = false;
  container.innerHTML = `
    <div class="page">
      <div class="page-header">
        <div style="display:flex;gap:8px">
          <button class="btn btn-secondary btn-sm" id="pur-archive-btn" onclick="togglePurchaseArchive()">📁 查看归档</button>
          <button class="btn btn-primary btn-sm" onclick="showPurchaseForm()">✚ 新增垫付</button>
          <button class="btn btn-secondary btn-sm" onclick="purchaseExport()">📥 导出Excel</button>
          <button class="btn btn-secondary btn-sm" onclick="purchaseImport()">📤 导入xlsx</button>
        </div>
      </div>
      <div class="page-body">
        <div class="stat-cards" id="pur-stats"></div>
        <div class="search-bar">
          <label>报销状态</label>
          <select class="select" id="pur-reimb-filter"><option value="">全部</option><option>未报销</option><option>已报销</option></select>
          <label>开票状态</label>
          <select class="select" id="pur-invoice-filter"><option value="">全部</option><option>未开票</option><option>已开票</option></select>
          <label>项目</label>
          <select class="select" id="pur-project-filter"><option value="">全部</option></select>
          <button class="btn btn-primary btn-sm" onclick="loadPurchaseData()">🔄 刷新</button>
        </div>
        <div class="table-container" id="pur-table-container"></div>
      </div>
    </div>
  `;

  try {
    await loadPurchaseData();
  } catch (e) { console.error(e); }
}

async function loadPurchaseData() {
  const data = await window.electronAPI.db.getPurchases(purchaseArchived ? 1 : 0);
  const reimbFilter = $('#pur-reimb-filter')?.value || '';
  const invoiceFilter = $('#pur-invoice-filter')?.value || '';
  const projectFilter = $('#pur-project-filter')?.value || '';

  let filtered = data;
  if (reimbFilter) filtered = filtered.filter(p => p.reimbursement_status === reimbFilter);
  if (invoiceFilter) filtered = filtered.filter(p => p.invoice_status === invoiceFilter);
  if (projectFilter) filtered = filtered.filter(p => p.project === projectFilter);
  purchaseFilteredData = filtered;

  const totalAmount = filtered.reduce((s, p) => s + (p.items||[]).reduce((a, i) => a + (i.total||0), 0), 0);
  const unreimbursed = filtered.filter(p => p.reimbursement_status !== '已报销');
  const uninvoiced = filtered.filter(p => p.invoice_status !== '已开票');
  const unreimbursedAmount = unreimbursed.reduce((s, p) => s + (p.items||[]).reduce((a, i) => a + (i.total||0), 0), 0);

  $('#pur-stats').innerHTML = `
    <div class="stat-card"><div class="stat-value">${filtered.length}</div><div class="stat-label">总记录数</div></div>
    <div class="stat-card"><div class="stat-value">${Utils.formatMoney(totalAmount)}</div><div class="stat-label">垫付总金额</div></div>
    <div class="stat-card"><div class="stat-value" style="color:var(--danger)">${Utils.formatMoney(unreimbursedAmount)}</div><div class="stat-label">未报销金额</div></div>
    <div class="stat-card"><div class="stat-value" style="color:var(--warning)">${uninvoiced.length}</div><div class="stat-label">未开票数</div></div>
  `;

  // 加载项目列表
  const projects = await window.electronAPI.db.getProjects();
  const sel = $('#pur-project-filter');
  if (sel) {
    const currentVal = sel.value;
    sel.innerHTML = '<option value="">全部</option>' + projects.map(p => `<option>${Utils.escapeHtml(p)}</option>`).join('');
    sel.value = currentVal;
  }

  $('#pur-table-container').innerHTML = `
    <table class="data-table">
      <thead><tr>
        <th>日期</th><th>项目</th><th>经手人</th><th>支付方式</th><th>物料摘要</th>
        <th>合计(¥)</th><th>开票</th><th>报销</th><th>操作</th>
      </tr></thead>
      <tbody>
        ${filtered.map(p => {
          const itemsTotal = (p.items||[]).reduce((s, i) => s + (i.total||0), 0);
          const summary = (p.items||[]).map(i => i.name).filter(Boolean).join('、') || '—';
          const style = p.reimbursement_status !== '已报销' ? 'color:var(--danger)' : '';
          return `
            <tr class="${purchaseArchived ? 'archived' : ''}" style="${style}">
              <td>${Utils.escapeHtml(p.date||'')}</td>
              <td>${Utils.escapeHtml(p.project)}</td>
              <td>${Utils.escapeHtml(p.handler)}</td>
              <td>${Utils.escapeHtml(p.payment_method)}</td>
              <td>${Utils.escapeHtml(summary.slice(0,30))}</td>
              <td>${Utils.formatMoney(itemsTotal)}</td>
              <td>${Utils.escapeHtml(p.invoice_status)}</td>
              <td>${Utils.escapeHtml(p.reimbursement_status)}</td>
              <td class="cell-action">
                ${purchaseArchived
                  ? `<span onclick="showPurchaseForm(${p.id})">查看</span>`
                  : `<span onclick="showPurchaseForm(${p.id})">编辑</span><span onclick="archivePurchase(${p.id})">归档</span>`
                }
                <span class="danger" onclick="deletePurchase(${p.id})">删除</span>
              </td>
            </tr>
          `;
        }).join('')}
      </tbody>
    </table>
  `;
}

function togglePurchaseArchive() {
  purchaseArchived = !purchaseArchived;
  $('#pur-archive-btn').textContent = purchaseArchived ? '📋 返回列表' : '📁 查看归档';
  loadPurchaseData();
}

let purchaseItemCount = 0;

function showPurchaseForm(id = null) {
  purchaseItemCount = 0;
  const isViewOnly = purchaseArchived && id !== null;
  Modal.show(id ? (isViewOnly ? '查看垫付' : '编辑垫付') : '新增垫付', `
    <div class="form-row">
      <label>日期</label><input class="input" id="puf-date" type="date" style="width:150px" ${isViewOnly?'readonly':''}>
      <label>经手人</label><input class="input" id="puf-handler" style="width:150px" ${isViewOnly?'readonly':''}>
    </div>
    <div class="form-row">
      <label>项目</label>
      <span style="display:flex;gap:4px">
        <select class="select" id="puf-project" style="width:150px" ${isViewOnly?'disabled':''}></select>
        ${isViewOnly ? '' : '<button class="btn btn-secondary btn-sm" onclick="addPurchaseProject()">+新增项目</button>'}
      </span>
      <label>支付方式</label>
      <select class="select" id="puf-method" style="width:120px" ${isViewOnly?'disabled':''}>
        <option>微信</option><option>支付宝</option><option>淘宝</option><option>银行卡</option><option>许丹红</option><option>宋总</option>
      </select>
    </div>
    <div class="form-row">
      <label>报销状态</label>
      <select class="select" id="puf-reimb" ${isViewOnly?'disabled':''}><option>未报销</option><option>已报销</option></select>
      <label>开票状态</label>
      <select class="select" id="puf-invoice" ${isViewOnly?'disabled':''}><option>未开票</option><option>已开票</option></select>
    </div>
    <div class="purchase-items">
      <h4>物料明细 ${isViewOnly ? '' : '<button class="btn btn-sm btn-secondary" onclick="addPurchaseItemRow()">+添加行</button>'}</h4>
      <div id="puf-items"></div>
    </div>
    <div class="form-group" style="margin-top:8px"><label>备注</label><input class="input" id="puf-remark" style="width:100%" ${isViewOnly?'readonly':''}></div>
  `, isViewOnly
    ? `<button class="btn btn-secondary" onclick="Modal.hide()">关闭</button>`
    : `<button class="btn btn-secondary" onclick="Modal.hide()">取消</button>
       <button class="btn btn-primary" onclick="savePurchase(${id||'null'})">保存</button>`
  );

  // 加载项目列表
  (async () => {
    const projects = await window.electronAPI.db.getProjects();
    const sel = $('#puf-project');
    if (sel) sel.innerHTML = projects.map(p => `<option>${Utils.escapeHtml(p)}</option>`).join('');
  })();

  if (id) {
    (async () => {
      const purchases = await window.electronAPI.db.getPurchases(0);
      const p = purchases.find(x => x.id === id);
      if (p) {
        $('#puf-date').value = p.date || '';
        $('#puf-handler').value = p.handler || '';
        $('#puf-method').value = p.payment_method || '微信';
        $('#puf-reimb').value = p.reimbursement_status || '未报销';
        $('#puf-invoice').value = p.invoice_status || '未开票';
        $('#puf-remark').value = p.remark || '';
        setTimeout(() => { $('#puf-project').value = p.project || ''; }, 100);
        if (p.items) {
          p.items.forEach(item => addPurchaseItemRow(item, isViewOnly));
        }
      }
    })();
  }
}

function addPurchaseItemRow(data = null, readonly = false) {
  const idx = purchaseItemCount++;
  const row = document.createElement('div');
  row.className = 'purchase-item-row';
  row.id = `pur-item-${idx}`;
  row.innerHTML = `
    <input class="input wide" placeholder="名称" value="${Utils.escapeHtml(data?.name||'')}" ${readonly?'readonly':''}>
    <input class="input" placeholder="规格" value="${Utils.escapeHtml(data?.spec||'')}" ${readonly?'readonly':''}>
    <input class="input" type="number" step="0.01" placeholder="数量" value="${data?.quantity||''}" oninput="calcPurItemTotal(${idx})" style="width:70px" ${readonly?'readonly':''}>
    <input class="input" type="number" step="0.01" placeholder="单价" value="${data?.unit_price||''}" oninput="calcPurItemTotal(${idx})" style="width:80px" ${readonly?'readonly':''}>
    <input class="input wide" placeholder="供应商" value="${Utils.escapeHtml(data?.supplier||'')}" ${readonly?'readonly':''}>
    <input class="input" type="number" step="0.01" placeholder="合计" value="${data?.total||''}" readonly style="width:90px">
    ${readonly ? '' : `<button class="btn btn-sm btn-danger" onclick="document.getElementById('pur-item-${idx}').remove()">×</button>`}
  `;
  $('#puf-items')?.appendChild(row);
}

function calcPurItemTotal(idx) {
  const row = document.getElementById(`pur-item-${idx}`);
  if (!row) return;
  const inputs = row.querySelectorAll('input');
  const qty = parseFloat(inputs[2].value) || 0;
  const price = parseFloat(inputs[3].value) || 0;
  inputs[5].value = (qty * price).toFixed(2);
}

async function addPurchaseProject() {
  const name = prompt('请输入新项目名称：');
  if (name && name.trim()) {
    await window.electronAPI.db.addProject(name.trim());
    const projects = await window.electronAPI.db.getProjects();
    const sel = $('#puf-project');
    if (sel) {
      sel.innerHTML = projects.map(p => `<option>${Utils.escapeHtml(p)}</option>`).join('');
      sel.value = name.trim();
    }
  }
}

async function savePurchase(id) {
  const data = {
    date: $('#puf-date').value,
    project: $('#puf-project').value,
    handler: $('#puf-handler').value,
    payment_method: $('#puf-method').value,
    invoice_status: $('#puf-invoice').value,
    reimbursement_status: $('#puf-reimb').value,
    remark: $('#puf-remark').value,
  };

  const items = [];
  document.querySelectorAll('#puf-items .purchase-item-row').forEach(row => {
    const inputs = row.querySelectorAll('input');
    items.push({
      name: inputs[0].value, spec: inputs[1].value,
      quantity: parseFloat(inputs[2].value) || 0, unit_price: parseFloat(inputs[3].value) || 0,
      supplier: inputs[4].value, total: parseFloat(inputs[5].value) || 0,
    });
  });

  if (id) {
    await window.electronAPI.db.updatePurchase(id, data, items);
  } else {
    await window.electronAPI.db.savePurchase(data, items);
  }
  Modal.hide();
  Utils.showToast('保存成功');
  loadPurchaseData();
  Utils.notifyDataChanged('purchase');
}

async function archivePurchase(id) { await window.electronAPI.db.archivePurchase(id); Utils.showToast('已归档'); loadPurchaseData(); Utils.notifyDataChanged('purchase'); }
async function deletePurchase(id) {
  const ok = await Utils.showConfirm('确认删除', '确定要删除该垫付记录吗？');
  if (ok) { await window.electronAPI.db.deletePurchase(id); Utils.showToast('删除成功'); loadPurchaseData(); Utils.notifyDataChanged('purchase'); }
}
async function purchaseExport() {
  const today = new Date().toISOString().slice(0, 10);
  const result = await window.electronAPI.dialog.saveFile({
    filters: [{ name: 'Excel文件', extensions: ['xlsx'] }],
    defaultPath: `垫付明细_${today}.xlsx`,
  });
  if (!result.canceled && result.filePath) {
    const flat = purchaseFilteredData.map(p => {
      const itemsSummary = (p.items || []).map(i => `${i.name} ${i.spec || ''}×${i.quantity || ''}`).join('; ');
      const itemsTotal = (p.items || []).reduce((s, i) => s + (i.total || 0), 0);
      return {
        date: p.date, project: p.project, handler: p.handler,
        payment_method: p.payment_method, itemsSummary, itemsTotal,
        reimbursement_status: p.reimbursement_status,
        invoice_status: p.invoice_status, remark: p.remark,
      };
    });
    const columnMap = {
      date: '日期', project: '项目', handler: '经手人',
      payment_method: '支付方式', itemsSummary: '物料摘要', itemsTotal: '合计金额',
      reimbursement_status: '报销状态', invoice_status: '开票状态', remark: '备注',
    };
    await window.electronAPI.db.exportToXLSX('垫付明细', flat, result.filePath, columnMap);
    Utils.showToast('导出成功');
  }
}
async function purchaseImport() {
  const result = await window.electronAPI.dialog.openFile({ filters: [{ name: 'Excel文件', extensions: ['xlsx', 'xls'] }] });
  if (!result.canceled) {
    const parseResult = await window.electronAPI.parse.xlsxRead(result.filePaths[0]);
    if (parseResult.success) {
      const sheet = Object.values(parseResult.data)[0];
      if (sheet && sheet.length > 1) {
        const headers = sheet[0];
        const mapField = (row, names) => { for (const n of names) { const idx = headers.findIndex(h => h && h.includes(n)); if (idx >= 0) return row[idx]; } return ''; };
        const groups = {};
        for (let i = 1; i < sheet.length; i++) {
          const row = sheet[i];
          if (!row[0] && !row[1]) continue;
          const key = `${row[0]}|${mapField(row, ['项目'])}|${mapField(row, ['经手人'])}`;
          if (!groups[key]) {
            groups[key] = { date: row[0], project: mapField(row, ['项目']), handler: mapField(row, ['经手人']), method: mapField(row, ['支付方式']) || '微信', items: [] };
          }
          groups[key].items.push({
            name: mapField(row, ['物料名称', '名称']), spec: mapField(row, ['规格']),
            quantity: parseFloat(mapField(row, ['数量'])) || 0, unit_price: parseFloat(mapField(row, ['单价'])) || 0,
            supplier: mapField(row, ['供应商']), total: parseFloat(mapField(row, ['合计', '总额'])) || 0,
          });
        }
        for (const g of Object.values(groups)) {
          await window.electronAPI.db.savePurchase({ date: g.date, project: g.project, handler: g.handler, payment_method: g.method, invoice_status: '未开票', reimbursement_status: '未报销', remark: '' }, g.items);
        }
        Utils.showToast('导入成功');
        loadPurchaseData();
        Utils.notifyDataChanged('purchase');
      }
    }
  }
}

// 上传函数已移至文件顶部
