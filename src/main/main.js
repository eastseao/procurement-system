const { app, BrowserWindow, ipcMain, Tray, Menu, nativeImage, dialog, shell, globalShortcut } = require('electron');
const path = require('path');
const fs = require('fs');
const https = require('https');
const { initDatabase, getDatabase } = require('./database');

// ── 显式声明运行期依赖（确保 electron-builder 静态分析时能识别并打包到 asar）──
require('exceljs');
require('jszip');
require('archiver');
require('unzipper');
require('dayjs');
require('fast-csv');
require('saxes');
require('readable-stream');
require('tmp');
require('uuid');

// ── 常量 ──
const APP_VERSION = '1.0.5';
const CONTENT_WIDTH = 1280;
const CONTENT_HEIGHT = 800;
const MIN_WIDTH = 1100;
const MIN_HEIGHT = 700;
const TITLE_BAR_HEIGHT = 40;
const SIDEBAR_WIDTH = 88;

const GITHUB_USER = 'eastseao';
const GITHUB_REPO = 'procurement-system';
const GITHUB_API_URL = `https://api.github.com/repos/${GITHUB_USER}/${GITHUB_REPO}/releases/latest`;

let mainWindow = null;
let tray = null;
let isQuitting = false;
let cachedAppIcon = null;  // 缓存应用图标引用，防止GC回收导致任务栏/快捷方式图标丢失

// ── 资源路径 ──
function getAssetPath(...parts) {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'assets', ...parts);
  }
  return path.join(__dirname, '..', '..', 'assets', ...parts);
}

function getDataDir() {
  // 优先读取自定义路径
  const configPath = path.join(app.getPath('userData'), 'data_path.txt');
  try {
    if (fs.existsSync(configPath)) {
      const customPath = fs.readFileSync(configPath, 'utf-8').trim();
      if (customPath && fs.existsSync(customPath)) {
        return customPath;
      }
    }
  } catch (e) { /* ignore */ }
  return path.join(app.getPath('userData'), '采购管理系统数据');
}

