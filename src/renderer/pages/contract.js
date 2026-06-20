/**
 * 合同管理页面
 * 功能：合同编号生成 / 合同产品管理 / 供应商管理(合同专用) / 甲方配置 / 生成DOCX合同
 * 入口：loadContractPage(container)
 */

// ── 全局计数器 ──
let contractProductRowCounter = 0;

// ═══════════════════════════════════════════════════════
// 人民币大写转换
// ═══════════════════════════════════════════════════════
function numToRmbUpper(num) {
  if (num === 0 || num == null || isNaN(num)) return '零元整';
  const isNeg = num < 0;
  num = Math.abs(num);
  const digits = ['零', '壹', '贰', '叁', '肆', '伍', '陆', '柒', '捌', '玖'];
  const intUnits = ['', '拾', '佰', '仟'];
  const bigUnits = ['', '万', '亿', '兆'];
  const decUnits = ['角', '分'];

  const parts = num.toFixed(2).split('.');
  const intPart = parts[0];
  const decPart = parts[1];

  let result = '';

  // 整数部分
  if (intPart === '0') {
    result = '';
  } else {
    // 按4位一组分组，从右到左
    let intStr = intPart;
    const groups = [];
    while (intStr.length > 0) {
      groups.unshift(intStr.slice(-4));
      intStr = intStr.slice(0, -4);
    }

    const groupResult = [];
    for (let i = 0; i < groups.length; i++) {
      const g = groups[i];
      const bigUnitIdx = groups.length - 1 - i;
      let gStr = '';
      let hasZero = false;
      let allZero = true;

      for (let j = 0; j < g.length; j++) {
        const d = parseInt(g[j]);
        const unitIdx = g.length - 1 - j;
        if (d === 0) {
          hasZero = true;
        } else {
          if (hasZero) {
            gStr += '零';
            hasZero = false;
          }
          gStr += digits[d] + intUnits[unitIdx];
          allZero = false;
        }
      }

      if (!allZero) {
        // 【修复】用 push 而不是 unshift，否则 >=10000 的金额顺序会被颠倒
        // 例如 123456 会变成 "叁仟肆佰伍拾陆壹拾贰万元整" 而不是 "壹拾贰万叁仟肆佰伍拾陆元整"
        groupResult.push(gStr + bigUnits[bigUnitIdx]);
      }
    }

    result = groupResult.join('') + '元';
  }

  // 小数部分
  const jiao = parseInt(decPart[0]);
  const fen = parseInt(decPart[1]);

  if (jiao === 0 && fen === 0) {
    result += '整';
  } else {
    if (jiao > 0) {
      result += digits[jiao] + '角';
    }
    if (fen > 0) {
      result += digits[fen] + '分';
    }
  }

  return isNeg ? '负' + result : result;
}

