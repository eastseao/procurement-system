#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""堂训页面 - 展示北京同仁堂企业文化核心内容"""

import os
import tkinter as tk
import customtkinter as ctk


class TangxunPage(ctk.CTkFrame):
    """同仁堂堂训页面"""

    def __init__(self, parent, db, colors):
        super().__init__(parent, fg_color=colors["bg"], corner_radius=0)
        self.C = colors
        self.db = db
        self._build()

    def _build(self):
        # ── 顶部标题栏 ─────────────────────────────
        header = ctk.CTkFrame(self, fg_color=self.C["card"], corner_radius=0, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="🏛  同仁堂堂训",
            font=ctk.CTkFont(family="Microsoft YaHei", size=20, weight="bold"),
            text_color=self.C["text"],
        ).pack(side="left", padx=24, pady=16)

        # ── 滚动内容区 ─────────────────────────────
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=24, pady=16)

        # 品牌历史简介
        self._add_section(scroll, "品牌渊源", [
            "同仁堂品牌始创于1669年（清康熙八年）。",
            "自1723年（清雍正元年）为清宫供御药，历经八代皇帝长达188年。",
            "「全心全意为人民健康服务」是同仁堂不变的宗旨。",
        ], icon="📜")

        # 对联
        self._add_quote_section(scroll, "同仁堂对联", [
            "但愿世间人无病，哪怕架上药生尘"
        ], note="同治年间学者赠予同仁堂十一世乐孟繁的对联，\n盛赞同仁堂济世养生的高尚医药道德与情怀。")

        # 古训（两个必不敢）
        self._add_section(scroll, "同仁堂古训（两个必不敢）", [
            "炮制虽繁必不敢省人工，品味虽贵必不敢减物力。",
            "",
            "始见于1706年同仁堂药店创始人乐凤鸣编写的《同仁堂药目叙》，是同仁堂人恪守至今的古训。",
            "",
            "「两个必不敢」的本意是：",
            "  不论制作过程多么繁琐、工艺多么复杂，为确保疗效显著，不敢有半点懈怠而节省步骤；",
            "  不论中药配方的成本多么高昂、药材多么稀缺，为出珍品，不敢有半点吝啬而省物料。",
            "",
            "「两个必不敢」体现的是以诚信精神为基础的质量观。",
        ], icon="📝")

        # 企业精神
        self._add_quote_section(scroll, "企业精神", [
            "同修仁德，济世养生"
        ], note="同仁堂品牌创始人乐显扬认为「可以养生、可以济人者，惟医药为最」，\n并把「同仁」二字命名为堂名，认为「公而雅」。\n\n「同修仁德，济世养生」是对同仁堂作为中医药企业的\n初心、使命和精神的新概括、新总结。")

        # 自律准则
        self._add_quote_section(scroll, "行业自律准则", [
            "修合无人见，存心有天知"
        ], note="「修合无人见，存心有天知」是中医药行业普遍遵循的传统规则，\n更是历代同仁堂人的自律准则。\n\n字面意思是：在没有监管、他人不知情的情况下，\n在中成药炮制的过程中依然要凭良心，自觉做到药材地道、\n斤两足称、制作遵法。")

        # 制药特色
        self._add_section(scroll, "制药特色与质量承诺", [
            "配方独特  选料上乘  工艺精湛  疗效显著",
            "",
            "配方独特：同仁堂的处方大多来源于乐家祖传、民间验方、古方及宫廷秘方。",
            "选料上乘：遵循古训和清宫制药标准，采用「采其地、用其时」和「上等、纯洁、地道」的药材。",
            "工艺精湛：遵照古训，同仁堂依法炮制修合，前处理环节的20个工序50多种加工方法沿用至今。",
            "疗效显著：同仁堂历来注重药品疗效，用有疗效的药品实现「济世养生」的价值观。",
        ], icon="💊")

        # 经营理念
        self._add_section(scroll, "经营理念", [
            "诚信为本，药德为魂",
            "",
            "同仁堂人在「两个必不敢」古训基础上总结出「诚信为本，药德为魂」的经营理念，",
            "以及「德、诚、信」三字企业真经等行为准则，保证了「疗效显著」，实现了「济世养生」的理想。",
        ], icon="🤝")

    def _add_section(self, parent, title, lines, icon="●"):
        """添加普通内容区块"""
        card = ctk.CTkFrame(parent, fg_color=self.C["card"], corner_radius=10)
        card.pack(fill="x", pady=(0, 12))

        # 标题
        title_frame = ctk.CTkFrame(card, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(16, 8))

        ctk.CTkLabel(
            title_frame, text=f"{icon}  {title}",
            font=ctk.CTkFont(family="Microsoft YaHei", size=15, weight="bold"),
            text_color=self.C["primary"],
        ).pack(anchor="w")

        # 分隔线
        sep = tk.Frame(card, height=1, bg=self.C["divider"])
        sep.pack(fill="x", padx=20, pady=(0, 8))

        # 内容
        for line in lines:
            if line == "":
                ctk.CTkLabel(card, text="", height=6).pack()
                continue
            ctk.CTkLabel(
                card, text=line,
                font=ctk.CTkFont(family="Microsoft YaHei", size=13),
                text_color=self.C["text"],
                justify="left",
                anchor="w",
            ).pack(fill="x", padx=24, pady=2)

        # 底部间距
        ctk.CTkLabel(card, text="", height=12).pack()

    def _add_quote_section(self, parent, title, quotes, note=""):
        """添加引用式内容区块（堂训、对联等）"""
        card = ctk.CTkFrame(parent, fg_color=self.C["card"], corner_radius=10)
        card.pack(fill="x", pady=(0, 12))

        # 标题
        ctk.CTkLabel(
            card, text=f"「 {title} 」",
            font=ctk.CTkFont(family="Microsoft YaHei", size=14, weight="bold"),
            text_color=self.C["primary"],
        ).pack(anchor="w", padx=20, pady=(16, 8))

        # 分隔线
        sep = tk.Frame(card, height=1, bg=self.C["divider"])
        sep.pack(fill="x", padx=20, pady=(0, 12))

        # 引用内容（大字号、居中、暖色背景）
        quote_bg = ctk.CTkFrame(card, fg_color=self.C["primary_light"], corner_radius=8)
        quote_bg.pack(fill="x", padx=20, pady=(0, 8))

        for q in quotes:
            ctk.CTkLabel(
                quote_bg, text=q,
                font=ctk.CTkFont(family="Microsoft YaHei", size=15, weight="bold"),
                text_color=self.C["primary"],
                justify="center",
            ).pack(pady=12)

        # 注释
        if note:
            ctk.CTkLabel(
                card, text=note,
                font=ctk.CTkFont(family="Microsoft YaHei", size=12),
                text_color=self.C["text_secondary"],
                justify="left",
                anchor="w",
                wraplength=600,
            ).pack(fill="x", padx=24, pady=(4, 16))
        else:
            ctk.CTkLabel(card, text="", height=8).pack()
