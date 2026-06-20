/**
 * 三方比价页面 V3.0.2
 * 修复：添加缺失的申请时间字段、导出基于模板、修复选中状态管理等
 */
async function loadComparePage(container) {
  container.innerHTML = `
    <div class="page">
      <div class="page-header">
        <div style="display:flex;gap:8px">
        </div>
      </div>
      <div class="page-body" style="flex-direction:column">
        <div class="compare-form" id="compare-form">
          <div class="form-row">
            <label>最终做货供应商</label><input class="input" id="cp-final" style="width:180px">
            <label>品名*</label><input class="input" id="cp-name" style="width:180px">
            <label>项目号</label><input class="input" id="cp-project-no" style="width:150px">
            <label>规格尺寸</label><input class="input" id="cp-spec" style="width:180px">
            <label>申请时间</label><input class="input" id="cp-time" type="date" style="width:150px" value="${new Date().toISOString().slice(0,10)}">
          </div>
          <div class="form-row">
            <label>材质结构</label><input class="input" id="cp-material" style="width:300px">
          </div>
          <div class="form-row">
            <label>供应商1</label><input class="input" id="cp-s1" oninput="updateCompareLabels()" style="width:180px">
            <label>供应商2</label><input class="input" id="cp-s2" oninput="updateCompareLabels()" style="width:180px">
            <label>供应商3</label><input class="input" id="cp-s3" oninput="updateCompareLabels()" style="width:180px">
          </div>
          <div id="cp-price-rows">
            <div class="compare-price-row">
              <input class="input" type="number" step="0.01" placeholder="数量" style="width:80px">
              <span class="supplier-tag s1" id="cp-label-s1">供应商1</span><input class="input" type="number" step="0.01" placeholder="价格" style="width:100px">
              <span class="supplier-tag s2" id="cp-label-s2">供应商2</span><input class="input" type="number" step="0.01" placeholder="价格" style="width:100px">
              <span class="supplier-tag s3" id="cp-label-s3">供应商3</span><input class="input" type="number" step="0.01" placeholder="价格" style="width:100px">
              <button class="btn btn-sm btn-danger" onclick="this.closest('.compare-price-row').remove()">×</button>
            </div>
          </div>
          <div style="display:flex;gap:8px;margin-top:8px">
            <button class="btn btn-secondary btn-sm" onclick="addComparePriceRow()">+ 添加数量</button>
            <button class="btn btn-secondary btn-sm" onclick="clearCompareForm()">清空表单</button>
            <button class="btn btn-primary btn-sm" id="cp-save-btn" onclick="saveCompare()">保存记录</button>
            <span class="stats-label" id="cp-edit-hint" style="display:none;color:var(--primary)">编辑模式</span>
          </div>
        </div>
        <div style="flex:1;overflow:auto;padding-top:12px">
          <div class="table-container" id="cp-table-container"></div>
        </div>
      </div>
    </div>
  `;
  updateCompareLabels();
  await loadCompareData();
}

let compareEditId = null;

function updateCompareLabels() {
  const s1 = $('#cp-s1')?.value || '供应商1';
  const s2 = $('#cp-s2')?.value || '供应商2';
  const s3 = $('#cp-s3')?.value || '供应商3';
  const l1 = $('#cp-label-s1'), l2 = $('#cp-label-s2'), l3 = $('#cp-label-s3');
  if (l1) l1.textContent = s1;
  if (l2) l2.textContent = s2;
  if (l3) l3.textContent = s3;
}

function addComparePriceRow() {
  const row = document.createElement('div');
  row.className = 'compare-price-row';
  row.innerHTML = `
    <input class="input" type="number" step="0.01" placeholder="数量" style="width:80px">
    <span class="supplier-tag s1">${$('#cp-s1')?.value||'供应商1'}</span><input class="input" type="number" step="0.01" placeholder="价格" style="width:100px">
    <span class="supplier-tag s2">${$('#cp-s2')?.value||'供应商2'}</span><input class="input" type="number" step="0.01" placeholder="价格" style="width:100px">
    <span class="supplier-tag s3">${$('#cp-s3')?.value||'供应商3'}</span><input class="input" type="number" step="0.01" placeholder="价格" style="width:100px">
    <button class="btn btn-sm btn-danger" onclick="this.closest('.compare-price-row').remove()">×</button>
  `;
  $('#cp-price-rows')?.appendChild(row);
}