// ═══════════════════════════════════════════════════════
// 页面入口
// ═══════════════════════════════════════════════════════
async function loadContractPage(container) {
  // 设置默认日期为今天
  const today = new Date().toISOString().slice(0, 10);
  const todayParts = today.split('-');
  const defaultMonthDay = todayParts[1] + '-' + todayParts[2];
  const defaultYear = todayParts[0];

  container.innerHTML = `
    <div class="page">
      <div class="page-header">

        <div style="display:flex;gap:8px">
          <button class="btn btn-secondary btn-sm" onclick="openSupplierMgmt()">🏭 供应商管理</button>
          <button class="btn btn-secondary btn-sm" onclick="openPartyAConfig()">🏢 甲方配置</button>
        </div>
      </div>
      <div class="page-body">
        <!-- 合同生成区域 -->
        <div class="contract-section">
          <h3>📋 合同生成</h3>

          <!-- 合同编号 + 签订日期 -->
          <div class="form-row">
            <label>合同编号</label>
            <div style="display:flex;gap:4px;align-items:center">
              <input class="input" id="ct-prefix" value="SC" style="width:50px;text-align:center;font-weight:bold" oninput="updateContractNo()">
              <input class="input" id="ct-year" value="${defaultYear}" placeholder="年份" maxlength="4" style="width:70px;text-align:center" oninput="updateContractNo()">
              <input class="input" id="ct-monthday" value="${defaultMonthDay}" placeholder="MM-DD" maxlength="5" style="width:80px;text-align:center" oninput="updateContractNo()">
              <input class="input" id="ct-seq" value="01" placeholder="序号" maxlength="2" style="width:50px;text-align:center" oninput="updateContractNo()">
              <span style="margin:0 8px;color:var(--text-secondary)">→</span>
              <input class="input" id="ct-fullno" readonly style="width:200px;background:var(--sidebar);font-weight:bold;color:var(--primary)">
            </div>
            <label style="margin-left:12px">签订日期</label>
            <input class="input" id="ct-date" type="date" value="${today}" style="width:150px">
          </div>

          <!-- 物料名称 -->
          <div class="form-row">
            <label>物料名称</label>
            <input class="input" id="ct-material" placeholder="输入物料名称" style="width:220px">
          </div>

          <!-- 供应商选择 -->
          <div class="form-row">
            <label>供应商</label>
            <select class="select" id="ct-supplier" style="width:280px">
              <option value="">-- 请选择供应商 --</option>
            </select>
            <button class="btn btn-secondary btn-sm" onclick="openSupplierMgmt()">管理供应商</button>
            <label style="margin-left:12px">税率(%)</label>
            <input class="input" id="ct-tax-rate" type="number" value="13" step="0.01" style="width:80px">
            <label style="margin-left:12px">供货周期(天)</label>
            <input class="input" id="ct-delivery-days" type="number" value="15" style="width:80px">
          </div>

          <!-- 产品明细表 -->
          <div style="margin-top:12px">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
              <label style="font-size:13px;font-weight:600;color:var(--text)">产品明细</label>
              <button class="btn btn-sm btn-secondary" onclick="addContractProductRow()">+ 添加产品</button>
            </div>
            <div class="table-container" style="max-height:300px">
              <table class="data-table" id="ct-product-table">
                <thead>
                  <tr>
                    <th style="width:40px">#</th>
                    <th style="width:160px">名称</th>
                    <th style="width:100px">项目号</th>
                    <th style="width:120px">规格</th>
                    <th style="width:60px">单位</th>
                    <th style="width:80px">数量</th>
                    <th style="width:90px">单价</th>
                    <th style="width:100px">金额</th>
                    <th style="width:100px">备注</th>
                    <th style="width:40px"></th>
                  </tr>
                </thead>
                <tbody id="ct-product-tbody">
                </tbody>
              </table>
            </div>
          </div>

          <!-- 合计金额 -->
          <div style="margin-top:12px;display:flex;justify-content:space-between;gap:20px;align-items:center;padding:12px;background:var(--sidebar);border-radius:8px">
            <div style="display:flex;gap:20px;align-items:center">
              <span style="color:var(--text-secondary);font-size:12px">合计金额：</span>
              <span id="ct-total" style="font-size:18px;font-weight:bold;color:var(--primary)">¥0.00</span>
              <span style="font-size:12px;color:var(--text-secondary)">大写：</span>
              <span id="ct-total-upper" style="font-weight:600;color:var(--text)">零元整</span>
            </div>
            <button class="btn btn-primary btn-sm" onclick="generateContract()">📄 生成合同</button>
          </div>
        </div>

        <!-- 已保存的合同产品列表 -->
        <div class="contract-section">
          <h3>📦 合同产品记录 <span id="ct-saved-stats" style="font-size:12px;color:var(--text-secondary);font-weight:normal"></span></h3>
          <div class="table-container" id="ct-saved-table-container"></div>
        </div>
      </div>
    </div>
  `;

  // 初始化
  updateContractNo();
  await loadContractSuppliers();
  await loadContractProducts();
}

// ═══════════════════════════════════════════════════════
// 合同编号自动组合
// ═══════════════════════════════════════════════════════
function updateContractNo() {
  const prefix = $('#ct-prefix')?.value || 'SC';
  const year = $('#ct-year')?.value || '';
  const monthday = $('#ct-monthday')?.value || '';
  const seq = $('#ct-seq')?.value || '';
  const full = prefix + year + '-' + monthday + '-' + seq;
  if ($('#ct-fullno')) {
    $('#ct-fullno').value = full;
  }
}

