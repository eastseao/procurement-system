#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""同仁堂集团介绍页面 - 内置版"""

import tkinter as tk
import customtkinter as ctk


class GroupIntroPage(ctk.CTkFrame):
    def __init__(self, parent, db, colors):
        super().__init__(parent, fg_color=colors["bg"], corner_radius=0)
        self.C = colors
        self._build()

    def _build(self):
        # ── 标题栏 ─────────────────────────────
        header = ctk.CTkFrame(self, fg_color=self.C["card"], corner_radius=0, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="北京同仁堂集团组织架构",
            font=ctk.CTkFont(family="Microsoft YaHei", size=20, weight="bold"),
            text_color=self.C["text"],
        ).pack(side="left", padx=24, pady=16)

        # ── 简介卡片 ──────────────────────────
        intro_card = ctk.CTkFrame(self, fg_color=self.C["primary_light"], corner_radius=12)
        intro_card.pack(fill="x", padx=24, pady=(16, 8))

        intro_text = (
            "北京同仁堂创建于清康熙八年（1669年），历经三百余年传承，"
            "是中国中医药行业著名的老字号。同仁堂集团以制药工业为核心，"
            "拥有健康养生、医疗养老、商业零售、国际药业等多个业务板块，"
            "形成了\u201c制药+\u201d大健康产业格局。"
        )
        ctk.CTkLabel(
            intro_card, text=intro_text,
            font=ctk.CTkFont(family="Microsoft YaHei", size=13),
            text_color=self.C["text"],
            wraplength=850,
            justify="left",
        ).pack(anchor="w", padx=20, pady=(14, 14))

        # ── 架构概览 ──────────────────────────
        groups = [
            ("🏛️", "同仁堂股份集团", "上市公司 · 核心制药业务", "#C1816D"),
            ("🏭", "同仁堂科技集团", "药品制造 · 配方颗粒 · 中药大健康", "#8FA882"),
            ("🌍", "同仁堂国药集团", "海外业务 · 中医药国际化", "#A8828F"),
            ("💊", "同仁堂健康集团", "健康食品 · 保健品 · 健康管理", "#C9A96E"),
            ("🏪", "同仁堂商业集团", "零售连锁 · 药店终端", "#B56A6A"),
            ("🌿", "同仁堂药材参茸集团", "中药材 · 参茸贵细 · 饮片", "#6A8FB5"),
            ("🏥", "同仁堂医养集团", "医疗 · 养老 · 健康服务", "#8F6AB5"),
            ("⚗️", "同仁堂制药公司", "中成药生产 · 质量管理", "#B56A8F"),
            ("🏢", "集团直属企业", "总部直属 · 综合管理", "#5D4E37"),
        ]

        # ── 滚动区域 ──────────────────────────
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        for icon, name, desc, color in groups:
            card = ctk.CTkFrame(scroll, fg_color=self.C["card"], corner_radius=10)
            card.pack(fill="x", pady=(0, 8))

            # 左侧图标
            icon_frame = ctk.CTkFrame(card, fg_color=color, corner_radius=10, width=56, height=56)
            icon_frame.pack(side="left", padx=16, pady=16)
            icon_frame.pack_propagate(False)

            ctk.CTkLabel(
                icon_frame, text=icon,
                font=ctk.CTkFont(size=24),
                text_color="white",
            ).pack(expand=True)

            # 中间信息
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, pady=12)

            ctk.CTkLabel(
                info_frame, text=name,
                font=ctk.CTkFont(family="Microsoft YaHei", size=15, weight="bold"),
                text_color=self.C["text"],
            ).pack(anchor="w")

            ctk.CTkLabel(
                info_frame, text=desc,
                font=ctk.CTkFont(family="Microsoft YaHei", size=12),
                text_color=self.C["text_secondary"],
            ).pack(anchor="w", pady=(2, 0))

        # ── 底部信息 ──────────────────────────
        footer = ctk.CTkFrame(self, fg_color=self.C["card"], corner_radius=0, height=40)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        ctk.CTkLabel(
            footer, text="传承三百余年中医药文化 · 服务大众健康",
            font=ctk.CTkFont(family="Microsoft YaHei", size=11),
            text_color=self.C["text_secondary"],
        ).pack(expand=True)
