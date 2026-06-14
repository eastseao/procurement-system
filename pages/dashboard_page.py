#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""看板页面 V2.3.4 — 天气卡片 + 核心指标（白底黑字圆角矩形）+ Treeview 三列动态"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from datetime import datetime, date, timedelta
import calendar
import configparser
import os
import json
import threading
import urllib.request
import urllib.error
import ssl

# 各模块莫兰迪色（用于动态列表的小圆点）
MODULE_COLORS = {
    "packaging":  "#C1816D",
    "collection": "#8FA882",
    "purchase":   "#C9A96E",
    "travel":     "#B56A6A",
    "memo":       "#7BA5B5",
    "quotation":  "#9B8AAE",
    "compare":    "#C4A35A",
    "contract":   "#6B9080",
    "arrival":    "#D4A76A",
}

# ═══════════════════════════════════════════════
# 和风天气 API 配置
# ═══════════════════════════════════════════════
QWEATHER_API_KEY = "45cad86ce05740188c06e6511714a62a"
QWEATHER_GEO_URL = "https://geoapi.qweather.com/v2/city/lookup"
QWEATHER_WEATHER_URL = "https://devapi.qweather.com/v7/weather/7d"

# 天气图标映射（和风天气 icon 代码 → emoji 文字）
WEATHER_ICON_MAP = {
    "100": "☀️",  # 晴
    "101": "⛅",  # 多云
    "102": "🌤️", # 少云
    "103": "⛅",  # 晴间多云
    "104": "☁️",  # 阴
    "150": "🌙",  # 晴(夜)
    "151": "☁️",  # 多云(夜)
    "152": "🌙",  # 少云(夜)
    "153": "☁️",  # 晴间多云(夜)
    "154": "☁️",  # 阴(夜)
    "300": "🌦️", # 阵雨
    "301": "🌧️", # 强阵雨
    "302": "⛈️", # 雷阵雨
    "303": "⛈️", # 强雷阵雨
    "304": "🌨️", # 雷阵雨伴有冰雹
    "305": "🌦️", # 小雨
    "306": "🌧️", # 中雨
    "307": "🌧️", # 大雨
    "308": "🌧️", # 极端降雨
    "309": "🌧️", # 毛毛雨/细雨
    "310": "🌧️", # 暴雨
    "311": "🌧️", # 大暴雨
    "312": "🌧️", # 特大暴雨
    "313": "🧊",  # 冻雨
    "314": "🌦️", # 小到中雨
    "315": "🌧️", # 中到大雨
    "316": "🌧️", # 大到暴雨
    "317": "🌧️", # 暴雨到大暴雨
    "318": "🌧️", # 大暴雨到特大暴雨
    "399": "🌧️", # 雨
    "400": "🌨️", # 小雪
    "401": "❄️",  # 中雪
    "402": "❄️",  # 大雪
    "403": "❄️",  # 暴雪
    "404": "🌨️", # 雨夹雪
    "405": "🌨️", # 雨雪天气
    "406": "🌨️", # 阵雨夹雪
    "407": "🌨️", # 阵雪
    "408": "🌨️", # 小到中雪
    "409": "❄️",  # 中到大雪
    "410": "❄️",  # 大到暴雪
    "499": "❄️",  # 雪
    "500": "🌫️", # 薄雾
    "501": "🌫️", # 雾
    "502": "🌫️", # 霾
    "503": "💨",  # 扬沙
    "504": "💨",  # 浮尘
    "507": "💨",  # 沙尘暴
    "508": "💨",  # 强沙尘暴
    "509": "🌫️", # 浓雾
    "510": "🌫️", # 强浓雾
    "511": "🌫️", # 中度霾
    "512": "🌫️", # 重度霾
    "513": "🌫️", # 严重霾
    "514": "🌫️", # 大雾
    "515": "🌫️", # 特强浓雾
    "900": "🌡️", # 热
    "901": "🥶",  # 冷
    "999": "❓",  # 未知
}

# 默认4个城市
DEFAULT_WEATHER_CITIES = [
    {"name": "北京", "id": "101010100"},
    {"name": "上海", "id": "101020100"},
    {"name": "广州", "id": "101280101"},
    {"name": "成都", "id": "101270101"},
]

# 和风天气 LocationID 数据库（常用城市直接内置，避免每次都调 Geo API）
BUILTIN_CITY_IDS = {
    "北京": "101010100", "上海": "101020100", "广州": "101280101",
    "深圳": "101280601", "成都": "101270101", "杭州": "101210101",
    "武汉": "101200101", "西安": "101110101", "重庆": "101040100",
    "南京": "101190101", "天津": "101030100", "苏州": "101190401",
    "长沙": "101250101", "郑州": "101180101", "青岛": "101120201",
    "大连": "101070201", "宁波": "101210401", "厦门": "101230201",
    "福州": "101230101", "合肥": "101220101", "济南": "101120101",
    "哈尔滨": "101050101", "沈阳": "101070101", "长春": "101060101",
    "昆明": "101290101", "贵阳": "101260101", "南宁": "101300101",
    "海口": "101310101", "石家庄": "101090101", "太原": "101100101",
    "呼和浩特": "101080101", "兰州": "101160101", "西宁": "101150101",
    "银川": "101170101", "乌鲁木齐": "101130101", "拉萨": "101140101",
    "南昌": "101240101", "香港": "101320101", "澳门": "101330101",
    "台北": "101340101", "无锡": "101190201", "东莞": "101281601",
    "佛山": "101280800", "温州": "101210701", "珠海": "101280701",
}