// ═══════════════════════════════════════════════════════
// 合同产品行（生成区域内的动态表格）
// ═══════════════════════════════════════════════════════
function addContractProductRow(data = null) {
  const idx = contractProductRowCounter++;
  const tbody = $('#ct-product-tbody');
  if (!tbody) return;

  const tr = document.createElement('tr');
  tr.id = `ct-prod-row-${idx}`;
  tr.innerHTML = `
    <td style="text-align:center;color:var(--text-secondary)">${idx + 1}</td>
    <td><input class="input input-sm" id="ct-pname-${idx}" value="${Utils.escapeHtml(data?.product_name || '')}" placeholder="名称" style="width:100%"></td>
    <td><input class="input input-sm" id="ct-pno-${idx}" value="${Utils.escapeHtml(data?.project_no || '')}" placeholder="项目号" style="width:100%"></td>
    <td><input class="input input-sm" id="ct-pspec-${idx}" value="${Utils.escapeHtml(data?.spec || '')}" placeholder="规格" style="width:100%"></td>
    <td><input class="input input-sm" id="ct-punit-${idx}" value="${Utils.escapeHtml(data?.unit || '')}" placeholder="单位" style="width:100%"></td>
    <td><input class="input input-sm" id="ct-pqty-${idx}" type="number" step="1" min="0" value="${data?.quantity || ''}" placeholder="0" style="width:100%" oninput="calcContractRowAmount(${idx})"></td>
    <td><input class="input input-sm" id="ct-pprice-${idx}" type="number" step="0.01" min="0" value="${data?.unit_price || ''}" placeholder="0.00" style="width:100%" oninput="calcContractRowAmount(${idx})"></td>
    <td><input class="input input-sm" id="ct-pamount-${idx}" type="number" step="0.01" value="${data?.amount || ''}" readonly style="width:100%;background:var(--sidebar);font-weight:600"></td>
    <td><input class="input input-sm" id="ct-premark-${idx}" value="${Utils.escapeHtml(data?.remark || '')}" placeholder="备注" style="width:100%"></td>
    <td><button class="btn btn-sm btn-danger" style="padding:2px 6px" onclick="removeContractProductRow(${idx})">×</button></td>
  `;
  tbody.appendChild(tr);

  // 如果有数据，计算金额
  if (data) calcContractRowAmount(idx);
}

function removeContractProductRow(idx) {
  const row = document.getElementById(`ct-prod-row-${idx}`);
  if (row) {
    row.remove();
    calcContractTotal();
  }
}

function calcContractRowAmount(idx) {
  const qty = parseFloat(document.getElementById(`ct-pqty-${idx}`)?.value) || 0;
  const price = parseFloat(document.getElementById(`ct-pprice-${idx}`)?.value) || 0;
  const amount = (qty * price).toFixed(2);
  const amountEl = document.getElementById(`ct-pamount-${idx}`);
  if (amountEl) amountEl.value = amount;
  calcContractTotal();
}

function calcContractTotal() {
  let total = 0;
  document.querySelectorAll('#ct-product-tbody tr').forEach(tr => {
    const amountInput = tr.querySelector('input[readonly]');
    if (amountInput) {
      total += parseFloat(amountInput.value) || 0;
    }
  });
  const totalEl = $('#ct-total');
  const upperEl = $('#ct-total-upper');
  if (totalEl) totalEl.textContent = Utils.formatMoney(total);
  if (upperEl) upperEl.textContent = numToRmbUpper(total);
}

