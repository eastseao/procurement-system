/**
 * 采购计划页面 - 对齐 V2.3.2
 * 按钮：手动添加/导入文件/导出/刷新/已归档/删除选中
 * 表格：序号/审批编号/采购明细序号/物料名称/规格/单位/数量/操作
 * 右键菜单
 */
let planArchived = false;

async function loadPlanPage(container) {
  planArchived = false;
  container.innerHTML = `
    <div class="page">
      <div class="page-header">
        <div style="display:flex;gap:8px">
          <button class="btn btn-primary btn-sm" onclick="planImportFile()">📄 导入文件</button>
          <button class="btn btn-secondary btn-sm" onclick="planDownloadTemplate()">📋 下载模板</button>
          <button class="btn btn-secondary btn-sm" onclick="showPlanForm()">✚ 手动添加</button>
        </div>
      </div>
      <div class="page-body">
        <div class="stats-bar">
          <span class="stats-label" id="plan-stats"></span>
          <div style="display:flex;gap:8px;margin-left:auto">
            <button class="btn btn-secondary btn-sm" onclick="planExport()">📥 导出</button>
            <button class="btn btn-secondary btn-sm" onclick="loadPlanData()">🔄 刷新</button>
            <button class="btn btn-secondary btn-sm" id="plan-archive-btn" onclick="togglePlanArchive()">📁 已归档</button>
            <button class="btn btn-secondary btn-sm" onclick="deleteSelectedPlans()" style="color:var(--danger);border-color:var(--danger)">🗑 删除</button>
          </div>
        </div>
        <div class="table-container" id="plan-table-container"></div>
      </div>
    </div>
  `;
  await loadPlanData();
}

async function loadPlanData() {
  const data = await window.electronAPI.db.getPlanRecords(planArchived ? 1 : 0);
  $('#plan-stats').innerHTML = `共 <strong>${data.length}</strong> 条记录`;

  // 新增的记录（id 较大）排在表格上方，原有顺序向下；若 data 已有 id，按 id 倒序即可
  const sortedData = [...data].sort((a, b) => {
    const idA = a.id || 0;
    const idB = b.id || 0;
    return idB - idA;
  });

  $('#plan-table-container').innerHTML = `
    <table class="data-table" id="plan-table">
      <thead><tr>
        <th><input type="checkbox" id="plan-select-all" onchange="togglePlanSelectAll(this.checked)"></th>
        <th>序号</th><th>审批编号</th><th>名称</th><th>规格</th>
        <th>单位</th><th>数量</th><th>操作</th>
      </tr></thead>
      <tbody>
        ${sortedData.map((r, i) => `
          <tr class="${planArchived?'archived':''}" data-id="${r.id}">
            <td><input type="checkbox" class="plan-row-check" data-id="${r.id}"></td>
            <td>${i + 1}</td>
            <td>${Utils.escapeHtml(r.approval_no||'')}</td>
            <td>${Utils.escapeHtml(r.material_name||r.name||'')}</td>
            <td>${Utils.escapeHtml(r.spec||'')}</td>
            <td>${Utils.escapeHtml(r.unit||'')}</td>
            <td>${r.quantity}</td>
            <td class="cell-action">
              <span onclick="showPlanForm(${r.id})">编辑</span>
              <span onclick="copyPlanRecord(${r.id})">复制</span>
              <span onclick="archivePlanRecord(${r.id})">${planArchived?'取消归档':'归档'}</span>
              <span class="danger" onclick="deletePlanRecord(${r.id})">删除</span>
            </td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;

  // 右键菜单
  $('#plan-table')?.addEventListener('contextmenu', (e) => {
    e.preventDefault();
    const row = e.target.closest('tr[data-id]');
    if (!row) return;
    const id = parseInt(row.dataset.id);
    showContextMenu(e.clientX, e.clientY, [
      { label: '编辑', action: () => showPlanForm(id) },
      { label: '复制', action: () => copyPlanRecord(id) },
      { label: planArchived ? '取消归档' : '归档', action: () => archivePlanRecord(id) },
      '-',
      { label: '删除', action: () => deletePlanRecord(id), danger: true },
    ]);
  });
}

