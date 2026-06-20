/**
 * 看板页面 - KPI 指标 + 三列动态展示（对齐 V2.3.2）
 */
let _dashboardTimer = null;

// ══════════════════════════════════════════════════
// 万年历相关
// ══════════════════════════════════════════════════
const _gan = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸'];
const _zhi = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥'];
const _shengxiao = ['鼠','牛','虎','兔','龙','蛇','马','羊','猴','鸡','狗','猪'];
const _lunarMonths = ['正','二','三','四','五','六','七','八','九','十','冬','腊'];
const _lunarDays = ['初一','初二','初三','初四','初五','初六','初七','初八','初九','初十',
  '十一','十二','十三','十四','十五','十六','十七','十八','十九','二十',
  '廿一','廿二','廿三','廿四','廿五','廿六','廿七','廿八','廿九','三十'];

// 农历数据（1900-2100）
const _lunarInfo = [
  0x04bd8,0x04ae0,0x0a570,0x054d5,0x0d260,0x0d950,0x16554,0x056a0,0x09ad0,0x055d2,
  0x04ae0,0x0a5b6,0x0a4d0,0x0d250,0x1d255,0x0b540,0x0d6a0,0x0ada2,0x095b0,0x14977,
  0x04970,0x0a4b0,0x0b4b5,0x06a50,0x06d40,0x1ab54,0x02b60,0x09570,0x052f2,0x04970,
  0x06566,0x0d4a0,0x0ea50,0x06e95,0x05ad0,0x02b60,0x186e3,0x092e0,0x1c8d7,0x0c950,
  0x0d4a0,0x1d8a6,0x0b550,0x056a0,0x1a5b4,0x025d0,0x092d0,0x0d2b2,0x0a950,0x0b557,
  0x06ca0,0x0b550,0x15355,0x04da0,0x0a5b0,0x14573,0x052b0,0x0a9a8,0x0e950,0x06aa0,
  0x0aea6,0x0ab50,0x04b60,0x0aae4,0x0a570,0x05260,0x0f263,0x0d950,0x05b57,0x056a0,
  0x096d0,0x04dd5,0x04ad0,0x0a4d0,0x0d4d4,0x0d250,0x0d558,0x0b540,0x0b6a0,0x195a6,
  0x095b0,0x049b0,0x0a974,0x0a4b0,0x0b27a,0x06a50,0x06d40,0x0af46,0x0ab60,0x09570,
  0x04af5,0x04970,0x064b0,0x074a3,0x0ea50,0x06b58,0x055c0,0x0ab60,0x096d5,0x092e0,
  0x0c960,0x0d954,0x0d4a0,0x0da50,0x07552,0x056a0,0x0abb7,0x025d0,0x092d0,0x0cab5,
  0x0a950,0x0b4a0,0x0baa4,0x0ad50,0x055d9,0x04ba0,0x0a5b0,0x15176,0x052b0,0x0a930,
  0x07954,0x06aa0,0x0ad50,0x05b52,0x04b60,0x0a6e6,0x0a4e0,0x0d260,0x0ea65,0x0d530,
  0x05aa0,0x076a3,0x096d0,0x04afb,0x04ad0,0x0a4d0,0x1d0b6,0x0d250,0x0d520,0x0dd45,
  0x0b5a0,0x056d0,0x055b2,0x049b0,0x0a577,0x0a4b0,0x0aa50,0x1b255,0x06d20,0x0ada0,
  0x14b63,0x09370,0x049f8,0x04970,0x064b0,0x168a6,0x0ea50,0x06b20,0x1a6c4,0x0aae0,
  0x0a2e0,0x0d2e3,0x0c960,0x0d557,0x0d4a0,0x0da50,0x05d55,0x056a0,0x0a6d0,0x055d4,
  0x052d0,0x0a9b8,0x0a950,0x0b4a0,0x0b6a6,0x0ad50,0x055a0,0x0aba4,0x0a5b0,0x052b0,
  0x0b273,0x06930,0x07337,0x06aa0,0x0ad50,0x14b55,0x04b60,0x0a570,0x054e4,0x0d160,
  0x0e968,0x0d520,0x0daa0,0x16aa6,0x056d0,0x04ae0,0x0a9d4,0x0a2d0,0x0d150,0x0f252,
  0x0d520
];

