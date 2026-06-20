/**
 * 供应商管理页面 - 对齐 V2.3.2
 * 按钮：新增/导出/导入
 * 筛选：供应商类别下拉/供应商名称搜索/合作状态下拉/查询/重置
 * 表格：名称/合作状态/主营/主营产品/联系人/电话/微信/询比价/打样/付款方式/开票类型/税率/操作
 * 表单分节：📋 基本信息 / 👤 联系方式 / 💼 合作信息 / 📝 备注
 */
let supplierData = [];

async function loadSupplierPage(container) {
  container.innerHTML = `
    <div class="page">
      <div class="page-header">
    
        <div style="display:flex;gap:8px">
          <button class="btn btn-primary btn-sm" onclick="showSupplierForm()">✚ 新增</button>
          <button class="btn btn-secondary btn-sm" onclick="supplierExport()">📥 导出</button>
          <button class="btn btn-secondary btn-sm" onclick="supplierImport()">📤 导入</button>
        </div>
      </div>
      <div class="page-body">
        <div class="search-bar">
          <label>供应商类别</label>
          <select class="select" id="sup-category">
            <option value="">全部</option>
            <option>礼盒</option><option>卡盒</option><option>标签</option>
            <option>玻璃瓶</option><option>复合膜</option><option>铝制品</option>
            <option>塑料罐</option><option>物流箱</option><option>其他</option>
          </select>
          <label>供应商名称</label>
          <input class="input" id="sup-keyword" placeholder="搜索名称/联系人" style="width:160px">
          <label>合作状态</label>
          <select class="select" id="sup-status">
            <option value="">全部</option>
            <option>合作中</option><option>接洽中</option><option>打样中</option><option>已暂停</option>
          </select>
          <button class="btn btn-primary btn-sm" onclick="loadSupplierData()">查询</button>
          <button class="btn btn-secondary btn-sm" onclick="document.getElementById('sup-category').value='';document.getElementById('sup-keyword').value='';document.getElementById('sup-status').value='';loadSupplierData()">重置</button>
        </div>
        <div class="stats-bar"><span class="stats-label" id="sup-stats"></span></div>
        <div class="table-container" id="sup-table-container"></div>
      </div>
    </div>
  `;
  await loadSupplierData();
}

async function loadSupplierData() {
  const category = $('#sup-category')?.value || '';
  const keyword = $('#sup-keyword')?.value || '';
  const status = $('#sup-status')?.value || '';
  const data = await window.electronAPI.db.getSuppliers(category, keyword, status);
  supplierData = data;
  $('#sup-stats').innerHTML = `共 <strong>${data.length}</strong> 家供应商`;

  $('#sup-table-container').innerHTML = `
    <table class="data-table" id="sup-table">
      <thead><tr>
        <th>名称</th><th>合作状态</th><th>主营</th><th>主营产品</th><th>联系人</th><th>电话</th>
        <th>微信</th><th>询比价</th><th>打样</th><th>付款方式</th><th>开票类型</th>
        <th>税率</th><th>操作</th>
      </tr></thead>
      <tbody>
        ${data.map(s => `
          <tr ondblclick="showSupplierForm(${s.id})" data-id="${s.id}">
            <td>${Utils.escapeHtml(s.name)}</td>
            <td>${Utils.escapeHtml(s.cooperation_status||'')}</td>
            <td>${Utils.escapeHtml(s.category||'')}</td>
            <td>${Utils.escapeHtml(s.main_product||'')}</td>
            <td>${Utils.escapeHtml(s.contact_person||'')}</td>
            <td>${Utils.escapeHtml(s.phone||'')}</td>
            <td>${Utils.escapeHtml(s.wechat||'')}</td>
            <td>${Utils.escapeHtml(s.quote_status||'')}</td>
            <td>${Utils.escapeHtml(s.sample_status||'')}</td>
            <td>${Utils.escapeHtml(s.payment_method||'')}</td>
            <td>${Utils.escapeHtml(s.invoice_type||'')}</td>
            <td>${Utils.escapeHtml(s.tax_rate||'')}</td>
            <td class="cell-action">
              <span onclick="event.stopPropagation();showSupplierForm(${s.id})">编辑</span>
              <span class="danger" onclick="event.stopPropagation();deleteSupplier(${s.id})">删除</span>
            </td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;

  // 右键菜单
  const table = $('#sup-table');
  table?.addEventListener('contextmenu', (e) => {
    e.preventDefault();
    const row = e.target.closest('tr[data-id]');
    if (!row) return;
    const id = parseInt(row.dataset.id);
    showContextMenu(e.clientX, e.clientY, [
      { label: '编辑', action: () => showSupplierForm(id) },
      '-',
      { label: '删除', action: () => deleteSupplier(id), danger: true },
    ]);
  });
}