function togglePlanSelectAll(checked) {
  document.querySelectorAll('.plan-row-check').forEach(cb => { cb.checked = checked; });
}

async function deleteSelectedPlans() {
  const checked = [...document.querySelectorAll('.plan-row-check:checked')];
  if (checked.length === 0) { Utils.showToast('请先选中要删除的记录', 'warning'); return; }
  const ok = await Utils.showConfirm('确认删除', `确定要删除选中的 ${checked.length} 条记录吗？`);
  if (ok) {
    for (const cb of checked) {
      await window.electronAPI.db.deletePlanRecord(parseInt(cb.dataset.id));
    }
    Utils.showToast(`已删除 ${checked.length} 条记录`);
    loadPlanData();
  }
}

function togglePlanArchive() {
  planArchived = !planArchived;
  $('#plan-archive-btn').textContent = planArchived ? '📋 返回' : '📁 已归档';
  loadPlanData();
}

function showPlanForm(id = null) {
  Modal.show(id ? '编辑计划' : '手动添加', `
    <div class="form-row">
      <label>审批编号</label><input class="input" id="plf-approval" style="width:150px">
    </div>
    <div class="form-row">
      <label>物料名称*</label><input class="input" id="plf-name" style="width:200px">
      <label>规格</label><input class="input" id="plf-spec" style="width:200px">
    </div>
    <div class="form-row">
      <label>数量*</label><input class="input" id="plf-qty" type="number" step="0.01" style="width:100px" oninput="calcPlanTotal()">
      <label>单位</label><input class="input" id="plf-unit" style="width:100px">
      <label>单价</label><input class="input" id="plf-price" type="number" step="0.01" style="width:100px" oninput="calcPlanTotal()">
      <label>金额</label><input class="input" id="plf-total" type="number" step="0.01" style="width:100px" readonly>
    </div>
    <div class="form-row">
      <label>期望交付日期</label><input class="input" id="plf-delivery" type="date" style="width:150px">
      <label>备注</label><input class="input" id="plf-remark" style="flex:1">
    </div>
  `, `
    <button class="btn btn-secondary" onclick="Modal.hide()">取消</button>
    <button class="btn btn-primary" onclick="savePlanRecord(${id||'null'})">保存</button>
  `);

  if (id) {
    (async () => {
      const all = await window.electronAPI.db.getPlanRecords(0);
      const r = all.find(x => x.id === id);
      if (r) {
        $('#plf-approval').value = r.approval_no || '';
        $('#plf-name').value = r.material_name || '';
        $('#plf-spec').value = r.spec || '';
        $('#plf-qty').value = r.quantity || '';
        $('#plf-unit').value = r.unit || '';
        $('#plf-price').value = r.unit_price || '';
        $('#plf-total').value = r.amount || '';
        $('#plf-delivery').value = r.expected_delivery || '';
        $('#plf-remark').value = r.remark || '';
      }
    })();
  }
}

function calcPlanTotal() {
  const qty = parseFloat($('#plf-qty').value) || 0;
  const price = parseFloat($('#plf-price').value) || 0;
  $('#plf-total').value = (qty * price).toFixed(2);
}

async function savePlanRecord(id) {
  const data = {
    approval_no: $('#plf-approval').value,
    material_name: $('#plf-name').value,
    spec: $('#plf-spec').value,
    quantity: parseFloat($('#plf-qty').value) || 0,
    unit: $('#plf-unit').value,
    unit_price: parseFloat($('#plf-price').value) || 0,
    amount: parseFloat($('#plf-total').value) || 0,
    expected_delivery: $('#plf-delivery').value,
    remark: $('#plf-remark').value,
  };
  if (!data.material_name) { Utils.showToast('请输入物料名称', 'warning'); return; }
  if (id) {
    await window.electronAPI.db.updatePlanRecord(id, data);
  } else {
    await window.electronAPI.db.savePlanRecord(data);
  }
  Modal.hide();
  Utils.showToast('保存成功');
  loadPlanData();
}