// ══════════════════════════════════════════════
// 24 节气（按年存储精确日期，格式: MM-DD）
// ══════════════════════════════════════════════
const _solarTerms = {
  2024: ['01-05','01-20','02-04','02-19','03-05','03-20','04-04','04-19',
         '05-05','05-21','06-05','06-21','07-06','07-22','08-07','08-22',
         '09-07','09-22','10-08','10-23','11-06','11-22','12-06','12-21'],
  2025: ['01-05','01-20','02-03','02-18','03-05','03-21','04-04','04-20',
         '05-05','05-21','06-05','06-21','07-07','07-23','08-07','08-23',
         '09-07','09-23','10-08','10-23','11-07','11-22','12-07','12-22'],
  2026: ['01-05','01-20','02-04','02-19','03-06','03-21','04-05','04-20',
         '05-05','05-21','06-06','06-21','07-07','07-23','08-07','08-23',
         '09-08','09-23','10-08','10-24','11-07','11-22','12-07','12-22'],
  2027: ['01-05','01-20','02-04','02-19','03-06','03-21','04-05','04-20',
         '05-06','05-21','06-06','06-21','07-07','07-23','08-08','08-23',
         '09-08','09-23','10-08','10-24','11-07','11-22','12-07','12-22'],
};
const _solarTermNames = [
  '小寒','大寒','立春','雨水','惊蛰','春分','清明','谷雨',
  '立夏','小满','芒种','夏至','小暑','大暑','立秋','处暑',
  '白露','秋分','寒露','霜降','立冬','小雪','大雪','冬至'
];

// ══════════════════════════════════════════════
// 农历节日表
// ══════════════════════════════════════════════
const _lunarFestivals = {
  '1-1':   '春节',
  '1-15':  '元宵节',
  '2-2':   '龙抬头',
  '5-5':   '端午节',
  '7-7':   '七夕节',
  '7-15':  '中元节',
  '8-15':  '中秋节',
  '9-9':   '重阳节',
  '12-8':  '腊八节',
  '12-23': '小年',
};

// ══════════════════════════════════════════════
// 公历节日表（每年固定）
// ══════════════════════════════════════════════
const _solarFestivals = {
  '1-1':   '元旦',
  '2-14':  '情人节',
  '3-8':   '妇女节',
  '3-12':  '植树节',
  '5-1':   '劳动节',
  '5-4':   '青年节',
  '6-1':   '儿童节',
  '7-1':   '建党节',
  '8-1':   '建军节',
  '9-10':  '教师节',
  '10-1':  '国庆节',
  '12-25': '圣诞节',
};

