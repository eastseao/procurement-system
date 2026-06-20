/**
 * 报价单页面 V3.0.4
 * 布局：顶部供应商检索 + 下拉/文本框 + 检索/确认/重置
 *       下方展开的产品信息输入板块（项目号/产品名称/尺寸/材质工艺/供货周期/发货箱规/阶梯价格）
 *       支持添加多个产品块，分别保存/编辑/删除
 *       板块底部：确认、预览、导出 按钮
 *       导出基于内置模板 产品包装报价单_模板.xlsx
 *       文件名：报价单_供方名称_物料项目号_报价时间
 */
let currentQuotationSupplier = null;
let quotationTierIdx = 0;
let quotationProductIdx = 0;

async function loadQuotationPage(container) {
  const suppliers = await window.electronAPI.db.getAllQuotationSuppliers();

  container.innerHTML = `
    <div class="page">
      <div class="page-header">
        <div style="display:flex;gap:8px">
          <button class="btn btn-secondary btn-sm" onclick="showQuotationSupplierForm()">供方</button>
          <button class="btn btn-secondary btn-sm" onclick="showQuotationConfig()">需方</button>
          <button class="btn btn-secondary btn-sm" onclick="showQuotationSupplierList()">管理</button>
        </div>
      </div>
      <div class="page-body">
        <!-- 供应商检索栏 -->
        <div class="search-bar" style="flex-wrap:wrap;gap:8px;align-items:center">
          <label style="font-weight:bold;font-size:13px;white-space:nowrap">供应商检索：</label>
          <select class="select" id="qt-combo" style="width:180px">
            <option value="">-- 请选择 --</option>
            ${suppliers.map(s => `<option value="${Utils.escapeHtml(s.supplier_name)}">${Utils.escapeHtml(s.supplier_name)}</option>`).join('')}
          </select>
          <span style="color:var(--text-secondary);font-size:12px">或输入：</span>
          <input class="input" id="qt-search" placeholder="简称..." style="width:140px">
          <button class="btn btn-primary btn-sm" onclick="searchQuotationSupplier()">检索</button>
          <button class="btn btn-sm btn-success" onclick="confirmQuotationSupplier()">确认</button>
          <button class="btn btn-secondary btn-sm" onclick="resetQuotationSupplier()">重置</button>
          <label style="font-weight:bold;font-size:13px;white-space:nowrap;margin-left:8px">报价日期：</label>
          <input class="input" id="qt-date" type="date" style="width:150px" value="${new Date().toISOString().slice(0,10)}">
          <span id="qt-confirm-status" style="font-size:12px;color:var(--text-secondary)"></span>
        </div>

        <!-- 产品信息输入板块（支持多产品） -->
        <div id="qt-products-area" style="margin-top:12px">
          <!-- 由 JS 动态添加产品块 -->
        </div>
        <div style="margin-top:8px;padding-left:12px">
          <button class="btn btn-sm btn-secondary" onclick="addQuotationProductBlock()">+ 添加产品</button>
        </div>

        <!-- 操作按钮 -->
        <div style="display:flex;gap:8px;margin-top:12px">
          <button class="btn btn-primary" onclick="confirmQuotationAllProducts()">确认保存全部</button>
          <button class="btn btn-secondary" onclick="previewQuotationFromForm()">预览</button>
          <button class="btn btn-secondary" onclick="exportQuotationFromForm()">导出</button>
          <span class="stats-label" id="qt-stats" style="margin-left:auto"></span>
        </div>

        <!-- 已保存产品列表 -->
        <div class="table-container" id="qt-table-container" style="margin-top:12px;flex:1;overflow:auto"></div>
      </div>
    </div>
  `;
  quotationProductIdx = 0;
  addQuotationProductBlock();
  await loadQuotationData();
}