async function copyPlanRecord(id) {
  const all = await window.electronAPI.db.getPlanRecords(0);
  const r = all.find(x => x.id === id);
  if (r) {
    await window.electronAPI.db.savePlanRecord({
      ...r, id: undefined,
    });
    Utils.showToast('已复制');
    loadPlanData();
  }
}

async function archivePlanRecord(id) {
  await window.electronAPI.db.updatePlanRecord(id, { archived: 1 });
  Utils.showToast('已归档');
  loadPlanData();
}

async function deletePlanRecord(id) {
  const ok = await Utils.showConfirm('确认删除', '确定要删除该计划记录吗？');
  if (ok) {
    await window.electronAPI.db.deletePlanRecord(id);
    Utils.showToast('删除成功');
    loadPlanData();
  }
}

async function planExport() {
  const result = await window.electronAPI.dialog.saveFile({
    filters: [{ name: 'Excel文件', extensions: ['xlsx'] }],
    defaultPath: `采购计划_${new Date().toISOString().slice(0,10).replace(/-/g,'')}.xlsx`,
  });
  if (!result.canceled && result.filePath) {
    const data = await window.electronAPI.db.getPlanRecords(0);
    const columnMap = {
      approval_no: '审批编号',
      material_name: '物料名称',
      spec: '规格',
      unit: '单位',
      quantity: '数量',
      unit_price: '单价',
      amount: '金额',
      expected_delivery: '期望交付日期',
      remark: '备注',
    };
    await window.electronAPI.db.exportToXLSX('plan', data, result.filePath, columnMap);
    Utils.showToast('导出成功');
  }
}

// ── 采购计划文件解析：通用表头识别（PDF / XLSX / XLS / CSV / DOCX）──
// 多别名映射：将各种常见中文表头统一识别到标准字段
const PLAN_HEADER_ALIASES = {
  approval_no: ['审批', '审批编号', '审批单号', '审批号', '采购单号', '项目编号', '项目号', '单号', '编号', '单据号'],
  material_name: ['物料名称', '物料', '名称', '货品名称', '产品名称', '品名', '材料名称', '商品名称', '物资名称', '物料描述'],
  spec: ['规格', '规格型号', '型号', '规格/型号', '尺寸', '规格尺寸', '规格说明'],
  unit: ['单位', '计量单位', '单位(个/盒/箱)', '计量单位/单位'],
  quantity: ['数量', '需求数量', '采购数量', '申请数量', '计划数量', '订购数量', '计划需求数量'],
  unit_price: ['单价', '单价(元)', '含税单价', '报价单价', '单价（元）'],
  amount: ['金额', '总价', '合计', '小计', '总金额', '含税金额', '金额(元)', '总金额(元)'],
  expected_delivery: ['期望交付', '期望到货', '交货日期', '交付日期', '到货日期', '需求日期', '交期', '发货日期', '交付', '期望', '计划到货日期'],
  remark: ['备注', '说明', '注释', '备注说明', '注'],
};

function _planFindHeaderIndex(headers, field) {
  const aliases = PLAN_HEADER_ALIASES[field] || [];
  for (const alias of aliases) {
    const i = headers.findIndex(h => {
      if (h == null) return false;
      const v = String(h).replace(/\s+/g, '').trim();
      return v === alias || v.includes(alias);
    });
    if (i >= 0) return i;
  }
  return -1;
}

