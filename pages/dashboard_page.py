#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""仪表盘页面 v1.5 - 圆角卡片 + 同类内容合并"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime

# 莫兰迪暖色卡
CARD_COLORS = [
    "#C1816D",  # 陶土色
    "#8FA882",  # 鼠尾草绿
    "#C9A96E",  # 麦色
    "#B56A6A",  # 暗玫瑰
    "#7BA5B5",  # 灰蓝
]


class DashboardPage(ctk.CTkFrame):
    """仪表盘主页面"""

    def __init__(self, parent, db, C):
        super().__init__(parent, fg_color=C["bg"], corner_radius=0)
        self.db = db
        self.C = C
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        # 标题
        header = ctk.CTkFrame(self, fg_color="transparent", height=56)
        header.pack(fill="x", padx=24, pady=(16, 8))
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="📊  仪表盘",
            font=ctk.CTkFont(family="Microsoft YaHei", size=20, weight="bold"),
            text_color=self.C["text"],
        ).pack(side="left", pady=12)

        # 更新时间
        self.time_label = ctk.CTkLabel(
            header, text="",
            font=ctk.CTkFont(size=12),
            text_color=self.C.get("text_secondary", "#8B7355"),
        )
        self.time_label.pack(side="right", pady=12)

        # 卡片区域
        scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        scroll_frame.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        # ── 第一行：3张卡片 ──
        row1 = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 14))

        # 物料下单（处理中 + 已完成 合并）
        self.card_packaging = self._create_dual_card(
            row1, "📦  物料下单",
            [("处理中", "0", "个"), ("已完成", "0", "个")],
            CARD_COLORS[0],
        )
        self.card_packaging.pack(side="left", fill="x", expand=True, padx=(0, 7))

        # 催款记录（单值）
        self.card_collection = self._create_card(
            row1, "💰  催款记录", "0", "条记录",
            CARD_COLORS[1],
        )
        self.card_collection.pack(side="left", fill="x", expand=True, padx=7)

        # 采购垫付（笔数 + 待报销 合并）
        self.card_purchase = self._create_dual_card(
            row1, "💳  采购垫付",
            [("笔数", "0", "笔"), ("待报销", "¥0", "元")],
            CARD_COLORS[2],
        )
        self.card_purchase.pack(side="left", fill="x", expand=True, padx=(7, 0))

        # ── 第二行：2张卡片 ──
        row2 = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 14))

        # 差旅报销（行程数 + 待报销 合并）
        self.card_travel = self._create_dual_card(
            row2, "✈️  差旅报销",
            [("行程数", "0", "个"), ("待报销", "¥0", "元")],
            CARD_COLORS[3],
        )
        self.card_travel.pack(side="left", fill="x", expand=True, padx=(0, 7))

        # 备忘录（单值）
        self.card_memo = self._create_card(
            row2, "📝  备忘录", "0", "条待处理",
            CARD_COLORS[4],
        )
        self.card_memo.pack(side="left", fill="x", expand=True, padx=(7, 0))

    # ── 单值卡片 ──────────────────────────────────────
    def _create_card(self, parent, title, value, unit, color):
        """创建一个单值统计卡片（圆角矩形）"""
        card = ctk.CTkFrame(parent, fg_color=color, corner_radius=18)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=18, pady=(16, 16))

        ctk.CTkLabel(
            content, text=title,
            font=ctk.CTkFont(family="Microsoft YaHei", size=14, weight="bold"),
            text_color="#FFFFFF",
        ).pack(anchor="w")

        value_label = ctk.CTkLabel(
            content, text=value,
            font=ctk.CTkFont(family="Microsoft YaHei", size=32, weight="bold"),
            text_color="#FFFFFF",
        )
        value_label.pack(anchor="w", pady=(8, 0))

        ctk.CTkLabel(
            content, text=unit,
            font=ctk.CTkFont(size=12),
            text_color="#F0E8E0",
        ).pack(anchor="w", pady=(2, 0))

        setattr(card, "value_label_0", value_label)
        return card

    # ── 双值合并卡片 ──────────────────────────────────
    def _create_dual_card(self, parent, title, items, color):
        """
        创建一个双值合并卡片
        items = [("子标题1", "值1", "单位1"), ("子标题2", "值2", "单位2")]
        """
        card = ctk.CTkFrame(parent, fg_color=color, corner_radius=18)

        header_frame = ctk.CTkFrame(card, fg_color="transparent")
        header_frame.pack(fill="x", padx=18, pady=(16, 12))

        ctk.CTkLabel(
            header_frame, text=title,
            font=ctk.CTkFont(family="Microsoft YaHei", size=14, weight="bold"),
            text_color="#FFFFFF",
        ).pack(anchor="w")

        # 两个值并排
        values_frame = ctk.CTkFrame(card, fg_color="transparent")
        values_frame.pack(fill="x", padx=18, pady=(0, 16))

        value_labels = []
        for idx, (subtitle, value, unit) in enumerate(items):
            col_frame = ctk.CTkFrame(values_frame, fg_color="transparent")
            col_frame.pack(side="left", fill="x", expand=True, padx=(0, 12) if idx == 0 else 0)

            value_label = ctk.CTkLabel(
                col_frame, text=value,
                font=ctk.CTkFont(family="Microsoft YaHei", size=28, weight="bold"),
                text_color="#FFFFFF",
            )
            value_label.pack(anchor="w")

            ctk.CTkLabel(
                col_frame, text=f"{subtitle}  {unit}",
                font=ctk.CTkFont(size=11),
                text_color="#F0E8E0",
            ).pack(anchor="w", pady=(2, 0))

            setattr(card, f"value_label_{idx}", value_label)

        return card

    def _load_data(self):
        """加载统计数据"""
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            self.time_label.configure(text=f"更新时间：{now}")

            # 物料下单 — 处理中 + 已完成
            packaging = self.db.get_packagings(archived=0)
            packaging_done = self.db.get_packagings(archived=1)
            self._update_card_value(self.card_packaging, 0, str(len(packaging)))
            self._update_card_value(self.card_packaging, 1, str(len(packaging_done)))

            # 催款记录
            collections = self.db.get_collections()
            self._update_card_value(self.card_collection, 0, str(len(collections)))

            # 采购垫付 — 笔数 + 待报销金额
            purchases = self.db.get_purchases(archived=0)
            purchase_amount = sum(p.get("total", 0) for p in purchases if p.get("reimbursement_status") != "已报销")
            self._update_card_value(self.card_purchase, 0, str(len(purchases)))
            self._update_card_value(self.card_purchase, 1, f"¥{purchase_amount:.2f}")

            # 差旅报销 — 行程数 + 待报销金额
            travels = self.db.get_travels(archived=0)
            travel_amount = sum(t.get("total", 0) for t in travels if t.get("reimbursement_status") != "已报销")
            self._update_card_value(self.card_travel, 0, str(len(travels)))
            self._update_card_value(self.card_travel, 1, f"¥{travel_amount:.2f}")

            # 备忘录
            memos = self.db.get_memos(status="待处理")
            self._update_card_value(self.card_memo, 0, str(len(memos)))

        except Exception as e:
            print(f"加载统计数据失败: {e}")

    def _update_card_value(self, card, idx, value):
        """更新卡片中指定索引的数值"""
        attr = f"value_label_{idx}"
        if hasattr(card, attr):
            getattr(card, attr).configure(text=value)

    def refresh(self):
        """刷新数据"""
        self._load_data()
