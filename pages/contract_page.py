#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合同生成页面 V5.0
修改：
  1. 使用默认合同模板（内置到exe），去掉模板选择按钮
  2. 合同编号拆分为 SC/年/月/日/序号 五个文本框
  3. 选择供应商后需点击 [确认] 按钮，将信息注入合同
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter as tk
import os, sys, re, tempfile, zipfile, shutil
from lxml import etree
from datetime import datetime
from ui_utils import WheelScrollFrame

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

def _get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

DEFAULT_TEMPLATE = _get_resource_path("assets/contract_template.docx")

# ═══ 人民币大写 ═══
def num_to_rmb_upper(num):
    if num is None: return ""
    try: f = float(num)
    except: return str(num)
    integer_part = int(f)
    decimal_part = round(f - integer_part, 2)
    cents = int(round(decimal_part * 100))
    if integer_part == 0 and cents == 0: return "零元整"
    digits = "零壹贰叁肆伍陆柒捌玖"
    int_units = ["","拾","佰","仟"]
    def _int_to_str(n):
        if n == 0: return ""
        result = ""; str_n = str(n); zero_flag = False
        for i,ch in enumerate(str_n):
            d = int(ch); ui = (len(str_n)-1-i)%4
            if d == 0:
                if not zero_flag and i!=len(str_n)-1: zero_flag=True; result+="零"
            else:
                if zero_flag: zero_flag=False
                result += digits[d] + int_units[ui]
        return result
    result = ""
    if integer_part == 0: result = "零元"
    else:
        yi = integer_part // 100000000
        wan = (integer_part % 100000000) // 10000
        ge = integer_part % 10000
        def _section(n):
            if n==0: return ""
            return _int_to_str(n).rstrip("零")
        parts = []
        if yi>0: parts.append(_section(yi)+"亿")
        if wan>0: parts.append(_section(wan)+"万")
        elif yi>0 and ge>0: parts.append("零")
        if ge>0: parts.append(_section(ge))
        result = "".join(parts) + "元"
    if cents==0: result+="整"
    else:
        jiao=cents//10; fen=cents%10
        if jiao>0: result+=digits[jiao]+"角"
        if fen>0:
            if jiao==0: result+="零"
            result+=digits[fen]+"分"
        else: result+="整"
    return result

# ═══ XML 文本替换（跨<w:t>精准替换） ═══
def _collect_wt_positions(root_or_elem):
    wt_list = []; full_len = 0
    def _walk(elem):
        nonlocal full_len
        for child in list(elem):
            if child.tag == W+'t':
                text = child.text or ""
                wt_list.append((child, full_len, full_len+len(text), text))
                full_len += len(text)
            _walk(child)
    _walk(root_or_elem)
    return wt_list, full_len

def _replace_text_in_xml(root_or_elem, old_text, new_text):
    wt_list, total_len = _collect_wt_positions(root_or_elem)
    if not wt_list: return False
    full_text = "".join(t[3] for t in wt_list)
    idx = full_text.find(old_text)
    if idx == -1: return False
    start_pos = idx; end_pos = idx+len(old_text)
    start_wt_idx = end_wt_idx = None
    for i,(wt_elem, ws, we, wt_text) in enumerate(wt_list):
        if start_wt_idx is None and ws <= start_pos < we: start_wt_idx=i
        if ws < end_pos <= we: end_wt_idx=i; break
    if start_wt_idx is None or end_wt_idx is None: return False
    if start_wt_idx == end_wt_idx:
        wt_elem,ws,we,wt_text = wt_list[start_wt_idx]
        off = start_pos - ws
        wt_elem.text = wt_text[:off] + new_text + wt_text[off+len(old_text):]
    else:
        first_wt, fws, _, ftxt = wt_list[start_wt_idx]
        foff = start_pos - fws
        first_wt.text = ftxt[:foff] + new_text
        # Delete intermediate wt elements (keep last_wt for remaining text)
        for i in range(start_wt_idx+1, end_wt_idx):
            parent = wt_list[i][0].getparent()
            if parent is not None:
                parent.remove(wt_list[i][0])
        # Keep last_wt: preserve text AFTER old_text
        last_wt, lws, lwe, ltxt = wt_list[end_wt_idx]
        loff = end_pos - lws
        if loff < len(ltxt):
            last_wt.text = ltxt[loff:]
        else:
            last_wt.text = ""
    return True

def _replace_all_text_in_xml(root_or_elem, old_text, new_text):
    result = False
    while _replace_text_in_xml(root_or_elem, old_text, new_text):
        result = True
    return result

# ═══ 对话框 ═══
class SupplierDialog(ctk.CTkToplevel):
    def __init__(self, parent, supplier=None, on_save=None):
        super().__init__(parent)
        self.title("编辑供应商" if supplier else "新增供应商")
        self.geometry("560x600"); self.resizable(False,False)
        self.supplier=supplier; self.on_save=on_save; self.entries={}
        try: self.after(200,lambda:self.attributes('-topmost',True))
        except: pass
        self._build()
    def _build(self):
        ctk.CTkLabel(self,text="供应商信息",
            font=ctk.CTkFont(family="Microsoft YaHei",size=17,weight="bold"),
        ).pack(pady=(16,12))
        form=ctk.CTkFrame(self,fg_color="transparent")
        form.pack(fill="both",expand=True,padx=20,pady=(0,10))
        fields=[
            ("short_name","简称 *",240),("full_name","公司全称 *",480),
            ("legal_rep","法定代表人",240),("address","地址",480),
            ("contact","联系人",240),("auth_rep","授权代表",240),
            ("phone","电话",240),("fax","传真",240),
            ("payment_days","账期（天）",160),
            ("account_name","账户名称",480),("bank","开户行",480),
            ("account","账号",480),
        ]
        for i,(key,label,w) in enumerate(fields):
            ctk.CTkLabel(form,text=label,width=100,anchor="e",
                font=ctk.CTkFont(size=13)).grid(row=i,column=0,padx=(0,6),pady=4)
            e=ctk.CTkEntry(form,width=w,height=30,font=ctk.CTkFont(size=13))
            e.grid(row=i,column=1,padx=0,pady=4,sticky="w")
            if self.supplier and key in self.supplier:
                e.insert(0,str(self.supplier.get(key,"")))
            self.entries[key]=e
        bf=ctk.CTkFrame(self,fg_color="transparent")
        bf.pack(fill="x",padx=20,pady=(0,16))
        ctk.CTkButton(bf,text="保存",width=100,height=32,
            font=ctk.CTkFont(size=14),command=self._save).pack(side="right",padx=4)
        ctk.CTkButton(bf,text="取消",width=100,height=32,
            fg_color="#6B7280",hover_color="#4B5563",
            font=ctk.CTkFont(size=14),command=self.destroy).pack(side="right",padx=4)
    def _save(self):
        data={k:v.get().strip() for k,v in self.entries.items()}
        if not data.get("short_name"): messagebox.showwarning("提示","简称不能为空");return
        if not data.get("full_name"): messagebox.showwarning("提示","公司全称不能为空");return
        if self.on_save: self.on_save(data)
        self.destroy()