// 新增一个产品块
function addQuotationProductBlock(data = null) {
  const blockIdx = quotationProductIdx++;
  const area = document.getElementById('qt-products-area');
  if (!area) return;

  const block = document.createElement('div');
  block.className = 'qt-product-block';
  block.id = `qt-block-${blockIdx}`;
  block.style.cssText = 'margin-top:12px;padding:12px;border:1px solid var(--border-color,#ddd);border-radius:6px;background:var(--bg-secondary,#fafafa)';
  block.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
      <div style="font-weight:bold;font-size:13px;color:var(--text-primary)">产品信息 #${blockIdx + 1}</div>
      <button class="btn btn-sm btn-danger" onclick="removeQuotationProductBlock(${blockIdx})">移除</button>
    </div>
    <div class="form-row">
      <label>项目号</label><input class="input qt-f-projno" style="width:140px" placeholder="如 81000088" value="${data?.item_no || ''}">
      <label>产品名称</label><input class="input qt-f-prodname" style="width:200px" placeholder="如 纸箱" value="${data?.product_name || ''}">
      <label>尺寸</label><input class="input qt-f-dim" style="width:180px" placeholder="如 400*400*400mm" value="${data?.product_size || ''}">
    </div>
    <div class="form-row">
      <label>材质/工艺</label><input class="input qt-f-material" style="width:240px" placeholder="如 五层瓦楞，牛卡等" value="${data?.material_process || ''}">
      <label>供货周期</label><input class="input qt-f-leadtime" style="width:120px" placeholder="如 7天" value="${data?.supply_cycle || ''}">
      <label>发货箱规</label><input class="input qt-f-carton" style="width:160px" placeholder="如 10pcs/箱" value="${data?.carton_spec || ''}">
    </div>

    <!-- 阶梯价格 -->
    <div style="margin-top:8px">
      <div style="font-weight:bold;font-size:12px;margin-bottom:6px;display:flex;align-items:center;gap:8px">
        <span>阶梯价格</span>
        <button class="btn btn-sm btn-secondary" onclick="addTierRow(${blockIdx})">+ 添加阶梯</button>
      </div>
      <div style="display:flex;gap:6px;align-items:center;font-size:12px;color:var(--text-secondary);margin-bottom:4px;padding-left:0">
        <span style="width:80px">最低数量</span>
        <span style="width:80px">最高数量</span>
        <span style="width:100px">单价(含税运)</span>
        <span style="width:30px"></span>
      </div>
      <div class="qt-tiers" data-block="${blockIdx}"></div>
    </div>
    <div style="margin-top:6px;text-align:right">
      <button class="btn btn-sm btn-primary" onclick="confirmSingleProduct(${blockIdx})">确认保存此产品</button>
    </div>
  `;
  area.appendChild(block);

  // 初始化阶梯价格（1 行或来自 data）
  const tiersEl = block.querySelector('.qt-tiers');
  const tiersData = data?.tiers && data.tiers.length > 0 ? data.tiers : [{ min_qty: '', max_qty: '', unit_price: '' }];
  tiersData.forEach(t => {
    addTierRow(blockIdx, t);
  });

  // 编辑模式记录
  if (data?.id) {
    block.setAttribute('data-editing-id', String(data.id));
  }
}

function removeQuotationProductBlock(idx) {
  const area = document.getElementById('qt-products-area');
  const block = document.getElementById(`qt-block-${idx}`);
  if (!area || !block) return;
  if (area.querySelectorAll('.qt-product-block').length <= 1) {
    Utils.showToast('至少保留一个产品块', 'warning');
    return;
  }
  block.remove();
}

function addTierRow(blockIdx, data = null) {
  const area = document.getElementById('qt-products-area');
  if (!area) return;
  const block = document.getElementById(`qt-block-${blockIdx}`);
  if (!block) return;
  const tiersEl = block.querySelector('.qt-tiers');
  if (!tiersEl) return;

  const rowId = `qt-tier-${quotationTierIdx++}`;
  const div = document.createElement('div');
  div.className = 'tier-row';
  div.id = rowId;
  div.style.cssText = 'display:flex;gap:6px;align-items:center;margin-bottom:4px';
  div.innerHTML = `
    <input class="input qt-t-min" type="number" placeholder="最低" style="width:80px" value="${data?.min_qty ?? ''}">
    <input class="input qt-t-max" type="number" placeholder="最高" style="width:80px" value="${data?.max_qty ?? ''}">
    <input class="input qt-t-price" type="number" step="0.01" placeholder="0.00" style="width:100px" value="${data?.unit_price ?? ''}">
    <button class="btn btn-sm btn-danger" onclick="removeTierRow('${rowId}', ${blockIdx})" style="width:30px">×</button>
  `;
  tiersEl.appendChild(div);
}

function removeTierRow(rowId, blockIdx) {
  const block = document.getElementById(`qt-block-${blockIdx}`);
  if (!block) return;
  const rows = block.querySelectorAll('.tier-row');
  if (rows.length <= 1) {
    Utils.showToast('至少保留一个价格阶梯', 'warning');
    return;
  }
  const el = document.getElementById(rowId);
  if (el) el.remove();
}

function collectSingleBlock(blockIdx) {
  const block = document.getElementById(`qt-block-${blockIdx}`);
  if (!block) return null;

  const projno = (block.querySelector('.qt-f-projno')?.value || '').trim();
  const prodname = (block.querySelector('.qt-f-prodname')?.value || '').trim();
  if (!prodname) { Utils.showToast(`产品 #${blockIdx + 1}：请输入产品名称`, 'warning'); return null; }

  const tiers = [];
  block.querySelectorAll('.qt-tiers .tier-row').forEach(row => {
    const inputs = row.querySelectorAll('input');
    tiers.push({
      min_qty: parseInt(inputs[0]?.value) || 0,
      max_qty: parseInt(inputs[1]?.value) || 0,
      unit_price: parseFloat(inputs[2]?.value) || 0,
    });
  });

  const editingId = block.hasAttribute('data-editing-id') ? parseInt(block.getAttribute('data-editing-id')) : null;

  return {
    id: editingId,
    item_no: projno,
    product_name: prodname,
    product_size: (block.querySelector('.qt-f-dim')?.value || '').trim(),
    material_process: (block.querySelector('.qt-f-material')?.value || '').trim(),
    supply_cycle: (block.querySelector('.qt-f-leadtime')?.value || '').trim(),
    carton_spec: (block.querySelector('.qt-f-carton')?.value || '').trim(),
    tiers,
  };
}

