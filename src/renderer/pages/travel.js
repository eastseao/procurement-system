/**
 * 差旅报销页面 - 对齐 V2.3.2
 * 按钮：查看归档/返回列表 + 新增差旅 + 导出Excel + 导入xlsx
 * 统计：出差次数/累计出差天数/报销总金额/未报销金额
 * 筛选：报销状态下拉 + 刷新
 * 表格：出发日期/出差事由/目的地/天数/出差人/交通摘要/住宿摘要/合计(¥)/报销/操作
 * 表单分节：🗺️ 基础信息 / 🚌 交通出行明细 / 🏨 酒店住宿明细 / 📝 备注
 */
let travelArchived = false;
let travelFilteredData = [];

async function loadTravelPage(container) {
  travelArchived = false;
  container.innerHTML = `
    <div class="page">
      <div class="page-header">
    
        <div style="display:flex;gap:8px">
          <button class="btn btn-secondary btn-sm" id="tvl-archive-btn" onclick="toggleTravelArchive()">📁 查看归档</button>
          <button class="btn btn-primary btn-sm" onclick="showTravelForm()">✚ 新增差旅</button>
          <button class="btn btn-secondary btn-sm" onclick="travelExport()">📥 导出Excel</button>
          <button class="btn btn-secondary btn-sm" onclick="travelImport()">📤 导入xlsx</button>
        </div>
      </div>
      <div class="page-body">
        <div class="stat-cards" id="tvl-stats"></div>
        <div class="search-bar">
          <label>报销状态</label>
          <select class="select" id="tvl-reimb-filter"><option value="">全部</option><option>未报销</option><option>已报销</option></select>
          <button class="btn btn-primary btn-sm" onclick="loadTravelData()">🔄 刷新</button>
        </div>
        <div class="table-container" id="tvl-table-container"></div>
      </div>
    </div>
  `;
  await loadTravelData();
}

async function loadTravelData() {
  const data = await window.electronAPI.db.getTravels(travelArchived ? 1 : 0);
  const reimbFilter = $('#tvl-reimb-filter')?.value || '';
  let filtered = data;
  if (reimbFilter) filtered = filtered.filter(t => t.reimbursement_status === reimbFilter);
  travelFilteredData = filtered;

  const totalAmount = filtered.reduce((s, t) => {
    const transTotal = (t.transports||[]).reduce((a, x) => a + (x.amount||0), 0);
    const hotelTotal = (t.hotels||[]).reduce((a, x) => a + (x.amount||0), 0);
    return s + transTotal + hotelTotal;
  }, 0);
  const totalDays = filtered.reduce((s, t) => s + (t.duration||0), 0);
  const unreimbursed = filtered.filter(t => t.reimbursement_status !== '已报销');
  const unreimbursedAmount = unreimbursed.reduce((s, t) => {
    const transTotal = (t.transports||[]).reduce((a, x) => a + (x.amount||0), 0);
    const hotelTotal = (t.hotels||[]).reduce((a, x) => a + (x.amount||0), 0);
    return s + transTotal + hotelTotal;
  }, 0);

  $('#tvl-stats').innerHTML = `
    <div class="stat-card"><div class="stat-value">${filtered.length}</div><div class="stat-label">出差次数</div></div>
    <div class="stat-card"><div class="stat-value">${totalDays}</div><div class="stat-label">累计出差天数</div></div>
    <div class="stat-card"><div class="stat-value">${Utils.formatMoney(totalAmount)}</div><div class="stat-label">报销总金额</div></div>
    <div class="stat-card"><div class="stat-value" style="color:var(--danger)">${Utils.formatMoney(unreimbursedAmount)}</div><div class="stat-label">未报销金额</div></div>
  `;

  $('#tvl-table-container').innerHTML = `
    <table class="data-table">
      <thead><tr>
        <th>出发日期</th><th>出差事由</th><th>目的地</th><th>天数</th><th>出差人</th>
        <th>交通摘要</th><th>住宿摘要</th><th>合计(¥)</th><th>报销</th><th>操作</th>
      </tr></thead>
      <tbody>
        ${filtered.map(t => {
          const transSummary = (t.transports||[]).map(x => `${x.transport_type} ${Utils.formatMoney(x.amount)}`).join('; ') || '—';
          const hotelSummary = (t.hotels||[]).map(x => `${x.checkin_date}~${x.checkout_date} ${Utils.formatMoney(x.amount)}`).join('; ') || '—';
          const total = (t.transports||[]).reduce((a,x)=>a+(x.amount||0),0) + (t.hotels||[]).reduce((a,x)=>a+(x.amount||0),0);
          return `
            <tr class="${travelArchived?'archived':''}">
              <td>${Utils.escapeHtml(t.start_date||'')}</td>
              <td>${Utils.escapeHtml((t.reason||'').slice(0,20))}</td>
              <td>${Utils.escapeHtml(t.destination||'')}</td>
              <td>${t.duration}</td>
              <td>${Utils.escapeHtml(t.handler||'')}</td>
              <td>${Utils.escapeHtml(transSummary.slice(0,30))}</td>
              <td>${Utils.escapeHtml(hotelSummary.slice(0,30))}</td>
              <td>${Utils.formatMoney(total)}</td>
              <td>${Utils.escapeHtml(t.reimbursement_status)}</td>
              <td class="cell-action">
                ${travelArchived?'':`<span onclick="showTravelForm(${t.id})">编辑</span><span onclick="archiveTravel(${t.id})">归档</span>`}
                <span class="danger" onclick="deleteTravel(${t.id})">删除</span>
              </td>
            </tr>
          `;
        }).join('')}
      </tbody>
    </table>
  `;
}

