# 采购助手 V1.0.5

> 企业采购全流程管理系统 — 一线采购从业者自主开发的桌面端工具

## 简介

**采购助手**是采购一线从业者 **EastSeaO** 利用业余时间独立开发的桌面端管理系统。作为日常采购工作的数字化工具，它覆盖了从物料下单、报价比价、合同生成到垫付报销、催款台账等核心业务环节，用代码解决重复劳动，用数据提升采购效率。

传统手工台账和分散的 Excel 文件难以满足采购全流程的跟踪与管理需求，采购助手正是在这一痛点下诞生——不依赖服务器、无需联网，单机即可运行，数据全部本地存储，零部署门槛。

---

## 功能模块

| 模块 | 页面 | 核心功能 |
|------|------|----------|
| 📊 **看板** | dashboard | KPI 实时指标 + 万年历（农历/节气/黄历宜忌）+ 三列动态看板 |
| 📦 **包材下单** | packaging | 物料台账查询 + 包材下单录入 + Excel 导入导出 |
| 📋 **采购计划** | plan | 月度采购计划管理 + 归档 + 批量导出 |
| 💰 **产品报价** | quotation | 产品报价录入 + 多供应商多阶梯报价 + 模板导出报价单 |
| ⚖️ **三方比价** | compare | 三供应商横向比价 + 模板导出比价表 |
| 📄 **合同生成** | contract | 合同供应商/甲方/产品管理 + Word 合同模板一键生成 |
| 🏭 **供应商** | supplier | 供应商分类管理 + 模糊搜索 + 详情编辑 |
| 📖 **物料台账** | query | 全量物料台账检索 + 批量导入 + 导出 |
| 🔧 **成品BOM** | product_bom | 成品 BOM 管理 + Excel 模板导入导出 + 批量新增 |
| 💳 **催款台账** | collection | 催款记录跟踪 + 逾期提醒 + 状态管理 |
| 💸 **采购垫付** | purchase | 垫付记录 + 多物料明细 + 报销状态跟踪 |
| ✈️ **差旅** | travel | 差旅记录 + 交通/住宿明细 + 报销状态 |
| 📝 **备忘录** | memo | 项目备忘 + 状态筛选 + 关键事项提醒 |
| ⚙️ **设置** | settings | 外观主题 + 数据管理 + 旧版导入 + 关于作者 |

---

## 技术架构

| 层级 | 技术 |
|------|------|
| 桌面框架 | **Electron 28.3.3** |
| 渲染层 | 原生 DOM（纯 JavaScript，非 React/Vue） |
| 数据库 | **SQLite**（sql.js WASM 模式，纯浏览器端运行） |
| 文档导出 | ExcelJS / XLSX（报价单/比价表模板导出） |
| 合同生成 | @xmldom/xmldom + adm-zip（Word DOCX 模板引擎） |
| UI 风格 | 自定义 CSS 变量体系（经典蓝 / Win11 原生双主题） |

**架构优势：**
- 🖥️ **零服务器依赖** — 全部数据本地存储，无需联网
- 🔒 **数据安全** — SQLite 本地数据库，不上传任何云端
- ⚡ **开箱即用** — 双击 EXE 即可运行，无需安装依赖
- 🎨 **双主题切换** — 经典蓝 + Win11 原生风格，浅色/深色模式

---

## 安装与使用

### 方式一：安装程序（推荐）

下载 `采购助手 Setup 1.0.5.exe`，双击运行，按提示安装到任意目录。

### 方式二：便携版

下载 `采购助手 1.0.5.exe`，双击即可运行，无需安装。可拷贝到任意位置使用。

### 从旧版导入数据

如果你之前使用 V2.x（Python 版），可在「设置」页面点击「从旧版导入数据」，选择旧版 `procurement.db` 文件即可一键迁移。

---

## 项目结构

```
procurement-system/
├── src/
│   ├── main/
│   │   └── main.js          # Electron 主进程
│   │   └── db.js            # 数据库核心逻辑
│   │   └── ipc-handlers.js  # IPC 通信处理
│   ├── renderer/
│   │   ├── index.html       # 主窗口 HTML
│   │   ├── app.js           # 全局状态管理
│   │   ├── nav.js           # 导航栏
│   │   ├── utils.js         # 工具函数
│   │   ├── theme.js         # 主题系统
│   │   ├── pages/           # 各功能页面
│   │   │   ├── dashboard.js
│   │   │   ├── packaging.js
│   │   │   ├── quotation.js
│   │   │   ├── compare.js
│   │   │   ├── contract.js
│   │   │   ├── supplier.js
│   │   │   ├── collection.js
│   │   │   ├── purchase.js
│   │   │   ├── travel.js
│   │   │   ├── memo.js
│   │   │   ├── plan.js
│   │   │   ├── product_bom.js
│   │   │   ├── query.js
│   │   │   ├── settings.js
│   │   │   └── ... 
│   │   └── styles/
│   │       ├── main.css
│   │       ├── components.css
│   │       ├── pages.css
│   │       └── theme-classic_blue.css
│   │       └── theme-win11.css
│   └── shared/
│       └── constants.js
├── assets/
│   ├── icon/                 # 应用图标
│   ├── author-avatar.png     # 作者头像
│   ├── author2.0.md          # 作者介绍
│   ├── contract_template.docx    # 合同模板
│   ├── 产品包装报价单_模板.xlsx   # 报价单模板
│   ├── 比价表模板.xlsx           # 比价表模板
├── build-hooks/              # electron-builder 钩子
├── preload.js                # 预加载脚本
├── package.json
└── README.md
```

---

## 开发指南

### 环境准备

```bash
# 安装依赖
npm install

# 本地开发运行
npm start

# 打包（便携版 + 安装程序）
npm run dist:win
```

### 技术要点

1. **IPC 通信架构** — preload.js 通过 contextBridge 暴露 `window.electronAPI`，renderer 层通过 IPC 调用主进程能力
2. **数据库操作** — sql.js 在 renderer 层加载 WASM，通过 IPC 将 SQL 操作委托给主进程执行
3. **模板导出** — 报价单/比价表基于 ExcelJS 模板填充，合同基于 DOCX XML 模板替换
4. **主题系统** — CSS 变量驱动，`theme.js` 管理 classic_blue / win11 双主题 + light/dark 双模式

---

## 版本历史

| 版本 | 日期 | 主要变更 |
|------|------|----------|
| V1.0.5 | 2026-06-20 | 设置页作者卡片重构（头像+了解作者弹窗）；版本号从 V3.0.4 调整为 V1.0.5 |
| V3.0.4 | 2026-06 | 自定义标题栏 + 可折叠导航 + 全面 UI 统一 |
| V3.0.3 | 2026-06 | 报价页下拉检索+预览+模板导出；比价页bug修复+导出；合同页命名格式 |
| V3.0.2 | 2026-05 | Electron 首个稳定版，从 Python V2.x 完整重写 |
| V2.2.0 | 2026 | Python + CustomTkinter 版本，功能覆盖完整 |

---

## 关于作者

**EastSeaO** — 目前就职于一家食品集团公司，在采购部从事包装采购业务。

作为一线采购从业者，作者在日常工作中发现传统手工台账、分散的 Excel 文件难以满足采购全流程的跟踪与管理需求。因此，利用业余时间独立自主开发了"采购助手"桌面端管理系统。

如果你对系统功能有任何建议，或者希望合作开发更多定制化功能，欢迎通过微信 **EastSeaO** 与作者交流。

> *"用代码解决重复劳动，用数据提升采购效率。"*

---

## 许可证

本项目仅供内部使用，未对外开源授权。
