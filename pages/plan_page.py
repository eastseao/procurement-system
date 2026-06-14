#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""计划页面 — 手动添加物料或导入PDF计划单，使用Treeview表格展示"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os, json, re
from datetime import datetime


class PlanPage(ctk.CTkFrame):
    """计划页面：管理采购计划物料清单，表格样式与下单页一致"""

    def __init__(self, parent, db, C):
        super().__init__(parent, fg_color=C["bg"], corner_radius=0)
        self.db = db
        self.C = C
        self._records = []
        self._show_archived = False
        self._build_ui()
        self._load_data()

    # ── UI 构建 ───────────────────────────────────────
    def _build_ui(self):
        C = self.C

        # ── 顶部工具栏 ──
        toolbar = ctk.CTkFrame(self, fg_color="transparent", height=44)
        toolbar.pack(fill="x", padx=20, pady=(12, 8))
        toolbar.pack_propagate(False)

        btn_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        btn_frame.pack(side="left", pady=5)

        # 手动添加物料按钮
        ctk.CTkButton(
            btn_frame, text="✚ 手动添加", width=110, height=34,
            fg_color=C["primary"], hover_color=C["primary_hover"],
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._open_add_dialog, corner_radius=8,
            text_color="#000000",
        ).pack(side="left", padx=4)

        # 导入文件按钮（PDF / Excel / CSV）
        ctk.CTkButton(
            btn_frame, text="📄 导入文件", width=110, height=34,
            fg_color="transparent", hover_color="#7A9A6E",
            font=ctk.CTkFont(size=13),
            command=self._import_file, corner_radius=8,
            border_width=1, border_color=C["border"],
            text_color="#000000",
        ).pack(side="left", padx=4)

        # 导出按钮
        ctk.CTkButton(
            btn_frame, text="📥 导出", width=90, height=34,
            fg_color="transparent", hover_color="#7A9A6E",
            font=ctk.CTkFont(size=13),
            command=self._export_xlsx, corner_radius=8,
            border_width=1, border_color=C["border"],
            text_color="#000000",
        ).pack(side="left", padx=4)

        # 刷新按钮
        ctk.CTkButton(
            btn_frame, text="🔄 刷新", width=90, height=34,
            fg_color="transparent", hover_color=C["sidebar_hover"],
            font=ctk.CTkFont(size=13),
            command=self._load_data, corner_radius=8,
            border_width=1, border_color=C["border"],
            text_color="#000000",
        ).pack(side="left", padx=4)

        # 已归档按钮
        self._archived_btn = ctk.CTkButton(
            btn_frame, text="📁 已归档", width=90, height=34,
            fg_color="transparent", hover_color=C["sidebar_hover"],
            font=ctk.CTkFont(size=13),
            command=self._toggle_archived, corner_radius=8,
            border_width=1, border_color=C["border"],
            text_color="#000000",
        )
        self._archived_btn.pack(side="left", padx=4)

        # 删除选中按钮
        ctk.CTkButton(
            btn_frame, text="🗑 删除", width=90, height=34,
            fg_color="transparent", hover_color="#B56A6A",
            font=ctk.CTkFont(size=13),
            command=self._delete_selected, corner_radius=8,
            border_width=1, border_color=C["border"],
            text_color="#000000",
        ).pack(side="left", padx=4)

        # 统计信息（右侧）
        self.stats_label = ctk.CTkLabel(
            toolbar, text="共 0 条计划",
            font=ctk.CTkFont(size=12),
            text_color=C["text_secondary"],
        )
        self.stats_label.pack(side="right", padx=(0, 8))

        # ═══════════════════════════════════════════
        # 表格区域：与下单页面一致的三层阴影 + ttk.Treeview
        # ═══════════════════════════════════════════

        # z1（外层阴影）
        z1_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=16)
        z1_frame.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        # z2（中层）
        z2_frame = ctk.CTkFrame(z1_frame, fg_color="transparent", corner_radius=8,
            border_width=1, border_color="#8B7D6B")
        z2_frame.pack(fill="both", expand=True, padx=4, pady=4)

        # z3（上层卡片）
        table_frame = ctk.CTkFrame(z2_frame, fg_color=C["card"], corner_radius=C["radius_card"])
        table_frame.pack(fill="both", expand=True, padx=4, pady=4)

        # 列定义：序号、审批编号、采购明细序号、名称、规格、单位、数量、操作
        columns = ("序号", "审批编号", "采购明细序号", "名称", "规格", "单位", "数量", "操作")

        # ttk.Treeview 样式（与下单页一致）
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Plan.Treeview",
            font=("Microsoft YaHei", 9),
            rowheight=36,
            background="#FFFFFF",
            fieldbackground="#FFFFFF",
            foreground="#1E293B",
            borderwidth=0,
            relief="flat")
        style.configure("Plan.Treeview.Heading",
            font=("Microsoft YaHei", 9, "bold"),
            background="#F8FAFC",
            foreground="#475569",
            relief="flat",
            borderwidth=0)
        style.map("Plan.Treeview",
            background=[("selected", "#E8D5C4")],
            foreground=[("selected", "#4A3728")])
        style.layout("Plan.Treeview", [
            ("Treeview.treearea", {"sticky": "nswe"})
        ])

        tree_wrap = tk.Frame(table_frame, bg="#FFFFFF")
        tree_wrap.pack(fill="both", expand=True, padx=8, pady=8)

        self.tree = ttk.Treeview(
            tree_wrap, style="Plan.Treeview",
            columns=columns, show="headings", height=15, selectmode="browse"
        )

        # 设置表头和列宽
        col_widths = {
            "序号": 50, "审批编号": 140, "采购明细序号": 100,
            "名称": 200, "规格": 100, "单位": 60, "数量": 70, "操作": 120,
        }
        col_anchors = {
            "序号": "center", "名称": "w", "规格": "w", "操作": "center",
        }
        for col in columns:
            self.tree.heading(col, text=col)
            anchor = col_anchors.get(col, "center")
            self.tree.column(col, width=col_widths.get(col, 80), minwidth=40,
                stretch=True, anchor=anchor)

        # 滚动条
        vsb = ttk.Scrollbar(tree_wrap, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_wrap, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")

        # 标签样式
        self.tree.tag_configure("odd", background="#F8FAFC")
        self.tree.tag_configure("even", background="#FFFFFF")
        self.tree.tag_configure("hover", background="#FFF2E6")
        self.tree.tag_configure("archived", foreground="#9CA3AF")

        self.tree.bind("<Motion>", self._on_hover)
        self.tree.bind("<Leave>", self._on_leave)
        self.tree.bind("<Double-1>", self._on_row_double_click)
        self.tree.bind("<Button-1>", self._on_row_click)

        # 右键菜单
        self._context_menu = tk.Menu(self, tearoff=0,
            bg="#FFFFFF", fg="#4A3728",
            activebackground="#E8D5C4", activeforeground="#4A3728",
            font=("Microsoft YaHei", 10),
        )
        self._context_menu.add_command(label="📝 编辑", command=self._on_edit_selected)
        self._context_menu.add_command(label="📁 归档/取消归档", command=self._on_archive_selected)
        self._context_menu.add_separator()
        self._context_menu.add_command(label="🗑️ 删除", command=self._on_delete_selected)
        self.tree.bind("<Button-3>", self._on_tree_right_click)

    # ── 悬浮高亮（与下单页一致）────
    def _on_hover(self, event):
        item = self.tree.identify_row(event.y)
        self._clear_hover()
        if item:
            tags = list(self.tree.item(item, "tags"))
            if "hover" not in tags:
                tags.append("hover")
                self.tree.item(item, tags=tags)
            self._hover_item = item

    def _on_leave(self, event):
        self._clear_hover()

    def _clear_hover(self):
        if hasattr(self, '_hover_item') and self._hover_item:
            try:
                tags = list(self.tree.item(self._hover_item, "tags"))
                if "hover" in tags:
                    tags.remove("hover")
                    self.tree.item(self._hover_item, tags=tags)
            except Exception:
                pass
            self._hover_item = None

    # ── 右键菜单 ───────────────────
    def _on_tree_right_click(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self._context_menu.post(event.x_root, event.y_root)

    def _on_edit_selected(self):
        sel = self.tree.selection()
        if sel:
            rid = int(sel[0])
            self._edit_record(rid)

    def _on_archive_selected(self):
        sel = self.tree.selection()
        if sel:
            rid = int(sel[0])
            rec = self._get_record_by_id(rid)
            if rec:
                if rec.get("archived", 0):
                    self._unarchive_one(rid)
                else:
                    self._archive_one(rid)

    def _on_delete_selected(self):
        sel = self.tree.selection()
        if sel:
            rid = int(sel[0])
            if messagebox.askyesno("确认删除", "确定要删除该条记录吗？"):
                self.db.delete_plan_record(rid)
                self._load_data()

    def _get_record_by_id(self, rid):
        for r in self._records:
            if r["id"] == rid:
                return r
        return None

    # ── 数据加载 ───────────────────────────────────────
    def _load_data(self):
        """从数据库加载计划记录"""
        try:
            archived_val = 1 if self._show_archived else 0
            self._records = self.db.get_plan_records(archived=archived_val)
        except Exception:
            self._records = []
        self._render_table()
        status_text = "已归档" if self._show_archived else "条计划"
        self.stats_label.configure(text=f"共 {len(self._records)} {status_text}")

    def _toggle_archived(self):
        """切换显示已归档/未归档"""
        self._show_archived = not self._show_archived
        if self._show_archived:
            self._archived_btn.configure(text="📋 返回", fg_color=self.C["primary"], text_color="#000000")
        else:
            self._archived_btn.configure(text="📁 已归档", fg_color="transparent", text_color="#000000")
        self._load_data()

    def _render_table(self):
        """渲染计划列表（与下单页一致的Treeview方式）"""
        # 清空现有行
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not self._records:
            return

        for i, rec in enumerate(self._records):
            rid = rec["id"]
            seq = str(i + 1)
            approval_no = rec.get("approval_no", "") or ""
            item_seq = rec.get("item_seq", "") or ""
            material_name = rec.get("material_name", "") or ""
            spec = rec.get("spec", "") or ""
            unit = rec.get("unit", "") or ""
            qty = rec.get("quantity", 0) or 0
            is_archived = rec.get("archived", 0)

            # 操作列文本
            action_text = "取消归档  删除" if is_archived else "编辑  归档  删除"

            values = (seq, approval_no, item_seq,
                      material_name, spec, unit, str(qty), action_text)

            # tag: 奇偶行 + 归档状态
            tags = ("odd",) if i % 2 == 0 else ("even",)
            if is_archived:
                tags = tags + ("archived",)

            self.tree.insert("", "end", iid=str(rid), values=values, tags=tags)

    # ── 行点击事件（与下单页一致的三区域逻辑）────
    def _on_row_click(self, event):
        """单击行事件：操作列按区域分发"""
        col = self.tree.identify_column(event.x)
        item = self.tree.identify_row(event.y)
        if not item:
            return

        col_idx = int(col.replace("#", "")) - 1
        # 操作列是第8列（索引7）
        if col_idx != 7:
            return

        rid = int(item)
        rec = self._get_record_by_id(rid)
        if not rec:
            return

        bbox = self.tree.bbox(item, column="#8")
        if not bbox:
            return
        rel_x = event.x - bbox[0]
        col_width = bbox[2]

        is_archived = rec.get("archived", 0)
        if is_archived:
            # 归档模式：左半=取消归档，右半=删除
            if rel_x < col_width * 0.5:
                self._unarchive_one(rid)
            else:
                if messagebox.askyesno("确认删除", "确定要删除该条记录吗？"):
                    self.db.delete_plan_record(rid)
                    self._load_data()
        else:
            # 非归档模式：左1/3=编辑，中1/3=归档，右1/3=删除
            if rel_x < col_width * 0.33:
                self._edit_record(rid)
            elif rel_x < col_width * 0.66:
                self._archive_one(rid)
            else:
                if messagebox.askyesno("确认删除", "确定要删除该条记录吗？"):
                    self.db.delete_plan_record(rid)
                    self._load_data()

    def _on_row_double_click(self, event):
        """双击编辑"""
        item = self.tree.identify_row(event.y)
        if item:
            rid = int(item)
            self._edit_record(rid)

    def _archive_one(self, rid):
        """归档单条记录"""
        self.db.archive_plan_record(rid)
        self._load_data()

    def _unarchive_one(self, rid):
        """取消归档单条记录"""
        try:
            cur = self.db.conn.cursor()
            cur.execute("UPDATE plan_records SET archived=0 WHERE id=?", (rid,))
            self.db.conn.commit()
        except Exception:
            pass
        self._load_data()

    # ── 手动添加物料 ───────────────────────────────────
    def _open_add_dialog(self):
        """打开手动添加物料对话框"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("添加计划物料")
        dialog.geometry("520x540")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.configure(fg_color=self.C["card"])

        dialog.update_idletasks()
        dw, dh = 520, 540
        sw = dialog.winfo_screenwidth()
        sh = dialog.winfo_screenheight()
        dialog.geometry(f"{dw}x{dh}+{(sw-dw)//2}+{(sh-dh)//2}")

        C = self.C

        ctk.CTkLabel(
            dialog, text="添加计划物料",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=C["text"],
        ).pack(pady=(16, 12))

        form = ctk.CTkFrame(dialog, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        fields = [
            ("审批编号", "approval_no", 280),
            ("采购明细序号", "item_seq", 140),
            ("名称 *", "material_name", 280),
            ("规格", "spec", 280),
            ("数量 *", "quantity", 140),
            ("单位", "unit", 140),
            ("单价(元)", "unit_price", 140),
            ("期望交付日期", "expected_delivery", 140),
            ("备注", "remark", 280),
        ]

        entries = {}
        for label_text, key, w in fields:
            row = ctk.CTkFrame(form, fg_color="transparent")
            row.pack(fill="x", pady=4)

            ctk.CTkLabel(
                row, text=label_text, width=110,
                font=ctk.CTkFont(size=12),
                text_color=C["text_secondary"], anchor="e",
            ).pack(side="left", padx=(0, 8))

            entry = ctk.CTkEntry(
                row, width=w, height=32,
                font=ctk.CTkFont(size=12),
                border_width=1, border_color=C["border"],
                placeholder_text=f"请输入{label_text.replace(' *', '')}",
            )
            entry.pack(side="left")
            entries[key] = entry

        # 金额自动计算提示
        amt_row = ctk.CTkFrame(form, fg_color="transparent")
        amt_row.pack(fill="x", pady=4)
        ctk.CTkLabel(
            amt_row, text="金额", width=110,
            font=ctk.CTkFont(size=12),
            text_color=C["text_secondary"], anchor="e",
        ).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(
            amt_row, text="自动计算（数量×单价）",
            font=ctk.CTkFont(size=11),
            text_color=C["text_secondary"], anchor="w",
        ).pack(side="left")

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=(0, 16))

        def do_save():
            name = entries["material_name"].get().strip()
            if not name:
                messagebox.showwarning("提示", "名称不能为空", parent=dialog)
                return
            qty_str = entries["quantity"].get().strip()
            if not qty_str:
                messagebox.showwarning("提示", "数量不能为空", parent=dialog)
                return
            try:
                qty = float(qty_str)
            except ValueError:
                messagebox.showwarning("提示", "数量必须是数字", parent=dialog)
                return

            price_str = entries["unit_price"].get().strip()
            price = 0
            if price_str:
                try:
                    price = float(price_str)
                except ValueError:
                    messagebox.showwarning("提示", "单价必须是数字", parent=dialog)
                    return

            amount = qty * price

            # 提交时间/通过时间使用当前时间
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

            data = {
                "approval_no": entries["approval_no"].get().strip(),
                "item_seq": entries["item_seq"].get().strip(),
                "material_name": name,
                "spec": entries["spec"].get().strip(),
                "quantity": qty,
                "unit": entries["unit"].get().strip(),
                "unit_price": price,
                "amount": amount,
                "expected_delivery": entries["expected_delivery"].get().strip(),
                "remark": entries["remark"].get().strip(),
                "submitted_at": now_str,
                "approved_at": now_str,
            }
            self.db.save_plan_record(data)
            dialog.destroy()
            self._load_data()

        ctk.CTkButton(
            btn_row, text="保存", width=100, height=34,
            fg_color=C["primary"], hover_color=C["primary_hover"],
            font=ctk.CTkFont(size=13, weight="bold"),
            command=do_save, corner_radius=8,
            text_color="#000000",
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            btn_row, text="取消", width=100, height=34,
            fg_color="transparent", hover_color=C["sidebar_hover"],
            font=ctk.CTkFont(size=13),
            command=dialog.destroy, corner_radius=8,
            border_width=1, border_color=C["border"],
            text_color="#000000",
        ).pack(side="right")

    # ── 编辑记录 ───────────────────────────────────────
    def _edit_record(self, record_id):
        """编辑已有计划记录"""
        rec = self._get_record_by_id(record_id)
        if not rec:
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("编辑计划物料")
        dialog.geometry("520x540")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.configure(fg_color=self.C["card"])

        dialog.update_idletasks()
        dw, dh = 520, 540
        sw = dialog.winfo_screenwidth()
        sh = dialog.winfo_screenheight()
        dialog.geometry(f"{dw}x{dh}+{(sw-dw)//2}+{(sh-dh)//2}")

        C = self.C

        ctk.CTkLabel(
            dialog, text="编辑计划物料",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=C["text"],
        ).pack(pady=(16, 12))

        form = ctk.CTkFrame(dialog, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        fields = [
            ("审批编号", "approval_no", 280),
            ("采购明细序号", "item_seq", 140),
            ("名称 *", "material_name", 280),
            ("规格", "spec", 280),
            ("数量 *", "quantity", 140),
            ("单位", "unit", 140),
            ("单价(元)", "unit_price", 140),
            ("期望交付日期", "expected_delivery", 140),
            ("备注", "remark", 280),
        ]

        entries = {}
        for label_text, key, w in fields:
            row = ctk.CTkFrame(form, fg_color="transparent")
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(
                row, text=label_text, width=110,
                font=ctk.CTkFont(size=12),
                text_color=C["text_secondary"], anchor="e",
            ).pack(side="left", padx=(0, 8))
            val = rec.get(key, "")
            if isinstance(val, (int, float)) and val == 0:
                val = ""
            entry = ctk.CTkEntry(
                row, width=w, height=32,
                font=ctk.CTkFont(size=12),
                border_width=1, border_color=C["border"],
            )
            entry.insert(0, str(val))
            entry.pack(side="left")
            entries[key] = entry

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=(0, 16))

        def do_save():
            name = entries["material_name"].get().strip()
            if not name:
                messagebox.showwarning("提示", "名称不能为空", parent=dialog)
                return
            qty_str = entries["quantity"].get().strip()
            if not qty_str:
                messagebox.showwarning("提示", "数量不能为空", parent=dialog)
                return
            try:
                qty = float(qty_str)
            except ValueError:
                messagebox.showwarning("提示", "数量必须是数字", parent=dialog)
                return
            price_str = entries["unit_price"].get().strip()
            price = 0
            if price_str:
                try:
                    price = float(price_str)
                except ValueError:
                    messagebox.showwarning("提示", "单价必须是数字", parent=dialog)
                    return
            amount = qty * price

            data = {
                "approval_no": entries["approval_no"].get().strip(),
                "item_seq": entries["item_seq"].get().strip(),
                "material_name": name,
                "spec": entries["spec"].get().strip(),
                "quantity": qty,
                "unit": entries["unit"].get().strip(),
                "unit_price": price,
                "amount": amount,
                "expected_delivery": entries["expected_delivery"].get().strip(),
                "remark": entries["remark"].get().strip(),
                "submitted_at": rec.get("submitted_at", ""),
                "approved_at": rec.get("approved_at", ""),
            }
            self.db.update_plan_record(record_id, data)
            dialog.destroy()
            self._load_data()

        ctk.CTkButton(
            btn_row, text="保存", width=100, height=34,
            fg_color=C["primary"], hover_color=C["primary_hover"],
            font=ctk.CTkFont(size=13, weight="bold"),
            command=do_save, corner_radius=8,
            text_color="#000000",
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            btn_row, text="取消", width=100, height=34,
            fg_color="transparent", hover_color=C["sidebar_hover"],
            font=ctk.CTkFont(size=13),
            command=dialog.destroy, corner_radius=8,
            border_width=1, border_color=C["border"],
            text_color="#000000",
        ).pack(side="right")

    # ── 导入文件（PDF / Excel / CSV）─────────────────────
    def _import_file(self):
        """导入计划文件：支持 PDF、Excel(.xlsx/.xls)、CSV"""
        filepath = filedialog.askopenfilename(
            title="选择计划文件",
            filetypes=[
                ("所有支持的文件", "*.pdf;*.xlsx;*.xls;*.csv"),
                ("PDF文件", "*.pdf"),
                ("Excel文件", "*.xlsx;*.xls"),
                ("CSV文件", "*.csv"),
            ],
        )
        if not filepath:
            return

        ext = os.path.splitext(filepath)[1].lower()

        try:
            if ext == ".pdf":
                extracted = self._parse_plan_pdf(filepath)
                title_prefix = "PDF"
            elif ext in (".xlsx", ".xls"):
                extracted = self._parse_plan_excel(filepath)
                title_prefix = "Excel"
            elif ext == ".csv":
                extracted = self._parse_plan_csv(filepath)
                title_prefix = "CSV"
            else:
                messagebox.showerror("不支持", f"不支持的文件格式：{ext}")
                return
        except Exception as e:
            messagebox.showerror("导入失败", f"文件解析失败：\n{e}")
            return

        if not extracted:
            messagebox.showinfo("提示", "未从文件中提取到物料信息，请检查文件格式。")
            return

        self._show_import_preview(filepath, extracted, title_prefix)

    def _parse_plan_excel(self, filepath):
        """解析Excel表格，按表头匹配字段提取物料信息"""
        items = []
        try:
            import openpyxl
            wb = openpyxl.load_workbook(filepath, data_only=True)
            ws = wb.active

            rows_data = []
            for row in ws.iter_rows(values_only=True):
                rows_data.append([str(c).strip() if c is not None else "" for c in row])

            items = self._parse_table_rows(rows_data)
            wb.close()
        except ImportError:
            raise Exception("缺少openpyxl库，请执行: pip install openpyxl")
        except Exception as e:
            # 尝试用 xlrd 读取旧版 .xls
            if str(e).startswith("缺少"):
                raise
            try:
                import xlrd
                wb = xlrd.open_workbook(filepath)
                ws = wb.sheet_by_index(0)
                rows_data = []
                for r in range(ws.nrows):
                    rows_data.append([str(ws.cell_value(r, c)).strip() if ws.cell_value(r, c) else "" for c in range(ws.ncols)])
                items = self._parse_table_rows(rows_data)
            except ImportError:
                raise Exception("缺少xlrd库，请执行: pip install xlrd")
            except Exception:
                raise e

        return items

    def _parse_plan_csv(self, filepath):
        """解析CSV表格，按表头匹配字段提取物料信息"""
        import csv
        rows_data = []
        # 尝试多种编码
        for encoding in ("utf-8-sig", "utf-8", "gbk", "gb2312"):
            try:
                with open(filepath, "r", encoding=encoding) as f:
                    reader = csv.reader(f)
                    rows_data = [row for row in reader]
                break
            except (UnicodeDecodeError, Exception):
                continue

        if not rows_data:
            raise Exception("无法解析CSV文件，请检查文件编码（支持 UTF-8 / GBK）")

        return self._parse_table_rows(rows_data)

    def _parse_table_rows(self, rows_data):
        """通用表格行解析：按表头匹配字段，提取物料信息（PDF表格/Excel/CSV共用）"""
        items = []
        if not rows_data:
            return items

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        approval_no = ""
        expected_delivery = ""
        reason = ""

        # 先扫描全文提取审批编号和期望交付日期
        full_text = "\n".join([" ".join(r) for r in rows_data])
        m_no = re.search(r'审批编号[：:\s]*(\S+)', full_text)
        if m_no:
            approval_no = m_no.group(1)
        m_deliv = re.search(r'期望交付日期[：:\s]*(\d{4}[-/]\d{1,2}[-/]\d{1,2})', full_text)
        if m_deliv:
            expected_delivery = m_deliv.group(1).replace('/', '-')
        m_reason = re.search(r'申请事由[：:\s]*([^\n]+)', full_text)
        if m_reason:
            reason = m_reason.group(1).strip()

        # ── 表头匹配 ──
        header_row_idx = -1
        col_map = {}

        for ri, row in enumerate(rows_data):
            if not row or all(not c for c in row):
                continue
            header_texts = [c.replace('\n', ' ').replace(' ', '') for c in row]

            has_material = any(
                kw in h for h in header_texts
                for kw in ["物料名称", "名称", "品名", "物料", "产品名称", "货品名称"]
            )
            has_qty = any(
                kw in h for h in header_texts
                for kw in ["数量", "采购数量", "计划数量"]
            )

            if has_material and has_qty:
                header_row_idx = ri
                for ci, h in enumerate(header_texts):
                    # 采购明细序号
                    if any(kw in h for kw in ["序号", "项次", "明细序号"]):
                        col_map["item_seq"] = ci
                    # 审批编号
                    if "审批编号" in h:
                        col_map["approval_no"] = ci
                    # 物料名称
                    if any(kw in h for kw in ["物料名称", "名称", "品名", "物料", "产品名称", "货品名称"]):
                        col_map["material_name"] = ci
                    # 规格
                    elif any(kw in h for kw in ["规格", "型号"]):
                        col_map["spec"] = ci
                    # 数量
                    elif any(kw in h for kw in ["数量", "采购数量", "计划数量"]):
                        col_map["quantity"] = ci
                    # 单位
                    elif "单位" in h:
                        col_map["unit"] = ci
                    # 单价
                    elif any(kw in h for kw in ["单价", "价格", "含税单价"]):
                        col_map["unit_price"] = ci
                    # 金额
                    elif any(kw in h for kw in ["金额", "总价", "合计金额", "小计"]):
                        col_map["amount"] = ci
                    # 期望交付日期
                    elif any(kw in h for kw in ["期望交付", "交付日期", "交货日期", "到货日期"]):
                        col_map["expected_delivery"] = ci
                    # 备注
                    elif "备注" in h or "说明" in h:
                        col_map["remark"] = ci
                break

            # 放宽条件：有物料+规格/数量的组合
            if header_row_idx < 0 and has_material and any(
                kw in h for h in header_texts
                for kw in ["规格", "型号", "数量", "采购数量", "计划数量"]
            ):
                header_row_idx = ri
                for ci, h in enumerate(header_texts):
                    if any(kw in h for kw in ["序号", "项次", "明细序号"]):
                        col_map["item_seq"] = ci
                    if "审批编号" in h:
                        col_map["approval_no"] = ci
                    if any(kw in h for kw in ["物料名称", "名称", "品名", "物料", "产品名称", "货品名称"]):
                        col_map["material_name"] = ci
                    elif any(kw in h for kw in ["规格", "型号"]):
                        col_map["spec"] = ci
                    elif any(kw in h for kw in ["数量", "采购数量", "计划数量"]):
                        col_map["quantity"] = ci
                    elif "单位" in h:
                        col_map["unit"] = ci
                    elif any(kw in h for kw in ["单价", "价格", "含税单价"]):
                        col_map["unit_price"] = ci
                    elif any(kw in h for kw in ["金额", "总价", "合计金额", "小计"]):
                        col_map["amount"] = ci
                    elif any(kw in h for kw in ["期望交付", "交付日期", "交货日期", "到货日期"]):
                        col_map["expected_delivery"] = ci
                    elif "备注" in h or "说明" in h:
                        col_map["remark"] = ci

        if header_row_idx < 0 or not col_map:
            return items

        # ── 遍历数据行 ──
        for ri in range(header_row_idx + 1, len(rows_data)):
            row = rows_data[ri]
            if not row or all(not c for c in row):
                continue
            first_cell = row[0].strip() if row[0] else ""
            if "合计" in first_cell or "总计" in first_cell or "小计" in first_cell:
                continue
            # 跳过可能的二级表头
            if any("物料名称" in c or "名称" == c.strip() for c in row):
                continue

            def _get_val(ci):
                if ci is not None and ci < len(row) and row[ci]:
                    return str(row[ci]).strip().replace(',', '').replace('，', '')
                return ""

            name = _get_val(col_map.get("material_name"))
            if not name:
                continue

            item_seq = _get_val(col_map.get("item_seq"))
            spec = _get_val(col_map.get("spec"))
            qty_str = _get_val(col_map.get("quantity"))
            unit = _get_val(col_map.get("unit"))
            price_str = _get_val(col_map.get("unit_price"))
            amt_str = _get_val(col_map.get("amount"))
            row_expected = _get_val(col_map.get("expected_delivery"))
            row_remark = _get_val(col_map.get("remark"))

            try:
                qty = float(qty_str) if qty_str else 0
            except ValueError:
                qty = 0
            try:
                price = float(price_str) if price_str else 0
            except ValueError:
                price = 0
            try:
                amount = float(amt_str) if amt_str else qty * price
            except ValueError:
                amount = qty * price

            final_remark = f"审批编号:{approval_no} 事由:{reason}" if approval_no else reason
            if row_remark:
                final_remark = row_remark + " | " + final_remark if final_remark else row_remark

            items.append({
                "approval_no": approval_no,
                "item_seq": item_seq,
                "material_name": name,
                "spec": spec,
                "quantity": qty,
                "unit": unit,
                "unit_price": price,
                "amount": amount,
                "expected_delivery": expected_delivery or row_expected,
                "remark": final_remark,
                "submitted_at": now_str,
                "approved_at": now_str,
            })

        return items

    def _parse_plan_pdf(self, filepath):
        """解析PDF计划单，优先用表格解析，回退到文本解析"""
        items = []
        try:
            import pdfplumber
            with pdfplumber.open(filepath) as pdf:
                full_text = ""
                all_table_rows = []
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        full_text += t + "\n"
                    tables = page.extract_tables()
                    for tbl in tables:
                        if tbl:
                            # 转为二维字符串列表
                            for row in tbl:
                                all_table_rows.append([str(c).strip() if c else "" for c in row])

            if not full_text.strip() and not all_table_rows:
                return items

            # ── 优先用通用表格解析 ──
            if all_table_rows:
                items = self._parse_table_rows(all_table_rows)

            # ── 回退到文本解析 ──
            if not items and full_text.strip():
                approval_no = ""
                expected_delivery = ""
                reason = ""
                m_no = re.search(r'审批编号[：:\s]*(\S+)', full_text)
                if m_no:
                    approval_no = m_no.group(1)
                m_deliv = re.search(r'期望交付日期[：:\s]*(\d{4}[-/]\d{1,2}[-/]\d{1,2})', full_text)
                if m_deliv:
                    expected_delivery = m_deliv.group(1).replace('/', '-')
                m_reason = re.search(r'申请事由[：:\s]*([^\n]+)', full_text)
                if m_reason:
                    reason = m_reason.group(1).strip()

                now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                lines = full_text.split('\n')
                for line in lines:
                    line = line.strip()
                    m = re.search(
                        r'采购明细(\d+)\s+(.+?)\s+([\d,.]+)\s*(\S+)\s+([\d,.]+)',
                        line
                    )
                    if m:
                        item_seq = m.group(1)
                        rest = m.group(2).strip()
                        qty_str = m.group(3).replace(',', '')
                        unit = m.group(4).strip()
                        price_str = m.group(5).replace(',', '')

                        name = rest
                        spec = ""
                        spec_match = re.search(r'(.+?)(\d+克|\d+g|\d+G).*', rest)
                        if spec_match:
                            name = spec_match.group(1).strip()
                            spec = spec_match.group(0)[len(name):].strip()

                        try:
                            qty = float(qty_str)
                        except ValueError:
                            qty = 0
                        try:
                            price = float(price_str)
                        except ValueError:
                            price = 0
                        amount = qty * price

                        items.append({
                            "approval_no": approval_no,
                            "item_seq": item_seq,
                            "material_name": name,
                            "spec": spec,
                            "quantity": qty,
                            "unit": unit,
                            "unit_price": price,
                            "amount": amount,
                            "expected_delivery": expected_delivery,
                            "remark": f"审批编号:{approval_no} 事由:{reason}" if approval_no else reason,
                            "submitted_at": now_str,
                            "approved_at": now_str,
                        })

        except ImportError:
            raise Exception("缺少pdfplumber库，请执行: pip install pdfplumber")
        except Exception as e:
            raise e

        return items

    def _show_import_preview(self, filepath, items, file_type="文件"):
        """预览导入结果并确认导入，每行后有删除按钮"""
        preview = ctk.CTkToplevel(self)
        preview.title(f"{file_type}导入预览")
        preview.geometry("960x600")
        preview.resizable(True, True)
        preview.minsize(780, 450)
        preview.transient(self)
        preview.grab_set()
        preview.configure(fg_color=self.C["card"])

        preview.update_idletasks()
        sw = preview.winfo_screenwidth()
        sh = preview.winfo_screenheight()
        preview.geometry(f"960x600+{(sw-960)//2}+{(sh-600)//2}")

        C = self.C

        # 顶部信息栏
        header = ctk.CTkFrame(preview, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 8))

        ctk.CTkLabel(
            header, text=f"{file_type}计划单导入预览",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=C["text"],
        ).pack(side="left")

        file_label = ctk.CTkLabel(
            header, text=os.path.basename(filepath)[:40],
            font=ctk.CTkFont(size=11),
            text_color=C["text_secondary"],
        )
        file_label.pack(side="left", padx=(12, 0))

        # 提示信息
        if items and items[0].get("remark"):
            info_frame = ctk.CTkFrame(preview, fg_color=C["primary_light"], corner_radius=8)
            info_frame.pack(fill="x", padx=20, pady=(0, 4))
            ctk.CTkLabel(
                info_frame, text=f"📋 {items[0].get('remark', '')}",
                font=ctk.CTkFont(size=11),
                text_color=C["text"],
            ).pack(padx=12, pady=6, anchor="w")

        # 使用可变列表管理条目
        import copy
        working_items = copy.deepcopy(items)

        # ═══ 使用 Frame 包裹每行的内容 + 删除按钮 ═══
        list_outer = tk.Frame(preview, bg=C["card"])
        list_outer.pack(fill="both", expand=True, padx=20, pady=(4, 8))

        # 滚动区域的canvas
        canvas = tk.Canvas(list_outer, bg="#FFFFFF", highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_outer, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#FFFFFF")

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw", tags="scroll_frame")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 鼠标滚轮支持
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_wheel(e):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_wheel(e):
            canvas.unbind_all("<MouseWheel>")

        canvas.bind("<Enter>", _bind_wheel)
        canvas.bind("<Leave>", _unbind_wheel)

        # 存储每行的frame引用
        row_frames = []

        def _refresh_list():
            for rf in row_frames:
                rf.destroy()
            row_frames.clear()

            if not working_items:
                empty_label = tk.Label(scroll_frame, text="暂无条目", bg="#FFFFFF",
                    fg=C["text_secondary"], font=("Microsoft YaHei", 12))
                empty_label.pack(pady=20)
                row_frames.append(empty_label)
                count_label.configure(text="共 0 条物料")
                return

            # 表头
            hdr_frame = tk.Frame(scroll_frame, bg="#F8FAFC")
            hdr_frame.pack(fill="x", pady=(0, 2))
            row_frames.append(hdr_frame)

            hdr_labels = [
                ("序号", 50), ("审批编号", 130), ("采购明细序号", 90),
                ("名称", 180), ("规格", 90), ("单位", 55),
                ("数量", 65), ("操作", 70),
            ]
            for htext, hw in hdr_labels:
                lbl = tk.Label(hdr_frame, text=htext, width=hw // 8 if hw > 50 else 7,
                    bg="#F8FAFC", fg="#475569",
                    font=("Microsoft YaHei", 9, "bold"), anchor="center")
                lbl.pack(side="left", padx=(1, 1))

            # 数据行
            for i, item in enumerate(working_items):
                bg_color = "#F8FAFC" if i % 2 == 0 else "#FFFFFF"
                row_frame = tk.Frame(scroll_frame, bg=bg_color)
                row_frame.pack(fill="x", pady=0)
                row_frames.append(row_frame)

                # 序号
                tk.Label(row_frame, text=str(i + 1), width=5, bg=bg_color,
                    fg="#1E293B", font=("Microsoft YaHei", 9), anchor="center"
                ).pack(side="left", padx=(0, 2))

                # 审批编号
                tk.Label(row_frame, text=str(item.get("approval_no", ""))[:16], width=14,
                    bg=bg_color, fg="#1E293B", font=("Microsoft YaHei", 9), anchor="w"
                ).pack(side="left", padx=(0, 2))

                # 采购明细序号
                tk.Label(row_frame, text=str(item.get("item_seq", "")), width=9,
                    bg=bg_color, fg="#1E293B", font=("Microsoft YaHei", 9), anchor="center"
                ).pack(side="left", padx=(0, 2))

                # 名称
                tk.Label(row_frame, text=str(item.get("material_name", ""))[:22], width=20,
                    bg=bg_color, fg="#1E293B", font=("Microsoft YaHei", 9), anchor="w"
                ).pack(side="left", padx=(0, 2))

                # 规格
                tk.Label(row_frame, text=str(item.get("spec", ""))[:10], width=9,
                    bg=bg_color, fg="#475569", font=("Microsoft YaHei", 9), anchor="w"
                ).pack(side="left", padx=(0, 2))

                # 单位
                tk.Label(row_frame, text=str(item.get("unit", "")), width=6,
                    bg=bg_color, fg="#475569", font=("Microsoft YaHei", 9), anchor="center"
                ).pack(side="left", padx=(0, 2))

                # 数量
                tk.Label(row_frame, text=str(item.get("quantity", 0)), width=7,
                    bg=bg_color, fg="#1E293B", font=("Microsoft YaHei", 9), anchor="center"
                ).pack(side="left", padx=(0, 2))

                # 删除按钮（每行独立）
                idx = i
                del_btn = ctk.CTkButton(
                    row_frame, text="✕ 删除", width=60, height=24,
                    fg_color="transparent", hover_color="#FFCCCC",
                    font=ctk.CTkFont(size=10),
                    command=lambda idx=idx: _delete_single(idx),
                    corner_radius=4,
                    border_width=1, border_color="#E0D0C0",
                    text_color="#B56A6A",
                )
                del_btn.pack(side="left", padx=(4, 0))

            count_label.configure(text=f"共 {len(working_items)} 条物料")
            # 更新canvas滚动区域
            scroll_frame.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _delete_single(idx):
            """删除单条"""
            if 0 <= idx < len(working_items):
                del working_items[idx]
                _refresh_list()

        # 底部操作栏
        bottom_bar = ctk.CTkFrame(preview, fg_color="transparent")
        bottom_bar.pack(fill="x", padx=20, pady=(0, 16))

        count_label = ctk.CTkLabel(
            bottom_bar, text=f"共 {len(working_items)} 条物料",
            font=ctk.CTkFont(size=12),
            text_color=C["text_secondary"],
        )
        count_label.pack(side="left")

        def do_import():
            if not working_items:
                messagebox.showinfo("提示", "没有可导入的条目", parent=preview)
                return
            for item in working_items:
                self.db.save_plan_record({
                    "approval_no": item.get("approval_no", ""),
                    "item_seq": item.get("item_seq", ""),
                    "material_name": item.get("material_name", ""),
                    "spec": item.get("spec", ""),
                    "quantity": item.get("quantity", 0),
                    "unit": item.get("unit", ""),
                    "unit_price": item.get("unit_price", 0),
                    "amount": item.get("amount", 0),
                    "expected_delivery": item.get("expected_delivery", ""),
                    "remark": item.get("remark", ""),
                    "submitted_at": item.get("submitted_at", ""),
                    "approved_at": item.get("approved_at", ""),
                })
            preview.destroy()
            self._load_data()
            messagebox.showinfo("导入成功", f"已成功导入 {len(working_items)} 条计划物料")

        ctk.CTkButton(
            bottom_bar, text="确认导入", width=110, height=34,
            fg_color=C["primary"], hover_color=C["primary_hover"],
            font=ctk.CTkFont(size=13, weight="bold"),
            command=do_import, corner_radius=8,
            text_color="#000000",
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            bottom_bar, text="取消", width=90, height=34,
            fg_color="transparent", hover_color=C["sidebar_hover"],
            font=ctk.CTkFont(size=13),
            command=preview.destroy, corner_radius=8,
            border_width=1, border_color=C["border"],
            text_color="#000000",
        ).pack(side="right")

        _refresh_list()

    # ── 删除选中 ───────────────────────────────────────
    def _delete_selected(self):
        """删除选中的记录"""
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("提示", "请先点击要删除的记录行")
            return

        if not messagebox.askyesno("确认删除", f"确定要删除选中的 {len(sel)} 条记录吗？"):
            return

        for iid in sel:
            self.db.delete_plan_record(int(iid))
        self._load_data()

    # ── 导出Excel ───────────────────────────────────────
    def _export_xlsx(self):
        """导出计划列表为Excel"""
        if not self._records:
            messagebox.showinfo("提示", "暂无数据可导出")
            return

        filepath = filedialog.asksaveasfilename(
            title="导出计划单",
            defaultextension=".xlsx",
            filetypes=[("Excel文件", "*.xlsx")],
            initialfile=f"采购计划_{datetime.now().strftime('%Y%m%d')}.xlsx",
        )
        if not filepath:
            return

        headers = ["序号", "审批编号", "采购明细序号", "名称", "规格", "数量", "单位", "单价", "金额", "期望交付日期", "备注", "提交时间", "通过时间"]
        rows = []
        for i, rec in enumerate(self._records):
            rows.append({
                "序号": i + 1,
                "审批编号": rec.get("approval_no", ""),
                "采购明细序号": rec.get("item_seq", ""),
                "名称": rec.get("material_name", ""),
                "规格": rec.get("spec", ""),
                "数量": rec.get("quantity", 0),
                "单位": rec.get("unit", ""),
                "单价": rec.get("unit_price", 0),
                "金额": rec.get("amount", 0),
                "期望交付日期": rec.get("expected_delivery", ""),
                "备注": rec.get("remark", ""),
                "提交时间": rec.get("submitted_at", ""),
                "通过时间": rec.get("approved_at", ""),
            })

        try:
            self.db.export_to_xlsx(filepath, "采购计划", headers, rows)
            messagebox.showinfo("导出成功", f"已导出到：\n{filepath}")
        except Exception as e:
            messagebox.showerror("导出失败", str(e))
