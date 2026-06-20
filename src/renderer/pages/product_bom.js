/**
 * 成品BOM页面 - 对齐 V2.3.2
 * 按钮：导出表格/导入表格/新增BOM
 * 筛选：物料名称/物料项目号/品名/成品项目号（LIKE模糊）
 * 表格：成品项目号/品名/规格/品牌/零售价/物料项目号/物料名称/数量/计量单位/操作
 */
async function loadProductBomPage(container) {
  container.innerHTML = `
    <div class="page">
      <div class="page-header">
    
        <div style="display:flex;gap:8px">
          <button class="btn btn-secondary btn-sm" onclick="bomExport()">📥 导出表格</button>
          <button class="btn btn-secondary btn-sm" onclick="bomImport()">📤 导入表格</button>
          <button class="btn btn-primary btn-sm" onclick="showBomForm()">✚ 新增BOM</button>
        </div>
      </div>
      <div class="page-body">
        <div class="search-bar">
          <label>物料名称</label><input class="input" id="bom-material" placeholder="模糊搜索" style="width:140px">
          <label>物料项目号</label><input class="input" id="bom-mat-no" style="width:120px">
          <label>品名</label><input class="input" id="bom-product" placeholder="模糊搜索" style="width:140px">
          <label>成品项目号</label><input class="input" id="bom-fin-no" style="width:120px">
          <button class="btn btn-primary btn-sm" onclick="loadBomData()">查询</button>
          <button class="btn btn-secondary btn-sm" onclick="document.getElementById('bom-material').value='';document.getElementById('bom-mat-no').value='';document.getElementById('bom-product').value='';document.getElementById('bom-fin-no').value='';loadBomData()">重置</button>
        </div>
        <div class="stats-bar"><span class="stats-label" id="bom-stats"></span></div>
        <div class="table-container" id="bom-table-container"></div>
      </div>
    </div>
  `;
  await loadBomData();
}

async function loadBomData() {
  const filters = {
    material_name: $('#bom-material')?.value || '',
    material_project_no: $('#bom-mat-no')?.value || '',
    product_name: $('#bom-product')?.value || '',
    finished_project_no: $('#bom-fin-no')?.value || '',
  };
  const data = await window.electronAPI.db.getProductBOM(filters);
  $('#bom-stats').innerHTML = `共 <strong>${data.length}</strong> 条BOM记录`;

  $('#bom-table-container').innerHTML = `
    <table class="data-table">
      <thead><tr>
        <th>成品项目号</th><th>品名</th><th>规格</th><th>品牌</th><th>零售价</th>
        <th>物料项目号</th><th>物料名称</th><th>数量</th><th>计量单位</th><th>操作</th>
      </tr></thead>
      <tbody>
        ${data.map(b => `
          <tr ondblclick="showBomForm(${b.id})">
            <td>${Utils.escapeHtml(b.finished_project_no||'')}</td>
            <td>${Utils.escapeHtml(b.product_name||'')}</td>
            <td>${Utils.escapeHtml(b.spec||'')}</td>
            <td>${Utils.escapeHtml(b.brand||'')}</td>
            <td>${Utils.formatMoney(b.retail_price)}</td>
            <td>${Utils.escapeHtml(b.material_project_no||'')}</td>
            <td>${Utils.escapeHtml(b.material_name||'')}</td>
            <td>${b.quantity}</td>
            <td>${Utils.escapeHtml(b.unit||'')}</td>
            <td class="cell-action">
              <span onclick="event.stopPropagation();showBomForm(${b.id})">编辑</span>
              <span class="danger" onclick="event.stopPropagation();deleteBom(${b.id})">删除</span>
            </td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
}

let bomItemCount = 0;

function showBomForm(id = null) {
  bomItemCount = 0;
  Modal.show(id ? '编辑BOM' : '新增BOM', `
    <h4 style="margin-bottom:8px">成品信息</h4>
    <div class="form-row">
      <label>成品项目号</label><input class="input" id="bomf-fin-no" style="width:150px">
      <label>品名</label><input class="input" id="bomf-product" style="width:200px">
    </div>
    <div class="form-row">
      <label>规格</label><input class="input" id="bomf-spec" style="width:150px">
      <label>品牌</label><input class="input" id="bomf-brand" style="width:200px">
    </div>
    <div class="form-row">
      <label>零售价</label><input class="input" id="bomf-retail-price" type="number" step="0.01" style="width:150px">
    </div>
    <h4 style="margin:12px 0 8px">物料清单 <button class="btn btn-sm btn-secondary" onclick="addBomMaterialRow()">+添加行</button></h4>
    <div id="bomf-materials"></div>
  `, `
    <button class="btn btn-secondary" onclick="Modal.hide()">取消</button>
    <button class="btn btn-primary" onclick="saveBom(${id||'null'})">保存</button>
  `);

  if (id) {
    (async () => {
      const all = await window.electronAPI.db.getProductBOM({});
      const item = all.find(b => b.id === id);
      if (item) {
        $('#bomf-fin-no').value = item.finished_project_no || '';
        $('#bomf-product').value = item.product_name || '';
        $('#bomf-spec').value = item.spec || '';
        $('#bomf-brand').value = item.brand || '';
        $('#bomf-retail-price').value = item.retail_price || 0;
        addBomMaterialRow(item);
      }
    })();
  }
}

