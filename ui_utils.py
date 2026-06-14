#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI 工具类：无滚动条的滚动容器
"""

import tkinter as tk
import customtkinter as ctk


class WheelScrollFrame(ctk.CTkFrame):
    """
    无可见滚动条的滚动容器，支持鼠标滚轮。
    用于替换 CTkScrollableFrame，隐藏滚动条并通过鼠标滚轮控制滚动。
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # Canvas + 隐藏的滚动条
        # tk.Canvas 不支持 "transparent" 作为 bg，需转换为实际颜色
        fg = kwargs.get("fg_color", None)
        canvas_bg = None  # None = 使用 Tkinter 默认背景
        if fg is not None:
            try:
                color = self._apply_appearance_mode(fg)
                if color != "transparent":
                    canvas_bg = color
            except Exception:
                pass
        if canvas_bg:
            self._canvas = tk.Canvas(self, highlightthickness=0, bg=canvas_bg)
        else:
            self._canvas = tk.Canvas(self, highlightthickness=0)
        self._scrollbar = ctk.CTkScrollbar(self, command=self._canvas.yview)
        # 完全隐藏滚动条
        self._scrollbar.configure(width=0)
        self._scrollbar.pack_forget()  # 不放置滚动条

        self._inner = ctk.CTkFrame(self._canvas, **{k: v for k, v in kwargs.items()
                                                      if k in ("fg_color", "corner_radius")})
        self._window_id = self._canvas.create_window((0, 0), window=self._inner, anchor="nw")

        self._canvas.pack(side="left", fill="both", expand=True)

        # 配置滚动区域
        self._inner.bind("<Configure>", self._on_frame_configure)
        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        # 鼠标滚轮绑定（Windows: <MouseWheel>, Linux: <Button-4/5>）
        for widget in (self, self._canvas, self._inner):
            widget.bind("<MouseWheel>", self._on_mousewheel, "+")
            widget.bind("<Button-4>", lambda e: self._canvas.yview_scroll(-1, "units"), "+")
            widget.bind("<Button-5>", lambda e: self._canvas.yview_scroll(1, "units"), "+")

    def _on_frame_configure(self, event=None):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        # 让 inner frame 宽度跟随 canvas
        self._canvas.itemconfig(self._window_id, width=self._canvas.winfo_width())

    def _on_mousewheel(self, event):
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    @property
    def inner_frame(self):
        """返回内部容器，供外部直接添加子组件"""
        return self._inner

    def configure(self, **kwargs):
        # 同步更新 inner frame 的颜色（如果需要）
        if "fg_color" in kwargs:
            self._inner.configure(fg_color=kwargs["fg_color"])
        super().configure(**kwargs)

    def pack(self, **kwargs):
        super().pack(**kwargs)
        # 延迟配置 canvas 宽度
        self._canvas.after(50, self._update_canvas_width)

    def _update_canvas_width(self):
        self._canvas.itemconfig(self._window_id, width=self._canvas.winfo_width())