def _get_city_id(city_name):
    """获取城市 LocationID，优先使用内置数据库，否则调用 Geo API"""
    if city_name in BUILTIN_CITY_IDS:
        return BUILTIN_CITY_IDS[city_name]
    try:
        ctx = ssl.create_default_context()
        url = f"{QWEATHER_GEO_URL}?location={urllib.parse.quote(city_name)}&key={QWEATHER_API_KEY}&range=cn&number=1"
        req = urllib.request.Request(url, headers={"User-Agent": "ProcurementSystem/2.3.4"})
        with urllib.request.urlopen(req, timeout=5, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("code") == "200" and data.get("location"):
                return data["location"][0]["id"]
    except Exception:
        pass
    return None

def fetch_weather_7d(city_name_or_id):
    """获取城市7天天气预报，返回 list[dict] 或 None"""
    city_id = city_name_or_id if city_name_or_id.isdigit() else _get_city_id(city_name_or_id)
    if not city_id:
        return None
    try:
        ctx = ssl.create_default_context()
        url = f"{QWEATHER_WEATHER_URL}?location={city_id}&key={QWEATHER_API_KEY}"
        req = urllib.request.Request(url, headers={"User-Agent": "ProcurementSystem/2.3.4"})
        with urllib.request.urlopen(req, timeout=8, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("code") == "200" and data.get("daily"):
                result = []
                for d in data["daily"]:
                    icon = d.get("iconDay", "999")
                    result.append({
                        "date": d.get("fxDate", ""),
                        "tempMax": d.get("tempMax", ""),
                        "tempMin": d.get("tempMin", ""),
                        "textDay": d.get("textDay", ""),
                        "textNight": d.get("textNight", ""),
                        "iconDay": icon,
                        "iconEmoji": WEATHER_ICON_MAP.get(icon, "❓"),
                        "windDirDay": d.get("windDirDay", ""),
                        "windScaleDay": d.get("windScaleDay", ""),
                        "humidity": d.get("humidity", ""),
                        "precip": d.get("precip", ""),
                    })
                return result
    except Exception:
        pass
    return None

def get_weather_cities():
    """从 settings.txt 读取天气城市配置"""
    from pages.settings_page import get_settings_path, load_settings
    path = get_settings_path()
    if os.path.exists(path):
        try:
            cfg = configparser.ConfigParser()
            cfg.read(path, encoding="utf-8")
            if "Weather" in cfg:
                cities_str = cfg.get("Weather", "cities", fallback="")
                if cities_str:
                    cities = []
                    for c in cities_str.split("|"):
                        parts = c.split(",")
                        if len(parts) >= 2:
                            cities.append({"name": parts[0].strip(), "id": parts[1].strip()})
                    if cities:
                        return cities
        except Exception:
            pass
    return DEFAULT_WEATHER_CITIES.copy()

def save_weather_cities(cities):
    """保存天气城市配置到 settings.txt"""
    from pages.settings_page import get_settings_path
    path = get_settings_path()
    # 读取现有内容
    lines = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    # 构建天气配置
    cities_str = "|".join(f"{c['name']},{c['id']}" for c in cities)
    weather_section = f"[Weather]\ncities = {cities_str}\n"
    # 更新或追加
    in_weather = False
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("[Weather]"):
            in_weather = True
            # 跳过现有 Weather section
            i += 1
            while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith("["):
                i += 1
            continue
        new_lines.append(line)
        i += 1
    if not in_weather:
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines.append("\n")
        new_lines.append(weather_section)
    else:
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines.append("\n")
        new_lines.append(weather_section)
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

TREND_UP_COLOR   = "#8FA882"
TREND_DOWN_COLOR = "#B56A6A"
TREND_NEUTRAL    = "#B0A8A0"

AVAILABLE_KPI_CARDS = {
    "packaging": {
        "title": "物料下单",
        "keys": [("处理中", "packaging_active"), ("已完成", "packaging_done")],
        "page_key": "packaging"
    },
    "collection": {
        "title": "催款记录",
        "keys": [(None, "collection_total")],
        "page_key": "collection"
    },
    "purchase": {
        "title": "采购垫付",
        "keys": [("总笔数", "purchase_total"), ("待报销", "purchase_pending")],
        "page_key": "purchase"
    },
    "travel": {
        "title": "差旅报销",
        "keys": [("行程数", "travel_total"), ("待报销", "travel_pending")],
        "page_key": "travel"
    },
    "contract_pending": {
        "title": "待签合同",
        "keys": [(None, "contract_pending")],
        "page_key": "packaging"
    },
    "compare_month": {
        "title": "本月比价",
        "keys": [(None, "compare_month")],
        "page_key": "compare"
    },
}


class DashboardPage(ctk.CTkFrame):
    """看板主页面 — 白底黑字KPI + 三列Treeview动态"""

    def __init__(self, parent, db, C, switch_page=None):
        super().__init__(parent, fg_color=C["bg"], corner_radius=0)
        self.db = db
        self.C = C
        self.switch_page = switch_page
        self._value_labels = {}
        self._trend_labels = {}
        self._card_refs = {}
        self._trees = {}  # 三列 Treeview 引用
        self._weather_cities = []
        self._weather_data = {}
        self._weather_active_city = ""
        self._weather_loading = False
        self._weather_city_btns = {}
        self._weather_content = None
        self._weather_card = None
        self._build_ui()
        self.update_idletasks()
        self._load_data()
        self._auto_refresh()

    # ──────────────────────────────────────────────
    # UI 构建
    # ──────────────────────────────────────────────
    def _build_ui(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True)

        # ── 更新时间 ──
        header_bar = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_bar.pack(fill="x", padx=24, pady=(12, 0))

        self.time_label = ctk.CTkLabel(
            header_bar, text="",
            font=ctk.CTkFont(family="Microsoft YaHei", size=12),
            text_color=self.C["text_secondary"],
        )
        self.time_label.pack(side="right")

        # ═══════════════════════════════════════════
        # 天气卡片：7天预报，4个城市可切换
        # ═══════════════════════════════════════════
        self._build_weather_card(main_frame)

        # ═══════════════════════════════════════════
        # 核心指标：白底黑字圆角矩形，一行四个
        # ═══════════════════════════════════════════
        self._kpi_grid = ctk.CTkFrame(main_frame, fg_color="transparent")
        self._kpi_grid.pack(fill="x", padx=24, pady=(8, 12))
        self._load_kpi_config()

        # ═══════════════════════════════════════════
        # 三列动态：下单动态 | 计划单动态 | 其他动态
        # ═══════════════════════════════════════════
        bottom_row = ctk.CTkFrame(main_frame, fg_color="transparent")
        bottom_row.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        bottom_row.grid_columnconfigure(0, weight=1, uniform="col")
        bottom_row.grid_columnconfigure(1, weight=1, uniform="col")
        bottom_row.grid_columnconfigure(2, weight=1, uniform="col")
        bottom_row.grid_rowconfigure(0, weight=1)

        # ── 左列：下单动态 ──
        self._build_tree_card(bottom_row, 0, "📦 下单动态", "packaging",
            columns=("时间", "内容"), col_widths={"时间": 75, "内容": 220})

        # ── 中列：计划单动态 ──
        self._build_tree_card(bottom_row, 1, "📋 计划单动态", "plan",
            columns=("时间", "内容"), col_widths={"时间": 75, "内容": 220})

        # ── 右列：其他动态 ──
        right_card = ctk.CTkFrame(bottom_row, fg_color=self.C["card"],
            corner_radius=self.C["radius_card"],
            border_width=1, border_color=self.C["border"])
        right_card.grid(row=0, column=2, sticky="nsew", padx=(6, 0))

        # 标题 + 刷新
        title_row2 = ctk.CTkFrame(right_card, fg_color="transparent")
        title_row2.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(
            title_row2, text="📋 其他动态",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.C["text"],
        ).pack(side="left")

        self._refresh_other_btn = ctk.CTkButton(
            title_row2, text="🔄 刷新", width=52, height=22,
            font=ctk.CTkFont(size=10),
            fg_color="transparent", hover_color="#E8E0D5",
            corner_radius=11, border_width=1,
            border_color=self.C["border"],
            command=self._manual_refresh,
            text_color=self.C["text_secondary"],
        )
        self._refresh_other_btn.pack(side="right")

        # 类型筛选
        filter_frame = ctk.CTkFrame(right_card, fg_color="transparent", height=28)
        filter_frame.pack(fill="x", padx=8, pady=(0, 4))
        filter_frame.pack_propagate(False)

        self._activity_type_filter = "all"
        filter_types = [
            ("全部", "all"), ("催款", "collection"),
            ("垫付", "purchase"), ("出差", "travel"), ("备忘", "memo"),
        ]
        self._filter_buttons = {}
        for label, key in filter_types:
            btn = ctk.CTkButton(
                filter_frame, text=label, width=50, height=22,
                font=ctk.CTkFont(size=10),
                fg_color="#E8D5C4" if key == "all" else "transparent",
                hover_color="#E8D5C4",
                corner_radius=16, border_width=1,
                border_color="#E8D5C4",
                command=lambda k=key: self._on_filter_click(k),
                text_color="#000000",
            )
            btn.pack(side="left", padx=(0, 2))
            self._filter_buttons[key] = btn

        # 其他动态 Treeview
        self._build_inline_tree(right_card, "other",
            columns=("时间", "内容"), col_widths={"时间": 75, "内容": 220},
            padx=6, pady=(0, 6))

    # ──────────────────────────────────────────────
    # 天气卡片
    # ──────────────────────────────────────────────
    def _build_weather_card(self, parent):
        """构建顶部天气卡片：4个城市Tab + 7天预报"""
        self._weather_cities = get_weather_cities()
        self._weather_data = {}  # {city_name: [day_dict, ...]}
        self._weather_active_city = self._weather_cities[0]["name"] if self._weather_cities else "北京"
        self._weather_loading = False

        # 天气主卡片容器
        self._weather_card = ctk.CTkFrame(
            parent, fg_color=self.C["card"],
            corner_radius=self.C["radius_card"],
            border_width=1, border_color=self.C["border"],
        )
        self._weather_card.pack(fill="x", padx=24, pady=(0, 10))

        # 标题行 + 城市切换 + 刷新
        title_row = ctk.CTkFrame(self._weather_card, fg_color="transparent")
        title_row.pack(fill="x", padx=12, pady=(8, 0))

        ctk.CTkLabel(
            title_row, text="🌤️ 天气预报",
            font=ctk.CTkFont(family="Microsoft YaHei", size=14, weight="bold"),
            text_color=self.C["text"],
        ).pack(side="left")

        # 城市切换按钮
        self._weather_city_btns = {}
        city_bar = ctk.CTkFrame(title_row, fg_color="transparent")
        city_bar.pack(side="left", padx=(16, 0))
        for i, city in enumerate(self._weather_cities[:4]):
            name = city["name"]
            is_active = (name == self._weather_active_city)
            btn = ctk.CTkButton(
                city_bar, text=name, width=52, height=22,
                font=ctk.CTkFont(size=10),
                fg_color="#E8D5C4" if is_active else "transparent",
                hover_color="#E8D5C4",
                corner_radius=11, border_width=1,
                border_color="#E8D5C4",
                command=lambda n=name: self._on_weather_city_click(n),
                text_color="#000000",
            )
            btn.pack(side="left", padx=(0, 3))
            self._weather_city_btns[name] = btn

        # 刷新按钮
        ctk.CTkButton(
            title_row, text="🔄 刷新", width=52, height=22,
            font=ctk.CTkFont(size=10),
            fg_color="transparent", hover_color="#E8E0D5",
            corner_radius=11, border_width=1,
            border_color=self.C["border"],
            command=self._refresh_weather,
            text_color=self.C["text_secondary"],
        ).pack(side="right")

        # 7天预报内容区
        self._weather_content = ctk.CTkFrame(self._weather_card, fg_color="transparent")
        self._weather_content.pack(fill="x", padx=8, pady=(4, 8))

        # 加载天气数据（异步）
        self._load_weather_data()

    def _on_weather_city_click(self, city_name):
        """切换天气城市"""
        if self._weather_loading:
            return
        self._weather_active_city = city_name
        for name, btn in self._weather_city_btns.items():
            is_active = (name == city_name)
            btn.configure(
                fg_color="#E8D5C4" if is_active else "transparent",
            )
        # 如果已有数据直接渲染，否则异步加载
        if city_name in self._weather_data:
            self._render_weather_content()
        else:
            self._load_weather_data()

    def _load_weather_data(self):
        """异步加载当前城市的天气数据"""
        city_name = self._weather_active_city
        # 显示加载中
        self._render_weather_loading()
        self._weather_loading = True

        def _worker():
            data = None
            # 先尝试用内置ID
            city_id = BUILTIN_CITY_IDS.get(city_name, "")
            # 从城市配置中获取ID
            for c in self._weather_cities:
                if c["name"] == city_name:
                    city_id = c["id"]
                    break
            if city_id:
                data = fetch_weather_7d(city_id)
            elif city_name:
                data = fetch_weather_7d(city_name)

            def _callback():
                self._weather_loading = False
                if data:
                    self._weather_data[city_name] = data
                self._render_weather_content()

            try:
                self.after(0, _callback)
            except Exception:
                pass

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def _refresh_weather(self):
        """手动刷新天气"""
        city_name = self._weather_active_city
        if city_name in self._weather_data:
            del self._weather_data[city_name]
        self._load_weather_data()

    def _render_weather_loading(self):
        """渲染加载中状态"""
        for w in self._weather_content.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self._weather_content,
            text="⏳ 加载天气数据中...",
            font=ctk.CTkFont(family="Microsoft YaHei", size=11),
            text_color=self.C["text_secondary"],
        ).pack(pady=(6, 6))

    def _render_weather_content(self):
        """渲染7天天气预报内容"""
        for w in self._weather_content.winfo_children():
            w.destroy()

        city_name = self._weather_active_city
        data = self._weather_data.get(city_name)

        if not data:
            # 无数据
            ctk.CTkLabel(
                self._weather_content,
                text="⚠️ 暂无天气数据，请检查网络后点击刷新",
                font=ctk.CTkFont(family="Microsoft YaHei", size=11),
                text_color="#B56A6A",
            ).pack(pady=(6, 6))
            return

        # 7天预报水平排列
        days_frame = ctk.CTkFrame(self._weather_content, fg_color="transparent")
        days_frame.pack(fill="x", padx=4)

        # 等分7列
        for i in range(7):
            days_frame.grid_columnconfigure(i, weight=1, uniform="weather_day")

        today = date.today()
        weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

        for i, day in enumerate(data[:7]):
            day_card = ctk.CTkFrame(
                days_frame, fg_color="transparent",
                corner_radius=8,
            )
            day_card.grid(row=0, column=i, sticky="n", padx=1, pady=2)

            # 解析日期
            day_date = None
            try:
                day_date = datetime.strptime(day["date"], "%Y-%m-%d").date()
            except Exception:
                day_date = today + timedelta(days=i)

            is_today = (day_date == today)
            weekday_idx = day_date.weekday()
            weekday_str = "今天" if is_today else weekday_names[weekday_idx]

            # 日期
            date_display = f"{day_date.month}/{day_date.day}"
            date_color = "#C1816D" if is_today else self.C["text_secondary"]
            date_weight = "bold" if is_today else "normal"

            ctk.CTkLabel(
                day_card, text=weekday_str,
                font=ctk.CTkFont(family="Microsoft YaHei", size=10, weight=date_weight),
                text_color=date_color,
            ).pack()

            ctk.CTkLabel(
                day_card, text=date_display,
                font=ctk.CTkFont(family="Microsoft YaHei", size=9),
                text_color=self.C["text_secondary"],
            ).pack()

            # 天气图标
            ctk.CTkLabel(
                day_card, text=day.get("iconEmoji", "❓"),
                font=ctk.CTkFont(size=18),
                text_color=self.C["text"],
            ).pack(pady=(2, 0))

            # 天气描述
            desc = day.get("textDay", "") or day.get("textNight", "") or "—"
            ctk.CTkLabel(
                day_card, text=desc,
                font=ctk.CTkFont(family="Microsoft YaHei", size=9),
                text_color=self.C["text"],
            ).pack()

            # 温度范围
            temp_text = f"{day.get('tempMin', '—')}° ~ {day.get('tempMax', '—')}°"
            ctk.CTkLabel(
                day_card, text=temp_text,
                font=ctk.CTkFont(family="Microsoft YaHei", size=9, weight="bold"),
                text_color=self.C["text"],
            ).pack(pady=(0, 2))

            # 风力和湿度
            wind = day.get("windScaleDay", "")
            wind_dir = day.get("windDirDay", "")
            wind_str = f"{wind_dir}{wind}级" if wind_dir and wind else ""
            humidity = day.get("humidity", "")
            extra = wind_str
            if humidity:
                extra += f" 湿度{humidity}%" if extra else f"湿度{humidity}%"
            if extra:
                ctk.CTkLabel(
                    day_card, text=extra,
                    font=ctk.CTkFont(family="Microsoft YaHei", size=8),
                    text_color=self.C["text_secondary"],
                ).pack()

        # 底部数据来源
        ctk.CTkLabel(
            self._weather_content,
            text="数据来源：和风天气",
            font=ctk.CTkFont(family="Microsoft YaHei", size=8),
            text_color="#B0A8A0",
        ).pack(pady=(4, 0))

    def _build_tree_card(self, parent, col, title, tree_key, columns, col_widths):
        """构建带标题+刷新+Treeview的动态卡片列"""
        card = ctk.CTkFrame(parent, fg_color=self.C["card"],
            corner_radius=self.C["radius_card"],
            border_width=1, border_color=self.C["border"])
        card.grid(row=0, column=col, sticky="nsew", padx=(0, 6))

        # 标题 + 刷新按钮
        title_row = ctk.CTkFrame(card, fg_color="transparent")
        title_row.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(
            title_row, text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.C["text"],
        ).pack(side="left")

        ctk.CTkButton(
            title_row, text="🔄 刷新", width=52, height=22,
            font=ctk.CTkFont(size=10),
            fg_color="transparent", hover_color="#E8E0D5",
            corner_radius=11, border_width=1,
            border_color=self.C["border"],
            command=self._manual_refresh,
            text_color=self.C["text_secondary"],
        ).pack(side="right")

        self._build_inline_tree(card, tree_key, columns, col_widths, padx=6, pady=(0, 6))

    def _build_inline_tree(self, parent, tree_key, columns, col_widths, padx=6, pady=(0, 6)):
        """在父容器内构建一个 Treeview 表格"""
        # 使用唯一的 style 名避免冲突
        style_name = f"Dash.{tree_key}.Treeview"
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(style_name,
            font=("Microsoft YaHei", 9),
            rowheight=30,
            background="#FFFFFF",
            fieldbackground="#FFFFFF",
            foreground="#1E293B",
            borderwidth=0,
            relief="flat")
        style.configure(f"{style_name}.Heading",
            font=("Microsoft YaHei", 9, "bold"),
            background="#F8FAFC",
            foreground="#475569",
            relief="flat",
            borderwidth=0)
        style.map(style_name,
            background=[("selected", "#E8D5C4")],
            foreground=[("selected", "#4A3728")])
        style.layout(style_name, [
            ("Treeview.treearea", {"sticky": "nswe"})
        ])

        tree_wrap = tk.Frame(parent, bg="#FFFFFF")
        tree_wrap.pack(fill="both", expand=True, padx=padx, pady=pady)

        tree = ttk.Treeview(
            tree_wrap, style=style_name,
            columns=columns, show="headings", height=8, selectmode="browse"
        )

        for col in columns:
            tree.heading(col, text=col)
            w = col_widths.get(col, 80)
            anchor = "w" if col == "内容" else "center"
            tree.column(col, width=w, minwidth=40, stretch=(col == "内容"), anchor=anchor)

        vsb = ttk.Scrollbar(tree_wrap, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)

        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        tree.tag_configure("odd", background="#F8FAFC")
        tree.tag_configure("even", background="#FFFFFF")
        tree.tag_configure("hover", background="#FFF2E6")
        tree.bind("<Motion>", lambda e, t=tree: self._on_tree_hover(e, t))
        tree.bind("<Leave>", lambda e, t=tree: self._on_tree_leave(e, t))

        self._trees[tree_key] = tree

    # ── 悬浮高亮 ────────────
    def _on_tree_hover(self, event, tree):
        item = tree.identify_row(event.y)
        # 清除上一个
        prev = getattr(tree, "_last_hover", None)
        if prev and prev != item:
            try:
                tags = list(tree.item(prev, "tags"))
                if "hover" in tags:
                    tags.remove("hover")
                    tree.item(prev, tags=tags)
            except Exception:
                pass
        if item:
            try:
                tags = list(tree.item(item, "tags"))
                if "hover" not in tags:
                    tags.append("hover")
                    tree.item(item, tags=tags)
            except Exception:
                pass
        tree._last_hover = item

    def _on_tree_leave(self, event, tree):
        prev = getattr(tree, "_last_hover", None)
        if prev:
            try:
                tags = list(tree.item(prev, "tags"))
                if "hover" in tags:
                    tags.remove("hover")
                    tree.item(prev, tags=tags)
            except Exception:
                pass
            tree._last_hover = None

    # ── KPI 配置加载 ─────────
    def _load_kpi_config(self):
        _settings_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "settings.txt")
        _data_dir = os.path.join(os.path.expanduser("~"), "采购管理系统数据")
        _std_settings_path = os.path.join(_data_dir, "settings.txt")
        _config = configparser.ConfigParser()
        if os.path.exists(_std_settings_path):
            try:
                _config.read(_std_settings_path, encoding="utf-8")
            except Exception:
                pass
        elif os.path.exists(_settings_path):
            try:
                _config.read(_settings_path, encoding="utf-8")
            except Exception:
                pass
        _default_kpis = "packaging,collection,purchase,travel"
        try:
            _selected_kpis = _config.get("General", "kpi_cards") if "General" in _config else _default_kpis
        except Exception:
            _selected_kpis = _default_kpis
        if _selected_kpis == _default_kpis:
            for _try_path in [_std_settings_path, _settings_path]:
                if not os.path.exists(_try_path):
                    continue
                try:
                    with open(_try_path, "r", encoding="utf-8") as _f:
                        for _line in _f:
                            _line = _line.strip()
                            if _line.startswith("kpi_cards="):
                                _selected_kpis = _line.split("=", 1)[1].strip()
                                break
                except Exception:
                    pass
                if _selected_kpis != _default_kpis:
                    break
        self._selected_kpi_keys = [k.strip() for k in _selected_kpis.split(",") if k.strip()]

        self._value_labels = {}
        self._trend_labels = {}
        self._card_refs = {}

        if hasattr(self, '_kpi_grid') and self._kpi_grid.winfo_exists():
            for child in self._kpi_grid.winfo_children():
                child.destroy()

        self._kpi_grid.grid_columnconfigure(0, weight=1, uniform="kpi")
        self._kpi_grid.grid_columnconfigure(1, weight=1, uniform="kpi")
        self._kpi_grid.grid_columnconfigure(2, weight=1, uniform="kpi")
        self._kpi_grid.grid_columnconfigure(3, weight=1, uniform="kpi")

        for idx, kpi_key in enumerate(self._selected_kpi_keys):
            if kpi_key not in AVAILABLE_KPI_CARDS:
                continue
            if idx >= 4:
                break
            kpi_cfg = AVAILABLE_KPI_CARDS[kpi_key]
            self._make_kpi_card(
                self._kpi_grid, idx,
                title=kpi_cfg["title"],
                keys=kpi_cfg["keys"],
                page_key=kpi_cfg["page_key"]
            )

    # ── KPI 卡片（白底黑字圆角矩形）────
    def _make_kpi_card(self, parent, col_idx, title, keys, page_key):
        """构建 KPI 卡片 — 白色圆角矩形，黑色文字，有边框"""
        card = ctk.CTkFrame(
            parent,
            fg_color="#FFFFFF",
            corner_radius=12,
            height=78,
            border_width=1,
            border_color="#E2E0DA",
        )
        card.grid(row=0, column=col_idx, sticky="ew", padx=4, pady=2)
        card.grid_propagate(False)

        # 悬浮高亮
        card.bind("<Enter>", lambda e, c=card: c.configure(border_color="#C1816D", border_width=2))
        card.bind("<Leave>", lambda e, c=card: c.configure(border_color="#E2E0DA", border_width=1))

        # 点击跳转
        btn = ctk.CTkButton(
            card, text="", fg_color="transparent",
            hover=False, corner_radius=12,
            command=lambda k=page_key: self._on_card_click(k),
        )
        btn.place(x=0, y=0, relwidth=1, relheight=1)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=12, pady=(8, 4))

        # 标题行
        title_row = ctk.CTkFrame(inner, fg_color="transparent")
        title_row.pack(fill="x")

        ctk.CTkLabel(
            title_row, text=title,
            font=ctk.CTkFont(family="Microsoft YaHei", size=12, weight="bold"),
            text_color="#000000",
        ).pack(side="left")

        # 趋势标签
        trend_label = ctk.CTkLabel(
            title_row, text="",
            font=ctk.CTkFont(family="Microsoft YaHei", size=11, weight="bold"),
            text_color="#8FA882",
        )
        trend_label.pack(side="right")
        self._trend_labels[title] = trend_label

        # 值区域
        if len(keys) == 1:
            _, key = keys[0]
            val_label = ctk.CTkLabel(
                inner, text="—",
                font=ctk.CTkFont(family="Microsoft YaHei", size=22, weight="bold"),
                text_color="#000000",
            )
            val_label.pack(anchor="w", pady=(1, 0))
            unit_label = ctk.CTkLabel(
                inner, text="",
                font=ctk.CTkFont(family="Microsoft YaHei", size=10),
                text_color="#666666",
            )
            unit_label.pack(anchor="w")
            self._value_labels[key] = val_label
            self._value_labels[f"{key}_unit"] = unit_label
        else:
            vals_row = ctk.CTkFrame(inner, fg_color="transparent")
            vals_row.pack(fill="x", pady=(2, 0))
            for sub, key in keys:
                col_frame = ctk.CTkFrame(vals_row, fg_color="transparent")
                col_frame.pack(side="left", fill="x", expand=True)
                val_label = ctk.CTkLabel(
                    col_frame, text="—",
                    font=ctk.CTkFont(family="Microsoft YaHei", size=18, weight="bold"),
                    text_color="#000000",
                )
                val_label.pack(anchor="w")
                ctk.CTkLabel(
                    col_frame, text=sub,
                    font=ctk.CTkFont(family="Microsoft YaHei", size=10),
                    text_color="#666666",
                ).pack(anchor="w")
                self._value_labels[key] = val_label

        self._card_refs[page_key] = card

    # ──────────────────────────────────────────────
    # 数据加载
    # ──────────────────────────────────────────────
    def _load_data(self):
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            if hasattr(self, 'time_label'):
                self.time_label.configure(text=f"更新时间：{now}")

            # 物料下单 KPI
            packaging_active = self.db.get_packagings(archived=0)
            packaging_done = self.db.get_packagings(archived=1)
            self._set_value("packaging_active", str(len(packaging_active)))
            self._set_value("packaging_done", str(len(packaging_done)))
            self._update_trend("物料下单", len(packaging_active), "packaging_orders", "created_at")

            # 催款记录 KPI
            collections = self.db.get_collections()
            self._set_value("collection_total", str(len(collections)))
            self._set_value("collection_total_unit", "条记录")
            self._update_trend("催款记录", len(collections), "collection_reminders", "created_at")

            # 采购垫付 KPI
            purchases = self.db.get_purchases(archived=0)
            purchase_pending_amt = sum(
                p.get("total", 0) for p in purchases
                if p.get("reimbursement_status") != "已报销"
            )
            self._set_value("purchase_total", str(len(purchases)))
            self._set_value("purchase_pending", f"¥{purchase_pending_amt:.0f}")
            self._update_trend("采购垫付", len(purchases), "purchase", "created_at")

            # 差旅报销 KPI
            travels = self.db.get_travels(archived=0)
            travel_pending_amt = sum(
                t.get("total", 0) for t in travels
                if t.get("reimbursement_status") != "已报销"
            )
            self._set_value("travel_total", str(len(travels)))
            self._set_value("travel_pending", f"¥{travel_pending_amt:.0f}")
            self._update_trend("差旅报销", len(travels), "travel", "created_at")

            # 待签合同数
            try:
                cur = self.db.conn.cursor()
                cur.execute("SELECT COUNT(*) FROM packaging_orders WHERE contract_status NOT IN ('已签', '已完成', '') OR contract_status IS NULL")
                self._set_value("contract_pending", str(cur.fetchone()[0]))
                self._set_value("contract_pending_unit", "个合同")
            except Exception:
                self._set_value("contract_pending", "—")

            # 本月比价次数
            try:
                today = date.today()
                month_start = today.replace(day=1).strftime("%Y-%m-%d")
                month_end = f"{today.strftime('%Y-%m-%d')} 23:59:59"
                cur = self.db.conn.cursor()
                cur.execute("SELECT COUNT(*) FROM third_party_records WHERE created_at >= ? AND created_at <= ?", (month_start, month_end))
                self._set_value("compare_month", str(cur.fetchone()[0]))
                self._set_value("compare_month_unit", "次比价")
            except Exception:
                self._set_value("compare_month", "—")

            # 加载三个 Treeview 动态
            self._update_packaging_tree()
            self._update_plan_tree()
            self._update_other_tree()

        except Exception as e:
            print(f"加载看板数据失败: {e}")
            import traceback
            traceback.print_exc()

    def _update_trend(self, card_title, current_val, table_name, date_field):
        try:
            cur = self.db.conn.cursor()
            today = date.today()
            if today.month == 1:
                last_month_end = today.replace(year=today.year-1, month=12, day=31)
            else:
                last_month_end = today.replace(month=today.month-1, day=1)
                last_day = calendar.monthrange(last_month_end.year, last_month_end.month)[1]
                last_month_end = last_month_end.replace(day=last_day)
            last_month_start = last_month_end.replace(day=1).strftime("%Y-%m-01")
            table_map = {
                "packaging_orders": "packaging_orders",
                "collection_reminders": "collection_reminders",
                "purchase": "purchase",
                "travel": "travel",
                "memos": "memos",
            }
            tbl = table_map.get(table_name, table_name)
            try:
                cur.execute(
                    f"SELECT COUNT(*) FROM {tbl} WHERE created_at >= ? AND created_at <= ?",
                    (last_month_start, last_month_end.strftime("%Y-%m-%d") + " 23:59:59")
                )
                last_month_count = cur.fetchone()[0]
            except Exception:
                last_month_count = 0

            trend_lbl = self._trend_labels.get(card_title)
            if trend_lbl is None:
                return
            if last_month_count == 0:
                if current_val > 0:
                    trend_lbl.configure(text="● 新增", text_color=TREND_UP_COLOR)
                else:
                    trend_lbl.configure(text="● —", text_color=TREND_NEUTRAL)
            else:
                pct = (current_val - last_month_count) / last_month_count * 100
                if pct > 0:
                    trend_lbl.configure(text=f"↑ {pct:.0f}%", text_color=TREND_UP_COLOR)
                elif pct < 0:
                    trend_lbl.configure(text=f"↓ {abs(pct):.0f}%", text_color=TREND_DOWN_COLOR)
                else:
                    trend_lbl.configure(text="→ 持平", text_color=TREND_NEUTRAL)
        except Exception as e:
            print(f"趋势计算失败({card_title}): {e}")

    def _fmt_time(self, ts):
        """格式化时间显示"""
        if not ts:
            return ""
        try:
            return datetime.strptime(ts[:16], "%Y-%m-%d %H:%M").strftime("%m-%d %H:%M")
        except Exception:
            return str(ts)[:16] if ts else ""

    def _fill_tree(self, tree_key, items):
        """填充 Treeview 数据"""
        tree = self._trees.get(tree_key)
        if not tree:
            return
        for item in tree.get_children():
            tree.delete(item)

        for i, (ts, desc, mod_key) in enumerate(items):
            time_str = self._fmt_time(ts)
            tag = "odd" if i % 2 == 0 else "even"
            tree.insert("", "end", values=(time_str, desc), tags=(tag,))

    # ── 下单动态（下单页面数据）────
    def _update_packaging_tree(self):
        """下单动态：直接展示 packaging_orders 表数据"""
        try:
            items = []
            try:
                records = self.db.get_packagings(archived=0)
                for rec in records[:30]:
                    name = rec.get("material_name", "") or "未命名"
                    name_str = name[:18] + "..." if len(name) > 18 else name
                    factory = rec.get("order_factory", "") or ""
                    factory_str = f" →{factory}" if factory else ""
                    ts = rec.get("created_at", "")
                    items.append((ts, f"📦 {name_str}{factory_str}", "packaging"))
            except Exception:
                pass

            items.sort(key=lambda x: x[0], reverse=True)
            self._fill_tree("packaging", items[:30])
        except Exception as e:
            print(f"下单动态加载失败: {e}")

    # ── 计划单动态 ────────────────
    def _update_plan_tree(self):
        """计划单动态：plan_records + quotation + compare + contract"""
        try:
            items = []

            # 计划记录
            try:
                cur = self.db.conn.cursor()
                cur.execute(
                    "SELECT approval_no, material_name, quantity, created_at FROM plan_records "
                    "WHERE created_at IS NOT NULL ORDER BY created_at DESC LIMIT 25"
                )
                for row in cur.fetchall():
                    approval_no, name, qty, ts = row
                    no_str = f"[{approval_no[:12]}] " if approval_no else ""
                    name_str = name[:18] + "..." if name and len(name) > 18 else (name or '未命名')
                    items.append((ts, f"📋 {no_str}{name_str} ×{int(qty) if qty else 0}", "quotation"))
            except Exception:
                pass

            # 报价单
            try:
                cur = self.db.conn.cursor()
                cur.execute(
                    "SELECT product_names, supplier_name, created_at FROM quotation_records "
                    "WHERE created_at IS NOT NULL ORDER BY created_at DESC LIMIT 15"
                )
                for row in cur.fetchall():
                    names, supplier, ts = row
                    name_str = names[:20] + "..." if names and len(names) > 20 else (names or '未命名')
                    sup_str = f"→{supplier}" if supplier else ""
                    items.append((ts, f"📄 {name_str} {sup_str}", "quotation"))
            except Exception:
                pass

            # 三方比价
            try:
                cur = self.db.conn.cursor()
                cur.execute(
                    "SELECT product_name, final_supplier, created_at FROM third_party_records "
                    "WHERE created_at IS NOT NULL ORDER BY created_at DESC LIMIT 10"
                )
                for row in cur.fetchall():
                    prod, supplier, ts = row
                    prod_str = prod[:18] + "..." if prod and len(prod) > 18 else (prod or '未命名')
                    sup_str = f"→{supplier}" if supplier else ""
                    items.append((ts, f"⚖️ {prod_str} {sup_str}", "compare"))
            except Exception:
                pass

            # 合同
            try:
                cur = self.db.conn.cursor()
                cur.execute(
                    "SELECT material_name, contract_status, created_at FROM packaging_orders "
                    "WHERE contract_status IS NOT NULL AND contract_status != '' "
                    "ORDER BY created_at DESC LIMIT 10"
                )
                for row in cur.fetchall():
                    name, status, ts = row
                    name_str = name[:16] + "..." if name and len(name) > 16 else (name or '未命名')
                    items.append((ts, f"📝 {name_str} ({status})", "contract"))
            except Exception:
                pass

            items.sort(key=lambda x: x[0], reverse=True)
            self._fill_tree("plan", items[:30])
        except Exception as e:
            print(f"计划单动态加载失败: {e}")

    # ── 其他动态 ──────────────────
    def _update_other_tree(self):
        """其他动态：催款/垫付/出差/备忘录"""
        try:
            items = []

            # 催款 — 对应应付页面 collection_reminders 表
            try:
                cur = self.db.conn.cursor()
                cur.execute(
                    "SELECT supplier_name, amount_due, reminder_date, created_at FROM collection_reminders "
                    "ORDER BY reminder_date DESC, created_at DESC LIMIT 25"
                )
                for row in cur.fetchall():
                    name, amount, rdate, ts = row
                    name_str = name[:14] + "..." if name and len(name) > 14 else (name or '未知')
                    amt_str = f" ¥{amount:,.0f}" if amount else ""
                    date_str = f" [{rdate}]" if rdate else ""
                    items.append((ts or rdate, f"💰 {name_str}{date_str}{amt_str}", "collection"))
            except Exception:
                pass

            # 垫付
            try:
                cur = self.db.conn.cursor()
                cur.execute(
                    "SELECT project, handler, created_at FROM purchase "
                    "WHERE created_at IS NOT NULL ORDER BY created_at DESC LIMIT 20"
                )
                for row in cur.fetchall():
                    project, handler, ts = row
                    proj_str = project or '默认项目'
                    handler_str = f"({handler})" if handler else ""
                    items.append((ts, f"💳 {proj_str} {handler_str}", "purchase"))
            except Exception:
                pass

            # 出差
            try:
                cur = self.db.conn.cursor()
                cur.execute(
                    "SELECT reason, destination, created_at FROM travel "
                    "WHERE created_at IS NOT NULL ORDER BY created_at DESC LIMIT 20"
                )
                for row in cur.fetchall():
                    reason, dest, ts = row
                    reason_str = reason[:14] + "..." if reason and len(reason) > 14 else (reason or '出差')
                    dest_str = dest or ''
                    items.append((ts, f"✈️ {reason_str} →{dest_str}", "travel"))
            except Exception:
                pass

            # 备忘录
            try:
                cur = self.db.conn.cursor()
                cur.execute(
                    "SELECT content, created_at FROM memos "
                    "WHERE created_at IS NOT NULL ORDER BY created_at DESC LIMIT 20"
                )
                for row in cur.fetchall():
                    content, ts = row
                    content_str = content[:22] + "..." if content and len(content) > 22 else (content or '无标题')
                    items.append((ts, f"📝 {content_str}", "memo"))
            except Exception:
                pass

            # 筛选
            if self._activity_type_filter and self._activity_type_filter != "all":
                items = [
                    (ts, desc, mod_key) for ts, desc, mod_key in items
                    if mod_key == self._activity_type_filter
                ]

            items.sort(key=lambda x: x[0], reverse=True)
            self._fill_tree("other", items[:30])
        except Exception as e:
            print(f"其他动态加载失败: {e}")

    # ── 筛选 ──────────────────────
    def _on_filter_click(self, key):
        self._activity_type_filter = key
        for k, btn in self._filter_buttons.items():
            is_active = (k == key)
            btn.configure(
                fg_color="#E8D5C4" if is_active else "transparent",
                text_color="#8B5E3C" if is_active else self.C["text_secondary"],
            )
        self._update_other_tree()

    # ── 交互 ──────────────────────
    def _on_card_click(self, page_key):
        if self.switch_page:
            self.switch_page(page_key)

    def _set_value(self, key, value):
        if key in self._value_labels:
            self._value_labels[key].configure(text=value)

    def _manual_refresh(self):
        self._load_data()

    def _auto_refresh(self):
        self._load_data()
        self.after(300000, self._auto_refresh)

    def _rebuild_kpi_cards(self):
        self._load_kpi_config()

    def refresh(self):
        self._rebuild_kpi_cards()
        self._load_data()
