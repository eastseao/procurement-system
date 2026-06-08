#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""物料查询页面 v1.2 - 默认不显示数据，需点击查询后才展示"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
import csv
import re
import os
from datetime import datetime


class QueryPage(ctk.CTkFrame):
    def __init__(self, parent, db, colors):
        super().__init__(parent, fg_color=colors["bg"], corner_radius=0)
        self.db = db
        self.C = colors
        self.raw_data = []       # 内存中的数据
        self.filtered_data = []  # 筛选后的数据
        self._sort_col = None
        self._sort_asc = True
        self._build()
        # v1.2：启动时只加载数据到内存，不自动显示
        self._load_from_db(show=False)

    def _build(self):
        # 顶部标题栏
        header = ctk.CTkFrame(self, fg_color=self.C["card"], corner_radius=0, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="物料查询",
                     font=ctk.CTkFont(family="Microsoft YaHei", size=20, weight="bold"),
                     text_color=self.C["text"]).pack(side="left", padx=24, pady=16)

        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right", padx=16)

        ctk.CTkButton(
            btn_frame, text="🗑  清除数据", width=100, height=34,
            fg_color="#FEE2E2", text_color=self.C["danger"],
            hover_color="#FECACA",
            font=ctk.CTkFont(family="Microsoft YaHei", size=13),
            command=self._clear_data
        ).pack(side="right", padx=4)

        ctk.CTkButton(
            btn_frame, text="📂  导入CSV", width=110, height=34,
            fg_color=self.C["primary"], hover_color=self.C["primary_hover"],
            font=ctk.CTkFont(family="Microsoft YaHei", size=13, weight="bold"),
            command=self._import_csv
        ).pack(side="right", padx=4)

        ctk.CTkButton(
            btn_frame, text="📤 导出Excel", width=110, height=34,
            fg_color=self.C["success"], hover_color="#7A9A6E",
            font=ctk.CTkFont(family="Microsoft YaHei", size=13, weight="bold"),
            command=self._export_xlsx
        ).pack(side="right", padx=4)

        self.import_status = ctk.CTkLabel(
            btn_frame, text="未导入数据", font=ctk.CTkFont(family="Microsoft YaHei", size=11),
            text_color=self.C["text_secondary"]
        )
        self.import_status.pack(side="right", padx=12)

        # === 筛选区域 ===
        filter_card = ctk.CTkFrame(self, fg_color=self.C["card"], corner_radius=10)
        filter_card.pack(fill="x", padx=16, pady=(12, 0))

        filter_inner = ctk.CTkFrame(filter_card, fg_color="transparent")
        filter_inner.pack(fill="x", padx=16, pady=14)

        row1 = ctk.CTkFrame(filter_inner, fg_color="transparent")
        row1.pack(fill="x", pady=4)

        # 年份下拉（不再实时触发查询，改为手动点查询）
        ctk.CTkLabel(row1, text="年份：", font=ctk.CTkFont(family="Microsoft YaHei", size=13),
                     text_color=self.C["text_secondary"]).pack(side="left")
        self.year_var = tk.StringVar(value="全部")
        self.year_combo = ctk.CTkComboBox(
            row1, values=["全部"], variable=self.year_var,
            width=100, height=34,
            font=ctk.CTkFont(family="Microsoft YaHei", size=13),
        )
        self.year_combo.pack(side="left", padx=(4, 18))

        # 供应商
        ctk.CTkLabel(row1, text="供应商：", font=ctk.CTkFont(family="Microsoft YaHei", size=13),
                     text_color=self.C["text_secondary"]).pack(side="left")
        self.supplier_var = tk.StringVar()
        ctk.CTkEntry(row1, textvariable=self.supplier_var, width=150, height=34,
                     font=ctk.CTkFont(family="Microsoft YaHei", size=13),
                     placeholder_text="模糊搜索…").pack(side="left", padx=(4, 18))

        # 物料名称
        ctk.CTkLabel(row1, text="物料名称：", font=ctk.CTkFont(family="Microsoft YaHei", size=13),
                     text_color=self.C["text_secondary"]).pack(side="left")
        self.name_var = tk.StringVar()
        ctk.CTkEntry(row1, textvariable=self.name_var, width=160, height=34,
                     font=ctk.CTkFont(family="Microsoft YaHei", size=13),
                     placeholder_text="模糊搜索…").pack(side="left", padx=(4, 18))

        # 物料项目号
        ctk.CTkLabel(row1, text="物料项目号：", font=ctk.CTkFont(family="Microsoft YaHei", size=13),
                     text_color=self.C["text_secondary"]).pack(side="left")
        self.item_no_var = tk.StringVar()
        item_entry = ctk.CTkEntry(row1, textvariable=self.item_no_var, width=140, height=34,
                     font=ctk.CTkFont(family="Microsoft YaHei", size=13),
                     placeholder_text="精准匹配…")
        item_entry.pack(side="left", padx=(4, 6))
        item_entry.bind("<Return>", lambda e: self._apply_filter())

        ctk.CTkButton(
            row1, text="查询", width=66, height=34,
            fg_color=self.C["primary"], hover_color=self.C["primary_hover"],
            font=ctk.CTkFont(family="Microsoft YaHei", size=13, weight="bold"),
            command=self._apply_filter
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(row1, text="重置", width=66, height=34,
                      fg_color="#F1F5F9", text_color=self.C["text"],
                      hover_color="#E2E8F0",
                      border_width=1, border_color=self.C["border"],
                      font=ctk.CTkFont(family="Microsoft YaHei", size=13),
                      command=self._reset_filter).pack(side="left")

        # 统计栏
        stats_frame = ctk.CTkFrame(self, fg_color=self.C["card"], corner_radius=10, height=52)
        stats_frame.pack(fill="x", padx=16, pady=8)
        stats_frame.pack_propagate(False)
        self.result_count_lbl = ctk.CTkLabel(
            stats_frame, text="请设置筛选条件后点击「查询」",
            font=ctk.CTkFont(family="Microsoft YaHei", size=13, weight="bold"),
            text_color=self.C["text_secondary"]
        )
        self.result_count_lbl.pack(side="left", padx=20, pady=12)
        self.result_total_lbl = ctk.CTkLabel(
            stats_frame, text="",
            font=ctk.CTkFont(family="Microsoft YaHei", size=13, weight="bold"),
            text_color=self.C["warning"]
        )
        self.result_total_lbl.pack(side="left", padx=20)

        # === 数据表格 ===
        table_frame = ctk.CTkFrame(self, fg_color=self.C["card"], corner_radius=10)
        table_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self._build_table(table_frame)

    def _build_table(self, parent):
        self.fixed_cols = [
            ("contract_no",    "合同编号",   150, "w"),
            ("supplier",       "供应商名称", 160, "w"),
            ("item_no",        "物料项目号", 130, "center"),
            ("material_name",  "物料名称",   200, "w"),
            ("quantity",       "数量",        80, "center"),
            ("unit",           "单位",        70, "center"),
            ("unit_price",     "采购单价",   100, "center"),
            ("amount",         "订单总额",   110, "center"),
        ]

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Query.Treeview",
                         font=("Microsoft YaHei", 11),
                         rowheight=36,
                         background="#FFFFFF",
                         fieldbackground="#FFFFFF",
                         foreground="#1E293B",
                         borderwidth=0,
                         relief="flat")
        style.configure("Query.Treeview.Heading",
                         font=("Microsoft YaHei", 11, "bold"),
                         background="#F8FAFC",
                         foreground="#475569",
                         relief="flat",
                         borderwidth=0)
        style.map("Query.Treeview",
                  background=[("selected", "#E8D5C4")],
                  foreground=[("selected", "#4A3728")])
        style.layout("Query.Treeview", [
            ("Treeview.treearea", {"sticky": "nswe"})
        ])

        tree_wrap = tk.Frame(parent, bg="#FFFFFF")
        tree_wrap.pack(fill="both", expand=True, padx=8, pady=8)

        self.tree = ttk.Treeview(
            tree_wrap, style="Query.Treeview",
            columns=[c[0] for c in self.fixed_cols],
            show="headings", selectmode="browse"
        )
        for cid, label, width, anchor in self.fixed_cols:
            self.tree.heading(cid, text=label,
                              command=lambda c=cid: self._sort_by_col(c))
            self.tree.column(cid, width=width, minwidth=50, anchor=anchor)

        vsb = ttk.Scrollbar(tree_wrap, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_wrap, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.tag_configure("odd", background="#F8FAFC")
        self.tree.tag_configure("even", background="#FFFFFF")
        self.tree.bind("<ButtonRelease-1>", self._on_tree_click)

    def _on_tree_click(self, event):
        """单击选中行高亮"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)

    def _load_from_db(self, show=True):
        """从数据库加载已持久化的物料台账数据。show=False时不渲染表格（v1.2默认行为）"""
        rows = self.db.get_material_ledger()
        if not rows:
            return
        self.raw_data = rows
        years = sorted(set(
            r["year"] for r in rows if r.get("year")
        ), reverse=True)
        self.year_combo.configure(values=["全部"] + years)
        self.import_status.configure(
            text=f"已加载 {len(rows)} 条（点击查询显示）", text_color=self.C.get("text_secondary", "#5D5D5D")
        )
        if show:
            self._apply_filter()

    def _import_csv(self):
        filepath = filedialog.askopenfilename(
            title="选择CSV文件",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )
        if not filepath:
            return

        try:
            data = []
            for encoding in ["utf-8-sig", "gbk", "gb2312", "utf-8"]:
                try:
                    with open(filepath, "r", encoding=encoding, newline="") as f:
                        reader = csv.DictReader(f)
                        rows = list(reader)
                        if rows:
                            data = rows
                            break
                except (UnicodeDecodeError, Exception):
                    continue

            if not data:
                messagebox.showerror("导入失败", "无法读取CSV文件，请检查文件格式和编码")
                return

            col_map = self._detect_columns(list(data[0].keys()))
            parsed_rows = [self._parse_row(row, col_map) for row in data]

            self.db.save_material_ledger(parsed_rows)
            self.raw_data = self.db.get_material_ledger()

            years = sorted(set(
                r["year"] for r in self.raw_data if r.get("year")
            ), reverse=True)
            self.year_combo.configure(values=["全部"] + years)
            self.year_var.set("全部")

            self.import_status.configure(
                text=f"✅ 已导入 {len(self.raw_data)} 条", text_color=self.C["success"]
            )
            self._apply_filter()
            messagebox.showinfo("导入成功", f"成功导入 {len(self.raw_data)} 条物料数据\n数据已保存，下次启动无需重新导入。")

        except Exception as e:
            messagebox.showerror("导入失败", f"读取CSV文件出错：{str(e)}")

    def _detect_columns(self, headers):
        mapping = {}
        hlist = [h.strip() for h in headers]
        patterns = {
            "contract_no":   ["合同编号", "合同号", "编号", "contract"],
            "supplier":      ["供应商名称", "供应商", "厂商", "vendor", "supplier"],
            "item_no":       ["物料项目号", "项目号", "物料号", "item_no", "itemno", "物料编码", "料号"],
            "material_name": ["物料名称", "品名", "产品名", "material"],
            "quantity":      ["数量", "qty", "quantity"],
            "unit":          ["单位", "unit", "计量单位"],
            "unit_price":    ["采购单价", "含税单价", "单价", "价格", "unit_price", "price"],
            "amount":        ["订单总额", "含税金额", "金额", "总价", "合计", "amount", "total"],
        }
        used = set()
        for field, candidates in patterns.items():
            for h in hlist:
                for c in candidates[:3]:
                    if c.lower() == h.lower() and h not in used:
                        mapping[field] = h
                        used.add(h)
                        break
                if field in mapping:
                    break
            if field in mapping:
                continue
            for h in hlist:
                if h in used:
                    continue
                hl = h.lower()
                for c in candidates:
                    if len(c) >= 3 and c.lower() in hl and hl.index(c.lower()) == 0:
                        mapping[field] = h
                        used.add(h)
                        break
                    elif len(c) >= 4 and c.lower() in hl:
                        mapping[field] = h
                        used.add(h)
                        break
                if field in mapping:
                    break
            if field in mapping:
                continue
            for h in hlist:
                if h in used:
                    continue
                hl = h.lower()
                if any(c.lower() in hl for c in candidates):
                    mapping[field] = h
                    used.add(h)
                    break
        return mapping

    def _parse_row(self, row, col_map):
        def get(field):
            key = col_map.get(field)
            return row.get(key, "").strip() if key else ""

        contract_no = get("contract_no") or ""
        year = self._extract_year(contract_no) or ""

        def to_float(s):
            try:
                return float(s.replace(",", "")) if s else 0.0
            except (ValueError, AttributeError):
                return 0.0

        return {
            "contract_no":   contract_no,
            "supplier":      get("supplier"),
            "item_no":       get("item_no"),
            "material_name": get("material_name"),
            "quantity":      to_float(get("quantity")),
            "unit":          get("unit"),
            "unit_price":    to_float(get("unit_price")),
            "amount":        to_float(get("amount")),
            "year":          year,
            "_raw":          row,
        }

    def _extract_year(self, text):
        if not text:
            return None
        m = re.search(r"(20\d{2})", text)
        return m.group(1) if m else None

    def _apply_filter(self):
        """执行查询并渲染表格（v1.2：只有调用此方法才会显示数据）"""
        year_f     = self.year_var.get()
        supplier_f = self.supplier_var.get().strip().lower()
        name_f     = self.name_var.get().strip().lower()
        item_no_f  = self.item_no_var.get().strip()

        self.filtered_data = []
        for r in self.raw_data:
            if year_f != "全部" and r.get("year", "") != year_f:
                continue
            if supplier_f and supplier_f not in (r.get("supplier") or "").lower():
                continue
            if name_f and name_f not in (r.get("material_name") or "").lower():
                continue
            if item_no_f and item_no_f != (r.get("item_no") or "").strip():
                continue
            self.filtered_data.append(r)

        self._render_table()

    def _render_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        total_amount = 0
        for i, r in enumerate(self.filtered_data):
            tag = "odd" if i % 2 == 0 else "even"
            qty = r.get("quantity") or 0
            qty_str = f"{qty:.0f}" if qty == int(qty) else str(qty)
            up = r.get("unit_price") or 0
            amt = r.get("amount") or 0
            self.tree.insert("", "end", values=(
                r.get("contract_no") or "—",
                r.get("supplier") or "—",
                r.get("item_no") or "—",
                r.get("material_name") or "—",
                qty_str if qty else "—",
                r.get("unit") or "—",
                f"¥{up:,.2f}" if up else "—",
                f"¥{amt:,.2f}" if amt else "—",
            ), tags=(tag,))
            total_amount += amt

        count = len(self.filtered_data)
        self.result_count_lbl.configure(text=f"共 {count} 条记录", text_color=self.C["primary"])
        self.result_total_lbl.configure(text=f"订单总额：¥ {total_amount:,.2f}")

    def _reset_filter(self):
        self.year_var.set("全部")
        self.supplier_var.set("")
        self.name_var.set("")
        self.item_no_var.set("")
        # v1.2：重置后清空表格，不自动重新查询
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.result_count_lbl.configure(
            text="请设置筛选条件后点击「查询」",
            text_color=self.C.get("text_secondary", "#5D5D5D")
        )
        self.result_total_lbl.configure(text="")
        self.filtered_data = []

    def _clear_data(self):
        if not self.raw_data:
            messagebox.showinfo("提示", "当前没有数据")
            return
        if messagebox.askyesno("确认清除", f"确定清除已导入的 {len(self.raw_data)} 条数据？\n清除后下次启动也不会自动加载。"):
            self.db.clear_material_ledger()
            self.raw_data.clear()
            self.filtered_data.clear()
            for row in self.tree.get_children():
                self.tree.delete(row)
            self.year_combo.configure(values=["全部"])
            self.year_var.set("全部")
            self.import_status.configure(text="未导入数据", text_color=self.C.get("text_secondary", "#5D5D5D"))
            self.result_count_lbl.configure(text="请设置筛选条件后点击「查询」",
                                             text_color=self.C.get("text_secondary", "#5D5D5D"))
            self.result_total_lbl.configure(text="")

    def _sort_by_col(self, col):
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True

        def sort_key(r):
            v = r.get(col, "")
            if col in ("amount", "unit_price", "quantity"):
                try:
                    return float(v or 0)
                except (ValueError, TypeError):
                    return 0
            return str(v or "").lower()

        self.filtered_data.sort(key=sort_key, reverse=not self._sort_asc)
        self._render_table()

    def _import_json(self):
        import json as _json
        filepath = filedialog.askopenfilename(
            title="选择JSON文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if not filepath:
            return

        try:
            content = None
            for encoding in ["utf-8-sig", "utf-8", "gbk", "gb2312"]:
                try:
                    with open(filepath, "r", encoding=encoding) as f:
                        content = _json.load(f)
                    break
                except (UnicodeDecodeError, _json.JSONDecodeError):
                    continue

            if content is None:
                messagebox.showerror("导入失败", "无法解析JSON文件，请检查文件格式和编码")
                return

            if isinstance(content, list):
                data = content
            elif isinstance(content, dict):
                data = None
                for v in content.values():
                    if isinstance(v, list) and v:
                        data = v
                        break
                if data is None:
                    messagebox.showerror("导入失败", "JSON文件中未找到有效的数据列表")
                    return
            else:
                messagebox.showerror("导入失败", "JSON格式不支持，需要数组或含数组的对象")
                return

            if not data:
                messagebox.showwarning("提示", "JSON文件中没有数据")
                return

            if not isinstance(data[0], dict):
                messagebox.showerror("导入失败", "JSON数组元素必须是对象（{key:value}）")
                return

            col_map = self._detect_columns(list(data[0].keys()))
            parsed_rows = [self._parse_row(row, col_map) for row in data]

            self.db.save_material_ledger(parsed_rows)
            self.raw_data = self.db.get_material_ledger()

            years = sorted(set(
                r["year"] for r in self.raw_data if r.get("year")
            ), reverse=True)
            self.year_combo.configure(values=["全部"] + years)
            self.year_var.set("全部")

            self.import_status.configure(
                text=f"✅ 已导入 {len(self.raw_data)} 条", text_color=self.C["success"]
            )
            self._apply_filter()
            messagebox.showinfo("导入成功", f"成功从JSON导入 {len(self.raw_data)} 条物料数据\n数据已保存，下次启动无需重新导入。")

        except Exception as e:
            messagebox.showerror("导入失败", f"读取JSON文件出错：{str(e)}")

    def _export_xlsx(self):
        data = self.filtered_data if self.filtered_data else self.raw_data
        if not data:
            messagebox.showinfo("提示", "没有可导出的数据，请先执行查询")
            return

        filepath = filedialog.asksaveasfilename(
            title="导出物料台账", defaultextension=".xlsx",
            filetypes=[("Excel文件", "*.xlsx")],
            initialfile=f"物料台账_{datetime.now().strftime('%Y%m%d')}.xlsx"
        )
        if not filepath:
            return

        headers = ["合同编号", "供应商名称", "物料项目号", "物料名称",
                    "数量", "单位", "采购单价", "订单总额"]
        rows = []
        for r in data:
            qty = r.get("quantity") or 0
            up = r.get("unit_price") or 0
            amt = r.get("amount") or 0
            rows.append({
                "合同编号": r.get("contract_no") or "",
                "供应商名称": r.get("supplier") or "",
                "物料项目号": r.get("item_no") or "",
                "物料名称": r.get("material_name") or "",
                "数量": qty,
                "单位": r.get("unit") or "",
                "采购单价": f"¥{up:,.2f}" if up else "",
                "订单总额": f"¥{amt:,.2f}" if amt else "",
            })

        try:
            self.db.export_to_xlsx(filepath, "物料台账", headers, rows,
                                   col_widths=[16, 16, 14, 20, 8, 6, 12, 12])
            messagebox.showinfo("导出成功", f"已导出 {len(rows)} 条记录到：\n{filepath}")
        except Exception as e:
            messagebox.showerror("导出失败", str(e))