// ── 创建主窗口 ──
function createWindow() {
  mainWindow = new BrowserWindow({
    width: CONTENT_WIDTH,
    height: CONTENT_HEIGHT,
    minWidth: MIN_WIDTH,
    minHeight: MIN_HEIGHT,
    frame: false,
    transparent: false,
    resizable: true,
    show: false,
    icon: getAssetPath('icon', 'app-icon-multi.ico'),
    webPreferences: {
      preload: path.join(__dirname, '..', '..', 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
    backgroundColor: '#F5F7FA',
    roundedCorners: true,
    thickFrame: true,
  });

  mainWindow.loadFile(path.join(__dirname, '..', 'renderer', 'index.html'));

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.on('close', (event) => {
    if (!isQuitting) {
      event.preventDefault();
      mainWindow.hide();
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// ── 系统托盘 ──
function createTray() {
  try {
    // 托盘图标：优先用16x16的独立PNG（清晰），ICO作为fallback
    const tray16Path = getAssetPath('icon', 'app-icon-16x16.png');
    const trayIcoPath = getAssetPath('icon', 'app-icon-multi.ico');
    const iconPath = require('fs').existsSync(tray16Path) ? tray16Path : trayIcoPath;
    const trayIcon = nativeImage.createFromPath(iconPath);
    tray = new Tray(trayIcon.isEmpty()
      ? nativeImage.createFromPath(trayIcoPath)
      : trayIcon);

    const contextMenu = Menu.buildFromTemplate([
      {
        label: '显示窗口',
        click: () => {
          if (mainWindow) {
            mainWindow.show();
            mainWindow.focus();
          }
        },
      },
      { type: 'separator' },
      {
        label: '退出',
        click: () => {
          isQuitting = true;
          app.quit();
        },
      },
    ]);

    tray.setToolTip('采购助手');
    tray.setContextMenu(contextMenu);

    tray.on('double-click', () => {
      if (mainWindow) {
        mainWindow.show();
        mainWindow.focus();
      }
    });
  } catch (e) {
    console.error('Tray creation failed:', e);
  }
}

// ── IPC 处理器 ──
function setupIPC() {
  const db = getDatabase();

  // 窗口控制
  ipcMain.handle('window:minimize', () => mainWindow?.minimize());
  ipcMain.handle('window:maximize', () => {
    if (mainWindow?.isMaximized()) {
      mainWindow.unmaximize();
    } else {
      mainWindow?.maximize();
    }
  });
  ipcMain.handle('window:close', () => mainWindow?.hide());
  ipcMain.handle('window:isMaximized', () => mainWindow?.isMaximized());

  // 对话框
  ipcMain.handle('dialog:openFile', async (event, options) => {
    const result = await dialog.showOpenDialog(mainWindow, options);
    return result;
  });
  ipcMain.handle('dialog:saveFile', async (event, options) => {
    const result = await dialog.showSaveDialog(mainWindow, options);
    return result;
  });
  ipcMain.handle('dialog:messageBox', async (event, options) => {
    const result = await dialog.showMessageBox(mainWindow, options);
    return result;
  });

  // 文件操作
  ipcMain.handle('file:read', async (event, filePath) => {
    return fs.readFileSync(filePath, 'utf-8');
  });
  ipcMain.handle('file:write', async (event, filePath, data) => {
    fs.writeFileSync(filePath, data, 'utf-8');
    return true;
  });
  ipcMain.handle('file:exists', async (event, filePath) => {
    return fs.existsSync(filePath);
  });
  ipcMain.handle('file:getAssetPath', async (event, ...parts) => {
    return getAssetPath(...parts);
  });

  // Shell
  ipcMain.handle('shell:openExternal', async (event, url) => {
    return shell.openExternal(url);
  });

  // ── 数据库 API ──
  // 采购垫付
  ipcMain.handle('db:getPurchases', (event, archived) => db.getPurchases(archived));
  ipcMain.handle('db:savePurchase', (event, data, items) => db.savePurchase(data, items));
  ipcMain.handle('db:updatePurchase', (event, id, data, items) => db.updatePurchase(id, data, items));
  ipcMain.handle('db:deletePurchase', (event, id) => db.deletePurchase(id));
  ipcMain.handle('db:archivePurchase', (event, id) => db.archivePurchase(id));

  // 差旅
  ipcMain.handle('db:getTravels', (event, archived) => db.getTravels(archived));
  ipcMain.handle('db:saveTravel', (event, data, transports, hotels) => db.saveTravel(data, transports, hotels));
  ipcMain.handle('db:updateTravel', (event, id, data, transports, hotels) => db.updateTravel(id, data, transports, hotels));
  ipcMain.handle('db:deleteTravel', (event, id) => db.deleteTravel(id));
  ipcMain.handle('db:archiveTravel', (event, id) => db.archiveTravel(id));

  // 供应商
  ipcMain.handle('db:getSuppliers', (event, category, keyword, status) => db.getSuppliers(category, keyword, status));
  ipcMain.handle('db:getSupplier', (event, id) => db.getSupplier(id));
  ipcMain.handle('db:saveSupplier', (event, data) => db.saveSupplier(data));
  ipcMain.handle('db:updateSupplier', (event, id, data) => db.updateSupplier(id, data));
  ipcMain.handle('db:deleteSupplier', (event, id) => db.deleteSupplier(id));

  // 催款
  ipcMain.handle('db:getCollections', (event, keyword, startDate, endDate) => db.getCollections(keyword, startDate, endDate));
  ipcMain.handle('db:getCollection', (event, id) => db.getCollection(id));
  ipcMain.handle('db:saveCollection', (event, data) => db.saveCollection(data));
  ipcMain.handle('db:updateCollection', (event, id, data) => db.updateCollection(id, data));
  ipcMain.handle('db:deleteCollection', (event, id) => db.deleteCollection(id));

  // 备忘录
  ipcMain.handle('db:getMemos', (event, keyword, project, status) => db.getMemos(keyword, project, status));
  ipcMain.handle('db:getMemo', (event, id) => db.getMemo(id));
  ipcMain.handle('db:saveMemo', (event, data) => db.saveMemo(data));
  ipcMain.handle('db:updateMemo', (event, id, data) => db.updateMemo(id, data));
  ipcMain.handle('db:deleteMemo', (event, id) => db.deleteMemo(id));

  // 物料台账
  ipcMain.handle('db:getMaterialLedger', (event, filters) => db.getMaterialLedger(filters));
  ipcMain.handle('db:saveMaterialLedger', (event, rows) => db.saveMaterialLedger(rows));
  ipcMain.handle('db:clearMaterialLedger', () => db.clearMaterialLedger());

  // 包材下单
  ipcMain.handle('db:getPackagingOrders', (event, filters) => db.getPackagingOrders(filters));
  ipcMain.handle('db:savePackagingOrder', (event, data) => db.savePackagingOrder(data));
  ipcMain.handle('db:updatePackagingOrder', (event, id, data) => db.updatePackagingOrder(id, data));
  ipcMain.handle('db:deletePackagingOrder', (event, id) => db.deletePackagingOrder(id));

  // 报价
  ipcMain.handle('db:getQuotationProducts', () => db.getQuotationProducts());
  ipcMain.handle('db:getQuotationProduct', (event, id) => db.getQuotationProduct(id));
  ipcMain.handle('db:saveQuotationProduct', (event, data) => db.saveQuotationProduct(data));
  ipcMain.handle('db:updateQuotationProduct', (event, id, data) => db.updateQuotationProduct(id, data));
  ipcMain.handle('db:deleteQuotationProduct', (event, id) => db.deleteQuotationProduct(id));
  ipcMain.handle('db:saveQuotationTier', (event, data) => db.saveQuotationTier(data));
  ipcMain.handle('db:deleteQuotationTiers', (event, productId) => db.deleteQuotationTiers(productId));
  ipcMain.handle('db:getQuotationConfig', () => db.getQuotationConfig());
  ipcMain.handle('db:updateQuotationConfig', (event, data) => db.updateQuotationConfig(data));
  ipcMain.handle('db:getAllQuotationSuppliers', () => db.getAllQuotationSuppliers());
  ipcMain.handle('db:saveQuotationSupplierRecord', (event, data) => db.saveQuotationSupplierRecord(data));
  ipcMain.handle('db:updateQuotationSupplierRecord', (event, id, data) => db.updateQuotationSupplierRecord(id, data));
  ipcMain.handle('db:deleteQuotationSupplierRecord', (event, id) => db.deleteQuotationSupplierRecord(id));

  // 合同
  ipcMain.handle('db:getContractSuppliers', () => db.getContractSuppliers());
  ipcMain.handle('db:getContractPartyA', () => db.getContractPartyA());
  ipcMain.handle('db:saveContractSupplier', (event, data) => db.saveContractSupplier(data));
  ipcMain.handle('db:updateContractSupplier', (event, id, data) => db.updateContractSupplier(id, data));
  ipcMain.handle('db:deleteContractSupplier', (event, id) => db.deleteContractSupplier(id));
  ipcMain.handle('db:saveContractPartyA', (event, data) => db.saveContractPartyA(data));
  ipcMain.handle('db:getContractProducts', () => db.getContractProducts());
  ipcMain.handle('db:saveContractProduct', (event, data) => db.saveContractProduct(data));
  ipcMain.handle('db:deleteContractProduct', (event, id) => db.deleteContractProduct(id));

  // 成品BOM
  ipcMain.handle('db:getProductBOM', (event, filters) => db.getProductBOM(filters));
  ipcMain.handle('db:importProductBOM', (event, rows) => db.importProductBOM(rows));
  ipcMain.handle('db:saveProductBOMBatch', (event, rows) => db.saveProductBOMBatch(rows));
  ipcMain.handle('db:deleteProductBOM', (event, id) => db.deleteProductBOM(id));

  // 三方比价
  ipcMain.handle('db:getThirdPartyRecords', () => db.getThirdPartyRecords());
  ipcMain.handle('db:getThirdPartyRecord', (event, id) => db.getThirdPartyRecord(id));
  ipcMain.handle('db:saveThirdPartyRecord', (event, data) => db.saveThirdPartyRecord(data));
  ipcMain.handle('db:updateThirdPartyRecord', (event, id, data) => db.updateThirdPartyRecord(id, data));
  ipcMain.handle('db:deleteThirdPartyRecord', (event, id) => db.deleteThirdPartyRecord(id));

  // 计划
  ipcMain.handle('db:getPlanRecords', (event, archived) => db.getPlanRecords(archived));
  ipcMain.handle('db:savePlanRecord', (event, data) => db.savePlanRecord(data));
  ipcMain.handle('db:updatePlanRecord', (event, id, data) => db.updatePlanRecord(id, data));
  ipcMain.handle('db:deletePlanRecord', (event, id) => db.deletePlanRecord(id));
  ipcMain.handle('db:archivePlanRecord', (event, id) => db.archivePlanRecord(id));

  // 项目
  ipcMain.handle('db:getProjects', () => db.getProjects());
  ipcMain.handle('db:addProject', (event, name) => db.addProject(name));

  // 设置
  ipcMain.handle('db:getSettings', () => db.getSettings());
  ipcMain.handle('db:updateSetting', (event, key, value) => db.updateSetting(key, value));

  // 导出
  ipcMain.handle('db:exportToXLSX', (event, tableName, rows, filePath, columnMap) => {
    return db.exportToXLSX(tableName, rows, filePath, columnMap);
  });

  // 合同生成（DOCX）
  ipcMain.handle('file:generateContract', async (event, params) => {
    try {
      const result = await generateContractDocx(params);
      return { success: true };
    } catch (e) {
      return { success: false, error: e.message };
    }
  });

  // 上传合同文件保存（拖拽上传）
  ipcMain.handle('file:saveUploadedFile', async (event, params) => {
    try {
      const { fileName, data } = params;
      const uploadDir = path.join(getDataDir(), 'contract_uploads');
      if (!fs.existsSync(uploadDir)) fs.mkdirSync(uploadDir, { recursive: true });
      const savePath = path.join(uploadDir, fileName);
      const buffer = Buffer.from(data);
      fs.writeFileSync(savePath, buffer);
      return { success: true, path: savePath };
    } catch (e) {
      return { success: false, error: e.message };
    }
  });

  // 生成计划导入模板（Excel）
  ipcMain.handle('file:generatePlanTemplate', async (event, params) => {
    try {
      const ExcelJS = require('exceljs');
      const workbook = new ExcelJS.Workbook();
      const worksheet = workbook.addWorksheet('采购计划');

      // 定义列（表头）
      worksheet.columns = [
        { header: '审批编号', key: 'approval_no', width: 18 },
        { header: '物料名称', key: 'material_name', width: 25 },
        { header: '规格', key: 'spec', width: 20 },
        { header: '单位', key: 'unit', width: 10 },
        { header: '数量', key: 'quantity', width: 10 },
        { header: '单价', key: 'unit_price', width: 12 },
        { header: '金额', key: 'amount', width: 12 },
        { header: '期望交付日期', key: 'expected_delivery', width: 16 },
        { header: '备注', key: 'remark', width: 20 },
      ];

      // 设置表头样式：加粗、居中、淡背景
      worksheet.getRow(1).eachCell((cell) => {
        cell.font = { bold: true, size: 11 };
        cell.alignment = { horizontal: 'center', vertical: 'middle' };
        cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFE7E8EB' } };
        cell.border = { top: { style: 'thin' }, left: { style: 'thin' }, bottom: { style: 'thin' }, right: { style: 'thin' } };
      });

      // 示例数据
      const sampleRows = [
        { approval_no: 'AP2026001', material_name: '标签纸（热敏）', spec: '60*40mm', unit: '卷', quantity: 20, unit_price: 15.00, amount: 300.00, expected_delivery: '2026-06-25', remark: '优先配送' },
        { approval_no: 'AP2026002', material_name: 'A4复印纸', spec: '70g/500张', unit: '包', quantity: 50, unit_price: 25.50, amount: 1275.00, expected_delivery: '2026-06-22', remark: '' },
        { approval_no: 'AP2026003', material_name: '不锈钢螺丝', spec: 'M4*12mm', unit: '个', quantity: 500, unit_price: 0.15, amount: 75.00, expected_delivery: '2026-06-20', remark: '需304材质' },
      ];

      sampleRows.forEach((row) => {
        const addedRow = worksheet.addRow(row);
        addedRow.eachCell((cell) => {
          cell.alignment = { horizontal: 'left', vertical: 'middle' };
          cell.border = { top: { style: 'thin' }, left: { style: 'thin' }, bottom: { style: 'thin' }, right: { style: 'thin' } };
        });
      });

      worksheet.views = [{ state: 'frozen', ySplit: 1 }];
      await workbook.xlsx.writeFile(params.filePath);
      return { success: true, path: params.filePath };
    } catch (e) {
      return { success: false, error: e.message };
    }
  });

  // 合同解析（提取产品信息和乙方信息）
  ipcMain.handle('file:parseContract', async (event, filePath) => {
    try {
      const result = parseContractDocx(filePath);
      return { success: true, data: result };
    } catch (e) {
      return { success: false, error: e.message };
    }
  });

  // 数据导入：从旧版数据库导入数据
  ipcMain.handle('db:importFromOld', async (event, oldDbPath) => {
    try {
      const result = importFromOldDatabase(oldDbPath);
      return { success: true, ...result };
    } catch (e) {
      return { success: false, error: e.message };
    }
  });

  // 数据存储路径
  ipcMain.handle('app:getDataPath', () => getDataDir());
  ipcMain.handle('app:setDataPath', async (event, newPath) => {
    try {
      if (!fs.existsSync(newPath)) {
        fs.mkdirSync(newPath, { recursive: true });
      }
      // 保存新路径到配置文件
      const configPath = path.join(app.getPath('userData'), 'data_path.txt');
      fs.writeFileSync(configPath, newPath, 'utf-8');
      return { success: true, path: newPath };
    } catch (e) {
      return { success: false, error: e.message };
    }
  });

  // 版本
  ipcMain.handle('app:getVersion', () => APP_VERSION);

  // 开机启动
  ipcMain.handle('app:getAutoLaunch', () => {
    try {
      const info = app.getLoginItemSettings();
      return { openAtLogin: info.openAtLogin, enabled: info.openAtLogin };
    } catch (e) {
      return { openAtLogin: false, error: e.message };
    }
  });

  ipcMain.handle('app:setAutoLaunch', async (event, enabled) => {
    try {
      app.setLoginItemSettings({
        openAtLogin: enabled,
        path: process.execPath,
        args: []
      });
      const info = app.getLoginItemSettings();
      return { success: true, openAtLogin: info.openAtLogin };
    } catch (e) {
      return { success: false, error: e.message };
    }
  });

  // 更新检查
  ipcMain.handle('app:checkUpdates', () => {
    return new Promise((resolve) => {
      const req = https.get(GITHUB_API_URL, {
        headers: {
          'Accept': 'application/vnd.github.v3+json',
          'User-Agent': `ProcurementSystem/${APP_VERSION}`,
        },
      }, (res) => {
        let body = '';
        res.on('data', chunk => body += chunk);
        res.on('end', () => {
          try {
            const data = JSON.parse(body);
            const tagName = (data.tag_name || '').replace(/^v/, '');
            const assetUrl = (data.assets || []).find(a => a.name.endsWith('.exe'))?.browser_download_url || '';
            resolve({
              hasUpdate: tagName > APP_VERSION,
              currentVersion: APP_VERSION,
              latestVersion: tagName || APP_VERSION,
              downloadUrl: data.html_url || '',
              assetDownloadUrl: assetUrl,
              releaseNotes: data.body || '',
            });
          } catch (e) {
            resolve({ hasUpdate: false, currentVersion: APP_VERSION, latestVersion: APP_VERSION });
          }
        });
      });
      req.on('error', () => {
        resolve({ hasUpdate: false, currentVersion: APP_VERSION, latestVersion: APP_VERSION });
      });
      req.setTimeout(8000, () => {
        req.destroy();
        resolve({ hasUpdate: false, currentVersion: APP_VERSION, latestVersion: APP_VERSION });
      });
    });
  });

  // ── XLSX 处理（通过 IPC 在主进程用 xlsx 库处理）──
  ipcMain.handle('xlsx:read', async (event, filePath) => {
    try {
      const XLSX = require('xlsx');
      const workbook = XLSX.readFile(filePath);
      const result = {};
      workbook.SheetNames.forEach(name => {
        result[name] = XLSX.utils.sheet_to_json(workbook.Sheets[name], { header: 1, defval: '' });
      });
      return { success: true, data: result };
    } catch (e) {
      return { success: false, error: e.message };
    }
  });

  ipcMain.handle('xlsx:write', async (event, filePath, sheets) => {
    try {
      const XLSX = require('xlsx');
      const workbook = XLSX.utils.book_new();
      Object.entries(sheets).forEach(([name, rows]) => {
        const ws = XLSX.utils.aoa_to_sheet(rows);
        XLSX.utils.book_append_sheet(workbook, ws, name);
      });
      XLSX.writeFile(workbook, filePath);
      return { success: true };
    } catch (e) {
      return { success: false, error: e.message };
    }
  });

  // ── 报价单模板导出（基于模板）──
  ipcMain.handle('file:exportQuotation', async (event, params) => {
    try {
      const result = await generateQuotationXlsx(params);
      return { success: true };
    } catch (e) {
      return { success: false, error: e.message };
    }
  });

  // ── 比价表导出（基于比价表模板.xlsx）──
  ipcMain.handle('file:exportCompare', async (event, params) => {
    try {
      const result = await generateCompareXlsx(params);
      return { success: true };
    } catch (e) {
      return { success: false, error: e.message };
    }
  });

  // ── CSV 处理 ──
  ipcMain.handle('csv:read', async (event, filePath) => {
    try {
      const content = fs.readFileSync(filePath, 'utf-8');
      const lines = content.split(/\r?\n/).filter(l => l.trim());
      const rows = lines.map(line => {
        const result = [];
        let current = '';
        let inQuotes = false;
        for (const ch of line) {
          if (ch === '"') { inQuotes = !inQuotes; continue; }
          if (ch === ',' && !inQuotes) { result.push(current.trim()); current = ''; continue; }
          current += ch;
        }
        result.push(current.trim());
        return result;
      });
      return { success: true, data: rows };
    } catch (e) {
      return { success: false, error: e.message };
    }
  });

  // ── PDF 解析（使用静态路径，避免 asar 打包动态 require 问题） ──
  ipcMain.handle('pdf:parse', async (event, filePath) => {
    try {
      const path = require('path');
      const fs = require('fs');

      if (!fs.existsSync(filePath)) {
        return { success: false, error: '文件不存在：' + filePath };
      }

      const dataBuffer = fs.readFileSync(filePath);

      // 静态加载 pdf.js（从 pdf-parse 的 lib 目录）
      // 避免 pdf-parse 内部动态 require 导致 asar 打包失败
      let PDFJS;
      try {
        const pdfParseRoot = path.dirname(require.resolve('pdf-parse'));
        const pdfJsPath = path.join(pdfParseRoot, 'lib', 'pdf.js', 'v1.10.100', 'build', 'pdf.js');
        PDFJS = require(pdfJsPath);
      } catch (e) {
          // 如果静态路径失败，回退到 pdf-parse
          const pdfParse = require('pdf-parse');
          const data = await pdfParse(dataBuffer);
          return { success: true, text: data.text };
      }

      PDFJS.disableWorker = true;
      const doc = await PDFJS.getDocument(dataBuffer);
      let fullText = '';
      for (let i = 1; i <= doc.numPages; i++) {
        try {
          const pageData = await doc.getPage(i);
          const textContent = await pageData.getTextContent({
            normalizeWhitespace: false,
            disableCombineTextItems: false,
          });
          let lastY = null;
          let pageText = '';
          for (const item of textContent.items) {
            if (lastY === item.transform[5] || !lastY) {
              pageText += item.str;
            } else {
              pageText += '\n' + item.str;
            }
            lastY = item.transform[5];
          }
          fullText += '\n\n' + pageText;
        } catch (pageErr) {
          // 跳过解析失败的页面
        }
      }
      doc.destroy();
      return { success: true, text: fullText };
    } catch (e) {
      return { success: false, error: e.message };
    }
  });

  // ── DOCX 解析（提取表格 + 文本） ──
  ipcMain.handle('docx:read', async (event, filePath) => {
    try {
      const AdmZip = require('adm-zip');
      const { DOMParser } = require('@xmldom/xmldom');
      if (!fs.existsSync(filePath)) return { success: false, error: '文件不存在' };
      const zip = new AdmZip(filePath);
      const docXmlRaw = zip.readAsText('word/document.xml');
      if (!docXmlRaw) return { success: false, error: '未找到 document.xml' };
      const doc = new DOMParser().parseFromString(docXmlRaw, 'text/xml');

      // ── 提取表格 tables: [[row_cells], ...] ──
      const tables = [];
      const tblEls = doc.getElementsByTagName('w:tbl');
      for (let t = 0; t < tblEls.length; t++) {
        const tbl = tblEls[t];
        const rows = tbl.getElementsByTagName('w:tr');
        const table = [];
        for (let r = 0; r < rows.length; r++) {
          const tr = rows[r];
          const cellEls = tr.getElementsByTagName('w:tc');
          const cells = [];
          for (let c = 0; c < cellEls.length; c++) {
            const pEls = cellEls[c].getElementsByTagName('w:p');
            const texts = [];
            for (let p = 0; p < pEls.length; p++) {
              const tEls = pEls[p].getElementsByTagName('w:t');
              let pText = '';
              for (let i = 0; i < tEls.length; i++) pText += (tEls[i].textContent || '');
              if (pText) texts.push(pText.trim());
            }
            cells.push(texts.join(' '));
          }
          table.push(cells);
        }
        if (table.length > 0) tables.push(table);
      }

      // ── 提取段落文本 ──
      const pEls = doc.getElementsByTagName('w:p');
      const textLines = [];
      for (let i = 0; i < pEls.length; i++) {
        const tEls = pEls[i].getElementsByTagName('w:t');
        let line = '';
        for (let j = 0; j < tEls.length; j++) line += (tEls[j].textContent || '');
        if (line.trim()) textLines.push(line.trim());
      }

      return { success: true, tables, text: textLines.join('\n') };
    } catch (e) {
      return { success: false, error: e.message };
    }
  });
}

// ── 合同生成（DOCX）──
// 注入字段全部带下划线（<w:u/>）
async function generateContractDocx(params) {
  const { templatePath, savePath, contractNo, contractDate, materialName, partyA, partyB, products, totalAmount, totalAmountUpper, taxRate, deliveryDays } = params;
  const AdmZip = require('adm-zip');
  const { DOMParser, XMLSerializer } = require('@xmldom/xmldom');

  if (!fs.existsSync(templatePath)) {
    throw new Error('模板文件不存在');
  }

  const tmpDir = path.join(require('os').tmpdir(), 'contract_' + Date.now());
  const unpackDir = path.join(tmpDir, 'unpacked');
  fs.mkdirSync(unpackDir, { recursive: true });

  const W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main';

  // ── 辅助：创建 text node（保留空格） ──
  function createText(doc, text) {
    const t = doc.createElementNS(W, 'w:t');
    t.setAttribute('xml:space', 'preserve');
    t.textContent = text || '';
    return t;
  }

  // ── 辅助：从 paragraph 中提取第一个有文本的 run 的 rPr（克隆） ──
  function extractDefaultRunRPr(p) {
    const runs = p.getElementsByTagNameNS(W, 'r');
    for (let i = 0; i < runs.length; i++) {
      const r = runs[i];
      const txts = r.getElementsByTagNameNS(W, 't');
      if (txts.length > 0 && (txts[0].textContent || '').trim() !== '') {
        const existingRPr = r.getElementsByTagNameNS(W, 'rPr');
        if (existingRPr.length > 0) {
          return existingRPr[0].cloneNode(true);
        }
        break;
      }
    }
    // 检查 pPr 中是否有默认 rPr
    const pPr = p.getElementsByTagNameNS(W, 'pPr');
    if (pPr.length > 0) {
      const defaultRPr = pPr[0].getElementsByTagNameNS(W, 'rPr');
      if (defaultRPr.length > 0) {
        return defaultRPr[0].cloneNode(true);
      }
    }
    return null;
  }

  // ── 辅助：克隆 rPr 并根据需求添加下划线 ──
  function cloneRPrWithUnderline(doc, baseRPr, wantUnderline) {
    if (!baseRPr) {
      if (!wantUnderline) return null;
      const rPr = doc.createElementNS(W, 'w:rPr');
      const u = doc.createElementNS(W, 'w:u');
      u.setAttribute('w:val', 'single');
      rPr.appendChild(u);
      return rPr;
    }
    const rPr = baseRPr.cloneNode(true);
    // 移除已有的 u 元素
    const existingUs = rPr.getElementsByTagNameNS(W, 'u');
    for (let i = existingUs.length - 1; i >= 0; i--) {
      rPr.removeChild(existingUs[i]);
    }
    if (wantUnderline) {
      const u = doc.createElementNS(W, 'w:u');
      u.setAttribute('w:val', 'single');
      rPr.appendChild(u);
    }
    return rPr;
  }

  // ── 辅助：创建带有继承格式的 run ──
  function createStyledRun(doc, text, baseRPr, underlined) {
    const r = doc.createElementNS(W, 'w:r');
    const rPr = cloneRPrWithUnderline(doc, baseRPr, underlined);
    if (rPr) r.appendChild(rPr);
    else if (underlined) {
      // 没有基础 rPr 的情况下添加下划线
      const newRPr = doc.createElementNS(W, 'w:rPr');
      const u = doc.createElementNS(W, 'w:u');
      u.setAttribute('w:val', 'single');
      newRPr.appendChild(u);
      r.appendChild(newRPr);
    }
    r.appendChild(createText(doc, text));
    return r;
  }

  // ── 辅助：替换 paragraph 的文本内容，保留原段落格式和 run 格式 ──
  // 【关键】不移除/改变 pPr，新 run 继承原 run 的 rPr 格式
  function replaceParagraph(p, segments) {
    const doc = p.ownerDocument;
    // 先提取原段落中第一个 run 的 rPr 作为默认格式
    const defaultRPr = extractDefaultRunRPr(p);

    // 只移除 <w:r> 节点（文本 runs），保留 <w:pPr>、<w:bookmarkStart> 等属性节点
    const toRemove = [];
    for (let i = 0; i < p.childNodes.length; i++) {
      const child = p.childNodes[i];
      if (child.tagName && child.tagName.replace(/^w:/, '') === 'r') {
        toRemove.push(child);
      }
    }
    for (const r of toRemove) p.removeChild(r);

    // 添加新的 runs（继承原格式）
    for (const seg of segments) {
      p.appendChild(createStyledRun(doc, seg.text, defaultRPr, seg.underlined));
    }
  }

  // ── 辅助：用一段纯文本替换 paragraph（保留所有格式，只改文字） ──
  function setParagraphText(p, text) {
    replaceParagraph(p, [{ text: text, underlined: false }]);
  }

  // ── 辅助：用段落 segments 填充 table cell（保留模板格式） ──
  // 对于新增的 paragraph，克隆原第一个 p 的完整结构（含 pPr），仅替换文本
  function setCellWithLines(tc, linesArr) {
    const doc = tc.ownerDocument;
    const paragraphs = tc.getElementsByTagNameNS(W, 'p');
    const paraCount = paragraphs.length;

    for (let i = 0; i < linesArr.length; i++) {
      const segments = linesArr[i];
      if (i < paraCount) {
        // 复用现有 paragraph，用 replaceParagraph 保留格式
        replaceParagraph(paragraphs[i], segments);
      } else {
        // 新增 paragraph：克隆原第一个 paragraph 的完整结构（含 pPr）
        let newP;
        if (paraCount > 0) {
          newP = paragraphs[0].cloneNode(true);
          // 清空克隆的 paragraph 中的 runs（保留 pPr）
          const childRuns = newP.getElementsByTagNameNS(W, 'r');
          const toRemove = [];
          for (let j = 0; j < childRuns.length; j++) toRemove.push(childRuns[j]);
          for (const r of toRemove) newP.removeChild(r);
          const defaultRPr = extractDefaultRunRPr(paragraphs[0]);
          for (const seg of segments) {
            newP.appendChild(createStyledRun(doc, seg.text, defaultRPr, seg.underlined));
          }
        } else {
          newP = doc.createElementNS(W, 'w:p');
          for (const seg of segments) {
            if (seg.underlined) {
              newP.appendChild(createStyledRun(doc, seg.text, null, true));
            } else {
              newP.appendChild(createStyledRun(doc, seg.text, null, false));
            }
          }
        }
        tc.appendChild(newP);
      }
    }

    // 清空多余的原 paragraph（设置为空文本，保留格式）
    for (let i = linesArr.length; i < paraCount; i++) {
      if (paragraphs[i]) {
        setParagraphText(paragraphs[i], '');
      }
    }
  }

  // ── 辅助：设置单元格文本（简单版，仅一行文本，完全保留格式） ──
  function setCellText(tc, text) {
    const paragraphs = tc.getElementsByTagNameNS(W, 'p');
    if (paragraphs.length > 0) {
      setParagraphText(paragraphs[0], text);
    } else {
      const doc = tc.ownerDocument;
      const p = doc.createElementNS(W, 'w:p');
      p.appendChild(createStyledRun(doc, text, null, false));
      tc.appendChild(p);
    }
  }

  // ── 辅助：查找段落中所有 run 的文本 ──
  function getParagraphRuns(p) {
    const runs = p.getElementsByTagNameNS(W, 'r');
    const result = [];
    for (let i = 0; i < runs.length; i++) {
      const ts = runs[i].getElementsByTagNameNS(W, 't');
      if (ts.length > 0) {
        result.push({ run: runs[i], text: ts[0], content: ts[0].textContent || '' });
      }
    }
    return result;
  }

  // ── 辅助：替换段落中包含特定文本的 run 的内容（保留原格式/下划线） ──
  function replaceRunByKeyword(p, keyword, newText) {
    const runs = getParagraphRuns(p);
    for (let i = 0; i < runs.length; i++) {
      if (runs[i].content.includes(keyword)) {
        runs[i].text.textContent = newText;
        return true;
      }
    }
    return false;
  }

  // ── 辅助：替换段落中最后一个有意义文本的 run ──
  function replaceLastRun(p, newText) {
    const runs = getParagraphRuns(p);
    let lastIdx = -1;
    for (let i = 0; i < runs.length; i++) {
      if (runs[i].content.trim() !== '') lastIdx = i;
    }
    if (lastIdx >= 0) {
      runs[lastIdx].text.textContent = newText;
      return true;
    }
    return false;
  }

  // ── 辅助：在段落的所有 run 中查找并替换文本 ──
  function replaceTextInRuns(p, searchText, newText) {
    const runs = getParagraphRuns(p);
    for (let i = 0; i < runs.length; i++) {
      if (runs[i].content.includes(searchText)) {
        runs[i].text.textContent = runs[i].content.replace(searchText, newText);
        return true;
      }
    }
    return false;
  }

  // ── 辅助：把整个段落的纯文本替换为新内容（保留第一个 run 的格式） ──
  function replaceParagraphSimple(p, newText) {
    const doc = p.ownerDocument;
    const runs = p.getElementsByTagNameNS(W, 'r');
    // 先清除所有 run
    const toRemove = [];
    for (let i = 0; i < runs.length; i++) toRemove.push(runs[i]);
    for (const r of toRemove) p.removeChild(r);
    // 添加新 run，继承原格式
    const baseRPr = extractDefaultRunRPr(p);
    p.appendChild(createStyledRun(doc, newText, baseRPr, false));
  }

  // ── 辅助：设置单元格段落的"值"部分（绝对保留格式/下划线） ──
  // 核心逻辑：只修改 run 的 textContent，绝不改动 rPr（包括下划线设置）
  // 当 value 为空时，**完全不做修改**，保留原模板中的空格下划线
  function setCellParagraphValue(tc, paraIndex, label, value) {
    const paragraphs = tc.getElementsByTagNameNS(W, 'p');
    if (paraIndex >= paragraphs.length) return;
    const p = paragraphs[paraIndex];
    const runs = getParagraphRuns(p);
    if (runs.length === 0) return;

    // 【关键修复1】值为空时，**完全保留原模板内容**（包括空格下划线）
    if (value === '' || value === null || value === undefined) {
      return;
    }

    // 找到":"或"："的 run 位置
    let colonIdx = -1;
    for (let i = 0; i < runs.length; i++) {
      if (runs[i].content.includes(':') || runs[i].content.includes('：')) {
        colonIdx = i;
        break;
      }
    }

    // 【关键修复2】值非空时：
    // - 找到":"后第一个**有实际文本内容**的 run（模板中值可能在多个下划线run之后）
    // - 修改该 run 的 textContent，清空后续多余内容run，保留空格run的下划线格式
    if (colonIdx === -1) {
      // 没找到冒号，就替换最后一个有文本的 run
      let lastIdx = -1;
      for (let i = 0; i < runs.length; i++) {
        if (runs[i].content.trim() !== '') lastIdx = i;
      }
      if (lastIdx >= 0) runs[lastIdx].text.textContent = value;
      return;
    }

    // 从 colonIdx+1 开始，找到第一个非纯空白的 run（这就是实际值的位置）
    let targetIdx = -1;
    for (let i = colonIdx + 1; i < runs.length; i++) {
      if (runs[i].content.trim() !== '') {
        targetIdx = i;
        break;
      }
    }
    // 如果":"后全是空格，就取直接下一个
    if (targetIdx === -1 && colonIdx + 1 < runs.length) {
      targetIdx = colonIdx + 1;
    }

    if (targetIdx >= 0) {
      // 设置目标 run 的值（保留原 rPr/下划线）
      runs[targetIdx].text.textContent = value;
      // 清空 targetIdx 之后**有实际意义文本**的 run（保留纯空格下划线run）
      for (let i = targetIdx + 1; i < runs.length; i++) {
        if (runs[i].content.trim() !== '') {
          runs[i].text.textContent = '';
        }
      }
    }
  }

  // ── 辅助：把单元格所有段落的纯文本替换为一个字符串（不改格式） ──
  // 【修复】完全替换单元格文本内容（删除所有原有run，只保留一个新run）
  // 原因：模板单元格可能有预置文字如"￥0.00元"或"0.00元整"，
  //       setCellTextSimple 只替换第一个 run 会导致"元"或"元整"残留
  function setCellTextSimple(tc, text) {
    const paragraphs = tc.getElementsByTagNameNS(W, 'p');
    if (paragraphs.length === 0) return;
    const p = paragraphs[0];
    const doc = p.ownerDocument;

    // 获取所有的 run 元素
    const runs = p.getElementsByTagNameNS(W, 'r');

    // 策略1：有 run 时，用第一个 run 的格式保留样式，其他 run 删除
    if (runs.length > 0) {
      // 提取第一个 run 的 rPr 作为样式基准
      const firstRun = runs[0];
      let baseRPr = null;
      const firstRPrEls = firstRun.getElementsByTagNameNS(W, 'rPr');
      if (firstRPrEls.length > 0) {
        baseRPr = firstRPrEls[0].cloneNode(true);
      }

      // 清除 paragraph 中所有 run 和 text 元素
      // 需要先把要删除的元素收集起来（live collection，遍历时不能直接删）
      const toRemove = [];
      for (let i = 0; i < p.childNodes.length; i++) {
        const node = p.childNodes[i];
        if (node && node.localName === 'r') {
          toRemove.push(node);
        }
      }
      for (const r of toRemove) {
        p.removeChild(r);
      }

      // 添加一个新的 run，包含正确文本和样式
      const newRun = doc.createElementNS(W, 'r');
      if (baseRPr) newRun.appendChild(baseRPr);
      const t = doc.createElementNS(W, 't');
      t.setAttribute('xml:space', 'preserve');
      t.textContent = text || '';
      newRun.appendChild(t);
      p.appendChild(newRun);
    } else {
      // 没有 run，直接添加一个
      p.appendChild(createStyledRun(doc, text, null, false));
    }
  }

  // ── 辅助：把单元格第二个段落的数字/大写金额替换（用于合计行） ──
  // 原格式类似：小写：￥100.00元  大写：壹佰元整
  function setCellTotalAmount(tc, lowerAmount, upperAmount) {
    const paragraphs = tc.getElementsByTagNameNS(W, 'p');
    if (paragraphs.length === 0) return;
    const p = paragraphs[0];
    const runs = getParagraphRuns(p);

    // 策略：遍历所有 run，找到数字部分和"元整"类文本
    let foundNum = false;
    for (let i = 0; i < runs.length; i++) {
      const content = runs[i].content;
      // 数字模式：包含数字+可能的小数点
      if (/^\d+(\.\d+)?$/.test(content.trim()) || /^￥?\d+(\.\d+)?元?$/.test(content.trim())) {
        if (!foundNum) {
          // 第一次遇到数字 → 这是小写金额
          runs[i].text.textContent = lowerAmount;
          foundNum = true;
        }
      }
    }

    // 如果找到数字后还需要处理大写
    // 策略：找到最后一个包含中文数字/大写金额的 run
    if (foundNum) {
      for (let i = runs.length - 1; i >= 0; i--) {
        const content = runs[i].content;
        // 匹配中文大写金额字符
        if (/[零壹贰叁肆伍陆柒捌玖拾佰仟万亿元整角分]/.test(content) && !content.includes('大写')) {
          runs[i].text.textContent = upperAmount;
          break;
        }
      }
    }
  }

  // ── 解压模板 ──
  const zip = new AdmZip(templatePath);
  zip.extractAllTo(unpackDir, true);

  // ── 处理日期 ──
  let yearStr = '', monthStr = '', dayStr = '';
  if (contractDate) {
    const parts = contractDate.split('-');
    if (parts.length === 3) {
      yearStr = parts[0];
      monthStr = String(parseInt(parts[1]));
      dayStr = String(parseInt(parts[2]));
    }
  }

  // ── 替换页眉：合同编号（仅替换文本内容，不改格式） ──
  const headerPath = path.join(unpackDir, 'word', 'header1.xml');
  if (fs.existsSync(headerPath)) {
    const headerXmlRaw = fs.readFileSync(headerPath, 'utf-8');
    const parser = new DOMParser();
    const headerDoc = parser.parseFromString(headerXmlRaw, 'text/xml');
    const headerPs = headerDoc.getElementsByTagNameNS(W, 'p');
    // 找到第一个有文本的段落，直接替换其文本内容（保留原格式）
    if (headerPs.length > 0) {
      const p = headerPs[0];
      const runs = getParagraphRuns(p);
      if (runs.length > 0) {
        // 只替换第一个有文本的 run 为合同编号
        runs[0].text.textContent = contractNo || '';
        // 清空其他 run
        for (let i = 1; i < runs.length; i++) {
          runs[i].text.textContent = '';
        }
      }
    }
    const serializer = new XMLSerializer();
    const headerXml = serializer.serializeToString(headerDoc);
    fs.writeFileSync(headerPath, headerXml, 'utf-8');
  }

  // ── 处理正文 document.xml ──
  const docPath = path.join(unpackDir, 'word', 'document.xml');
  if (fs.existsSync(docPath)) {
    const docXmlRaw = fs.readFileSync(docPath, 'utf-8');
    const parser = new DOMParser();
    const doc = parser.parseFromString(docXmlRaw, 'text/xml');

    const paragraphs = doc.getElementsByTagNameNS(W, 'p');

    // ── 2) 遍历 paragraph 做文本替换（只改 run 的 textContent，保留格式） ──
    for (let pi = 0; pi < paragraphs.length; pi++) {
      const p = paragraphs[pi];
      const ptxts = p.getElementsByTagNameNS(W, 't');
      let fullText = '';
      for (let ti = 0; ti < ptxts.length; ti++) {
        fullText += ptxts[ti].textContent || '';
      }

      // 2a) 物料名称 + 签订日期段（保留原模板下划线格式，只改文本）
      // 模板结构：...购得[物料名（带U）]产品...于[年份]年[月份数字]月[日期数字]日签订合同...
      // 修复：以"年"、"月"、"日"汉字为锚点，精确找到对应的数字run并替换
      if (fullText.includes('购得') && fullText.includes('标签')) {
        const runs = getParagraphRuns(p);

        // 替换物料名称：找到包含"标签"的run
        for (let i = 0; i < runs.length; i++) {
          if (runs[i].content.includes('标签')) {
            runs[i].text.textContent = materialName || '';
            break;
          }
        }

        // ===== 精确注入年/月/日 =====
        // 1) 年份：找到"年"字 run，其前面第一个纯数字run = 年份
        // 2) 月份：找到"月"字 run，其前面的连续数字run = 月份（可能被拆分）
        // 3) 日期：找到"日"字 run，其前面的数字run = 日期
        let idx = 0;

        // 年份
        for (; idx < runs.length; idx++) {
          const c = runs[idx].content;
          if (/^\D*年\D*$/.test(c) || (c.includes('年') && !c.includes('月') && !c.includes('日'))) {
            for (let j = idx - 1; j >= 0; j--) {
              if (/^\s*\d+\s*$/.test(runs[j].content) && runs[j].content.trim().length >= 3) {
                if (yearStr) runs[j].text.textContent = yearStr;
                break;
              }
            }
            break;
          }
        }

        // 月份：从"年"之后继续找"月"，其前面的连续数字run
        for (idx = idx + 1; idx < runs.length; idx++) {
          const c = runs[idx].content;
          if (/^\D*月\D*$/.test(c) || (c.includes('月') && !c.includes('年') && !c.includes('日'))) {
            let monthRuns = [];
            for (let j = idx - 1; j >= 0; j--) {
              if (/^\s*\d+\s*$/.test(runs[j].content)) {
                monthRuns.unshift(j);
              } else {
                break;
              }
            }
            if (monthRuns.length > 0 && monthStr) {
              runs[monthRuns[0]].text.textContent = monthStr;
              for (let k = 1; k < monthRuns.length; k++) {
                runs[monthRuns[k]].text.textContent = '';
              }
            }
            break;
          }
        }

        // 日期：从"月"之后找"日"，其前面的数字run
        for (idx = idx + 1; idx < runs.length; idx++) {
          const c = runs[idx].content;
          if (c.includes('日') && !c.includes('月') && !c.includes('年')) {
            for (let j = idx - 1; j >= 0; j--) {
              if (/^\s*\d+\s*$/.test(runs[j].content)) {
                if (dayStr) runs[j].text.textContent = dayStr;
                break;
              }
            }
            break;
          }
        }

        continue;
      }

      // 2b) 税率行（保留格式）
      if (fullText.includes('增值税') && fullText.includes('%')) {
        const taxPct = (taxRate || 13).toFixed(2).replace(/\.00$/, '');
        // 找到包含"%"的 run 并替换
        const runs = getParagraphRuns(p);
        for (let i = 0; i < runs.length; i++) {
          if (runs[i].content.includes('%')) {
            const newContent = runs[i].content.replace(/\d+(?:\.\d+)?%/, taxPct + '%');
            runs[i].text.textContent = newContent;
            break;
          }
        }
        continue;
      }

      // 2c) 货到票到付款天数
      if (fullText.includes('货到票到') && fullText.includes('天内')) {
        const paymentDays = (partyB?.payment_days) || 90;
        const runs = getParagraphRuns(p);
        for (let i = 0; i < runs.length; i++) {
          if (/^\d+$/.test(runs[i].content.trim())) {
            runs[i].text.textContent = String(paymentDays);
            break;
          }
        }
        continue;
      }

      // 2d) 4.1条 供货周期 / 发货天数
      if (fullText.includes('交货时间') && fullText.includes('天内发货')) {
        const days = deliveryDays || 15;
        const runs = getParagraphRuns(p);
        for (let i = 0; i < runs.length; i++) {
          if (/^\d+$/.test(runs[i].content.trim())) {
            runs[i].text.textContent = String(days);
            break;
          }
        }
        continue;
      }

      // 2e) 合同末尾甲方名称（不加下划线，只替换文本）
      if (fullText.includes('甲方（盖章）') || fullText.includes('甲方(盖章)')) {
        const name = partyA?.company_name || '北京同仁堂健康药业（青海）有限公司';
        replaceParagraphSimple(p, '甲方（盖章）：' + name);
        continue;
      }

      // 2f) 合同末尾乙方名称（不加下划线，只替换文本）
      if (fullText.includes('乙方（盖章）') || fullText.includes('乙方(盖章)')) {
        const name = partyB?.full_name || partyB?.name || '';
        replaceParagraphSimple(p, '乙方（盖章）：' + name);
        continue;
      }

      // 2g) 账户名称（付款信息，不加下划线）
      if (fullText.includes('账户名称')) {
        const accName = partyB?.account_name || '';
        replaceParagraphSimple(p, '账户名称：' + accName);
        continue;
      }

      // 2h) 开户行（付款信息，不加下划线）
      if (fullText.includes('开') && fullText.includes('户') && fullText.includes('行') && !fullText.includes('账户名称')) {
        const bank = partyB?.bank || '';
        replaceParagraphSimple(p, '开  户  行：' + bank);
        continue;
      }

      // 2i) 账号（付款信息，不加下划线）
      if (fullText.includes('账') && fullText.includes('号')) {
        const accNo = partyB?.account || '';
        replaceParagraphSimple(p, '账    号：' + accNo);
        continue;
      }
    }

    // ── 3) 处理表格1：甲方 / 乙方信息（保留原模板格式，只改文本） ──
    const tables = doc.getElementsByTagNameNS(W, 'tbl');

    if (tables.length >= 1) {
      const table1 = tables[0];
      const rows1 = table1.getElementsByTagNameNS(W, 'tr');
      if (rows1.length >= 1) {
        const cells1 = rows1[0].getElementsByTagNameNS(W, 'tc');
        if (cells1.length >= 2) {
          // 甲方单元格（7段：公司名、法定代表人、地址、联系人、授权代表、电话、传真）
          // 第0段：甲方公司名称
          setCellParagraphValue(cells1[0], 0, '甲方', partyA?.company_name || '北京同仁堂健康药业（青海）有限公司');
          // 第1段：法定代表人
          setCellParagraphValue(cells1[0], 1, '法定代表人', partyA?.legal_rep || '');
          // 第2段：地址
          setCellParagraphValue(cells1[0], 2, '地址', partyA?.address || '青海省德令哈市河西街道同仁堂路1号');
          // 第3段：联系人
          setCellParagraphValue(cells1[0], 3, '联系人', partyA?.contact || '龙存英');
          // 第4段：授权代表（为空时保留原格式空白）
          setCellParagraphValue(cells1[0], 4, '授权代表', partyA?.auth_rep || '');
          // 第5段：电话
          setCellParagraphValue(cells1[0], 5, '电话', partyA?.phone || '13897764859');
          // 第6段：传真（为空时保留原格式空白）
          setCellParagraphValue(cells1[0], 6, '传真', partyA?.fax || '');

          // 乙方单元格
          setCellParagraphValue(cells1[1], 0, '乙方', partyB?.full_name || partyB?.name || '');
          setCellParagraphValue(cells1[1], 1, '法定代表人', partyB?.legal_rep || '');
          setCellParagraphValue(cells1[1], 2, '地址', partyB?.address || '');
          setCellParagraphValue(cells1[1], 3, '联系人', partyB?.contact || '');
          setCellParagraphValue(cells1[1], 4, '授权代表', partyB?.auth_rep || '');
          setCellParagraphValue(cells1[1], 5, '电话', (partyB?.phone !== undefined && partyB?.phone !== null) ? String(partyB.phone) : '');
          setCellParagraphValue(cells1[1], 6, '传真', partyB?.fax || '');
        }
      }
    }

    // ───────────────────────────────────────
    // 表格2：产品明细（先保存合计行引用，再处理产品，最后统一注入合计金额）
    // ───────────────────────────────────────
    if (tables.length >= 2) {
      const table2 = tables[1];
      // 【关键】转成静态数组，避免插入新行时 live collection 索引混乱
      const allRows = Array.from(table2.getElementsByTagNameNS(W, 'tr'));
      const totalRowsCount = allRows.length;

      // 至少3行：表头 + 1个产品 + 合计
      if (totalRowsCount >= 3) {
        const totalRow = allRows[totalRowsCount - 1];  // 保存合计行引用（最后一行）

        // ── 写入产品数据 ──
        if (products && products.length > 0) {
          // 第1个产品：写入模板已有的第2行
          const templateRow = allRows[1];
          const firstCells = templateRow.getElementsByTagNameNS(W, 'tc');
          const firstFields = [
            products[0].product_name || '',
            products[0].project_no || '',
            products[0].spec || '',
            products[0].unit || '',
            String(products[0].quantity || 0),
            products[0].unit_price ? String(products[0].unit_price) : '',
            (products[0].amount || 0).toFixed(2),
            products[0].remark || '',
          ];
          for (let ci = 0; ci < Math.min(firstCells.length, firstFields.length); ci++) {
            setCellTextSimple(firstCells[ci], firstFields[ci]);
          }

          // 第2个及以后产品：克隆模板行后插入到合计行之前
          if (products.length > 1) {
            for (let pi = 1; pi < products.length; pi++) {
              const p = products[pi];
              const fields = [
                p.product_name || '',
                p.project_no || '',
                p.spec || '',
                p.unit || '',
                String(p.quantity || 0),
                p.unit_price ? String(p.unit_price) : '',
                (p.amount || 0).toFixed(2),
                p.remark || '',
              ];
              const newRow = templateRow.cloneNode(true);
              const newCells = newRow.getElementsByTagNameNS(W, 'tc');
              for (let ci = 0; ci < Math.min(newCells.length, fields.length); ci++) {
                setCellTextSimple(newCells[ci], fields[ci]);
              }
              // 【关键】用已保存的 totalRow 作为插入锚点（不会被 live collection 影响）
              table2.insertBefore(newRow, totalRow);
            }
          }
        }

        // ── 写入合计行（关键修复） ──
        const totalCells = totalRow.getElementsByTagNameNS(W, 'tc');
        if (totalCells.length >= 2) {
          const lowerStr = (totalAmount || 0).toFixed(2);
          const upperStr = totalAmountUpper || '零元整';
          console.log('[合同] 合计金额: ' + lowerStr + ' 元 => 大写: ' + upperStr);

          // cell0: "合计"
          setCellTextSimple(totalCells[0], '合计');

          // cell1: "大写：XX元整   小写：￥XX元整"
          // 【策略】直接重写整个 cell1 文本，保证格式稳定、注入位置精确，
          //        避免因模板内部 run 拆分方式不同导致的漏改
          setCellTextSimple(totalCells[1], '大写：' + upperStr + '   小写：￥' + lowerStr + '元整');
        }
      }
    }

    // ── 序列化并写回 ──
    const serializer = new XMLSerializer();
    const finalXml = serializer.serializeToString(doc);
    fs.writeFileSync(docPath, finalXml, 'utf-8');
  }

  // ── 重新打包 ──
  const outZip = new AdmZip();
  function addDirToZip(dir, zipDir) {
    const files = fs.readdirSync(dir);
    for (const file of files) {
      const fullPath = path.join(dir, file);
      const zipPath = zipDir ? path.join(zipDir, file) : file;
      if (fs.statSync(fullPath).isDirectory()) {
        addDirToZip(fullPath, zipPath);
      } else {
        outZip.addLocalFile(fullPath, zipDir || '');
      }
    }
  }
  addDirToZip(unpackDir, '');
  outZip.writeZip(savePath);

  // 清理临时目录
  try { fs.rmSync(tmpDir, { recursive: true, force: true }); } catch (e) {}

  return { success: true, path: savePath };
}

// ── 数据导入：从旧版数据库迁移 ──
function importFromOldDatabase(oldDbPath) {
  if (!fs.existsSync(oldDbPath)) {
    throw new Error('旧版数据库文件不存在: ' + oldDbPath);
  }

  const initSqlJs = require('sql.js');
  const fileBuffer = fs.readFileSync(oldDbPath);
  const SQL = initSqlJs();
  const oldDb = new SQL.Database(fileBuffer);
  const db = getDatabase();

  const stats = { suppliers: 0, contractSuppliers: 0, memos: 0, collections: 0, plans: 0, packaging: 0, purchase: 0, travel: 0, bom: 0, thirdParty: 0, quotationProducts: 0, quotationSuppliers: 0, quotationConfig: 0, materialLedger: 0, projects: 0 };

  // 导入供应商
  try {
    const stmt = oldDb.prepare('SELECT * FROM suppliers');
    const suppliers = [];
    while (stmt.step()) suppliers.push(stmt.getAsObject());
    stmt.free();
    for (const s of suppliers) {
      db.saveSupplier({
        name: s.name || '',
        cooperation_status: s.cooperation_status || '',
        category: s.category || '',
        contact: s.contact_person || s.contact || '',
        phone: s.phone || '',
        wechat: s.wechat || '',
        inquiry_status: s.quote_status || '',
        sample_status: s.sample_status || '',
        payment_terms: s.payment_method || '',
        invoice_type: s.invoice_type || '',
        tax_rate: s.tax_rate || '',
        remark: s.remark || '',
      });
    }
    stats.suppliers = suppliers.length;
  } catch (e) { console.error('Import suppliers error:', e); }

  // 导入合同供应商
  try {
    const stmt = oldDb.prepare('SELECT * FROM contract_suppliers');
    const csuppliers = [];
    while (stmt.step()) csuppliers.push(stmt.getAsObject());
    stmt.free();
    for (const s of csuppliers) {
      db.saveContractSupplier({
        short_name: s.short_name || '',
        full_name: s.full_name || '',
        legal_rep: s.legal_rep || '',
        address: s.address || '',
        contact: s.contact || '',
        auth_rep: s.auth_rep || '',
        phone: s.phone || '',
        fax: s.fax || '',
        payment_days: s.payment_days || '90',
        payment_method: s.payment_method || '电汇',
        account_name: s.account_name || '',
        bank: s.bank || '',
        account: s.account || '',
        remark: s.remark || '',
      });
    }
    stats.contractSuppliers = csuppliers.length;
  } catch (e) { console.error('Import contract suppliers error:', e); }

  // 导入合同甲方
  try {
    const pa = oldDb.prepare('SELECT * FROM contract_party_a WHERE id=1').getAsObject();
    if (pa) {
      db.saveContractPartyA({
        company_name: pa.company_name || '',
        legal_rep: pa.legal_rep || '',
        address: pa.address || '',
        contact: pa.contact || '',
        phone: pa.phone || '',
      });
    }
  } catch (e) { console.error('Import party A error:', e); }

  // 导入备忘录
  try {
    const stmt = oldDb.prepare('SELECT * FROM memos');
    const memos = [];
    while (stmt.step()) memos.push(stmt.getAsObject());
    stmt.free();
    for (const m of memos) {
      db.saveMemo({
        date: m.date || '',
        project: m.project || '',
        handler: m.handler || '',
        content: m.content || '',
        deadline: m.deadline || '',
        status: m.status || '待处理',
        remark: m.remark || '',
      });
    }
    stats.memos = memos.length;
  } catch (e) { console.error('Import memos error:', e); }

  // 导入催款记录
  try {
    const stmt = oldDb.prepare('SELECT * FROM collection_reminders');
    const collections = [];
    while (stmt.step()) collections.push(stmt.getAsObject());
    stmt.free();
    for (const c of collections) {
      db.saveCollection({
        supplier_name: c.supplier_name || '',
        contact_name: c.contact_person || c.contact_name || '',
        wechat_name: c.wechat || c.wechat_name || '',
        reminder_time: c.reminder_date || c.reminder_time || '',
        amount: c.amount_due || c.amount || 0,
        notify_office: c.notify_internal || c.notify_office || 0,
        notify_manager: c.notify_manager || 0,
        remark: c.remark || '',
      });
    }
    stats.collections = collections.length;
  } catch (e) { console.error('Import collections error:', e); }

  // 导入采购计划
  try {
    const stmt = oldDb.prepare('SELECT * FROM plan_records');
    const plans = [];
    while (stmt.step()) plans.push(stmt.getAsObject());
    stmt.free();
    for (const p of plans) {
      db.savePlanRecord({
        approval_no: p.approval_no || '',
        item_seq: p.item_seq || '',
        name: p.material_name || p.name || '',
        spec: p.spec || '',
        unit: p.unit || '',
        quantity: p.quantity || 0,
        unit_price: p.unit_price || 0,
        total: p.amount || p.total || 0,
        expected_delivery: p.expected_delivery || '',
        remark: p.remark || '',
      });
    }
    stats.plans = plans.length;
  } catch (e) { console.error('Import plans error:', e); }

  // 导入包材下单
  try {
    const stmt = oldDb.prepare('SELECT * FROM packaging_orders');
    const orders = [];
    while (stmt.step()) orders.push(stmt.getAsObject());
    stmt.free();
    for (const o of orders) {
      const qty = parseFloat(o.order_quantity) || 0;
      db.savePackagingOrder({
        order_date: o.compare_date || o.notify_date || o.created_at || '',
        product_name: o.material_name || '',
        project_no: o.project_no || '',
        spec: '',
        quantity: qty,
        unit: '',
        supplier: o.order_factory || '',
        unit_price: o.compare_price || 0,
        total: qty * (o.compare_price || 0) || o.compare_price || 0,
        stage: o.contract_status === '已签订' ? 'contract' : (o.compare_price ? 'compare' : 'inquiry'),
        contract_url: '',
        production_status: o.production_cycle || '',
        shipment_status: o.ship_date || '',
        remark: o.contract_remark || o.compare_remark || '',
      });
    }
    stats.packaging = orders.length;
  } catch (e) { console.error('Import packaging error:', e); }

  // 导入采购垫付
  try {
    const pStmt = oldDb.prepare('SELECT * FROM purchase WHERE archived=0');
    const purchases = [];
    while (pStmt.step()) purchases.push(pStmt.getAsObject());
    pStmt.free();
    for (const p of purchases) {
      const itemsStmt = oldDb.prepare('SELECT * FROM purchase_items WHERE purchase_id=?');
      itemsStmt.bind([p.id]);
      const items = [];
      while (itemsStmt.step()) items.push(itemsStmt.getAsObject());
      itemsStmt.free();
      db.savePurchase({
        date: p.date || '',
        project: p.project || '默认项目',
        handler: p.handler || '',
        payment_method: p.payment_method || '',
        invoice_status: p.invoice_status || '未开票',
        reimbursement_status: p.reimbursement_status || '未报销',
        remark: p.remark || '',
      }, items.map(i => ({
        name: i.name || i.material_name || '',
        spec: i.spec || i.specification || '',
        quantity: i.quantity || 0,
        unit_price: i.unit_price || 0,
        supplier: i.supplier || '',
        total: i.total || i.total_price || 0,
      })));
    }
    stats.purchase = purchases.length;
  } catch (e) { console.error('Import purchase error:', e); }

  // 导入差旅
  try {
    const tStmt = oldDb.prepare('SELECT * FROM travel WHERE archived=0');
    const travels = [];
    while (tStmt.step()) travels.push(tStmt.getAsObject());
    tStmt.free();
    for (const t of travels) {
      const trStmt = oldDb.prepare('SELECT * FROM travel_transport WHERE travel_id=?');
      trStmt.bind([t.id]);
      const transports = [];
      while (trStmt.step()) transports.push(trStmt.getAsObject());
      trStmt.free();

      const hStmt = oldDb.prepare('SELECT * FROM travel_hotel WHERE travel_id=?');
      hStmt.bind([t.id]);
      const hotels = [];
      while (hStmt.step()) hotels.push(hStmt.getAsObject());
      hStmt.free();

      db.saveTravel({
        start_date: t.start_date || '',
        end_date: t.end_date || '',
        purpose: t.reason || t.purpose || '',
        destination: t.destination || '',
        traveler: t.handler || t.traveler || '',
        days: t.duration || t.days || 0,
        reimbursement_status: t.reimbursement_status || '未报销',
        invoice_status: t.invoice_status || '未开票',
      }, transports.map(tr => ({
        transport_type: tr.transport_type || '',
        date: tr.travel_date || tr.transport_date || tr.date || '',
        departure: tr.departure || '',
        arrival: tr.destination || tr.arrival || '',
        amount: tr.amount || 0,
      })), hotels.map(h => ({
        check_in: h.checkin_date || h.check_in_date || h.check_in || '',
        check_out: h.checkout_date || h.check_out_date || h.check_out || '',
        rooms: h.room_count || h.rooms || 1,
        amount: h.amount || 0,
        invoice_status: h.invoice_status || '未开票',
      })));
    }
    stats.travel = travels.length;
  } catch (e) { console.error('Import travel error:', e); }

  // 导入成品BOM
  try {
    const stmt = oldDb.prepare('SELECT * FROM product_bom');
    const boms = [];
    while (stmt.step()) boms.push(stmt.getAsObject());
    stmt.free();
    if (boms.length > 0) {
      db.saveProductBOMBatch(boms.map(b => ({
        finished_project_no: b.finished_project_no || '',
        product_name: b.product_name || '',
        spec: b.spec || '',
        brand: b.brand || '',
        material_project_no: b.material_project_no || '',
        material_name: b.material_name || '',
        quantity: b.quantity || 0,
        unit: b.unit || '',
      })));
    }
    stats.bom = boms.length;
  } catch (e) { console.error('Import BOM error:', e); }

  // 导入三方比价
  try {
    const stmt = oldDb.prepare('SELECT * FROM third_party_records');
    const records = [];
    while (stmt.step()) records.push(stmt.getAsObject());
    stmt.free();
    for (const r of records) {
      db.saveThirdPartyRecord({
        apply_date: r.created_at || '',
        final_supplier: r.final_supplier || '',
        product_name: r.product_name || '',
        project_no: r.item_no || '',
        material_structure: r.material_structure || '',
        spec: r.spec_size || r.spec || '',
        supplier1_name: r.supplier1 || '',
        supplier2_name: r.supplier2 || '',
        supplier3_name: r.supplier3 || '',
        quantity_tier: r.quantity_tier || '',
        price1_tier: r.price1_tier || r.price_tier || '',
        price2_tier: r.price2_tier || '',
        price3_tier: r.price3_tier || '',
      });
    }
    stats.thirdParty = records.length;
  } catch (e) { console.error('Import third party error:', e); }

  // 导入报价产品
  try {
    const stmt = oldDb.prepare('SELECT * FROM quotation_products');
    const products = [];
    while (stmt.step()) products.push(stmt.getAsObject());
    stmt.free();
    for (const p of products) {
      const id = db.saveQuotationProduct({
        project_no: p.item_no || '',
        product_name: p.product_name || '',
        dimensions: p.product_size || '',
        material_process: p.material_process || '',
        lead_time: p.supply_cycle || '',
        carton_spec: p.carton_spec || '',
        unit: p.unit || '',
      });
      // 导入该产品的价格阶梯
      try {
        const tStmt = oldDb.prepare('SELECT * FROM quotation_tiers WHERE product_id = ?');
        tStmt.bind([p.id]);
        const tiers = [];
        while (tStmt.step()) tiers.push(tStmt.getAsObject());
        tStmt.free();
        for (const t of tiers) {
          db.saveQuotationTier({
            product_id: id,
            min_qty: t.min_qty || 0,
            max_qty: t.max_qty || 0,
            price: t.unit_price || 0,
          });
        }
      } catch (e2) { /* ignore */ }
    }
    stats.quotationProducts = products.length;
  } catch (e) { console.error('Import quotation products error:', e); }

  // 导入报价配置
  try {
    const config = oldDb.prepare('SELECT * FROM quotation_config WHERE id = 1').getAsObject();
    if (config) {
      db.updateQuotationConfig({
        buyer_name: config.buyer_name || '',
        buyer_contact: config.buyer_contact || '',
        buyer_phone: config.buyer_phone || '',
        delivery_address: config.buyer_address || '',
        payment_terms: config.payment_terms || '',
        transport_method: config.transport_method || '',
        shipping_docs: config.delivery_docs || '',
        quotation_requirements: config.quote_requirement || '',
        template_notes: config.quote_template_note || '',
        footer_notes: config.footer_note || '',
      });
      stats.quotationConfig = 1;
    }
  } catch (e) { console.error('Import quotation config error:', e); }

  // 导入报价供应商 (合并 quotation_suppliers 和 quotation_supplier 两个表)
  try {
    let allSuppliers = [];
    try {
      const stmt = oldDb.prepare('SELECT * FROM quotation_suppliers');
      while (stmt.step()) allSuppliers.push(stmt.getAsObject());
      stmt.free();
    } catch (e2) { /* ignore */ }
    try {
      const stmt = oldDb.prepare('SELECT * FROM quotation_supplier');
      while (stmt.step()) allSuppliers.push(stmt.getAsObject());
      stmt.free();
    } catch (e2) { /* ignore */ }
    // 按 supplier_name 去重
    const seen = new Set();
    const unique = [];
    for (const s of allSuppliers) {
      if (!seen.has(s.supplier_name)) {
        seen.add(s.supplier_name);
        unique.push(s);
      }
    }
    for (const s of unique) {
      db.saveQuotationSupplierRecord({
        supplier_name: s.supplier_name || '',
        contact: s.contact_person || '',
        phone: s.phone || '',
        address: s.address || '',
        quote_date: s.quote_date || '',
        valid_until: s.quote_validity || '',
      });
    }
    stats.quotationSuppliers = unique.length;
  } catch (e) { console.error('Import quotation suppliers error:', e); }

  // 导入物料台账
  try {
    const stmt = oldDb.prepare('SELECT * FROM material_ledger');
    const rows = [];
    while (stmt.step()) rows.push(stmt.getAsObject());
    stmt.free();
    if (rows.length > 0) {
      db.clearMaterialLedger();
      const batchRows = rows.map(r => ({
        contract_no: r.contract_no || '',
        supplier: r.supplier || '',
        item_no: r.item_no || '',
        material_name: r.material_name || '',
        quantity: parseFloat(r.quantity) || 0,
        unit: r.unit || '',
        unit_price: parseFloat(r.unit_price) || 0,
        amount: parseFloat(r.amount) || 0,
        year: r.year || '',
      }));
      db.saveMaterialLedger(batchRows);
      stats.materialLedger = batchRows.length;
    }
  } catch (e) { console.error('Import material ledger error:', e); }

  // 导入项目
  try {
    const stmt = oldDb.prepare('SELECT * FROM projects');
    const projects = [];
    while (stmt.step()) projects.push(stmt.getAsObject());
    stmt.free();
    for (const p of projects) {
      if (p.name) {
        try { db.addProject(p.name); } catch (e2) { /* ignore duplicates */ }
      }
    }
    stats.projects = projects.length;
  } catch (e) { console.error('Import projects error:', e); }

  // 导入plan_records时保留archived状态
  try {
    // 已经在上面的plan_records导入中完成，这里仅补充archived字段
    // 注意：新版savePlanRecord默认archived=0，需要再手动更新
    const stmt = oldDb.prepare('SELECT * FROM plan_records WHERE archived = 1');
    const archivedPlans = [];
    while (stmt.step()) archivedPlans.push(stmt.getAsObject());
    stmt.free();
    // 由于导入顺序问题，这里通过approval_no+item_seq+name匹配并更新archived状态
    if (archivedPlans.length > 0) {
      const newPlans = db.getPlanRecords(0);
      for (const ap of archivedPlans) {
        for (const np of newPlans) {
          if (np.name === (ap.material_name || ap.name || '') &&
              np.approval_no === (ap.approval_no || '') &&
              np.item_seq === (ap.item_seq || '')) {
            db.archivePlanRecord(np.id); // toggle to archived
            break;
          }
        }
      }
    }
  } catch (e) { console.error('Import plan archive status error:', e); }

  oldDb.close();
  return { stats };
}

// ── 报价单模板导出（基于模板）──
// 参考 V2.2.1 quotation_page.py _generate_excel 逻辑
async function generateQuotationXlsx(params) {
  const { templatePath, savePath, products, config, supplier } = params;
  const ExcelJS = require('exceljs');

  if (!fs.existsSync(templatePath)) {
    throw new Error('报价单模板文件不存在: ' + templatePath);
  }

  const wb = new ExcelJS.Workbook();
  await wb.xlsx.readFile(templatePath);
  const ws = wb.worksheets[0];
  if (!ws) throw new Error('模板中未找到工作表');

  // ── 辅助：写入单元格（处理合并单元格，只写 master）──
  function setCell(row, col, value) {
    const cell = ws.getCell(row, col);
    const target = cell.isMerged ? cell.master : cell;
    target.value = value ?? '';
  }

  // ── 填写需方信息（左侧） ──
  // 模板(1-indexed): F5=需方名称, F7=联系人, F9=联系方式, F11=送货地址
  setCell(5, 6, config?.buyer_name || '北京同仁堂健康药业（青海）有限公司');
  setCell(7, 6, config?.buyer_contact || '');
  setCell(9, 6, config?.buyer_phone ? String(config.buyer_phone) : '');
  setCell(11, 6, config?.buyer_address || '');

  // ── 填写供方信息（右侧） ──
  // 模板(1-indexed): O5=供应商名称, O6=联系人, O7=联系方式, O8=地址, O9=报价日期, O10=有效期
  setCell(5, 15, supplier?.supplier_name || '');
  setCell(6, 15, supplier?.contact_person || supplier?.contact || '');
  setCell(7, 15, supplier?.phone || '');
  setCell(8, 15, supplier?.address || '');
  setCell(9, 15, supplier?.quote_date || '');
  setCell(10, 15, supplier?.quote_validity || supplier?.valid_until || '30天');

  // ── 填写产品数据 ──
  // 模板结构(1-indexed): R14=表头, R15-R18=4行数据区
  // 原始合并: B15:B18, C15:D18, E15:F18, G15:I18, J15:M18, N15:N18, O15:O18 (产品信息纵向合并)
  //           P15:Q15, R15:T15 等 (数量/单价横向合并)
  const DATA_START = 15;
  const DATA_ROWS = 4;

  // 计算所需数据行数
  let totalTiers = 0;
  for (const p of (products || [])) {
    const tiers = p.tiers || [];
    totalTiers += Math.max(1, tiers.length);
  }

  // 如果数据行超过模板4行，需要插入行
  const extraRows = totalTiers - DATA_ROWS;
  if (extraRows > 0) {
    for (let i = 0; i < extraRows; i++) {
      ws.insertRow(DATA_START + DATA_ROWS, [], 'i');
    }
  }

  // 取消数据区所有合并（R15及以后），后续重建
  const toRemoveKeys = [];
  for (const [key, val] of Object.entries(ws._merges)) {
    const range = val.range;
    const start = range.split(':')[0];
    const startRow = parseInt(start.replace(/[A-Z]/g, ''));
    if (startRow >= DATA_START) {
      toRemoveKeys.push(key);
    }
  }
  for (const key of toRemoveKeys) {
    delete ws._merges[key];
  }
  ws.model.merges = ws.model.merges.filter(m => {
    const start = m.split(':')[0];
    const startRow = parseInt(start.replace(/[A-Z]/g, ''));
    return startRow < DATA_START;
  });

  // 清除数据区旧内容（先清除 _cells 缓存，再写 null，再清空缓存确保独立）
  for (let r = DATA_START; r < DATA_START + Math.max(totalTiers, DATA_ROWS); r++) {
    const row = ws.getRow(r);
    if (row._cells) {
      for (let ci = 0; ci < row._cells.length; ci++) {
        const cell = row._cells[ci];
        if (cell && cell.col && cell.col.number >= 2 && cell.col.number <= 20) {
          cell.value = null;
          cell.type = 0; // ValueType.Null
        }
      }
    }
    // 清空 row 缓存，确保后续 getCell 创建独立的 cell
    row._cells = [];
  }

  // 写入产品数据
  let currentRow = DATA_START;
  for (let idx = 0; idx < (products || []).length; idx++) {
    const p = products[idx];
    const tiers = p.tiers || [];
    const tierCount = Math.max(1, tiers.length);
    const productStartRow = currentRow;

    for (let ti = 0; ti < tierCount; ti++) {
      const r = currentRow;
      const tier = tiers[ti] || {};

      if (ti === 0) {
        // 首行写产品信息 — 与模板列对齐
        ws.getCell(r, 2).value = String(idx + 1);                      // B: 序号
        ws.getCell(r, 3).value = p.item_no || p.project_no || '';      // C: 项目号
        ws.getCell(r, 5).value = p.product_name || '';                 // E: 产品名称
        ws.getCell(r, 7).value = p.product_size || p.dimensions || ''; // G: 产品尺寸
        ws.getCell(r, 10).value = p.material_process || '';             // J: 材质/工艺
        ws.getCell(r, 14).value = p.supply_cycle || p.lead_time || ''; // N: 供货周期
        ws.getCell(r, 15).value = p.carton_spec || '';                  // O: 发货箱规
      }

      // 数量 (P列)
      const mn = tier.min_qty || 0;
      const mx = tier.max_qty || 0;
      if (mx) {
        ws.getCell(r, 16).value = `${mn}-${parseInt(mx) - 1}`;
      } else {
        ws.getCell(r, 16).value = mn ? `≥${mn}` : '';
      }
      // 单价 (R列) — 使用 unit_price
      const price = tier.unit_price || tier.price || '';
      ws.getCell(r, 18).value = price !== '' ? Number(price) : '';

      currentRow++;
    }

    // 按产品添加纵向合并（产品信息列）
    if (tierCount > 1) {
      const endRow = productStartRow + tierCount - 1;
      ws.mergeCells(`B${productStartRow}:B${endRow}`);
      ws.mergeCells(`C${productStartRow}:D${endRow}`);
      ws.mergeCells(`E${productStartRow}:F${endRow}`);
      ws.mergeCells(`G${productStartRow}:I${endRow}`);
      ws.mergeCells(`J${productStartRow}:M${endRow}`);
      ws.mergeCells(`N${productStartRow}:N${endRow}`);
      ws.mergeCells(`O${productStartRow}:O${endRow}`);
    }

    // 每行添加横向合并（数量 P:Q, 单价 R:T）
    for (let ti = 0; ti < tierCount; ti++) {
      const r = productStartRow + ti;
      ws.mergeCells(`P${r}:Q${r}`);
      ws.mergeCells(`R${r}:T${r}`);
    }
  }

  // ── 数据区域单元格样式：居中 + 边框 ──
  const dataEndRow = DATA_START + Math.max(totalTiers, DATA_ROWS) - 1;
  const borderStyle = { style: 'thin', color: { argb: 'FF000000' } };
  for (let r = DATA_START; r <= dataEndRow; r++) {
    for (let col = 2; col <= 20; col++) {
      const cell = ws.getCell(r, col);
      cell.alignment = { horizontal: 'center', vertical: 'middle', wrapText: true };
      cell.border = {
        top: borderStyle,
        bottom: borderStyle,
        left: borderStyle,
        right: borderStyle,
      };
    }
  }

  // ── 填写底部条款 ──
  // 模板原始位置(1-indexed): E24=付款方式, E25=运输方式, E26=发货文件, E27=报价要求
  // 如果插入了行，页脚行号也要下移
  const footerOffset = extraRows > 0 ? extraRows : 0;
  setCell(24 + footerOffset, 5, config?.payment_terms || '按协议条件付款；');
  setCell(25 + footerOffset, 5, config?.transport_method || '物料或者专车请提前说明');
  setCell(26 + footerOffset, 5, config?.delivery_docs || '请随货放【发货单】【厂检报告】');
  setCell(27 + footerOffset, 5, config?.quote_requirement || '需含税含运');

  // 写入文件
  await wb.xlsx.writeFile(savePath);

  return { success: true, path: savePath };
}

// ── 比价表模板导出（基于比价表模板.xlsx）──
// 模板结构（1-indexed）：
//   Row 1: 公司名称
//   Row 2: 地址 / 申请时间 (col 7)
//   Row 3: 电话 / 负责人 (col 7)
//   Row 4: 比价表
//   Row 5: 表头 序号|品名|项目号|材质结构|规格尺寸|数量（PCS）|供应商1（￥）|供应商2（￥）|供应商3（￥）
//   Row 6..: 数据行
//   Row 10: 备注
//   Row 12: 最终做货供应商
//   Row 13: 部门主管签字
//   Row 14: 采购复核签字
async function generateCompareXlsx(params) {
  const { templatePath, savePath, record, buyerConfig } = params;
  const ExcelJS = require('exceljs');

  if (!fs.existsSync(templatePath)) {
    throw new Error('比价表模板文件不存在: ' + templatePath);
  }

  const wb = new ExcelJS.Workbook();
  await wb.xlsx.readFile(templatePath);
  const ws = wb.worksheets[0];
  if (!ws) throw new Error('模板中未找到工作表');

  // 辅助：写入单元格
  function setCell(row, col, value) {
    const cell = ws.getCell(row, col);
    const target = cell.isMerged ? cell.master : cell;
    target.value = value ?? '';
  }

  // ── 写入需方信息（如有配置）──
  if (buyerConfig) {
    if (buyerConfig.buyer_name) {
      // Row 1 合并单元格的主格通常是 (1,1)
      setCell(1, 1, buyerConfig.buyer_name);
    }
    if (buyerConfig.buyer_address) {
      setCell(2, 1, '地址：' + buyerConfig.buyer_address);
    }
    if (buyerConfig.buyer_phone) {
      setCell(3, 1, '电话：' + buyerConfig.buyer_phone);
    }
  }

  // ── 申请时间（Row 2, col 8）—— 模板中 col 7 是"申请时间"标签，col 8 为值位置
  if (record?.apply_date) {
    setCell(2, 8, record.apply_date);
  }

  // ── 负责人（Row 3, col 8）—— 模板中 col 7 是"负责人"标签，col 8 为值位置
  setCell(3, 8, '王纪委');

  // ── 表头供应商名称（Row 5，col 7/8/9）
  const s1 = record?.supplier1 || record?.supplier1_name || '';
  const s2 = record?.supplier2 || record?.supplier2_name || '';
  const s3 = record?.supplier3 || record?.supplier3_name || '';
  if (s1) setCell(5, 7, (s1.includes('￥') || s1.includes('供应商') ? s1 : s1 + '（￥）'));
  if (s2) setCell(5, 8, (s2.includes('￥') || s2.includes('供应商') ? s2 : s2 + '（￥）'));
  if (s3) setCell(5, 9, (s3.includes('￥') || s3.includes('供应商') ? s3 : s3 + '（￥）'));

  // ── 数据行（Row 6 开始）
  const DATA_START = 6;
  const qtys = (record?.quantity_tier || '').toString().split(',').filter(x => x !== '' && x !== undefined);
  const prices1 = (record?.price1_tier || '').toString().split(',');
  const prices2 = (record?.price2_tier || '').toString().split(',');
  const prices3 = (record?.price3_tier || '').toString().split(',');
  const maxRows = Math.max(qtys.length, 1);

  // 写入第一行（序号/品名/项目号/材质/规格）——与模板数据起始区对齐
  setCell(DATA_START, 1, 1);
  setCell(DATA_START, 2, record?.product_name || '');
  setCell(DATA_START, 3, record?.item_no || record?.project_no || '');
  setCell(DATA_START, 4, record?.material_structure || '');
  setCell(DATA_START, 5, record?.spec || record?.spec_size || '');

  // 数量阶梯与三供应商价格
  for (let i = 0; i < maxRows; i++) {
    const r = DATA_START + i;
    setCell(r, 6, qtys[i] !== undefined ? qtys[i] : '');
    setCell(r, 7, prices1[i] !== undefined && prices1[i] !== '' ? Number(prices1[i]) : '');
    setCell(r, 8, prices2[i] !== undefined && prices2[i] !== '' ? Number(prices2[i]) : '');
    setCell(r, 9, prices3[i] !== undefined && prices3[i] !== '' ? Number(prices3[i]) : '');
  }

  // 清除模板中多余的示例数据行（从 maxRows 之后到 row 9 的数据列）
  for (let i = maxRows; i < 4; i++) {
    const r = DATA_START + i;
    for (let c = 1; c <= 9; c++) {
      const cell = ws.getCell(r, c);
      if (cell.isMerged && cell.master) {
        // 跳过合并单元格区域（避免破坏上面产品信息的纵向合并）
      } else {
        cell.value = '';
      }
    }
  }

  // ── 最终做货供应商（Row 12, col 7）—— 模板 cols 4-6 是"最终做货供应商"合并标签，col 7 写入值
  if (record?.final_supplier) {
    setCell(12, 7, record.final_supplier);
  }

  // 写入文件
  await wb.xlsx.writeFile(savePath);

  return { success: true, path: savePath };
}

// ── 合同解析（提取产品信息和乙方名称）──
function parseContractDocx(filePath) {
  if (!fs.existsSync(filePath)) {
    throw new Error('合同文件不存在');
  }

  const AdmZip = require('adm-zip');
  const { DOMParser } = require('@xmldom/xmldom');
  const tmpDir = path.join(require('os').tmpdir(), 'contract_parse_' + Date.now());
  const unpackDir = path.join(tmpDir, 'unpacked');
  fs.mkdirSync(unpackDir, { recursive: true });

  try {
    const zip = new AdmZip(filePath);
    zip.extractAllTo(unpackDir, true);

    const docPath = path.join(unpackDir, 'word', 'document.xml');
    if (!fs.existsSync(docPath)) {
      throw new Error('无法读取合同文档内容');
    }

    const docXml = fs.readFileSync(docPath, 'utf-8');
    const parser = new DOMParser();
    const doc = parser.parseFromString(docXml, 'text/xml');
    const W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main';

    const result = {
      product_name: '',
      project_no: '',
      spec: '',
      quantity: '',
      unit: '',
      unit_price: '',
      supplier: '',
      party_a: '',
      contract_no: '',
      contract_date: '',
      total_amount: '',
      delivery_date: '',
      payment_terms: '',
    };

    // 收集所有段落文本（用于提取合同编号、日期、甲乙方等）
    const allParagraphTexts = [];
    const allParagraphs = doc.getElementsByTagNameNS(W, 'p');
    for (let pi = 0; pi < allParagraphs.length; pi++) {
      const p = allParagraphs[pi];
      const tEls = p.getElementsByTagNameNS(W, 't');
      const fullText = Array.from(tEls).map(t => (t.textContent || '').trim()).join('');
      if (fullText && fullText.trim()) allParagraphTexts.push(fullText);
    }

    // 1. 提取产品信息：查找包含产品表格的数据
    const tables = doc.getElementsByTagNameNS(W, 'tbl');
    // 遍历所有表格收集信息
    for (let ti = 0; ti < tables.length; ti++) {
      const table = tables[ti];
      const rows = table.getElementsByTagNameNS(W, 'tr');
      const allRowTexts = [];
      for (let i = 0; i < rows.length; i++) {
        const cells = rows[i].getElementsByTagNameNS(W, 'tc');
        const texts = [];
        for (const cell of cells) {
          const tEls = cell.getElementsByTagNameNS(W, 't');
          const cellText = Array.from(tEls).map(t => (t.textContent || '').trim()).join('');
          texts.push(cellText);
        }
        allRowTexts.push(texts);
      }

      // 尝试识别产品/物料表格
      let headerRowIndex = -1;
      for (let i = 0; i < allRowTexts.length; i++) {
        const rowText = allRowTexts[i].join(' ');
        if (rowText.includes('物料名称') || rowText.includes('产品名称') ||
            rowText.includes('材料结构') || rowText.includes('品名规格') ||
            (rowText.includes('项目号') && (rowText.includes('数量') || rowText.includes('单价')))) {
          headerRowIndex = i;
          break;
        }
      }

      if (headerRowIndex >= 0 && headerRowIndex + 1 < allRowTexts.length) {
        const headerRow = allRowTexts[headerRowIndex];
        const dataRow = allRowTexts[headerRowIndex + 1];

        for (let j = 0; j < headerRow.length; j++) {
          const hdr = headerRow[j].replace(/\s+/g, '');
          const val = dataRow[j] || '';
          if (!result.product_name && (hdr.includes('物料名称') || hdr.includes('产品名称') || hdr.includes('品名'))) {
            result.product_name = val;
          }
          else if (!result.project_no && hdr.includes('项目号')) result.project_no = val;
          else if (!result.spec && (hdr.includes('尺寸') || hdr.includes('规格') || hdr.includes('型号'))) result.spec = val;
          else if (!result.quantity && hdr.includes('数量')) result.quantity = val;
          else if (!result.unit && hdr.includes('单位')) result.unit = val;
          else if (!result.unit_price && hdr.includes('单价')) result.unit_price = val;
        }
        if (result.product_name) break;
      }
    }

    // 2. 遍历段落文本提取其他字段
    for (const text of allParagraphTexts) {
      // 合同编号
      if (!result.contract_no) {
        const m = text.match(/合\s*同\s*编\s*号\s*[：:]\s*(.+)/);
        if (m && m[1].trim() && !m[1].includes('盖章')) result.contract_no = m[1].trim();
      }
      // 合同日期 / 签订日期
      if (!result.contract_date) {
        const m = text.match(/(签订|签订|合同|签订日期|签订时间)\s*(日期)?\s*[：:]\s*(.+)/);
        if (m && m[3]) result.contract_date = m[3].trim();
      }
      if (!result.contract_date) {
        const m = text.match(/(\d{4})\s*[年\-\/]\s*(\d{1,2})\s*[月\-\/]\s*(\d{1,2})\s*日?/);
        if (m) result.contract_date = `${m[1]}-${m[2].padStart(2,'0')}-${m[3].padStart(2,'0')}`;
      }
      // 乙方（供应商）
      if (!result.supplier) {
        const m = text.match(/乙\s*方\s*[：:]\s*(.+)/);
        if (m) {
          const name = m[1].trim();
          if (name && name.length > 2 && !name.includes('盖章') && !name.includes('签字') && !name.includes('地址')) {
            result.supplier = name;
          }
        }
      }
      // 甲方
      if (!result.party_a) {
        const m = text.match(/甲\s*方\s*[：:]\s*(.+)/);
        if (m) {
          const name = m[1].trim();
          if (name && name.length > 2 && !name.includes('盖章') && !name.includes('签字') && !name.includes('地址')) {
            result.party_a = name;
          }
        }
      }
      // 总金额
      if (!result.total_amount) {
        const m = text.match(/(合同)?\s*(总)?\s*(金额|价款|总价|合计)\s*(人民币)?\s*[：:]\s*(.+)/);
        if (m && m[5]) result.total_amount = m[5].trim();
      }
      // 供货期 / 交货日期
      if (!result.delivery_date) {
        const m = text.match(/(供货|交货|交付)\s*(日期|时间|期)?\s*[：:]\s*(.+)/);
        if (m && m[3]) result.delivery_date = m[3].trim();
      }
      // 付款方式
      if (!result.payment_terms) {
        const m = text.match(/(付款|结算)\s*(方式|条件)?\s*[：:]\s*(.+)/);
        if (m && m[3]) result.payment_terms = m[3].trim();
      }
    }

    return result;
  } finally {
    try { fs.rmSync(tmpDir, { recursive: true, force: true }); } catch (e) {}
  }
}

// ── 应用生命周期 ──
// Windows: 必须在 app.whenReady() 之前设置 AppUserModelId
if (process.platform === 'win32') {
  app.setAppUserModelId('com.trt.procurement');
}

app.whenReady().then(() => {
  // 设置应用图标（用于任务栏显示）
  try {
    const iconPath = getAssetPath('icon', 'app-icon-multi.ico');
    cachedAppIcon = nativeImage.createFromPath(iconPath);
    if (cachedAppIcon.isEmpty()) {
      console.warn('[图标] 加载失败: ' + iconPath);
    } else {
      app.setIcon(cachedAppIcon);
      console.log('[图标] 已设置应用图标: ' + iconPath);
    }
  } catch (e) {
    console.error('[图标] 设置应用图标失败:', e);
  }

  // 确保数据目录存在
  const dataDir = getDataDir();
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
  }

  // 初始化数据库
  initDatabase(dataDir);

  // 设置 IPC
  setupIPC();

  // 创建窗口
  createWindow();

  // 创建托盘
  createTray();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    } else if (mainWindow) {
      mainWindow.show();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    // 不退出，保持在托盘
  }
});

app.on('before-quit', () => {
  isQuitting = true;
});