class FilterBar(ctk.CTkFrame):
    """统一的快速筛选栏组件。"""
    def __init__(self, parent, C, placeholder='搜索关键词...',
                 show_date=True, show_status=True, status_options=None,
                 on_filter=None, on_reset=None):
        super().__init__(parent, fg_color=C['card'], corner_radius=C['radius_card'],
                         border_width=1, border_color=C['border'])
        self.C = C
        self.on_filter = on_filter
        self.on_reset = on_reset

        inner = ctk.CTkFrame(self, fg_color='transparent')
        inner.pack(fill='x', padx=12, pady=8)

        # 关键词搜索
        ctk.CTkLabel(inner, text='🔍', font=ctk.CTkFont(size=14),
                     text_color=C['text_secondary'], width=24).pack(side='left', padx=(0, 4))
        self.keyword_var = tk.StringVar()
        keyword_entry = ctk.CTkEntry(
            inner, textvariable=self.keyword_var,
            placeholder_text=placeholder,
            font=ctk.CTkFont(size=13), width=180, height=32,
            border_width=1, border_color=C['border'],
        )
        keyword_entry.pack(side='left', padx=(0, 8))
        keyword_entry.bind('<Return>', lambda e: self._do_filter())

        # 日期范围
        if show_date:
            ctk.CTkLabel(inner, text='从', font=ctk.CTkFont(size=12),
                         text_color=C['text_secondary']).pack(side='left', padx=(0, 2))
            self.date_from_var = tk.StringVar()
            ctk.CTkEntry(inner, textvariable=self.date_from_var,
                          placeholder_text='YYYY-MM-DD',
                          font=ctk.CTkFont(size=12), width=110, height=32,
                          border_width=1, border_color=C['border']).pack(side='left', padx=(0, 4))
            ctk.CTkLabel(inner, text='至', font=ctk.CTkFont(size=12),
                         text_color=C['text_secondary']).pack(side='left', padx=(0, 2))
            self.date_to_var = tk.StringVar()
            ctk.CTkEntry(inner, textvariable=self.date_to_var,
                          placeholder_text='YYYY-MM-DD',
                          font=ctk.CTkFont(size=12), width=110, height=32,
                          border_width=1, border_color=C['border']).pack(side='left', padx=(0, 8))
        else:
            self.date_from_var = None
            self.date_to_var = None

        # 状态
        if show_status and status_options:
            ctk.CTkLabel(inner, text='状态', font=ctk.CTkFont(size=12),
                         text_color=C['text_secondary']).pack(side='left', padx=(0, 4))
            self.status_var = tk.StringVar(value='全部')
            status_menu = ctk.CTkOptionMenu(
                inner, variable=self.status_var,
                values=['全部'] + list(status_options),
                font=ctk.CTkFont(size=12), width=120, height=32,
                fg_color=C['card'], button_color=C['primary'],
                dropdown_fg_color=C['card'], text_color=C['text'],
            )
            status_menu.pack(side='left', padx=(0, 8))
        else:
            self.status_var = None

        # 按钮
        ctk.CTkButton(inner, text='筛选', width=64, height=32,
                       fg_color=C['primary'], hover_color=C['primary_hover'],
                       font=ctk.CTkFont(size=13),
                       command=self._do_filter, corner_radius=20).pack(side='left', padx=(0, 4))
        ctk.CTkButton(inner, text='重置', width=64, height=32,
                       fg_color='transparent', hover_color=C['hover'],
                       font=ctk.CTkFont(size=13), text_color=C['text_secondary'],
                       border_width=1, border_color=C['border'],
                       command=self._do_reset, corner_radius=20).pack(side='left')

    def _do_filter(self):
        params = {'keyword': self.keyword_var.get().strip()}
        if self.date_from_var:
            params['date_from'] = self.date_from_var.get().strip()
            params['date_to'] = self.date_to_var.get().strip()
        if self.status_var:
            params['status'] = self.status_var.get()
        if self.on_filter:
            self.on_filter(params)

    def _do_reset(self):
        self.keyword_var.set('')
        if self.date_from_var:
            self.date_from_var.set('')
            self.date_to_var.set('')
        if self.status_var:
            self.status_var.set('全部')
        if self.on_reset:
            self.on_reset()

    def get_params(self):
        params = {'keyword': self.keyword_var.get().strip()}
        if self.date_from_var:
            params['date_from'] = self.date_from_var.get().strip()
            params['date_to'] = self.date_to_var.get().strip()
        if self.status_var:
            params['status'] = self.status_var.get()
        return params


class FormValidator:
    """表单前端校验工具"""
    ERROR_COLOR = '#D4917A'

    @staticmethod
    def validate_required(widget, value, field_name):
        if not value or str(value).strip() == '':
            FormValidator._mark_error(widget, field_name + '不能为空')
            return False
        FormValidator._clear_error(widget)
        return True

    @staticmethod
    def validate_numeric(widget, value, field_name, min_val=None, max_val=None):
        try:
            num = float(value)
            if min_val is not None and num < min_val:
                FormValidator._mark_error(widget, field_name + '不能小于' + str(min_val))
                return False
            if max_val is not None and num > max_val:
                FormValidator._mark_error(widget, field_name + '不能大于' + str(max_val))
                return False
            FormValidator._clear_error(widget)
            return True
        except (ValueError, TypeError):
            FormValidator._mark_error(widget, field_name + '必须是数字')
            return False

    @staticmethod
    def validate_date(widget, value, field_name):
        import re
        if not value or str(value).strip() == '':
            FormValidator._clear_error(widget)
            return True
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', str(value).strip()):
            FormValidator._mark_error(widget, field_name + '格式错误，应为YYYY-MM-DD')
            return False
        FormValidator._clear_error(widget)
        return True

    @staticmethod
    def _mark_error(widget, msg=''):
        try:
            widget.configure(border_color='#D4917A')
        except Exception:
            pass

    @staticmethod
    def _clear_error(widget):
        try:
            widget.configure(border_color='#C0B5A8')
        except Exception:
            pass
