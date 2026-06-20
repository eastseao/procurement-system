const initSqlJs = require('sql.js');
const path = require('path');
const fs = require('fs');

let db = null;
let SQL = null;
let dbPath = null;

// 当前时间戳（本地格式）
function now() {
  const d = new Date();
  const pad = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

// ── 保存数据库到磁盘 ──
function saveToDisk() {
  if (db && dbPath) {
    try {
      const data = db.export();
      const buffer = Buffer.from(data);
      fs.writeFileSync(dbPath, buffer);
    } catch (e) {
      console.error('Failed to save database:', e);
    }
  }
}

// ── 查询辅助函数 ──
function queryAll(sql, params = []) {
  try {
    const stmt = db.prepare(sql);
    if (params.length > 0) stmt.bind(params);
    const rows = [];
    while (stmt.step()) {
      rows.push(stmt.getAsObject());
    }
    stmt.free();
    return rows;
  } catch (e) {
    console.error('Query error:', sql, e);
    return [];
  }
}

function queryOne(sql, params = []) {
  const rows = queryAll(sql, params);
  return rows.length > 0 ? rows[0] : null;
}

function execute(sql, params = []) {
  try {
    db.run(sql, params);
    saveToDisk();
    return { lastInsertRowid: 0, changes: db.getRowsModified() };
  } catch (e) {
    console.error('Execute error:', sql, e);
    return { lastInsertRowid: 0, changes: 0 };
  }
}

function insertAndGetId(sql, params = []) {
  try {
    db.run(sql, params);
    const result = queryOne('SELECT last_insert_rowid() as id');
    saveToDisk();
    return result ? result.id : 0;
  } catch (e) {
    console.error('Insert error:', sql, e);
    return 0;
  }
}

// ── 列检测辅助 ──
function hasColumn(table, column) {
  try {
    const stmt = db.prepare(`PRAGMA table_info(${table})`);
    while (stmt.step()) {
      const row = stmt.getAsObject();
      if (row.name === column) { stmt.free(); return true; }
    }
    stmt.free();
    return false;
  } catch (e) {
    return false;
  }
}

function tableExists(table) {
  try {
    const row = queryOne(`SELECT name FROM sqlite_master WHERE type='table' AND name=?`, [table]);
    return !!row;
  } catch (e) {
    return false;
  }
}

function addColumn(table, column, typeDef) {
  if (!hasColumn(table, column)) {
    try {
      db.run(`ALTER TABLE ${table} ADD COLUMN ${column} ${typeDef}`);
    } catch (e) {
      console.error(`Failed to add column ${table}.${column}:`, e);
    }
  }
}

// ── 表重建辅助（列名迁移用） ──
function rebuildTable(table, newDDL, colMap) {
  try {
    // 检查是否有数据
    const countRow = queryOne(`SELECT COUNT(*) as cnt FROM ${table}`);
    const hasData = countRow && countRow.cnt > 0;

    if (hasData && colMap) {
      // 备份 → 重建 → 恢复
      db.run(`CREATE TABLE IF NOT EXISTS ${table}_backup AS SELECT * FROM ${table}`);
      db.run(`DROP TABLE ${table}`);
      db.run(newDDL);

      // 获取旧表中与colMap匹配的列
      const oldCols = Object.keys(colMap);
      const newCols = Object.values(colMap);
      const cols = newCols.join(', ');
      const placeholders = newCols.map(() => '?').join(', ');
      const oldColsStr = oldCols.join(', ');

      try {
        const rows = queryAll(`SELECT ${oldColsStr} FROM ${table}_backup`);
        for (const row of rows) {
          const vals = oldCols.map(c => row[c]);
          db.run(`INSERT INTO ${table}(${cols}) VALUES(${placeholders})`, vals);
        }
      } catch (e) {
        console.error(`Migration data copy failed for ${table}:`, e);
      }
      db.run(`DROP TABLE IF EXISTS ${table}_backup`);
    } else {
      db.run(`DROP TABLE IF EXISTS ${table}`);
      db.run(newDDL);
    }
    saveToDisk();
  } catch (e) {
    console.error(`Failed to rebuild table ${table}:`, e);
    db.run(`DROP TABLE IF EXISTS ${table}_backup`);
  }
}

// ════════════════════════════════════════════════════════
// 数据库迁移引擎
// 以 Python V2.3.2 schema 为权威基准
// ════════════════════════════════════════════════════════
function migrateTables() {
  console.log('[Migrate] Starting database migration...');

  // ── purchase_items: 列名映射 ──
  if (tableExists('purchase_items')) {
    if (hasColumn('purchase_items', 'material_name') && !hasColumn('purchase_items', 'name')) {
      rebuildTable('purchase_items',
        `CREATE TABLE IF NOT EXISTS purchase_items (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          purchase_id INTEGER NOT NULL,
          name TEXT, spec TEXT, quantity REAL, unit_price REAL,
          supplier TEXT, total REAL,
          FOREIGN KEY(purchase_id) REFERENCES purchase(id)
        )`,
        { purchase_id: 'purchase_id', material_name: 'name', specification: 'spec', quantity: 'quantity', unit_price: 'unit_price', total_price: 'total' }
      );
    }
  }

  // ── travel: traveler→handler ──
  if (tableExists('travel') && hasColumn('travel', 'traveler') && !hasColumn('travel', 'handler')) {
    rebuildTable('travel',
      `CREATE TABLE IF NOT EXISTS travel (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reason TEXT NOT NULL, destination TEXT NOT NULL,
        start_date TEXT NOT NULL, end_date TEXT NOT NULL,
        duration INTEGER, handler TEXT,
        invoice_status TEXT NOT NULL DEFAULT '未开票',
        reimbursement_status TEXT NOT NULL DEFAULT '未报销',
        remark TEXT, archived INTEGER DEFAULT 0,
        created_at TEXT DEFAULT ''
      )`,
      { id: 'id', reason: 'reason', destination: 'destination', start_date: 'start_date', end_date: 'end_date',
        duration: 'duration', traveler: 'handler', invoice_status: 'invoice_status',
        reimbursement_status: 'reimbursement_status', remark: 'remark', archived: 'archived', created_at: 'created_at' }
    );
  }

  // ── travel_transport: transport_date→travel_date ──
  if (tableExists('travel_transport') && hasColumn('travel_transport', 'transport_date') && !hasColumn('travel_transport', 'travel_date')) {
    rebuildTable('travel_transport',
      `CREATE TABLE IF NOT EXISTS travel_transport (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        travel_id INTEGER NOT NULL,
        transport_type TEXT, travel_date TEXT, departure TEXT,
        destination TEXT, amount REAL,
        FOREIGN KEY(travel_id) REFERENCES travel(id)
      )`,
      { travel_id: 'travel_id', transport_type: 'transport_type', transport_date: 'travel_date', departure: 'departure', destination: 'destination', amount: 'amount' }
    );
  }

  // ── travel_hotel: check_in_date→checkin_date ──
  if (tableExists('travel_hotel')) {
    const needRebuild = (hasColumn('travel_hotel', 'check_in_date') && !hasColumn('travel_hotel', 'checkin_date'))
      || (hasColumn('travel_hotel', 'check_out_date') && !hasColumn('travel_hotel', 'checkout_date'))
      || (!hasColumn('travel_hotel', 'room_count') && hasColumn('travel_hotel', 'rooms'));
    if (needRebuild) {
      rebuildTable('travel_hotel',
        `CREATE TABLE IF NOT EXISTS travel_hotel (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          travel_id INTEGER NOT NULL,
          checkin_date TEXT, checkout_date TEXT, room_count INTEGER,
          amount REAL, invoice_status TEXT,
          FOREIGN KEY(travel_id) REFERENCES travel(id)
        )`,
        { travel_id: 'travel_id', check_in_date: 'checkin_date', check_out_date: 'checkout_date',
          rooms: 'room_count', amount: 'amount', invoice_status: 'invoice_status' }
      );
    }
  }

  // ── suppliers: contact→contact_person, inquiry_status→quote_status ──
  if (tableExists('suppliers')) {
    const needRebuild = (hasColumn('suppliers', 'contact') && !hasColumn('suppliers', 'contact_person'))
      || (hasColumn('suppliers', 'inquiry_status') && !hasColumn('suppliers', 'quote_status'))
      || (hasColumn('suppliers', 'payment_terms') && !hasColumn('suppliers', 'payment_method'));
    if (needRebuild) {
      rebuildTable('suppliers',
        `CREATE TABLE IF NOT EXISTS suppliers (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL,
          category TEXT,
          main_product TEXT,
          contact_person TEXT,
          phone TEXT,
          wechat TEXT,
          cooperation_status TEXT DEFAULT '接洽中',
          quote_status TEXT,
          sample_status TEXT,
          payment_method TEXT,
          invoice_type TEXT,
          tax_rate TEXT,
          remark TEXT,
          created_at TEXT DEFAULT ''
        )`,
        { id: 'id', name: 'name', category: 'category', contact: 'contact_person',
          phone: 'phone', wechat: 'wechat', cooperation_status: 'cooperation_status',
          inquiry_status: 'quote_status', sample_status: 'sample_status',
          payment_terms: 'payment_method', invoice_type: 'invoice_type',
          tax_rate: 'tax_rate', remark: 'remark', created_at: 'created_at' }
      );
    }
  }

  // ── collection_reminders: contact_name→contact_person, wechat_name→wechat, reminder_time→reminder_date ──
  if (tableExists('collection_reminders')) {
    const needRebuild = (hasColumn('collection_reminders', 'contact_name') && !hasColumn('collection_reminders', 'contact_person'))
      || (hasColumn('collection_reminders', 'wechat_name') && !hasColumn('collection_reminders', 'wechat'))
      || (hasColumn('collection_reminders', 'reminder_time') && !hasColumn('collection_reminders', 'reminder_date'))
      || (hasColumn('collection_reminders', 'amount') && !hasColumn('collection_reminders', 'amount_due'));
    if (needRebuild) {
      rebuildTable('collection_reminders',
        `CREATE TABLE IF NOT EXISTS collection_reminders (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          supplier_name TEXT NOT NULL,
          contact_person TEXT,
          wechat TEXT,
          reminder_date TEXT,
          amount_due REAL,
          notify_internal INTEGER DEFAULT 0,
          notify_manager INTEGER DEFAULT 0,
          remark TEXT,
          created_at TEXT DEFAULT ''
        )`,
        { id: 'id', supplier_name: 'supplier_name', contact_name: 'contact_person',
          wechat_name: 'wechat', reminder_time: 'reminder_date',
          amount: 'amount_due', notify_office: 'notify_internal',
          notify_manager: 'notify_manager', remark: 'remark' }
      );
    }
  }

  // ── quotation_products: project_no→item_no, dimensions→product_size, lead_time→supply_cycle ──
  if (tableExists('quotation_products')) {
    const needRebuild = (hasColumn('quotation_products', 'project_no') && !hasColumn('quotation_products', 'item_no'))
      || (hasColumn('quotation_products', 'dimensions') && !hasColumn('quotation_products', 'product_size'))
      || (hasColumn('quotation_products', 'lead_time') && !hasColumn('quotation_products', 'supply_cycle'));
    if (needRebuild) {
      rebuildTable('quotation_products',
        `CREATE TABLE IF NOT EXISTS quotation_products (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          item_no TEXT,
          product_name TEXT NOT NULL,
          product_size TEXT,
          material_process TEXT,
          supply_cycle TEXT,
          carton_spec TEXT,
          unit TEXT DEFAULT 'PCS',
          created_at TEXT DEFAULT ''
        )`,
        { id: 'id', project_no: 'item_no', product_name: 'product_name',
          dimensions: 'product_size', material_process: 'material_process',
          lead_time: 'supply_cycle', carton_spec: 'carton_spec', unit: 'unit' }
      );
    }
  }

  // ── quotation_tiers: price→unit_price, 补tier_name ──
  if (tableExists('quotation_tiers')) {
    if (hasColumn('quotation_tiers', 'price') && !hasColumn('quotation_tiers', 'unit_price')) {
      rebuildTable('quotation_tiers',
        `CREATE TABLE IF NOT EXISTS quotation_tiers (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          product_id INTEGER NOT NULL,
          tier_name TEXT NOT NULL,
          min_qty INTEGER NOT NULL DEFAULT 0,
          max_qty INTEGER,
          unit_price REAL NOT NULL DEFAULT 0,
          FOREIGN KEY(product_id) REFERENCES quotation_products(id) ON DELETE CASCADE
        )`,
        { product_id: 'product_id', min_qty: 'min_qty', max_qty: 'max_qty', price: 'unit_price' }
      );
      // price映射到unit_price后补tier_name
      if (!hasColumn('quotation_tiers', 'tier_name')) {
        db.run(`ALTER TABLE quotation_tiers ADD COLUMN tier_name TEXT NOT NULL DEFAULT ''`);
      }
    } else {
      addColumn('quotation_tiers', 'tier_name', 'TEXT NOT NULL DEFAULT \'\'');
    }
  }

  // ── quotation_config: delivery_address→buyer_address等 ──
  if (tableExists('quotation_config')) {
    const needRebuild = (hasColumn('quotation_config', 'delivery_address') && !hasColumn('quotation_config', 'buyer_address'))
      || (hasColumn('quotation_config', 'shipping_docs') && !hasColumn('quotation_config', 'delivery_docs'))
      || (hasColumn('quotation_config', 'quotation_requirements') && !hasColumn('quotation_config', 'quote_requirement'))
      || (hasColumn('quotation_config', 'template_notes') && !hasColumn('quotation_config', 'quote_template_note'))
      || (hasColumn('quotation_config', 'footer_notes') && !hasColumn('quotation_config', 'footer_note'));
    if (needRebuild) {
      rebuildTable('quotation_config',
        `CREATE TABLE IF NOT EXISTS quotation_config (
          id INTEGER PRIMARY KEY,
          buyer_name TEXT DEFAULT '北京同仁堂健康药业（青海）有限公司',
          buyer_contact TEXT DEFAULT '龙存英',
          buyer_phone TEXT DEFAULT '13897764859',
          buyer_address TEXT DEFAULT '青海省海西州德令哈市同仁堂路1号',
          payment_terms TEXT DEFAULT '按协议条件付款',
          transport_method TEXT DEFAULT '物料或者专车请提前说明',
          delivery_docs TEXT DEFAULT '请随货放【发货单】【厂检报告】',
          quote_requirement TEXT DEFAULT '需含税含运',
          quote_template_note TEXT DEFAULT '报价单模板由需方提供',
          footer_note TEXT DEFAULT '请写明产品尺寸和详细的材质工艺、发货包装形式、箱规等信息',
          created_at TEXT DEFAULT ''
        )`,
        { id: 'id', buyer_name: 'buyer_name', buyer_contact: 'buyer_contact', buyer_phone: 'buyer_phone',
          delivery_address: 'buyer_address', payment_terms: 'payment_terms',
          transport_method: 'transport_method', shipping_docs: 'delivery_docs',
          quotation_requirements: 'quote_requirement', template_notes: 'quote_template_note',
          footer_notes: 'footer_note' }
      );
    }
  }

  // ── quotation_suppliers: valid_until→quote_validity ──
  if (tableExists('quotation_suppliers')) {
    if (hasColumn('quotation_suppliers', 'valid_until') && !hasColumn('quotation_suppliers', 'quote_validity')) {
      rebuildTable('quotation_suppliers',
        `CREATE TABLE IF NOT EXISTS quotation_suppliers (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          supplier_name TEXT NOT NULL DEFAULT '',
          contact_person TEXT DEFAULT '',
          phone TEXT DEFAULT '',
          address TEXT DEFAULT '',
          quote_date TEXT DEFAULT '',
          quote_validity TEXT DEFAULT '',
          created_at TEXT DEFAULT ''
        )`,
        { id: 'id', supplier_name: 'supplier_name', contact: 'contact_person',
          phone: 'phone', address: 'address', quote_date: 'quote_date',
          valid_until: 'quote_validity' }
      );
    }
  }

  // ── third_party_records: project_no→item_no, supplier1_name→supplier1等 ──
  if (tableExists('third_party_records')) {
    const needRebuild = (hasColumn('third_party_records', 'project_no') && !hasColumn('third_party_records', 'item_no'))
      || (hasColumn('third_party_records', 'supplier1_name') && !hasColumn('third_party_records', 'supplier1'))
      || (hasColumn('third_party_records', 'spec') && !hasColumn('third_party_records', 'spec_size'));
    if (needRebuild) {
      rebuildTable('third_party_records',
        `CREATE TABLE IF NOT EXISTS third_party_records (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          product_name TEXT DEFAULT '',
          item_no TEXT DEFAULT '',
          material_structure TEXT DEFAULT '',
          spec_size TEXT DEFAULT '',
          quantity_tier TEXT DEFAULT '',
          supplier1 TEXT DEFAULT '',
          supplier2 TEXT DEFAULT '',
          supplier3 TEXT DEFAULT '',
          final_supplier TEXT DEFAULT '',
          price1_tier TEXT DEFAULT '',
          price2_tier TEXT DEFAULT '',
          price3_tier TEXT DEFAULT '',
          created_at TEXT DEFAULT '',
          updated_at TEXT DEFAULT ''
        )`,
        { id: 'id', product_name: 'product_name', project_no: 'item_no',
          material_structure: 'material_structure', spec: 'spec_size',
          quantity_tier: 'quantity_tier', supplier1_name: 'supplier1',
          supplier2_name: 'supplier2', supplier3_name: 'supplier3',
          final_supplier: 'final_supplier', price1_tier: 'price1_tier',
          price2_tier: 'price2_tier', price3_tier: 'price3_tier',
          created_at: 'created_at', updated_at: 'updated_at' }
      );
    }
  }

  // ── plan_records: name→material_name, total→amount ──
  if (tableExists('plan_records')) {
    const needRebuild = (hasColumn('plan_records', 'name') && !hasColumn('plan_records', 'material_name'))
      || (hasColumn('plan_records', 'total') && !hasColumn('plan_records', 'amount'));
    if (needRebuild) {
      rebuildTable('plan_records',
        `CREATE TABLE IF NOT EXISTS plan_records (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          approval_no TEXT DEFAULT '',
          item_seq TEXT DEFAULT '',
          material_name TEXT NOT NULL DEFAULT '',
          spec TEXT DEFAULT '',
          quantity REAL DEFAULT 0,
          unit TEXT DEFAULT '',
          unit_price REAL DEFAULT 0,
          amount REAL DEFAULT 0,
          expected_delivery TEXT DEFAULT '',
          remark TEXT DEFAULT '',
          archived INTEGER DEFAULT 0,
          submitted_at TEXT DEFAULT '',
          approved_at TEXT DEFAULT '',
          created_at TEXT DEFAULT ''
        )`,
        { id: 'id', approval_no: 'approval_no', item_seq: 'item_seq',
          name: 'material_name', spec: 'spec', unit: 'unit',
          quantity: 'quantity', unit_price: 'unit_price', total: 'amount',
          expected_delivery: 'expected_delivery', remark: 'remark',
          archived: 'archived', created_at: 'created_at' }
      );
    }
  }

  // ── packaging_orders: product_name→material_name, supplier→order_factory, unit_price→compare_price 等 ──
  if (tableExists('packaging_orders')) {
    const needRebuild = (hasColumn('packaging_orders', 'product_name') && !hasColumn('packaging_orders', 'material_name'))
      || (hasColumn('packaging_orders', 'supplier') && !hasColumn('packaging_orders', 'order_factory'))
      || (hasColumn('packaging_orders', 'unit_price') && !hasColumn('packaging_orders', 'compare_price'));
    if (needRebuild) {
      rebuildTable('packaging_orders',
        `CREATE TABLE IF NOT EXISTS packaging_orders (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          material_name TEXT NOT NULL,
          project TEXT NOT NULL,
          project_no TEXT,
          order_factory TEXT,
          compare_price REAL,
          compare_date TEXT,
          compare_remark TEXT,
          contract_status TEXT,
          contract_remark TEXT,
          notify_date TEXT,
          expected_delivery_date TEXT,
          notify_remark TEXT,
          production_cycle TEXT,
          expected_ship_date TEXT,
          production_remark TEXT,
          ship_date TEXT,
          ship_method TEXT,
          tracking_no TEXT,
          expected_arrival TEXT,
          notify_warehouse INTEGER DEFAULT 0,
          archived INTEGER DEFAULT 0,
          created_at TEXT DEFAULT ''
        )`,
        { id: 'id', product_name: 'material_name', project_no: 'project_no',
          supplier: 'order_factory', unit_price: 'compare_price',
          notify_date: 'notify_date', estimated_ship_date: 'expected_ship_date',
          ship_date: 'ship_date', estimated_arrival: 'expected_arrival',
          contract_status: 'contract_status', created_at: 'created_at' }
      );
    }
  }

  // ── 通用：补齐缺失的 created_at 列 ──
  if (tableExists('suppliers')) addColumn('suppliers', 'created_at', 'TEXT DEFAULT ""');
  if (tableExists('collection_reminders')) addColumn('collection_reminders', 'created_at', 'TEXT DEFAULT ""');
  if (tableExists('memos')) addColumn('memos', 'created_at', 'TEXT DEFAULT ""');
  if (tableExists('quotation_products')) addColumn('quotation_products', 'created_at', 'TEXT DEFAULT ""');
  if (tableExists('quotation_config')) addColumn('quotation_config', 'created_at', 'TEXT DEFAULT ""');
  if (tableExists('quotation_suppliers')) addColumn('quotation_suppliers', 'created_at', 'TEXT DEFAULT ""');
  if (tableExists('product_bom')) addColumn('product_bom', 'created_at', 'TEXT DEFAULT ""');

  // ── suppliers: 补 main_product ──
  if (tableExists('suppliers')) addColumn('suppliers', 'main_product', 'TEXT');

  // ── product_bom: 补 retail_price ──
  if (tableExists('product_bom')) addColumn('product_bom', 'retail_price', 'REAL DEFAULT 0');

  // ── memos: status DEFAULT '待处理' ──
  // (不迁移status默认值，因为ALTER TABLE不设DEFAULT)

  // ── plan_records: 补 submitted_at, approved_at ──
  if (tableExists('plan_records')) {
    addColumn('plan_records', 'submitted_at', "TEXT DEFAULT ''");
    addColumn('plan_records', 'approved_at', "TEXT DEFAULT ''");
  }

  // ── third_party_records: 补 updated_at ──
  if (tableExists('third_party_records')) {
    addColumn('third_party_records', 'updated_at', "TEXT DEFAULT ''");
  }

  // ── quotation_tiers: 补 ON DELETE CASCADE（需重建外键） ──
  // SQLite不支持ALTER CONSTRAINT，需要重建表
  if (tableExists('quotation_tiers') && hasColumn('quotation_tiers', 'unit_price')) {
    const fkRow = queryOne(`SELECT sql FROM sqlite_master WHERE type='table' AND name='quotation_tiers'`);
    if (fkRow && fkRow.sql && !fkRow.sql.includes('ON DELETE CASCADE')) {
      const rows = queryAll('SELECT * FROM quotation_tiers');
      db.run('DROP TABLE IF EXISTS quotation_tiers');
      db.run(`CREATE TABLE IF NOT EXISTS quotation_tiers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        tier_name TEXT NOT NULL,
        min_qty INTEGER NOT NULL DEFAULT 0,
        max_qty INTEGER,
        unit_price REAL NOT NULL DEFAULT 0,
        FOREIGN KEY(product_id) REFERENCES quotation_products(id) ON DELETE CASCADE
      )`);
      for (const row of rows) {
        db.run('INSERT INTO quotation_tiers (product_id, tier_name, min_qty, max_qty, unit_price) VALUES (?, ?, ?, ?, ?)',
          [row.product_id, row.tier_name || '', row.min_qty, row.max_qty, row.unit_price]);
      }
      saveToDisk();
    }
  }

  console.log('[Migrate] Database migration complete.');
}

async function initDatabase(dataDir) {
  SQL = await initSqlJs();
  dbPath = path.join(dataDir, 'procurement.db');

  if (fs.existsSync(dbPath)) {
    const fileBuffer = fs.readFileSync(dbPath);
    db = new SQL.Database(fileBuffer);
  } else {
    db = new SQL.Database();
  }

  db.run('PRAGMA foreign_keys = ON');
  db.run('PRAGMA journal_mode = MEMORY');
  initTables();
  migrateTables();
  saveToDisk();
  return db;
}

// ════════════════════════════════════════════════════════
// 初始化表结构 — 以 Python V2.3.2 为权威基准
// ════════════════════════════════════════════════════════
function initTables() {
  // 1. purchase — 采购垫付主表
  db.run(`CREATE TABLE IF NOT EXISTS purchase (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    project TEXT NOT NULL,
    handler TEXT NOT NULL,
    payment_method TEXT NOT NULL,
    invoice_status TEXT NOT NULL,
    reimbursement_status TEXT NOT NULL,
    remark TEXT,
    archived INTEGER DEFAULT 0,
    created_at TEXT DEFAULT ''
  )`);

  // 2. purchase_items — 采购物料明细
  db.run(`CREATE TABLE IF NOT EXISTS purchase_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    purchase_id INTEGER NOT NULL,
    name TEXT, spec TEXT, quantity REAL, unit_price REAL,
    supplier TEXT, total REAL,
    FOREIGN KEY(purchase_id) REFERENCES purchase(id)
  )`);

  // 3. projects — 自定义项目
  db.run(`CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
  )`);
  db.run(`INSERT OR IGNORE INTO projects(name) VALUES('默认项目')`);
  db.run(`INSERT OR IGNORE INTO projects(name) VALUES('电商新品')`);
  db.run(`INSERT OR IGNORE INTO projects(name) VALUES('传渠项目')`);

  // 4. material_ledger — 物料台账
  db.run(`CREATE TABLE IF NOT EXISTS material_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_no TEXT, supplier TEXT, item_no TEXT, material_name TEXT,
    quantity REAL, unit TEXT, unit_price REAL, amount REAL,
    year TEXT, raw_data TEXT
  )`);

  // 5. packaging_orders — 包材下单表
  db.run(`CREATE TABLE IF NOT EXISTS packaging_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    material_name TEXT NOT NULL,
    project TEXT NOT NULL,
    project_no TEXT,
    order_factory TEXT,
    compare_price REAL,
    compare_date TEXT,
    compare_remark TEXT,
    contract_status TEXT,
    contract_remark TEXT,
    notify_date TEXT,
    expected_delivery_date TEXT,
    notify_remark TEXT,
    production_cycle TEXT,
    expected_ship_date TEXT,
    production_remark TEXT,
    ship_date TEXT,
    ship_method TEXT,
    tracking_no TEXT,
    expected_arrival TEXT,
    notify_warehouse INTEGER DEFAULT 0,
    archived INTEGER DEFAULT 0,
    created_at TEXT DEFAULT ''
  )`);

  // 6. travel — 差旅主表
  db.run(`CREATE TABLE IF NOT EXISTS travel (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reason TEXT NOT NULL,
    destination TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    duration INTEGER,
    handler TEXT,
    invoice_status TEXT NOT NULL,
    reimbursement_status TEXT NOT NULL,
    remark TEXT,
    archived INTEGER DEFAULT 0,
    created_at TEXT DEFAULT ''
  )`);

  // 7. travel_transport — 差旅交通明细
  db.run(`CREATE TABLE IF NOT EXISTS travel_transport (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    travel_id INTEGER NOT NULL,
    transport_type TEXT,
    travel_date TEXT,
    departure TEXT,
    destination TEXT,
    amount REAL,
    FOREIGN KEY(travel_id) REFERENCES travel(id)
  )`);

  // 8. travel_hotel — 差旅住宿明细
  db.run(`CREATE TABLE IF NOT EXISTS travel_hotel (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    travel_id INTEGER NOT NULL,
    checkin_date TEXT,
    checkout_date TEXT,
    room_count INTEGER,
    amount REAL,
    invoice_status TEXT,
    FOREIGN KEY(travel_id) REFERENCES travel(id)
  )`);

  // 9. suppliers — 供应商管理表
  db.run(`CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT,
    main_product TEXT,
    contact_person TEXT,
    phone TEXT,
    wechat TEXT,
    cooperation_status TEXT DEFAULT '接洽中',
    quote_status TEXT,
    sample_status TEXT,
    payment_method TEXT,
    invoice_type TEXT,
    tax_rate TEXT,
    remark TEXT,
    created_at TEXT DEFAULT ''
  )`);

  // 10. collection_reminders — 催款记录表
  db.run(`CREATE TABLE IF NOT EXISTS collection_reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_name TEXT NOT NULL,
    contact_person TEXT,
    wechat TEXT,
    reminder_date TEXT,
    amount_due REAL,
    notify_internal INTEGER DEFAULT 0,
    notify_manager INTEGER DEFAULT 0,
    remark TEXT,
    created_at TEXT DEFAULT ''
  )`);

  // 11. memos — 备忘录表
  db.run(`CREATE TABLE IF NOT EXISTS memos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    project TEXT,
    handler TEXT,
    content TEXT,
    deadline TEXT,
    status TEXT DEFAULT '待处理',
    remark TEXT,
    created_at TEXT DEFAULT ''
  )`);

  // 12. quotation_products — 报价单产品表
  db.run(`CREATE TABLE IF NOT EXISTS quotation_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_no TEXT,
    product_name TEXT NOT NULL,
    product_size TEXT,
    material_process TEXT,
    supply_cycle TEXT,
    carton_spec TEXT,
    unit TEXT DEFAULT 'PCS',
    created_at TEXT DEFAULT ''
  )`);

  // 13. quotation_tiers — 报价单阶梯价格表
  db.run(`CREATE TABLE IF NOT EXISTS quotation_tiers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    tier_name TEXT NOT NULL,
    min_qty INTEGER NOT NULL DEFAULT 0,
    max_qty INTEGER,
    unit_price REAL NOT NULL DEFAULT 0,
    FOREIGN KEY(product_id) REFERENCES quotation_products(id) ON DELETE CASCADE
  )`);

  // 14. quotation_config — 报价单需方配置表
  // 从 party_a.json 提取默认需方信息
  let defaultBuyer = {
    buyer_name: '北京同仁堂健康药业（青海）有限公司',
    buyer_contact: '王维',
    buyer_phone: '18094719236',
    buyer_address: '青海省海西州德令哈市同仁堂路1号',
  };
  try {
    const partyAPath = path.join(__dirname, '..', '..', 'assets', 'party_a.json');
    if (fs.existsSync(partyAPath)) {
      const pa = JSON.parse(fs.readFileSync(partyAPath, 'utf-8'));
      defaultBuyer.buyer_name = pa.company_name || defaultBuyer.buyer_name;
      defaultBuyer.buyer_contact = pa.contact || defaultBuyer.buyer_contact;
      defaultBuyer.buyer_phone = pa.phone || defaultBuyer.buyer_phone;
      defaultBuyer.buyer_address = pa.address || defaultBuyer.buyer_address;
    }
  } catch (e) { /* use defaults */ }

  db.run(`CREATE TABLE IF NOT EXISTS quotation_config (
    id INTEGER PRIMARY KEY,
    buyer_name TEXT DEFAULT '${defaultBuyer.buyer_name.replace(/'/g, "''")}',
    buyer_contact TEXT DEFAULT '${defaultBuyer.buyer_contact.replace(/'/g, "''")}',
    buyer_phone TEXT DEFAULT '${defaultBuyer.buyer_phone.replace(/'/g, "''")}',
    buyer_address TEXT DEFAULT '${defaultBuyer.buyer_address.replace(/'/g, "''")}',
    payment_terms TEXT DEFAULT '按协议条件付款',
    transport_method TEXT DEFAULT '物料或者专车请提前说明',
    delivery_docs TEXT DEFAULT '请随货放【发货单】【厂检报告】',
    quote_requirement TEXT DEFAULT '需含税含运',
    quote_template_note TEXT DEFAULT '报价单模板由需方提供',
    footer_note TEXT DEFAULT '请写明产品尺寸和详细的材质工艺、发货包装形式、箱规等信息',
    created_at TEXT DEFAULT ''
  )`);
  db.run(`INSERT OR IGNORE INTO quotation_config(id) VALUES(1)`);

  // 首次创建时用 party_a.json 覆盖默认值
  const existingConfig = queryOne('SELECT * FROM quotation_config WHERE id = 1');
  if (existingConfig && (!existingConfig.buyer_contact || existingConfig.buyer_contact === '龙存英' || existingConfig.buyer_contact === '')) {
    execute(
      `UPDATE quotation_config SET buyer_name=?, buyer_contact=?, buyer_phone=?, buyer_address=? WHERE id=1`,
      [defaultBuyer.buyer_name, defaultBuyer.buyer_contact, defaultBuyer.buyer_phone, defaultBuyer.buyer_address]
    );
  }

  // 15. quotation_supplier — 报价单供方配置表（单条，向后兼容）
  db.run(`CREATE TABLE IF NOT EXISTS quotation_supplier (
    id INTEGER PRIMARY KEY,
    supplier_name TEXT DEFAULT '',
    contact_person TEXT DEFAULT '',
    phone TEXT DEFAULT '',
    address TEXT DEFAULT '',
    quote_date TEXT DEFAULT '',
    quote_validity TEXT DEFAULT '',
    created_at TEXT DEFAULT ''
  )`);
  db.run(`INSERT OR IGNORE INTO quotation_supplier(id) VALUES(1)`);

  // 16. quotation_suppliers — 报价单供方库（多条）
  db.run(`CREATE TABLE IF NOT EXISTS quotation_suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_name TEXT NOT NULL DEFAULT '',
    contact_person TEXT DEFAULT '',
    phone TEXT DEFAULT '',
    address TEXT DEFAULT '',
    quote_date TEXT DEFAULT '',
    quote_validity TEXT DEFAULT '',
    created_at TEXT DEFAULT ''
  )`);

  // 17. quotation_records — 报价单记录表
  db.run(`CREATE TABLE IF NOT EXISTS quotation_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_name TEXT DEFAULT '',
    product_ids TEXT DEFAULT '',
    product_names TEXT DEFAULT '',
    product_count INTEGER DEFAULT 0,
    excel_path TEXT DEFAULT '',
    created_at TEXT DEFAULT ''
  )`);

  // 18. third_party_records — 三方比价记录表
  db.run(`CREATE TABLE IF NOT EXISTS third_party_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT DEFAULT '',
    item_no TEXT DEFAULT '',
    material_structure TEXT DEFAULT '',
    spec_size TEXT DEFAULT '',
    quantity_tier TEXT DEFAULT '',
    supplier1 TEXT DEFAULT '',
    supplier2 TEXT DEFAULT '',
    supplier3 TEXT DEFAULT '',
    final_supplier TEXT DEFAULT '',
    price1_tier TEXT DEFAULT '',
    price2_tier TEXT DEFAULT '',
    price3_tier TEXT DEFAULT '',
    created_at TEXT DEFAULT '',
    updated_at TEXT DEFAULT ''
  )`);

  // 19. contract_suppliers — 合同供应商表
  db.run(`CREATE TABLE IF NOT EXISTS contract_suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    short_name TEXT DEFAULT '',
    full_name TEXT DEFAULT '',
    legal_rep TEXT DEFAULT '',
    address TEXT DEFAULT '',
    contact TEXT DEFAULT '',
    auth_rep TEXT DEFAULT '',
    phone TEXT DEFAULT '',
    fax TEXT DEFAULT '',
    payment_days TEXT DEFAULT '90',
    payment_method TEXT DEFAULT '电汇',
    account_name TEXT DEFAULT '',
    bank TEXT DEFAULT '',
    account TEXT DEFAULT '',
    remark TEXT DEFAULT '',
    created_at TEXT DEFAULT ''
  )`);

  // 20. contract_party_a — 合同甲方配置表
  db.run(`CREATE TABLE IF NOT EXISTS contract_party_a (
    id INTEGER PRIMARY KEY DEFAULT 1,
    company_name TEXT DEFAULT '北京同仁堂健康药业（青海）有限公司',
    legal_rep TEXT DEFAULT '施能文',
    address TEXT DEFAULT '',
    contact TEXT DEFAULT '龙存英',
    phone TEXT DEFAULT '13897764859'
  )`);
  db.run(`INSERT OR IGNORE INTO contract_party_a(id) VALUES(1)`);

  // 21. contract_products — 合同产品记录表（JS新增，保留）
  db.run(`CREATE TABLE IF NOT EXISTS contract_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_no TEXT,
    product_name TEXT,
    project_no TEXT,
    material_structure TEXT,
    spec TEXT,
    unit TEXT,
    quantity REAL,
    unit_price REAL,
    amount REAL,
    remark TEXT,
    created_at TEXT DEFAULT ''
  )`);

  // 22. product_bom — 成品BOM表
  db.run(`CREATE TABLE IF NOT EXISTS product_bom (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    finished_project_no TEXT NOT NULL,
    product_name TEXT,
    spec TEXT,
    retail_price REAL DEFAULT 0,
    brand TEXT,
    material_project_no TEXT NOT NULL,
    material_name TEXT,
    quantity REAL DEFAULT 0,
    unit TEXT DEFAULT '',
    created_at TEXT DEFAULT ''
  )`);

  // 23. plan_records — 采购计划表
  db.run(`CREATE TABLE IF NOT EXISTS plan_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    approval_no TEXT DEFAULT '',
    item_seq TEXT DEFAULT '',
    material_name TEXT NOT NULL DEFAULT '',
    spec TEXT DEFAULT '',
    quantity REAL DEFAULT 0,
    unit TEXT DEFAULT '',
    unit_price REAL DEFAULT 0,
    amount REAL DEFAULT 0,
    expected_delivery TEXT DEFAULT '',
    remark TEXT DEFAULT '',
    archived INTEGER DEFAULT 0,
    submitted_at TEXT DEFAULT '',
    approved_at TEXT DEFAULT '',
    created_at TEXT DEFAULT ''
  )`);

  // 24. settings — 键值对设置存储表（JS新增，保留）
  db.run(`CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
  )`);
}

// ════════════════════════════════════════════════════════
// getDatabase() — 全部CRUD方法
// 字段名已统一为 Python V2.3.2 基准
// ════════════════════════════════════════════════════════
function getDatabase() {
  return {
    // ══════════════════════════════════════════════════
    // 采购垫付
    // ══════════════════════════════════════════════════
    getPurchases(archived = 0) {
      const purchases = queryAll('SELECT * FROM purchase WHERE archived = ? ORDER BY date DESC', [archived]);
      return purchases.map(p => ({
        ...p,
        items: queryAll('SELECT * FROM purchase_items WHERE purchase_id = ?', [p.id]),
        total: queryOne('SELECT COALESCE(SUM(total),0) as s FROM purchase_items WHERE purchase_id = ?', [p.id]).s,
      }));
    },

    getPurchase(id) {
      const p = queryOne('SELECT * FROM purchase WHERE id = ?', [id]);
      if (p) {
        p.items = queryAll('SELECT * FROM purchase_items WHERE purchase_id = ?', [id]);
        p.total = queryOne('SELECT COALESCE(SUM(total),0) as s FROM purchase_items WHERE purchase_id = ?', [id]).s;
      }
      return p;
    },

    savePurchase(data, items) {
      const id = insertAndGetId(
        'INSERT INTO purchase (date, project, handler, payment_method, invoice_status, reimbursement_status, remark, archived) VALUES (?, ?, ?, ?, ?, ?, ?, 0)',
        [data.date, data.project, data.handler, data.payment_method, data.invoice_status, data.reimbursement_status, data.remark || '']
      );
      if (items && items.length > 0) {
        for (const item of items) {
          execute(
            'INSERT INTO purchase_items (purchase_id, name, spec, quantity, unit_price, supplier, total) VALUES (?, ?, ?, ?, ?, ?, ?)',
            [id, item.name, item.spec, item.quantity, item.unit_price, item.supplier, item.total]
          );
        }
      }
      return id;
    },

    updatePurchase(id, data, items) {
      execute(
        'UPDATE purchase SET date=?, project=?, handler=?, payment_method=?, invoice_status=?, reimbursement_status=?, remark=? WHERE id=?',
        [data.date, data.project, data.handler, data.payment_method, data.invoice_status, data.reimbursement_status, data.remark || '', id]
      );
      execute('DELETE FROM purchase_items WHERE purchase_id = ?', [id]);
      if (items && items.length > 0) {
        for (const item of items) {
          execute(
            'INSERT INTO purchase_items (purchase_id, name, spec, quantity, unit_price, supplier, total) VALUES (?, ?, ?, ?, ?, ?, ?)',
            [id, item.name, item.spec, item.quantity, item.unit_price, item.supplier, item.total]
          );
        }
      }
    },

    deletePurchase(id) {
      execute('DELETE FROM purchase_items WHERE purchase_id = ?', [id]);
      execute('DELETE FROM purchase WHERE id = ?', [id]);
    },

    archivePurchase(id) {
      execute('UPDATE purchase SET archived = 1 WHERE id = ?', [id]);
    },

    // ══════════════════════════════════════════════════
    // 差旅报销
    // ══════════════════════════════════════════════════
    getTravels(archived = 0) {
      const travels = queryAll('SELECT * FROM travel WHERE archived = ? ORDER BY start_date DESC', [archived]);
      return travels.map(t => {
        const transports = queryAll('SELECT * FROM travel_transport WHERE travel_id = ?', [t.id]);
        const hotels = queryAll('SELECT * FROM travel_hotel WHERE travel_id = ?', [t.id]);
        const tTotal = transports.reduce((s, r) => s + (r.amount || 0), 0);
        const hTotal = hotels.reduce((s, r) => s + (r.amount || 0), 0);
        return { ...t, transports, hotels, total: tTotal + hTotal };
      });
    },

    getTravel(id) {
      const t = queryOne('SELECT * FROM travel WHERE id = ?', [id]);
      if (t) {
        t.transports = queryAll('SELECT * FROM travel_transport WHERE travel_id = ?', [id]);
        t.hotels = queryAll('SELECT * FROM travel_hotel WHERE travel_id = ?', [id]);
        t.total = t.transports.reduce((s, r) => s + (r.amount || 0), 0) + t.hotels.reduce((s, r) => s + (r.amount || 0), 0);
      }
      return t;
    },

    saveTravel(data, transports, hotels) {
      const id = insertAndGetId(
        'INSERT INTO travel (reason, destination, start_date, end_date, duration, handler, invoice_status, reimbursement_status, archived, remark) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)',
        [data.reason, data.destination, data.start_date, data.end_date, data.duration || 0, data.handler, data.invoice_status, data.reimbursement_status, data.remark || '']
      );
      if (transports && transports.length > 0) {
        for (const t of transports) {
          execute('INSERT INTO travel_transport (travel_id, transport_type, travel_date, departure, destination, amount) VALUES (?, ?, ?, ?, ?, ?)',
            [id, t.transport_type, t.travel_date, t.departure, t.destination, t.amount]);
        }
      }
      if (hotels && hotels.length > 0) {
        for (const h of hotels) {
          execute('INSERT INTO travel_hotel (travel_id, checkin_date, checkout_date, room_count, amount, invoice_status) VALUES (?, ?, ?, ?, ?, ?)',
            [id, h.checkin_date, h.checkout_date, h.room_count, h.amount, h.invoice_status || '未开票']);
        }
      }
      return id;
    },

    updateTravel(id, data, transports, hotels) {
      execute(
        'UPDATE travel SET reason=?, destination=?, start_date=?, end_date=?, duration=?, handler=?, invoice_status=?, reimbursement_status=?, remark=? WHERE id=?',
        [data.reason, data.destination, data.start_date, data.end_date, data.duration || 0, data.handler, data.invoice_status, data.reimbursement_status, data.remark || '', id]
      );
      execute('DELETE FROM travel_transport WHERE travel_id = ?', [id]);
      execute('DELETE FROM travel_hotel WHERE travel_id = ?', [id]);
      if (transports && transports.length > 0) {
        for (const t of transports) {
          execute('INSERT INTO travel_transport (travel_id, transport_type, travel_date, departure, destination, amount) VALUES (?, ?, ?, ?, ?, ?)',
            [id, t.transport_type, t.travel_date, t.departure, t.destination, t.amount]);
        }
      }
      if (hotels && hotels.length > 0) {
        for (const h of hotels) {
          execute('INSERT INTO travel_hotel (travel_id, checkin_date, checkout_date, room_count, amount, invoice_status) VALUES (?, ?, ?, ?, ?, ?)',
            [id, h.checkin_date, h.checkout_date, h.room_count, h.amount, h.invoice_status || '未开票']);
        }
      }
    },

    deleteTravel(id) {
      execute('DELETE FROM travel_transport WHERE travel_id = ?', [id]);
      execute('DELETE FROM travel_hotel WHERE travel_id = ?', [id]);
      execute('DELETE FROM travel WHERE id = ?', [id]);
    },

    archiveTravel(id) {
      execute('UPDATE travel SET archived = 1 WHERE id = ?', [id]);
    },

    // ══════════════════════════════════════════════════
    // 供应商
    // ══════════════════════════════════════════════════
    getSuppliers(category, keyword, status) {
      let sql = 'SELECT * FROM suppliers WHERE 1=1';
      const params = [];
      if (category) { sql += ' AND category = ?'; params.push(category); }
      if (keyword) { sql += ' AND (name LIKE ? OR contact_person LIKE ?)'; params.push(`%${keyword}%`, `%${keyword}%`); }
      if (status) { sql += ' AND cooperation_status = ?'; params.push(status); }
      sql += ' ORDER BY id DESC';
      return queryAll(sql, params);
    },

    getSupplier(id) {
      return queryOne('SELECT * FROM suppliers WHERE id = ?', [id]);
    },

    saveSupplier(data) {
      return insertAndGetId(
        'INSERT INTO suppliers (name, cooperation_status, category, main_product, contact_person, phone, wechat, quote_status, sample_status, payment_method, invoice_type, tax_rate, remark) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        [data.name, data.cooperation_status || '接洽中', data.category || '', data.main_product || '', data.contact_person || '', data.phone || '', data.wechat || '', data.quote_status || '', data.sample_status || '', data.payment_method || '', data.invoice_type || '', data.tax_rate || '', data.remark || '']
      );
    },

    updateSupplier(id, data) {
      execute(
        'UPDATE suppliers SET name=?, cooperation_status=?, category=?, main_product=?, contact_person=?, phone=?, wechat=?, quote_status=?, sample_status=?, payment_method=?, invoice_type=?, tax_rate=?, remark=? WHERE id=?',
        [data.name, data.cooperation_status || '接洽中', data.category || '', data.main_product || '', data.contact_person || '', data.phone || '', data.wechat || '', data.quote_status || '', data.sample_status || '', data.payment_method || '', data.invoice_type || '', data.tax_rate || '', data.remark || '', id]
      );
    },

    deleteSupplier(id) {
      execute('DELETE FROM suppliers WHERE id = ?', [id]);
    },

    // ══════════════════════════════════════════════════
    // 催款记录
    // ══════════════════════════════════════════════════
    getCollections(keyword, startDate, endDate) {
      let sql = 'SELECT * FROM collection_reminders WHERE 1=1';
      const params = [];
      if (keyword) { sql += ' AND (supplier_name LIKE ? OR contact_person LIKE ? OR wechat LIKE ?)'; params.push(`%${keyword}%`, `%${keyword}%`, `%${keyword}%`); }
      if (startDate) { sql += ' AND reminder_date >= ?'; params.push(startDate); }
      if (endDate) { sql += ' AND reminder_date <= ?'; params.push(endDate); }
      sql += ' ORDER BY reminder_date DESC';
      return queryAll(sql, params);
    },

    getCollection(id) {
      return queryOne('SELECT * FROM collection_reminders WHERE id = ?', [id]);
    },

    saveCollection(data) {
      return insertAndGetId(
        'INSERT INTO collection_reminders (supplier_name, contact_person, wechat, reminder_date, amount_due, notify_internal, notify_manager, remark) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        [data.supplier_name, data.contact_person || '', data.wechat || '', data.reminder_date, data.amount_due, data.notify_internal || 0, data.notify_manager || 0, data.remark || '']
      );
    },

    updateCollection(id, data) {
      execute(
        'UPDATE collection_reminders SET supplier_name=?, contact_person=?, wechat=?, reminder_date=?, amount_due=?, notify_internal=?, notify_manager=?, remark=? WHERE id=?',
        [data.supplier_name, data.contact_person || '', data.wechat || '', data.reminder_date, data.amount_due, data.notify_internal || 0, data.notify_manager || 0, data.remark || '', id]
      );
    },

    deleteCollection(id) {
      execute('DELETE FROM collection_reminders WHERE id = ?', [id]);
    },

    // ══════════════════════════════════════════════════
    // 备忘录
    // ══════════════════════════════════════════════════
    getMemos(keyword, project, status) {
      let sql = 'SELECT * FROM memos WHERE 1=1';
      const params = [];
      if (keyword) { sql += ' AND (content LIKE ? OR handler LIKE ? OR remark LIKE ?)'; params.push(`%${keyword}%`, `%${keyword}%`, `%${keyword}%`); }
      if (project) { sql += ' AND project = ?'; params.push(project); }
      if (status) { sql += ' AND status = ?'; params.push(status); }
      sql += ' ORDER BY date DESC';
      return queryAll(sql, params);
    },

    getMemo(id) {
      return queryOne('SELECT * FROM memos WHERE id = ?', [id]);
    },

    saveMemo(data) {
      return insertAndGetId(
        'INSERT INTO memos (date, project, handler, content, deadline, status, remark) VALUES (?, ?, ?, ?, ?, ?, ?)',
        [data.date, data.project, data.handler, data.content, data.deadline, data.status || '待处理', data.remark || '']
      );
    },

    updateMemo(id, data) {
      execute(
        'UPDATE memos SET date=?, project=?, handler=?, content=?, deadline=?, status=?, remark=? WHERE id=?',
        [data.date, data.project, data.handler, data.content, data.deadline, data.status || '待处理', data.remark || '', id]
      );
    },

    deleteMemo(id) {
      execute('DELETE FROM memos WHERE id = ?', [id]);
    },

    // ══════════════════════════════════════════════════
    // 物料台账
    // ══════════════════════════════════════════════════
    getMaterialLedger(filters = {}) {
      let sql = 'SELECT * FROM material_ledger WHERE 1=1';
      const params = [];
      if (filters.year) { sql += ' AND year = ?'; params.push(filters.year); }
      if (filters.supplier) { sql += ' AND supplier LIKE ?'; params.push(`%${filters.supplier}%`); }
      if (filters.material_name) { sql += ' AND material_name LIKE ?'; params.push(`%${filters.material_name}%`); }
      if (filters.item_no) { sql += ' AND item_no = ?'; params.push(filters.item_no); }
      sql += ' ORDER BY contract_no';
      return queryAll(sql, params);
    },

    saveMaterialLedger(rows) {
      execute('DELETE FROM material_ledger');
      for (const row of rows) {
        execute(
          'INSERT INTO material_ledger (contract_no, supplier, item_no, material_name, quantity, unit, unit_price, amount, year, raw_data) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
          [row.contract_no, row.supplier, row.item_no, row.material_name, row.quantity, row.unit, row.unit_price, row.amount, row.year, row.raw_data || '']
        );
      }
    },

    clearMaterialLedger() {
      execute('DELETE FROM material_ledger');
    },

    // ══════════════════════════════════════════════════
    // 包材下单
    // ══════════════════════════════════════════════════
    getPackagingOrders(filters = {}) {
      let sql = 'SELECT * FROM packaging_orders WHERE 1=1';
      const params = [];
      if (filters.archived !== undefined) { sql += ' AND archived = ?'; params.push(filters.archived); }
      if (filters.keyword) { sql += ' AND (material_name LIKE ? OR order_factory LIKE ? OR project_no LIKE ?)'; params.push(`%${filters.keyword}%`, `%${filters.keyword}%`, `%${filters.keyword}%`); }
      sql += ' ORDER BY id DESC';
      return queryAll(sql, params);
    },

    getPackagingOrder(id) {
      return queryOne('SELECT * FROM packaging_orders WHERE id = ?', [id]);
    },

    getPackagingFactories() {
      return queryAll('SELECT DISTINCT order_factory FROM packaging_orders WHERE order_factory IS NOT NULL AND order_factory != \'\' ORDER BY order_factory');
    },

    savePackagingOrder(data) {
      return insertAndGetId(
        'INSERT INTO packaging_orders (material_name, project, project_no, order_factory, compare_price, compare_date, compare_remark, contract_status, contract_remark, notify_date, expected_delivery_date, notify_remark, production_cycle, expected_ship_date, production_remark, ship_date, ship_method, tracking_no, expected_arrival, notify_warehouse) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        [data.material_name, data.project || '', data.project_no || '', data.order_factory || '', data.compare_price || 0, data.compare_date || '', data.compare_remark || '', data.contract_status || '', data.contract_remark || '', data.notify_date || '', data.expected_delivery_date || '', data.notify_remark || '', data.production_cycle || '', data.expected_ship_date || '', data.production_remark || '', data.ship_date || '', data.ship_method || '', data.tracking_no || '', data.expected_arrival || '', data.notify_warehouse || 0]
      );
    },

    updatePackagingOrder(id, data) {
      execute(
        'UPDATE packaging_orders SET material_name=?, project=?, project_no=?, order_factory=?, compare_price=?, compare_date=?, compare_remark=?, contract_status=?, contract_remark=?, notify_date=?, expected_delivery_date=?, notify_remark=?, production_cycle=?, expected_ship_date=?, production_remark=?, ship_date=?, ship_method=?, tracking_no=?, expected_arrival=?, notify_warehouse=? WHERE id=?',
        [data.material_name, data.project || '', data.project_no || '', data.order_factory || '', data.compare_price || 0, data.compare_date || '', data.compare_remark || '', data.contract_status || '', data.contract_remark || '', data.notify_date || '', data.expected_delivery_date || '', data.notify_remark || '', data.production_cycle || '', data.expected_ship_date || '', data.production_remark || '', data.ship_date || '', data.ship_method || '', data.tracking_no || '', data.expected_arrival || '', data.notify_warehouse || 0, id]
      );
    },

    deletePackagingOrder(id) {
      execute('DELETE FROM packaging_orders WHERE id = ?', [id]);
    },

    archivePackagingOrder(id) {
      execute('UPDATE packaging_orders SET archived = 1 WHERE id = ?', [id]);
    },

    // ══════════════════════════════════════════════════
    // 报价单
    // ══════════════════════════════════════════════════
    getQuotationProducts() {
      const products = queryAll('SELECT * FROM quotation_products ORDER BY id');
      return products.map(p => ({
        ...p,
        tiers: queryAll('SELECT * FROM quotation_tiers WHERE product_id = ? ORDER BY min_qty', [p.id]),
      }));
    },

    getQuotationProduct(id) {
      const p = queryOne('SELECT * FROM quotation_products WHERE id = ?', [id]);
      if (p) p.tiers = queryAll('SELECT * FROM quotation_tiers WHERE product_id = ? ORDER BY min_qty', [id]);
      return p;
    },

    saveQuotationProduct(data) {
      return insertAndGetId(
        'INSERT INTO quotation_products (item_no, product_name, product_size, material_process, supply_cycle, carton_spec, unit) VALUES (?, ?, ?, ?, ?, ?, ?)',
        [data.item_no || '', data.product_name, data.product_size || '', data.material_process || '', data.supply_cycle || '', data.carton_spec || '', data.unit || 'PCS']
      );
    },

    updateQuotationProduct(id, data) {
      execute(
        'UPDATE quotation_products SET item_no=?, product_name=?, product_size=?, material_process=?, supply_cycle=?, carton_spec=?, unit=? WHERE id=?',
        [data.item_no || '', data.product_name, data.product_size || '', data.material_process || '', data.supply_cycle || '', data.carton_spec || '', data.unit || 'PCS', id]
      );
    },

    deleteQuotationProduct(id) {
      execute('DELETE FROM quotation_tiers WHERE product_id = ?', [id]);
      execute('DELETE FROM quotation_products WHERE id = ?', [id]);
    },

    saveQuotationTier(data) {
      return insertAndGetId(
        'INSERT INTO quotation_tiers (product_id, tier_name, min_qty, max_qty, unit_price) VALUES (?, ?, ?, ?, ?)',
        [data.product_id, data.tier_name || '', data.min_qty, data.max_qty, data.unit_price]
      );
    },

    deleteQuotationTiers(productId) {
      execute('DELETE FROM quotation_tiers WHERE product_id = ?', [productId]);
    },

    getQuotationConfig() {
      return queryOne('SELECT * FROM quotation_config WHERE id = 1');
    },

    updateQuotationConfig(data) {
      execute(
        'UPDATE quotation_config SET buyer_name=?, buyer_contact=?, buyer_phone=?, buyer_address=?, payment_terms=?, transport_method=?, delivery_docs=?, quote_requirement=?, quote_template_note=?, footer_note=? WHERE id=1',
        [data.buyer_name || '', data.buyer_contact || '', data.buyer_phone || '', data.buyer_address || '', data.payment_terms || '', data.transport_method || '', data.delivery_docs || '', data.quote_requirement || '', data.quote_template_note || '', data.footer_note || '']
      );
    },

    // 报价单供方配置（单条，向后兼容）
    getQuotationSupplier() {
      return queryOne('SELECT * FROM quotation_supplier WHERE id = 1');
    },

    updateQuotationSupplier(data) {
      execute(
        'UPDATE quotation_supplier SET supplier_name=?, contact_person=?, phone=?, address=?, quote_date=?, quote_validity=? WHERE id=1',
        [data.supplier_name || '', data.contact_person || '', data.phone || '', data.address || '', data.quote_date || '', data.quote_validity || '']
      );
    },

    // 报价单供方库（多条）
    getAllQuotationSuppliers() {
      return queryAll('SELECT * FROM quotation_suppliers ORDER BY id');
    },

    saveQuotationSupplierRecord(data) {
      return insertAndGetId(
        'INSERT INTO quotation_suppliers (supplier_name, contact_person, phone, address, quote_date, quote_validity) VALUES (?, ?, ?, ?, ?, ?)',
        [data.supplier_name, data.contact_person || '', data.phone || '', data.address || '', data.quote_date || '', data.quote_validity || '']
      );
    },

    updateQuotationSupplierRecord(id, data) {
      execute(
        'UPDATE quotation_suppliers SET supplier_name=?, contact_person=?, phone=?, address=?, quote_date=?, quote_validity=? WHERE id=?',
        [data.supplier_name, data.contact_person || '', data.phone || '', data.address || '', data.quote_date || '', data.quote_validity || '', id]
      );
    },

    deleteQuotationSupplierRecord(id) {
      execute('DELETE FROM quotation_suppliers WHERE id = ?', [id]);
    },

    // 报价单记录
    getQuotationRecords() {
      return queryAll('SELECT * FROM quotation_records ORDER BY id DESC');
    },

    getQuotationRecord(id) {
      return queryOne('SELECT * FROM quotation_records WHERE id = ?', [id]);
    },

    saveQuotationRecord(data) {
      return insertAndGetId(
        'INSERT INTO quotation_records (supplier_name, product_ids, product_names, product_count, excel_path) VALUES (?, ?, ?, ?, ?)',
        [data.supplier_name || '', data.product_ids || '', data.product_names || '', data.product_count || 0, data.excel_path || '']
      );
    },

    updateQuotationRecordPath(id, excelPath) {
      execute('UPDATE quotation_records SET excel_path=? WHERE id=?', [excelPath, id]);
    },

    deleteQuotationRecord(id) {
      execute('DELETE FROM quotation_records WHERE id = ?', [id]);
    },

    // ══════════════════════════════════════════════════
    // 合同
    // ══════════════════════════════════════════════════
    getContractSuppliers() {
      return queryAll('SELECT * FROM contract_suppliers ORDER BY id');
    },

    getContractPartyA() {
      return queryOne('SELECT * FROM contract_party_a WHERE id = 1');
    },

    saveContractSupplier(data) {
      return insertAndGetId(
        'INSERT INTO contract_suppliers (short_name, full_name, legal_rep, address, contact, auth_rep, phone, fax, payment_days, payment_method, account_name, bank, account, remark) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        [data.short_name, data.full_name || '', data.legal_rep || '', data.address || '', data.contact || '', data.auth_rep || '', data.phone || '', data.fax || '', data.payment_days || '90', data.payment_method || '电汇', data.account_name || '', data.bank || '', data.account || '', data.remark || '']
      );
    },

    updateContractSupplier(id, data) {
      execute(
        'UPDATE contract_suppliers SET short_name=?, full_name=?, legal_rep=?, address=?, contact=?, auth_rep=?, phone=?, fax=?, payment_days=?, payment_method=?, account_name=?, bank=?, account=?, remark=? WHERE id=?',
        [data.short_name, data.full_name || '', data.legal_rep || '', data.address || '', data.contact || '', data.auth_rep || '', data.phone || '', data.fax || '', data.payment_days || '90', data.payment_method || '电汇', data.account_name || '', data.bank || '', data.account || '', data.remark || '', id]
      );
    },

    deleteContractSupplier(id) {
      execute('DELETE FROM contract_suppliers WHERE id = ?', [id]);
    },

    saveContractPartyA(data) {
      execute('DELETE FROM contract_party_a WHERE id = 1');
      execute(
        'INSERT INTO contract_party_a (id, company_name, legal_rep, address, contact, phone) VALUES (1, ?, ?, ?, ?, ?)',
        [data.company_name, data.legal_rep || '', data.address || '', data.contact || '', data.phone || '']
      );
    },

    // 合同产品记录（JS新增，保留）
    getContractProducts() {
      return queryAll('SELECT * FROM contract_products ORDER BY id DESC');
    },

    saveContractProduct(data) {
      return insertAndGetId(
        'INSERT INTO contract_products (contract_no, product_name, project_no, material_structure, spec, unit, quantity, unit_price, amount, remark) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        [data.contract_no || '', data.product_name || '', data.project_no || '', data.material_structure || '', data.spec || '', data.unit || '', data.quantity || 0, data.unit_price || 0, data.amount || 0, data.remark || '']
      );
    },

    deleteContractProduct(id) {
      execute('DELETE FROM contract_products WHERE id = ?', [id]);
    },

    // ══════════════════════════════════════════════════
    // 成品BOM
    // ══════════════════════════════════════════════════
    getProductBOM(filters = {}) {
      let sql = 'SELECT * FROM product_bom WHERE 1=1';
      const params = [];
      if (filters.product_name) { sql += ' AND product_name LIKE ?'; params.push(`%${filters.product_name}%`); }
      if (filters.finished_project_no) { sql += ' AND finished_project_no LIKE ?'; params.push(`%${filters.finished_project_no}%`); }
      if (filters.material_project_no) { sql += ' AND material_project_no LIKE ?'; params.push(`%${filters.material_project_no}%`); }
      if (filters.material_name) { sql += ' AND material_name LIKE ?'; params.push(`%${filters.material_name}%`); }
      sql += ' ORDER BY finished_project_no, id';
      return queryAll(sql, params);
    },

    saveProductBOM(data) {
      return insertAndGetId(
        'INSERT INTO product_bom (finished_project_no, product_name, spec, retail_price, brand, material_project_no, material_name, quantity, unit) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
        [data.finished_project_no, data.product_name || '', data.spec || '', data.retail_price || 0, data.brand || '', data.material_project_no, data.material_name || '', data.quantity || 0, data.unit || '']
      );
    },

    updateProductBOM(id, data) {
      execute(
        'UPDATE product_bom SET finished_project_no=?, product_name=?, spec=?, retail_price=?, brand=?, material_project_no=?, material_name=?, quantity=?, unit=? WHERE id=?',
        [data.finished_project_no, data.product_name || '', data.spec || '', data.retail_price || 0, data.brand || '', data.material_project_no, data.material_name || '', data.quantity || 0, data.unit || '', id]
      );
    },

    saveProductBOMBatch(rows) {
      for (const row of rows) {
        insertAndGetId(
          'INSERT INTO product_bom (finished_project_no, product_name, spec, retail_price, brand, material_project_no, material_name, quantity, unit) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
          [row.finished_project_no, row.product_name || '', row.spec || '', row.retail_price || 0, row.brand || '', row.material_project_no, row.material_name || '', row.quantity || 0, row.unit || '']
        );
      }
    },

    importProductBOM(rows) {
      return this.saveProductBOMBatch(rows);
    },

    deleteProductBOM(id) {
      execute('DELETE FROM product_bom WHERE id = ?', [id]);
    },

    // ══════════════════════════════════════════════════
    // 三方比价
    // ══════════════════════════════════════════════════
    getThirdPartyRecords() {
      return queryAll('SELECT * FROM third_party_records ORDER BY created_at DESC');
    },

    getThirdPartyRecord(id) {
      return queryOne('SELECT * FROM third_party_records WHERE id = ?', [id]);
    },

    saveThirdPartyRecord(data) {
      return insertAndGetId(
        'INSERT INTO third_party_records (product_name, item_no, material_structure, spec_size, quantity_tier, supplier1, supplier2, supplier3, final_supplier, price1_tier, price2_tier, price3_tier) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        [data.product_name || '', data.item_no || '', data.material_structure || '', data.spec_size || '', data.quantity_tier, data.supplier1 || '', data.supplier2 || '', data.supplier3 || '', data.final_supplier || '', data.price1_tier, data.price2_tier, data.price3_tier]
      );
    },

    updateThirdPartyRecord(id, data) {
      execute(
        'UPDATE third_party_records SET product_name=?, item_no=?, material_structure=?, spec_size=?, quantity_tier=?, supplier1=?, supplier2=?, supplier3=?, final_supplier=?, price1_tier=?, price2_tier=?, price3_tier=?, updated_at=? WHERE id=?',
        [data.product_name || '', data.item_no || '', data.material_structure || '', data.spec_size || '', data.quantity_tier, data.supplier1 || '', data.supplier2 || '', data.supplier3 || '', data.final_supplier || '', data.price1_tier, data.price2_tier, data.price3_tier, now(), id]
      );
    },

    deleteThirdPartyRecord(id) {
      execute('DELETE FROM third_party_records WHERE id = ?', [id]);
    },

    // ══════════════════════════════════════════════════
    // 采购计划
    // ══════════════════════════════════════════════════
    getPlanRecords(archived = 0) {
      return queryAll('SELECT * FROM plan_records WHERE archived = ? ORDER BY id', [archived]);
    },

    getPlanRecord(id) {
      return queryOne('SELECT * FROM plan_records WHERE id = ?', [id]);
    },

    savePlanRecord(data) {
      return insertAndGetId(
        'INSERT INTO plan_records (approval_no, item_seq, material_name, spec, unit, quantity, unit_price, amount, expected_delivery, remark, archived) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)',
        [data.approval_no || '', data.item_seq || '', data.material_name, data.spec || '', data.unit || '', data.quantity, data.unit_price || 0, data.amount || 0, data.expected_delivery || '', data.remark || '']
      );
    },

    updatePlanRecord(id, data) {
      execute(
        'UPDATE plan_records SET approval_no=?, item_seq=?, material_name=?, spec=?, unit=?, quantity=?, unit_price=?, amount=?, expected_delivery=?, remark=? WHERE id=?',
        [data.approval_no || '', data.item_seq || '', data.material_name, data.spec || '', data.unit || '', data.quantity, data.unit_price || 0, data.amount || 0, data.expected_delivery || '', data.remark || '', id]
      );
    },

    deletePlanRecord(id) {
      execute('DELETE FROM plan_records WHERE id = ?', [id]);
    },

    archivePlanRecord(id) {
      execute('UPDATE plan_records SET archived = 1 WHERE id = ?', [id]);
    },

    // ══════════════════════════════════════════════════
    // 项目
    // ══════════════════════════════════════════════════
    getProjects() {
      return queryAll('SELECT * FROM projects ORDER BY id').map(r => r.name);
    },

    addProject(name) {
      try {
        execute('INSERT INTO projects (name) VALUES (?)', [name]);
        return true;
      } catch (e) { return false; }
    },

    // ══════════════════════════════════════════════════
    // 设置
    // ══════════════════════════════════════════════════
    getSettings() {
      const rows = queryAll('SELECT key, value FROM settings');
      const settings = {};
      rows.forEach(r => { settings[r.key] = r.value; });
      return settings;
    },

    updateSetting(key, value) {
      execute('INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = ?', [key, String(value), String(value)]);
    },

    // ══════════════════════════════════════════════════
    // 导出
    // ══════════════════════════════════════════════════
    // 参数：tableName, rows, filePath, columnMap（可选：{ 英文字段: 中文标签 }）
    exportToXLSX(tableName, rows, filePath, columnMap) {
      try {
        const XLSX = require('xlsx');
        let exportRows = rows;
        // 如果提供了列映射，将字段名转为中文标签
        if (columnMap && typeof columnMap === 'object' && Object.keys(columnMap).length > 0) {
          exportRows = rows.map(r => {
            const newRow = {};
            for (const [key, label] of Object.entries(columnMap)) {
              if (r[key] !== undefined) newRow[label] = r[key];
            }
            return newRow;
          });
        }
        const ws = XLSX.utils.json_to_sheet(exportRows);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, tableName);
        XLSX.writeFile(wb, filePath);
        return { success: true };
      } catch (e) {
        return { success: false, error: e.message };
      }
    },
  };
}

module.exports = { initDatabase, getDatabase };