function _planNormalizeDate(val) {
  if (!val) return '';
  const s = String(val).trim();
  // yyyy-mm-dd 或 yyyy/mm/dd 或 yyyy年mm月dd日
  const m = s.match(/(\d{4})\s*[年\-\/.]\s*(\d{1,2})\s*[月\-\/.]\s*(\d{1,2})/);
  if (m) return `${m[1]}-${m[2].padStart(2, '0')}-${m[3].padStart(2, '0')}`;
  // Excel 序列号日期（部分解析器会返回数字）
  if (/^\d{4,5}$/.test(s)) {
    const num = parseInt(s, 10);
    if (num > 10000 && num < 100000) {
      const d = new Date(Math.round((num - 25569) * 86400 * 1000));
      if (!isNaN(d.getTime())) return d.toISOString().slice(0, 10);
    }
  }
  // 简单 yyyy-mm-dd
  const m2 = s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})/);
  if (m2) return `${m2[1]}-${m2[2].padStart(2, '0')}-${m2[3].padStart(2, '0')}`;
  return s;
}

function _planToRow(row, headers) {
  const get = (field) => {
    const idx = _planFindHeaderIndex(headers, field);
    if (idx < 0) return '';
    return row[idx] == null ? '' : String(row[idx]).trim();
  };
  const qty = parseFloat(get('quantity')) || 0;
  const price = parseFloat(get('unit_price')) || 0;
  const amountRaw = parseFloat(get('amount'));
  return {
    approval_no: get('approval_no'),
    material_name: get('material_name'),
    spec: get('spec'),
    unit: get('unit'),
    quantity: qty,
    unit_price: price,
    amount: !isNaN(amountRaw) && amountRaw > 0 ? amountRaw : (qty * price),
    expected_delivery: _planNormalizeDate(get('expected_delivery')),
    remark: get('remark'),
  };
}

// 当无法识别表头时（首行是纯数据），自动按"物质名称 / 规格 / 单位 / 数量 / 单价 / 金额 / 备注"顺序兜底
function _planFallbackRow(row) {
  if (!row || row.length === 0) return null;
  const qtyIdx = row.findIndex((v, i) => {
    const n = parseFloat(v);
    return !isNaN(n) && n > 0 && !/^[\d.]+$/.test(String(row[0] || ''));
  });
  const qty = qtyIdx >= 0 ? parseFloat(row[qtyIdx]) : parseFloat(row[row.length - 1]) || 0;
  return {
    material_name: String(row[0] || '').trim(),
    spec: row.length > 2 ? String(row[1] || '').trim() : '',
    unit: row.length > 3 ? String(row[2] || '').trim() : '',
    quantity: qty,
    unit_price: 0, amount: 0,
    expected_delivery: '', remark: '',
  };
}

