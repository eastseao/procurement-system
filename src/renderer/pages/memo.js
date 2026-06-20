/**
 * 备忘录页面 - 对齐 V2.3.2
 * 按钮：新增备忘/导出Excel
 * 筛选：项目下拉/状态下拉/模糊搜索/查询/重置
 * 表格：日期/项目归属/经手人/具体内容/时间节点/状态/备注/操作
 * 操作列：编辑/完成/删除（3部分）
 */
let memoData = [];

async function loadMemoPage(container) {
  container.innerHTML = `
    <div class="page">
      <div class="page-header">
    
        <div style="display:flex;gap:8px">
          <button class="btn btn-primary btn-sm" onclick="showMemoForm()">✚ 新增备忘</button>
          <button class="btn btn-secondary btn-sm" onclick="memoExport()">📥 导出Excel</button>
        </div>
      </div>
      <div class="page-body">
        <div class="search-bar">
          <label>项目</label>
          <select class="select" id="memo-project"><option value="">全部</option></select>
          <label>状态</label>
          <select class="select" id="memo-status"><option value="">全部</option><option>待处理</option><option>处理中</option><option>已完成</option></select>
          <label>模糊搜索</label>
          <input class="input" id="memo-keyword" placeholder="内容/经手人/备注" style="width:160px">
          <button class="btn btn-primary btn-sm" onclick="loadMemoData()">查询</button>
          <button class="btn btn-secondary btn-sm" onclick="document.getElementById('memo-project').value='';document.getElementById('memo-status').value='';document.getElementById('memo-keyword').value='';loadMemoData()">重置</button>
        </div>
        <div class="stats-bar"><span class="stats-label" id="memo-stats"></span></div>
        <div class="table-container" id="memo-table-container"></div>
      </div>
    </div>
  `;
  await loadMemoData();
}

async function loadMemoData() {
  const keyword = $('#memo-keyword')?.value || '';
  const project = $('#memo-project')?.value || '';
  const status = $('#memo-status')?.value || '';
  const data = await window.electronAPI.db.getMemos(keyword, project, status);
  memoData = data;
  $('#memo-stats').innerHTML = `共 <strong>${data.length}</strong> 条备忘`;

  // 加载项目
  const projects = await window.electronAPI.db.getProjects();
  const sel = $('#memo-project');
  if (sel && sel.children.length <= 1) {
    sel.innerHTML = '<option value="">全部</option>' + projects.map(p => `<option>${Utils.escapeHtml(p)}</option>`).join('');
  }

  $('#memo-table-container').innerHTML = `
    <table class="data-table">
      <thead><tr>
        <th>日期</th><th>项目归属</th><th>经手人</th><th>具体内容</th><th>时间节点</th>
        <th>状态</th><th>备注</th><th>操作</th>
      </tr></thead>
      <tbody>
        ${data.map(m => `
          <tr>
            <td>${Utils.escapeHtml(m.date||'')}</td>
            <td>${Utils.escapeHtml(m.project||'')}</td>
            <td>${Utils.escapeHtml(m.handler||'')}</td>
            <td>${Utils.escapeHtml((m.content||'').slice(0,40))}</td>
            <td>${Utils.escapeHtml(m.deadline||'')}</td>
            <td><span class="status-badge ${m.status==='已完成'?'completed':m.status==='处理中'?'processing':'pending'}">${m.status}</span></td>
            <td>${Utils.escapeHtml((m.remark||'').slice(0,20))}</td>
            <td class="cell-action">
              <span onclick="showMemoForm(${m.id})">编辑</span>
              <span onclick="toggleMemoStatus(${m.id},'${m.status}')">${m.status==='已完成'?'撤销':'完成'}</span>
              <span class="danger" onclick="deleteMemo(${m.id})">删除</span>
            </td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
}

