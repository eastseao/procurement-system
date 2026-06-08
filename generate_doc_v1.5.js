const fs = require('fs');
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, 
        Header, Footer, AlignmentType, LevelFormat, ExternalHyperlink,
        InternalHyperlink, PageNumber, PageBreak, HeadingLevel, BorderStyle, 
        WidthType, ShadingType, VerticalAlign, TableOfContents, Column, 
        SectionType, TabStopType, TabStopPosition } = require('docx');

const doc = new Document({
  styles: {
    default: { 
      document: { run: { font: "Microsoft YaHei", size: 22 } } 
    },
    paragraphStyles: [
      { 
        id: "Heading1", 
        name: "Heading 1", 
        basedOn: "Normal", 
        next: "Normal", 
        quickFormat: true,
        run: { size: 32, bold: true, font: "Microsoft YaHei", color: "2E75B6" },
        paragraph: { spacing: { before: 480, after: 240 }, outlineLevel: 0 } 
      },
      { 
        id: "Heading2", 
        name: "Heading 2", 
        basedOn: "Normal", 
        next: "Normal", 
        quickFormat: true,
        run: { size: 28, bold: true, font: "Microsoft YaHei", color: "5B9BD5" },
        paragraph: { spacing: { before: 360, after: 180 }, outlineLevel: 1 } 
      },
      { 
        id: "Heading3", 
        name: "Heading 3", 
        basedOn: "Normal", 
        next: "Normal", 
        quickFormat: true,
        run: { size: 24, bold: true, font: "Microsoft YaHei", color: "70AD47" },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 2 } 
      },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: {
          width: 12240,   // A4 width in DXA
          height: 15840   // A4 height in DXA
        },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    children: [
      // 标题页
      new Paragraph({
        heading: HeadingLevel.HEADING_1,
        children: [new TextRun({ text: "采购管理系统", bold: true, size: 48 })],
        alignment: AlignmentType.CENTER,
        spacing: { before: 2880, after: 480 }
      }),
      new Paragraph({
        children: [new TextRun({ text: "开发者文档 V1.5", bold: true, size: 36 })],
        alignment: AlignmentType.CENTER,
        spacing: { after: 240 }
      }),
      new Paragraph({
        children: [new TextRun({ text: "采购助手 · 北京同仁堂健康药业（青海）有限公司", size: 24 })],
        alignment: AlignmentType.CENTER,
        spacing: { after: 480 }
      }),
      new Paragraph({
        children: [new TextRun({ text: "© 2026 EastSeaO", size: 20, color: "666666" })],
        alignment: AlignmentType.CENTER,
        spacing: { after: 1440 }
      }),
      
      new Paragraph({ children: [new PageBreak()] }),
      
      // 目录
      new TableOfContents("目录", { hyperlink: true, headingStyleRange: "1-3" }),
      
      new Paragraph({ children: [new PageBreak()] }),
      
      // 第一章：系统概述
      new Paragraph({
        heading: HeadingLevel.HEADING_1,
        children: [new TextRun("系统概述")]
      }),
      
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("系统简介")]
      }),
      
      new Paragraph({
        children: [new TextRun("采购管理系统是一款面向企业采购部门的桌面应用程序，基于 Python + CustomTkinter + SQLite 技术栈开发。系统采用莫兰迪暖色调 UI 设计，支持 Windows 10/11 原生适配，提供从物料管理、供应商管理到采购垫付、差旅报销的全流程数字化管理。")],
        spacing: { after: 240 }
      }),
      
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("主要功能")]
      }),
      
      new Paragraph({
        children: [new TextRun("• 物料管理：物料信息查询、新增、编辑、导入导出")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("• 物料下单：创建包装物料订单，支持 Excel 导入")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("• 报价单管理：产品报价单创建、编辑、导出 Excel")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("• 供应商管理：供应商信息维护、资质管理")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("• 催款记录：付款催收记录管理")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("• 采购垫付：采购垫付款项记录")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("• 差旅报销：差旅费用报销管理")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("• 备忘录：工作备忘记录")],
        spacing: { after: 240 }
      }),
      
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("技术栈")]
      }),
      
      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [3120, 6240],
        rows: [
          new TableRow({
            children: [
              new TableCell({
                shading: { fill: "2E75B6", type: ShadingType.CLEAR },
                children: [new Paragraph({ children: [new TextRun({ text: "技术层", bold: true, color: "FFFFFF" })] })],
                width: { size: 3120, type: WidthType.DXA }
              }),
              new TableCell({
                shading: { fill: "2E75B6", type: ShadingType.CLEAR },
                children: [new Paragraph({ children: [new TextRun({ text: "技术选型", bold: true, color: "FFFFFF" })] })],
                width: { size: 6240, type: WidthType.DXA }
              })
            ]
          }),
          new TableRow({
            children: [
              new TableCell({
                children: [new Paragraph({ children: [new TextRun("前端框架")] })],
                width: { size: 3120, type: WidthType.DXA }
              }),
              new TableCell({
                children: [new Paragraph({ children: [new TextRun("CustomTkinter (CTk)")] })],
                width: { size: 6240, type: WidthType.DXA }
              })
            ]
          }),
          new TableRow({
            children: [
              new TableCell({
                children: [new Paragraph({ children: [new TextRun("后端语言")] })],
                width: { size: 3120, type: WidthType.DXA }
              }),
              new TableCell({
                children: [new Paragraph({ children: [new TextRun("Python 3.12+")] })],
                width: { size: 6240, type: WidthType.DXA }
              })
            ]
          }),
          new TableRow({
            children: [
              new TableCell({
                children: [new Paragraph({ children: [new TextRun("数据库")] })],
                width: { size: 3120, type: WidthType.DXA }
              }),
              new TableCell({
                children: [new Paragraph({ children: [new TextRun("SQLite 3")] })],
                width: { size: 6240, type: WidthType.DXA }
              })
            ]
          }),
          new TableRow({
            children: [
              new TableCell({
                children: [new Paragraph({ children: [new TextRun("打包工具")] })],
                width: { size: 3120, type: WidthType.DXA }
              }),
              new TableCell({
                children: [new Paragraph({ children: [new TextRun("PyInstaller")] })],
                width: { size: 6240, type: WidthType.DXA }
              })
            ]
          }),
          new TableRow({
            children: [
              new TableCell({
                children: [new Paragraph({ children: [new TextRun("UI 配色")] })],
                width: { size: 3120, type: WidthType.DXA }
              }),
              new TableCell({
                children: [new Paragraph({ children: [new TextRun("莫兰迪暖色调")] })],
                width: { size: 6240, type: WidthType.DXA }
              })
            ]
          })
        ]
      }),
      
      new Paragraph({ children: [new PageBreak()] }),
      
      // 第二章：V1.5 版本更新内容
      new Paragraph({
        heading: HeadingLevel.HEADING_1,
        children: [new TextRun("V1.5 版本更新内容")]
      }),
      
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("UI 优化")]
      }),
      
      new Paragraph({
        children: [new TextRun("1. 按钮配色统一：所有页面的右上方按钮统一采用莫兰迪暖色配色方案，与报价单页面保持一致。")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("2. 信息框风格统一：所有页面的信息显示框采用统一的视觉风格，提升用户体验一致性。")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("3. 表格 UI 统一：物料下单和报价单页面下方的信息框表格 UI 与物料查询页面风格统一。")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("4. 添加按钮统一：所有页面的添加按钮统一放置在按钮区域的最左侧，配色统一使用莫兰迪红色（#B56A6A）。")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("5. 设置页面布局优化：设置页面从通栏卡片布局改为左侧分类导航、右侧设置项卡片的左右分栏格式，解决卡片太宽的问题。")],
        spacing: { after: 240 }
      }),
      
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("功能增强")]
      }),
      
      new Paragraph({
        children: [new TextRun("1. 数据存放位置设置：设置页面增加数据存放位置设置项，支持自定义 procurement.db 的存放位置，可通过浏览按钮选择文件夹，保存设置时自动迁移已有数据库文件。")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("2. 堂训页面：新增堂训页面，点击导航栏顶部的 Logo 可跳转到堂训页面，展示北京同仁堂的品牌渊源、对联、古训（两个必不敢）、企业精神、自律准则、制药特色和经营理念。")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("3. 版本介绍和作者信息：设置页面中的\"关于\"改为\"版本介绍\"，新增\"作者\"板块，介绍作者信息和联系方式。")],
        spacing: { after: 240 }
      }),
      
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("Bug 修复")]
      }),
      
      new Paragraph({
        children: [new TextRun("1. 修复物料下单和报价单页面打不开的问题：原因是缺少 import tkinter as tk，已添加。")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("2. 修复 settings_icon 未定义错误：在使用前添加 settings_icon = self._nav_icon_images.get(\"settings\")。")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("3. 修复 main.py 中的多处语法错误。")],
        spacing: { after: 240 }
      }),
      
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("界面优化")]
      }),
      
      new Paragraph({
        children: [new TextRun("1. 导航栏图标更新：重新设计导航栏的各导航图标，更加大气简洁。")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("2. 采购垫付图标：使用金币图标。")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("3. 差旅报销图标：使用飞机图标。")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("4. 置顶按钮放大：顶部的"固定窗口到最前"按钮放大，居中对齐。")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("5. 折叠按钮放大：最下方的折叠按钮放大 50%。")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("6. 导航栏顶部添加 Logo：在置顶按钮下方添加居中显示的 Logo，宽高 40×40 与导航图标一致。")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("7. 标题栏配色统一：程序最上方的标题栏配色与下方页面保持一致。")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("8. exe 图标更新：程序 exe 的图标文件使用同仁堂企业 LOGO2.png。")],
        spacing: { after: 240 }
      }),
      
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("文案修正")]
      }),
      
      new Paragraph({
        children: [new TextRun("1. 物料下单页面标题修正：将"包材下单"修正为"物料下单"。")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("2. 物料查询页面标题修改：将标题改成"物料查询"，右侧的按钮去掉导入 JSON，其他按钮的配色符合莫兰迪暖色 UI。")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("3. 关于板块文案修改：将"如果觉得这个程序对你工作有所帮助"改为"如果你觉得这个程序对你有所帮助"。")],
        spacing: { after: 240 }
      }),
      
      new Paragraph({ children: [new PageBreak()] }),
      
      // 第三章：系统架构
      new Paragraph({
        heading: HeadingLevel.HEADING_1,
        children: [new TextRun("系统架构")]
      }),
      
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("文件结构")]
      }),
      
      new Paragraph({
        children: [new TextRun("采购管理系统1.4/")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("├── main.py                 # 程序主入口")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("├── database.py             # 数据库操作封装")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("├── 采购助手V1.3.spec      # PyInstaller 打包配置")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("├── assets/                # 资源文件目录")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("│   ├── 同仁堂企业LOGO2.ico        # 程序图标")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("│   ├── logo_40x40.png            # 导航栏 Logo")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("│   ├── nav_*.png                 # 导航栏图标")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("│   └── 产品包装报价单_模板.xlsx   # 报价单 Excel 模板")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("└── pages/                 # 页面模块目录")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("    ├── dashboard_page.py   # 仪表盘页面")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("    ├── tangxun_page.py    # 堂训页面")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("    ├── packaging_page.py   # 物料下单页面")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("    ├── quotation_page.py   # 报价单页面")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("    ├── query_page.py       # 物料查询页面")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("    ├── supplier_page.py    # 供应商页面")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("    ├── collection_page.py  # 催款记录页面")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("    ├── purchase_page.py    # 采购垫付页面")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("    ├── travel_page.py      # 差旅报销页面")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("    ├── memo_page.py        # 备忘录页面")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("    └── settings_page.py    # 设置页面")],
        spacing: { after: 240 }
      }),
      
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("数据库结构")]
      }),
      
      new Paragraph({
        heading: HeadingLevel.HEADING_3,
        children: [new TextRun("物料表 (materials)")]
      }),
      
      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [2340, 2340, 4680],
        rows: [
          new TableRow({
            children: [
              new TableCell({
                shading: { fill: "2E75B6", type: ShadingType.CLEAR },
                children: [new Paragraph({ children: [new TextRun({ text: "字段名", bold: true, color: "FFFFFF" })] })],
                width: { size: 2340, type: WidthType.DXA }
              }),
              new TableCell({
                shading: { fill: "2E75B6", type: ShadingType.CLEAR },
                children: [new Paragraph({ children: [new TextRun({ text: "类型", bold: true, color: "FFFFFF" })] })],
                width: { size: 2340, type: WidthType.DXA }
              }),
              new TableCell({
                shading: { fill: "2E75B6", type: ShadingType.CLEAR },
                children: [new Paragraph({ children: [new TextRun({ text: "说明", bold: true, color: "FFFFFF" })] })],
                width: { size: 4680, type: WidthType.DXA }
              })
            ]
          }),
          new TableRow({
            children: [
              new TableCell({
                children: [new Paragraph({ children: [new TextRun("id")] })],
                width: { size: 2340, type: WidthType.DXA }
              }),
              new TableCell({
                children: [new Paragraph({ children: [new TextRun("INTEGER")] })],
                width: { size: 2340, type: WidthType.DXA }
              }),
              new TableCell({
                children: [new Paragraph({ children: [new TextRun("主键，自增")] })],
                width: { size: 4680, type: WidthType.DXA }
              })
            ]
          }),
          new TableRow({
            children: [
              new TableCell({
                children: [new Paragraph({ children: [new TextRun("品名")] })],
                width: { size: 2340, type: WidthType.DXA }
              }),
              new TableCell({
                children: [new Paragraph({ children: [new TextRun("TEXT")] })],
                width: { size: 2340, type: WidthType.DXA }
              }),
              new TableCell({
                children: [new Paragraph({ children: [new TextRun("物料名称")] })],
                width: { size: 4680, type: WidthType.DXA }
              })
            ]
          }),
          new TableRow({
            children: [
              new TableCell({
                children: [new Paragraph({ children: [new TextRun("规格")] })],
                width: { size: 2340, type: WidthType.DXA }
              }),
              new TableCell({
                children: [new Paragraph({ children: [new TextRun("TEXT")] })],
                width: { size: 2340, type: WidthType.DXA }
              }),
              new TableCell({
                children: [new Paragraph({ children: [new TextRun("物料规格")] })],
                width: { size: 4680, type: WidthType.DXA }
              })
            ]
          }),
          new TableRow({
            children: [
              new TableCell({
                children: [new Paragraph({ children: [new TextRun("单位")] })],
                width: { size: 2340, type: WidthType.DXA }
              }),
              new TableCell({
                children: [new Paragraph({ children: [new TextRun("TEXT")] })],
                width: { size: 2340, type: WidthType.DXA }
              }),
              new TableCell({
                children: [new Paragraph({ children: [new TextRun("计量单位")] })],
                width: { size: 4680, type: WidthType.DXA }
              })
            ]
          }),
          new TableRow({
            children: [
              new TableCell({
                children: [new Paragraph({ children: [new TextRun("类型")] })],
                width: { size: 2340, type: WidthType.DXA }
              }),
              new TableCell({
                children: [new Paragraph({ children: [new TextRun("TEXT")] })],
                width: { size: 2340, type: WidthType.DXA }
              }),
              new TableCell({
                children: [new Paragraph({ children: [new TextRun("物料类型")] })],
                width: { size: 4680, type: WidthType.DXA }
              })
            ]
          })
        ]
      }),
      
      new Paragraph({ children: [new PageBreak()] }),
      
      // 第四章：打包说明
      new Paragraph({
        heading: HeadingLevel.HEADING_1,
        children: [new TextRun("打包说明")]
      }),
      
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("环境要求")]
      }),
      
      new Paragraph({
        children: [new TextRun("• Python 3.12+")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("• CustomTkinter 5.2+")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("• PyInstaller 6.0+")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("• Pillow (PIL) 10.0+")],
        spacing: { after: 240 }
      }),
      
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("打包步骤")]
      }),
      
      new Paragraph({
        children: [new TextRun("1. 安装依赖：")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("   pip install customtkinter Pillow openpyxl pyinstaller")],
        spacing: { after: 240 }
      }),
      
      new Paragraph({
        children: [new TextRun("2. 执行打包：")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("   pyinstaller "采购助手V1.3.spec"")],
        spacing: { after: 240 }
      }),
      
      new Paragraph({
        children: [new TextRun("3. 打包完成后，exe 文件位于 dist/采购助手.exe")],
        spacing: { after: 240 }
      }),
      
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("注意事项")]
      }),
      
      new Paragraph({
        children: [new TextRun("• spec 文件中的 name='采购助手'，不显示版本号")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("• console=False，不显示控制台窗口")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("• icon='assets/同仁堂企业LOGO2.ico'，使用同仁堂企业图标")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("• datas 中包含所有资源文件（assets/ 目录下的所有文件）")],
        spacing: { after: 240 }
      }),
      
      new Paragraph({ children: [new PageBreak()] }),
      
      // 第五章：使用说明
      new Paragraph({
        heading: HeadingLevel.HEADING_1,
        children: [new TextRun("使用说明")]
      }),
      
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("首次使用")]
      }),
      
      new Paragraph({
        children: [new TextRun("1. 双击"采购助手.exe"启动程序")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("2. 程序会自动在用户目录下创建"采购管理系统数据"文件夹")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("3. 所有数据文件（procurement.db、settings.txt、error.log）都存放在这个文件夹中")],
        spacing: { after: 240 }
      }),
      
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("数据管理")]
      }),
      
      new Paragraph({
        children: [new TextRun("1. 打开设置页面，进入"数据管理"分类")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("2. 点击"浏览..."按钮，选择新的数据存放位置")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("3. 点击"保存设置"，程序会自动迁移已有数据库文件到新位置")],
        spacing: { after: 240 }
      }),
      
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("导航栏使用")]
      }),
      
      new Paragraph({
        children: [new TextRun("• 点击导航栏顶部的 Logo，可以跳转到堂训页面")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("• 点击导航栏中的按钮，可以切换到对应的功能页面")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("• 点击底部的折叠按钮，可以展开/收起导航栏")],
        spacing: { after: 240 }
      }),
      
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("联系人")]
      }),
      
      new Paragraph({
        children: [new TextRun("如有任何问题或建议，请联系：")],
        spacing: { after: 240 }
      }),
      
      new Paragraph({
        children: [new TextRun("作者：EastSeaO")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("微信：EastSeaO")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("单位：北京同仁堂健康药业（青海）有限公司 采购部")],
        spacing: { after: 240 }
      }),
      
      new Paragraph({ children: [new PageBreak()] }),
      
      // 第六章：开发者信息
      new Paragraph({
        heading: HeadingLevel.HEADING_1,
        children: [new TextRun("开发者信息")]
      }),
      
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("关于作者")]
      }),
      
      new Paragraph({
        children: [new TextRun("作者目前就职于北京同仁堂健康药业（青海）有限公司 采购部，负责包装采购业务。如果你觉得这个程序对你有所帮助，可以加作者微信"EastSeaO"，探讨加入更多功能。")],
        spacing: { after: 240 }
      }),
      
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("版本历史")]
      }),
      
      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [2340, 2340, 4680],
        rows: [
          new TableRow({
            children: [
              new TableCell({
                shading: { fill: "2E75B6", type: ShadingType.CLEAR },
                children: [new Paragraph({ children: [new TextRun({ text: "版本", bold: true, color: "FFFFFF" })] })],
                width: { size: 2340, type: WidthType.DXA }
              }),
              new TableCell({
                shading: { fill: "2E75B6", type: ShadingType.CLEAR },
                children: [new Paragraph({ children: [new TextRun({ text: "日期", bold: true, color: "FFFFFF" })] })],
                width: { size: 2340, type: WidthType.DXA }
              }),
              new TableCell({
                shading: { fill: "2E75B6", type: ShadingType.CLEAR },
                children: [new Paragraph({ children: [new TextRun({ text: "说明", bold: true, color: "FFFFFF" })] })],
                width: { size: 4680, type: WidthType.DXA }
              })
            ]
          }),
          new TableRow({
            children: [
              new TableCell({
                children: [new Paragraph({ children: [new TextRun("V1.0")] })],
                width: { size: 2340, type: WidthType.DXA }
              }),
              new TableCell({
                children: [new Paragraph({ children: [new TextRun("2026-01")] })],
                width: { size: 2340, type: WidthType.DXA }
              }),
              new TableCell({
                children: [new Paragraph({ children: [new TextRun("初始版本发布")] })],
                width: { size: 4680, type: WidthType.DXA }
              })
            ]
          }),
          new TableRow({
            children: [
              new TableCell({
                children: [new Paragraph({ children: [new TextRun("V1.4")] })],
                width: { size: 2340, type: WidthType.DXA }
              }),
              new TableCell({
                children: [new Paragraph({ children: [new TextRun("2026-06-07")] })],
                width: { size: 2340, type: WidthType.DXA }
              }),
              new TableCell({
                children: [new Paragraph({ children: [new TextRun("多项 UI 优化和功能增强")] })],
                width: { size: 4680, type: WidthType.DXA }
              })
            ]
          }),
          new TableRow({
            children: [
              new TableCell({
                children: [new Paragraph({ children: [new TextRun("V1.5")] })],
                width: { size: 2340, type: WidthType.DXA }
              }),
              new TableCell({
                children: [new Paragraph({ children: [new TextRun("2026-06-09")] })],
                width: { size: 2340, type: WidthType.DXA }
              }),
              new TableCell({
                children: [new Paragraph({ children: [new TextRun("数据管理、堂训页面、设置页面优化")] })],
                width: { size: 4680, type: WidthType.DXA }
              })
            ]
          })
        ]
      }),
      
      new Paragraph({ children: [new PageBreak()] }),
      
      // 附录：API 说明
      new Paragraph({
        heading: HeadingLevel.HEADING_1,
        children: [new TextRun("附录：API 说明")]
      }),
      
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("Database 类")]
      }),
      
      new Paragraph({
        children: [new TextRun("Database 类封装了所有数据库操作，支持自定义数据目录。")],
        spacing: { after: 240 }
      }),
      
      new Paragraph({
        heading: HeadingLevel.HEADING_3,
        children: [new TextRun("初始化")]
      }),
      
      new Paragraph({
        children: [new TextRun("db = Database(data_dir=None)")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("• data_dir：可选参数，指定数据库文件存放目录")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("• 如果不指定，默认使用 ~/采购管理系统数据/")],
        spacing: { after: 240 }
      }),
      
      new Paragraph({
        heading: HeadingLevel.HEADING_3,
        children: [new TextRun("主要方法")]
      }),
      
      new Paragraph({
        children: [new TextRun("• fetch_all(sql, params=())：执行查询，返回所有结果")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("• fetch_one(sql, params=())：执行查询，返回第一条结果")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("• execute(sql, params=())：执行 INSERT/UPDATE/DELETE")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("• executemany(sql, seq_of_params)：批量执行")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("• create_tables()：创建所有数据表")],
        spacing: { after: 240 }
      }),
      
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("设置管理")]
      }),
      
      new Paragraph({
        children: [new TextRun("设置通过 load_settings() 和 save_settings(settings) 函数管理。")],
        spacing: { after: 240 }
      }),
      
      new Paragraph({
        heading: HeadingLevel.HEADING_3,
        children: [new TextRun("设置项")]
      }),
      
      new Paragraph({
        children: [new TextRun("• theme：主题（light/dark）")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("• data_dir：数据存放位置")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("• startup_sections：启动时需要打开的页面")],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("• window_geometry：窗口大小和位置")],
        spacing: { after: 240 }
      }),
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("开发者文档_V1.5.docx", buffer);
  console.log("文档生成成功：开发者文档_V1.5.docx");
});