async function planImportFile() {
  const result = await window.electronAPI.dialog.openFile({
    filters: [
      { name: '支持的格式', extensions: ['pdf', 'xlsx', 'xls', 'csv', 'docx'] },
    ],
  });
  if (!result.canceled) {
    const filePath = result.filePaths[0];
    const ext = filePath.split('.').pop().toLowerCase();
    let rows = [];

    try {
      if (ext === 'pdf') {
        Utils.showToast('PDF解析中，请稍候...', 'warning');
        const parseResult = await window.electronAPI.parse.pdfParse(filePath);
        if (parseResult.success) {
          const rawText = parseResult.text || '';
          const rawLines = rawText.split('\n').map(l => l.trim()).filter(Boolean);

          // ── 策略A：钉钉/企业采购类PDF（采购明细N + 名称/数量单位0） ──
          const pdfMeta = {};
          const dingRows = [];

          const UNIT_RE = '(kg|g|克|公斤|套|张|个|盒|箱|瓶|袋|包|支|米|ml|L|l|升|mL|台|件|桶)';
          const TAIL_RE = new RegExp('(\\d+(?:\\.\\d+)?)\\s*' + UNIT_RE + '\\s*0*\\s*$');

          for (const line of rawLines) {
            // 1) 数据行：采购明细N + 物料信息
            const lineNorm = line.replace(/[\s\u00a0]+/g, '').trim();
            const detailMatch = lineNorm.match(/^采购明细(\d+)(.+)$/);
            if (detailMatch) {
              const rest = detailMatch[2];
              const slashIdx = rest.lastIndexOf('/');
              let name = '';
              let spec = '';
              let qty = 0;
              let unit = '个';

              // 从末尾匹配"数量+单位+0"
              const tailMatch = rest.match(TAIL_RE);
              if (tailMatch && slashIdx > 0) {
                // 有明确单位：名称=斜杠前，数量单位=斜杠后
                qty = parseFloat(tailMatch[1]);
                unit = tailMatch[2];
                const qtyStartInRest = rest.length - tailMatch[0].length;
                name = rest.substring(0, qtyStartInRest);
                // 去除末尾的 "/"
                if (name.endsWith('/')) name = name.slice(0, -1);
              } else if (slashIdx > 0) {
                // 没匹配到单位尾部，但有 "/"——尝试从 "/" 后解析数字
                name = rest.substring(0, slashIdx);
                const after = rest.substring(slashIdx + 1);
                const numMatch = after.match(/^(\d+(?:\.\d+)?)/);
                if (numMatch) {
                  qty = parseFloat(numMatch[1]);
                  const unitPart = after.substring(numMatch[0].length).replace(/0*$/, '').trim();
                  unit = unitPart || '个';
                } else {
                  qty = 1;
                }
              } else {
                // 没有 "/"，把整行当作名称
                name = rest;
                qty = 1;
              }

              if (name && qty > 0) {
                dingRows.push({
                  material_name: name.trim(),
                  spec: spec.trim(),
                  unit: unit,
                  quantity: qty,
                  unit_price: 0, amount: 0,
                  expected_delivery: '', remark: '',
                });
              }
              continue;
            }

            // 2) 顶部元信息（在出现第一行采购明细之前）
            if (dingRows.length === 0) {
              if (line.startsWith('审批编号') && !pdfMeta.approval_no) {
                pdfMeta.approval_no = line.substring(4).trim();
              } else if (line.startsWith('期望交付日期') && !pdfMeta.expected_delivery) {
                pdfMeta.expected_delivery = line.substring(6).trim();
              } else if (line.startsWith('创建人') && !line.startsWith('创建人部门') && !pdfMeta.creator) {
                pdfMeta.creator = line.substring(3).trim();
              }
            }

            // 3) 遇到"总价格"即停止（后续是审批流程等噪声）
            if (dingRows.length > 0 && /^总价格/.test(line)) break;
          }

          if (dingRows.length > 0) {
            rows = dingRows.map(r => ({
              ...r,
              approval_no: pdfMeta.approval_no || '',
              expected_delivery: pdfMeta.expected_delivery || '',
            }));
          } else {
            // ── 策略B：普通表格型PDF（多空格/tab分隔） ──
            const candidates = [];
            for (const line of rawLines) {
              const parts = line.split(/\s{2,}|\t|[,，;；|/]/).map(p => p.trim()).filter(Boolean);
              if (parts.length >= 3) candidates.push(parts);
            }
            let header = null;
            let headerIdx = -1;
            for (let i = 0; i < candidates.length; i++) {
              const row = candidates[i];
              const joined = row.join('').replace(/\s+/g, '');
              const hasQtyKeyword = PLAN_HEADER_ALIASES.quantity.some(a => joined.includes(a));
              const hasMatKeyword = PLAN_HEADER_ALIASES.material_name.some(a => joined.includes(a));
              if (hasQtyKeyword || hasMatKeyword) { header = row; headerIdx = i; break; }
            }
            if (header) {
              for (let i = headerIdx + 1; i < candidates.length; i++) {
                const r = _planToRow(candidates[i], header);
                if (r && r.material_name) rows.push(r);
              }
            } else if (candidates.length > 0) {
              for (const parts of candidates) {
                const r = _planFallbackRow(parts);
                if (r && r.material_name && r.quantity > 0) rows.push(r);
              }
            }
          }
        } else {
          Utils.showToast('PDF解析失败：' + (parseResult.error || '未知错误'), 'error');
        }
      } else if (ext === 'csv') {
        const parseResult = await window.electronAPI.parse.csvRead(filePath);
        if (parseResult.success && parseResult.data.length > 1) {
          const headers = parseResult.data[0];
          const hasHeader = PLAN_HEADER_ALIASES.material_name.some(a =>
            headers.some(h => h != null && String(h).replace(/\s+/g, '').includes(a))
          );
          const dataRows = parseResult.data.slice(1).filter(r => r && r.some(c => c != null && String(c).trim() !== ''));
          if (hasHeader) {
            for (const row of dataRows) {
              const r = _planToRow(row, headers);
              if (r && r.material_name) rows.push(r);
            }
          } else {
            for (const row of dataRows) {
              const r = _planFallbackRow(row);
              if (r && r.material_name) rows.push(r);
            }
          }
        }
      } else if (ext === 'docx') {
        Utils.showToast('Word文档解析中，请稍候...', 'warning');
        const parseResult = await window.electronAPI.parse.docxRead(filePath);
        if (parseResult && parseResult.success && parseResult.tables && parseResult.tables.length > 0) {
          // 遍历所有表格，选择包含物料识别词的表格
          for (const table of parseResult.tables) {
            if (!table || table.length < 2) continue;
            const headers = table[0] || [];
            const hasHeader = PLAN_HEADER_ALIASES.material_name.some(a =>
              headers.some(h => h != null && String(h).replace(/\s+/g, '').includes(a))
            );
            if (!hasHeader) continue;
            for (let i = 1; i < table.length; i++) {
              const r = _planToRow(table[i], headers);
              if (r && r.material_name) rows.push(r);
            }
          }
        } else if (parseResult && parseResult.success && parseResult.text) {
          // 退化为按行解析
          const lines = parseResult.text.split('\n').filter(l => l.trim());
          for (const line of lines) {
            const parts = line.split(/\s{2,}|\t|,|，/).map(p => p.trim()).filter(Boolean);
            if (parts.length >= 3) {
              const r = _planFallbackRow(parts);
              if (r && r.material_name && r.quantity > 0) rows.push(r);
            }
          }
        }
      } else {
        const parseResult = await window.electronAPI.parse.xlsxRead(filePath);
        if (parseResult.success) {
          // 遍历所有工作表
          const sheetEntries = Object.entries(parseResult.data);
          let usedSheet = '';
          for (const [sheetName, sheet] of sheetEntries) {
            if (!sheet || sheet.length < 2) continue;
            const headers = sheet[0] || [];
            const hasHeader = PLAN_HEADER_ALIASES.material_name.some(a =>
              headers.some(h => h != null && String(h).replace(/\s+/g, '').includes(a))
            );
            if (!hasHeader) continue;
            usedSheet = sheetName;
            for (let i = 1; i < sheet.length; i++) {
              const row = sheet[i];
              if (!row || row.every(c => c == null || String(c).trim() === '')) continue;
              const r = _planToRow(row, headers);
              if (r && r.material_name) rows.push(r);
            }
            if (rows.length > 0) break; // 找到第一个有效表即可
          }
          // 如果所有 sheet 都没识别到表头，尝试第一个 sheet 作为纯数据
          if (rows.length === 0 && sheetEntries.length > 0) {
            const [, firstSheet] = sheetEntries[0];
            if (firstSheet && firstSheet.length >= 1) {
              const dataRows = firstSheet.slice(firstSheet.length > 1 ? 1 : 0);
              for (const row of dataRows) {
                if (!row || row.every(c => c == null || String(c).trim() === '')) continue;
                const r = _planFallbackRow(row);
                if (r && r.material_name) rows.push(r);
              }
            }
          }
        }
      }
    } catch (err) {
      console.error('planImportFile error:', err);
      Utils.showToast('文件解析异常：' + (err.message || err), 'error');
    }

    // 过滤没有物料名称的行，并去重
    rows = rows.filter(r => r && r.material_name && r.material_name.toString().trim());

    if (rows.length > 0) {
      // 预处理：计算金额（如果没有）
      rows.forEach(r => {
        if (!r.amount || r.amount === 0) r.amount = (r.quantity || 0) * (r.unit_price || 0);
      });

      Modal.show('导入预览', `
        <div style="max-height:400px;overflow:auto">
          <table class="data-table">
            <thead><tr><th>审批编号</th><th>物料名称</th><th>规格</th><th>单位</th><th>数量</th><th>单价</th><th>金额</th><th>期望交付</th><th>操作</th></tr></thead>
            <tbody id="plan-preview-body">
              ${rows.map((r, i) => `
                <tr id="plan-preview-${i}" data-index="${i}">
                  <td>${Utils.escapeHtml(r.approval_no||'')}</td>
                  <td>${Utils.escapeHtml(r.material_name||'')}</td>
                  <td>${Utils.escapeHtml(r.spec||'')}</td>
                  <td>${Utils.escapeHtml(r.unit||'')}</td>
                  <td>${r.quantity}</td>
                  <td>${r.unit_price || ''}</td>
                  <td>${r.amount || ''}</td>
                  <td>${Utils.escapeHtml(r.expected_delivery||'')}</td>
                  <td><span class="cell-action"><span class="danger" onclick="document.getElementById('plan-preview-${i}').remove()">删除</span></span></td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
        <div style="margin-top:8px;font-size:12px;color:#6B7280">共 ${rows.length} 条记录，请确认后点击导入</div>
      `, `
        <button class="btn btn-secondary" onclick="Modal.hide()">取消</button>
        <button class="btn btn-primary" id="plan-import-confirm">确认导入</button>
      `);

      $('#plan-import-confirm').onclick = async () => {
        const remainingIndexes = [...document.querySelectorAll('#plan-preview-body tr')]
          .map(tr => parseInt(tr.dataset.index));
        const selectedRows = remainingIndexes.map(i => rows[i]).filter(Boolean);
        for (const r of selectedRows) {
          await window.electronAPI.db.savePlanRecord({
            approval_no: r.approval_no || '',
            material_name: r.material_name || '',
            spec: r.spec || '',
            unit: r.unit || '',
            quantity: parseFloat(r.quantity) || 0,
            unit_price: parseFloat(r.unit_price) || 0,
            amount: parseFloat(r.amount) || 0,
            expected_delivery: r.expected_delivery || '',
            remark: r.remark || '',
          });
        }
        Modal.hide();
        Utils.showToast(`导入 ${selectedRows.length} 条记录`);
        loadPlanData();
      };
    } else {
      Utils.showToast('未能解析到有效数据，请检查文件内容', 'warning');
    }
  }
}

// ── 下载计划导入模板 ──
async function planDownloadTemplate() {
  const result = await window.electronAPI.dialog.saveFile({
    filters: [{ name: 'Excel文件', extensions: ['xlsx'] }],
    defaultPath: '采购计划导入模板.xlsx',
  });
  if (result.canceled || !result.filePath) return;
  try {
    const r = await window.electronAPI.file.generatePlanTemplate({ filePath: result.filePath });
    if (r && r.success) Utils.showToast('模板已生成，请按模板填写后导入');
    else Utils.showToast('模板生成失败', 'error');
  } catch (e) {
    Utils.showToast('模板生成失败：' + (e.message || e), 'error');
  }
}