// ═══════════════════════════════════════════════════════
// 生成合同 (调用文件生成接口)
// ═══════════════════════════════════════════════════════
async function generateContract() {
  const contractNo = $('#ct-fullno')?.value || '';
  const signingDate = $('#ct-date')?.value || '';
  const materialName = $('#ct-material')?.value || '';
  const supplierId = $('#ct-supplier')?.value || '';
  const taxRate = parseFloat($('#ct-tax-rate')?.value) || 13;
  const deliveryDays = parseInt($('#ct-delivery-days')?.value) || 15;

  if (!contractNo) { Utils.showToast('请填写合同编号', 'warning'); return; }
  if (!signingDate) { Utils.showToast('请选择签订日期', 'warning'); return; }
  if (!supplierId) { Utils.showToast('请选择供应商', 'warning'); return; }

  // 收集产品明细
  const products = [];
  document.querySelectorAll('#ct-product-tbody tr').forEach(tr => {
    const inputs = tr.querySelectorAll('input:not([readonly])');
    const amountInput = tr.querySelector('input[readonly]');
    if (inputs.length >= 6) {
      const qty = parseFloat(inputs[4]?.value) || 0;
      const price = parseFloat(inputs[5]?.value) || 0;
      products.push({
        product_name: inputs[0]?.value || '',
        project_no: inputs[1]?.value || '',
        spec: inputs[2]?.value || '',
        unit: inputs[3]?.value || '',
        quantity: qty,
        unit_price: price,
        amount: qty * price,
        remark: inputs[6]?.value || '',
      });
    }
  });

  if (products.length === 0) { Utils.showToast('请至少添加一个产品', 'warning'); return; }

  // 计算合计
  const totalAmount = products.reduce((s, p) => s + p.amount, 0);

  // 获取供应商信息 - 从合同供应商表获取（包含完整的银行账号信息）
  const allSuppliers = await window.electronAPI.db.getContractSuppliers();
  let supplierData = allSuppliers?.find(s => s.id === parseInt(supplierId)) || null;
  // 若合同供应商表中不存在，尝试从普通供应商表回退
  if (!supplierData) {
    const supplier = await window.electronAPI.db.getSupplier(parseInt(supplierId));
    supplierData = supplier;
  }

  // 获取甲方配置
  let partyA = {
    company_name: '北京同仁堂健康药业（青海）有限公司',
    address: '青海省德令哈市河西街道同仁堂路1号',
    contact: '龙存英',
    phone: '13897764859',
    legal_rep: '',
  };
  try {
    const partyAResult = await window.electronAPI.db.getContractPartyA();
    if (partyAResult && partyAResult.company_name) {
      partyA = {
        company_name: partyAResult.company_name || '北京同仁堂健康药业（青海）有限公司',
        address: partyAResult.address || '青海省德令哈市河西街道同仁堂路1号',
        contact: partyAResult.contact || '龙存英',
        phone: partyAResult.phone || '13897764859',
        legal_rep: partyAResult.legal_rep || '',
      };
    } else {
      // 向后兼容：读取旧的settings配置
      const settings = await window.electronAPI.db.getSettings();
      const partyAStr = settings?.find(s => s.key === 'contract_party_a')?.value;
      if (partyAStr) {
        const saved = JSON.parse(partyAStr);
        partyA = {
          company_name: saved.company_name || '北京同仁堂健康药业（青海）有限公司',
          address: saved.address || '青海省德令哈市河西街道同仁堂路1号',
          contact: saved.contact || '龙存英',
          phone: saved.phone || '13897764859',
          legal_rep: saved.legal_rep || '',
        };
      }
    }
  } catch (e) { /* ignore */ }

  // 获取模板路径
  const templatePath = await window.electronAPI.file.getAssetPath('contract_template.docx');

  // 文件名格式：采购合同_供应商名_物料名_合同编号
  let supplierFileName = (supplierData?.full_name || supplierData?.name || '').substring(0, 30).replace(/[\\/:*?"<>|]/g, '') || '未指定';
  let materialFileName = materialName.substring(0, 20).replace(/[\\/:*?"<>|]/g, '') || '未命名';
  const defaultFileName = `采购合同_${supplierFileName}_${materialFileName}_${contractNo}.docx`;

  // 弹出保存文件对话框
  const saveResult = await window.electronAPI.dialog.saveFile({
    title: '保存合同文件',
    defaultPath: defaultFileName,
    filters: [{ name: 'Word文档', extensions: ['docx'] }],
  });

  if (saveResult.canceled) return;

  try {
    const result = await window.electronAPI.file.generateContract({
      templatePath,
      savePath: saveResult.filePath,
      contractNo,
      contractDate: signingDate,
      materialName,
      partyB: supplierData,
      partyA,
      products,
      totalAmount,
      totalAmountUpper: numToRmbUpper(totalAmount),
      taxRate,
      deliveryDays,
    });

    if (result && result.success) {
      Utils.showToast('合同文件生成成功！');
      // 同时保存产品到数据库
      for (const p of products) {
        await window.electronAPI.db.saveContractProduct({
          contract_no: contractNo,
          ...p,
        });
      }
      await loadContractProducts();
    } else {
      Utils.showToast('合同生成失败：' + (result?.error || '未知错误'), 'error');
    }
  } catch (err) {
    Utils.showToast('合同生成异常：' + (err.message || err), 'error');
  }
}

// ═══════════════════════════════════════════════════════
// 加载合同供应商下拉
// ═══════════════════════════════════════════════════════
async function loadContractSuppliers() {
  try {
    const suppliers = await window.electronAPI.db.getContractSuppliers();
    const sel = $('#ct-supplier');
    if (!sel) return;
    const currentVal = sel.value;
    sel.innerHTML = '<option value="">-- 请选择供应商 --</option>' +
      suppliers.map(s => `<option value="${s.id}">${Utils.escapeHtml(s.full_name || s.short_name || '')}</option>`).join('');
    sel.value = currentVal;
  } catch (e) {
    // getContractSuppliers may not exist yet, silently ignore
  }
}

// ═══════════════════════════════════════════════════════
// 加载已保存的合同产品列表
// ═══════════════════════════════════════════════════════
async function loadContractProducts() {
  try {
    const products = await window.electronAPI.db.getContractProducts();
    const statsEl = $('#ct-saved-stats');
    if (statsEl) statsEl.textContent = `共 ${products.length} 条记录`;

    const container = $('#ct-saved-table-container');
    if (!container) return;

    container.innerHTML = `
      <table class="data-table" id="ct-saved-table">
        <thead>
          <tr>
            <th>合同编号</th>
            <th>名称</th>
            <th>项目号</th>
            <th>规格</th>
            <th>单位</th>
            <th>数量</th>
            <th>单价</th>
            <th>金额</th>
            <th>备注</th>
            <th style="width:140px">操作</th>
          </tr>
        </thead>
        <tbody>
          ${products.map(p => `
            <tr data-id="${p.id}">
              <td>${Utils.escapeHtml(p.contract_no || '')}</td>
              <td>${Utils.escapeHtml(p.product_name || '')}</td>
              <td>${Utils.escapeHtml(p.project_no || '')}</td>
              <td>${Utils.escapeHtml(p.spec || '')}</td>
              <td>${Utils.escapeHtml(p.unit || '')}</td>
              <td>${p.quantity || 0}</td>
              <td>${Utils.formatMoney(p.unit_price || 0)}</td>
              <td>${Utils.formatMoney(p.amount || 0)}</td>
              <td>${Utils.escapeHtml(p.remark || '')}</td>
              <td class="cell-action" style="display:flex;gap:8px">
                <span class="link" onclick="editContractProduct(${p.id})">编辑</span>
                <span class="link" onclick="exportContractProduct(${p.id})">导出</span>
                <span class="danger" onclick="deleteContractProduct(${p.id})">删除</span>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;

    // 右键菜单
    const table = $('#ct-saved-table');
    if (table) {
      table.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        const row = e.target.closest('tr[data-id]');
        if (!row) return;
        const id = parseInt(row.dataset.id);
        showContextMenu(e.clientX, e.clientY, [
          { label: '编辑', action: () => editContractProduct(id) },
          { label: '导出', action: () => exportContractProduct(id) },
          { label: '删除', action: () => deleteContractProduct(id), danger: true },
        ]);
      });
    }
  } catch (e) {
    // silently ignore
  }
}

async function deleteContractProduct(id) {
  const ok = await Utils.showConfirm('确认删除', '确定要删除该合同产品记录吗？');
  if (ok) {
    try {
      await window.electronAPI.db.deleteContractProduct(id);
      Utils.showToast('删除成功');
      await loadContractProducts();
    } catch (e) {
      Utils.showToast('删除失败', 'error');
    }
  }
}

// ── 编辑合同产品：将记录数据加载到上方的合同生成表单 ──
async function editContractProduct(id) {
  try {
    // 获取全部合同产品，找到所有与此合同编号相关的产品
    const allProducts = await window.electronAPI.db.getContractProducts();
    const target = allProducts.find(p => p.id === id);
    if (!target) {
      Utils.showToast('未找到记录', 'error');
      return;
    }

    // 填充合同编号
    const ctNo = target.contract_no || '';
    if ($('#ct-fullno')) $('#ct-fullno').value = ctNo;
    // 尝试分解 SC2026-06-15-01 格式
    const match = ctNo.match(/^SC(\d{4})-(\d{2}-\d{2})-(\d{2})$/);
    if (match) {
      if ($('#ct-year')) $('#ct-year').value = match[1];
      if ($('#ct-monthday')) $('#ct-monthday').value = match[2];
      if ($('#ct-seq')) $('#ct-seq').value = match[3];
    }

    // 清空现有产品行
    const tbody = document.getElementById('ct-product-tbody');
    if (tbody) tbody.innerHTML = '';
    // 重置计数器
    if (typeof contractProductRowCounter !== 'undefined') contractProductRowCounter = 0;

    // 添加产品行
    addContractProductRow({
      product_name: target.product_name,
      project_no: target.project_no,
      spec: target.spec,
      unit: target.unit,
      quantity: target.quantity,
      unit_price: target.unit_price,
      amount: target.amount,
      remark: target.remark,
    });

    // 滚动到合同生成区域
    window.scrollTo({ top: 0, behavior: 'smooth' });
    Utils.showToast('已加载到合同生成表单');
  } catch (e) {
    Utils.showToast('编辑失败：' + e.message, 'error');
  }
}

// ── 导出合同产品为单独的合同文档 ──
async function exportContractProduct(id) {
  try {
    const allProducts = await window.electronAPI.db.getContractProducts();
    const target = allProducts.find(p => p.id === id);
    if (!target) {
      Utils.showToast('未找到记录', 'error');
      return;
    }

    // 准备产品数据
    const products = [{
      product_name: target.product_name || '',
      project_no: target.project_no || '',
      spec: target.spec || '',
      unit: target.unit || '',
      quantity: target.quantity || 0,
      unit_price: target.unit_price || 0,
      amount: target.amount || 0,
      remark: target.remark || '',
    }];

    const totalAmount = target.amount || 0;

    // 获取甲方配置（默认值）
    const partyA = {
      company_name: '北京同仁堂健康药业（青海）有限公司',
      address: '青海省德令哈市河西街道同仁堂路1号',
      contact: '龙存英',
      phone: '13897764859',
      legal_rep: '',
    };
    const settings = await window.electronAPI.db.getSettings();
    try {
      const savedStr = settings?.find(s => s.key === 'contract_party_a')?.value;
      if (savedStr) {
        const saved = JSON.parse(savedStr);
        partyA.company_name = saved.company_name || partyA.company_name;
        partyA.address = saved.address || partyA.address;
        partyA.contact = saved.contact || partyA.contact;
        partyA.phone = saved.phone || partyA.phone;
        partyA.legal_rep = saved.legal_rep || '';
      }
    } catch (e) { /* ignore */ }

    // 空的乙方（导出时不自动填充供应商）
    const partyB = {};

    // 弹出保存对话框
    const templatePath = await window.electronAPI.file.getAssetPath('contract_template.docx');
    const saveResult = await window.electronAPI.dialog.saveFile({
      title: '导出合同文件',
      defaultPath: `采购合同_${target.contract_no || '未命名'}_${target.product_name || 'product'}.docx`,
      filters: [{ name: 'Word文档', extensions: ['docx'] }],
    });
    if (saveResult.canceled) return;

    const result = await window.electronAPI.file.generateContract({
      templatePath,
      savePath: saveResult.filePath,
      contractNo: target.contract_no || '',
      contractDate: '',
      materialName: target.product_name || '',
      partyB,
      partyA,
      products,
      totalAmount,
      totalAmountUpper: numToRmbUpper(totalAmount),
      taxRate: 13,
      deliveryDays: 15,
    });

    if (result && result.success) {
      Utils.showToast('导出成功！');
    } else {
      Utils.showToast('导出失败：' + (result?.error || '未知错误'), 'error');
    }
  } catch (e) {
    Utils.showToast('导出异常：' + e.message, 'error');
  }
}

// ═══════════════════════════════════════════════════════
// 供应商管理弹窗（合同专用表）
// ═══════════════════════════════════════════════════════
async function openSupplierMgmt() {
  const suppliers = await window.electronAPI.db.getContractSuppliers();

  Modal.show('供应商管理（合同专用）', `
    <div style="display:flex;justify-content:flex-end;margin-bottom:8px">
      <button class="btn btn-primary btn-sm" onclick="showContractSupplierForm()">✚ 新增供应商</button>
    </div>
    <div class="table-container" style="max-height:400px">
      <table class="data-table" id="ct-sup-table">
        <thead>
          <tr>
            <th>简称</th>
            <th>全称</th>
            <th>法人</th>
            <th>联系人</th>
            <th>电话</th>
            <th>账期(天)</th>
            <th>开户行</th>
            <th style="width:100px">操作</th>
          </tr>
        </thead>
        <tbody>
          ${suppliers.map(s => `
            <tr data-id="${s.id}">
              <td>${Utils.escapeHtml(s.short_name || '')}</td>
              <td>${Utils.escapeHtml(s.full_name || '')}</td>
              <td>${Utils.escapeHtml(s.legal_rep || '')}</td>
              <td>${Utils.escapeHtml(s.contact || '')}</td>
              <td>${Utils.escapeHtml(s.phone || '')}</td>
              <td>${s.payment_days || ''}</td>
              <td>${Utils.escapeHtml(s.bank || '')}</td>
              <td class="cell-action">
                <span onclick="showContractSupplierForm(${s.id})">编辑</span>
                <span class="danger" onclick="deleteContractSupplier(${s.id})">删除</span>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `, `<button class="btn btn-secondary" onclick="Modal.hide()">关闭</button>`);
}

function showContractSupplierForm(id = null) {
  Modal.show(id ? '编辑供应商' : '新增供应商', `
    <h4 style="margin-bottom:8px">📋 基本信息</h4>
    <div class="supplier-form-grid">
      <div class="form-group"><label>简称 *</label><input class="input" id="csf-short" style="width:100%"></div>
      <div class="form-group"><label>全称 *</label><input class="input" id="csf-full" style="width:100%"></div>
      <div class="form-group"><label>法人代表</label><input class="input" id="csf-legal" style="width:100%"></div>
      <div class="form-group"><label>地址</label><input class="input" id="csf-address" style="width:100%"></div>
    </div>
    <h4 style="margin:12px 0 8px">👤 联系信息</h4>
    <div class="supplier-form-grid">
      <div class="form-group"><label>联系人</label><input class="input" id="csf-contact" style="width:100%"></div>
      <div class="form-group"><label>授权代表</label><input class="input" id="csf-auth" style="width:100%"></div>
      <div class="form-group"><label>电话</label><input class="input" id="csf-phone" style="width:100%"></div>
      <div class="form-group"><label>传真</label><input class="input" id="csf-fax" style="width:100%"></div>
    </div>
    <h4 style="margin:12px 0 8px">💰 财务信息</h4>
    <div class="supplier-form-grid">
      <div class="form-group"><label>付款天数</label><input class="input" id="csf-days" type="number" value="90" style="width:100%"></div>
      <div class="form-group"><label>付款方式</label>
        <select class="select" id="csf-paymethod" style="width:100%">
          <option>电汇</option><option>转账</option><option>承兑</option><option>现金</option>
        </select>
      </div>
      <div class="form-group"><label>账户名称</label><input class="input" id="csf-account" style="width:100%"></div>
      <div class="form-group"><label>开户银行</label><input class="input" id="csf-bank" style="width:100%"></div>
      <div class="form-group" style="grid-column:span 2"><label>账号</label><input class="input" id="csf-bankno" style="width:100%"></div>
    </div>
    <h4 style="margin:12px 0 8px">📝 备注</h4>
    <div class="form-group"><label>备注</label><textarea class="textarea" id="csf-remark" rows="2" style="width:100%"></textarea></div>
  `, `
    <button class="btn btn-secondary" onclick="openSupplierMgmt()">返回</button>
    <button class="btn btn-primary" onclick="saveContractSupplier(${id || 'null'})">保存</button>
  `);

  if (id) {
    (async () => {
      const suppliers = await window.electronAPI.db.getContractSuppliers();
      const s = suppliers.find(x => x.id === id);
      if (s) {
        $('#csf-short').value = s.short_name || '';
        $('#csf-full').value = s.full_name || '';
        $('#csf-legal').value = s.legal_rep || '';
        $('#csf-address').value = s.address || '';
        $('#csf-contact').value = s.contact || '';
        $('#csf-auth').value = s.auth_rep || '';
        $('#csf-phone').value = s.phone || '';
        $('#csf-fax').value = s.fax || '';
        $('#csf-days').value = s.payment_days || 90;
        $('#csf-paymethod').value = s.payment_method || '电汇';
        $('#csf-account').value = s.account_name || '';
        $('#csf-bank').value = s.bank || '';
        $('#csf-bankno').value = s.account || '';
        $('#csf-remark').value = s.remark || '';
      }
    })();
  }
}

async function saveContractSupplier(id) {
  const shortName = $('#csf-short')?.value || '';
  const fullName = $('#csf-full')?.value || '';
  if (!shortName) { Utils.showToast('请输入供应商简称', 'warning'); return; }
  if (!fullName) { Utils.showToast('请输入供应商全称', 'warning'); return; }

  const data = {
    short_name: shortName,
    full_name: fullName,
    legal_rep: $('#csf-legal')?.value || '',
    address: $('#csf-address')?.value || '',
    contact: $('#csf-contact')?.value || '',
    auth_rep: $('#csf-auth')?.value || '',
    phone: $('#csf-phone')?.value || '',
    fax: $('#csf-fax')?.value || '',
    payment_days: parseInt($('#csf-days')?.value) || 90,
    payment_method: $('#csf-paymethod')?.value || '电汇',
    account_name: $('#csf-account')?.value || '',
    bank: $('#csf-bank')?.value || '',
    account: $('#csf-bankno')?.value || '',
    remark: $('#csf-remark')?.value || '',
  };

  try {
    if (id) {
      await window.electronAPI.db.updateContractSupplier(id, data);
    } else {
      await window.electronAPI.db.saveContractSupplier(data);
    }
    Utils.showToast('保存成功');
    await openSupplierMgmt();
    await loadContractSuppliers();
  } catch (e) {
    Utils.showToast('保存失败：' + (e.message || e), 'error');
  }
}

async function deleteContractSupplier(id) {
  const ok = await Utils.showConfirm('确认删除', '确定要删除该供应商吗？');
  if (ok) {
    try {
      await window.electronAPI.db.deleteContractSupplier(id);
      Utils.showToast('删除成功');
      await openSupplierMgmt();
      await loadContractSuppliers();
    } catch (e) {
      Utils.showToast('删除失败', 'error');
    }
  }
}

// ═══════════════════════════════════════════════════════
// 甲方配置弹窗
// ═══════════════════════════════════════════════════════
async function openPartyAConfig() {
  // 从 settings 中加载
  let partyA = {};
  try {
    const settings = await window.electronAPI.db.getSettings();
    const partyAStr = settings?.find(s => s.key === 'contract_party_a')?.value;
    if (partyAStr) partyA = JSON.parse(partyAStr);
  } catch (e) { /* ignore */ }

  Modal.show('甲方配置', `
    <div class="form-group">
      <label>公司名称 *</label>
      <input class="input" id="pa-company" style="width:100%" placeholder="请输入甲方公司全称">
    </div>
    <div class="supplier-form-grid">
      <div class="form-group"><label>法人代表</label><input class="input" id="pa-legal" style="width:100%"></div>
      <div class="form-group"><label>地址</label><input class="input" id="pa-address" style="width:100%"></div>
      <div class="form-group"><label>联系人</label><input class="input" id="pa-contact" style="width:100%"></div>
      <div class="form-group"><label>电话</label><input class="input" id="pa-phone" style="width:100%"></div>
    </div>
  `, `
    <button class="btn btn-secondary" onclick="Modal.hide()">取消</button>
    <button class="btn btn-primary" onclick="savePartyAConfig()">保存</button>
  `);

  // 填充已有数据，如无则使用默认值
  setTimeout(() => {
    if ($('#pa-company')) $('#pa-company').value = partyA.company_name || '北京同仁堂健康药业（青海）有限公司';
    if ($('#pa-legal')) $('#pa-legal').value = partyA.legal_rep || '';
    if ($('#pa-address')) $('#pa-address').value = partyA.address || '青海省德令哈市河西街道同仁堂路1号';
    if ($('#pa-contact')) $('#pa-contact').value = partyA.contact || '龙存英';
    if ($('#pa-phone')) $('#pa-phone').value = partyA.phone || '13897764859';
  }, 50);
}

async function savePartyAConfig() {
  const companyName = $('#pa-company')?.value || '';
  if (!companyName) {
    Utils.showToast('请输入甲方公司名称', 'warning');
    return;
  }

  const partyA = {
    company_name: companyName,
    legal_rep: $('#pa-legal')?.value || '',
    address: $('#pa-address')?.value || '',
    contact: $('#pa-contact')?.value || '',
    phone: $('#pa-phone')?.value || '',
  };

  try {
    await window.electronAPI.db.updateSetting('contract_party_a', JSON.stringify(partyA));
    Modal.hide();
    Utils.showToast('甲方配置已保存');
  } catch (e) {
    Utils.showToast('保存失败：' + (e.message || e), 'error');
  }
}
