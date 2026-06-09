# 采购管理系统 V1.9.0

**采购助手 · 北京同仁堂健康药业（青海）有限公司**

面向企业采购部门的桌面应用程序，基于 Python + CustomTkinter + SQLite 技术栈，采用莫兰迪暖色调 UI 设计，支持 Windows 10/11 原生适配。

---

## 功能模块

| 模块 | 说明 |
|------|------|
| 📊 仪表盘 | 关键数据概览、莫兰迪暖色卡片展示 |
| 📦 物料下单 | 包装物料订单创建、Excel 导入 |
| 📋 报价单管理 | 产品报价单创建、编辑、阶梯定价、Excel 导出 |
| 🔍 物料查询 | 物料信息检索、CSV/JSON 导入导出 |
| 🏭 供应商管理 | 供应商信息维护、资质管理 |
| 💰 催款记录 | 付款催收记录管理 |
| 💳 采购垫付 | 采购垫付款项记录 |
| ✈️ 差旅报销 | 差旅费用报销管理 |
| 📝 备忘录 | 工作备忘记录 |
| ⚙️ 设置中心 | 主题切换、开机自启、系统托盘、数据目录 |

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 语言 | Python 3.12+ |
| GUI | CustomTkinter 5.2+ / tkinter |
| 数据库 | SQLite 3 |
| 打包 | PyInstaller 6.0+ |
| Excel | openpyxl 3.1+ |
| 图片 | Pillow 10+ |
| 托盘 | pystray 0.19+ |

---

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/eastseao/procurement-system.git
cd procurement-system
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 运行程序

```bash
python main.py
```

### 4. 打包为 EXE（可选）

```bash
pyinstaller 采购助手V1.7.spec
```

---

## 项目结构

```
├── main.py                  # 主入口（App类、导航路由、系统托盘、置顶）
├── database.py              # 数据库层（15张表CRUD、迁移、导出）
├── version.py               # 版本管理（自动检查GitHub更新）
├── requirements.txt         # Python依赖清单
├── 采购助手V1.7.spec         # PyInstaller打包配置
├── pages/                   # 页面模块
│   ├── dashboard_page.py    # 仪表盘
│   ├── packaging_page.py    # 物料下单
│   ├── quotation_page.py    # 报价单
│   ├── query_page.py        # 物料查询
│   ├── supplier_page.py     # 供应商管理
│   ├── collection_page.py   # 催款记录
│   ├── purchase_page.py     # 采购垫付
│   ├── travel_page.py       # 差旅报销
│   ├── memo_page.py         # 备忘录
│   ├── settings_page.py     # 设置中心
│   └── tangxun_page.py      # 堂训
└── assets/                  # 资源文件
    ├── *.png / *.ico        # 图标、Logo
    ├── *.jpg                # 火漆印
    ├── 产品包装报价单_模板.xlsx # 报价单模板
    └── 物料查询导入模板.csv    # 导入模板
```

---

## 自动版本更新

程序启动时会自动通过 **GitHub Releases API** 检查最新版本。当检测到新版本时，会弹出莫兰迪风格的通知窗口，包含：

- 版本号对比（当前 → 最新）
- 更新日志摘要
- 「前往下载」按钮（打开 GitHub Releases 页面）
- 「暂不更新」按钮

> 版本号定义在 `version.py` 中的 `__version__`，发布新版本时需同步更新。

---

## 配色方案（莫兰迪暖色调）

| 用途 | 色值 | 名称 |
|------|------|------|
| 主色 | `#C1816D` | 陶土色 |
| 主色悬停 | `#A86B58` | 深陶土 |
| 成功色 | `#8FA882` | 鼠尾草绿 |
| 警告色 | `#C9A96E` | 麦色 |
| 危险色 | `#B56A6A` | 暗玫瑰 |
| 背景 | `#F5F0EB` | 暖米白 |
| 卡片 | `#FFFAF5` | 暖白 |
| 侧边栏 | `#F0EBE3` | 暖灰 |

---

## 发布新版本

```bash
# 1. 更新版本号
# 编辑 version.py，修改 __version__ 和 __version_date__

# 2. 提交并打标签
git add .
git commit -m "Release V1.5.1: xxx更新"
git tag v1.5.1
git push origin main --tags

# 3. 在 GitHub 上创建 Release
# 前往 https://github.com/eastseao/procurement-system/releases
# 点击 "Create a new release"，选择标签 v1.5.1，填写更新日志
```

---

## 许可证

© 2026 EastSeaO. All rights reserved.
