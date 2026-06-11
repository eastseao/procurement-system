#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""成品BOM页面 - V1.9.7 从 BOM管理系统 集成"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk


class ProductBomPage(ctk.CTkFrame):
    def __init__(self, parent, db, colors):
        super().__init__(parent, fg_color=colors["bg"], corner_radius=0)
        self.C = colors
        self.db = db
        self._all_data = []
        self._build()

    def _build(self):
        # ── 顶部标题栏 ─────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0, height=52)
        header.pack(fill="x", padx=20, pady=(16, 8))
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="BOM查询",
            font=ctk.CTkFont(family="Microsoft YaHei", size=16, weight="bold"),
            text_color=self.C["text"],
        ).pack(side="left", pady=14)

        # ── 筛选区 ─────────────────────────────────
        filter_frame = ctk.CTkFrame(self, fg_color=self.C["card"], corner_radius=10)
        filter_frame.pack(fill="x", padx=16, pady=(16, 8))

        filter_inner = ctk.CTkFrame(filter_frame, fg_color="transparent")
        filter_inner.pack(fill="x", padx=16, pady=12)

        # 第一行：品名 + 成品项目号 + 物料项目号
        row1 = ctk.CTkFrame(filter_inner, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(row1, text="品名", font=ctk.CTkFont(family="Microsoft YaHei", size=13),
                     text_color=self.C["text_secondary"], width=70).pack(side="left", padx=(0, 4))
        self.product_name_entry = ctk.CTkEntry(
            row1, width=140, placeholder_text="支持模糊搜索",
            font=ctk.CTkFont(family="Microsoft YaHei", size=13),
            fg_color=self.C["bg"], border_color=self.C["border"],
        )
        self.product_name_entry.pack(side="left", padx=(0, 16))

        ctk.CTkLabel(row1, text="成品项目号", font=ctk.CTkFont(family="Microsoft YaHei", size=13),
                     text_color=self.C["text_secondary"], width=70).pack(side="left", padx=(0, 4))
        self.finished_project_no_entry = ctk.CTkEntry(
            row1, width=140,
            font=ctk.CTkFont(family="Microsoft YaHei", size=13),
            fg_color=self.C["bg"], border_color=self.C["border"],
        )
        self.finished_project_no_entry.pack(side="left", padx=(0, 16))

        ctk.CTkLabel(row1, text="物料项目号", font=ctk.CTkFont(family="Microsoft YaHei", size=13),
                     text_color=self.C["text_secondary"], width=70).pack(side="left", padx=(0, 4))
        self.material_project_no_entry = ctk.CTkEntry(
            row1, width=140,
            font=ctk.CTkFont(family="Microsoft YaHei", size=13),
            fg_color=self.C["bg"], border_color=self.C["border"],
        )
        self.material_project_no_entry.pack(side="left")

        # 第二行：物料名称
        row2 = ctk.CTkFrame(filter_inner, fg_color="transparent")
        row2.pack(fill="x")

        ctk.CTkLabel(row2, text="物料名称", font=ctk.CTkFont(family="Microsoft YaHei", size=13),
                     text_color=self.C["text_secondary"], width=70).pack(side="left", padx=(0, 4))
        self.material_name_entry = ctk.CTkEntry(
            row2, width=140, placeholder_text="支持模糊搜索",
            font=ctk.CTkFont(family="Microsoft YaHei", size=13),
            fg_color=self.C["bg"], border_color=self.C["border"],
        )
        self.material_name_entry.pack(side="left")

        # 第三行：按钮
        row3 = ctk.CTkFrame(filter_inner, fg_color="transparent")
        row3.pack(fill="x", pady=(6, 0))

        self.query_btn = ctk.CTkButton(
            row3, text="🔍 查询", width=90, height=34,
            fg_color=self.C["primary"], hover_color=self.C["primary_hover"],
            font=ctk.CTkFont(family="Microsoft YaHei", size=14),
            command=self._on_query, corner_radius=20,
        )
        self.query_btn.pack(side="left", padx=(0, 8))

        self.reset_btn = ctk.CTkButton(
            row3, text="🔄 重置", width=90, height=34,
            fg_color="transparent", text_color=self.C["primary"],
            border_color=self.C["border"], border_width=1,
            font=ctk.CTkFont(family="Microsoft YaHei", size=14),
            command=self._on_reset, corner_radius=20,
        )
        self.reset_btn.pack(side="left", padx=(0, 16))

        self.import_btn = ctk.CTkButton(
            row3, text="📥 导入Excel", width=100, height=34,
            fg_color=self.C["success"], hover_color="#7A9472",
            font=ctk.CTkFont(family="Microsoft YaHei", size=14),
            command=self._on_import, corner_radius=20,
        )
        self.import_btn.pack(side="left", padx=(0, 8))

        self.export_btn = ctk.CTkButton(
            row3, text="📤 导出Excel", width=100, height=34,
            fg_color=self.C["warning"], hover_color="#B89A5D",
            font=ctk.CTkFont(family="Microsoft YaHei", size=14),
            command=self._on_export, corner_radius=20,
        )
        self.export_btn.pack(side="left")

        ctk.CTkButton(
            row3, text="➕ 新增BOM", width=90, height=34,
            fg_color="transparent", text_color=self.C["success"],
            border_color=self.C["success"], border_width=1,
            font=ctk.CTkFont(family="Microsoft YaHei", size=14),
            command=self._on_add, corner_radius=20,
        ).pack(side="right")

        # ── 表格区 ─────────────────────────────────
        table_frame = ctk.CTkFrame(self, fg_color=self.C["card"], corner_radius=10)
        table_frame.pack(fill="both", expand=True, padx=16, pady=(8, 16))

        self._build_treeview(table_frame)

    def _build_treeview(self, parent):
        """构建Treeview表格"""
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Bom.Treeview",
                        background=self.C["card"],
                        fieldbackground=self.C["card"],
                        foreground=self.C["text"],
                        rowheight=32,
                        font=("Microsoft YaHei", 9),
                        borderwidth=0)
        style.configure("Bom.Treeview.Heading",
                        background=self.C["primary"],
                        foreground="#FFFFFF",
                        font=("Microsoft YaHei", 9, "bold"),
                        relief="flat",
                        borderwidth=0,
                        padding=(6, 6))
        style.map("Bom.Treeview.Heading",
                  background=[("active", self.C["primary_hover"])])
        style.map("Bom.Treeview",
                  background=[("selected", self.C["primary_light"])],
                  foreground=[("selected", self.C["text"])])

        self.columns = ["成品项目号", "品名", "规格", "零售价（元）", "品牌",
                        "物料项目号", "物料名称", "数量", "计量单位"]

        tree_container = ctk.CTkFrame(parent, fg_color="transparent")
        tree_container.pack(fill="both", expand=True, padx=8, pady=8)

        self.tree = ttk.Treeview(
            tree_container,
            columns=self.columns,
            show="headings",
            style="Bom.Treeview",
        )

        col_widths = [110, 150, 80, 90, 90, 120, 150, 70, 80]
        for col, width in zip(self.columns, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, minwidth=60, stretch=True, anchor="center")

        vsb = ctk.CTkScrollbar(tree_container, orientation="vertical", command=self.tree.yview, button_color=self.C["border"], button_hover_color=self.C.get("sidebar_hover", "#ddd"), width=8)
        hsb = ctk.CTkScrollbar(tree_container, orientation="horizontal", command=self.tree.xview, button_color=self.C["border"], button_hover_color=self.C.get("sidebar_hover", "#ddd"), width=8, height=8)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        self.tree.bind("<Double-1>", self._on_double_click)

    def _on_query(self):
        """查询BOM数据"""
        product_name = self.product_name_entry.get().strip()
        finished_project_no = self.finished_project_no_entry.get().strip()
        material_project_no = self.material_project_no_entry.get().strip()
        material_name = self.material_name_entry.get().strip()

        data = self.db.get_product_bom(
            product_name=product_name if product_name else None,
            finished_project_no=finished_project_no if finished_project_no else None,
            material_project_no=material_project_no if material_project_no else None,
            material_name=material_name if material_name else None,
        )
        self._all_data = data
        self._refresh_table(data)

    def _on_reset(self):
        """重置筛选条件"""
        self.product_name_entry.delete(0, "end")
        self.finished_project_no_entry.delete(0, "end")
        self.material_project_no_entry.delete(0, "end")
        self.material_name_entry.delete(0, "end")
        self._all_data = []
        self._clear_table()

    def _on_add(self):
        """新增BOM记录"""
        self._show_edit_dialog({})

    def _on_import(self):
        """从Excel导入BOM数据"""
        filepath = filedialog.askopenfilename(
            title="选择Excel文件",
            filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")]
        )
        if not filepath:
            return

        try:
            from openpyxl import load_workbook
            wb = load_workbook(filepath)
            ws = wb.active

            rows = []
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row[0]:
                    continue
                rows.append({
                    "finished_project_no": str(row[0]) if row[0] else "",
                    "product_name": str(row[1]) if row[1] else "",
                    "spec": str(row[2]) if row[2] else "",
                    "retail_price": float(row[3]) if row[3] and str(row[3]).strip() else 0,
                    "brand": str(row[4]) if row[4] else "",
                    "material_project_no": str(row[5]) if row[5] else "",
                    "material_name": str(row[6]) if row[6] else "",
                    "quantity": float(row[7]) if row[7] and str(row[7]).strip() else 0,
                    "unit": str(row[8]) if row[8] else "",
                })

            if rows:
                self.db.import_product_bom(rows)
                messagebox.showinfo("导入成功", f"成功导入 {len(rows)} 条BOM数据")
                self._on_query()
            else:
                messagebox.showwarning("提示", "未找到有效数据")
        except Exception as e:
            messagebox.showerror("导入失败", f"导入Excel时出错：\n{e}")

    def _on_export(self):
        """导出BOM数据到Excel"""
        if not self._all_data:
            messagebox.showwarning("提示", "当前没有数据可导出，请先查询")
            return

        filepath = filedialog.asksaveasfilename(
            title="导出Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel文件", "*.xlsx")],
            initialfile="成品BOM导出.xlsx",
        )
        if not filepath:
            return

        try:
            headers = self.columns
            rows = []
            for d in self._all_data:
                rows.append({
                    "成品项目号": d.get("finished_project_no", ""),
                    "品名": d.get("product_name", ""),
                    "规格": d.get("spec", ""),
                    "零售价（元）": d.get("retail_price", 0),
                    "品牌": d.get("brand", ""),
                    "物料项目号": d.get("material_project_no", ""),
                    "物料名称": d.get("material_name", ""),
                    "数量": d.get("quantity", 0),
                    "计量单位": d.get("unit", ""),
                })
            self.db.export_to_xlsx(filepath, "成品BOM", headers, rows)
            messagebox.showinfo("导出成功", f"成功导出 {len(rows)} 条记录")
        except Exception as e:
            messagebox.showerror("导出失败", f"导出Excel时出错：\n{e}")

    def _on_double_click(self, event):
        """双击编辑行"""
        item = self.tree.selection()
        if not item:
            return
        idx = self.tree.index(item[0])
        if idx >= len(self._all_data):
            return

        record = self._all_data[idx]
        self._show_edit_dialog(record)

    def _show_edit_dialog(self, record):
        """显示编辑/新增对话框"""
        is_new = not record.get("id")
        dialog = tk.Toplevel(self)
        dialog.title("新增BOM记录" if is_new else "编辑BOM记录")
        dialog.geometry("480x520")
        dialog.resizable(False, False)
        dialog.configure(bg=self.C["card"])
        dialog.transient(self)
        dialog.grab_set()

        dialog.update_idletasks()
        dw, dh = 480, 520
        sw = dialog.winfo_screenwidth()
        sh = dialog.winfo_screenheight()
        dialog.geometry(f"{dw}x{dh}+{(sw-dw)//2}+{(sh-dh)//2}")

        fields = [
            ("成品项目号", "finished_project_no"),
            ("品名", "product_name"),
            ("规格", "spec"),
            ("零售价（元）", "retail_price"),
            ("品牌", "brand"),
            ("物料项目号", "material_project_no"),
            ("物料名称", "material_name"),
            ("数量", "quantity"),
            ("计量单位", "unit"),
        ]

        entries = {}
        for label, key in fields:
            ctk.CTkLabel(dialog, text=label,
                         font=ctk.CTkFont(family="Microsoft YaHei", size=13),
                         text_color=self.C["text"]).pack(anchor="w", padx=24, pady=(8, 2))

            var = tk.StringVar(value=str(record.get(key, "")) if record.get(key) is not None else "")
            entry = ctk.CTkEntry(
                dialog, textvariable=var, width=420,
                font=ctk.CTkFont(family="Microsoft YaHei", size=13),
                fg_color=self.C["bg"], border_color=self.C["border"],
            )
            entry.pack(padx=24)
            entries[key] = var

        def _save():
            data = {key: var.get().strip() for key, var in entries.items()}
            try:
                data["retail_price"] = float(data["retail_price"]) if data["retail_price"] else 0
            except ValueError:
                data["retail_price"] = 0
            try:
                data["quantity"] = float(data["quantity"]) if data["quantity"] else 0
            except ValueError:
                data["quantity"] = 0

            if not data["finished_project_no"] or not data["material_project_no"]:
                messagebox.showwarning("提示", "成品项目号和物料项目号不能为空")
                return

            if is_new:
                self.db.save_product_bom(data)
            else:
                self.db.update_product_bom(record["id"], data)

            dialog.destroy()
            self._on_query()
            messagebox.showinfo("成功", "保存成功")

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(16, 16))

        ctk.CTkButton(
            btn_frame, text="✓ 保存", width=100, height=36,
            fg_color=self.C["success"], hover_color="#7A9472",
            font=ctk.CTkFont(family="Microsoft YaHei", size=14, weight="bold"),
            command=_save, corner_radius=20,
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            btn_frame, text="取消", width=80, height=36,
            fg_color="transparent", text_color=self.C["text_secondary"],
            border_color=self.C["border"], border_width=1,
            font=ctk.CTkFont(family="Microsoft YaHei", size=14),
            command=dialog.destroy, corner_radius=20,
        ).pack(side="right")

        if not is_new:
            ctk.CTkButton(
                btn_frame, text="🗑 删除", width=80, height=36,
                fg_color=self.C["danger"], hover_color="#A05A5A",
                font=ctk.CTkFont(family="Microsoft YaHei", size=14),
                command=lambda: self._on_delete(record["id"], dialog), corner_radius=20,
            ).pack(side="left")

    def _on_delete(self, item_id, dialog):
        """删除BOM记录"""
        if messagebox.askyesno("确认删除", "确定要删除这条BOM记录吗？"):
            self.db.delete_product_bom(item_id)
            dialog.destroy()
            self._on_query()
            messagebox.showinfo("成功", "删除成功")

    def _refresh_table(self, data):
        """刷新表格数据 - 相同成品信息合并显示（首行显示，后续行留空）"""
        self._clear_table()
        if not data:
            return

        groups = []
        current_key = None
        current_group = []

        for d in data:
            key = (
                d.get("finished_project_no", ""),
                d.get("product_name", ""),
                d.get("spec", ""),
                d.get("retail_price", 0),
                d.get("brand", ""),
            )
            if key != current_key:
                if current_group:
                    groups.append((current_key, current_group))
                current_key = key
                current_group = [d]
            else:
                current_group.append(d)
        if current_group:
            groups.append((current_key, current_group))

        for key, rows in groups:
            d0 = rows[0]
            values = (
                key[0], key[1], key[2], key[3], key[4],
                d0.get("material_project_no", ""),
                d0.get("material_name", ""),
                d0.get("quantity", 0),
                d0.get("unit", ""),
            )
            self.tree.insert("", "end", values=values)

            for d in rows[1:]:
                values = (
                    "", "", "", "", "",
                    d.get("material_project_no", ""),
                    d.get("material_name", ""),
                    d.get("quantity", 0),
                    d.get("unit", ""),
                )
                self.tree.insert("", "end", values=values)

    def _clear_table(self):
        """清空表格"""
        for item in self.tree.get_children():
            self.tree.delete(item)