class PartyAConfigDialog(ctk.CTkToplevel):
    def __init__(self, parent, config, on_save):
        super().__init__(parent)
        self.title("甲方配置"); self.geometry("520x380"); self.resizable(False,False)
        self.config=config; self.on_save=on_save; self.entries={}
        try: self.after(200,lambda:self.attributes('-topmost',True))
        except: pass
        self._build()
    def _build(self):
        ctk.CTkLabel(self,text="甲方信息配置",
            font=ctk.CTkFont(family="Microsoft YaHei",size=17,weight="bold"),
        ).pack(pady=(16,12))
        form=ctk.CTkFrame(self,fg_color="transparent")
        form.pack(fill="both",expand=True,padx=20,pady=(0,10))
        fields=[
            ("company_name","公司全称：",400),
            ("legal_rep","法定代表人：",200),
            ("address","地址：",400),
            ("contact","联系人：",200),
            ("phone","电话：",200),
        ]
        for i,(key,label,w) in enumerate(fields):
            ctk.CTkLabel(form,text=label,width=100,anchor="e",
                font=ctk.CTkFont(size=14)).grid(row=i,column=0,padx=(0,8),pady=8)
            e=ctk.CTkEntry(form,width=w,height=32,font=ctk.CTkFont(size=14))
            e.grid(row=i,column=1,padx=0,pady=8,sticky="w")
            if self.config and key in self.config:
                e.insert(0,str(self.config.get(key,"")))
            self.entries[key]=e
        bf=ctk.CTkFrame(self,fg_color="transparent")
        bf.pack(fill="x",padx=20,pady=(0,16))
        ctk.CTkButton(bf,text="保存",width=100,height=34,
            fg_color="#2563BE",hover_color="#1D4ED8",
            font=ctk.CTkFont(size=14,weight="bold"),
            command=self._save).pack(side="right",padx=4)
        ctk.CTkButton(bf,text="取消",width=100,height=34,
            fg_color="#6B7280",hover_color="#4B5563",
            font=ctk.CTkFont(size=14),command=self.destroy).pack(side="right",padx=4)
    def _save(self):
        data={k:v.get().strip() for k,v in self.entries.items()}
        if not data.get("company_name"): messagebox.showwarning("提示","公司全称不能为空");return
        if self.on_save: self.on_save(data)
        self.destroy()