// ══════════════════════════════════════════════
// 国家法定节假日（含调休）— 2024 ~ 2027
// 格式: { 'YYYY-MM-DD': '节日名称', ... }
// ══════════════════════════════════════════════
const _statutoryHolidays = {
  // ─── 2025 ───
  '2025-01-01': '元旦',
  '2025-01-28': '春节',
  '2025-01-29': '春节',
  '2025-01-30': '春节',
  '2025-01-31': '春节',
  '2025-02-01': '春节',
  '2025-02-02': '春节',
  '2025-02-03': '春节',
  '2025-02-04': '春节',
  '2025-04-04': '清明',
  '2025-04-05': '清明',
  '2025-04-06': '清明',
  '2025-05-01': '劳动节',
  '2025-05-02': '劳动节',
  '2025-05-03': '劳动节',
  '2025-05-04': '劳动节',
  '2025-05-05': '劳动节',
  '2025-06-10': '端午',
  '2025-06-11': '端午',
  '2025-06-12': '端午',
  '2025-10-01': '国庆',
  '2025-10-02': '国庆',
  '2025-10-03': '国庆',
  '2025-10-04': '国庆',
  '2025-10-05': '国庆',
  '2025-10-06': '国庆',
  '2025-10-07': '国庆',
  '2025-10-08': '国庆',
  // ─── 2026 ───
  '2026-01-01': '元旦',
  '2026-02-16': '春节',
  '2026-02-17': '春节',
  '2026-02-18': '春节',
  '2026-02-19': '春节',
  '2026-02-20': '春节',
  '2026-02-21': '春节',
  '2026-02-22': '春节',
  '2026-02-23': '春节',
  '2026-04-04': '清明',
  '2026-04-05': '清明',
  '2026-04-06': '清明',
  '2026-05-01': '劳动节',
  '2026-05-02': '劳动节',
  '2026-05-03': '劳动节',
  '2026-05-04': '劳动节',
  '2026-05-05': '劳动节',
  '2026-06-18': '端午',
  '2026-06-19': '端午',
  '2026-06-20': '端午',
  '2026-09-24': '中秋',
  '2026-09-25': '中秋',
  '2026-09-26': '中秋',
  '2026-10-01': '国庆',
  '2026-10-02': '国庆',
  '2026-10-03': '国庆',
  '2026-10-04': '国庆',
  '2026-10-05': '国庆',
  '2026-10-06': '国庆',
  '2026-10-07': '国庆',
  // ─── 2027 ───
  '2027-01-01': '元旦',
  '2027-02-06': '春节',
  '2027-02-07': '春节',
  '2027-02-08': '春节',
  '2027-02-09': '春节',
  '2027-02-10': '春节',
  '2027-02-11': '春节',
  '2027-02-12': '春节',
  '2027-02-13': '春节',
  '2027-02-14': '春节',
  '2027-04-03': '清明',
  '2027-04-04': '清明',
  '2027-04-05': '清明',
  '2027-05-01': '劳动节',
  '2027-05-02': '劳动节',
  '2027-05-03': '劳动节',
  '2027-05-04': '劳动节',
  '2027-05-05': '劳动节',
  '2027-06-09': '端午',
  '2027-06-10': '端午',
  '2027-06-11': '端午',
  '2027-09-15': '中秋',
  '2027-09-16': '中秋',
  '2027-09-17': '中秋',
  '2027-10-01': '国庆',
  '2027-10-02': '国庆',
  '2027-10-03': '国庆',
  '2027-10-04': '国庆',
  '2027-10-05': '国庆',
  '2027-10-06': '国庆',
  '2027-10-07': '国庆',
  '2027-10-08': '国庆',
};

function _pad(n) { return n < 10 ? '0' + n : '' + n; }

function _lYearDays(y) {
  let sum = 348;
  for (let i = 0x8000; i > 0x8; i >>= 1) sum += (_lunarInfo[y - 1900] & i) ? 1 : 0;
  return sum + _leapDays(y);
}
function _leapMonth(y) { return _lunarInfo[y - 1900] & 0xf; }
function _leapDays(y) {
  if (_leapMonth(y)) return (_lunarInfo[y - 1900] & 0x10000) ? 30 : 29;
  return 0;
}
function _monthDays(y, m) {
  return (_lunarInfo[y - 1900] & (0x10000 >> m)) ? 30 : 29;
}
function solarToLunar(date) {
  let y = date.getFullYear(), m = date.getMonth() + 1, d = date.getDate();
  const baseDate = new Date(1900, 0, 31);
  let offset = Math.floor((date - baseDate) / 86400000);

  let lunarYear = 1900, daysInYear = 0;
  while (lunarYear < 2101 && offset > 0) {
    daysInYear = _lYearDays(lunarYear);
    if (offset < daysInYear) break;
    offset -= daysInYear;
    lunarYear++;
  }

  const leap = _leapMonth(lunarYear);
  let isLeap = false;
  let lunarMonth = 1, daysInMonth = 0;
  while (lunarMonth < 13 && offset > 0) {
    if (leap > 0 && lunarMonth === leap + 1 && !isLeap) {
      --lunarMonth;
      isLeap = true;
      daysInMonth = _leapDays(lunarYear);
    } else {
      daysInMonth = _monthDays(lunarYear, lunarMonth);
    }
    if (isLeap && lunarMonth === leap + 1) isLeap = false;
    if (offset < daysInMonth) break;
    offset -= daysInMonth;
    lunarMonth++;
  }
  const lunarDay = offset + 1;

  // 干支纪年
  const ganZhiYear = _gan[(lunarYear - 4) % 10] + _zhi[(lunarYear - 4) % 12];
  const shengxiao = _shengxiao[(lunarYear - 4) % 12];

  return {
    year: lunarYear,
    month: lunarMonth,
    day: lunarDay,
    monthName: (isLeap ? '闰' : '') + _lunarMonths[lunarMonth - 1] + '月',
    dayName: _lunarDays[lunarDay - 1],
    ganZhi: ganZhiYear,
    shengxiao: shengxiao
  };
}

