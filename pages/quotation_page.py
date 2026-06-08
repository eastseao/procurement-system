#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""报价单页面 v1.3 - 阶梯定价、自动生成报价单、导出Excel"""

import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
import tkinter as tk
from datetime import datetime
import os
import sys


def _get_resource_path(relative_path):
    """获取资源绝对路径（兼容打包后 _MEIPASS）"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)


class QuotationPage(ctk.CTkFrame):
    """产品报价单主页面"""

    def __init__(self, parent, db, C):
        super().__init__(parent, fg_color=C["bg"], corner_radius=0)
        self.db = db
        self.C = C
        self.products = []
        self.config_data = {}
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        toolbar = ctk.CTkFrame(self, fg_color="transparent", height=56)
        toolbar.pack(fill="x", padx=24, pady=(16, 8))
        toolbar.pack_propagate(False)

        ctk.CTkLabel(
            toolbar, text="📋  产品报价单",
            font=ctk.CTkFont(family="Microsoft YaHei", size=20, weight="bold"),
            text_color=self.C["text"],
        ).pack(side="left", pady=12)

        btn_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        btn_frame.pack(side="right", pady=8)

        ctk.CTkButton(
            btn_frame, text="📤 导出报价单", width=120, height=34,
            fg_color=self.C["success"], hover_color="#7A9A6E",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._export_quotation,
        ).pack(side="right", padx=4)

        ctk.CTkButton(
            btn_frame, text="⚙ 供方配置", width=100, height=34,
            fg_color="#6B7280", hover_color="#4B5563",
            font=ctk.CTkFont(size=13),
            command=self._open_supplier_config,
        ).pack(side="right", padx=4)

        ctk.CTkButton(
            btn_frame, text="⚙ 需方配置", width=100, height=34,
            fg_color="#6B7280", hover_color="#4B5563",
            font=ctk.CTkFont(size=13),
            command=self._open_config,
        ).pack(side="right", padx=4)

        ctk.CTkButton(
            btn_frame, text="＋ 添加产品", width=110, height=34,
            fg_color=self.C["danger"], hover_color="#A85A5A",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._open_form,
        ).pack(side="left", padx=4)

        # 统计栏
        stats = ctk.CTkFrame(self, fg_color="transparent", height=28)
        stats.pack(fill="x", padx=24, pady=(0, 4))
        self.stats_label = ctk.CTkLabel(
            stats, text="", font=ctk.CTkFont(size=12),
            text_color=self.C.get("text_secondary", "#5D5D5D"),
        )
        self.stats_label.pack(side="left")

        # 表格
        table_frame = ctk.CTkFrame(self, fg_color=self.C["card"], corner_radius=10)
        table_frame.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        columns = ("序号", "项目号", "产品名称", "产品尺寸", "材质/工艺", "供货周期", "发货箱规", "阶梯价格", "操作")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Quotation.Treeview",
                         font=("Microsoft YaHei", 11),
                         rowheight=36,
                         background="#FFFFFF",
                         fieldbackground="#FFFFFF",
                         foreground="#1E293B",
                         borderwidth=0,
                         relief="flat")
        style.configure("Quotation.Treeview.Heading",
                         font=("Microsoft YaHei", 11, "bold"),
                         background="#F8FAFC",
                         foreground="#475569",
                         relief="flat",
                         borderwidth=0)
        style.map("Quotation.Treeview",
                  background=[("selected", "#E8D5C4")],
                  foreground=[("selected", "#4A3728")])
        style.layout("Quotation.Treeview", [
            ("Treeview.treearea", {"sticky": "nswe"})
        ])

        tree_wrap = tk.Frame(table_frame, bg="#FFFFFF")
        tree_wrap.pack(fill="both", expand=True, padx=8, pady=8)

        self.tree = ttk.Treeview(
            tree_wrap, style="Quotation.Treeview",
            columns=columns, show="headings", height=15, selectmode="browse"
        )

        widths = {"序号": 50, "项目号": 80, "产品名称": 140, "产品尺寸": 100,
                  "材质/工艺": 160, "供货周期": 80, "发货箱规": 80, "阶梯价格": 220, "操作": 80}
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=widths.get(col, 100), anchor="center")
        self.tree.column("产品名称", anchor="w")
        self.tree.column("材质/工艺", anchor="w")
        self.tree.column("阶梯价格", anchor="w")

        vsb = ttk.Scrollbar(tree_wrap, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_wrap, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.tag_configure("odd", background="#F8FAFC")
        self.tree.tag_configure("even", background="#FFFFFF")

        self.tree.bind("<Double-1>", self._on_row_double_click)
        self.tree.bind("<Button-1>", self._on_row_click)

    def _load_data(self):
        self.products = self.db.get_quotation_products()
        self.config_data = self.db.get_quotation_config()
        self._render_table()
        total = len(self.products)
        total_tiers = sum(len(p.get("tiers", [])) for p in self.products)
        buyer = self.config_data.get("buyer_name", "")
        self.stats_label.configure(text=f"共 {total} 款产品 | {total_tiers} 个价格阶梯 | 需方：{buyer}")

    def _render_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for idx, p in enumerate(self.products, 1):
            tiers = p.get("tiers", [])
            if tiers:
                tier_texts = []
                for t in tiers:
                    mn = int(t.get("min_qty", 0))
                    mx = t.get("max_qty")
                    up = t.get("unit_price", 0)
                    if mx:
                        tier_texts.append(f"≥{mn} / <{mx}: ¥{up:.2f}")
                    else:
                        tier_texts.append(f"≥{mn}: ¥{up:.2f}")
                tier_str = " | ".join(tier_texts)
            else:
                tier_str = "未设置"

            self.tree.insert("", "end", iid=str(p["id"]),
                values=(
                    idx,
                    p.get("item_no", "-"),
                    p.get("product_name", ""),
                    p.get("product_size", "-"),
                    p.get("material_process", "-"),
                    p.get("supply_cycle", "-"),
                    p.get("carton_spec", "-"),
                    tier_str,
                    "编辑  删除",
                ))

    def _on_row_double_click(self, event):
        sel = self.tree.selection()
        if sel:
            self._open_form(oid=int(sel[0]))

    def _on_row_click(self, event):
        item = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not item:
            return
        self.tree.selection_set(item)
        col_idx = int(col.replace("#", "")) - 1
        if col_idx != 8:  # 操作列
            return
        bbox = self.tree.bbox(item, col)
        if not bbox:
            return
        x_rel = event.x - bbox[0]
        col_w = bbox[2]
        oid = int(item)
        if x_rel < col_w * 0.5:
            self._edit_product(oid)
        else:
            self._delete_product(oid)

    def _edit_product(self, oid):
        self._open_form(oid=oid)

    def _delete_product(self, oid):
        rec = next((p for p in self.products if p["id"] == oid), None)
        name = rec.get("product_name", "") if rec else ""
        if messagebox.askyesno("删除确认", f"确定删除产品「{name}」及其所有阶梯价格？", icon="warning"):
            self.db.delete_quotation_product(oid)
            self._load_data()

    def _open_form(self, oid=None):
        try:
            form = QuotationForm(self, self.db, self.C, oid=oid, on_save=self._load_data)
            form.grab_set()
        except Exception as e:
            import traceback
            messagebox.showerror("打开表单失败", f"{e}\n\n{traceback.format_exc()}")

    def _open_config(self):
        try:
            dlg = QuotationConfigDialog(self, self.db, self.C, on_save=self._load_data)
            dlg.grab_set()
        except Exception as e:
            import traceback
            messagebox.showerror("打开配置失败", f"{e}\n\n{traceback.format_exc()}")

    def _open_supplier_config(self):
        try:
            dlg = QuotationSupplierDialog(self, self.db, self.C, on_save=self._load_data)
            dlg.grab_set()
        except Exception as e:
            import traceback
            messagebox.showerror("打开供方配置失败", f"{e}\n\n{traceback.format_exc()}")

    # ── 模板路径 ──
    TEMPLATE_REL = "assets/产品包装报价单_模板.xlsx"

    def _get_template_path(self):
        """获取模板文件路径（支持打包后 _MEIPASS）"""
        # PyInstaller 打包后路径
        if hasattr(sys, '_MEIPASS'):
            p = os.path.join(sys._MEIPASS, self.TEMPLATE_REL)
            if os.path.exists(p):
                return p
        # 开发环境：项目根目录
        project = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        p = os.path.join(project, self.TEMPLATE_REL)
        if os.path.exists(p):
            return p
        # 备用：原始参考路径
        alt = r"E:/采购合同/包材供应商合同/产品包装报价单.xlsx"
        if os.path.exists(alt):
            return alt
        raise FileNotFoundError(
            "找不到报价单模板文件，请确认存在以下任一位置：\n"
            f"  {p}\n  {alt}"
        )

    def _get_next_export_name(self, directory):
        """获取当天自动递增的导出文件名"""
        today = datetime.now().strftime("%Y%m%d")
        base = f"产品包装报价单_{today}"
        # 查找目录下最大的序号
        max_idx = 0
        if os.path.isdir(directory):
            for fn in os.listdir(directory):
                if fn.startswith(base) and fn.endswith(".xlsx"):
                    parts = fn.replace(".xlsx", "").split("_")
                    try:
                        idx = int(parts[-1])
                        if idx > max_idx:
                            max_idx = idx
                    except ValueError:
                        pass
        next_idx = max_idx + 1
        return os.path.join(directory, f"{base}_{next_idx:03d}.xlsx")

    def _export_quotation(self):
        """基于模板导出报价单Excel，自动递增文件名"""
        if not self.products:
            messagebox.showinfo("提示", "请先添加产品")
            return

        # 先选目录
        directory = filedialog.askdirectory(title="选择导出目录")
        if not directory:
            return

        filepath = self._get_next_export_name(directory)

        try:
            self._generate_excel(filepath)
            messagebox.showinfo("导出成功", f"报价单已导出到：\n{filepath}")
        except Exception as e:
            import traceback
            messagebox.showerror("导出失败", f"{e}\n\n{traceback.format_exc()}")

    def _generate_excel(self, filepath):
        from openpyxl import load_workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

        # ── 加载模板（保持所有格式、合并单元格、logo图片、打印设置）──
        template = self._get_template_path()
        wb = load_workbook(template)
        ws = wb.active
        ws.title = "产品包装报价单"

        cfg = self.config_data or {}
        supplier = self.db.get_quotation_supplier() or {}

        # ── 字号参考 ──
        normal_font = Font(name="宋体", size=14)

        thin = Side(style="thin")
        border_all = Border(left=thin, right=thin, top=thin, bottom=thin)
        center = Alignment(horizontal="center", vertical="center", wrap_text=True)
        left_wrap = Alignment(horizontal="left", vertical="center", wrap_text=True)

        # ============================================================
        # 1. 需方信息区 (Left side, E-F columns, rows 5/7/9/11)
        # ============================================================
        # F5 → 需方名称
        ws["F5"] = cfg.get("buyer_name", "")
        ws["F5"].font = normal_font
        # F7 → 联系人
        ws["F7"] = cfg.get("buyer_contact", "")
        ws["F7"].font = normal_font
        # F9 → 联系方式
        ws["F9"] = str(cfg.get("buyer_phone", ""))
        ws["F9"].font = normal_font
        # F11 → 送货地址
        ws["F11"] = cfg.get("buyer_address", "")
        ws["F11"].font = normal_font

        # ============================================================
        # 2. 供方信息区 (Right side, M-O columns, rows 5-10)
        # ============================================================
        # O5 → 供应商名称
        ws["O5"] = supplier.get("supplier_name", "")
        ws["O5"].font = normal_font
        # O6 → 联系人
        ws["O6"] = supplier.get("contact_person", "")
        ws["O6"].font = normal_font
        # O7 → 联系方式
        ws["O7"] = supplier.get("phone", "")
        ws["O7"].font = normal_font
        # O8 → 地址
        ws["O8"] = supplier.get("address", "")
        ws["O8"].font = normal_font
        # O9 → 报价日期
        ws["O9"] = supplier.get("quote_date", "")
        ws["O9"].font = normal_font
        # O10 → 报价有效期
        ws["O10"] = supplier.get("quote_validity", "")
        ws["O10"].font = normal_font

        # ============================================================
        # 3. 底部条款区 (Rows 20-25)
        # ============================================================
        ws["E21"] = cfg.get("payment_terms", "按协议条件付款；")
        ws["E21"].font = normal_font
        ws["E22"] = cfg.get("transport_method", "物料或者专车请提前说明")
        ws["E22"].font = normal_font
        ws["E23"] = cfg.get("delivery_docs", "请随货放【发货单】【厂检报告】")
        ws["E23"].font = Font(name="宋体", size=14, bold=True, color="FFFF0000")
        ws["E24"] = cfg.get("quote_requirement", "需含税含运")
        ws["E24"].font = normal_font

        # ============================================================
        # 4. 数据行 —— 动态处理
        # ============================================================
        # 模板原始有4行数据 (rows 15-18)，按产品/阶梯数量动态调整

        # 计算所需总行数
        total_rows = 0
        for product in self.products:
            tiers = product.get("tiers", [])
            total_rows += max(1, len(tiers))

        ORIGINAL_DATA_START = 15
        ORIGINAL_DATA_END = 18   # 模板原始4行
        ORIGINAL_DATA_COUNT = ORIGINAL_DATA_END - ORIGINAL_DATA_START + 1  # =4

        # 先解除数据区域原有的所有合并单元格
        from openpyxl.utils import range_boundaries
        merges_to_remove = []
        for mc in list(ws.merged_cells.ranges):
            mc_str = str(mc)
            min_col, min_row, max_col, max_row = range_boundaries(mc_str)
            if min_row >= ORIGINAL_DATA_START and max_row <= ORIGINAL_DATA_END:
                merges_to_remove.append(mc_str)

        for mr in merges_to_remove:
            try:
                ws.unmerge_cells(mr)
            except Exception:
                pass

        # 如果需要更多行，在数据区域末尾插入
        extra_rows = total_rows - ORIGINAL_DATA_COUNT
        if extra_rows > 0:
            # 在 row 19 (模板数据末尾之后) 插入额外行
            ws.insert_rows(ORIGINAL_DATA_END + 1, extra_rows)
        elif extra_rows < 0:
            # 如果产品更少，删除多余行
            ws.delete_rows(ORIGINAL_DATA_END + extra_rows + 1, -extra_rows)

        # 清理原数据行的内容
        for r in range(ORIGINAL_DATA_START, ORIGINAL_DATA_START + total_rows):
            for c in range(2, 21):
                cell = ws.cell(row=r, column=c)
                cell.value = None

        # 写入产品数据
        current_row = ORIGINAL_DATA_START

        for idx, product in enumerate(self.products, 1):
            tiers = product.get("tiers", [])
            tier_count = max(1, len(tiers))
            first_r = current_row
            last_r = current_row + tier_count - 1

            # 设置行高
            for r in range(first_r, last_r + 1):
                ws.row_dimensions[r].height = 36

            # 产品信息列：跨行合并 (B→O)
            if tier_count > 1:
                # 序号 B
                ws.merge_cells(f"B{first_r}:B{last_r}")
                # 项目号 C:D
                ws.merge_cells(f"C{first_r}:D{last_r}")
                # 产品名称 E:F
                ws.merge_cells(f"E{first_r}:F{last_r}")
                # 产品尺寸 G:I
                ws.merge_cells(f"G{first_r}:I{last_r}")
                # 材质/工艺 J:M
                ws.merge_cells(f"J{first_r}:M{last_r}")
                # 供货周期 N
                ws.merge_cells(f"N{first_r}:N{last_r}")
                # 发货箱规 O
                ws.merge_cells(f"O{first_r}:O{last_r}")

            for ti in range(tier_count):
                r = current_row

                # 仅在首行写产品信息
                if ti == 0:
                    ws.cell(row=r, column=2, value=idx).font = normal_font
                    ws.cell(row=r, column=2).alignment = center
                    ws.cell(row=r, column=2).border = border_all

                    ws.cell(row=r, column=3, value=product.get("item_no", "")).font = normal_font
                    ws.cell(row=r, column=3).alignment = center
                    ws.cell(row=r, column=3).border = border_all

                    ws.cell(row=r, column=5, value=product.get("product_name", "")).font = normal_font
                    ws.cell(row=r, column=5).alignment = left_wrap
                    ws.cell(row=r, column=5).border = border_all

                    ws.cell(row=r, column=7, value=product.get("product_size", "")).font = normal_font
                    ws.cell(row=r, column=7).alignment = center
                    ws.cell(row=r, column=7).border = border_all

                    ws.cell(row=r, column=10, value=product.get("material_process", "")).font = normal_font
                    ws.cell(row=r, column=10).alignment = left_wrap
                    ws.cell(row=r, column=10).border = border_all

                    ws.cell(row=r, column=14, value=product.get("supply_cycle", "")).font = normal_font
                    ws.cell(row=r, column=14).alignment = center
                    ws.cell(row=r, column=14).border = border_all

                    ws.cell(row=r, column=15, value=product.get("carton_spec", "")).font = normal_font
                    ws.cell(row=r, column=15).alignment = center
                    ws.cell(row=r, column=15).border = border_all

                # 阶梯数量 (P:Q) — 每行独立
                if tiers and ti < len(tiers):
                    tier = tiers[ti]
                    mn = int(tier.get("min_qty", 0))
                    mx = tier.get("max_qty")
                    if mx:
                        qty_text = f"{mn}-{int(mx)-1}"
                    else:
                        qty_text = f"≥{mn}"
                    ws.merge_cells(f"P{r}:Q{r}")
                    ws.cell(row=r, column=16, value=qty_text).font = normal_font
                    ws.cell(row=r, column=16).alignment = center
                    ws.cell(row=r, column=16).border = border_all
                else:
                    ws.merge_cells(f"P{r}:Q{r}")
                    ws.cell(row=r, column=16).alignment = center
                    ws.cell(row=r, column=16).border = border_all

                # 单价 (R:T) — 留空给供方填写
                ws.merge_cells(f"R{r}:T{r}")
                ws.cell(row=r, column=18).alignment = center
                ws.cell(row=r, column=18).border = border_all

                # 补全边框 (所有列)
                for c_idx in range(2, 21):
                    ws.cell(row=r, column=c_idx).border = border_all

                current_row += 1

        # ── 打印设置（保持模板原有的横向打印）──
        ws.page_setup.orientation = 'landscape'

        wb.save(filepath)


# ============================
# 报价单产品表单弹窗
# ============================

class QuotationForm(ctk.CTkToplevel):
    """产品报价单新增/编辑表单"""

    def __init__(self, parent, db, C, oid=None, on_save=None):
        super().__init__(parent)
        self.db = db
        self.C = C
        self.oid = oid
        self.on_save = on_save
        self.tiers = []  # 阶梯价格列表
        self.title("编辑产品" if oid else "添加产品")
        self.geometry("800x680")
        self.configure(fg_color=self.C["bg"])
        self._build_ui()
        if oid:
            self._load_data()

    def _build_ui(self):
        canvas = ctk.CTkScrollableFrame(self, fg_color=self.C["bg"], corner_radius=0)
        canvas.pack(fill="both", expand=True, padx=16, pady=(12, 8))

        # ── 基本信息 ──
        info_frame = ctk.CTkFrame(canvas, fg_color=self.C["card"], corner_radius=10)
        info_frame.pack(fill="x", pady=(0, 12), padx=4)

        ctk.CTkLabel(
            info_frame, text="📦 产品信息",
            font=ctk.CTkFont(family="Microsoft YaHei", size=15, weight="bold"),
            text_color=self.C["text"],
        ).pack(anchor="w", padx=16, pady=(12, 8))

        fields = [
            ("项目号", "item_no_entry"),
            ("产品名称 *", "name_entry"),
            ("产品尺寸", "size_entry"),
            ("材质/工艺描述", "process_entry"),
            ("供货周期", "cycle_entry"),
            ("发货箱规", "carton_entry"),
            ("单位", "unit_entry"),
        ]
        self.entries = {}
        for label, attr in fields:
            r = ctk.CTkFrame(info_frame, fg_color="transparent")
            r.pack(fill="x", padx=16, pady=3)
            ctk.CTkLabel(r, text=label, width=100, anchor="w",
                         font=ctk.CTkFont(size=13)).pack(side="left")
            ent = ctk.CTkEntry(r, height=32, font=ctk.CTkFont(size=13))
            ent.pack(side="left", fill="x", expand=True, padx=(8, 0))
            self.entries[attr] = ent

        # 默认值
        self.entries["unit_entry"].insert(0, "PCS")

        # ── 阶梯价格 ──
        tier_frame = ctk.CTkFrame(canvas, fg_color=self.C["card"], corner_radius=10)
        tier_frame.pack(fill="x", pady=(0, 12), padx=4)

        tier_header = ctk.CTkFrame(tier_frame, fg_color="transparent")
        tier_header.pack(fill="x", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            tier_header, text="💰 阶梯价格",
            font=ctk.CTkFont(family="Microsoft YaHei", size=15, weight="bold"),
            text_color=self.C["text"],
        ).pack(side="left")

        ctk.CTkButton(
            tier_header, text="＋ 添加阶梯", width=100, height=30,
            fg_color=self.C["primary"], hover_color=self.C["primary_hover"],
            font=ctk.CTkFont(size=12), command=self._add_tier_row,
        ).pack(side="right")

        # 阶梯价格容器
        self.tier_container = ctk.CTkFrame(tier_frame, fg_color="transparent")
        self.tier_container.pack(fill="x", padx=16, pady=(4, 12))

        # 表头
        tier_hdr = ctk.CTkFrame(self.tier_container, fg_color=self.C["sidebar"], corner_radius=4)
        tier_hdr.pack(fill="x", pady=(0, 4))
        for text, w in [("最低数量", 120), ("最高数量(留空=无限)", 150), ("", 60)]:
            ctk.CTkLabel(tier_hdr, text=text, width=w, anchor="center",
                         font=ctk.CTkFont(size=11)).pack(side="left", padx=2, pady=2)

        # 预设提示
        hint = ctk.CTkLabel(
            self.tier_container,
            text="💡 提示：填入阶梯数量后，导出时每个阶梯会独立显示一行。如：100-499 ¥5.00 | 500-999 ¥4.50 | ≥1000 ¥4.00",
            font=ctk.CTkFont(size=11), text_color=self.C.get("text_secondary", "#8B7355"),
        )
        hint.pack(anchor="w", pady=(2, 6))

        # ── 底部按钮 ──
        btn_frame = ctk.CTkFrame(canvas, fg_color="transparent")
        btn_frame.pack(fill="x", pady=16, padx=4)

        ctk.CTkButton(
            btn_frame, text="💾 保存", width=100, height=38,
            fg_color=self.C["primary"], hover_color=self.C["primary_hover"],
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._save,
        ).pack(side="right", padx=8)

        ctk.CTkButton(
            btn_frame, text="取消", width=80, height=38,
            fg_color="#9CA3AF", hover_color="#6B7280",
            font=ctk.CTkFont(size=13), command=self.destroy,
        ).pack(side="right", padx=8)

    def _add_tier_row(self, data=None):
        """添加一行阶梯价格输入（只有数量，单价留供方填写）"""
        row = ctk.CTkFrame(self.tier_container, fg_color="transparent")
        row.pack(fill="x", pady=2)

        min_entry = ctk.CTkEntry(row, width=120, height=30, font=ctk.CTkFont(size=12),
                                  placeholder_text="最低数量，如：100")
        min_entry.pack(side="left", padx=4)

        max_entry = ctk.CTkEntry(row, width=150, height=30, font=ctk.CTkFont(size=12),
                                  placeholder_text="最高数量，留空=无上限")
        max_entry.pack(side="left", padx=4)

        def _remove():
            row.destroy()
            self.tiers = [t for t in self.tiers if t["row"] is not row]

        del_btn = ctk.CTkButton(row, text="✕", width=40, height=30,
                                fg_color=self.C["danger"], hover_color="#9A5555",
                                font=ctk.CTkFont(size=12), command=_remove)
        del_btn.pack(side="left", padx=4)

        tier_data = {"row": row, "min": min_entry, "max": max_entry}

        if data:
            min_entry.insert(0, str(data.get("min_qty", "")))
            if data.get("max_qty"):
                max_entry.insert(0, str(data["max_qty"]))

        self.tiers.append(tier_data)

    def _load_data(self):
        if not self.oid:
            return
        data = self.db.get_quotation_product(self.oid)
        if not data:
            return

        self.entries["item_no_entry"].insert(0, data.get("item_no", ""))
        self.entries["name_entry"].insert(0, data.get("product_name", ""))
        self.entries["size_entry"].insert(0, data.get("product_size", ""))
        self.entries["process_entry"].insert(0, data.get("material_process", ""))
        self.entries["cycle_entry"].insert(0, data.get("supply_cycle", ""))
        self.entries["carton_entry"].insert(0, data.get("carton_spec", ""))
        self.entries["unit_entry"].delete(0, "end")
        self.entries["unit_entry"].insert(0, data.get("unit", "PCS"))

        for t in data.get("tiers", []):
            self._add_tier_row(t)

    def _save(self):
        name = self.entries["name_entry"].get().strip()
        if not name:
            messagebox.showerror("错误", "请输入产品名称")
            return

        # 验证阶梯价格（只有数量，单价供方填写）
        valid_tiers = []
        for t in self.tiers:
            try:
                min_qty = int(t["min"].get().strip())
            except (ValueError, TypeError):
                messagebox.showerror("错误", "最低数量必须为整数")
                return
            max_val = t["max"].get().strip()
            max_qty = int(max_val) if max_val else None
            
            valid_tiers.append({
                "min_qty": min_qty,
                "max_qty": max_qty,
            })

        product_data = {
            "item_no": self.entries["item_no_entry"].get().strip(),
            "product_name": name,
            "product_size": self.entries["size_entry"].get().strip(),
            "material_process": self.entries["process_entry"].get().strip(),
            "supply_cycle": self.entries["cycle_entry"].get().strip(),
            "carton_spec": self.entries["carton_entry"].get().strip(),
            "unit": self.entries["unit_entry"].get().strip() or "PCS",
        }

        try:
            if self.oid:
                self.db.update_quotation_product(self.oid, product_data)
                self.db.delete_quotation_tiers(self.oid)
                pid = self.oid
            else:
                pid = self.db.save_quotation_product(product_data)

            for t in valid_tiers:
                self.db.save_quotation_tier({**t, "product_id": pid})

            messagebox.showinfo("成功", "产品已保存")
            if self.on_save:
                self.on_save()
            self.destroy()
        except Exception as e:
            messagebox.showerror("保存失败", str(e))


# ============================
# 报价单配置弹窗（需方信息）
# ============================

class QuotationConfigDialog(ctk.CTkToplevel):
    """需方信息和报价条款配置"""

    def __init__(self, parent, db, C, on_save=None):
        super().__init__(parent)
        self.db = db
        self.C = C
        self.on_save = on_save
        self.title("报价单配置 - 需方信息")
        self.geometry("700x600")
        self.configure(fg_color=self.C["bg"])
        self._build_ui()
        self._load_config()

    def _build_ui(self):
        canvas = ctk.CTkScrollableFrame(self, fg_color=self.C["bg"], corner_radius=0)
        canvas.pack(fill="both", expand=True, padx=16, pady=(12, 8))

        frame = ctk.CTkFrame(canvas, fg_color=self.C["card"], corner_radius=10)
        frame.pack(fill="x", padx=4)

        ctk.CTkLabel(
            frame, text="⚙ 需方信息与条款配置",
            font=ctk.CTkFont(family="Microsoft YaHei", size=15, weight="bold"),
            text_color=self.C["text"],
        ).pack(anchor="w", padx=16, pady=(12, 8))

        self.fields = {}
        config_fields = [
            ("需方名称", "buyer_name"),
            ("联系人", "buyer_contact"),
            ("联系方式", "buyer_phone"),
            ("送货地址", "buyer_address"),
            ("付款方式", "payment_terms"),
            ("运输方式", "transport_method"),
            ("发货文件要求", "delivery_docs"),
            ("报价要求", "quote_requirement"),
            ("模板说明", "quote_template_note"),
            ("底部注释", "footer_note"),
        ]

        for label, key in config_fields:
            r = ctk.CTkFrame(frame, fg_color="transparent")
            r.pack(fill="x", padx=16, pady=3)
            ctk.CTkLabel(r, text=label, width=110, anchor="w",
                         font=ctk.CTkFont(size=13)).pack(side="left")
            ent = ctk.CTkEntry(r, height=32, font=ctk.CTkFont(size=13))
            ent.pack(side="left", fill="x", expand=True, padx=(8, 0))
            self.fields[key] = ent

        # 底部按钮
        btn_frame = ctk.CTkFrame(canvas, fg_color="transparent")
        btn_frame.pack(fill="x", pady=16, padx=4)

        ctk.CTkButton(
            btn_frame, text="💾 保存配置", width=110, height=38,
            fg_color=self.C["primary"], hover_color=self.C["primary_hover"],
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._save,
        ).pack(side="right", padx=8)

        ctk.CTkButton(
            btn_frame, text="取消", width=80, height=38,
            fg_color="#9CA3AF", hover_color="#6B7280",
            font=ctk.CTkFont(size=13), command=self.destroy,
        ).pack(side="right", padx=8)

    def _load_config(self):
        cfg = self.db.get_quotation_config()
        for key, ent in self.fields.items():
            val = cfg.get(key, "")
            if val:
                ent.insert(0, str(val))

    def _save(self):
        data = {}
        for key, ent in self.fields.items():
            data[key] = ent.get().strip()
        try:
            self.db.update_quotation_config(data)
            messagebox.showinfo("成功", "报价单配置已保存")
            if self.on_save:
                self.on_save()
            self.destroy()
        except Exception as e:
            messagebox.showerror("保存失败", str(e))


# ============================
# 报价单供方配置弹窗
# ============================

class QuotationSupplierDialog(ctk.CTkToplevel):
    """供方信息配置"""
    
    def __init__(self, parent, db, C, on_save=None):
        super().__init__(parent)
        self.db = db
        self.C = C
        self.on_save = on_save
        self.title("报价单配置 - 供方信息")
        self.geometry("700x500")
        self.configure(fg_color=self.C["bg"])
        self._build_ui()
        self._load_config()
        
    def _build_ui(self):
        canvas = ctk.CTkScrollableFrame(self, fg_color=self.C["bg"], corner_radius=0)
        canvas.pack(fill="both", expand=True, padx=16, pady=(12, 8))
        
        frame = ctk.CTkFrame(canvas, fg_color=self.C["card"], corner_radius=10)
        frame.pack(fill="x", padx=4)
        
        ctk.CTkLabel(
            frame, text="⚙ 供方信息配置",
            font=ctk.CTkFont(family="Microsoft YaHei", size=15, weight="bold"),
            text_color=self.C["text"],
        ).pack(anchor="w", padx=16, pady=(12, 8))
        
        self.fields = {}
        config_fields = [
            ("供应商名称", "supplier_name"),
            ("联系人", "contact_person"),
            ("联系方式", "phone"),
            ("地址", "address"),
            ("报价日期", "quote_date"),
            ("报价有效期", "quote_validity"),
        ]
        
        for label, key in config_fields:
            r = ctk.CTkFrame(frame, fg_color="transparent")
            r.pack(fill="x", padx=16, pady=3)
            ctk.CTkLabel(r, text=label, width=110, anchor="w",
                         font=ctk.CTkFont(size=13)).pack(side="left")
            ent = ctk.CTkEntry(r, height=32, font=ctk.CTkFont(size=13))
            ent.pack(side="left", fill="x", expand=True, padx=(8, 0))
            self.fields[key] = ent
            
        # 底部按钮
        btn_frame = ctk.CTkFrame(canvas, fg_color="transparent")
        btn_frame.pack(fill="x", pady=16, padx=4)
        
        ctk.CTkButton(
            btn_frame, text="💾 保存配置", width=110, height=38,
            fg_color=self.C["primary"], hover_color=self.C["primary_hover"],
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._save,
        ).pack(side="right", padx=8)
        
        ctk.CTkButton(
            btn_frame, text="取消", width=80, height=38,
            fg_color="#9CA3AF", hover_color="#6B7280",
            font=ctk.CTkFont(size=13), command=self.destroy,
        ).pack(side="right", padx=8)
        
    def _load_config(self):
        cfg = self.db.get_quotation_supplier()
        for key, ent in self.fields.items():
            val = cfg.get(key, "")
            if val:
                ent.insert(0, str(val))
                
    def _save(self):
        data = {}
        for key, ent in self.fields.items():
            data[key] = ent.get().strip()
        try:
            self.db.update_quotation_supplier(data)
            messagebox.showinfo("成功", "供方配置已保存")
            if self.on_save:
                self.on_save()
            self.destroy()
        except Exception as e:
            messagebox.showerror("保存失败", str(e))