function showSupplierForm(id = null) {
  Modal.show(id ? '编辑供应商' : '新增供应商', `
    <h4 style="margin-bottom:8px">📋 基本信息</h4>
    <div class="supplier-form-grid">
      <div class="form-group"><label>名称 *</label><input class="input" id="sf-name" style="width:100%"></div>
      <div class="form-group"><label>合作状态</label><select class="select" id="sf-status" style="width:100%"><option>合作中</option><option>接洽中</option><option>打样中</option><option>已暂停</option></select></div>
      <div class="form-group"><label>主营类别</label><select class="select" id="sf-category" style="width:100%"><option>礼盒</option><option>卡盒</option><option>标签</option><option>玻璃瓶</option><option>复合膜</option><option>铝制品</option><option>塑料罐</option><option>物流箱</option><option>其他</option></select></div>
      <div class="form-group"><label>主营产品</label><input class="input" id="sf-main-product" style="width:100%"></div>
    </div>
    <h4 style="margin:12px 0 8px">👤 联系方式</h4>
    <div class="supplier-form-grid">
      <div class="form-group"><label>联系人</label><input class="input" id="sf-contact" style="width:100%"></div>
      <div class="form-group"><label>电话</label><input class="input" id="sf-phone" style="width:100%"></div>
      <div class="form-group"><label>微信</label><input class="input" id="sf-wechat" style="width:100%"></div>
    </div>
    <h4 style="margin:12px 0 8px">💼 合作信息</h4>
    <div class="supplier-form-grid">
      <div class="form-group"><label>询比价</label><select class="select" id="sf-inquiry" style="width:100%"><option>已询价</option><option>比价中</option><option>已确认</option><option>—</option></select></div>
      <div class="form-group"><label>打样状态</label><select class="select" id="sf-sample" style="width:100%"><option>未打样</option><option>打样中</option><option>已确认</option><option>—</option></select></div>
      <div class="form-group"><label>付款方式</label><select class="select" id="sf-payment" style="width:100%"><option>款到发货</option><option>货到付款</option><option>30天账期</option><option>60天账期</option><option>月结</option><option>其他</option></select></div>
      <div class="form-group"><label>开票类型</label><select class="select" id="sf-invoice" style="width:100%"><option>增值税专票</option><option>增值税普票</option><option>无需发票</option><option>其他</option></select></div>
      <div class="form-group"><label>税率</label><input class="input" id="sf-tax" style="width:100%"></div>
    </div>
    <h4 style="margin:12px 0 8px">📝 备注</h4>
    <div class="form-group"><label>备注</label><textarea class="textarea" id="sf-remark" rows="2" style="width:100%"></textarea></div>
  `, `
    <button class="btn btn-secondary" onclick="Modal.hide()">取消</button>
    <button class="btn btn-primary" onclick="saveSupplier(${id||'null'})">保存</button>
  `);

  if (id) {
    (async () => {
      const s = await window.electronAPI.db.getSupplier(id);
      if (s) {
        $('#sf-name').value = s.name || '';
        $('#sf-status').value = s.cooperation_status || '合作中';
        $('#sf-category').value = s.category || '礼盒';
        $('#sf-contact').value = s.contact_person || '';
        $('#sf-phone').value = s.phone || '';
        $('#sf-wechat').value = s.wechat || '';
        $('#sf-main-product').value = s.main_product || '';
        $('#sf-inquiry').value = s.quote_status || '—';
        $('#sf-sample').value = s.sample_status || '—';
        $('#sf-payment').value = s.payment_method || '款到发货';
        $('#sf-invoice').value = s.invoice_type || '增值税专票';
        $('#sf-tax').value = s.tax_rate || '';
        $('#sf-remark').value = s.remark || '';
      }
    })();
  }
}

async function saveSupplier(id) {
  const data = {
    name: $('#sf-name').value,
    cooperation_status: $('#sf-status').value,
    category: $('#sf-category').value,
    contact_person: $('#sf-contact').value,
    phone: $('#sf-phone').value,
    wechat: $('#sf-wechat').value,
    main_product: $('#sf-main-product').value,
    quote_status: $('#sf-inquiry').value,
    sample_status: $('#sf-sample').value,
    payment_method: $('#sf-payment').value,
    invoice_type: $('#sf-invoice').value,
    tax_rate: $('#sf-tax').value,
    remark: $('#sf-remark').value,
  };
  if (!data.name) { Utils.showToast('请输入供应商名称', 'warning'); return; }
  if (id) {
    await window.electronAPI.db.updateSupplier(id, data);
  } else {
    await window.electronAPI.db.saveSupplier(data);
  }
  Modal.hide();
  Utils.showToast('保存成功');
  loadSupplierData();
}

async function deleteSupplier(id) {
  const ok = await Utils.showConfirm('确认删除', '确定要删除该供应商吗？');
  if (ok) {
    await window.electronAPI.db.deleteSupplier(id);
    Utils.showToast('删除成功');
    loadSupplierData();
  }
}

async function supplierExport() {
  const result = await window.electronAPI.dialog.saveFile({ filters: [{ name: 'Excel文件', extensions: ['xlsx'] }] });
  if (!result.canceled && result.filePath) {
    await window.electronAPI.db.exportToXLSX('suppliers', supplierData, result.filePath);
    Utils.showToast('导出成功');
  }
}

async function supplierImport() {
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
          await window.electronAPI.db.saveSupplier({
            name: mapField(row, ['名称', '供应商']),
            cooperation_status: mapField(row, ['合作状态', '状态']) || '合作中',
            category: mapField(row, ['主营', '类别']),
            contact_person: mapField(row, ['联系人']),
            phone: mapField(row, ['电话']),
            wechat: mapField(row, ['微信']),
            main_product: mapField(row, ['主营产品']),
            quote_status: mapField(row, ['询比价']),
            sample_status: mapField(row, ['打样']),
            payment_method: mapField(row, ['付款方式']),
            invoice_type: mapField(row, ['开票类型']),
            tax_rate: mapField(row, ['税率']),
            remark: mapField(row, ['备注']),
          });
        }
        Utils.showToast('导入成功');
        loadSupplierData();
      }
    }
  }
}
