const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, PageBreak, PageNumber, LevelFormat, TableOfContents
} = require("docx");

// --- Helpers ---
const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };
const cellMargins = { top: 60, bottom: 60, left: 100, right: 100 };
const tableWidth = 9026; // A4 content width

function heading1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 200 },
    children: [new TextRun({ text, bold: true, size: 32, font: "Microsoft YaHei" })],
  });
}

function heading2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 280, after: 160 },
    children: [new TextRun({ text, bold: true, size: 28, font: "Microsoft YaHei" })],
  });
}

function heading3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 200, after: 120 },
    children: [new TextRun({ text, bold: true, size: 24, font: "Microsoft YaHei" })],
  });
}

function bodyText(text) {
  return new Paragraph({
    spacing: { after: 80, line: 360 },
    children: [new TextRun({ text, size: 21, font: "Microsoft YaHei" })],
  });
}

function boldBodyText(label, text) {
  return new Paragraph({
    spacing: { after: 80, line: 360 },
    children: [
      new TextRun({ text: label, bold: true, size: 21, font: "Microsoft YaHei" }),
      new TextRun({ text, size: 21, font: "Microsoft YaHei" }),
    ],
  });
}

function makeCell(text, width, opts = {}) {
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    margins: cellMargins,
    shading: opts.header
      ? { fill: "F5F0EB", type: ShadingType.CLEAR }
      : undefined,
    children: [
      new Paragraph({
        children: [
          new TextRun({
            text,
            size: 20,
            font: "Microsoft YaHei",
            bold: opts.header || false,
          }),
        ],
      }),
    ],
  });
}

function makeTable(headers, rows, colWidths) {
  const totalW = colWidths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: totalW, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [
      new TableRow({
        children: headers.map((h, i) =>
          makeCell(h, colWidths[i], { header: true })
        ),
      }),
      ...rows.map(
        (row) =>
          new TableRow({
            children: row.map((cell, i) =>
              makeCell(cell || "", colWidths[i])
            ),
          })
      ),
    ],
  });
}

function tipBox(text) {
  return new Paragraph({
    spacing: { before: 120, after: 120 },
    indent: { left: 360 },
    children: [
      new TextRun({ text: "\u{1F4A1} ", size: 21 }),
      new TextRun({ text, size: 21, font: "Microsoft YaHei", italics: true, color: "666666" }),
    ],
  });
}

