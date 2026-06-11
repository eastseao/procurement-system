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
