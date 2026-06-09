#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""仪表盘页面 V1.8.3 - 重新设计，更美观大气"""

import customtkinter as ctk
import tkinter as tk
from datetime import datetime
import json
import urllib.request
import threading

# 各模块莫兰迪色
MODULE_COLORS = {
    "packaging":  "#C1816D",   # 陶土色 - 物料下单
    "collection": "#8FA882",   # 鼠尾草绿 - 催款记录
    "purchase":   "#C9A96E",   # 麦色 - 采购垫付
    "travel":     "#B56A6A",   # 暗玫瑰 - 差旅报销
    "memo":       "#7BA5B5",   # 灰蓝 - 备忘录
}


class DashboardPage(ctk.CTkFrame):
    """仪表盘主页面 - V1.8.3 优化版"""

    def __init__(self, parent, db, C):
        super().__init__(parent, fg_color=C["bg"], corner_radius=0)
        self.db = db
        self.C = C
        self._value_labels = {}  # key -> label widget
        self._build_ui()
        self._load_data()
        self._fetch_weather()

    # ── UI构建 ────────────────────────────────────
    def _build_ui(self):
        # ── 顶部概览横幅 ──────────────────────────────
        banner = ctk.CTkFrame(
            self, fg_color=self.C["primary"], corner_radius=16,
        )
        banner.pack(fill="x", padx=24, pady=(16, 12))

        banner_inner = ctk.CTkFrame(banner, fg_color="transparent")
        banner_inner.pack(fill="x", padx=28, pady=(22, 22))

        # 左侧：欢迎语 + 日期
        left_col = ctk.CTkFrame(banner_inner, fg_color="transparent")
        left_col.pack(side="left", fill="y")

        ctk.CTkLabel(
            left_col,
            text="仪表盘",
            font=ctk.CTkFont(family="Microsoft YaHei", size=24, weight="bold"),
            text_color="white",
        ).pack(anchor="w")

        ctk.CTkLabel(
            left_col,
            text="采购管理数据总览",
            font=ctk.CTkFont(family="Microsoft YaHei", size=13),
            text_color="#F5F0EB",
        ).pack(anchor="w", pady=(4, 0))

        # 右侧：天气预报 + 更新时间
        right_col = ctk.CTkFrame(banner_inner, fg_color="transparent")
        right_col.pack(side="right", fill="y")

        # 天气 + 时间 横向排列
        wt_frame = ctk.CTkFrame(right_col, fg_color="transparent")
        wt_frame.pack(side="right", pady=(10, 0))

        self.weather_label = ctk.CTkLabel(
            wt_frame,
            text="🌤 天气获取中...",
            font=ctk.CTkFont(family="Microsoft YaHei", size=12),
            text_color="#F5F0EB",
        )
        self.weather_label.pack(side="left", padx=(0, 12))

        self.time_label = ctk.CTkLabel(
            wt_frame,
            text="",
            font=ctk.CTkFont(family="Microsoft YaHei", size=12),
            text_color="#F5F0EB",
        )
        self.time_label.pack(side="left")

        # ── 主卡片网格 ──────────────────────────────
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        # 第一行：3 张卡片
        row1 = ctk.CTkFrame(content, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 12))
        row1.grid_columnconfigure((0, 1, 2), weight=1)

        # 物料下单
        self.card_packaging = self._make_dual_card(
            row1, "物料下单", [
                ("处理中", "0", "条"),
                ("已完成", "0", "条"),
            ],
            MODULE_COLORS["packaging"],
            col=0, col_pad=(0, 6),
        )

        # 催款记录
        self.card_collection = self._make_single_card(
            row1, "催款记录", "0", "条记录",
            MODULE_COLORS["collection"],
            col=1, col_pad=6,
        )

        # 采购垫付
        self.card_purchase = self._make_dual_card(
            row1, "采购垫付", [
                ("总笔数", "0", "笔"),
                ("待报销", "¥0", ""),
            ],
            MODULE_COLORS["purchase"],
            col=2, col_pad=(6, 0),
        )

        # 第二行：2 张卡片
        row2 = ctk.CTkFrame(content, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 12))
        row2.grid_columnconfigure((0, 1), weight=1)

        # 差旅报销
        self.card_travel = self._make_dual_card(
            row2, "差旅报销", [
                ("行程数", "0", "个"),
                ("待报销", "¥0", ""),
            ],
            MODULE_COLORS["travel"],
            col=0, col_pad=(0, 6),
        )

        # 备忘录
        self.card_memo = self._make_single_card(
            row2, "备忘录", "0", "条待处理",
            MODULE_COLORS["memo"],
            col=1, col_pad=(6, 0),
        )

        # ── 底部快捷入口提示 ──
        hints = ctk.CTkFrame(content, fg_color=self.C["card"], corner_radius=12)
        hints.pack(fill="x", pady=(0, 8))

        hint_items = [
            ("物料下单", "快速记录采购订单，支持导入模板"),
            ("催款记录", "跟踪供应商催款状态，及时跟进"),
            ("采购垫付", "记录个人垫付费用，一键报销"),
        ]
        for idx, (hint_title, hint_desc) in enumerate(hint_items):
            hint_frame = ctk.CTkFrame(hints, fg_color="transparent")
            hint_frame.pack(side="left", fill="x", expand=True, padx=18, pady=(14, 14))

            ctk.CTkLabel(
                hint_frame, text=f"💡 {hint_title}",
                font=ctk.CTkFont(family="Microsoft YaHei", size=13, weight="bold"),
                text_color=self.C["text"],
            ).pack(anchor="w")

            ctk.CTkLabel(
                hint_frame, text=hint_desc,
                font=ctk.CTkFont(family="Microsoft YaHei", size=11),
                text_color=self.C["text_secondary"],
            ).pack(anchor="w", pady=(2, 0))

    # ── 单值卡片 ──────────────────────────────────
    def _make_single_card(self, parent, title, value, unit, color, col, col_pad):
        card = ctk.CTkFrame(
            parent, fg_color=color, corner_radius=18,
        )
        card.grid(row=0, column=col, sticky="nsew", padx=col_pad if isinstance(col_pad, tuple) else (col_pad, col_pad))

        # 内边距容器
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=22, pady=(20, 22))

        ctk.CTkLabel(
            inner, text=title,
            font=ctk.CTkFont(family="Microsoft YaHei", size=14, weight="bold"),
            text_color="#FFFFFF",
        ).pack(anchor="w")

        val_label = ctk.CTkLabel(
            inner, text=value,
            font=ctk.CTkFont(family="Microsoft YaHei", size=38, weight="bold"),
            text_color="#FFFFFF",
        )
        val_label.pack(anchor="w", pady=(10, 0))

        ctk.CTkLabel(
            inner, text=unit,
            font=ctk.CTkFont(family="Microsoft YaHei", size=12),
            text_color="#F0E8E0",
        ).pack(anchor="w", pady=(4, 0))

        self._value_labels[title] = val_label
        return card

    # ── 双值卡片 ──────────────────────────────────
    def _make_dual_card(self, parent, title, items, color, col, col_pad):
        card = ctk.CTkFrame(
            parent, fg_color=color, corner_radius=18,
        )
        card.grid(row=0, column=col, sticky="nsew", padx=col_pad if isinstance(col_pad, tuple) else (col_pad, col_pad))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=22, pady=(20, 22))

        ctk.CTkLabel(
            inner, text=title,
            font=ctk.CTkFont(family="Microsoft YaHei", size=14, weight="bold"),
            text_color="#FFFFFF",
        ).pack(anchor="w")

        # 两个值并排
        vals_row = ctk.CTkFrame(inner, fg_color="transparent")
        vals_row.pack(fill="x", pady=(14, 0))

        for idx, (sub, val, unit) in enumerate(items):
            col_frame = ctk.CTkFrame(vals_row, fg_color="transparent")
            col_frame.pack(side="left", fill="x", expand=True)

            val_label = ctk.CTkLabel(
                col_frame, text=val,
                font=ctk.CTkFont(family="Microsoft YaHei", size=32, weight="bold"),
                text_color="#FFFFFF",
            )
            val_label.pack(anchor="w")

            sub_label = ctk.CTkLabel(
                col_frame, text=f"{sub}  {unit}",
                font=ctk.CTkFont(family="Microsoft YaHei", size=11),
                text_color="#F0E8E0",
            )
            sub_label.pack(anchor="w", pady=(2, 0))

            self._value_labels[f"{title}_{sub}"] = val_label

        return card

    # ── 数据加载 ──────────────────────────────────
    def _load_data(self):
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            self.time_label.configure(text=f"更新时间：{now}")

            # 物料下单
            packaging = self.db.get_packagings(archived=0)
            packaging_done = self.db.get_packagings(archived=1)
            self._set_value("物料下单_处理中", str(len(packaging)))
            self._set_value("物料下单_已完成", str(len(packaging_done)))

            # 催款记录
            collections = self.db.get_collections()
            self._set_value("催款记录", str(len(collections)))

            # 采购垫付
            purchases = self.db.get_purchases(archived=0)
            purchase_amount = sum(p.get("total", 0) for p in purchases if p.get("reimbursement_status") != "已报销")
            self._set_value("采购垫付_总笔数", str(len(purchases)))
            self._set_value("采购垫付_待报销", f"¥{purchase_amount:.0f}")

            # 差旅报销
            travels = self.db.get_travels(archived=0)
            travel_amount = sum(t.get("total", 0) for t in travels if t.get("reimbursement_status") != "已报销")
            self._set_value("差旅报销_行程数", str(len(travels)))
            self._set_value("差旅报销_待报销", f"¥{travel_amount:.0f}")

            # 备忘录
            memos = self.db.get_memos(status="待处理")
            self._set_value("备忘录", str(len(memos)))

        except Exception as e:
            print(f"加载统计数据失败: {e}")

    def _set_value(self, key, value):
        """更新标签值"""
        if key in self._value_labels:
            self._value_labels[key].configure(text=value)


    # ── 天气预报 ──────────────────────────────
    def _fetch_weather(self):
        """后台获取 IP 所在地天气预报（wttr.in，无需 API key）"""
        def _worker():
            try:
                url = "https://wttr.in/?format=j1"
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    current = data["current_condition"][0]
                    area = data["nearest_area"][0]
                    city = area.get("areaName", [{"value": "未知"}])[0]["value"]
                    temp = current.get("temp_C", "N/A")
                    desc = current.get("weatherDesc", [{"value": ""}])[0]["value"]
                    code = current.get("weatherCode", "113")
                    emoji = self._weather_emoji(code)
                    weather_text = f"{emoji} {city} {temp}°C {desc}"
                    self.after(0, lambda t=weather_text: self.weather_label.configure(text=t))
            except Exception:
                self.after(0, lambda: self.weather_label.configure(text="🌤 天气获取失败"))

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def _weather_emoji(self, code):
        """根据 weatherCode 返回 emoji"""
        code = int(code) if isinstance(code, str) else code
        if code in (113, 116):
            return "☀️"
        if code in (116, 119, 122):
            return "☁️"
        if code in (176, 263, 266, 293, 296, 299, 302, 305, 308, 311, 314, 317, 320, 323, 326, 329, 332, 335, 338):
            return "🌧️"
        if code in (200, 386, 389, 392, 395):
            return "⛈️"
        return "🌤️"

    def refresh(self):
        """刷新数据"""
        self._load_data()