function toggleTravelArchive() {
  travelArchived = !travelArchived;
  $('#tvl-archive-btn').textContent = travelArchived ? '📋 返回列表' : '📁 查看归档';
  loadTravelData();
}

let travelTransportCount = 0;
let travelHotelCount = 0;

function showTravelForm(id = null) {
  travelTransportCount = 0;
  travelHotelCount = 0;
  Modal.show(id ? '编辑差旅' : '新增差旅', `
    <h4 style="margin-bottom:8px">🗺️ 基础信息</h4>
    <div class="form-row">
      <label>出差事由</label><input class="input" id="tf-purpose" style="width:200px">
      <label>目的地</label><input class="input" id="tf-dest" style="width:200px">
      <label>出差人</label><input class="input" id="tf-traveler" style="width:120px">
    </div>
    <div class="form-row">
      <label>出发日期</label><input class="input" id="tf-start" type="date" onchange="calcTravelDays()">
      <label>返回日期</label><input class="input" id="tf-end" type="date" onchange="calcTravelDays()">
      <label>天数</label><input class="input" id="tf-days" type="number" readonly style="width:60px">
      <label>报销</label><select class="select" id="tf-reimb"><option>未报销</option><option>已报销</option></select>
      <label>开票</label><select class="select" id="tf-invoice"><option>未开票</option><option>已开票</option></select>
    </div>
    <h4 style="margin:12px 0 8px">🚌 交通出行明细 <button class="btn btn-sm btn-secondary" onclick="addTravelTransportRow()">+添加行</button></h4>
    <div id="tf-transports"></div>
    <h4 style="margin:12px 0 8px">🏨 酒店住宿明细 <button class="btn btn-sm btn-secondary" onclick="addTravelHotelRow()">+添加行</button></h4>
    <div id="tf-hotels"></div>
    <h4 style="margin:12px 0 8px">📝 备注</h4>
    <div class="form-group"><textarea class="textarea" id="tf-remark" rows="2" style="width:100%"></textarea></div>
  `, `
    <button class="btn btn-secondary" onclick="Modal.hide()">取消</button>
    <button class="btn btn-primary" onclick="saveTravel(${id||'null'})">保存</button>
  `);

  if (id) {
    (async () => {
      const travels = await window.electronAPI.db.getTravels(0);
      const t = travels.find(x => x.id === id);
      if (t) {
        $('#tf-purpose').value = t.reason || '';
        $('#tf-dest').value = t.destination || '';
        $('#tf-traveler').value = t.handler || '';
        $('#tf-start').value = t.start_date || '';
        $('#tf-end').value = t.end_date || '';
        $('#tf-days').value = t.duration || '';
        $('#tf-reimb').value = t.reimbursement_status || '未报销';
        $('#tf-invoice').value = t.invoice_status || '未开票';
        $('#tf-remark').value = t.remark || '';
        if (t.transports) t.transports.forEach(tr => addTravelTransportRow(tr));
        if (t.hotels) t.hotels.forEach(h => addTravelHotelRow(h));
      }
    })();
  }
}

function calcTravelDays() {
  const s = $('#tf-start').value;
  const e = $('#tf-end').value;
  if (s && e) {
    const diff = (new Date(e) - new Date(s)) / 86400000 + 1;
    $('#tf-days').value = diff > 0 ? diff : 0;
  }
}