function clearAllProductBlocks() {
  quotationProductIdx = 0;
  const area = document.getElementById('qt-products-area');
  if (!area) return;
  area.innerHTML = '';
  addQuotationProductBlock();
}

async function confirmSingleProduct(blockIdx) {
  const data = collectSingleBlock(blockIdx);
  if (!data) return;

  if (data.id) {
    await window.electronAPI.db.updateQuotationProduct(data.id, {
      item_no: data.item_no,
      product_name: data.product_name,
      product_size: data.product_size,
      material_process: data.material_process,
      supply_cycle: data.supply_cycle,
      carton_spec: data.carton_spec,
      unit: 'PCS',
    });
    await window.electronAPI.db.deleteQuotationTiers(data.id);
    for (const t of data.tiers) {
      await window.electronAPI.db.saveQuotationTier({
        product_id: data.id,
        tier_name: '',
        min_qty: t.min_qty,
        max_qty: t.max_qty,
        unit_price: t.unit_price,
      });
    }
    Utils.showToast(`产品「${data.product_name}」已更新`);
  } else {
    const productId = await window.electronAPI.db.saveQuotationProduct({
      item_no: data.item_no,
      product_name: data.product_name,
      product_size: data.product_size,
      material_process: data.material_process,
      supply_cycle: data.supply_cycle,
      carton_spec: data.carton_spec,
      unit: 'PCS',
    });
    for (const t of data.tiers) {
      await window.electronAPI.db.saveQuotationTier({
        product_id: productId,
        tier_name: '',
        min_qty: t.min_qty,
        max_qty: t.max_qty,
        unit_price: t.unit_price,
      });
    }
    Utils.showToast(`产品「${data.product_name}」已保存`);
  }
  await loadQuotationData();
}