function addBomMaterialRow(data = null) {
  const idx = bomItemCount++;
  const row = document.createElement('div');
  row.className = 'travel-row';
  row.id = `bom-item-${idx}`;
  row.innerHTML = `
    <input class="input" placeholder="物料项目号" value="${Utils.escapeHtml(data?.material_project_no||'')}" style="width:120px">
    <input class="input" placeholder="物料名称" value="${Utils.escapeHtml(data?.material_name||'')}" style="width:150px">
    <input class="input" type="number" step="0.01" placeholder="数量" value="${data?.quantity||''}" style="width:80px">
    <input class="input" placeholder="单位" value="${Utils.escapeHtml(data?.unit||'')}" style="width:80px">
    <button class="btn btn-sm btn-danger" onclick="document.getElementById('bom-item-${idx}').remove()">×</button>
  `;
  $('#bomf-materials')?.appendChild(row);
}

async function saveBom(id) {
  const finished_project_no = cleanBomValue($('#bomf-fin-no').value);
  const product_name = cleanBomValue($('#bomf-product').value);
  const spec = cleanBomValue($('#bomf-spec').value);
  const brand = cleanBomValue($('#bomf-brand').value);
  const retail_price = parseFloat($('#bomf-retail-price')?.value) || 0;

  if (!finished_project_no) { Utils.showToast('请输入成品项目号', 'error'); return; }

  const rows = [];
  document.querySelectorAll('#bomf-materials .travel-row').forEach(row => {
    const inputs = row.querySelectorAll('input');
    const mpn = cleanBomValue(inputs[0].value);
    const mn = cleanBomValue(inputs[1].value);
    if (!mpn && !mn) return; // skip empty rows
    rows.push({
      finished_project_no,
      product_name,
      spec,
      retail_price,
      brand,
      material_project_no: mpn,
      material_name: mn,
      quantity: parseFloat(inputs[2].value) || 0,
      unit: cleanBomValue(inputs[3].value),
    });
  });

  if (rows.length === 0) { Utils.showToast('请至少添加一条物料', 'error'); return; }

  if (id) {
    // Update: delete old rows, insert new rows
    await window.electronAPI.db.deleteProductBOM(id);
    for (const row of rows) {
      await window.electronAPI.db.saveProductBOM(row);
    }
  } else {
    // Create: insert each row individually
    for (const row of rows) {
      await window.electronAPI.db.saveProductBOM(row);
    }
  }
  Modal.hide();
  Utils.showToast('保存成功');
  loadBomData();
}

/**
 * 清洗BOM值：去空格/换行/制表符，空值返回空字符串
 * 对应 Python clean_bom_value()
 */
function cleanBomValue(val) {
  if (val === null || val === undefined) return '';
  return String(val).replace(/[\s\r\n\t]+/g, ' ').trim();
}

async function deleteBom(id) {
  const ok = await Utils.showConfirm('确认删除', '确定要删除该BOM记录吗？');
  if (ok) {
    await window.electronAPI.db.deleteProductBOM(id);
    Utils.showToast('删除成功');
    loadBomData();
  }
}

async function bomExport() {
  const result = await window.electronAPI.dialog.saveFile({ filters: [{ name: 'Excel文件', extensions: ['xlsx'] }] });
  if (!result.canceled && result.filePath) {
    const data = await window.electronAPI.db.getProductBOM({});
    await window.electronAPI.db.exportToXLSX('product_bom', data, result.filePath);
    Utils.showToast('导出成功');
  }
}

async function bomImport() {
  const result = await window.electronAPI.dialog.openFile({ filters: [{ name: 'Excel文件', extensions: ['xlsx', 'xls'] }] });
  if (!result.canceled) {
    const parseResult = await window.electronAPI.parse.xlsxRead(result.filePaths[0]);
    if (parseResult.success) {
      const sheet = Object.values(parseResult.data)[0];
      if (sheet && sheet.length > 1) {
        // 按 Python V2.3.2 schema: 成品项目号/品名/规格/零售价/品牌/物料项目号/物料名称/数量/单位
        const rows = sheet.slice(1).filter(r => r.some(c => c)).map(row => ({
          finished_project_no: cleanBomValue(row[0]),
          product_name: cleanBomValue(row[1]),
          spec: cleanBomValue(row[2]),
          retail_price: parseFloat(row[3]) || 0,
          brand: cleanBomValue(row[4]),
          material_project_no: cleanBomValue(row[5]),
          material_name: cleanBomValue(row[6]),
          quantity: parseFloat(row[7]) || 0,
          unit: cleanBomValue(row[8]),
        }));
        await window.electronAPI.db.importProductBOM(rows);
        Utils.showToast(`导入 ${rows.length} 条BOM`);
        loadBomData();
      }
    }
  }
}