function clearCompareForm() {
  ['cp-time','cp-final','cp-name','cp-project-no','cp-material','cp-spec','cp-s1','cp-s2','cp-s3'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = (id === 'cp-time') ? new Date().toISOString().slice(0,10) : '';
  });
  $('#cp-price-rows').innerHTML = '';
  addComparePriceRow();
  compareEditId = null;
  compareSelectedId = null;
  $('#cp-save-btn').textContent = '保存记录';
  const hint = $('#cp-edit-hint');
  if (hint) hint.style.display = 'none';
  updateCompareLabels();
}

async function saveCompare() {
  const rows = [...document.querySelectorAll('#cp-price-rows .compare-price-row')];
  const quantities = rows.map(r => r.querySelectorAll('input')[0].value).join(',');
  const prices1 = rows.map(r => r.querySelectorAll('input')[1].value).join(',');
  const prices2 = rows.map(r => r.querySelectorAll('input')[2].value).join(',');
  const prices3 = rows.map(r => r.querySelectorAll('input')[3].value).join(',');

  const data = {
    apply_date: $('#cp-time').value,
    final_supplier: $('#cp-final').value,
    product_name: $('#cp-name').value,
    item_no: $('#cp-project-no').value,
    material_structure: $('#cp-material').value,
    spec: $('#cp-spec').value,
    supplier1: $('#cp-s1').value,
    supplier2: $('#cp-s2').value,
    supplier3: $('#cp-s3').value,
    quantity_tier: quantities,
    price1_tier: prices1,
    price2_tier: prices2,
    price3_tier: prices3,
  };

  if (!data.product_name) { Utils.showToast('请输入品名', 'warning'); return; }

  if (compareEditId) {
    await window.electronAPI.db.updateThirdPartyRecord(compareEditId, data);
  } else {
    await window.electronAPI.db.saveThirdPartyRecord(data);
  }
  Utils.showToast('保存成功');
  clearCompareForm();
  await loadCompareData();
}

async function loadCompareData() {
  const data = await window.electronAPI.db.getThirdPartyRecords();
  // 新增记录放在表格上方（按 id 倒序）
  data.sort((a, b) => (b.id || 0) - (a.id || 0));

  // 表格刷新时重置选中状态
  compareSelectedId = null;

  $('#cp-table-container').innerHTML = `
    <table class="data-table" id="cp-data-table">
      <thead><tr>
        <th>时间</th><th>品名</th><th>项目号</th><th>材质</th><th>规格</th><th>数量</th>
        <th id="cp-th-s1">供应商1</th><th id="cp-th-s2">供应商2</th><th id="cp-th-s3">供应商3</th>
        <th>最终</th><th>操作</th>
      </tr></thead>
      <tbody>
        ${data.map(r => {
          const qty = (r.quantity_tier||'').split(',');
          const p1 = (r.price1_tier||'').split(',');
          const p2 = (r.price2_tier||'').split(',');
          const p3 = (r.price3_tier||'').split(',');
          const s1 = r.supplier1_name || r.supplier1 || '';
          const s2 = r.supplier2_name || r.supplier2 || '';
          const s3 = r.supplier3_name || r.supplier3 || '';
          return qty.map((q, i) => `
            <tr ondblclick="editCompare(${r.id})" onclick="selectCompareRow(${r.id}, this, event)" data-id="${r.id}">
              <td>${Utils.formatDate(r.apply_date)}</td>
              <td>${Utils.escapeHtml(r.product_name)}</td>
              <td>${Utils.escapeHtml(r.item_no||r.project_no||'')}</td>
              <td>${Utils.escapeHtml(r.material_structure||'')}</td>
              <td>${Utils.escapeHtml(r.spec||r.spec_size||'')}</td>
              <td>${q}</td>
              <td>${s1} ${p1[i]?Utils.formatMoney(p1[i]):''}</td>
              <td>${s2} ${p2[i]?Utils.formatMoney(p2[i]):''}</td>
              <td>${s3} ${p3[i]?Utils.formatMoney(p3[i]):''}</td>
              <td>${i===0?Utils.escapeHtml(r.final_supplier||''):''}</td>
              <td class="cell-action">
                ${i===0?`<span onclick="event.stopPropagation();exportCompare(${r.id})">导出</span><span onclick="event.stopPropagation();editCompare(${r.id})">编辑</span><span class="danger" onclick="event.stopPropagation();deleteCompare(${r.id})">删除</span>`:''}
              </td>
            </tr>
          `).join('');
        }).join('')}
      </tbody>
    </table>
  `;
}

