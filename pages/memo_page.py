#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""备忘录页面 - v1.3"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from datetime import datetime

MEMO_STATUS = ["待处理", "处理中", "已完成"]

TABLE_COLS = [
    ("date",      "日期",      95,  "center"),
    ("project",   "项目归属",  100, "center"),
    ("handler",   "经手人",    80,  "center"),
    ("content",   "具体内容",  240, "w"),
    ("deadline",  "时间节点",  95,  "center"),
    ("status",    "状态",      80,  "center"),
    ("remark",    "备注",      160, "w"),
]


class MemoPage(ctk.CTkFrame):
    def __init__(self, parent, db, colors):
        super().__init__(parent, fg_color=colors["bg"], corner_radius=0)
        self.db = db
        self.C = colors
        self._build()
        self._do_search()

    def _build(self):
        # ── 顶部标题栏 ─────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0, height=52)
        header.pack(fill="x", padx=20, pady=(16, 8))
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="备忘录",
            font=ctk.CTkFont(family="Microsoft YaHei", size=16, weight="bold"),
            text_color=self.C["text"],
        ).pack(side="left", pady=14)

        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right", padx=16)

        ctk.CTkButton(
            btn_frame, text="＋ 新增备忘", width=120, height=34,
            fg_color=self.C["danger"], hover_color="#A85A5A",
            font=ctk.CTkFont(family="Microsoft YaHei", size=14, weight="bold"),
            command=self._open_form, corner_radius=20,
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_frame, text="📤 导出Excel", width=110, height=34,
            fg_color=self.C["success"], hover_color="#7A9470",
            font=ctk.CTkFont(family="Microsoft YaHei", size=14, weight="bold"),
            command=self._export_xlsx, corner_radius=20,
        ).pack(side="right", padx=4)

        # ── 搜索栏 ─────────────────────────────────────
        search_frame = ctk.CTkFrame(self, fg_color=self.C["card"], corner_radius=self.C["radius_card"], height=56)
        search_frame.pack(fill="x", padx=16, pady=(12, 0))
        search_frame.pack_propagate(False)

        inner = ctk.CTkFrame(search_frame, fg_color="transparent")
        inner.pack(side="left", fill="y", padx=16)

        # 项目筛选
        ctk.CTkLabel(inner, text="项目：",
                     font=ctk.CTkFont(family="Microsoft YaHei", size=13),
                     text_color=self.C["text_secondary"]).pack(side="left", pady=12)
        self.project_var = tk.StringVar(value="全部")
        self.project_combo = ctk.CTkComboBox(
            inner, values=["全部"], variable=self.project_var,
            width=120, height=32, font=ctk.CTkFont(family="Microsoft YaHei", size=13),
        )
        self.project_combo.pack(side="left", padx=(4, 16), pady=12)
        self._refresh_project_filter()

        # 状态筛选
        ctk.CTkLabel(inner, text="状态：",
                     font=ctk.CTkFont(family="Microsoft YaHei", size=13),
                     text_color=self.C["text_secondary"]).pack(side="left")
        self.status_var = tk.StringVar(value="全部")
        self.status_combo = ctk.CTkComboBox(
            inner, values=["全部"] + MEMO_STATUS, variable=self.status_var,
            width=100, height=32, font=ctk.CTkFont(family="Microsoft YaHei", size=13),
        )
        self.status_combo.pack(side="left", padx=(4, 16))

        # 模糊搜索
        ctk.CTkLabel(inner, text="搜索：",
                     font=ctk.CTkFont(family="Microsoft YaHei", size=13),
                     text_color=self.C["text_secondary"]).pack(side="left")
        self.kw_var = tk.StringVar()
        kw_entry = ctk.CTkEntry(
            inner, textvariable=self.kw_var, width=180, height=32,
            font=ctk.CTkFont(family="Microsoft YaHei", size=13),
            placeholder_text="模糊搜索…",
        )
        kw_entry.pack(side="left", padx=(4, 16))
        kw_entry.bind("<Return>", lambda e: self._do_search())

        ctk.CTkButton(
            inner, text="查询", width=70, height=32,
            fg_color=self.C["primary"], hover_color=self.C["primary_hover"],
            font=ctk.CTkFont(family="Microsoft YaHei", size=13, weight="bold"),
            command=self._do_search, corner_radius=20,
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            inner, text="重置", width=60, height=32,
            fg_color=self.C["border"], text_color=self.C["text"],
            hover_color=self.C["sidebar_hover"],
            font=ctk.CTkFont(family="Microsoft YaHei", size=13),
            command=self._reset, corner_radius=20,
        ).pack(side="left", padx=4)

        # 统计
        self.count_lbl = ctk.CTkLabel(
            search_frame, text="",
            font=ctk.CTkFont(family="Microsoft YaHei", size=13),
            text_color=self.C["text_secondary"],
        )
        self.count_lbl.pack(side="right", padx=20)

        # ── 表格区域 ─────────────────────────────────────
        list_frame = ctk.CTkFrame(self, fg_color=self.C["card"], corner_radius=self.C["radius_card"])
        list_frame.pack(fill="both", expand=True, padx=16, pady=(8, 16))

        style = ttk.Style()
        style.configure("Memo.Treeview",
                         font=("Microsoft YaHei", 9), rowheight=36,
                         background="#FFFFFF", fieldbackground="#FFFFFF",
                         foreground="#4A3728")
        style.configure("Memo.Treeview.Heading",
                         font=("Microsoft YaHei", 9, "bold"),
                         background="#F8FAFC", foreground="#475569", relief="flat")
        style.map("Memo.Treeview",
                  background=[("selected", "#E8D5C4")],
                  foreground=[("selected", "#4A3728")])

        tree_frame = tk.Frame(list_frame, bg="#FFFFFF")
        tree_frame.pack(fill="both", expand=True, padx=8, pady=8)

        col_ids = [c[0] for c in TABLE_COLS] + ["action"]
        self.tree = ttk.Treeview(
            tree_frame, style="Memo.Treeview",
            columns=col_ids, show="headings", selectmode="browse",
        )
        for cid, label, width, anchor in TABLE_COLS:
            self.tree.heading(cid, text=label)
            self.tree.column(cid, width=width, minwidth=40, stretch=True, anchor=anchor)
        self.tree.heading("action", text="操作")
        self.tree.column("action", width=130, minwidth=40, stretch=True, anchor="center")

        vsb = ctk.CTkScrollbar(tree_frame, orientation="vertical", command=self.tree.yview,
                              button_color=self.C["border"], button_hover_color=self.C.get("sidebar_hover", "#ddd"), width=8)
        hsb = ctk.CTkScrollbar(tree_frame, orientation="horizontal", command=self.tree.xview,
                              button_color=self.C["border"], button_hover_color=self.C.get("sidebar_hover", "#ddd"), width=8, height=8)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree.tag_configure("odd", background="#FFFAF5")
        self.tree.tag_configure("even", background="#FFFFFF")
        self.tree.tag_configure("done", foreground="#8FA882")

        # 事件绑定：单击选中高亮行
        self.tree.bind("<Button-1>", self._on_click)
        self.tree.bind("<Double-1>", self._on_double_click)

        # ── 右键菜单 ──
        self._context_menu = tk.Menu(self, tearoff=0,
            bg="#FFFFFF", fg="#4A3728",
            activebackground="#E8D5C4", activeforeground="#4A3728",
            font=("Microsoft YaHei", 10),
        )
        self._context_menu.add_command(label="📝 编辑", command=self._on_edit_selected)
        self._context_menu.add_command(label="📋 复制", command=self._on_copy_selected)
        self._context_menu.add_separator()
        self._context_menu.add_command(label="🗑️ 删除", command=self._on_delete_selected)
        self.tree.bind("<Button-3>", self._on_tree_right_click)

    def _refresh_project_filter(self):
        projects = self.db.get_projects()
        values = ["全部"] + projects
        current = self.project_var.get()
        self.project_combo.configure(values=values)
        if current not in values:
            self.project_var.set("全部")

    def _do_search(self):
        kw = self.kw_var.get().strip()
        proj = self.project_var.get()
        st = self.status_var.get()
        records = self.db.get_memos(
            keyword=kw if kw else None,
            project=proj if proj != "全部" else None,
            status=st if st != "全部" else None,
        )
        self._render(records)
        self.count_lbl.configure(text=f"共 {len(records)} 条")

    def _reset(self):
        self.kw_var.set("")
        self.project_var.set("全部")
        self.status_var.set("全部")
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.count_lbl.configure(text="")

    def _render(self, records):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for i, r in enumerate(records):
            tag = "odd" if i % 2 == 0 else "even"
            status = r.get("status") or "—"
            if status == "已完成":
                tag = (tag, "done")

            self.tree.insert("", "end", iid=str(r["id"]),
                             values=(
                                 r.get("date") or "—",
                                 r.get("project") or "—",
                                 r.get("handler") or "—",
                                 r.get("content") or "—",
                                 r.get("deadline") or "—",
                                 status,
                                 r.get("remark") or "—",
                                 "编辑  完成  删除",
                             ), tags=tag)

    # ── 单击选中高亮行 ──────────────────────────────
    def _on_click(self, event):
        item = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not item:
            return
        # 先选中当前行
        self.tree.selection_set(item)
        col_idx = int(col.replace("#", "")) - 1

        # 操作列处理
        if col_idx == len(TABLE_COLS):  # 操作列
            bbox = self.tree.bbox(item, col)
            if bbox:
                x_rel = event.x - bbox[0]
                col_w = bbox[2]
                mid = int(item)
                if x_rel < col_w * 0.33:
                    self._open_form(mid)
                elif x_rel < col_w * 0.66:
                    self._mark_done(mid)
                else:
                    self._delete(mid)

    def _on_double_click(self, event):
        item = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not item:
            return
        mid = int(item)
        col_idx = int(col.replace("#", "")) - 1
        if col_idx == len(TABLE_COLS):
            return  # 操作列双击不处理，交给单击
        self._open_form(mid)

    # ── 右键菜单回调 ─────────────────────────────────
    def _on_tree_right_click(self, event):
        """右键点击表格行→弹出菜单"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self._context_menu.post(event.x_root, event.y_root)

    def _on_edit_selected(self):
        """编辑选中行"""
        selection = self.tree.selection()
        if not selection:
            return
        mid = int(selection[0])
        self._open_form(mid)

    def _on_copy_selected(self):
        """复制选中行信息到剪贴板"""
        selection = self.tree.selection()
        if not selection:
            return
        mid = int(selection[0])
        rec = self.db.get_memo(mid)
        if rec:
            text = f"内容:{rec.get('content','')} 项目:{rec.get('project','')} 状态:{rec.get('status','')}"
            self.clipboard_clear()
            self.clipboard_append(text)

    def _on_delete_selected(self):
        """删除选中行"""
        selection = self.tree.selection()
        if not selection:
            return
        mid = int(selection[0])
        self._delete(mid)

    def _open_form(self, mid=None):
        try:
            form = MemoForm(self, self.db, self.C, mid=mid, on_save=self._do_search)
            form.grab_set()
        except Exception as e:
            import traceback
            messagebox.showerror("打开表单失败", f"{e}\n\n{traceback.format_exc()}")

    def _mark_done(self, mid):
        rec = self.db.get_memo(mid)
        if not rec:
            return
        if rec.get("status") == "已完成":
            # 撤销完成 → 改为待处理
            data = {
                "date": rec.get("date", ""),
                "project": rec.get("project", ""),
                "handler": rec.get("handler", ""),
                "content": rec.get("content", ""),
                "deadline": rec.get("deadline", ""),
                "status": "待处理",
                "remark": rec.get("remark", ""),
            }
            self.db.update_memo(mid, data)
            self._do_search()
            return
        if not messagebox.askyesno("确认", "将此备忘录标记为已完成？"):
            return
        data = {
            "date": rec.get("date", ""),
            "project": rec.get("project", ""),
            "handler": rec.get("handler", ""),
            "content": rec.get("content", ""),
            "deadline": rec.get("deadline", ""),
            "status": "已完成",
            "remark": rec.get("remark", ""),
        }
        self.db.update_memo(mid, data)
        self._do_search()

    def _delete(self, mid):
        rec = self.db.get_memo(mid)
        name = rec.get("content", "") if rec else ""
        preview = name[:30] + "…" if len(name) > 30 else name
        if messagebox.askyesno("删除确认", f"确定删除备忘录：\n「{preview}」？", icon="warning"):
            self.db.delete_memo(mid)
            self._do_search()

    # ── 导出 Excel ─────────────────────────────────────
    def _export_xlsx(self):
        kw = self.kw_var.get().strip()
        proj = self.project_var.get()
        st = self.status_var.get()
        records = self.db.get_memos(
            keyword=kw if kw else None,
            project=proj if proj != "全部" else None,
            status=st if st != "全部" else None,
        )
        if not records:
            messagebox.showinfo("提示", "没有可导出的数据，请先查询")
            return

        filepath = filedialog.asksaveasfilename(
            title="导出备忘录", defaultextension=".xlsx",
            filetypes=[("Excel文件", "*.xlsx")],
            initialfile=f"备忘录_{datetime.now().strftime('%Y%m%d')}.xlsx",
        )
        if not filepath:
            return

        headers = ["日期", "项目归属", "经手人", "具体内容", "时间节点", "状态", "备注"]
        rows = []
        for r in records:
            rows.append({
                "日期": r.get("date") or "",
                "项目归属": r.get("project") or "",
                "经手人": r.get("handler") or "",
                "具体内容": r.get("content") or "",
                "时间节点": r.get("deadline") or "",
                "状态": r.get("status") or "",
                "备注": r.get("remark") or "",
            })
        try:
            self.db.export_to_xlsx(filepath, "备忘录", headers, rows,
                                   col_widths=[12, 12, 10, 40, 14, 10, 30])
            messagebox.showinfo("导出成功", f"已导出 {len(rows)} 条记录到：\n{filepath}")
        except Exception as e:
            messagebox.showerror("导出失败", str(e))


# ============================
# 备忘录表单弹窗
# ============================
class MemoForm(ctk.CTkToplevel):
    def __init__(self, parent, db, colors, mid=None, on_save=None):
        super().__init__(parent)
        self.db = db
        self.C = colors
        self.mid = mid
        self.on_save = on_save

        self.title("编辑备忘录" if mid else "新增备忘录")
        self.geometry("680x580")
        self.resizable(True, True)
        self.configure(fg_color=self.C["bg"])

        self.update_idletasks()
        pw, ph = parent.winfo_rootx(), parent.winfo_rooty()
        self.geometry(f"680x580+{pw+80}+{ph+40}")

        self._build()
        if mid:
            self._load(mid)

    def _build(self):
        outer = ctk.CTkScrollableFrame(self, fg_color=self.C["bg"])
        outer.pack(fill="both", expand=True)

        card = ctk.CTkFrame(outer, fg_color=self.C["card"], corner_radius=12)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        def row(parent, label, widget_fn, **kw):
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.pack(fill="x", padx=16, pady=4)
            ctk.CTkLabel(f, text=label, width=90, anchor="w",
                         font=ctk.CTkFont(family="Microsoft YaHei", size=13),
                         text_color=self.C["text_secondary"]).pack(side="left")
            widget_fn(f, **kw)

        def entry(parent, var, ph=""):
            e = ctk.CTkEntry(parent, textvariable=var, height=32,
                             font=ctk.CTkFont(family="Microsoft YaHei", size=13),
                             placeholder_text=ph)
            e.pack(side="left", fill="x", expand=True, padx=(8, 0))

        def combo(parent, var, values, width=180):
            c = ctk.CTkComboBox(parent, variable=var, values=values,
                                width=width, height=32,
                                font=ctk.CTkFont(family="Microsoft YaHei", size=13))
            c.pack(side="left", padx=(8, 0))

        # ── 字段 ──
        self.v_date     = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.v_project  = tk.StringVar()
        self.v_handler  = tk.StringVar(value="纪委")
        self.v_content  = tk.StringVar()
        self.v_deadline = tk.StringVar()
        self.v_status   = tk.StringVar(value="待处理")
        self.v_remark   = tk.StringVar()

        self._section(card, "📋 基本信息")
        row(card, "日期 *",     entry, var=self.v_date,    ph="YYYY-MM-DD")
        row(card, "项目归属",   entry, var=self.v_project, ph="项目名称")
        row(card, "经手人",     entry, var=self.v_handler, ph="经手人姓名")

        self._section(card, "📝 内容")
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(content_frame, text="具体内容 *", width=90, anchor="nw",
                     font=ctk.CTkFont(family="Microsoft YaHei", size=13),
                     text_color=self.C["text_secondary"]).pack(side="left", pady=4)
        self.content_text = ctk.CTkTextbox(content_frame, height=120,
                                           font=ctk.CTkFont(family="Microsoft YaHei", size=13))
        self.content_text.pack(side="left", fill="x", expand=True, padx=(8, 0))

        self._section(card, "⏰ 时间与状态")
        row(card, "时间节点",   entry, var=self.v_deadline, ph="YYYY-MM-DD")
        row(card, "状态",       combo, var=self.v_status,   values=MEMO_STATUS, width=140)

        self._section(card, "📝 备注")
        remark_frame = ctk.CTkFrame(card, fg_color="transparent")
        remark_frame.pack(fill="x", padx=16, pady=4)
        self.remark_text = ctk.CTkTextbox(remark_frame, height=80,
                                          font=ctk.CTkFont(family="Microsoft YaHei", size=13))
        self.remark_text.pack(fill="x")

        # 按钮
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=12)
        ctk.CTkButton(btn_row, text="✓ 保存", width=120, height=38,
                      fg_color=self.C["primary"], hover_color=self.C["primary_hover"],
                      font=ctk.CTkFont(family="Microsoft YaHei", size=16, weight="bold"),
                      command=self._save, corner_radius=20).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="✕ 关闭", width=80, height=38,
                      fg_color="#A0907B", hover_color="#8B7B68",
                      font=ctk.CTkFont(family="Microsoft YaHei", size=14),
                      command=self.destroy, corner_radius=20).pack(side="left", padx=4)

    def _section(self, parent, title):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=16, pady=(12, 4))
        ctk.CTkLabel(f, text=title, font=ctk.CTkFont(family="Microsoft YaHei", size=14, weight="bold"),
                     text_color=self.C["primary"]).pack(side="left")
        ctk.CTkFrame(f, height=1, fg_color=self.C["border"]).pack(
            side="left", fill="x", expand=True, padx=(8, 0))

    def _load(self, mid):
        r = self.db.get_memo(mid)
        if not r:
            return
        self.v_date.set(r.get("date") or "")
        self.v_project.set(r.get("project") or "")
        self.v_handler.set(r.get("handler") or "")
        self.v_deadline.set(r.get("deadline") or "")
        self.v_status.set(r.get("status") or "待处理")
        if r.get("content"):
            self.content_text.insert("1.0", r["content"])
        if r.get("remark"):
            self.remark_text.insert("1.0", r["remark"])

    def _save(self):
        date_val = self.v_date.get().strip()
        content = self.content_text.get("1.0", "end").strip()
        if not date_val:
            messagebox.showerror("验证失败", "请填写日期", parent=self)
            return
        if not content:
            messagebox.showerror("验证失败", "请填写具体内容", parent=self)
            return

        data = {
            "date": date_val,
            "project": self.v_project.get().strip(),
            "handler": self.v_handler.get().strip(),
            "content": content,
            "deadline": self.v_deadline.get().strip(),
            "status": self.v_status.get().strip(),
            "remark": self.remark_text.get("1.0", "end").strip(),
        }

        if self.mid:
            self.db.update_memo(self.mid, data)
            messagebox.showinfo("成功", "备忘录已更新", parent=self)
        else:
            self.db.save_memo(data)
            messagebox.showinfo("成功", "备忘录已添加", parent=self)
        if self.on_save:
            self.on_save()
        self.destroy()
