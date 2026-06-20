const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // ── 窗口控制 ──
  window: {
    minimize: () => ipcRenderer.invoke('window:minimize'),
    maximize: () => ipcRenderer.invoke('window:maximize'),
    close: () => ipcRenderer.invoke('window:close'),
    isMaximized: () => ipcRenderer.invoke('window:isMaximized'),
  },

  // ── 对话框 ──
  dialog: {
    openFile: (options) => ipcRenderer.invoke('dialog:openFile', options),
    saveFile: (options) => ipcRenderer.invoke('dialog:saveFile', options),
    messageBox: (options) => ipcRenderer.invoke('dialog:messageBox', options),
  },

  // ── 文件操作 ──
  file: {
    read: (filePath) => ipcRenderer.invoke('file:read', filePath),
    write: (filePath, data) => ipcRenderer.invoke('file:write', filePath, data),
    exists: (filePath) => ipcRenderer.invoke('file:exists', filePath),
    getAssetPath: (...parts) => ipcRenderer.invoke('file:getAssetPath', ...parts),
    generateContract: (params) => ipcRenderer.invoke('file:generateContract', params),
    parseContract: (filePath) => ipcRenderer.invoke('file:parseContract', filePath),
    exportQuotation: (params) => ipcRenderer.invoke('file:exportQuotation', params),
    exportCompare: (params) => ipcRenderer.invoke('file:exportCompare', params),
    saveUploadedFile: (params) => ipcRenderer.invoke('file:saveUploadedFile', params),
    generatePlanTemplate: (params) => ipcRenderer.invoke('file:generatePlanTemplate', params),
  },

  // ── Shell ──
  shell: {
    openExternal: (url) => ipcRenderer.invoke('shell:openExternal', url),
  },

  // ── 应用信息 ──
  app: {
    getVersion: () => ipcRenderer.invoke('app:getVersion'),
    checkUpdates: () => ipcRenderer.invoke('app:checkUpdates'),
    getDataPath: () => ipcRenderer.invoke('app:getDataPath'),
    setDataPath: (newPath) => ipcRenderer.invoke('app:setDataPath', newPath),
    getAutoLaunch: () => ipcRenderer.invoke('app:getAutoLaunch'),
    setAutoLaunch: (enabled) => ipcRenderer.invoke('app:setAutoLaunch', enabled),
  },

  // ── 数据库操作 ──
  db: {
    // 采购垫付
    getPurchases: (archived) => ipcRenderer.invoke('db:getPurchases', archived),
    savePurchase: (data, items) => ipcRenderer.invoke('db:savePurchase', data, items),
    updatePurchase: (id, data, items) => ipcRenderer.invoke('db:updatePurchase', id, data, items),
    deletePurchase: (id) => ipcRenderer.invoke('db:deletePurchase', id),
    archivePurchase: (id) => ipcRenderer.invoke('db:archivePurchase', id),

    // 差旅
    getTravels: (archived) => ipcRenderer.invoke('db:getTravels', archived),
    saveTravel: (data, transports, hotels) => ipcRenderer.invoke('db:saveTravel', data, transports, hotels),
    updateTravel: (id, data, transports, hotels) => ipcRenderer.invoke('db:updateTravel', id, data, transports, hotels),
    deleteTravel: (id) => ipcRenderer.invoke('db:deleteTravel', id),
    archiveTravel: (id) => ipcRenderer.invoke('db:archiveTravel', id),

    // 供应商
    getSuppliers: (category, keyword, status) => ipcRenderer.invoke('db:getSuppliers', category, keyword, status),
    getSupplier: (id) => ipcRenderer.invoke('db:getSupplier', id),
    saveSupplier: (data) => ipcRenderer.invoke('db:saveSupplier', data),
    updateSupplier: (id, data) => ipcRenderer.invoke('db:updateSupplier', id, data),
    deleteSupplier: (id) => ipcRenderer.invoke('db:deleteSupplier', id),

    // 催款
    getCollections: (keyword, startDate, endDate) => ipcRenderer.invoke('db:getCollections', keyword, startDate, endDate),
    getCollection: (id) => ipcRenderer.invoke('db:getCollection', id),
    saveCollection: (data) => ipcRenderer.invoke('db:saveCollection', data),
    updateCollection: (id, data) => ipcRenderer.invoke('db:updateCollection', id, data),
    deleteCollection: (id) => ipcRenderer.invoke('db:deleteCollection', id),

    // 备忘录
    getMemos: (keyword, project, status) => ipcRenderer.invoke('db:getMemos', keyword, project, status),
    getMemo: (id) => ipcRenderer.invoke('db:getMemo', id),
    saveMemo: (data) => ipcRenderer.invoke('db:saveMemo', data),
    updateMemo: (id, data) => ipcRenderer.invoke('db:updateMemo', id, data),
    deleteMemo: (id) => ipcRenderer.invoke('db:deleteMemo', id),

    // 物料台账
    getMaterialLedger: (filters) => ipcRenderer.invoke('db:getMaterialLedger', filters),
    saveMaterialLedger: (rows) => ipcRenderer.invoke('db:saveMaterialLedger', rows),
    clearMaterialLedger: () => ipcRenderer.invoke('db:clearMaterialLedger'),

    // 包材下单
    getPackagingOrders: (filters) => ipcRenderer.invoke('db:getPackagingOrders', filters),
    savePackagingOrder: (data) => ipcRenderer.invoke('db:savePackagingOrder', data),
    updatePackagingOrder: (id, data) => ipcRenderer.invoke('db:updatePackagingOrder', id, data),
    deletePackagingOrder: (id) => ipcRenderer.invoke('db:deletePackagingOrder', id),

    // 报价
    getQuotationProducts: () => ipcRenderer.invoke('db:getQuotationProducts'),
    getQuotationProduct: (id) => ipcRenderer.invoke('db:getQuotationProduct', id),
    saveQuotationProduct: (data) => ipcRenderer.invoke('db:saveQuotationProduct', data),
    updateQuotationProduct: (id, data) => ipcRenderer.invoke('db:updateQuotationProduct', id, data),
    deleteQuotationProduct: (id) => ipcRenderer.invoke('db:deleteQuotationProduct', id),
    saveQuotationTier: (data) => ipcRenderer.invoke('db:saveQuotationTier', data),
    deleteQuotationTiers: (productId) => ipcRenderer.invoke('db:deleteQuotationTiers', productId),
    getQuotationConfig: () => ipcRenderer.invoke('db:getQuotationConfig'),
    updateQuotationConfig: (data) => ipcRenderer.invoke('db:updateQuotationConfig', data),
    getAllQuotationSuppliers: () => ipcRenderer.invoke('db:getAllQuotationSuppliers'),
    saveQuotationSupplierRecord: (data) => ipcRenderer.invoke('db:saveQuotationSupplierRecord', data),
    updateQuotationSupplierRecord: (id, data) => ipcRenderer.invoke('db:updateQuotationSupplierRecord', id, data),
    deleteQuotationSupplierRecord: (id) => ipcRenderer.invoke('db:deleteQuotationSupplierRecord', id),

    // 合同
    getContractSuppliers: () => ipcRenderer.invoke('db:getContractSuppliers'),
    getContractPartyA: () => ipcRenderer.invoke('db:getContractPartyA'),
    saveContractSupplier: (data) => ipcRenderer.invoke('db:saveContractSupplier', data),
    updateContractSupplier: (id, data) => ipcRenderer.invoke('db:updateContractSupplier', id, data),
    deleteContractSupplier: (id) => ipcRenderer.invoke('db:deleteContractSupplier', id),
    saveContractPartyA: (data) => ipcRenderer.invoke('db:saveContractPartyA', data),
    getContractProducts: () => ipcRenderer.invoke('db:getContractProducts'),
    saveContractProduct: (data) => ipcRenderer.invoke('db:saveContractProduct', data),
    deleteContractProduct: (id) => ipcRenderer.invoke('db:deleteContractProduct', id),

    // 成品BOM
    getProductBOM: (filters) => ipcRenderer.invoke('db:getProductBOM', filters),
    importProductBOM: (rows) => ipcRenderer.invoke('db:importProductBOM', rows),
    saveProductBOMBatch: (rows) => ipcRenderer.invoke('db:saveProductBOMBatch', rows),
    deleteProductBOM: (id) => ipcRenderer.invoke('db:deleteProductBOM', id),

    // 三方比价
    getThirdPartyRecords: () => ipcRenderer.invoke('db:getThirdPartyRecords'),
    getThirdPartyRecord: (id) => ipcRenderer.invoke('db:getThirdPartyRecord', id),
    saveThirdPartyRecord: (data) => ipcRenderer.invoke('db:saveThirdPartyRecord', data),
    updateThirdPartyRecord: (id, data) => ipcRenderer.invoke('db:updateThirdPartyRecord', id, data),
    deleteThirdPartyRecord: (id) => ipcRenderer.invoke('db:deleteThirdPartyRecord', id),

    // 计划
    getPlanRecords: (archived) => ipcRenderer.invoke('db:getPlanRecords', archived),
    savePlanRecord: (data) => ipcRenderer.invoke('db:savePlanRecord', data),
    updatePlanRecord: (id, data) => ipcRenderer.invoke('db:updatePlanRecord', id, data),
    deletePlanRecord: (id) => ipcRenderer.invoke('db:deletePlanRecord', id),
    archivePlanRecord: (id) => ipcRenderer.invoke('db:archivePlanRecord', id),

    // 项目
    getProjects: () => ipcRenderer.invoke('db:getProjects'),
    addProject: (name) => ipcRenderer.invoke('db:addProject', name),

    // 设置
    getSettings: () => ipcRenderer.invoke('db:getSettings'),
    updateSetting: (key, value) => ipcRenderer.invoke('db:updateSetting', key, value),

    // 导出/导入
    exportToXLSX: (tableName, rows, filePath) => ipcRenderer.invoke('db:exportToXLSX', tableName, rows, filePath),
    importFromOld: (oldDbPath) => ipcRenderer.invoke('db:importFromOld', oldDbPath),
  },

  // ── 文件解析 ──
  parse: {
    xlsxRead: (filePath) => ipcRenderer.invoke('xlsx:read', filePath),
    xlsxWrite: (filePath, sheets) => ipcRenderer.invoke('xlsx:write', filePath, sheets),
    csvRead: (filePath) => ipcRenderer.invoke('csv:read', filePath),
    pdfParse: (filePath) => ipcRenderer.invoke('pdf:parse', filePath),
  },
});