function addTravelTransportRow(data = null) {
  const idx = travelTransportCount++;
  const row = document.createElement('div');
  row.className = 'travel-row';
  row.id = `tvt-${idx}`;
  row.innerHTML = `
    <select class="select" style="height:28px;font-size:11px"><option>飞机</option><option>高铁</option><option>动车</option><option>火车</option><option>汽车</option><option>轮船</option><option>出租车</option><option>地铁</option><option>其他</option></select>
    <input class="input" type="date" value="${data?.travel_date||''}" style="width:130px">
    <input class="input" placeholder="出发地" value="${Utils.escapeHtml(data?.departure||'')}" style="width:80px">
    <input class="input" placeholder="目的地" value="${Utils.escapeHtml(data?.destination||'')}" style="width:80px">
    <input class="input" type="number" step="0.01" placeholder="金额" value="${data?.amount||''}" style="width:90px">
    <button class="btn btn-sm btn-danger" onclick="document.getElementById('tvt-${idx}').remove()">×</button>
  `;
  if (data) {
    const sel = row.querySelector('select');
    if (sel) sel.value = data.transport_type || '高铁';
  }
  $('#tf-transports')?.appendChild(row);
}

function addTravelHotelRow(data = null) {
  const idx = travelHotelCount++;
  const row = document.createElement('div');
  row.className = 'travel-row';
  row.id = `tvh-${idx}`;
  row.innerHTML = `
    <input class="input" type="date" value="${data?.checkin_date||''}" style="width:130px">
    <input class="input" type="date" value="${data?.checkout_date||''}" style="width:130px">
    <input class="input" type="number" placeholder="房间数" value="${data?.room_count||''}" style="width:70px">
    <input class="input" type="number" step="0.01" placeholder="金额" value="${data?.amount||''}" style="width:90px">
    <select class="select" style="height:28px;font-size:11px"><option>未开票</option><option>已开票</option></select>
    <button class="btn btn-sm btn-danger" onclick="document.getElementById('tvh-${idx}').remove()">×</button>
  `;
  if (data) {
    const sel = row.querySelectorAll('select')[0];
    if (sel) sel.value = data.invoice_status || '未开票';
  }
  $('#tf-hotels')?.appendChild(row);
}

async function saveTravel(id) {
  const data = {
    start_date: $('#tf-start').value,
    end_date: $('#tf-end').value,
    reason: $('#tf-purpose').value,
    destination: $('#tf-dest').value,
    handler: $('#tf-traveler').value,
    duration: parseInt($('#tf-days').value) || 0,
    reimbursement_status: $('#tf-reimb').value,
    invoice_status: $('#tf-invoice').value,
    remark: $('#tf-remark').value,
  };

  const transports = [];
  document.querySelectorAll('#tf-transports .travel-row').forEach(row => {
    const sel = row.querySelector('select');
    const inputs = row.querySelectorAll('input');
    transports.push({
      transport_type: sel ? sel.value : '高铁',
      travel_date: inputs[0].value, departure: inputs[1].value,
      destination: inputs[2].value, amount: parseFloat(inputs[3].value) || 0,
    });
  });

  const hotels = [];
  document.querySelectorAll('#tf-hotels .travel-row').forEach(row => {
    const inputs = row.querySelectorAll('input');
    const sel = row.querySelector('select');
    hotels.push({
      checkin_date: inputs[0].value, checkout_date: inputs[1].value,
      room_count: parseInt(inputs[2].value) || 0, amount: parseFloat(inputs[3].value) || 0,
      invoice_status: sel ? sel.value : '未开票',
    });
  });

  if (id) {
    await window.electronAPI.db.updateTravel(id, data, transports, hotels);
  } else {
    await window.electronAPI.db.saveTravel(data, transports, hotels);
  }
  Modal.hide();
  Utils.showToast('保存成功');
  loadTravelData();
  Utils.notifyDataChanged('travel');
}

