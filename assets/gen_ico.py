"""
生成符合Windows标准的多尺寸ICO文件。
小尺寸 (16/24/32/48/64) → BMP/DIB格式  (Windows Explorer/Taskbar 必须)
大尺寸 (128/256)        → PNG压缩格式

运行: python assets/gen_ico.py
"""
import struct
import io
import os
from PIL import Image

SRC = os.path.join(os.path.dirname(__file__), 'icon', 'app-icon-256x256.png')
DST = os.path.join(os.path.dirname(__file__), 'icon', 'app-icon-multi.ico')

# 规格: (size, use_png)
SIZES = [
    (16,  False),
    (24,  False),
    (32,  False),
    (48,  False),
    (64,  False),
    (128, True),
    (256, True),
]

def make_dib(img: Image.Image) -> bytes:
    """将RGBA图像转为ICO内嵌的DIB数据（带AND mask的BMP，无文件头）"""
    w, h = img.size
    # 确保像素数据按行4字节对齐
    row_bytes = w * 4  # 32bpp BGRA，每行 w*4 字节，已对齐

    buf = io.BytesIO()
    # BITMAPINFOHEADER (40 bytes)
    buf.write(struct.pack('<IiiHHIIiiII',
        40,       # biSize
        w,        # biWidth
        h * 2,    # biHeight: 正值 = bottom-up；ICO中高度是实际高度的2倍
        1,        # biPlanes
        32,       # biBitCount
        0,        # biCompression = BI_RGB
        0,        # biSizeImage (可以为0)
        0, 0,     # biXPelsPerMeter, biYPelsPerMeter
        0, 0,     # biClrUsed, biClrImportant
    ))
    # 像素数据：bottom-up，BGRA
    pixels = img.load()
    for y in range(h - 1, -1, -1):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            buf.write(bytes([b, g, r, a]))
    # AND mask：每行按32位对齐，全0（透明通道已在BGRA的alpha中）
    mask_row_bits = w
    mask_row_bytes = ((mask_row_bits + 31) // 32) * 4
    for _ in range(h):
        buf.write(b'\x00' * mask_row_bytes)
    return buf.getvalue()

def make_png(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format='PNG', optimize=True)
    return buf.getvalue()

def main():
    if not os.path.exists(SRC):
        print(f'ERROR: 源文件不存在: {SRC}')
        return

    base = Image.open(SRC).convert('RGBA')
    print(f'源图像: {base.size[0]}x{base.size[1]} {base.mode}')

    entries = []
    for size, use_png in SIZES:
        img = base.resize((size, size), Image.LANCZOS)
        if use_png:
            data = make_png(img)
            fmt = 'PNG'
        else:
            data = make_dib(img)
            fmt = 'DIB'
        entries.append((size, data, fmt))
        print(f'  {size:3d}x{size:<3d}  {fmt}  {len(data):>8d} bytes')

    # 写ICO
    n = len(entries)
    dir_offset = 6 + n * 16
    data_offset = dir_offset

    with open(DST, 'wb') as f:
        # ICO文件头
        f.write(struct.pack('<HHH', 0, 1, n))
        # 目录
        offsets = []
        cur = data_offset
        for size, data, _ in entries:
            w = size if size < 256 else 0
            h = size if size < 256 else 0
            f.write(struct.pack('<BBBBHHII',
                w, h,   # 宽高（0=256）
                0,      # colorCount
                0,      # reserved
                1,      # planes
                32,     # bitCount
                len(data),
                cur,
            ))
            offsets.append(cur)
            cur += len(data)
        # 数据
        for size, data, _ in entries:
            f.write(data)

    print(f'\nDone: {DST}  ({os.path.getsize(DST)} bytes, {n} icons)')

if __name__ == '__main__':
    main()
