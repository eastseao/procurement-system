#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成采购助手应用图标 — 多尺寸PNG + 合并ICO（16/32/48/64/128/256）"""

from PIL import Image, ImageDraw, ImageFont
import os, math

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_DIR = os.path.join(OUT_DIR, '采购助手logo')
os.makedirs(LOGO_DIR, exist_ok=True)

def draw_logo_on_canvas(size):
    """在 size×size 画布上绘制图标 — 蓝色圆形+金色购物箱+￥符号"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # 调色板
    BLUE_DARK = (25, 75, 145, 255)
    BLUE_MID = (35, 100, 185, 255)
    BLUE_LIGHT = (70, 140, 220, 255)
    GOLD = (212, 175, 55, 255)
    GOLD_LIGHT = (232, 200, 85, 255)
    WHITE = (255, 255, 255, 255)
    GREEN = (46, 125, 50, 255)

    cx, cy = size / 2, size / 2
    r_main = size * 0.46

    # 1. 径向渐变的蓝色圆形背景（多层椭圆叠加）
    steps = 14
    for i in range(steps):
        rr = r_main * (1 - i / steps)
        t = i / steps
        color = (
            int(BLUE_LIGHT[0] * (1-t) + BLUE_DARK[0] * t),
            int(BLUE_LIGHT[1] * (1-t) + BLUE_DARK[1] * t),
            int(BLUE_LIGHT[2] * (1-t) + BLUE_DARK[2] * t),
            255
        )
        bbox = [cx-rr, cy-rr, cx+rr, cy+rr]
        d.ellipse(bbox, fill=color)

    # 2. 金色外圈边框
    border_w = max(1, int(size * 0.04))
    for i in range(border_w):
        rr = r_main - i
        d.ellipse([cx-rr, cy-rr, cx+rr, cy+rr], outline=GOLD)

    # 3. 购物箱（立体透视效果）
    box_w = size * 0.36
    box_h = size * 0.26
    box_top = cy - box_h * 0.15
    box_left = cx - box_w / 2
    box_right = cx + box_w / 2
    box_bottom = box_top + box_h

    # 箱子正面（亮金）
    d.polygon([
        (box_left, box_top + box_h * 0.3),
        (box_right, box_top + box_h * 0.3),
        (box_right, box_bottom),
        (box_left, box_bottom),
    ], fill=GOLD_LIGHT)

    # 顶部（更深的金色，体现立体感）
    top_left = (box_left - box_w * 0.12, box_top + box_h * 0.15)
    top_right = (box_right, box_top + box_h * 0.15)
    d.polygon([
        top_left,
        (box_left, box_top),
        (box_right, box_top),
        top_right,
    ], fill=GOLD)

    # 左侧面（深色金，阴影）
    GOLD_DARK = (170, 140, 40, 255)
    d.polygon([
        top_left,
        (box_left, box_top),
        (box_left, box_bottom),
        (box_left - box_w * 0.12, box_bottom - box_h * 0.15),
    ], fill=GOLD_DARK)

    # 4. ￥ 符号（白色，在箱子正面中央）
    yuan_font_size = max(int(size * 0.18), 8)
    yuan = '¥'
    try:
        font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', yuan_font_size)
    except:
        try:
            font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', yuan_font_size)
        except:
            font = ImageFont.load_default()

    try:
        bbox = d.textbbox((0, 0), yuan, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
    except:
        tw, th = font.getsize(yuan)

    tx = cx - tw / 2
    ty = cy + box_h * 0.25 - th / 2
    d.text((tx, ty), yuan, fill=WHITE, font=font)

    # 5. 右上角绿色对勾（≥32px 才显示，避免小尺寸混乱）
    if size >= 32:
        check_cx = cx + box_w * 0.55
        check_cy = box_top - box_h * 0.2
        cr = max(size * 0.08, 2)
        d.ellipse([check_cx-cr, check_cy-cr, check_cx+cr, check_cy+cr], fill=GREEN)
        d.ellipse([check_cx-cr, check_cy-cr, check_cx+cr, check_cy+cr], outline=GOLD)
        # 白色对勾（在绿色圆内）
        hook_w = max(1, int(size * 0.015))
        d.line([check_cx-cr*0.4, check_cy, check_cx-cr*0.1, check_cy+cr*0.4], fill=WHITE, width=hook_w)
        d.line([check_cx-cr*0.1, check_cy+cr*0.4, check_cx+cr*0.5, check_cy-cr*0.35], fill=WHITE, width=hook_w)

    # 6. 外边缘高光（增强立体感，≥48px）
    if size >= 48:
        highlight_box = [
            cx - r_main * 0.85, cy - r_main * 0.85,
            cx - r_main * 0.25, cy - r_main * 0.25
        ]
        # 用半透明白色椭圆做高光
        hi = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        hid = ImageDraw.Draw(hi)
        hid.ellipse(highlight_box, fill=(255, 255, 255, 60))
        img = Image.alpha_composite(img, hi)
        d = ImageDraw.Draw(img)

    return img

# ── 生成各尺寸 PNG ──
sizes = [16, 24, 32, 48, 64, 128, 256]
images = []
for s in sizes:
    img = draw_logo_on_canvas(s)
    png_path = os.path.join(LOGO_DIR, f'采购助手logo_{s}x{s}.png')
    img.save(png_path, 'PNG')
    images.append(img)
    print(f'  ✅ {s}x{s} PNG')

# ── 生成合并 ICO（关键：使用 PIL 的 native ICO 保存方式，正确嵌入多尺寸）──
ico_path = os.path.join(OUT_DIR, 'app-icon.ico')
# 以 256 为主图，附带其他尺寸
try:
    # Pillow >= 9.0 支持 sizes 参数
    images[6].save(ico_path, format='ICO', sizes=[(s, s) for s in sizes], optimize=False)
except TypeError:
    # 老版本 Pillow 兼容写法
    images[6].save(ico_path, format='ICO', sizes=[(s, s) for s in sizes])

# 验证 ICO 中的尺寸数量
try:
    test = Image.open(ico_path)
    size_list = []
    i = 0
    while True:
        try:
            test.seek(i)
            size_list.append(f'{test.size[0]}x{test.size[1]}')
            i += 1
        except EOFError:
            break
    print(f'  ✅ ICO 文件: {os.path.basename(ico_path)}')
    print(f'  ✅ 嵌入尺寸: {", ".join(size_list)}')
    print(f'  ✅ 文件大小: {os.path.getsize(ico_path)} 字节')
except Exception as e:
    print(f'  ⚠️  ICO 验证失败: {e}')

print(f'\n🎉 完成！图标生成目录: {LOGO_DIR}')
print(f'🎉 主 ICO: {ico_path}')