// --- Build Document ---
const doc = new Document({
  styles: {
    default: { document: { run: { font: "Microsoft YaHei", size: 21 } } },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Microsoft YaHei", color: "4A3728" },
        paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 },
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "Microsoft YaHei", color: "5D4037" },
        paragraph: { spacing: { before: 280, after: 160 }, outlineLevel: 1 },
      },
      {
        id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: "Microsoft YaHei", color: "6D4C41" },
        paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 2 },
      },
    ],
  },
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [
          {
            level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } },
          },
        ],
      },
      {
        reference: "numbers",
        levels: [
          {
            level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } },
          },
        ],
      },
      {
        reference: "sub-numbers",
        levels: [
          {
            level: 0, format: LevelFormat.DECIMAL, text: "(%1)", alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 1080, hanging: 360 } } },
          },
        ],
      },
    ],
  },
  sections: [
    // ========== COVER PAGE ==========
    {
      properties: {
        page: {
          size: { width: 11906, height: 16838 },
          margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
        },
      },
      headers: {
        default: new Header({
          children: [
            new Paragraph({
              alignment: AlignmentType.RIGHT,
              children: [
                new TextRun({ text: "\u91c7\u8d2d\u52a9\u624b\u00a0V1.6\u00a0\u4f7f\u7528\u8bf4\u660e", size: 18, color: "999999", font: "Microsoft YaHei" }),
              ],
            }),
          ],
        }),
      },
      footers: {
        default: new Footer({
          children: [
            new Paragraph({
              alignment: AlignmentType.CENTER,
              children: [
                new TextRun({ text: "\u2014\u00a0", size: 18, color: "999999" }),
                new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "999999" }),
                new TextRun({ text: "\u00a0\u2014", size: 18, color: "999999" }),
              ],
            }),
          ],
        }),
      },
      children: [
        new Paragraph({ spacing: { before: 2400 } }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 200 },
          children: [
            new TextRun({ text: "\u5317\u4eac\u540c\u4ec1\u5802\u5065\u5eb7\u836f\u4e1a\uff08\u9752\u6d77\uff09\u6709\u9650\u516c\u53f8", size: 28, color: "7A6B5D", font: "Microsoft YaHei" }),
          ],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 400 },
          children: [
            new TextRun({ text: "\u91c7\u8d2d\u52a9\u624b\u00a0\u4f7f\u7528\u8bf4\u660e\u4e66", size: 48, bold: true, font: "Microsoft YaHei", color: "4A3728" }),
          ],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 100 },
          children: [
            new TextRun({ text: "V1.6", size: 36, color: "B56A6A", font: "Microsoft YaHei", bold: true }),
          ],
        }),
        new Paragraph({ spacing: { before: 1200 } }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 60 },
          children: [
            new TextRun({ text: "\u91c7\u8d2d\u90e8\u00a0\u00a0\u00b7\u00a0\u00a0\u4f7f\u7528\u6307\u5357", size: 22, color: "7A6B5D", font: "Microsoft YaHei" }),
          ],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 60 },
          children: [
            new TextRun({ text: "\u00a9 2026 EastSeaO", size: 20, color: "999999", font: "Microsoft YaHei" }),
          ],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ text: "2026\u5e746\u6708", size: 20, color: "999999", font: "Microsoft YaHei" }),
          ],
        }),

        // ========== TOC ==========
        new Paragraph({ children: [new PageBreak()] }),
        new TableOfContents("\u76ee\u5f55", { hyperlink: true, headingStyleRange: "1-3" }),

        // ========== 1. OVERVIEW ==========
        new Paragraph({ children: [new PageBreak()] }),
        heading1("\u4e00\u3001\u7cfb\u7edf\u6982\u8ff0"),

        heading2("1.1 \u7cfb\u7edf\u7b80\u4ecb"),
        bodyText("\u91c7\u8d2d\u52a9\u624b\u662f\u4e00\u6b3e\u4e13\u4e3a\u4f01\u4e1a\u91c7\u8d2d\u90e8\u95e8\u8bbe\u8ba1\u7684\u684c\u9762\u7ba1\u7406\u5de5\u5177\uff0c\u91c7\u7528\u83ab\u5170\u8fea\u6696\u8272\u8c03\u8bbe\u8ba1\u98ce\u683c\uff0c\u652f\u6301 Windows 10/11 \u7cfb\u7edf\u3002\u7cfb\u7edf\u63d0\u4f9b\u4ece\u7269\u6599\u67e5\u8be2\u3001\u7269\u6599\u4e0b\u5355\u3001\u4f9b\u5e94\u5546\u7ba1\u7406\u5230\u91c7\u8d2d\u57ab\u4ed8\u3001\u5dee\u65c5\u62a5\u9500\u7684\u5168\u6d41\u7a0b\u6570\u5b57\u5316\u7ba1\u7406\u3002"),

        heading2("1.2 \u4e3b\u8981\u529f\u80fd\u6a21\u5757"),
        makeTable(
          ["\u6a21\u5757\u540d\u79f0", "\u529f\u80fd\u8bf4\u660e"],
          [
            ["\u4eea\u8868\u76d8", "\u7edf\u8ba1\u6982\u89c8\uff0c\u5c55\u793a\u5404\u6a21\u5757\u7684\u5173\u952e\u6570\u636e\u6307\u6807"],
            ["\u7269\u6599\u67e5\u8be2", "\u7269\u6599\u53f0\u8d26\u67e5\u8be2\uff0c\u652f\u6301 CSV/JSON \u5bfc\u5165\u3001Excel \u5bfc\u51fa"],
            ["\u7269\u6599\u4e0b\u5355", "\u5305\u6750/\u7269\u6599\u5168\u6d41\u7a0b\u4e0b\u5355\u7ba1\u7406\uff08\u6bd4\u4ef7\u2192\u5408\u540c\u2192\u901a\u77e5\u2192\u751f\u4ea7\u2192\u53d1\u8d27\uff09"],
            ["\u62a5\u4ef7\u5355", "\u4ea7\u54c1\u62a5\u4ef7\u5355\u7ba1\u7406\uff0c\u652f\u6301\u9636\u68af\u5b9a\u4ef7\uff0c\u57fa\u4e8e\u6a21\u677f\u5bfc\u51fa Excel"],
            ["\u4f9b\u5e94\u5546\u7ba1\u7406", "\u4f9b\u5e94\u5546\u4fe1\u606f\u7ef4\u62a4\u3001\u8d44\u8d28\u7ba1\u7406"],
            ["\u50ac\u6b3e\u8bb0\u5f55", "\u4ed8\u6b3e\u50ac\u6536\u8bb0\u5f55\u7ba1\u7406"],
            ["\u91c7\u8d2d\u57ab\u4ed8", "\u91c7\u8d2d\u57ab\u4ed8\u6b3e\u9879\u8bb0\u5f55\uff0c\u542b\u7269\u6599\u660e\u7ec6"],
            ["\u5dee\u65c5\u62a5\u9500", "\u5dee\u65c5\u8d39\u7528\u62a5\u9500\u7ba1\u7406\uff0c\u542b\u4ea4\u901a/\u4f4f\u5bbf\u660e\u7ec6"],
            ["\u5907\u5fd8\u5f55", "\u5de5\u4f5c\u5907\u5fd8\u8bb0\u5f55\uff0c\u652f\u6301\u6807\u8bb0\u5b8c\u6210"],
            ["\u8bbe\u7f6e", "\u5916\u89c2\u3001\u6570\u636e\u7ba1\u7406\u3001\u542f\u52a8\u8bbe\u7f6e\u3001\u7cfb\u7edf\u8bbe\u7f6e"],
          ],
          [2200, 6826]
        ),

        heading2("1.3 \u754c\u9762\u5e03\u5c40"),
        bodyText("\u7a0b\u5e8f\u91c7\u7528\u5de6\u4fa7\u5bfc\u822a\u680f + \u53f3\u4fa7\u5185\u5bb9\u533a\u7684\u7ecf\u5178\u5e03\u5c40\u3002"),
        new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u5de6\u4fa7\u5bfc\u822a\u680f\uff1a\u70b9\u51fb\u4e0d\u540c\u6309\u94ae\u5207\u6362\u529f\u80fd\u9875\u9762\uff0c\u5e95\u90e8\u53ef\u6298\u53e0/\u5c55\u5f00", size: 21, font: "Microsoft YaHei" })] }),
        new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u9876\u90e8 Logo\uff1a\u70b9\u51fb\u53ef\u8fdb\u5165\u5802\u8bad\u9875\u9762\uff0c\u67e5\u770b\u540c\u4ec1\u5802\u4f01\u4e1a\u6587\u5316", size: 21, font: "Microsoft YaHei" })] }),
        new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u7f6e\u9876\u6309\u94ae\uff1a\u53ef\u5c06\u7a97\u53e3\u56fa\u5b9a\u5728\u6700\u524d\u65b9\uff0c\u65b9\u4fbf\u5de5\u4f5c\u65f6\u53c2\u8003", size: 21, font: "Microsoft YaHei" })] }),
        new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u7cfb\u7edf\u6258\u76d8\uff1a\u6700\u5c0f\u5316\u65f6\u81ea\u52a8\u6700\u5c0f\u5316\u5230\u7cfb\u7edf\u6258\u76d8\uff0c\u53ef\u5728\u8bbe\u7f6e\u4e2d\u5f00\u542f/\u5173\u95ed", size: 21, font: "Microsoft YaHei" })] }),

        // ========== 2. MATERIAL QUERY ==========
        new Paragraph({ children: [new PageBreak()] }),
        heading1("\u4e8c\u3001\u7269\u6599\u67e5\u8be2"),

        heading2("2.1 \u529f\u80fd\u8bf4\u660e"),
        bodyText("\u7269\u6599\u67e5\u8be2\u9875\u9762\u7528\u4e8e\u7ba1\u7406\u548c\u67e5\u770b\u7269\u6599\u53f0\u8d26\u6570\u636e\uff0c\u652f\u6301\u4ece CSV \u6587\u4ef6\u6216 JSON \u6587\u4ef6\u5bfc\u5165\u6570\u636e\uff0c\u5e76\u53ef\u4ee5\u5bfc\u51fa\u4e3a Excel \u6587\u4ef6\u3002\u5bfc\u5165\u7684\u6570\u636e\u4f1a\u81ea\u52a8\u4fdd\u5b58\u5230\u6570\u636e\u5e93\uff0c\u4e0b\u6b21\u542f\u52a8\u65e0\u9700\u91cd\u65b0\u5bfc\u5165\u3002"),

        heading2("2.2 CSV \u5bfc\u5165\u64cd\u4f5c"),
        heading3("\u5bfc\u5165\u6b65\u9aa4"),
        new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u70b9\u51fb\u9875\u9762\u53f3\u4e0a\u89d2\u7684\u201c\u5bfc\u5165 CSV\u201d\u6309\u94ae", size: 21, font: "Microsoft YaHei" })] }),
        new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u5728\u5f39\u51fa\u7684\u6587\u4ef6\u9009\u62e9\u5668\u4e2d\u9009\u62e9 CSV \u6587\u4ef6", size: 21, font: "Microsoft YaHei" })] }),
        new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u7a0b\u5e8f\u4f1a\u81ea\u52a8\u8bc6\u522b\u7f16\u7801\uff08\u652f\u6301 UTF-8\u3001GBK\u3001GB2312\uff09\u548c\u5217\u540d\u6620\u5c04", size: 21, font: "Microsoft YaHei" })] }),
        new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u5bfc\u5165\u6210\u529f\u540e\u4f1a\u663e\u793a\u5bfc\u5165\u7684\u8bb0\u5f55\u6570", size: 21, font: "Microsoft YaHei" })] }),
        tipBox("\u53ef\u53c2\u8003\u968f\u9644\u7684\u300c\u7269\u6599\u67e5\u8be2\u5bfc\u5165\u6a21\u677f.csv\u300d\u6587\u4ef6\u8fdb\u884c\u6570\u636e\u683c\u5f0f\u51c6\u5907\u3002"),

        heading3("CSV \u6587\u4ef6\u683c\u5f0f\u8981\u6c42"),
        bodyText("CSV \u6587\u4ef6\u7684\u7b2c\u4e00\u884c\u5fc5\u987b\u662f\u8868\u5934\u884c\uff0c\u7a0b\u5e8f\u4f1a\u81ea\u52a8\u8bc6\u522b\u4ee5\u4e0b\u5217\u540d\uff08\u4e2d\u82f1\u6587\u5747\u53ef\uff09\uff1a"),
        makeTable(
          ["\u6570\u636e\u5b57\u6bb5", "\u53ef\u8bc6\u522b\u7684\u5217\u540d"],
          [
            ["\u5408\u540c\u7f16\u53f7", "\u5408\u540c\u7f16\u53f7\u3001\u5408\u540c\u53f7\u3001\u7f16\u53f7\u3001contract"],
            ["\u4f9b\u5e94\u5546", "\u4f9b\u5e94\u5546\u540d\u79f0\u3001\u4f9b\u5e94\u5546\u3001\u5382\u5546\u3001vendor"],
            ["\u7269\u6599\u9879\u76ee\u53f7", "\u7269\u6599\u9879\u76ee\u53f7\u3001\u9879\u76ee\u53f7\u3001\u7269\u6599\u53f7\u3001\u7269\u6599\u7f16\u7801\u3001\u6599\u53f7"],
            ["\u7269\u6599\u540d\u79f0", "\u7269\u6599\u540d\u79f0\u3001\u54c1\u540d\u3001\u4ea7\u54c1\u540d"],
            ["\u6570\u91cf", "\u6570\u91cf\u3001qty"],
            ["\u5355\u4f4d", "\u5355\u4f4d\u3001\u8ba1\u91cf\u5355\u4f4d"],
            ["\u91c7\u8d2d\u5355\u4ef7", "\u91c7\u8d2d\u5355\u4ef7\u3001\u542b\u7a0e\u5355\u4ef7\u3001\u5355\u4ef7\u3001\u4ef7\u683c"],
            ["\u8ba2\u5355\u603b\u989d", "\u8ba2\u5355\u603b\u989d\u3001\u542b\u7a0e\u91d1\u989d\u3001\u91d1\u989d\u3001\u603b\u4ef7\u3001\u5408\u8ba1"],
          ],
          [2500, 6526]
        ),

        heading2("2.3 \u67e5\u8be2\u7b5b\u9009"),
        bodyText("\u7269\u6599\u67e5\u8be2\u9875\u9762\u63d0\u4f9b\u4e86\u56db\u79cd\u7b5b\u9009\u65b9\u5f0f\uff1a"),
        new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u5e74\u4efd\u7b5b\u9009\uff1a\u4e0b\u62c9\u83dc\u5355\u9009\u62e9\u5e74\u4efd\uff08\u81ea\u52a8\u4ece\u5408\u540c\u7f16\u53f7\u63d0\u53d6\uff09", size: 21, font: "Microsoft YaHei" })] }),
        new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u4f9b\u5e94\u5546\u7b5b\u9009\uff1a\u8f93\u5165\u5173\u952e\u8bcd\u6a21\u7cca\u5339\u914d\u4f9b\u5e94\u5546\u540d\u79f0", size: 21, font: "Microsoft YaHei" })] }),
        new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u7269\u6599\u540d\u79f0\u7b5b\u9009\uff1a\u8f93\u5165\u5173\u952e\u8bcd\u6a21\u7cca\u5339\u914d\u7269\u6599\u540d\u79f0", size: 21, font: "Microsoft YaHei" })] }),
        new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u9879\u76ee\u53f7\u7b5b\u9009\uff1a\u8f93\u5165\u9879\u76ee\u53f7\u7cbe\u786e\u5339\u914d", size: 21, font: "Microsoft YaHei" })] }),
        bodyText("\u8bbe\u7f6e\u7b5b\u9009\u6761\u4ef6\u540e\uff0c\u70b9\u51fb\u201c\u67e5\u8be2\u201d\u6309\u94ae\u663e\u793a\u7b5b\u9009\u7ed3\u679c\u3002\u70b9\u51fb\u201c\u91cd\u7f6e\u201d\u53ef\u6e05\u7a7a\u6240\u6709\u7b5b\u9009\u6761\u4ef6\u3002"),

        heading2("2.4 Excel \u5bfc\u51fa"),
        bodyText("\u70b9\u51fb\u201c\u5bfc\u51fa Excel\u201d\u6309\u94ae\uff0c\u53ef\u5c06\u5f53\u524d\u67e5\u8be2\u7ed3\u679c\u5bfc\u51fa\u4e3a Excel \u6587\u4ef6\u3002\u5bfc\u51fa\u7684\u6587\u4ef6\u5305\u542b\u6240\u6709\u5f53\u524d\u663e\u793a\u7684\u6570\u636e\u5217\u3002"),

        heading2("2.5 \u6e05\u9664\u6570\u636e"),
        bodyText("\u70b9\u51fb\u201c\u6e05\u9664\u6570\u636e\u201d\u6309\u94ae\uff0c\u53ef\u6e05\u7a7a\u6240\u6709\u5df2\u5bfc\u5165\u7684\u7269\u6599\u53f0\u8d26\u6570\u636e\u3002\u6b64\u64cd\u4f5c\u4e0d\u53ef\u64a4\u9500\uff0c\u8bf7\u8c28\u614e\u4f7f\u7528\u3002"),

        // ========== 3. PACKAGING ==========
        new Paragraph({ children: [new PageBreak()] }),
        heading1("\u4e09\u3001\u7269\u6599\u4e0b\u5355"),

        heading2("3.1 \u529f\u80fd\u8bf4\u660e"),
        bodyText("\u7269\u6599\u4e0b\u5355\u9875\u9762\u662f\u7cfb\u7edf\u7684\u6838\u5fc3\u529f\u80fd\u6a21\u5757\uff0c\u652f\u6301\u5305\u6750/\u7269\u6599\u4ece\u4e0b\u5355\u5230\u5230\u8d27\u7684\u4e94\u4e2a\u73af\u8282\u5168\u6d41\u7a0b\u8ddf\u8e2a\u7ba1\u7406\u3002\u6bcf\u6761\u8bb0\u5f55\u4f1a\u6839\u636e\u5f53\u524d\u8fdb\u5ea6\u81ea\u52a8\u663e\u793a\u72b6\u6001\uff08\u5f85\u6bd4\u4ef7\u3001\u5df2\u6bd4\u4ef7\u3001\u5408\u540c\u5904\u7406\u4e2d\u3001\u5df2\u7b7e\u5408\u540c\u3001\u5df2\u53d1\u8d27\u3001\u5df2\u5f52\u6863\uff09\u3002"),

        heading2("3.2 \u7b5b\u9009\u529f\u80fd"),
        bodyText("\u9875\u9762\u9876\u90e8\u7684\u7b5b\u9009\u680f\u63d0\u4f9b\u4e09\u79cd\u7b5b\u9009\u65b9\u5f0f\uff1a"),
        new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u9879\u76ee\u7b5b\u9009\uff1a\u4e0b\u62c9\u83dc\u5355\u9009\u62e9\u6240\u5c5e\u9879\u76ee", size: 21, font: "Microsoft YaHei" })] }),
        new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u4f9b\u5e94\u5546\u7b5b\u9009\uff1a\u8f93\u5165\u4f9b\u5e94\u5546\u540d\u79f0\u5173\u952e\u8bcd\uff0c\u5b9e\u65f6\u6a21\u7cca\u5339\u914d", size: 21, font: "Microsoft YaHei" })] }),
        new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u9879\u76ee\u53f7\u7b5b\u9009\uff1a\u8f93\u51658\u4f4d\u7eaf\u6570\u5b57\u7684\u9879\u76ee\u53f7\uff0c\u5b9e\u65f6\u524d\u7f00\u5339\u914d", size: 21, font: "Microsoft YaHei" })] }),
        bodyText("\u70b9\u51fb\u201c\u2715 \u6e05\u9664\u7b5b\u9009\u201d\u6309\u94ae\u53ef\u4e00\u952e\u91cd\u7f6e\u6240\u6709\u7b5b\u9009\u6761\u4ef6\u3002"),

        heading2("3.3 \u65b0\u589e\u7269\u6599\u4e0b\u5355"),
        new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u70b9\u51fb\u5de6\u4e0a\u89d2\u7684\u201c+\u65b0\u589e\u7269\u6599\u201d\u6309\u94ae", size: 21, font: "Microsoft YaHei" })] }),
        new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u5728\u5f39\u51fa\u7684\u8868\u5355\u4e2d\u586b\u5199\u57fa\u672c\u4fe1\u606f\uff1a\u7269\u6599\u540d\u79f0\u3001\u6240\u5c5e\u9879\u76ee\u3001\u9879\u76ee\u53f7\u3001\u4e0b\u5355\u6570\u91cf\u3001\u4e0b\u5355\u5382\u5bb6", size: 21, font: "Microsoft YaHei" })] }),
        new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u6839\u636e\u9700\u8981\u586b\u5199\u4e94\u4e2a\u73af\u8282\u7684\u4fe1\u606f\uff1a\u6bd4\u4ef7\u2192\u5408\u540c\u2192\u901a\u77e5\u2192\u751f\u4ea7\u2192\u53d1\u8d27", size: 21, font: "Microsoft YaHei" })] }),
        new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u70b9\u51fb\u201c\u4fdd\u5b58\u201d\u5b8c\u6210\u65b0\u589e", size: 21, font: "Microsoft YaHei" })] }),

        heading2("3.4 \u4e94\u73af\u8282\u8bf4\u660e"),
        makeTable(
          ["\u73af\u8282", "\u586b\u5199\u5b57\u6bb5", "\u8bf4\u660e"],
          [
            ["\u2460 \u6bd4\u4ef7", "\u6bd4\u4ef7\u5355\u4ef7\u3001\u6bd4\u4ef7\u65e5\u671f\u3001\u6bd4\u4ef7\u5907\u6ce8", "\u8bb0\u5f55\u4f9b\u5e94\u5546\u62a5\u4ef7\u4fe1\u606f"],
            ["\u2461 \u5408\u540c", "\u5408\u540c\u72b6\u6001\u3001\u5408\u540c\u5907\u6ce8", "\u8ddf\u8e2a\u5408\u540c\u7b7e\u8ba2\u8fdb\u5ea6"],
            ["\u2462 \u901a\u77e5", "\u901a\u77e5\u65e5\u671f\u3001\u6c9f\u901a\u8d27\u671f\u3001\u901a\u77e5\u5907\u6ce8", "\u8bb0\u5f55\u4e0b\u5355\u901a\u77e5\u4fe1\u606f"],
            ["\u2463 \u751f\u4ea7", "\u751f\u4ea7\u5468\u671f\u3001\u9884\u5b9a\u53d1\u8d27\u65e5\u671f\u3001\u751f\u4ea7\u5907\u6ce8", "\u8ddf\u8e2a\u751f\u4ea7\u8fdb\u5ea6"],
            ["\u2464 \u53d1\u8d27", "\u53d1\u8d27\u65e5\u671f\u3001\u53d1\u8d27\u65b9\u5f0f\u3001\u7269\u6d41\u5355\u53f7\u3001\u9884\u8ba1\u5230\u8d27\u3001\u901a\u77e5\u5e93\u623f", "\u8ddf\u8e2a\u7269\u6d41\u4fe1\u606f"],
          ],
          [1200, 4026, 3800]
        ),

        heading2("3.5 \u7f16\u8f91\u548c\u5f52\u6863"),
        new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u7f16\u8f91\uff1a\u53cc\u51fb\u8868\u683c\u4e2d\u7684\u4efb\u610f\u4e00\u884c\u53ef\u6253\u5f00\u7f16\u8f91\u8868\u5355", size: 21, font: "Microsoft YaHei" })] }),
        new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u5f52\u6863\uff1a\u70b9\u51fb\u64cd\u4f5c\u5217\u7684\u201c\u5f52\u6863\u201d\u6309\u94ae\u53ef\u5f52\u6863\u5df2\u5b8c\u6210\u7684\u8bb0\u5f55", size: 21, font: "Microsoft YaHei" })] }),
        new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u5220\u9664\uff1a\u70b9\u51fb\u64cd\u4f5c\u5217\u7684\u201c\u5220\u9664\u201d\u6309\u94ae\u53ef\u5220\u9664\u8bb0\u5f55", size: 21, font: "Microsoft YaHei" })] }),

        heading2("3.6 Excel \u5bfc\u5165\u5bfc\u51fa"),
        bodyText("\u652f\u6301\u5c06\u7269\u6599\u4e0b\u5355\u6570\u636e\u5bfc\u51fa\u4e3a Excel \u6587\u4ef6\uff0c\u4e5f\u652f\u6301\u4ece Excel \u6587\u4ef6\u5bfc\u5165\u6570\u636e\u3002\u5bfc\u5165\u65f6\u7a0b\u5e8f\u4f1a\u6839\u636e\u8868\u5934\u5217\u540d\u81ea\u52a8\u6620\u5c04\u5b57\u6bb5\u3002"),

        // ========== 4. QUOTATION ==========
        new Paragraph({ children: [new PageBreak()] }),
        heading1("\u56db\u3001\u62a5\u4ef7\u5355\u7ba1\u7406"),

        heading2("4.1 \u529f\u80fd\u8bf4\u660e"),
        bodyText("\u62a5\u4ef7\u5355\u7ba1\u7406\u9875\u9762\u7528\u4e8e\u7ba1\u7406\u4ea7\u54c1\u62a5\u4ef7\u4fe1\u606f\uff0c\u652f\u6301\u9636\u68af\u5b9a\u4ef7\uff0c\u53ef\u57fa\u4e8e\u6a21\u677f\u5bfc\u51fa\u6807\u51c6\u62a5\u4ef7\u5355 Excel \u6587\u4ef6\u3002"),

        heading2("4.2 \u65b0\u589e\u62a5\u4ef7\u4ea7\u54c1"),
        new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u70b9\u51fb\u201c+\u65b0\u589e\u62a5\u4ef7\u201d\u6309\u94ae", size: 21, font: "Microsoft YaHei" })] }),
        new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u586b\u5199\u4ea7\u54c1\u4fe1\u606f\uff1a\u9879\u76ee\u53f7\u3001\u4ea7\u54c1\u540d\u79f0\u3001\u5c3a\u5bf8\u3001\u6750\u8d28/\u5de5\u827a\u3001\u4f9b\u8d27\u5468\u671f\u3001\u7bb1\u89c4\u3001\u5355\u4f4d", size: 21, font: "Microsoft YaHei" })] }),
        new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u6dfb\u52a0\u9636\u68af\u4ef7\u683c\uff1a\u70b9\u51fb\u201c+\u6dfb\u52a0\u9636\u68af\u201d\uff0c\u8bbe\u7f6e\u9636\u68af\u540d\u79f0\u3001\u6700\u4f4e\u6570\u91cf\u3001\u6700\u9ad8\u6570\u91cf\u3001\u5355\u4ef7", size: 21, font: "Microsoft YaHei" })] }),
        new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u70b9\u51fb\u201c\u4fdd\u5b58\u201d\u5b8c\u6210", size: 21, font: "Microsoft YaHei" })] }),

        heading2("4.3 \u5bfc\u51fa\u62a5\u4ef7\u5355 Excel"),
        bodyText("\u70b9\u51fb\u201c\u5bfc\u51fa\u62a5\u4ef7\u5355\u201d\u6309\u94ae\uff0c\u7a0b\u5e8f\u4f1a\u57fa\u4e8e\u9884\u8bbe\u6a21\u677f\u751f\u6210\u6807\u51c6\u683c\u5f0f\u7684\u62a5\u4ef7\u5355 Excel \u6587\u4ef6\uff0c\u5305\u542b\u9700\u65b9\u4fe1\u606f\u3001\u4f9b\u65b9\u4fe1\u606f\u548c\u4ea7\u54c1\u9636\u68af\u4ef7\u683c\u3002"),

        heading2("4.4 \u9700\u65b9/\u4f9b\u65b9\u914d\u7f6e"),
        bodyText("\u70b9\u51fb\u201c\u9700\u65b9\u914d\u7f6e\u201d\u6216\u201c\u4f9b\u65b9\u914d\u7f6e\u201d\u6309\u94ae\uff0c\u53ef\u914d\u7f6e\u62a5\u4ef7\u5355\u4e2d\u7684\u516c\u53f8\u4fe1\u606f\u3001\u8054\u7cfb\u65b9\u5f0f\u3001\u9001\u8d27\u5730\u5740\u7b49\uff0c\u914d\u7f6e\u4fe1\u606f\u4f1a\u81ea\u52a8\u586b\u5165\u5230\u5bfc\u51fa\u7684 Excel \u6587\u4ef6\u4e2d\u3002"),

        // ========== 5. SUPPLIER ==========
        new Paragraph({ children: [new PageBreak()] }),
        heading1("\u4e94\u3001\u4f9b\u5e94\u5546\u7ba1\u7406"),

        heading2("5.1 \u529f\u80fd\u8bf4\u660e"),
        bodyText("\u4f9b\u5e94\u5546\u7ba1\u7406\u9875\u9762\u7528\u4e8e\u7ef4\u62a4\u4f9b\u5e94\u5546\u4fe1\u606f\uff0c\u5305\u62ec\u57fa\u672c\u4fe1\u606f\u3001\u8054\u7cfb\u65b9\u5f0f\u3001\u5408\u4f5c\u4fe1\u606f\u7b49\u3002"),

        heading2("5.2 \u65b0\u589e\u4f9b\u5e94\u5546"),
        new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u70b9\u51fb\u201c+\u65b0\u589e\u4f9b\u5e94\u5546\u201d\u6309\u94ae", size: 21, font: "Microsoft YaHei" })] }),
        new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u586b\u5199\u57fa\u672c\u4fe1\u606f\uff1a\u540d\u79f0\u3001\u7c7b\u522b\u3001\u4e3b\u8425\u4ea7\u54c1", size: 21, font: "Microsoft YaHei" })] }),
        new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u586b\u5199\u8054\u7cfb\u65b9\u5f0f\uff1a\u8054\u7cfb\u4eba\u3001\u7535\u8bdd\u3001\u5fae\u4fe1", size: 21, font: "Microsoft YaHei" })] }),
        new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u586b\u5199\u5408\u4f5c\u4fe1\u606f\uff1a\u5408\u4f5c\u72b6\u6001\u3001\u4ed8\u6b3e\u65b9\u5f0f\u3001\u5f00\u7968\u7c7b\u578b\u3001\u7a0e\u7387\u3001\u5907\u6ce8", size: 21, font: "Microsoft YaHei" })] }),
        new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u70b9\u51fb\u201c\u4fdd\u5b58\u201d\u5b8c\u6210", size: 21, font: "Microsoft YaHei" })] }),

        heading2("5.3 \u641c\u7d22\u7b5b\u9009"),
        bodyText("\u652f\u6301\u6309\u7c7b\u522b\u3001\u540d\u79f0\u548c\u5408\u4f5c\u72b6\u6001\u8fdb\u884c\u7b5b\u9009\u3002\u8f93\u5165\u641c\u7d22\u5173\u952e\u8bcd\u540e\u70b9\u51fb\u201c\u641c\u7d22\u201d\u6309\u94ae\uff0c\u70b9\u51fb\u201c\u91cd\u7f6e\u201d\u6e05\u7a7a\u7b5b\u9009\u3002"),

        heading2("5.4 \u4f9b\u5e94\u5546\u7c7b\u522b"),
        makeTable(
          ["\u7c7b\u522b", "", "", ""],
          [
            ["\u793c\u76d2", "\u5361\u76d2", "\u6807\u7b7e", "\u73bb\u7483\u74f6"],
            ["\u590d\u5408\u819c", "\u94dd\u5236\u54c1", "\u5851\u6599\u7f50", "\u7269\u6d41\u7bb1"],
            ["\u5176\u4ed6", "", "", ""],
          ],
          [2256, 2256, 2257, 2257]
        ),

        // ========== 6. OTHER MODULES ==========
        new Paragraph({ children: [new PageBreak()] }),
        heading1("\u516d\u3001\u5176\u4ed6\u529f\u80fd\u6a21\u5757"),

        heading2("6.1 \u50ac\u6b3e\u8bb0\u5f55"),
        bodyText("\u7528\u4e8e\u7ba1\u7406\u4ed8\u6b3e\u50ac\u6536\u8bb0\u5f55\uff0c\u652f\u6301\u6a21\u7cca\u641c\u7d22\uff08\u6309\u4f9b\u5e94\u5546\u540d\u3001\u8054\u7cfb\u4eba\u3001\u5fae\u4fe1\uff09\uff0c\u53ef\u8bbe\u7f6e\u901a\u77e5\u5185\u52e4\u548c\u901a\u77e5\u7ecf\u7406\u6807\u8bb0\u3002\u652f\u6301 Excel \u5bfc\u5165\u5bfc\u51fa\u3002"),

        heading2("6.2 \u91c7\u8d2d\u57ab\u4ed8"),
        bodyText("\u7528\u4e8e\u8bb0\u5f55\u91c7\u8d2d\u57ab\u4ed8\u6b3e\u9879\uff0c\u652f\u6301\u591a\u6761\u7269\u6599\u660e\u7ec6\uff08\u540d\u79f0\u3001\u89c4\u683c\u3001\u6570\u91cf\u3001\u5355\u4ef7\u3001\u4f9b\u5e94\u5546\u3001\u5408\u8ba1\uff09\uff0c\u81ea\u52a8\u8ba1\u7b97\u603b\u91d1\u989d\u3002\u9876\u90e8\u663e\u793a\u7edf\u8ba1\u680f\uff08\u603b\u8bb0\u5f55\u3001\u603b\u91d1\u989d\u3001\u672a\u62a5\u9500\u3001\u672a\u5f00\u7968\uff09\u3002\u652f\u6301\u6309\u62a5\u9500\u72b6\u6001\u3001\u5f00\u7968\u72b6\u6001\u3001\u9879\u76ee\u7b5b\u9009\u3002\u652f\u6301 Excel \u5bfc\u5165\u5bfc\u51fa\u3002"),

        heading2("6.3 \u5dee\u65c5\u62a5\u9500"),
        bodyText("\u7528\u4e8e\u7ba1\u7406\u5dee\u65c5\u8d39\u7528\u62a5\u9500\uff0c\u652f\u6301\u591a\u6761\u4ea4\u901a\u660e\u7ec6\uff08\u5de5\u5177\u3001\u65e5\u671f\u3001\u51fa\u53d1\u5730\u3001\u76ee\u7684\u5730\u3001\u91d1\u989d\uff09\u548c\u4f4f\u5bbf\u660e\u7ec6\uff08\u5165\u4f4f/\u9000\u623f\u65e5\u671f\u3001\u623f\u95f4\u6570\u3001\u91d1\u989d\u3001\u5f00\u7968\uff09\uff0c\u81ea\u52a8\u8ba1\u7b97\u51fa\u5dee\u5929\u6570\u548c\u603b\u8d39\u7528\u3002\u652f\u6301 Excel \u5bfc\u5165\u5bfc\u51fa\u3002"),

        heading2("6.4 \u5907\u5fd8\u5f55"),
        bodyText("\u7528\u4e8e\u5de5\u4f5c\u5907\u5fd8\u8bb0\u5f55\uff0c\u652f\u6301\u6309\u9879\u76ee\u3001\u72b6\u6001\u7b5b\u9009\u548c\u6a21\u7cca\u641c\u7d22\u3002\u53ef\u5c06\u5907\u5fd8\u5f55\u6807\u8bb0\u4e3a\u201c\u5df2\u5b8c\u6210\u201d\uff0c\u5df2\u5b8c\u6210\u7684\u6761\u76ee\u4f1a\u663e\u793a\u4e3a\u7eff\u8272\u6807\u8bb0\u3002\u652f\u6301 Excel \u5bfc\u51fa\u3002"),

        heading2("6.5 \u4eea\u8868\u76d8"),
        bodyText("\u4eea\u8868\u76d8\u9875\u9762\u5c55\u793a\u5404\u6a21\u5757\u7684\u5173\u952e\u6570\u636e\u6307\u6807\uff1a"),
        new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u7269\u6599\u4e0b\u5355\uff1a\u5904\u7406\u4e2d/\u5df2\u5b8c\u6210", size: 21, font: "Microsoft YaHei" })] }),
        new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u50ac\u6b3e\u8bb0\u5f55\uff1a\u603b\u6761\u6570", size: 21, font: "Microsoft YaHei" })] }),
        new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u91c7\u8d2d\u57ab\u4ed8\uff1a\u7b14\u6570/\u5f85\u62a5\u9500\u91d1\u989d", size: 21, font: "Microsoft YaHei" })] }),
        new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u5dee\u65c5\u62a5\u9500\uff1a\u884c\u7a0b\u6570/\u5f85\u62a5\u9500\u91d1\u989d", size: 21, font: "Microsoft YaHei" })] }),
        new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u5907\u5fd8\u5f55\uff1a\u5f85\u5904\u7406\u6761\u6570", size: 21, font: "Microsoft YaHei" })] }),

        // ========== 7. SETTINGS ==========
        new Paragraph({ children: [new PageBreak()] }),
        heading1("\u4e03\u3001\u8bbe\u7f6e"),

        heading2("7.1 \u5916\u89c2\u8bbe\u7f6e"),
        bodyText("\u53ef\u5207\u6362\u4e3b\u9898\u5916\u89c2\uff08\u4eae\u8272/\u6697\u8272/\u8ddf\u968f\u7cfb\u7edf\uff09\u548c\u989c\u8272\u65b9\u6848\uff08\u83ab\u5170\u8fea\u6696\u8272/\u7ecf\u5178\u84dd\uff09\uff0c\u5207\u6362\u540e\u5373\u65f6\u751f\u6548\u3002"),

        heading2("7.2 \u6570\u636e\u7ba1\u7406"),
        bodyText("\u53ef\u67e5\u770b\u548c\u4fee\u6539\u6570\u636e\u5b58\u653e\u4f4d\u7f6e\u3002\u70b9\u51fb\u201c\u6d4f\u89c8...\u201d\u6309\u94ae\u9009\u62e9\u65b0\u7684\u6587\u4ef6\u5939\uff0c\u70b9\u51fb\u201c\u4fdd\u5b58\u8bbe\u7f6e\u201d\u540e\u7a0b\u5e8f\u4f1a\u81ea\u52a8\u8fc1\u79fb\u5df2\u6709\u6570\u636e\u5e93\u6587\u4ef6\u5230\u65b0\u4f4d\u7f6e\u3002"),

        heading2("7.3 \u542f\u52a8\u8bbe\u7f6e"),
        bodyText("\u53ef\u5f00\u542f/\u5173\u95ed\u5f00\u673a\u81ea\u52a8\u542f\u52a8\uff0c\u542f\u7528\u540e\u6bcf\u6b21\u5f00\u673a\u4f1a\u81ea\u52a8\u8fd0\u884c\u91c7\u8d2d\u52a9\u624b\u3002"),

        heading2("7.4 \u7cfb\u7edf\u8bbe\u7f6e"),
        bodyText("\u53ef\u5f00\u542f/\u5173\u95ed\u7cfb\u7edf\u6258\u76d8\u529f\u80fd\uff0c\u5f00\u542f\u540e\u5173\u95ed\u7a97\u53e3\u4f1a\u81ea\u52a8\u6700\u5c0f\u5316\u5230\u7cfb\u7edf\u6258\u76d8\uff0c\u800c\u4e0d\u662f\u76f4\u63a5\u9000\u51fa\u7a0b\u5e8f\u3002"),

        // ========== 8. FAQ ==========
        new Paragraph({ children: [new PageBreak()] }),
        heading1("\u516b\u3001\u5e38\u89c1\u95ee\u9898"),

        heading2("8.1 \u6570\u636e\u5b58\u50a8\u5728\u54ea\u91cc\uff1f"),
        bodyText("\u9ed8\u8ba4\u5b58\u50a8\u5728\u7528\u6237\u76ee\u5f55\u4e0b\u7684\u201c\u91c7\u8d2d\u7ba1\u7406\u7cfb\u7edf\u6570\u636e\u201d\u6587\u4ef6\u5939\u4e2d\uff0c\u53ef\u5728\u8bbe\u7f6e\u9875\u9762\u4e2d\u4fee\u6539\u5b58\u50a8\u4f4d\u7f6e\u3002"),

        heading2("8.2 \u5982\u4f55\u5907\u4efd\u6570\u636e\uff1f"),
        bodyText("\u76f4\u63a5\u590d\u5236\u201c\u91c7\u8d2d\u7ba1\u7406\u7cfb\u7edf\u6570\u636e\u201d\u6587\u4ef6\u5939\u5373\u53ef\u5b8c\u6210\u5907\u4efd\u3002\u5efa\u8bae\u5b9a\u671f\u590d\u5236\u5230\u5176\u4ed6\u5b89\u5168\u4f4d\u7f6e\u3002"),

        heading2("8.3 CSV \u5bfc\u5165\u5931\u8d25\u600e\u4e48\u529e\uff1f"),
        bodyText("\u8bf7\u68c0\u67e5\u4ee5\u4e0b\u51e0\u70b9\uff1a"),
        new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u786e\u8ba4\u6587\u4ef6\u7f16\u7801\u4e3a UTF-8 \u6216 GBK", size: 21, font: "Microsoft YaHei" })] }),
        new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u786e\u8ba4\u7b2c\u4e00\u884c\u662f\u8868\u5934\u884c", size: 21, font: "Microsoft YaHei" })] }),
        new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u786e\u8ba4\u5217\u540d\u7b26\u5408\u7cfb\u7edf\u8bc6\u522b\u89c4\u5219\uff08\u53c2\u89c1\u7269\u6599\u67e5\u8be2\u7ae0\u8282\u7684\u5217\u540d\u5bf9\u7167\u8868\uff09", size: 21, font: "Microsoft YaHei" })] }),
        new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: "\u53c2\u8003\u968f\u9644\u7684 CSV \u5bfc\u5165\u6a21\u677f\u6587\u4ef6", size: 21, font: "Microsoft YaHei" })] }),

        heading2("8.4 \u7a97\u53e3\u6700\u5c0f\u5316\u540e\u627e\u4e0d\u5230\u7a0b\u5e8f\uff1f"),
        bodyText("\u5982\u679c\u5df2\u5f00\u542f\u7cfb\u7edf\u6258\u76d8\u529f\u80fd\uff0c\u53ef\u4ee5\u5728\u4efb\u52a1\u680f\u53f3\u4e0b\u89d2\u7684\u6258\u76d8\u533a\u57df\u627e\u5230\u91c7\u8d2d\u52a9\u624b\u56fe\u6807\uff0c\u53cc\u51fb\u5373\u53ef\u6062\u590d\u7a97\u53e3\u3002\u4e5f\u53ef\u4ee5\u5728\u8bbe\u7f6e\u4e2d\u5173\u95ed\u6258\u76d8\u529f\u80fd\u3002"),

        heading2("8.5 \u8054\u7cfb\u4e0e\u53cd\u9988"),
        bodyText("\u5982\u6709\u4efb\u4f55\u95ee\u9898\u6216\u5efa\u8bae\uff0c\u8bf7\u8054\u7cfb\uff1a"),
        boldBodyText("\u4f5c\u8005\uff1a", "EastSeaO"),
        boldBodyText("\u5fae\u4fe1\uff1a", "EastSeaO"),
        boldBodyText("\u5355\u4f4d\uff1a", "\u5317\u4eac\u540c\u4ec1\u5802\u5065\u5eb7\u836f\u4e1a\uff08\u9752\u6d77\uff09\u6709\u9650\u516c\u53f8 \u91c7\u8d2d\u90e8"),
      ],
    },
  ],
});

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync("I:/采购管理系统/采购管理系统1.4/采购助手使用说明书V1.6.docx", buffer);
  console.log("DOCX created successfully");
});
