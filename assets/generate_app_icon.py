#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成采购助手应用图标 — 专业蓝金配色，含16/24/32/48/256多尺寸"""

from PIL import Image, ImageDraw, ImageFont
import os, math

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_DIR = os.path.join(OUT_DIR, '采购助手logo')
os.makedirs(LOGO_DIR, exist_ok=True)

def draw_logo(size):
    """绘制采购助手图标 — 蓝色圆形+金色购物框+￥符号"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # 调色板
    BLUE_DARK = (25, 75, 145)    # 深蓝
    BLUE_MID = (35, 100, 185)    # 中蓝
    BLUE_LIGHT = (70, 140, 220)  # 浅蓝
    GOLD = (212, 175, 55)        # 金色
    GOLD_LIGHT = (232, 200, 85)  # 亮金
    WHITE = (255, 255, 255)

    # 根据尺寸计算比例
    cx, cy = size / 2, size / 2
    r_main = size * 0.46  # 主圆形半径

    # ── 1. 蓝色圆形背景（径向渐变模拟）──
    steps = 12
    for i in range(steps):
        rr = r_main * (1 - i / steps)
        t = i / steps
        color = (
            int(BLUE_LIGHT[0] * (1-t) + BLUE_DARK[0] * t),
            int(BLUE_LIGHT[1] * (1-t) + BLUE_DARK[1] * t),
            int(BLUE_LIGHT[2] * (1-t) + BLUE_DARK[2] * t),
            255
        )
        d.ellipse([cx-rr, cy-rr, cx+rr, cy+rr], fill=color)

    # ── 2. 金色内圆边框 ──
    border_w = max(1, int(size * 0.035))
    for i in range(border_w):
        rr = r_main - i
        d.ellipse([cx-rr, cy-rr, cx+rr, cy+rr], outline=GOLD)

    # ── 3. 购物箱/采购单图形 ──
    # 箱子尺寸（根据图标缩放）
    box_w = size * 0.42
    box_h = size * 0.30
    box_top = cy - box_h * 0.3
    box_left = cx - box_w / 2
    box_right = cx + box_w / 2
    box_bottom = box_top + box_h

    # 箱体（金色）
    # 侧面矩形（表示立体）
    d.polygon([
        (box_left, box_top + box_h * 0.3),
        (box_left, box_bottom),
        (box_right, box_bottom),
        (box_right, box_top + box_h * 0.3),
        (box_right - box_w * 0.1, box_top + box_h * 0.15),
        (box_left - box_w * 0.1, box_top + box_h * 0.15),
    ], fill=GOLD, outline=WHITE)

    # 箱盖（亮金）
    d.polygon([
        (box_left - box_w * 0.1, box_top + box_h * 0.15),
        (box_left, box_top),
        (box_right, box_top),
        (box_right - box_w * 0.1, box_top + box_h * 0.15),
    ], fill=GOLD_LIGHT, outline=WHITE)

    # 正面（亮金+￥符号）
    d.polygon([
        (box_left, box_top + box_h * 0.3),
        (box_right, box_top + box_h * 0.3),
        (box_right, box_bottom),
        (box_left, box_bottom),
    ], fill=GOLD_LIGHT)

    # 添加￥货币符号（白色）
    font_size = max(int(size * 0.18), 8)
    try:
        font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', font_size)
    except:
        try:
            font = ImageFont.truetype('DejaVuSans.ttf', font_size)
        except:
            font = ImageFont.load_default()

    yuan_text = '¥'
    try:
        bbox = d.textbbox((0, 0), yuan_text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
    except:
        tw, th = font.getsize(yuan_text)

    tx = cx - tw / 2
    ty = cy + box_h * 0.1 - th / 2
    # 在箱子正面绘制￥
    d.text((tx, ty), yuan_text, fill=BLUE_DARK, font=font)

    # ── 4. 顶部装饰小元素（星星/对勾，表示完成采购）──
    if size >= 32:
        check_cx = cx + box_w * 0.35
        check_cy = box_top - box_h * 0.1
        cr = max(size * 0.06, 2)
        # 小圆背景
        d.ellipse([check_cx-cr, check_cy-cr, check_cx+cr, check_cy+cr], fill=(46, 125, 50))
        # 对勾
        d.line([check_cx-cr*0.5, check_cy, check_cx-cr*0.15, check_cy+cr*0.45], fill=WHITE, width=max(1, int(size*0.012)))
        d.line([check_cx-cr*0.15, check_cy+cr*0.45, check_cx+cr*0.5, check_cy-cr*0.35], fill=WHITE, width=max(1, int(size*0.012)))

    # ── 5. 外边缘小高光（增强立体感）──
    if size >= 24:
        hl_box = [cx - r_main + border_w, cy - r_main + border_w,
                   cx - r_main * 0.5, cy - r_main * 0.3]
        d.ellipse(hl_box, fill=(255, 255, 255, 60))

    return img

# 生成各种尺寸
sizes = [16, 24, 32, 48, 256]
generated = []
for s in sizes:
    img = draw_logo(s)
    path = os.path.join(LOGO_DIR, f'采购助手logo_×{s}.png')
    img.save(path)
    generated.append((s, img))
    print(f'  ✅ {s}×{s} PNG  -> {os.path.basename(path)}')

# 生成 ICO（包含多种尺寸）
ico_path = os.path.join(OUT_DIR, 'app-icon.ico')
try:
    # 使用256尺寸作为基础，添加其他尺寸
    base_256 = draw_logo(256)
    sizes_for_ico = [16, 24, 32, 48, 64, 128, 256]
    img_list = []
    for s in sizes_for_ico:
        img_list.append(draw_logo(s))
    base_256.save(ico_path, format='ICO', sizes=[(s, s) for s in sizes_for_ico])
    print(f'  ✅ 多尺寸 ICO  -> {os.path.relpath(ico_path, OUT_DIR)}')
except Exception as e:
    print(f'  ⚠️ ICO生成失败: {e}')
    # 备用方案：分别生成单个尺寸ICO
    for s in sizes:
        img = draw_logo(s)
        p = os.path.join(LOGO_DIR, f'采购助手logo_×{s}.ico')
        img.save(p)
        print(f'  ✅ {s}×{s} ICO -> {os.path.basename(p)}')

print(f'\n🎉 采购助手图标已生成到: {LOGO_DIR}')
print(f'   主 ICO 文件: {ico_path}')