// 黄历宜忌（简化版：基于日期取模）
const _yiList = ['祭祀','祈福','求嗣','开光','出行','解除','订婚','纳采','嫁娶',
  '移徙','入宅','安床','开市','交易','立券','纳财','开仓','栽种','纳畜','牧养',
  '修造','动土','上梁','安门','修厨','作灶','会亲友','出行','赴任','见贵'];
const _jiList = ['诸事不宜','开市','嫁娶','安葬','动土','修造','入宅','安门',
  '上梁','开仓','出行','移徙','纳采','入殓','破土','作灶','伐木','栽种',
  '嫁娶','词讼','伐木','作灶','安葬','开市','交易','纳财','出货'];

function getHuangLi(date) {
  const seed = date.getFullYear() * 10000 + (date.getMonth() + 1) * 100 + date.getDate();
  const yi = [_yiList[seed % _yiList.length], _yiList[(seed + 7) % _yiList.length], _yiList[(seed + 13) % _yiList.length]];
  const ji = [_jiList[seed % _jiList.length], _jiList[(seed + 3) % _jiList.length]];
  return { yi: yi.join(' '), ji: ji.join(' ') };
}

// ══════════════════════════════════════════════
// 获取指定公历日期的日历标签（节气/节日/节假日/农历日）
// 返回: { text: string, type: 'festival'|'term'|'holiday'|'lunar'|'' }
// ══════════════════════════════════════════════
function getCellLabel(year, month, day) {
  const mmdd = _pad(month) + '-' + _pad(day);
  const ymd = year + '-' + mmdd;

  // 1. 国家法定节假日（最高优先级，红色）
  if (_statutoryHolidays[ymd]) {
    return { text: _statutoryHolidays[ymd], type: 'holiday' };
  }

  // 2. 公历节日
  const solarKey = month + '-' + day;
  if (_solarFestivals[solarKey]) {
    return { text: _solarFestivals[solarKey], type: 'festival' };
  }

  // 3. 农历节日
  const dateObj = new Date(year, month - 1, day);
  const lunar = solarToLunar(dateObj);
  const lunarKey = lunar.month + '-' + lunar.day;
  if (_lunarFestivals[lunarKey]) {
    return { text: _lunarFestivals[lunarKey], type: 'festival' };
  }
  // 除夕特殊处理：农历当年最后一天 (非闰月 12-30，若腊月只有29天则 12-29)
  if (lunar.month === 12) {
    const lastLunarDay = _monthDays(lunar.year, 12);
    if (lunar.day === lastLunarDay) {
      return { text: '除夕', type: 'festival' };
    }
  }

  // 4. 节气
  const termArr = _solarTerms[year];
  if (termArr) {
    for (let i = 0; i < termArr.length; i++) {
      if (termArr[i] === mmdd) {
        return { text: _solarTermNames[i], type: 'term' };
      }
    }
  }

  // 5. 默认显示农历日（初一、十五等农历日名）
  return { text: lunar.dayName, type: 'lunar' };
}