function showMemoForm(id = null) {
  Modal.show(id ? '编辑备忘' : '新增备忘', `
    <h4 style="margin-bottom:8px">📋 基本信息</h4>
    <div class="supplier-form-grid">
      <div class="form-group"><label>日期</label><input class="input" id="mf-date" type="date" style="width:100%"></div>
      <div class="form-group"><label>项目归属</label><select class="select" id="mf-project" style="width:100%"></select></div>
      <div class="form-group"><label>经手人</label><input class="input" id="mf-handler" style="width:100%"></div>
    </div>
    <h4 style="margin:12px 0 8px">📝 内容</h4>
    <div class="form-group"><label>具体内容</label><textarea class="textarea" id="mf-content" rows="3" style="width:100%"></textarea></div>
    <h4 style="margin:12px 0 8px">⏰ 时间与状态</h4>
    <div class="supplier-form-grid">
      <div class="form-group"><label>时间节点</label><input class="input" id="mf-deadline" style="width:100%"></div>
      <div class="form-group"><label>状态</label><select class="select" id="mf-status" style="width:100%"><option>待处理</option><option>处理中</option><option>已完成</option></select></div>
    </div>
    <h4 style="margin:12px 0 8px">📝 备注</h4>
    <div class="form-group"><label>备注</label><textarea class="textarea" id="mf-remark" rows="2" style="width:100%"></textarea></div>
  `, `
    <button class="btn btn-secondary" onclick="Modal.hide()">取消</button>
    <button class="btn btn-primary" onclick="saveMemo(${id||'null'})">保存</button>
  `);

  (async () => {
    const projects = await window.electronAPI.db.getProjects();
    const sel = $('#mf-project');
    if (sel) sel.innerHTML = projects.map(p => `<option>${Utils.escapeHtml(p)}</option>`).join('');
  })();

  if (id) {
    (async () => {
      const m = await window.electronAPI.db.getMemo(id);
      if (m) {
        $('#mf-date').value = m.date || '';
        $('#mf-handler').value = m.handler || '';
        $('#mf-content').value = m.content || '';
        $('#mf-deadline').value = m.deadline || '';
        $('#mf-status').value = m.status || '待处理';
        $('#mf-remark').value = m.remark || '';
        setTimeout(() => { $('#mf-project').value = m.project || ''; }, 100);
      }
    })();
  }
}

async function saveMemo(id) {
  const data = {
    date: $('#mf-date').value,
    project: $('#mf-project').value,
    handler: $('#mf-handler').value,
    content: $('#mf-content').value,
    deadline: $('#mf-deadline').value,
    status: $('#mf-status').value || '待处理',
    remark: $('#mf-remark').value,
  };
  if (id) {
    await window.electronAPI.db.updateMemo(id, data);
  } else {
    await window.electronAPI.db.saveMemo(data);
  }
  Modal.hide();
  Utils.showToast('保存成功');
  loadMemoData();
  Utils.notifyDataChanged('memo');
}

async function toggleMemoStatus(id, currentStatus) {
  const newStatus = currentStatus === '已完成' ? '待处理' : '已完成';
  const m = await window.electronAPI.db.getMemo(id);
  if (m) {
    m.status = newStatus;
    await window.electronAPI.db.updateMemo(id, m);
    Utils.showToast(newStatus === '已完成' ? '已标记完成' : '已撤销完成');
    loadMemoData();
    Utils.notifyDataChanged('memo');
  }
}

async function deleteMemo(id) {
  const ok = await Utils.showConfirm('确认删除', '确定要删除该备忘吗？');
  if (ok) {
    await window.electronAPI.db.deleteMemo(id);
    Utils.showToast('删除成功');
    loadMemoData();
    Utils.notifyDataChanged('memo');
  }
}

async function memoExport() {
  const result = await window.electronAPI.dialog.saveFile({ filters: [{ name: 'Excel文件', extensions: ['xlsx'] }] });
  if (!result.canceled && result.filePath) {
    await window.electronAPI.db.exportToXLSX('memos', memoData, result.filePath);
    Utils.showToast('导出成功');
  }
}