async function confirmQuotationAllProducts() {
  const blocks = document.querySelectorAll('#qt-products-area .qt-product-block');
  let saved = 0;
  for (let i = 0; i < blocks.length; i++) {
    const idx = parseInt(blocks[i].id.replace(/^qt-block-/, ''));
    const data = collectSingleBlock(idx);
    if (!data) continue;
    if (data.id) {
      await window.electronAPI.db.updateQuotationProduct(data.id, {
        item_no: data.item_no,
        product_name: data.product_name,
        product_size: data.product_size,
        material_process: data.material_process,
        supply_cycle: data.supply_cycle,
        carton_spec: data.carton_spec,
        unit: 'PCS',
      });
      await window.electronAPI.db.deleteQuotationTiers(data.id);
      for (const t of data.tiers) {
        await window.electronAPI.db.saveQuotationTier({
          product_id: data.id,
          tier_name: '',
          min_qty: t.min_qty,
          max_qty: t.max_qty,
          unit_price: t.unit_price,
        });
      }
    } else {
      const productId = await window.electronAPI.db.saveQuotationProduct({
        item_no: data.item_no,
        product_name: data.product_name,
        product_size: data.product_size,
        material_process: data.material_process,
        supply_cycle: data.supply_cycle,
        carton_spec: data.carton_spec,
        unit: 'PCS',
      });
      for (const t of data.tiers) {
        await window.electronAPI.db.saveQuotationTier({
          product_id: productId,
          tier_name: '',
          min_qty: t.min_qty,
          max_qty: t.max_qty,
          unit_price: t.unit_price,
        });
      }
    }
    saved++;
  }
  if (saved > 0) {
    Utils.showToast(`已保存 ${saved} 个产品`);
    clearAllProductBlocks();
    await loadQuotationData();
  }
}

// ── 加载产品列表 ──
async function loadQuotationData() {
  const productsRaw = await window.electronAPI.db.getQuotationProducts();
  // 新增记录放在表格上方（id 越大越靠前）
  const products = [...productsRaw].sort((a, b) => (b.id || 0) - (a.id || 0));
  const config = await window.electronAPI.db.getQuotationConfig();
  const stats = [];
  stats.push(`已保存: ${products.length} 个产品`);
  if (config) stats.push(`需方: ${config.buyer_name || '北京同仁堂健康药业（青海）有限公司'}`);
  if (currentQuotationSupplier) stats.push(`供方: ${currentQuotationSupplier.supplier_name}`);
  const statsEl = document.getElementById('qt-stats');
  if (statsEl) statsEl.textContent = stats.join(' | ');

  const tc = document.getElementById('qt-table-container');
  if (tc) {
    tc.innerHTML = `
      <table class="data-table">
        <thead><tr>
          <th>序号</th><th>项目号</th><th>产品名称</th><th>尺寸</th><th>材质/工艺</th>
          <th>供货周期</th><th>发货箱规</th><th>阶梯价格</th><th>操作</th>
        </tr></thead>
        <tbody>
          ${products.map((p, i) => `
            <tr data-id="${p.id}">
              <td>${i + 1}</td>
              <td>${Utils.escapeHtml(p.item_no||'')}</td>
              <td>${Utils.escapeHtml(p.product_name)}</td>
              <td>${Utils.escapeHtml(p.product_size||'')}</td>
              <td>${Utils.escapeHtml(p.material_process||'')}</td>
              <td>${Utils.escapeHtml(p.supply_cycle||'')}</td>
              <td>${Utils.escapeHtml(p.carton_spec||'')}</td>
              <td>${(p.tiers||[]).map(t => `≥${t.min_qty}/<${t.max_qty}: ${Utils.formatMoney(t.unit_price)}`).join(' | ') || '—'}</td>
              <td class="cell-action">
                <span class="primary" onclick="editQuotationProduct(${p.id})">编辑</span>
                <span class="primary" onclick="exportSingleQuotationProduct(${p.id})">导出</span>
                <span class="danger" onclick="deleteQuotationProduct(${p.id})">删除</span>
              </td>
            </tr>
          `).join('')}
          ${products.length === 0 ? '<tr><td colspan="9" style="text-align:center;color:var(--text-secondary)">暂无已保存的产品，请在上方填写后点击确认</td></tr>' : ''}
        </tbody>
      </table>
    `;
  }
}

// ── 编辑产品（回填到一个新产品块）──
async function editQuotationProduct(id) {
  const product = await window.electronAPI.db.getQuotationProduct(id);
  if (!product) { Utils.showToast('产品不存在', 'warning'); return; }

  // 新建一个产品块，回填数据
  addQuotationProductBlock({
    id: product.id,
    item_no: product.item_no,
    product_name: product.product_name,
    product_size: product.product_size,
    material_process: product.material_process,
    supply_cycle: product.supply_cycle,
    carton_spec: product.carton_spec,
    tiers: product.tiers || [],
  });

  Utils.showToast('正在编辑产品，修改后点击"确认保存此产品"或"确认保存全部"');
}