function renderCalendar() {
  const now = new Date();
  const weekNames = ['星期日','星期一','星期二','星期三','星期四','星期五','星期六'];
  const lunar = solarToLunar(now);
  const hl = getHuangLi(now);

  // 月历视图
  const y = now.getFullYear(), m = now.getMonth();
  const firstDay = new Date(y, m, 1);
  const lastDay = new Date(y, m + 1, 0);
  const startWeekday = firstDay.getDay();
  const totalDays = lastDay.getDate();
  const today = now.getDate();

  let cells = '';
  // 星期头部
  ['日','一','二','三','四','五','六'].forEach((w, idx) => {
    const cls = (idx === 0 || idx === 6) ? 'cal-weekend' : '';
    cells += `<div class="cal-hcell ${cls}">${w}</div>`;
  });
  // 前面空格
  for (let i = 0; i < startWeekday; i++) cells += `<div class="cal-cell"></div>`;
  // 日期
  for (let d = 1; d <= totalDays; d++) {
    const wd = new Date(y, m, d).getDay();
    const isToday = d === today;
    const wCls = (wd === 0 || wd === 6) ? 'cal-cell-weekend' : '';
    const tCls = isToday ? 'cal-cell-today' : '';
    const label = getCellLabel(y, m + 1, d);
    const lCls = label.type ? 'cal-label cal-label-' + label.type : 'cal-label';
    cells += `<div class="cal-cell ${wCls} ${tCls}"><div class="cal-num">${d}</div><div class="${lCls}">${label.text}</div></div>`;
  }

  return `
    <div class="calendar-widget">
      <div class="cal-left">
        <div class="cal-date-block">
          <div class="cal-month">${y}年${m + 1}月</div>
          <div class="cal-day">${today}</div>
          <div class="cal-week">${weekNames[now.getDay()]}</div>
        </div>
        <div class="cal-lunar-row">
          <span class="cal-ganzhi">${lunar.ganZhi}年</span>
          <span class="cal-shengxiao">【${lunar.shengxiao}】</span>
          <span class="cal-lunar-date">${lunar.monthName}${lunar.dayName}</span>
        </div>
        <div class="cal-huangli-block">
          <div class="cal-yi"><span class="cal-tag-yi">宜</span><span class="cal-hl-text">${hl.yi}</span></div>
          <div class="cal-ji"><span class="cal-tag-ji">忌</span><span class="cal-hl-text">${hl.ji}</span></div>
        </div>
      </div>
      <div class="cal-mini-grid">
        ${cells}
      </div>
    </div>
  `;
}

async function loadDashboardPage(container) {
  // 首次被调用时传入 DOM 节点，后续下拉刷新也能触发重新加载
  if (typeof container === 'string') {
    container = document.getElementById(container) || document.querySelector(container);
  }
  if (container) {
    window.__dashboardContainer__ = container;
    container.innerHTML = `
      <div class="page">
        <div class="page-body">
          <div class="dashboard-kpi-row" id="dashboard-kpi-row"></div>
          <div class="dashboard-grid" id="dashboard-grid"></div>
        </div>
      </div>
    `;
  }

  await refreshDashboard();

  // 自动刷新：每5分钟
  if (_dashboardTimer) clearInterval(_dashboardTimer);
  _dashboardTimer = setInterval(refreshDashboard, 5 * 60 * 1000);

  // 监听全局数据变更事件，实现看板实时更新
  // 当其他页面进行增删改操作后会派发 dataChanged 事件
  window.addEventListener('dataChanged', _onDataChanged);
}

// 数据变更的防抖处理：避免频繁刷新
let _dataChangeTimer = null;
function _onDataChanged(e) {
  // 如果当前不在看板页面，记录一次脏标记即可，下次进入时重新加载
  if (AppState.currentPage !== 'dashboard') return;
  if (_dataChangeTimer) clearTimeout(_dataChangeTimer);
  _dataChangeTimer = setTimeout(() => {
    refreshDashboard();
  }, 500);
}

