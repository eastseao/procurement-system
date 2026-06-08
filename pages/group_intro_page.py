#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""同仁堂集团介绍页面 - V1.8.3 完整版（含下拉展开/折叠）"""

import tkinter as tk
import customtkinter as ctk


class GroupIntroPage(ctk.CTkFrame):
    def __init__(self, parent, db, colors):
        super().__init__(parent, fg_color=colors["bg"], corner_radius=0)
        self.C = colors
        self._expanded_groups = {}  # group_key -> bool
        self._content_frames = {}   # group_key -> ctk.CTkFrame
        self._arrow_labels = {}     # group_key -> ctk.CTkLabel
        self._build()

    # ── 颜色常量 ──────────────────────────────────
    GROUP_COLORS = {
        "gufen":    (0xC1, 0x81, 0x6D),
        "keji":     (0x8F, 0xA8, 0x82),
        "guoyao":   (0xA8, 0x82, 0x8F),
        "jiankang": (0xC9, 0xA9, 0x6E),
        "shangye":  (0xB5, 0x6A, 0x6A),
        "yaocai":   (0x6A, 0x8F, 0xB5),
        "yiyang":   (0x8F, 0x6A, 0xB5),
        "zhiyao":   (0xB5, 0x6A, 0x8F),
        "zhishu":   (0x5D, 0x4E, 0x37),
    }

    def _build(self):
        # ── 顶部标题栏 ─────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=self.C["card"], corner_radius=0, height=72)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="北京同仁堂（集团）有限责任公司",
            font=ctk.CTkFont(family="Microsoft YaHei", size=20, weight="bold"),
            text_color=self.C["text"],
        ).pack(side="left", padx=24, pady=18)

        ctk.CTkLabel(
            header,
            text="组织架构全景图 3.0",
            font=ctk.CTkFont(family="Microsoft YaHei", size=12),
            text_color=self.C["text_secondary"],
        ).pack(side="left", pady=18)

        ctk.CTkLabel(
            header,
            text="编制日期：2026年6月2日 | 数据来源：集团官网及公开信息",
            font=ctk.CTkFont(family="Microsoft YaHei", size=11),
            text_color=self.C["text_secondary"],
        ).pack(side="right", padx=24, pady=18)

        # ── 集团概况统计 ───────────────────────────────
        stats_frame = ctk.CTkFrame(self, fg_color=self.C["card"], corner_radius=12)
        stats_frame.pack(fill="x", padx=24, pady=(12, 8))

        stats_label = ctk.CTkLabel(
            stats_frame,
            text="集团概况统计",
            font=ctk.CTkFont(family="Microsoft YaHei", size=15, weight="bold"),
            text_color=self.C["text"],
        )
        stats_label.pack(anchor="w", padx=18, pady=(14, 10))

        stats_grid = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_grid.pack(fill="x", padx=18, pady=(0, 14))

        stat_items = [
            ("1669", "创立年份"),
            ("8", "二级集团"),
            ("60+", "三级子公司"),
            ("3", "上市公司"),
            ("12", "海外市场"),
            ("400+", "产品品规"),
        ]
        for num, label in stat_items:
            sc = ctk.CTkFrame(stats_grid, fg_color=self.C["primary_light"], corner_radius=10)
            sc.pack(side="left", fill="x", expand=True, padx=3)

            ctk.CTkLabel(
                sc, text=num,
                font=ctk.CTkFont(family="Microsoft YaHei", size=26, weight="bold"),
                text_color=self.C["primary"],
            ).pack(pady=(12, 0))

            ctk.CTkLabel(
                sc, text=label,
                font=ctk.CTkFont(family="Microsoft YaHei", size=11),
                text_color=self.C["text_secondary"],
            ).pack(pady=(0, 12))

        # ── 滚动区域 ─────────────────────────────────
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24, pady=(0, 8))

        # ── 9个集团板块 ──
        self._build_group(
            scroll,
            group_key="gufen",
            icon="📈",
            name="同仁堂股份集团",
            tags=[
                ("A股：600085", True),
                ("成立：1997年", False),
                ("持股：52.45%", False),
            ],
            color_hex="#C1816D",
            summary_fields=[
                ("全称：", "北京同仁堂股份有限公司"),
                ("主营业务：", "传统中成药生产销售，涵盖丸剂、散剂、酒剂等20余种剂型，400多个品规"),
                ("代表产品：", "安宫牛黄丸、同仁牛黄清心丸、同仁大活络丸、乌鸡白凤丸等"),
            ],
            table_cols=["序号", "公司名称", "所在地", "业务范围", "规模/特色"],
            table_rows=[
                ("1", "北京同仁堂天然药物有限公司", "北京市大兴区", "天然药物研发与生产", "大型生产基地"),
                ("2", "北京同仁堂吉林人参有限责任公司", "吉林省白山市靖宇县", "人参种植、加工、销售", "参源基地10000亩+"),
                ("3", "北京同仁堂内蒙古中药材发展有限公司", "内蒙古包头市昆都仑区", "中药材种植与贸易", "蒙药原料基地"),
                ("4", "北京同仁堂（安国）中药材加工有限责任公司", "河北省保定市安国市", "中药材加工", "华北地区重要加工基地"),
                ("5", "北京同仁堂股份集团（安国）中药材物流有限公司", "河北省保定市安国市", "中药材物流配送", "现代化物流中心"),
                ("6", "北京同仁堂陕西麝业有限公司", "陕西省宝鸡市", "麝香养殖及产品开发", "特种养殖基地"),
            ],
        )

        self._build_group(
            scroll,
            group_key="keji",
            icon="🔬",
            name="同仁堂科技集团",
            tags=[
                ("港股：01666", True),
                ("成立：2000年", False),
                ("控股股东：同仁堂股份", False),
            ],
            color_hex="#8FA882",
            summary_fields=[
                ("全称：", "北京同仁堂科技发展股份有限公司"),
                ("主营业务：", "现代中药研发生产，颗粒剂、胶囊、片剂等新剂型"),
                ("特色认证：", "GMP、ISO9001、澳大利亚TGA、日本厚生省认证"),
            ],
            table_cols=["序号", "公司名称", "所在地", "业务范围", "规模/特色"],
            table_rows=[
                ("1", "北京同仁堂安徽中药材有限公司", "安徽省铜陵市金桥工业园区", "中药材种植、牡丹籽油生产、保健食品", "国家高新技术企业，年销售额6000万+"),
                ("2", "北京同仁堂河北中药材科技开发有限公司", "河北省唐山市玉田县新兴产业园区", "荆芥、柴胡等6品种规范化种植基地", "繁育田200亩，试验田50亩"),
                ("3", "北京同仁堂湖北中药材有限公司", "湖北省", "中药材种植与加工", "区域药材基地"),
                ("4", "北京同仁堂浙江中药材有限公司", "浙江省", "中药材种植与贸易", "区域药材基地"),
                ("5", "北京同仁堂河南中药材科技开发有限公司", "河南省", "中药材规范化种植", "区域药材基地"),
                ("6", "北京同仁堂延边中药材基地有限公司", "吉林省延边州", "中药材种植基地", "长白山药材基地"),
                ("7", "北京同仁堂通科药业有限责任公司", "北京市", "药品生产", "药品制造"),
                ("8", "北京同仁堂科技发展（唐山）有限公司", "河北省唐山市", "药品生产", "现代化生产基地"),
                ("9", "北京同仁堂（唐山）营养保健品有限公司", "河北省唐山市", "营养保健品生产", "保健品制造"),
                ("10", "北京同仁堂麦尔海生物技术有限公司", "北京市", "生物技术研发、化妆品原料", "高新技术企业"),
                ("11", "北京同仁堂（辽宁）科技药业有限公司", "辽宁省", "药品生产", "区域生产基地"),
                ("12", "北京同仁堂科技发展成都有限公司", "四川省成都市", "药品生产", "西南生产基地"),
                ("13", "北京同仁堂世纪广告有限公司", "北京市", "广告宣传服务", "集团内广告服务"),
                ("14", "北京同仁堂南三环中路药店有限公司", "北京市", "药品零售", "零售终端"),
                ("15", "北京同仁堂第二中医医院", "北京市", "中医医疗服务", "综合性中医院"),
            ],
        )

        self._build_group(
            scroll,
            group_key="guoyao",
            icon="🌍",
            name="同仁堂国药集团",
            tags=[
                ("港股：03613", True),
                ("所在地：香港", False),
                ("控股股东：同仁堂股份", False),
            ],
            color_hex="#A8828F",
            summary_fields=[
                ("全称：", "同仁堂国药有限公司"),
                ("主营业务：", "国际市场销售，中国大陆以外地区（香港、澳门及海外）"),
                ("特色：", "集团首个境外生产基地，覆盖全球12+市场"),
            ],
            table_cols=["序号", "公司名称", "所在地", "业务范围", "规模/特色"],
            table_rows=[
                ("1", "同仁堂国药有限公司（香港总部）", "中国香港", "国际市场销售、生产基地", "集团首个境外生产基地"),
            ],
        )

        self._build_group(
            scroll,
            group_key="jiankang",
            icon="💊",
            name="同仁堂健康集团",
            tags=[
                ("成立：2003年", False),
                ("品牌：知嘛健康、总统牌", False),
                ("生产基地：12个", False),
            ],
            color_hex="#C9A96E",
            summary_fields=[
                ("全称：", "北京同仁堂健康药业股份有限公司"),
                ("主营业务：", "健康产品、保健食品、营养补充剂、中药饮片"),
                ("全球生产基地：", "北京、福州、江山、辽宁、大连、青海、宁夏、山西、四川、海南、云南、美国"),
            ],
            table_cols=["序号", "公司名称", "所在地", "业务范围", "规模/特色"],
            table_rows=[
                ("1", "北京同仁堂健康药业股份有限公司（总部）", "北京市大兴区生物医药产业基地", "综合生产研发物流基地", "占地8.6万㎡，工业4.0智慧工厂"),
                ("2", "北京同仁堂健康药业（福州）有限公司", "福建省福州市仓山区金山工业区", "中药饮片、西洋参、燕窝", "福建省高新技术企业，800㎡实验室"),
                ("3", "北京同仁堂蜂产品（江山）有限公司", "浙江省衢州市江山市", "蜂蜜及蜂产品制品", '"中国蜜蜂之乡"核心企业，20+品种'),
                ("4", "北京同仁堂健康药业（辽宁）有限公司", "辽宁省桓仁满族自治县", "人参制品、保健食品", "占地7.6万㎡，建筑面积6.5万㎡"),
                ("5", "北京同仁堂健康（大连）海洋食品有限公司", "辽宁省大连市旅顺口区", "海洋食品加工", "海洋健康产品"),
                ("6", "北京同仁堂健康药业（青海）有限公司", "青海省德令哈市", "特色产品生产", "青藏高原特色产品"),
                ("7", "北京同仁堂健康药业（宁夏）有限公司", "宁夏银川市经济技术开发区", "健康产品生产", "西北生产基地"),
                ("8", "北京同仁堂健康药业（山西）有限公司", "山西省太原市综改示范区", "健康产品生产", "华北生产基地"),
                ("9", "北京同仁堂（四川）健康药业有限公司", "四川省成都市新都区", "健康产品生产", "西南生产基地"),
                ("10", "北京同仁堂健康有机产业（海南）有限公司", "海南省海口市", "有机产品", "热带有机产品"),
                ("11", "北京同仁堂健康茶产业（普洱）有限公司", "云南省普洱市宁洱县", "普洱茶产品", '获"普洱茶"地理标志使用权'),
                ("12", "Beijing Tong Ren Tang Health(USA)Inc.", "美国威斯康星州", "海外生产基地", "集团首个美国生产基地"),
            ],
            subsections=[
                {
                    "title": "销售与服务（5家）",
                    "cols": ["序号", "公司名称", "所在地", "业务范围", "规模/特色"],
                    "rows": [
                        ("1", "北京同仁堂健康药品经营有限公司", "北京市大兴区", "药品批发", "-"),
                        ("2", "北京同仁堂健康药业电子商务有限公司", "北京市门头沟区", "线上销售", "-"),
                        ("3", "北京同仁堂上海保健食品有限公司", "上海市徐汇区", "保健食品销售", "-"),
                        ("4", "北京同仁堂（四川）中西医结合医院有限公司", "四川省成都市新都区", "医疗服务", "-"),
                        ("5", "北京同仁堂施小墨医药有限公司", "北京市朝阳区", "医药服务", "-"),
                    ],
                },
            ],
        )

        self._build_group(
            scroll,
            group_key="shangye",
            icon="🏪",
            name="同仁堂商业集团",
            tags=[
                ("控股股东：同仁堂股份", False),
                ("所在地：北京西城", False),
            ],
            color_hex="#B56A6A",
            summary_fields=[
                ("全称：", "北京同仁堂商业投资集团有限公司"),
                ("主营业务：", "药店零售连锁业务，全国布局连锁药店网络"),
                ("规模：", "拥有遍布全国的连锁药店网络"),
            ],
            table_cols=None,
            table_rows=None,
            note="主要为分布在全国各地的连锁药店，数量众多，在此不逐一列举。",
        )

        self._build_group(
            scroll,
            group_key="yaocai",
            icon="🌿",
            name="同仁堂药材参茸集团",
            tags=[
                ("所在地：北京", False),
                ("业务：药材供应", False),
            ],
            color_hex="#6A8FB5",
            summary_fields=[
                ("全称：", "北京同仁堂药材参茸集团"),
                ("主营业务：", "中药材、参茸产品采购、加工、经营"),
                ("业务范围：", "全产业链药材供应"),
            ],
            table_cols=None,
            table_rows=None,
            note="具体三级公司信息未完全公开，主要业务涵盖药材采购、加工、仓储、销售等环节。",
        )

        self._build_group(
            scroll,
            group_key="yiyang",
            icon="🏥",
            name="同仁堂医养集团",
            tags=[
                ("所在地：北京", False),
                ("特色：筹备上市中", False),
            ],
            color_hex="#8F6AB5",
            summary_fields=[
                ("全称：", "同仁堂医养集团"),
                ("主营业务：", "医疗服务、养老健康产业"),
                ("特色：", "整合收购中医院，筹备上市中"),
            ],
            table_cols=["序号", "公司名称", "所在地", "业务范围", "规模/特色"],
            table_rows=[
                ("1", "北京同仁堂三溪堂中医诊所", "多地布局", "中医诊疗服务", "连锁中医诊所"),
            ],
        )

        self._build_group(
            scroll,
            group_key="zhiyao",
            icon="🏭",
            name="同仁堂制药公司",
            tags=[
                ("所在地：北京大兴", False),
                ("业务：药品生产", False),
            ],
            color_hex="#B56A8F",
            summary_fields=[
                ("全称：", "北京同仁堂制药有限公司"),
                ("所在地：", "北京市大兴区"),
                ("主营业务：", "药品生产"),
            ],
            table_cols=None,
            table_rows=None,
            note="作为集团直属生产企业，主要生产基地位于北京大兴区。",
        )

        self._build_group(
            scroll,
            group_key="zhishu",
            icon="⚙️",
            name="集团直属企业",
            tags=[
                ("数量：5家", False),
            ],
            color_hex="#5D4E37",
            summary_fields=[
                ("全称：", "集团直属企业"),
            ],
            table_cols=["序号", "公司名称", "所在地", "业务范围", "规模/特色"],
            table_rows=[
                ("1", "北京市中药科学研究所有限公司", "北京市朝阳区", "中药研发", "集团研发中心"),
                ("2", "北京同仁堂国际有限公司", "中国香港", "国际业务拓展", "海外业务支持"),
                ("3", "北京同仁堂化妆品有限公司", "北京市丰台区", "化妆品生产销售", "美妆护肤产品"),
                ("4", "北京同仁堂生物制品开发有限公司", "北京市海淀区", "生物制品研发", "生物科技研发"),
                ("5", "北京同仁堂健康产业投资有限公司", "北京市大兴区", "健康产业投资", "战略投资"),
            ],
        )

        # ── 底部信息 ─────────────────────────────────
        footer = ctk.CTkFrame(self, fg_color=self.C["card"], corner_radius=0, height=48)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        ctk.CTkLabel(
            footer,
            text="北京同仁堂（集团）有限责任公司组织架构全景图 3.0",
            font=ctk.CTkFont(family="Microsoft YaHei", size=11),
            text_color=self.C["text_secondary"],
        ).pack(side="left", padx=24, pady=12)

        ctk.CTkLabel(
            footer,
            text="数据来源：集团官网、企查查、公开信息 | 部分公司营业额数据未公开，具体以企业官方披露为准",
            font=ctk.CTkFont(family="Microsoft YaHei", size=10),
            text_color=self.C["text_secondary"],
        ).pack(side="right", padx=24, pady=12)

    # ── 集团板块构建 ──────────────────────────────────
    def _build_group(
        self, parent, group_key, icon, name, tags, color_hex, summary_fields,
        table_cols=None, table_rows=None, note=None, subsections=None
    ):
        """构建一个可展开/折叠的集团板块"""
        w = parent  # 直接添加到父级（scrollable frame）

        # ── 卡片容器 ──────────
        card = ctk.CTkFrame(w, fg_color=self.C["card"], corner_radius=10)
        card.pack(fill="x", pady=(0, 8))

        # ── 头部（可点击）──
        hdr = ctk.CTkFrame(card, fg_color=color_hex, corner_radius=10, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        # 图标
        ctk.CTkLabel(
            hdr, text=icon,
            font=ctk.CTkFont(size=22),
            text_color="white",
        ).pack(side="left", padx=(16, 10), pady=12)

        # 名称 + 标签
        info_frame = ctk.CTkFrame(hdr, fg_color="transparent")
        info_frame.pack(side="left", fill="y", pady=8)

        ctk.CTkLabel(
            info_frame, text=name,
            font=ctk.CTkFont(family="Microsoft YaHei", size=15, weight="bold"),
            text_color="white",
        ).pack(anchor="w")

        tags_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        tags_row.pack(anchor="w", pady=(2, 0))

        for tag_text, is_highlight in tags:
            tag_bg = "#FFD700" if is_highlight else "rgba(255,255,255,0.3)"
            tag_fg = "#8B4513" if is_highlight else "white"
            tag_frame = ctk.CTkFrame(
                tags_row,
                fg_color="#FFD700" if is_highlight else "#E8DDD0",
                corner_radius=12,
            )
            tag_frame.pack(side="left", padx=(0, 6))

            ctk.CTkLabel(
                tag_frame, text=tag_text,
                font=ctk.CTkFont(family="Microsoft YaHei", size=10),
                text_color="#8B4513" if is_highlight else "white",
            ).pack(padx=8, pady=2)

        # 展开/折叠箭头
        arrow_label = ctk.CTkLabel(
            hdr, text="▼",
            font=ctk.CTkFont(size=16),
            text_color="white",
            cursor="hand2",
        )
        arrow_label.pack(side="right", padx=16, pady=12)
        self._arrow_labels[group_key] = arrow_label

        # 为头部绑定点击事件
        for widget in [hdr, arrow_label]:
            widget.bind("<Button-1>", lambda e, k=group_key: self._toggle_group(k))

        # ── 内容区（默认折叠）──
        content = ctk.CTkFrame(card, fg_color="transparent")
        # 默认不显示
        self._content_frames[group_key] = content
        self._expanded_groups[group_key] = False

        # 摘要信息
        if summary_fields:
            summary_box = ctk.CTkFrame(content, fg_color=self.C["primary_light"], corner_radius=8)
            summary_box.pack(fill="x", padx=16, pady=(14, 10))

            for sf_label, sf_value in summary_fields:
                row_f = ctk.CTkFrame(summary_box, fg_color="transparent")
                row_f.pack(fill="x", padx=14, pady=3)

                ctk.CTkLabel(
                    row_f, text=sf_label,
                    font=ctk.CTkFont(family="Microsoft YaHei", size=12, weight="bold"),
                    text_color=self.C["text"],
                ).pack(side="left")

                ctk.CTkLabel(
                    row_f, text=sf_value,
                    font=ctk.CTkFont(family="Microsoft YaHei", size=12),
                    text_color=self.C["text_secondary"],
                    wraplength=700,
                ).pack(side="left", padx=(4, 0))

        # 备注文字（无表格的板块）
        if note:
            note_box = ctk.CTkFrame(content, fg_color=self.C["primary_light"], corner_radius=8)
            note_box.pack(fill="x", padx=16, pady=(0, 14))

            ctk.CTkLabel(
                note_box, text=note,
                font=ctk.CTkFont(family="Microsoft YaHei", size=12),
                text_color=self.C["text_secondary"],
                wraplength=700,
            ).pack(padx=14, pady=12)

        # 主表格
        if table_cols and table_rows:
            sub_label = None
            if group_key == "jiankang":
                sub_label = "生产基地（12家）"
            elif group_key == "yiyang":
                sub_label = "医疗机构"
            self._build_table(content, table_cols, table_rows, padding=(16, 8, 16, 14), label=sub_label)

        # 子区域（如健康集团的"销售与服务"）
        if subsections:
            for sub in subsections:
                self._build_table(
                    content, sub["cols"], sub["rows"],
                    padding=(16, 8, 16, 14),
                    label=sub["title"],
                )

    def _build_table(self, parent, cols, rows, padding, label=None):
        """构建表格"""
        if label:
            ctk.CTkLabel(
                parent, text=label,
                font=ctk.CTkFont(family="Microsoft YaHei", size=13, weight="bold"),
                text_color=self.C["text"],
            ).pack(anchor="w", padx=padding[0], pady=(6, 4))

        table_frame = ctk.CTkFrame(parent, fg_color="transparent")
        table_frame.pack(fill="x", padx=padding[0], pady=(0, padding[3]))

        # ── 表头 ──
        th_frame = ctk.CTkFrame(table_frame, fg_color=self.C["primary"])
        th_frame.pack(fill="x")

        # 计算列宽比
        if cols == ["序号", "公司名称", "所在地", "业务范围", "规模/特色"]:
            weights = [1, 6, 3, 4, 3]
        else:
            n = len(cols)
            weights = [1] * n

        for idx, col_name in enumerate(cols):
            col_f = ctk.CTkFrame(th_frame, fg_color="transparent")
            col_f.pack(side="left", fill="x", expand=True)
            # 使列宽更好看
            if weights:
                col_f.pack_configure(expand=True)
            ctk.CTkLabel(
                col_f, text=col_name,
                font=ctk.CTkFont(family="Microsoft YaHei", size=11, weight="bold"),
                text_color="white",
            ).pack(padx=10, pady=8)

        # ── 表体 ──
        for ridx, row_data in enumerate(rows):
            row_bg = self.C["card"] if ridx % 2 == 0 else self.C["bg"]
            tr_frame = ctk.CTkFrame(table_frame, fg_color=row_bg)
            tr_frame.pack(fill="x")

            for cidx, cell_val in enumerate(row_data):
                col_f = ctk.CTkFrame(tr_frame, fg_color="transparent")
                col_f.pack(side="left", fill="x", expand=True)
                text_color = self.C["primary"] if cidx == 1 else self.C["text_secondary"]
                weight = "bold" if cidx == 1 else "normal"

                ctk.CTkLabel(
                    col_f, text=cell_val,
                    font=ctk.CTkFont(family="Microsoft YaHei", size=11, weight=weight),
                    text_color=text_color,
                    wraplength=180 if cidx >= 2 else 80,
                ).pack(padx=10, pady=6)

    def _toggle_group(self, group_key):
        """展开/折叠集团板块"""
        content = self._content_frames.get(group_key)
        arrow = self._arrow_labels.get(group_key)
        if not content or not arrow:
            return

        if self._expanded_groups.get(group_key):
            # 折叠
            content.pack_forget()
            arrow.configure(text="▼")
            self._expanded_groups[group_key] = False
        else:
            # 展开
            content.pack(fill="x", ipady=0)
            arrow.configure(text="▲")
            self._expanded_groups[group_key] = True