async function archiveTravel(id) { await window.electronAPI.db.archiveTravel(id); Utils.showToast('已归档'); loadTravelData(); Utils.notifyDataChanged('travel'); }
async function deleteTravel(id) {
  const ok = await Utils.showConfirm('确认删除', '确定要删除该差旅记录吗？');
  if (ok) { await window.electronAPI.db.deleteTravel(id); Utils.showToast('删除成功'); loadTravelData(); Utils.notifyDataChanged('travel'); }
}
async function travelExport() {
  const today = new Date().toISOString().slice(0, 10);
  const result = await window.electronAPI.dialog.saveFile({
    filters: [{ name: 'Excel文件', extensions: ['xlsx'] }],
    defaultPath: `差旅明细_${today}.xlsx`,
  });
  if (!result.canceled && result.filePath) {
    const flat = travelFilteredData.map(t => {
      const transportSummary = (t.transports || []).map(x => `${x.transport_type} ${x.amount || ''}`).join('; ');
      const hotelSummary = (t.hotels || []).map(x => `${x.checkin_date || ''}~${x.checkout_date || ''} ${x.amount || ''}`).join('; ');
      return {
        start_date: t.start_date, reason: t.reason, destination: t.destination,
        duration: t.duration, handler: t.handler,
        transportSummary, hotelSummary,
        total_amount: (t.transports || []).reduce((s, x) => s + (x.amount || 0), 0) + (t.hotels || []).reduce((s, x) => s + (x.amount || 0), 0),
        reimbursement_status: t.reimbursement_status,
        invoice_status: t.invoice_status,
        remark: t.remark,
      };
    });
    const columnMap = {
      start_date: '出发日期', reason: '出差事由', destination: '目的地',
      duration: '天数', handler: '出差人',
      transportSummary: '交通摘要', hotelSummary: '住宿摘要',
      total_amount: '合计金额', reimbursement_status: '报销状态',
      invoice_status: '开票状态', remark: '备注',
    };
    await window.electronAPI.db.exportToXLSX('差旅明细', flat, result.filePath, columnMap);
    Utils.showToast('导出成功');
  }
}
async function travelImport() {
  const result = await window.electronAPI.dialog.openFile({ filters: [{ name: 'Excel文件', extensions: ['xlsx', 'xls'] }] });
  if (result.canceled) return;

  const filePath = result.filePaths?.[0];
  if (!filePath) return;

  try {
    Utils.showToast('正在解析文件...', 'info');
    const wb = await window.electronAPI.parse.xlsxRead(filePath);
    if (!wb || !wb.sheets || wb.sheets.length === 0) {
      Utils.showToast('文件中没有找到工作表', 'warning');
      return;
    }

    const sheet = wb.sheets[0];
    const rows = sheet.data; // [[row1], [row2], ...]
    if (!rows || rows.length < 2) {
      Utils.showToast('工作表数据不足', 'warning');
      return;
    }

    // ── Build header index (first non-empty row) ──
    const headerRow = rows.find(r => r && r.some(c => c != null && String(c).trim() !== '')) || rows[0];
    const colMap = {};
    headerRow.forEach((h, i) => {
      if (h == null) return;
      const v = String(h).trim();
      // Chinese headers → normalized field names
      const zhMap = {
        '事由': 'reason', '出差事由': 'reason',
        '出发日期': 'start_date', '开始日期': 'start_date',
        '返回日期': 'end_date', '结束日期': 'end_date',
        '出差人': 'handler', '出差人姓名': 'handler',
        '目的地': 'destination',
        '天数': 'duration',
        '报销状态': 'reimbursement_status',
        '开票状态': 'invoice_status', '发票状态': 'invoice_status',
        '出发地': 'departure',
        '金额': 'amount', '交通金额': 'transport_amount', '住宿金额': 'hotel_amount',
        '入住日期': 'checkin_date',
        '离店日期': 'checkout_date',
        '房间数': 'room_count',
        '交通类型': 'transport_type', '交通工具': 'transport_type',
        '交通日期': 'travel_date', '出行日期': 'travel_date',
      };
      // English headers → normalized field names
      const enMap = {
        'reason': 'reason',
        'start_date': 'start_date', 'start date': 'start_date',
        'end_date': 'end_date', 'end date': 'end_date',
        'handler': 'handler', 'traveler': 'handler',
        'destination': 'destination',
        'duration': 'duration',
        'reimbursement_status': 'reimbursement_status',
        'invoice_status': 'invoice_status',
        'departure': 'departure',
        'amount': 'amount',
        'checkin_date': 'checkin_date', 'checkin date': 'checkin_date',
        'checkout_date': 'checkout_date', 'checkout date': 'checkout_date',
        'rooms': 'room_count', 'room_count': 'room_count',
        'transport_type': 'transport_type',
        'travel_date': 'travel_date',
      };

      const key = zhMap[v] || enMap[v.toLowerCase()] || v;
      if (!colMap[key]) colMap[key] = i; // first occurrence wins
    });

    // Helper: read cell value by normalized field name
    const cell = (row, field) => {
      const idx = colMap[field];
      return idx !== undefined && row ? (row[idx] != null ? String(row[idx]).trim() : '') : '';
    };
    const cellNum = (row, field) => parseFloat(cell(row, field)) || 0;
    const cellInt = (row, field) => parseInt(cell(row, field)) || 0;

    // ── Detect row type ──
    // Transport row: has transport_type column OR value looks like a transport keyword
    const TRANSPORT_KEYWORDS = ['高铁', '动车', '火车', '飞机', '自驾', '汽车', '轮船', '出租车', '地铁', '飞机/高铁', '其他'];
    const isTransportRow = (row) => {
      if (colMap['transport_type'] !== undefined) {
        const v = cell(row, 'transport_type');
        return v !== '' && (TRANSPORT_KEYWORDS.includes(v) || /交通|transport/i.test(v));
      }
      // Fallback: if row has travel_date/departure/destination but no reason/checkin
      const hasTravelDate = cell(row, 'travel_date') !== '';
      const hasDeparture = cell(row, 'departure') !== '';
      const hasAmount = cell(row, 'amount') !== '';
      return hasTravelDate && hasDeparture && hasAmount && cell(row, 'reason') === '' && cell(row, 'checkin_date') === '';
    };

    // Hotel row: has checkin_date column with value
    const isHotelRow = (row) => {
      return cell(row, 'checkin_date') !== '' && cell(row, 'reason') === '' && colMap['transport_type'] === undefined || (cell(row, 'checkin_date') !== '' && cell(row, 'checkin_date') !== '');
    };

    // Travel group header: has reason/事由
    const isTravelGroupRow = (row) => {
      return cell(row, 'reason') !== '';
    };

    // ── Group rows ──
    const dataRows = rows.slice(rows.indexOf(headerRow) + 1);
    const groups = []; // { travelData, transports, hotels }
    let currentGroup = null;

    for (const row of dataRows) {
      if (!row || row.every(c => c == null || String(c).trim() === '')) continue; // skip blank

      if (isTravelGroupRow(row)) {
        // Save previous group
        if (currentGroup) groups.push(currentGroup);

        const startVal = cell(row, 'start_date');
        const endVal = cell(row, 'end_date');
        let duration = cellInt(row, 'duration');
        if (!duration && startVal && endVal) {
          const diff = Math.round((new Date(endVal) - new Date(startVal)) / 86400000) + 1;
          duration = diff > 0 ? diff : 0;
        }

        currentGroup = {
          travelData: {
            reason: cell(row, 'reason'),
            destination: cell(row, 'destination'),
            start_date: startVal,
            end_date: endVal,
            duration: duration,
            handler: cell(row, 'handler'),
            invoice_status: cell(row, 'invoice_status') || '未开票',
            reimbursement_status: cell(row, 'reimbursement_status') || '未报销',
          },
          transports: [],
          hotels: [],
        };
      } else if (isHotelRow(row) && currentGroup) {
        // Refined check: checkin_date present AND no reason
        const checkinVal = cell(row, 'checkin_date');
        const reasonVal = cell(row, 'reason');
        if (checkinVal && !reasonVal) {
          currentGroup.hotels.push({
            checkin_date: checkinVal,
            checkout_date: cell(row, 'checkout_date'),
            room_count: cellInt(row, 'room_count') || 1,
            amount: cellNum(row, 'amount'),
            invoice_status: cell(row, 'invoice_status') || '未开票',
          });
        }
      } else if (isTransportRow(row) && currentGroup) {
        const typeVal = cell(row, 'transport_type');
        if (typeVal || cell(row, 'travel_date') || cell(row, 'departure')) {
          currentGroup.transports.push({
            transport_type: typeVal || '其他',
            travel_date: cell(row, 'travel_date') || currentGroup.travelData.start_date,
            departure: cell(row, 'departure'),
            destination: cell(row, 'destination') || currentGroup.travelData.destination,
            amount: cellNum(row, 'amount'),
          });
        }
      }
    }
    if (currentGroup) groups.push(currentGroup);

    if (groups.length === 0) {
      Utils.showToast('未识别到有效差旅记录，请检查表格格式', 'warning');
      return;
    }

    // ── Save each group ──
    let saved = 0;
    for (const g of groups) {
      try {
        await window.electronAPI.db.saveTravel(g.travelData, g.transports, g.hotels);
        saved++;
      } catch (err) {
        console.error('导入差旅记录失败:', err, g);
      }
    }

    Utils.showToast(`成功导入 ${saved} 条差旅记录（含 ${groups.reduce((s,g) => s+g.transports.length, 0)} 条交通、${groups.reduce((s,g) => s+g.hotels.length, 0)} 条住宿）`);
    loadTravelData();
    Utils.notifyDataChanged('travel');
  } catch (err) {
    console.error('travelImport error:', err);
    Utils.showToast('导入失败：' + (err.message || err), 'error');
  }
}