async function refreshDashboard() {
  try {
    // 并行加载所有数据
    const [packagingOrders, planRecords, purchases, travels, collections, suppliers] = await Promise.all([
      window.electronAPI.db.getPackagingOrders({}),
      window.electronAPI.db.getPlanRecords(0),
      window.electronAPI.db.getPurchases(0),
      window.electronAPI.db.getTravels(0),
      window.electronAPI.db.getCollections(''),
      window.electronAPI.db.getSuppliers('', '', ''),
    ]);

    // 计算 KPI（对齐 V2.3.2：排除已报销记录）
    const totalOrders = packagingOrders.length;
    const totalCollections = collections.length;
    // 采购垫付：排除 reimbursement_status === '已报销'
    const totalPurchaseAmount = purchases
      .filter(p => p.reimbursement_status !== '已报销')
      .reduce((s, p) => s + (p.items||[]).reduce((a, i) => a + (i.total||0), 0), 0);
    // 差旅报销：排除 reimbursement_status === '已报销'
    const totalTravelAmount = travels
      .filter(t => t.reimbursement_status !== '已报销')
      .reduce((s, t) => {
        const transTotal = (t.transports||[]).reduce((a, x) => a + (x.amount||0), 0);
        const hotelTotal = (t.hotels||[]).reduce((a, x) => a + (x.amount||0), 0);
        return s + transTotal + hotelTotal;
      }, 0);

    $('#dashboard-kpi-row').innerHTML = `
      <div class="dashboard-kpi-card" onclick="switchPage('packaging')">
        <div class="kpi-title">📦 物料下单</div>
        <div class="kpi-value">${totalOrders}</div>
        <div class="kpi-subtitle">包材下单总数</div>
      </div>
      <div class="dashboard-kpi-card" onclick="switchPage('collection')">
        <div class="kpi-title">💰 催款记录</div>
        <div class="kpi-value" style="color:var(--warning)">${totalCollections}</div>
        <div class="kpi-subtitle">应付催款记录数</div>
      </div>
      <div class="dashboard-kpi-card" onclick="switchPage('purchase')">
        <div class="kpi-title">🛒 采购垫付</div>
        <div class="kpi-value" style="color:var(--danger)">${Utils.formatMoney(totalPurchaseAmount)}</div>
        <div class="kpi-subtitle">待报销金额</div>
      </div>
      <div class="dashboard-kpi-card" onclick="switchPage('travel')">
        <div class="kpi-title">✈️ 差旅报销</div>
        <div class="kpi-value" style="color:var(--primary)">${Utils.formatMoney(totalTravelAmount)}</div>
        <div class="kpi-subtitle">待报销金额</div>
      </div>
    `;

    // 三列动态：下单动态、计划单动态、垫付和差旅
    const quoteProducts = await window.electronAPI.db.getQuotationProducts();
    const compareRecords = await window.electronAPI.db.getThirdPartyRecords();
    const memos = await window.electronAPI.db.getMemos('', '', '');
    const bomItems = await window.electronAPI.db.getProductBOM({});

    const orderItems = packagingOrders.slice(0, 20).map(o => ({
      title: o.material_name || '未命名',
      meta: `${o.order_factory || ''} | ${Utils.formatMoney(o.compare_price)} | ${o.contract_status || ''}`,
      page: 'packaging',
    }));

    const planItems = planRecords.slice(0, 20).map(r => ({
      title: r.material_name || '未命名',
      meta: `${r.spec || ''} | 数量:${r.quantity}${r.unit||''} | ${Utils.formatMoney(r.amount||0)}`,
      page: 'plan',
    }));

    // 应付催款记录 - 按催款日期倒序 取前8条
    const collectionItems = collections.slice(0, 8).map(c => ({
      title: (c.supplier_name || '供应商') + ' - 应付催款',
      meta: `${c.reminder_date || ''} | 应付:${Utils.formatMoney(c.amount_due)}${c.notify_manager ? ' | 已通知经理' : ''}`,
      page: 'collection',
      badge: '应付',
      badgeColor: '#e74c3c',
    }));

    // 采购垫付记录 - 按日期倒序 取前8条（重点：未报销的优先展示）
    const purchasesSorted = [...purchases].sort((a, b) => {
      const aUrgent = a.reimbursement_status !== '已报销' ? 0 : 1;
      const bUrgent = b.reimbursement_status !== '已报销' ? 0 : 1;
      if (aUrgent !== bUrgent) return aUrgent - bUrgent;
      return (b.date || '').localeCompare(a.date || '');
    });
    const purchaseItems = purchasesSorted.slice(0, 8).map(p => {
      const total = (p.items||[]).reduce((s, i) => s + (i.total||0), 0);
      const summary = (p.items||[]).map(i => i.name).filter(Boolean).join('、') || '物料';
      return {
        title: `${p.project || '项目'} - ${summary.slice(0, 20)}`,
        meta: `${p.date || ''} | ¥${Utils.formatMoney(total).replace('¥','')} | ${p.reimbursement_status || ''}`,
        page: 'purchase',
        badge: '垫付',
        badgeColor: p.reimbursement_status !== '已报销' ? '#e67e22' : '#27ae60',
      };
    });

    // 差旅报销记录 - 按出发日期倒序 取前8条（重点：未报销的优先展示）
    const travelsSorted = [...travels].sort((a, b) => {
      const aUrgent = a.reimbursement_status !== '已报销' ? 0 : 1;
      const bUrgent = b.reimbursement_status !== '已报销' ? 0 : 1;
      if (aUrgent !== bUrgent) return aUrgent - bUrgent;
      return (b.start_date || '').localeCompare(a.start_date || '');
    });
    const travelItems = travelsSorted.slice(0, 8).map(t => {
      const total = (t.transports||[]).reduce((s,x)=>s+(x.amount||0),0) + (t.hotels||[]).reduce((s,x)=>s+(x.amount||0),0);
      return {
        title: `${t.destination || '出差'} - ${(t.reason||'').slice(0, 20)}`,
        meta: `${t.start_date || ''} | ${t.duration || 0}天 | ¥${Utils.formatMoney(total).replace('¥','')} | ${t.reimbursement_status || ''}`,
        page: 'travel',
        badge: '差旅',
        badgeColor: t.reimbursement_status !== '已报销' ? '#3498db' : '#27ae60',
      };
    });

    // 备忘记录 - 按内容倒序 取前8条（优先展示未完成的）
    const memosSorted = [...memos].sort((a, b) => {
      const aDone = a.status === '已完成' ? 1 : 0;
      const bDone = b.status === '已完成' ? 1 : 0;
      if (aDone !== bDone) return aDone - bDone;
      return (b.id || 0) - (a.id || 0);
    });
    const memoItems = memosSorted.slice(0, 8).map(m => ({
      title: (m.content || '备忘').slice(0, 30),
      meta: `${m.status || ''} | ${m.project || ''}`,
      page: 'memo',
      badge: '备忘',
      badgeColor: m.status === '已完成' ? '#27ae60' : '#9b59b6',
    }));

    // 报价/比价/BOM 辅助信息
    const quoteItems = quoteProducts.slice(0, 5).map(p => ({
      title: p.product_name || '报价产品',
      meta: `报价 | 项目号:${p.item_no}`,
      page: 'quotation',
      badge: '报价',
      badgeColor: '#16a085',
    }));
    const compareItems = compareRecords.slice(0, 5).map(r => ({
      title: r.product_name || '比价产品',
      meta: `比价 | ${Utils.formatDate(r.apply_date)}`,
      page: 'compare',
      badge: '比价',
      badgeColor: '#2c3e50',
    }));
    const bomItemsList = bomItems.slice(0, 5).map(b => ({
      title: b.product_name || 'BOM产品',
      meta: `BOM: ${b.material_name} ×${b.quantity}`,
      page: 'product_bom',
      badge: 'BOM',
      badgeColor: '#8e44ad',
    }));

    // 第三列：只合并 垫付 和 差旅 动态
    let otherItems = [
      ...purchaseItems,
      ...travelItems,
    ];

    function renderColumn(title, items, extraHeader = '') {
      return `
        <div class="dashboard-column">
          <div class="dashboard-column-header" style="display:flex;align-items:center;justify-content:space-between">
            <span>${title}</span>
            ${extraHeader}
          </div>
          <div class="dashboard-column-body">
            ${items.length === 0 ? '<div style="padding:20px;text-align:center;color:var(--text-secondary);font-size:13px">暂无数据</div>' : items.map(item => {
              const badge = item.badge
                ? `<span class="item-badge" style="background:${item.badgeColor};color:#fff;padding:1px 6px;border-radius:4px;font-size:11px;margin-right:6px;font-weight:500">${item.badge}</span>`
                : '';
              return `
                <div class="dashboard-item" onclick="switchPage('${item.page}')">
                  <div class="item-title">${badge}${Utils.escapeHtml(item.title)}</div>
                  <div class="item-meta">${Utils.escapeHtml(item.meta)}</div>
                </div>
              `;
            }).join('')}
          </div>
        </div>
      `;
    }

    // 让 loadDashboardPage 能读取容器，供下拉切换时刷新
    if (typeof window.__dashboardContainer__ === 'undefined') {
      window.__dashboardContainer__ = null;
    }

    $('#dashboard-grid').innerHTML =
      renderColumn('📦 下单动态', orderItems) +
      renderColumn('📋 计划单动态', planItems) +
      renderColumn('💳 垫付和差旅', otherItems);
    // 保存容器元素引用（loadDashboardPage 第一个参数是容器 DOM 节点）
    // 我们在 loadDashboardPage 里将其存入 window，使下拉刷新可以调用

  } catch (e) {
    console.error('Dashboard load error:', e);
  }
}