async function deleteQuotationProduct(id) {
  const ok = await Utils.showConfirm('确认删除', '确定要删除该产品吗？');
  if (ok) {
    await window.electronAPI.db.deleteQuotationProduct(id);
    Utils.showToast('已删除');
    loadQuotationData();
  }
}

// ── 导出单条产品报价单 ──
async function exportSingleQuotationProduct(id) {
  const product = await window.electronAPI.db.getQuotationProduct(id);
  if (!product) { Utils.showToast('产品不存在', 'warning'); return; }
  if (!currentQuotationSupplier) { Utils.showToast('请先确认供应商', 'warning'); return; }

  const config = await window.electronAPI.db.getQuotationConfig();
  const supplier = currentQuotationSupplier;
  const products = [product];

  const quoteDateStr = ($('#qt-date')?.value || new Date().toISOString().slice(0,10));
  const dateStr = quoteDateStr.replace(/-/g, '');
  const supplierShort = (supplier.supplier_name || '').replace(/[\\/:*?"<>|]/g, '').substring(0, 20);
  const projectNo = (product.item_no || '').replace(/[\\/:*?"<>|]/g, '').substring(0, 20);
  const prodName = (product.product_name || '').replace(/[\\/:*?"<>|]/g, '').substring(0, 20);
  const defaultName = `报价单_${supplierShort}_${projectNo}_${prodName}_${dateStr}.xlsx`;

  const result = await window.electronAPI.dialog.saveFile({
    defaultPath: defaultName,
    filters: [{ name: 'Excel文件', extensions: ['xlsx'] }],
  });
  if (result.canceled || !result.filePath) return;

  try {
    const templatePath = await window.electronAPI.file.getAssetPath('产品包装报价单_模板.xlsx');
    const exportResult = await window.electronAPI.file.exportQuotation({
      templatePath,
      savePath: result.filePath,
      products,
      config,
      supplier,
    });

    if (exportResult && exportResult.success) {
      Utils.showToast(`报价单已导出：${defaultName}`);
    } else {
      throw new Error(exportResult?.error || '导出失败');
    }
  } catch (e) {
    console.error('报价单导出失败:', e);
    Utils.showToast('导出失败: ' + e.message, 'error');
  }
}

// 收集所有产品块里还未保存的产品（用于预览/导出）
function collectAllPendingProducts() {
  const result = [];
  const blocks = document.querySelectorAll('#qt-products-area .qt-product-block');
  blocks.forEach((block, i) => {
    const blockIdx = parseInt(block.id.replace(/^qt-block-/, ''));
    const d = collectSingleBlock(blockIdx);
    if (d && d.product_name) result.push(d);
  });
  return result;
}

// ── 预览（基于已保存产品）──
async function previewQuotationFromForm() {
  if (!currentQuotationSupplier) {
    Utils.showToast('请先确认供应商', 'warning');
    return;
  }

  const products = await window.electronAPI.db.getQuotationProducts();
  const config = await window.electronAPI.db.getQuotationConfig();
  const supplier = currentQuotationSupplier;

  const bodyHtml = `
    <div style="font-size:12px;line-height:1.8">
      <div style="text-align:center;font-size:16px;font-weight:bold;margin-bottom:8px">产品包装报价单</div>
      <div style="display:flex;justify-content:space-between;margin-bottom:8px">
        <div>
          <div><b>需方：</b>${Utils.escapeHtml(config?.buyer_name || '北京同仁堂健康药业（青海）有限公司')}</div>
          <div><b>联系人：</b>${Utils.escapeHtml(config?.buyer_contact || '')}　<b>电话：</b>${Utils.escapeHtml(config?.buyer_phone || '')}</div>
          <div><b>地址：</b>${Utils.escapeHtml(config?.buyer_address || '')}</div>
        </div>
        <div>
          <div><b>供方：</b>${Utils.escapeHtml(supplier?.supplier_name || '未选择')}</div>
          <div><b>联系人：</b>${Utils.escapeHtml(supplier?.contact_person || supplier?.contact || '')}　<b>电话：</b>${Utils.escapeHtml(supplier?.phone || '')}</div>
          <div><b>报价日期：</b>${($('#qt-date')?.value || new Date().toISOString().slice(0,10))}</div>
        </div>
      </div>
      <table class="data-table" style="font-size:11px;min-width:700px">
        <thead><tr>
          <th>序号</th><th>项目号</th><th>产品名称</th><th>尺寸</th><th>材质/工艺</th>
          <th>供货周期</th><th>箱规</th><th>阶梯价格</th>
        </tr></thead>
        <tbody>
          ${products.map((p, i) => `
            <tr>
              <td>${i+1}</td>
              <td>${Utils.escapeHtml(p.item_no||'')}</td>
              <td>${Utils.escapeHtml(p.product_name)}</td>
              <td>${Utils.escapeHtml(p.product_size||'')}</td>
              <td>${Utils.escapeHtml(p.material_process||'')}</td>
              <td>${Utils.escapeHtml(p.supply_cycle||'')}</td>
              <td>${Utils.escapeHtml(p.carton_spec||'')}</td>
              <td>${(p.tiers||[]).map(t => `≥${t.min_qty}/<${t.max_qty}: ${Utils.formatMoney(t.unit_price)}`).join('<br>') || '—'}</td>
            </tr>
          `).join('')}
          ${products.length === 0 ? '<tr><td colspan="8" style="text-align:center">暂无产品</td></tr>' : ''}
        </tbody>
      </table>
      <div style="margin-top:12px;font-size:11px;color:var(--text-secondary)">
        <div><b>付款方式：</b>${Utils.escapeHtml(config?.payment_terms || '')}</div>
        <div><b>运输方式：</b>${Utils.escapeHtml(config?.transport_method || '')}</div>
        <div><b>发货文件：</b>${Utils.escapeHtml(config?.delivery_docs || '')}</div>
        <div><b>报价要求：</b>${Utils.escapeHtml(config?.quote_requirement || '')}</div>
      </div>
    </div>
  `;
  Modal.show('报价单预览', bodyHtml, `<button class="btn btn-secondary" onclick="Modal.hide()">关闭</button>`);
}

// ── 导出报价单（通过主进程基于模板导出）──
async function exportQuotationFromForm() {
  const products = await window.electronAPI.db.getQuotationProducts();
  if (products.length === 0) { Utils.showToast('没有可导出的产品，请先确认产品', 'warning'); return; }
  if (!currentQuotationSupplier) { Utils.showToast('请先确认供应商', 'warning'); return; }

  const config = await window.electronAPI.db.getQuotationConfig();
  const supplier = currentQuotationSupplier;

  // 文件名：报价单_供方名称_物料项目号_报价时间
  const quoteDateStr2 = ($('#qt-date')?.value || new Date().toISOString().slice(0,10));
  const dateStr = quoteDateStr2.replace(/-/g, '');
  const supplierShort = (supplier.supplier_name || '').replace(/[\\/:*?"<>|]/g, '').substring(0, 20);
  const projectNo = (products[0].item_no || '').replace(/[\\/:*?"<>|]/g, '').substring(0, 20);
  const defaultName = `报价单_${supplierShort}_${projectNo}_${dateStr}.xlsx`;

  const result = await window.electronAPI.dialog.saveFile({
    defaultPath: defaultName,
    filters: [{ name: 'Excel文件', extensions: ['xlsx'] }],
  });
  if (result.canceled || !result.filePath) return;

  try {
    const templatePath = await window.electronAPI.file.getAssetPath('产品包装报价单_模板.xlsx');
    const exportResult = await window.electronAPI.file.exportQuotation({
      templatePath,
      savePath: result.filePath,
      products,
      config,
      supplier,
    });

    if (exportResult && exportResult.success) {
      Utils.showToast(`报价单已导出：${defaultName}`);
    } else {
      throw new Error(exportResult?.error || '导出失败');
    }
  } catch (e) {
    console.error('报价单导出失败:', e);
    Utils.showToast('导出失败: ' + e.message, 'error');
  }
}

// ── 供方信息弹窗 ──
function showQuotationSupplierForm() {
  Modal.show('供方信息', `
    <div class="form-group"><label>供应商名称</label><input class="input" id="qsf-name" style="width:100%"></div>
    <div class="form-row">
      <label>联系人</label><input class="input" id="qsf-contact" style="width:200px">
      <label>联系方式</label><input class="input" id="qsf-phone" style="width:200px">
    </div>
    <div class="form-group"><label>地址</label><input class="input" id="qsf-addr" style="width:100%"></div>
    <div class="form-row">
      <label>报价有效期</label><input class="input" id="qsf-valid" style="width:150px">
    </div>
  `, `
    <button class="btn btn-secondary" onclick="Modal.hide()">取消</button>
    <button class="btn btn-primary" onclick="saveQuotationSupplier()">确认</button>
  `);
}

async function saveQuotationSupplier() {
  await window.electronAPI.db.saveQuotationSupplierRecord({
    supplier_name: $('#qsf-name').value,
    contact_person: $('#qsf-contact').value,
    phone: $('#qsf-phone').value,
    address: $('#qsf-addr').value,
    quote_validity: $('#qsf-valid').value,
  });
  Modal.hide();
  Utils.showToast('供方信息已保存');
  refreshQuotationCombo();
}

async function showQuotationSupplierList() {
  const suppliers = await window.electronAPI.db.getAllQuotationSuppliers();
  Modal.show('供方管理', `
    <div style="max-height:400px;overflow:auto">
      ${suppliers.length === 0 ? '<p style="text-align:center;color:var(--text-secondary)">暂无供方记录</p>' : `
        <table class="data-table">
          <thead><tr><th>名称</th><th>联系人</th><th>电话</th><th>地址</th><th>操作</th></tr></thead>
          <tbody>
            ${suppliers.map(s => `
              <tr>
                <td>${Utils.escapeHtml(s.supplier_name)}</td>
                <td>${Utils.escapeHtml(s.contact||'')}</td>
                <td>${Utils.escapeHtml(s.phone||'')}</td>
                <td>${Utils.escapeHtml(s.address||'')}</td>
                <td class="cell-action">
                  <span class="danger" onclick="deleteQuotationSupplier(${s.id})">删除</span>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `}
    </div>
  `, `<button class="btn btn-secondary" onclick="Modal.hide()">关闭</button>`);
}

async function deleteQuotationSupplier(id) {
  await window.electronAPI.db.deleteQuotationSupplierRecord(id);
  Utils.showToast('已删除');
  showQuotationSupplierList();
  refreshQuotationCombo();
}

async function refreshQuotationCombo() {
  const suppliers = await window.electronAPI.db.getAllQuotationSuppliers();
  const combo = document.getElementById('qt-combo');
  if (combo) {
    combo.innerHTML = `<option value="">-- 请选择 --</option>` + suppliers.map(s => `<option value="${Utils.escapeHtml(s.supplier_name)}">${Utils.escapeHtml(s.supplier_name)}</option>`).join('');
  }
}

// ── 需方配置弹窗 ──
function showQuotationConfig() {
  Modal.show('需方配置', `
    <div class="form-group"><label>需方名称</label><input class="input" id="qcf-buyer" style="width:100%"></div>
    <div class="form-row">
      <label>联系人</label><input class="input" id="qcf-contact" style="width:200px">
      <label>联系方式</label><input class="input" id="qcf-phone" style="width:200px">
    </div>
    <div class="form-group"><label>送货地址</label><input class="input" id="qcf-addr" style="width:100%"></div>
    <div class="form-row">
      <label>付款方式</label><input class="input" id="qcf-payment" style="width:200px">
      <label>运输方式</label><input class="input" id="qcf-transport" style="width:200px">
    </div>
    <div class="form-group"><label>发货文件要求</label><input class="input" id="qcf-docs" style="width:100%"></div>
    <div class="form-group"><label>报价要求</label><textarea class="textarea" id="qcf-requirements" rows="2"></textarea></div>
  `, `
    <button class="btn btn-secondary" onclick="Modal.hide()">取消</button>
    <button class="btn btn-primary" onclick="saveQuotationConfig()">保存</button>
  `);

  (async () => {
    const config = await window.electronAPI.db.getQuotationConfig();
    if (config) {
      $('#qcf-buyer').value = config.buyer_name || '';
      $('#qcf-contact').value = config.buyer_contact || '王维';
      $('#qcf-phone').value = config.buyer_phone || '18094719236';
      $('#qcf-addr').value = config.buyer_address || '';
      $('#qcf-payment').value = config.payment_terms || '';
      $('#qcf-transport').value = config.transport_method || '';
      $('#qcf-docs').value = config.delivery_docs || '';
      $('#qcf-requirements').value = config.quote_requirement || '';
    } else {
      // 默认值
      $('#qcf-contact').value = '王维';
      $('#qcf-phone').value = '18094719236';
    }
  })();
}

async function saveQuotationConfig() {
  await window.electronAPI.db.updateQuotationConfig({
    buyer_name: $('#qcf-buyer').value,
    buyer_contact: $('#qcf-contact').value,
    buyer_phone: $('#qcf-phone').value,
    buyer_address: $('#qcf-addr').value,
    payment_terms: $('#qcf-payment').value,
    transport_method: $('#qcf-transport').value,
    delivery_docs: $('#qcf-docs').value,
    quote_requirement: $('#qcf-requirements').value,
  });
  Modal.hide();
  Utils.showToast('需方配置已保存');
  loadQuotationData();
}

// ── 供应商检索 ──
async function searchQuotationSupplier() {
  const kw = ($('#qt-search')?.value || '').trim();
  if (!kw) {
    const comboVal = document.getElementById('qt-combo')?.value;
    if (!comboVal) return;
    const suppliers = await window.electronAPI.db.getAllQuotationSuppliers();
    const found = suppliers.find(s => s.supplier_name === comboVal);
    if (found) {
      currentQuotationSupplier = found;
      document.getElementById('qt-confirm-status').textContent = `已匹配: ${found.supplier_name}`;
      document.getElementById('qt-confirm-status').style.color = 'var(--primary)';
    }
    return;
  }
  const suppliers = await window.electronAPI.db.getAllQuotationSuppliers();
  const found = suppliers.find(s =>
    (s.supplier_name||'').toLowerCase().includes(kw.toLowerCase()) ||
    (s.contact||'').toLowerCase().includes(kw.toLowerCase()) ||
    (s.address||'').toLowerCase().includes(kw.toLowerCase())
  );
  if (found) {
    currentQuotationSupplier = found;
    const combo = document.getElementById('qt-combo');
    if (combo) combo.value = found.supplier_name;
    document.getElementById('qt-confirm-status').textContent = `已匹配: ${found.supplier_name}`;
    document.getElementById('qt-confirm-status').style.color = 'var(--primary)';
    Utils.showToast(`已匹配: ${found.supplier_name}`);
  } else {
    Utils.showToast('未找到匹配的供应商', 'warning');
  }
}

document.addEventListener('change', (e) => {
  if (e.target.id === 'qt-combo') {
    const name = e.target.value;
    if (!name) { currentQuotationSupplier = null; return; }
    (async () => {
      const suppliers = await window.electronAPI.db.getAllQuotationSuppliers();
      const found = suppliers.find(s => s.supplier_name === name);
      if (found) {
        currentQuotationSupplier = found;
        const status = document.getElementById('qt-confirm-status');
        if (status) { status.textContent = `已选择: ${found.supplier_name}`; status.style.color = 'var(--primary)'; }
        const search = document.getElementById('qt-search');
        if (search) search.value = '';
      }
    })();
  }
});

function confirmQuotationSupplier() {
  if (currentQuotationSupplier) {
    document.getElementById('qt-confirm-status').textContent = `已确认: ${currentQuotationSupplier.supplier_name}`;
    document.getElementById('qt-confirm-status').style.color = 'var(--success, #2E7D32)';
    Utils.showToast(`当前供方: ${currentQuotationSupplier.supplier_name}`);
  } else {
    Utils.showToast('请先检索供应商', 'warning');
  }
}

function resetQuotationSupplier() {
  currentQuotationSupplier = null;
  const combo = document.getElementById('qt-combo');
  if (combo) combo.value = '';
  const search = document.getElementById('qt-search');
  if (search) search.value = '';
  const status = document.getElementById('qt-confirm-status');
  if (status) status.textContent = '';
  loadQuotationData();
}