# ═══ 合同生成主页面 ═══
class ContractPage(ctk.CTkFrame):
    def __init__(self, parent, db, C):
        super().__init__(parent, fg_color=C["bg"], corner_radius=0)
        self.db=db; self.C=C
        self.product_rows=[]
        self.suppliers=self.db.get_contract_suppliers()
        self.party_a=self.db.get_contract_party_a()
        # 内部存储乙方数据
        self.party_b = {
            "full_name":"","legal_rep":"","address":"",
            "contact":"","auth_rep":"","phone":"","fax":"",
            "payment_days":"90",
            "account_name":"","bank":"","account":"",
        }
        # 确认状态：是否已确认供应商
        self.supplier_confirmed = False
        self._build_ui()

    # ── UI ──
    def _build_ui(self):
        # 顶部工具栏
        toolbar=ctk.CTkFrame(self,fg_color="transparent",height=52)
        toolbar.pack(fill="x",padx=20,pady=(16,8)); toolbar.pack_propagate(False)
        ctk.CTkLabel(toolbar,text="合同生成",
            font=ctk.CTkFont(family="Microsoft YaHei",size=16,weight="bold"),
            text_color=self.C["text"]).pack(side="left",pady=14)
        bf=ctk.CTkFrame(toolbar,fg_color="transparent"); bf.pack(side="right",pady=8)
        ctk.CTkButton(bf,text="生成合同",width=130,height=34,
            fg_color=self.C["primary"],hover_color=self.C["primary_hover"],
            font=ctk.CTkFont(size=14,weight="bold"),
            command=self._generate_contract).pack(side="right",padx=4)
        ctk.CTkButton(bf,text="甲方配置",width=120,height=34,
            fg_color="#2563BE",hover_color="#1D4ED8",
            font=ctk.CTkFont(size=13,weight="bold"),
            command=self._open_party_a_config).pack(side="right",padx=4)
        ctk.CTkButton(bf,text="+管理供应商",width=130,height=34,
            fg_color="#B5605A",hover_color="#9B4F4A",
            font=ctk.CTkFont(size=13,weight="bold"),
            command=self._manage_suppliers).pack(side="right",padx=(4,8))

        # 供应商检索栏
        sb=ctk.CTkFrame(self,fg_color=self.C["card"],corner_radius=self.C["radius_card"])
        sb.pack(fill="x",padx=24,pady=(0,8))
        ctk.CTkLabel(sb,text="[搜索]  供应商检索：",
            font=ctk.CTkFont(family="Microsoft YaHei",size=14,weight="bold"),
            text_color=self.C["text"]).pack(side="left",padx=(16,6),pady=12)
        self.supplier_var=tk.StringVar()
        self.supplier_combo=ctk.CTkComboBox(sb,
            values=[""]+[s["short_name"] for s in self.suppliers],
            variable=self.supplier_var,width=180,height=32,
            font=ctk.CTkFont(size=14),command=self._on_supplier_select)
        self.supplier_combo.pack(side="left",padx=(0,10),pady=12)
        ctk.CTkLabel(sb,text="或输入：",font=ctk.CTkFont(size=13),
            text_color="#9CA3AF").pack(side="left",padx=(0,6),pady=12)
        self.search_entry=ctk.CTkEntry(sb,width=140,height=32,
            placeholder_text="输入简称/全称...",font=ctk.CTkFont(size=13))
        self.search_entry.pack(side="left",padx=(0,10),pady=12)
        self.search_entry.bind("<KeyRelease>",self._on_search)
        ctk.CTkButton(sb,text="检索",width=60,height=30,
            fg_color=self.C["primary"],hover_color=self.C["primary_hover"],
            font=ctk.CTkFont(size=13),
            command=lambda:self._on_search(None)).pack(side="left",padx=(0,10),pady=12)
        # 确认按钮
        self.confirm_btn = ctk.CTkButton(sb,text="确认",width=100,height=30,
            fg_color=self.C["success"],hover_color="#7A9A6E",
            font=ctk.CTkFont(size=13,weight="bold"),
            command=self._on_confirm_supplier)
        self.confirm_btn.pack(side="left",padx=(0,10),pady=12)
        ctk.CTkButton(sb,text="重置",width=100,height=30,
            fg_color="#6B7280",hover_color="#4B5563",
            font=ctk.CTkFont(size=13,weight="bold"),
            command=self._on_reset_all).pack(side="left",padx=(0,10),pady=12)
        # 确认状态标签
        self.confirm_status_label = ctk.CTkLabel(sb,text="",
            font=ctk.CTkFont(size=12),text_color="#9CA3AF")
        self.confirm_status_label.pack(side="left",padx=(0,10),pady=12)

        # 滚动区域
        scroll=ctk.CTkScrollableFrame(self,fg_color="transparent",corner_radius=0)
        scroll.pack(fill="both",expand=True,padx=24,pady=(0,16))
        self._build_contract_info(scroll)
        self._build_products(scroll)

    # ── 甲方配置 ──
    def _open_party_a_config(self):
        PartyAConfigDialog(self,self.party_a,self._save_party_a_config)
    def _save_party_a_config(self,data):
        self.party_a=data; self.db.update_contract_party_a(data)
        messagebox.showinfo("成功","甲方配置已保存")

    # ── 供应商检索 ──
    def _on_search(self,event):
        kw=self.search_entry.get().strip()
        if not kw: return
        matched=[s for s in self.suppliers
                 if kw.lower() in s.get("short_name","").lower()
                 or kw.lower() in s.get("full_name","").lower()]
        if matched:
            names=[s["short_name"] for s in matched]
            self.supplier_combo.configure(values=names)
            if names:
                self.supplier_var.set(names[0])
                # 选择后重置确认状态
                self.supplier_confirmed = False
                self.confirm_status_label.configure(text="")
                self._on_supplier_select(names[0])

    def _on_supplier_select(self,name):
        if not name: return
        # 供应商变更时重置确认状态
        self.supplier_confirmed = False
        self.confirm_status_label.configure(text="")
        # 填充乙方（暂存，等确认后才生效）
        for s in self.suppliers:
            if s.get("short_name")==name:
                self._pending_supplier = s
                return

    def _on_confirm_supplier(self):
        """确认按钮：注入供应商信息到合同"""
        name = self.supplier_var.get().strip()
        if not name:
            messagebox.showwarning("提示","请先选择供应商")
            return
        s = None
        for sup in self.suppliers:
            if sup.get("short_name")==name:
                s = sup
                break
        if not s:
            messagebox.showwarning("提示","未找到该供应商")
            return
        # 注入乙方数据
        self._fill_party_b(s)
        self.supplier_confirmed = True
        self.confirm_status_label.configure(text=f"已确认: {s.get('short_name','')}", text_color="#8FA882")
        # 更新合同编号
        self._update_combined_no()

    def _on_reset_all(self):
        """重置合同信息和产品信息"""
        if not messagebox.askyesno("确认重置","将清空合同信息和产品信息，是否继续？"):
            return
        # 重置合同编号
        self.entry_sc.delete(0,"end")
        self.entry_year.delete(0,"end")
        self.entry_month.delete(0,"end")
        self.entry_day.delete(0,"end")
        self.entry_seq.delete(0,"end")
        self.entry_combined_no.configure(state="normal")
        self.entry_combined_no.delete(0,"end")
        self.entry_combined_no.configure(state="readonly")
        # 重置签订日期
        self.entry_contract_date.delete(0,"end")
        # 重置下单物料
        self.entry_material_name.delete(0,"end")
        # 重置乙方信息
        for k in self.party_b:
            self.party_b[k] = ""
        self.party_b["payment_days"] = "90"
        # 重置供应商确认状态
        self.supplier_confirmed = False
        self.confirm_status_label.configure(text="")
        self.supplier_var.set("")
        self._pending_supplier = None
        # 重置产品信息：清空所有产品行，只保留一个空行
        for item in list(self.product_rows):
            self._remove_product_row(item)
        self._add_product_row(default=True)
        # 重置确认按钮状态
        # 确认按钮已移除，无需重置
        # 重置供应商确认按钮外观
        if hasattr(self,'confirm_btn'):
            self.confirm_btn.configure(fg_color=self.C["success"],state="normal")
        messagebox.showinfo("重置成功","合同信息和产品信息已重置")

    def _fill_party_b(self,s):
        """注入乙方数据"""
        self.party_b["full_name"]    = s.get("full_name","")
        self.party_b["legal_rep"]    = s.get("legal_rep","")
        self.party_b["address"]      = s.get("address","")
        self.party_b["contact"]      = s.get("contact","")
        self.party_b["auth_rep"]     = s.get("auth_rep","")
        self.party_b["phone"]        = s.get("phone","")
        self.party_b["fax"]          = s.get("fax","")
        self.party_b["payment_days"] = s.get("payment_days","90")
        self.party_b["account_name"] = s.get("account_name","")
        self.party_b["bank"]         = s.get("bank","")
        self.party_b["account"]      = s.get("account","")

    # ── 供应商管理 ──
    def _manage_suppliers(self):
        dialog=ctk.CTkToplevel(self)
        dialog.title("供应商管理"); dialog.geometry("750x520")
        dialog.resizable(False,False)
        try: dialog.after(200,lambda:dialog.attributes('-topmost',True))
        except: pass
        top=ctk.CTkFrame(dialog,fg_color="transparent",height=50)
        top.pack(fill="x",padx=16,pady=(14,4)); top.pack_propagate(False)
        ctk.CTkLabel(top,text="供应商信息库",
            font=ctk.CTkFont(family="Microsoft YaHei",size=17,weight="bold"),
        ).pack(side="left",pady=10)
        ctk.CTkButton(top,text="+ 新增",width=80,height=30,
            font=ctk.CTkFont(size=13),
            command=lambda:self._add_supplier_dialog(dialog),
        ).pack(side="right",padx=4,pady=8)
        self._supplier_list_frame=WheelScrollFrame(dialog,fg_color="transparent")
        self._supplier_list_frame.pack(fill="both",expand=True,padx=16,pady=(0,12))
        self._refresh_supplier_list(dialog,self._supplier_list_frame)
    def _refresh_supplier_list(self,dialog,lf):
        for w in lf.winfo_children(): w.destroy()
        if not self.suppliers:
            ctk.CTkLabel(lf,text="暂无供应商数据，点击右上角 [新增] 添加",
                font=ctk.CTkFont(size=14),text_color="#9CA3AF").pack(pady=24)
        else:
            for s in self.suppliers:
                r=ctk.CTkFrame(lf,fg_color=self.C["card"],corner_radius=6)
                r.pack(fill="x",pady=3)
                info=f"[{s.get('short_name','')}]  {s.get('full_name','')}  |  账期:{s.get('payment_days','')}天  |  {s.get('contact','')} {s.get('phone','')}"
                ctk.CTkLabel(r,text=info,font=ctk.CTkFont(size=13),anchor="w",
                ).pack(side="left",padx=(12,4),pady=8)
                ctk.CTkButton(r,text="编辑",width=50,height=26,
                    fg_color=self.C["primary"],hover_color=self.C["primary_hover"],
                    font=ctk.CTkFont(size=12),
                    command=lambda sup=s: [dialog.destroy(),self._edit_supplier_dialog(sup)],
                ).pack(side="right",padx=4,pady=4)
                ctk.CTkButton(r,text="删除",width=50,height=26,
                    fg_color="#B56A6A",hover_color="#A85A5A",
                    font=ctk.CTkFont(size=12),
                    command=lambda sup=s: self._delete_supplier(sup,dialog,lf),
                ).pack(side="right",padx=2,pady=4)
    def _add_supplier_dialog(self,pd=None):
        if pd: pd.destroy()
        SupplierDialog(self,on_save=self._save_new_supplier)
    def _edit_supplier_dialog(self,supplier):
        SupplierDialog(self,supplier=supplier,
            on_save=lambda data:self._update_supplier(supplier,data))
    def _save_new_supplier(self,data):
        data.setdefault("payment_method","电汇")
        data.setdefault("remark","")
        sid=self.db.save_contract_supplier(data)
        data["id"]=sid
        self.suppliers=self.db.get_contract_suppliers()
        self._refresh_combo()
        messagebox.showinfo("成功",f"供应商 {data['short_name']} 已添加")
    def _update_supplier(self,old,data):
        data.setdefault("payment_method",old.get("payment_method","电汇"))
        data.setdefault("remark",old.get("remark",""))
        self.db.update_contract_supplier(old["id"],data)
        self.suppliers=self.db.get_contract_suppliers()
        self._refresh_combo()
        messagebox.showinfo("成功",f"供应商 {data['short_name']} 已更新")
    def _delete_supplier(self,supplier,dialog,lf):
        if messagebox.askyesno("确认删除",f"确定要删除供应商 [{supplier.get('short_name')}] 吗？"):
            self.db.delete_contract_supplier(supplier["id"])
            self.suppliers=self.db.get_contract_suppliers()
            self._refresh_combo(); self._refresh_supplier_list(dialog,lf)
    def _refresh_combo(self):
        names=[s["short_name"] for s in self.suppliers]
        self.supplier_combo.configure(values=names)

    # ── 合同信息（编号拆分版）──
    def _build_contract_info(self,parent):
        card=ctk.CTkFrame(parent,fg_color=self.C["card"],corner_radius=self.C["radius_card"])
        card.pack(fill="x",pady=(0,12))
        # 标题行 + 确认按钮
        header=ctk.CTkFrame(card,fg_color="transparent")
        header.pack(fill="x",padx=20,pady=(14,8))
        ctk.CTkLabel(header,text="合同信息",
            font=ctk.CTkFont(family="Microsoft YaHei",size=17,weight="bold"),
            text_color=self.C["text"]).pack(side="left")
        # 确认按钮已移除
        form=ctk.CTkFrame(card,fg_color="transparent")
        form.pack(fill="x",padx=20,pady=(0,14))

        now=datetime.now()

        # 第0行：合同编号 (拆分版)
        ctk.CTkLabel(form,text="合同编号：",width=100,anchor="e",
            font=ctk.CTkFont(size=14)).grid(row=0,column=0,padx=(0,8),pady=6,sticky="e")

        no_frame = ctk.CTkFrame(form,fg_color="transparent")
        no_frame.grid(row=0,column=1,columnspan=3,padx=4,pady=6,sticky="w")

        # SC 前缀
        self.entry_sc_prefix = ctk.CTkEntry(no_frame,width=50,height=32,
            font=ctk.CTkFont(size=14),justify="center")
        self.entry_sc_prefix.pack(side="left",padx=(0,2))
        self.entry_sc_prefix.insert(0,"SC")

        # 年
        self.entry_sc_year = ctk.CTkEntry(no_frame,width=58,height=32,
            font=ctk.CTkFont(size=14),justify="center")
        self.entry_sc_year.pack(side="left",padx=1)
        self.entry_sc_year.insert(0,str(now.year))

        ctk.CTkLabel(no_frame,text="-",font=ctk.CTkFont(size=16),
            width=12).pack(side="left")

        # 月
        self.entry_sc_month = ctk.CTkEntry(no_frame,width=40,height=32,
            font=ctk.CTkFont(size=14),justify="center")
        self.entry_sc_month.pack(side="left",padx=1)
        self.entry_sc_month.insert(0,f"{now.month:02d}")

        ctk.CTkLabel(no_frame,text="-",font=ctk.CTkFont(size=16),
            width=12).pack(side="left")

        # 日
        self.entry_sc_day = ctk.CTkEntry(no_frame,width=40,height=32,
            font=ctk.CTkFont(size=14),justify="center")
        self.entry_sc_day.pack(side="left",padx=1)
        self.entry_sc_day.insert(0,f"{now.day:02d}")

        ctk.CTkLabel(no_frame,text="-",font=ctk.CTkFont(size=16),
            width=12).pack(side="left")

        # 序号
        self.entry_sc_seq = ctk.CTkEntry(no_frame,width=50,height=32,
            font=ctk.CTkFont(size=14),justify="center")
        self.entry_sc_seq.pack(side="left",padx=1)
        self.entry_sc_seq.insert(0,"01")

        # 合并编号显示
        ctk.CTkLabel(no_frame,text="  => 合并编号：",font=ctk.CTkFont(size=13),
            text_color="#9CA3AF").pack(side="left",padx=(8,2))
        self.entry_combined_no = ctk.CTkEntry(no_frame,width=200,height=32,
            font=ctk.CTkFont(size=14,weight="bold"),
            state="readonly")
        self.entry_combined_no.pack(side="left",padx=1)

        # 绑定各字段变化自动更新合并编号
        for entry in [self.entry_sc_prefix, self.entry_sc_year,
                       self.entry_sc_month, self.entry_sc_day, self.entry_sc_seq]:
            entry.bind("<KeyRelease>", lambda e: self._update_combined_no())

        # 第1行：下单物料
        ctk.CTkLabel(form,text="下单物料：",width=100,anchor="e",
            font=ctk.CTkFont(size=14)).grid(row=1,column=0,padx=(0,8),pady=6,sticky="e")
        self.entry_material_name=ctk.CTkEntry(form,
            placeholder_text="例如：铁棍山药粉纸盒",width=280,height=32,
            font=ctk.CTkFont(size=14))
        self.entry_material_name.grid(row=1,column=1,padx=4,pady=6,sticky="w")

        # 第2行：签订日期
        ctk.CTkLabel(form,text="签订日期：",width=100,anchor="e",
            font=ctk.CTkFont(size=14)).grid(row=2,column=0,padx=(0,8),pady=6,sticky="e")
        self.entry_contract_date=ctk.CTkEntry(form,
            placeholder_text="2026年06月09日",width=200,height=32,
            font=ctk.CTkFont(size=14))
        self.entry_contract_date.grid(row=2,column=1,padx=4,pady=6,sticky="w")
        self.entry_contract_date.insert(0,self._auto_contract_date())

        # 合计金额（原结算方式行变为合计金额行）
        ctk.CTkLabel(form,text="合计金额：",width=100,anchor="e",
            font=ctk.CTkFont(size=14)).grid(row=3,column=0,padx=(0,8),pady=6,sticky="e")
        self.total_label=ctk.CTkLabel(form,text="合计: 0.00 元",
            font=ctk.CTkFont(family="Microsoft YaHei",size=16,weight="bold"),
            text_color=self.C["primary"])
        self.total_label.grid(row=3,column=1,sticky="w",padx=4,pady=6)

        # 初始更新合并编号
        self._update_combined_no()

    def _update_combined_no(self):
        """根据拆分的字段更新合并编号"""
        prefix = self.entry_sc_prefix.get().strip()
        year = self.entry_sc_year.get().strip()
        month = self.entry_sc_month.get().strip()
        day = self.entry_sc_day.get().strip()
        seq = self.entry_sc_seq.get().strip()
        combined = f"{prefix}{year}-{month}-{day}-{seq}"
        self.entry_combined_no.configure(state="normal")
        self.entry_combined_no.delete(0,"end")
        self.entry_combined_no.insert(0,combined)
        self.entry_combined_no.configure(state="readonly")
        # 自动匹配签订日期
        if year and month and day:
            contract_date = f"{year}年{month.zfill(2)}月{day.zfill(2)}日"
            self.entry_contract_date.delete(0, "end")
            self.entry_contract_date.insert(0, contract_date)

    # ── 产品信息 ──
    def _build_products(self,parent):
        card=ctk.CTkFrame(parent,fg_color=self.C["card"],corner_radius=self.C["radius_card"])
        card.pack(fill="x",pady=(0,12))
        hf=ctk.CTkFrame(card,fg_color="transparent")
        hf.pack(fill="x",padx=20,pady=(14,8))
        ctk.CTkLabel(hf,text="产品信息",
            font=ctk.CTkFont(family="Microsoft YaHei",size=17,weight="bold"),
            text_color=self.C["text"]).pack(side="left")
        ctk.CTkButton(hf,text="+ 添加产品",width=100,height=30,
            fg_color=self.C["success"],hover_color="#7A9A6E",
            font=ctk.CTkFont(size=13),
            command=self._add_product_row).pack(side="right")
        self.product_container=ctk.CTkFrame(card,fg_color="transparent")
        self.product_container.pack(fill="x",padx=20,pady=(0,14))
        hdr=ctk.CTkFrame(self.product_container,fg_color="transparent")
        hdr.pack(fill="x",pady=(0,4))
        for h in ["物料名称","项目号","材料结构","尺寸","单位","数量","单价","金额","备注","操作"]:
            ctk.CTkLabel(hdr,text=h,width=88,anchor="center",
                font=ctk.CTkFont(size=13,weight="bold")).pack(side="left",padx=1)
        self._add_product_row(default=True)

        # 确认按钮已移除

    def _add_product_row(self,default=False):
        rf=ctk.CTkFrame(self.product_container,fg_color="transparent")
        rf.pack(fill="x",pady=2)
        entries={}
        for fn in ["物料名称","项目号","材料结构","尺寸","单位","数量","单价"]:
            e=ctk.CTkEntry(rf,width=130,height=30,font=ctk.CTkFont(size=12))
            e.pack(side="left",padx=1); entries[fn]=e
        amt_label=ctk.CTkLabel(rf,text="",width=90,anchor="center",
            font=ctk.CTkFont(size=12),text_color=self.C["text"])
        amt_label.pack(side="left",padx=1)
        entries["_amt_label"]=amt_label
        e_note=ctk.CTkEntry(rf,width=130,height=30,font=ctk.CTkFont(size=12))
        e_note.pack(side="left",padx=1); entries["备注"]=e_note
        def _calc_amt(*a):
            try:
                q=float(entries["数量"].get() or 0)
                p=float(entries["单价"].get() or 0)
                amt=q*p
                entries["_amt_label"].configure(text=f"{amt:.2f}")
                self._update_total_display()
            except: pass
        entries["数量"].bind("<KeyRelease>",_calc_amt)
        entries["单价"].bind("<KeyRelease>",_calc_amt)
        if default:
            defaults={"物料名称":"青源堂红黑枸杞原浆礼盒1.8L外盒",
                "项目号":"81014365","材料结构":"","尺寸":"350*168*93","单位":"个",
                "数量":"5000","单价":"4.3","备注":""}
            for k,v in defaults.items():
                entries[k].insert(0,v)
            _calc_amt()
        del_btn=ctk.CTkButton(rf,text="X",width=30,height=30,
            fg_color="#B56A6A",hover_color="#A85A5A",
            font=ctk.CTkFont(size=12),
            command=lambda f=rf: self._del_product_row(f))
        del_btn.pack(side="left",padx=2)
        rf.entries=entries; self.product_rows.append(rf)

    def _del_product_row(self,rf):
        if len(self.product_rows)<=1:
            messagebox.showwarning("提示","至少保留一行产品信息"); return
        rf.destroy(); self.product_rows.remove(rf)
        self._update_total_display()

    def _update_total_display(self):
        total=0.0
        for row in self.product_rows:
            try:
                q=float(row.entries["数量"].get() or 0)
                p=float(row.entries["单价"].get() or 0)
                total+=q*p
            except: pass
        if hasattr(self,'total_label'):
            rmb=num_to_rmb_upper(total)
            self.total_label.configure(text=f"合计: {total:.2f} 元 (大写: {rmb})")

    # ── 辅助方法 ──
    def _get_contract_no(self):
        """获取合并后的合同编号"""
        return self.entry_combined_no.get().strip()

    def _auto_contract_date(self):
        now=datetime.now()
        return f"{now.year}年{now.month:02d}月{now.day:02d}日"

    def _get_material_name(self):
        """获取下单物料名称（购得XXXX产品中的XXXX）"""
        return self.entry_material_name.get().strip()

    def _get_products(self):
        products=[]
        for row in self.product_rows:
            e=row.entries
            p={}
            p["name"]=e["物料名称"].get().strip()
            p["item_no"]=e["项目号"].get().strip()
            p["material_struct"]=e["材料结构"].get().strip()
            p["size"]=e["尺寸"].get().strip()
            p["unit"]=e["单位"].get().strip()
            p["qty"]=e["数量"].get().strip()
            p["price"]=e["单价"].get().strip()
            p["note"]=e["备注"].get().strip()
            try:
                q=float(p["qty"] or 0); pr=float(p["price"] or 0)
                p["amount"]=f"{q*pr:.2f}"
            except: p["amount"]="0.00"
            if p["name"]: products.append(p)
        return products

    # ── 生成合同 ──
    def _generate_contract(self):
        if not self.supplier_confirmed:
            messagebox.showerror("错误","请先选择供应商并点击 [确认] 按钮"); return

        contract_no=self._get_contract_no()
        contract_date=self.entry_contract_date.get().strip()
        material_name=self._get_material_name()
        products=self._get_products()
        pa=self.party_a.copy()
        pb=dict(self.party_b)

        if not contract_no: messagebox.showerror("错误","请输入合同编号"); return
        if not pb.get("full_name"): messagebox.showerror("错误","请先检索并选择供应商"); return
        if not material_name: messagebox.showerror("错误","请输入下单物料名称"); return
        if not products: messagebox.showerror("错误","请至少添加一个产品"); return

        # 文件名格式：采购合同_供应商全称_YYYY_MM_DD_物料名称
        date_str=datetime.now().strftime("%Y_%m_%d")
        supplier_name=pb.get("full_name","")[:30]  # 供应商全称，最长30字符
        material_short=material_name[:20] if material_name else "未命名"
        # 替换Windows文件名非法字符
        import re as _re
        supplier_name=_re.sub(r'[\\/:*?"<>|]', '', supplier_name)
        material_short=_re.sub(r'[\\/:*?"<>|]', '', material_short)
        initial_name=f"采购合同_{supplier_name}_{date_str}_{material_short}.docx"
        save_path=filedialog.asksaveasfilename(
            title="保存合同",
            initialfile=initial_name,
            defaultextension=".docx", filetypes=[("Word文档","*.docx")])
        if not save_path: return

        try:
            self._do_generate(save_path,contract_no,contract_date,
                material_name,pa,pb,products)
            messagebox.showinfo("成功",f"合同已生成：\n{save_path}")
        except Exception as e:
            messagebox.showerror("生成失败",f"错误：\n{str(e)}")
            import traceback; traceback.print_exc()

    def _do_generate(self,save_path,contract_no,contract_date,
                     material_name,pa,pb,products):
        template=DEFAULT_TEMPLATE
        if not os.path.exists(template):
            raise FileNotFoundError(f"模板不存在：\n{template}")
        tmp_dir=tempfile.mkdtemp(prefix="contract_")
        unpack_dir=os.path.join(tmp_dir,"unpacked")
        os.makedirs(unpack_dir,exist_ok=True)
        tmp_template=os.path.join(tmp_dir,"template.docx")
        shutil.copy2(template,tmp_template)
        with zipfile.ZipFile(tmp_template,"r") as zf:
            zf.extractall(unpack_dir)
        self._replace_header(unpack_dir,contract_no)
        self._replace_document(unpack_dir,contract_no,contract_date,
            material_name,pa,pb,products)
        self._repack_docx(unpack_dir,save_path)
        shutil.rmtree(tmp_dir,ignore_errors=True)

    # ── 页眉替换 ──
    def _replace_header(self,unpack_dir,contract_no):
        hp=os.path.join(unpack_dir,"word","header1.xml")
        if not os.path.exists(hp): return
        tree=etree.parse(hp); root=tree.getroot()
        m=re.search(r'SC(\d{4})-(\d{2}-\d{2})-(\d{2})',contract_no)
        if not m: return
        new_mmdd=m.group(2); new_seq="-"+m.group(3)
        wt_list=root.findall(f'.//{W}t')
        for wt in wt_list:
            if wt.text and re.search(r'\d{2}-\d{2}',wt.text):
                wt.text=re.sub(r'\d{2}-\d{2}',new_mmdd,wt.text)
        for wt in wt_list:
            if wt.text and re.match(r'-\d{2}$',wt.text):
                wt.text=new_seq
        tree.write(hp,encoding="UTF-8",xml_declaration=True)

    # ── 正文替换 ──
    def _replace_document(self,unpack_dir,contract_no,contract_date,
                          material_name,pa,pb,products):
        """替换合同正文：适配干净模板（无预填乙方数据）"""
        dp=os.path.join(unpack_dir,"word","document.xml")
        if not os.path.exists(dp): return
        tree=etree.parse(dp); root=tree.getroot()
        paragraphs=list(root.iter(W + 'p'))
        tables=list(root.iter(W + 'tbl'))

        pb_full = pb.get("full_name","")
        pb_contact = pb.get("contact","")
        pb_phone = pb.get("phone","")
        account_name = pb.get("account_name","")
        bank = pb.get("bank","")
        account = pb.get("account","")

        # === 1. 产品名称 + 签订日期（直接操作 w:r 保留下划线）===
        for para in paragraphs:
            full_text="".join((t.text or "") for t in para.iter(W + 't'))
            if "生产经营需要" in full_text:
                self._fill_underlined_placeholders(para, material_name, contract_date)
                break

        # === 2. 甲乙双方表格 ===
        if len(tables)>=1:
            self._replace_party_table(tables[0],pa,pb)

        # === 3. 产品表格 ===
        if len(tables)>=2:
            self._replace_product_table(tables[1],products)

        # === 4. 账户信息（干净模板：3个独立段落）===
        for para in paragraphs:
            full_text="".join((t.text or "") for t in para.iter(W + 't'))
            # 账户名称段落
            if "账户名称" in full_text and account_name:
                m = re.search(r'账户名称：(\s*)', full_text)
                if m:
                    _replace_text_in_xml(para, m.group(0), f'账户名称：{account_name}')
                continue
            # 开户行段落
            if "开 户 行" in full_text and bank:
                m = re.search(r'开 户 行：(\s*)', full_text)
                if m:
                    _replace_text_in_xml(para, m.group(0), f'开 户 行：{bank}')
                continue
            # 账号段落
            if re.search(r'账\s+号', full_text) and account:
                m = re.search(r'(账\s+号：)(\s*)', full_text)
                if m:
                    _replace_text_in_xml(para, m.group(0), m.group(1) + account)
                continue

        # === 7. 乙方公司名（签名区段落）===
        for para in paragraphs:
            full_text="".join((t.text or "") for t in para.iter(W + 't'))
            if "乙方（盖章）" in full_text:
                if pb_full:
                    m = re.search(r'乙方（盖章）：(\s*)', full_text)
                    if m:
                        _replace_text_in_xml(para, m.group(0),
                                             f'乙方（盖章）：{pb_full}')
                break

        tree.write(dp,encoding="UTF-8",xml_declaration=True)

    def _add_underline_to_run(self, run_elem):
        """给指定的 w:r 元素添加下划线格式（w:u val=single）"""
        rPr = run_elem.find(W + 'rPr')
        if rPr is None:
            rPr = etree.SubElement(run_elem, W + 'rPr')
        u = rPr.find(W + 'u')
        if u is None:
            u = etree.SubElement(rPr, W + 'u')
        u.set(W + 'val', 'single')

    def _replace_party_table(self,table_elem,pa,pb):
        """填充甲乙双方表格，并给乙方信息添加下划线格式"""
        cells=list(table_elem.iter(W + 'tc'))
        if len(cells)<2: return

        # ── 甲方：按配置覆盖（保留原格式）──
        cell_a = cells[0]
        ct_a = "".join((t.text or "") for t in cell_a.iter(W + 't'))
        if pa.get("company_name"):
            m = re.search(r'甲\s+方(\S+)', ct_a)
            if m and m.group(1) != pa["company_name"]:
                _replace_text_in_xml(cell_a, m.group(1), pa["company_name"])
        if pa.get("legal_rep"):
            m = re.search(r'法定代表人：(\S+)', ct_a)
            if m and m.group(1) != pa["legal_rep"]:
                _replace_text_in_xml(cell_a, m.group(1), pa["legal_rep"])

        # ── 乙方：直接操作 w:r 元素，给填入的值加下划线 ──
        cell_b = cells[1]
        label_fields = [
            (r'乙\s+方：', "full_name"),
            (r'法定代表人：', "legal_rep"),
            (r'地\s+址：', "address"),
            (r'联\s*系\s*人：', "contact"),
            (r'授权代表：', "auth_rep"),
            (r'电\s+话：', "phone"),
            (r'传\s+真：', "fax"),
        ]

        # 收集 cell_b 中所有 run
        all_runs = list(cell_b.iter(W + 'r'))

        # 简化策略：直接替换标签后的空格文本，然后给对应 run 加下划线
        for label_pat, field_key in label_fields:
            value = pb.get(field_key, "")
            if not value: continue

            ct_b = "".join((t.text or "") for t in cell_b.iter(W + 't'))
            m_space = re.search(label_pat + r'(\s{1,})', ct_b)
            if m_space:
                old_text = m_space.group(0)
                new_text = m_space.group(0)[:len(m_space.group(0))-len(m_space.group(1))] + value + m_space.group(1)
                _replace_text_in_xml(cell_b, old_text, new_text)

                # 找到包含 value 的 run，加下划线
                for r in all_runs:
                    rt = "".join((t.text or "") for t in r.iter(W + 't'))
                    if value in rt:
                        self._add_underline_to_run(r)
                        break

    def _fill_underlined_placeholders(self, para, material_name, contract_date):
        """直接操作 w:r 元素，将带下划线的空格占位符替换为物料名称和签订日期。
        模板中「购得」和「产品」之间、以及日期位置的空格已经带有下划线，
        我们只需将这些 w:r 中的空格文字替换为实际内容即可保留下划线。"""
        runs = list(para.iter(W + 'r'))
        # 建立每个 run 的索引信息
        run_info = []
        for i, r in enumerate(runs):
            rt = ''.join((t.text or '') for t in r.iter(W + 't'))
            rPr = r.find(W + 'rPr')
            has_u = rPr is not None and rPr.find(W + 'u') is not None
            run_info.append((i, r, rt, has_u))

        def _clear_run_spaces(run_elem):
            """清空 run 中所有 w:t 元素"""
            for wt in run_elem.iter(W + 't'):
                wt.text = ''

        def _set_first_wt(run_elem, text):
            """设置第一个 w:t 元素的内容"""
            wt_list = list(run_elem.iter(W + 't'))
            if wt_list:
                wt_list[0].text = text

        # ── 填充物料名称（「购得」和「产品」之间的下划线空格）──
        gd_idx = cp_idx = None
        for i, (idx, r, rt, has_u) in enumerate(run_info):
            if '购得' in rt: gd_idx = i
            if gd_idx is not None and cp_idx is None and '产品' in rt: cp_idx = i
        if gd_idx is not None and cp_idx is not None and material_name:
            prod_runs = []
            for i in range(gd_idx + 1, cp_idx):
                if run_info[i][3]:  # has underline
                    prod_runs.append(i)
            if prod_runs:
                for i in prod_runs:
                    _clear_run_spaces(run_info[i][1])
                _set_first_wt(run_info[prod_runs[0]][1], material_name)

        # ── 填充签订日期（年月日分别填入对应下划线空格）──
        date_m = re.match(r'(\d{4})年(\d{2})月(\d{2})日', contract_date) if contract_date else None
        if date_m:
            year, month, day = date_m.groups()

            # 年：between 「于」 and 「年」
            yu_idx = nian_idx = None
            for i, (idx, r, rt, has_u) in enumerate(run_info):
                if '于' in rt: yu_idx = i
                if yu_idx is not None and rt.strip() == '年': nian_idx = i; break
            if yu_idx is not None and nian_idx is not None:
                yr_runs = [i for i in range(yu_idx + 1, nian_idx) if run_info[i][3]]
                for i in yr_runs: _clear_run_spaces(run_info[i][1])
                if yr_runs: _set_first_wt(run_info[yr_runs[0]][1], year)

            # 月：between 「年」 and 「月」
            yue_idx = None
            for i, (idx, r, rt, has_u) in enumerate(run_info):
                if i > nian_idx and rt.strip() == '月': yue_idx = i; break
            if yue_idx is not None:
                mo_runs = [i for i in range(nian_idx + 1, yue_idx) if run_info[i][3]]
                for i in mo_runs: _clear_run_spaces(run_info[i][1])
                if mo_runs: _set_first_wt(run_info[mo_runs[0]][1], month)

            # 日：between 「月」 and 「日」
            ri_idx = None
            for i, (idx, r, rt, has_u) in enumerate(run_info):
                if i > yue_idx and '日' in rt: ri_idx = i; break
            if ri_idx is not None:
                day_runs = [i for i in range(yue_idx + 1, ri_idx) if run_info[i][3]]
                for i in day_runs: _clear_run_spaces(run_info[i][1])
                if day_runs: _set_first_wt(run_info[day_runs[0]][1], day)

    def _replace_product_table(self, table_elem, products):
        """填充产品明细表格"""
        rows=list(table_elem.iter(W + 'tr'))
        if len(rows)<3: return
        template_row=rows[1]; total_row=rows[2]

        total_amount=0.0
        for p in products:
            try:
                q=float(p.get("qty",0)); pr=float(p.get("price",0))
                total_amount+=q*pr
            except: pass

        self._fill_product_row(template_row,products[0])
        for i in range(1,len(products)):
            nr=self._clone_row(template_row)
            self._fill_product_row(nr,products[i])
            parent=total_row.getparent()
            idx=list(parent).index(total_row)
            parent.insert(idx,nr)
        self._update_total_row(total_row,total_amount)

    def _clone_row(self,row_elem):
        return etree.fromstring(etree.tostring(row_elem))

    def _fill_product_row(self,row_elem,product):
        cells=list(row_elem.iter(W + 'tc'))
        try:
            q=float(product.get("qty",0)); pr=float(product.get("price",0))
            amt=f"{q*pr:.2f}"
        except: amt="0.00"
        fields=[
            product.get("name",""),product.get("item_no",""),
            product.get("material_struct",""),
            product.get("size",""),product.get("unit",""),
            product.get("qty",""),product.get("price",""),
            amt,product.get("note",""),
        ]
        for i,cell in enumerate(cells):
            if i<len(fields):
                text_val=str(fields[i]) if fields[i] else ""
                wt_list=list(cell.iter(W + 't'))
                if wt_list:
                    wt_list[0].text=text_val
                    for wt in wt_list[1:]: wt.text=""
                else:
                    # 模板单元格没有 w:t 元素（如"材质结构""备注"默认空列）
                    p_list=list(cell.iter(W + 'p'))
                    if p_list:
                        r=etree.SubElement(p_list[0],W + 'r')
                        t=etree.SubElement(r,W + 't')
                        t.text=text_val

    def _update_total_row(self,total_row,total_amount):
        rmb=num_to_rmb_upper(total_amount)
        amt_str=f"{total_amount:.2f}"
        amt_int_str=f"{total_amount:.0f}"
        for cell in total_row.iter(W + 'tc'):
            ct="".join((t.text or "") for t in cell.iter(W + 't'))
            # 匹配含数字的单元格：替换模板中的旧数字为实际金额
            num_m=re.search(r'(\d+(?:\.\d+)?)',ct)
            if num_m:
                old_num=num_m.group(1)
                # 判断是整数还是小数
                if '.' in old_num:
                    _replace_text_in_xml(cell,old_num,amt_str)
                else:
                    # 先尝试替换小数形式，再尝试整数
                    old_dec=f"{float(old_num):.2f}"
                    if old_dec in ct:
                        _replace_text_in_xml(cell,old_dec,amt_str)
                    else:
                        _replace_text_in_xml(cell,old_num,amt_int_str)
                    # 也处理可能存在的 .00 形式
                    if old_num+".00" in ct:
                        _replace_text_in_xml(cell,old_num+".00",amt_str)
            # 匹配含中文大写金额的单元格：替换为实际大写
            rmb_m=re.search(r'[壹贰叁肆伍陆柒捌玖][壹贰叁肆伍陆柒捌玖拾佰仟万亿零元整角分]*',ct)
            if rmb_m:
                _replace_text_in_xml(cell,rmb_m.group(0),rmb)

    # ── 重新打包 ──
    def _repack_docx(self,unpack_dir,save_path):
        with zipfile.ZipFile(save_path,"w",zipfile.ZIP_DEFLATED) as zf:
            for root_dir,_,files in os.walk(unpack_dir):
                for file in files:
                    full=os.path.join(root_dir,file)
                    arcname=os.path.relpath(full,unpack_dir).replace(os.sep,"/")
                    zf.write(full,arcname)
