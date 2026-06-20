/**
 * 物料台账查询页面
 */
async function loadQueryPage(container) {
  container.innerHTML = `
    <div class="page">
      <div class="page-header">
    
        <div style="display:flex;gap:8px">
          <button class="btn btn-danger btn-sm" onclick="clearLedger()">清除数据</button>
          <button class="btn btn-secondary btn-sm" onclick="ledgerImportCSV()">导入CSV</button>
          <button class="btn btn-secondary btn-sm" onclick="ledgerExport()">导出</button>
        </div>
      </div>
      <div class="page-body">
        <div class="search-bar">
          <label>年份</label>
          <select class="select" id="ledger-year"><option value="">全部</option></select>
          <label>供应商</label>
          <input class="input" id="ledger-supplier" placeholder="模糊搜索" style="width:140px">
          <label>物料名称</label>
          <input class="input" id="ledger-material" placeholder="模糊搜索" style="width:140px">
          <label>项目号</label>
          <input class="input" id="ledger-itemno" placeholder="精准匹配" style="width:120px">
          <button class="btn btn-primary btn-sm" onclick="loadLedgerData()">查询</button>
          <button class="btn btn-secondary btn-sm" onclick="document.getElementById('ledger-year').value='';document.getElementById('ledger-supplier').value='';document.getElementById('ledger-material').value='';document.getElementById('ledger-itemno').value='';loadLedgerData()">重置</button>
        </div>
        <div class="stats-bar"><span class="stats-label" id="ledger-stats"></span></div>
        <div class="table-container" id="ledger-table-container"></div>
      </div>
    </div>
  `;

  // 加载年份列表
  const allData = await window.electronAPI.db.getMaterialLedger({});
  const years = [...new Set(allData.map(d => d.year).filter(Boolean))].sort();
  const yearSel = $('#ledger-year');
  if (yearSel) yearSel.innerHTML = '<option value="">全部</option>' + years.map(y => `<option>${y}</option>`).join('');

  // 默认不显示数据
  $('#ledger-stats').innerHTML = '请点击「查询」加载数据';
  $('#ledger-table-container').innerHTML = '';
}

async function loadLedgerData() {
  const filters = {
    year: $('#ledger-year')?.value || '',
    supplier: $('#ledger-supplier')?.value || '',
    material_name: $('#ledger-material')?.value || '',
    item_no: $('#ledger-itemno')?.value || '',
  };
  const data = await window.electronAPI.db.getMaterialLedger(filters);
  const totalAmount = data.reduce((s, d) => s + (d.amount||0), 0);

  $('#ledger-stats').innerHTML = `共 <strong>${data.length}</strong> 条记录 | 订单总额 <strong>${Utils.formatMoney(totalAmount)}</strong>`;

  $('#ledger-table-container').innerHTML = `
    <table class="data-table">
      <thead><tr>
        <th>合同编号</th><th>供应商</th><th>物料项目号</th><th>物料名称</th>
        <th>产品尺寸</th><th>数量</th><th>单位</th><th>采购单价</th><th>订单总额</th>
      </tr></thead>
      <tbody>
        ${data.map(d => `
          <tr>
            <td>${Utils.escapeHtml(d.contract_no||'')}</td>
            <td>${Utils.escapeHtml(d.supplier||'')}</td>
            <td>${Utils.escapeHtml(d.item_no||'')}</td>
            <td>${Utils.escapeHtml(d.material_name||'')}</td>
            <td>${Utils.escapeHtml(d.product_size||'')}</td>
            <td>${d.quantity}</td>
            <td>${Utils.escapeHtml(d.unit||'')}</td>
            <td>${Utils.formatMoney(d.unit_price)}</td>
            <td>${Utils.formatMoney(d.amount)}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
}

async function clearLedger() {
  const ok = await Utils.showConfirm('确认清除', '确定要清除所有物料台账数据吗？此操作不可撤销！');
  if (ok) {
    await window.electronAPI.db.clearMaterialLedger();
    Utils.showToast('已清除');
    loadLedgerData();
  }
}

async function ledgerExport() {
  const result = await window.electronAPI.dialog.saveFile({
    filters: [{ name: 'Excel文件', extensions: ['xlsx'] }],
  });
  if (!result.canceled && result.filePath) {
    const data = await window.electronAPI.db.getMaterialLedger({});
    await window.electronAPI.db.exportToXLSX('material_ledger', data, result.filePath);
    Utils.showToast('导出成功');
  }
}

async function ledgerImportCSV() {
  const result = await window.electronAPI.dialog.openFile({
    filters: [{ name: 'CSV/JSON文件', extensions: ['csv', 'json'] }],
  });
  if (!result.canceled) {
    const filePath = result.filePaths[0];
    if (filePath.endsWith('.json')) {
      const content = await window.electronAPI.file.read(filePath);
      try {
        const jsonData = JSON.parse(content);
        const rows = Array.isArray(jsonData) ? jsonData : (jsonData.data || []);
        const ledgerRows = rows.map(r => ({
          contract_no: r.contract_no || r['合同编号'] || '',
          supplier: r.supplier || r['供应商'] || r['供应商名称'] || r.vendor || '',
          item_no: r.item_no || r['物料项目号'] || r['项目号'] || '',
          material_name: r.material_name || r['物料名称'] || r['名称'] || '',
          quantity: parseFloat(r.quantity || r['数量']) || 0,
          unit: r.unit || r['单位'] || '',
          unit_price: parseFloat(r.unit_price || r['采购单价'] || r['单价']) || 0,
          amount: parseFloat(r.amount || r['订单总额'] || r['金额']) || 0,
          year: r.year || r['年份'] || ((r.contract_no||'').match(/20\d{2}/)||[''])[0] || '',
          product_size: r.product_size || r['产品尺寸'] || '',
        }));
        await window.electronAPI.db.saveMaterialLedger(ledgerRows);
        Utils.showToast(`导入 ${ledgerRows.length} 条记录`);
        loadLedgerData();
      } catch (e) {
        Utils.showToast('JSON解析失败: ' + e.message, 'error');
      }
    } else {
      const parseResult = await window.electronAPI.parse.csvRead(filePath);
      if (parseResult.success && parseResult.data.length > 1) {
        const headers = parseResult.data[0];
        const mapCol = (row, names) => {
          for (const n of names) {
            const idx = headers.findIndex(h => h && (h === n || h.includes(n)));
            if (idx >= 0) return row[idx];
          }
          return '';
        };
        const rows = parseResult.data.slice(1).filter(r => r.some(c => c)).map(row => {
          const contractNo = mapCol(row, ['合同编号', '合同号', 'contract']);
          return {
            contract_no: contractNo,
            supplier: mapCol(row, ['供应商', '供应商名称', '厂商', 'vendor', 'supplier']),
            item_no: mapCol(row, ['物料项目号', '项目号', 'item_no']),
            material_name: mapCol(row, ['物料名称', '名称', 'material']),
            quantity: parseFloat(mapCol(row, ['数量', 'quantity'])) || 0,
            unit: mapCol(row, ['单位', 'unit']),
            unit_price: parseFloat(mapCol(row, ['采购单价', '单价', 'unit_price'])) || 0,
            amount: parseFloat(mapCol(row, ['订单总额', '金额', 'amount'])) || 0,
            year: (contractNo.match(/20\d{2}/)||[''])[0] || '',
            product_size: mapCol(row, ['产品尺寸', '尺寸', '规格']),
          };
        });
        await window.electronAPI.db.saveMaterialLedger(rows);
        Utils.showToast(`导入 ${rows.length} 条记录`);
        loadLedgerData();
      }
    }
  }
}