async function editCompare(id) {
  const r = await window.electronAPI.db.getThirdPartyRecord(id);
  if (r) {
    $('#cp-time').value = r.apply_date || '';
    $('#cp-final').value = r.final_supplier || '';
    $('#cp-name').value = r.product_name || '';
    $('#cp-project-no').value = r.item_no || r.project_no || '';
    $('#cp-material').value = r.material_structure || '';
    $('#cp-spec').value = r.spec || r.spec_size || '';
    $('#cp-s1').value = r.supplier1 || r.supplier1_name || '';
    $('#cp-s2').value = r.supplier2 || r.supplier2_name || '';
    $('#cp-s3').value = r.supplier3 || r.supplier3_name || '';

    $('#cp-price-rows').innerHTML = '';
    const qtys = (r.quantity_tier||'').split(',');
    const p1 = (r.price1_tier||'').split(',');
    const p2 = (r.price2_tier||'').split(',');
    const p3 = (r.price3_tier||'').split(',');
    for (let i = 0; i < qtys.length; i++) {
      addComparePriceRow();
      const rows = [...document.querySelectorAll('#cp-price-rows .compare-price-row')];
      const last = rows[rows.length - 1];
      if (last) {
        const inputs = last.querySelectorAll('input');
        inputs[0].value = qtys[i] || '';
        inputs[1].value = p1[i] || '';
        inputs[2].value = p2[i] || '';
        inputs[3].value = p3[i] || '';
      }
    }

    compareEditId = id;
    compareSelectedId = id;
    $('#cp-save-btn').textContent = '保存修改';
    const hint = $('#cp-edit-hint');
    if (hint) hint.style.display = 'inline';
    updateCompareLabels();

    // 高亮选中行
    document.querySelectorAll('#cp-data-table tbody tr').forEach(tr => {
      tr.style.backgroundColor = '';
    });
    document.querySelectorAll(`#cp-data-table tbody tr[data-id="${id}"]`).forEach(tr => {
      tr.style.backgroundColor = 'var(--bg-hover, #f0f0f0)';
    });
  }
}

async function deleteCompare(id) {
  const ok = await Utils.showConfirm('确认删除', '确定要删除该比价记录吗？');
  if (ok) {
    await window.electronAPI.db.deleteThirdPartyRecord(id);
    Utils.showToast('删除成功');
    compareSelectedId = null;
    await loadCompareData();
  }
}

let compareSelectedId = null;

function selectCompareRow(id, row, event) {
  // 不阻止冒泡，但只在非操作按钮点击时处理选中
  if (event && event.target.closest('.cell-action')) return;

  // 取消所有行的选中状态
  document.querySelectorAll('#cp-data-table tbody tr').forEach(tr => {
    tr.style.backgroundColor = '';
  });
  // 选中当前记录的所有行（同 id 可能有多行）
  document.querySelectorAll(`#cp-data-table tbody tr[data-id="${id}"]`).forEach(tr => {
    tr.style.backgroundColor = 'var(--bg-hover, #f0f0f0)';
  });
  compareSelectedId = id;
}

async function exportCompare(id) {
  const record = await window.electronAPI.db.getThirdPartyRecord(id);
  if (!record) { Utils.showToast('记录不存在', 'error'); return; }

  const finalSupplier = (record.final_supplier || '未指定').replace(/[\\/:*?"<>|]/g, '').substring(0, 20);
  const productName = (record.product_name || '物料').replace(/[\\/:*?"<>|]/g, '').substring(0, 20);
  const applyDate = (record.apply_date || new Date().toISOString().slice(0,10)).replace(/-/g, '');
  const defaultName = `比价表_${finalSupplier}_${productName}_${applyDate}.xlsx`;

  const result = await window.electronAPI.dialog.saveFile({
    defaultPath: defaultName,
    filters: [{ name: 'Excel文件', extensions: ['xlsx'] }],
  });
  if (result.canceled || !result.filePath) return;

  // 基于比价表模板导出
  try {
    const templatePath = await window.electronAPI.file.getAssetPath('比价表模板.xlsx');
    const buyerConfig = await window.electronAPI.db.getQuotationConfig();
    const exportResult = await window.electronAPI.file.exportCompare({
      templatePath,
      savePath: result.filePath,
      record,
      buyerConfig,
    });

    if (exportResult && exportResult.success) {
      Utils.showToast(`比价表已导出（基于模板）：${defaultName}`);
    } else {
      throw new Error(exportResult?.error || '导出失败');
    }
  } catch (e) {
    console.error('比价表导出失败:', e);
    Utils.showToast('导出失败: ' + e.message, 'error');
  }
}
