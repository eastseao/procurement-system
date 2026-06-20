"""
inject_icon.py - 用 Windows API 向 EXE 写入多尺寸 ICO 图标
绕过 rcedit，直接调用 kernel32.dll 的 UpdateResource API
用法: python inject_icon.py <exe_path> <ico_path>
"""
import struct
import sys
import os
import ctypes
import ctypes.wintypes

# 加载 kernel32
k32 = ctypes.WinDLL('kernel32', use_last_error=True)

# 常量
RT_ICON = 3
RT_GROUP_ICON = 14

# 设置函数原型
k32.BeginUpdateResourceW.argtypes = [ctypes.c_wchar_p, ctypes.c_bool]
k32.BeginUpdateResourceW.restype = ctypes.c_void_p

k32.UpdateResourceW.argtypes = [
    ctypes.c_void_p,   # hUpdate
    ctypes.c_void_p,   # lpType  (INTRESOURCE)
    ctypes.c_void_p,   # lpName  (INTRESOURCE)
    ctypes.c_ushort,   # wLanguage
    ctypes.c_void_p,   # lpData
    ctypes.c_ulong      # cbData
]
k32.UpdateResourceW.restype = ctypes.c_int

k32.EndUpdateResourceW.argtypes = [ctypes.c_void_p, ctypes.c_bool]
k32.EndUpdateResourceW.restype = ctypes.c_int

def MAKEINTRESOURCE(id):
    """把整数资源 ID 转为 LPTSTR（高位0，低位=id）"""
    return ctypes.c_void_p(id)

def read_ico(ico_path):
    """读取 ICO 文件，返回 [(width, height, bpp, data), ...]"""
    with open(ico_path, 'rb') as f:
        data = f.read()
    if data[:4] != b'\x00\x00\x01\x00':
        raise Exception('Not a valid ICO file')
    num = struct.unpack('<H', data[4:6])[0]
    entries = []
    for i in range(num):
        off = 6 + i * 16
        w = data[off]
        h = data[off+1]
        bpp = data[off+6]
        size = struct.unpack('<I', data[off+8:off+12])[0]
        offset = struct.unpack('<I', data[off+12:off+16])[0]
        w = w if w != 0 else 256
        h = h if h != 0 else 256
        ico_data = data[offset:offset+size]
        entries.append((w, h, bpp, ico_data))
    return entries

def build_group_icon(entries):
    """
    构建 RT_GROUP_ICON 数据（GRPICONDIR + GRPICONDIRENTRY）
    RT_GROUP_ICON 只包含目录结构，不包含实际图标数据。
    实际图标数据在各自的 RT_ICON 资源中。
    """
    buf = bytearray()
    # 头部: reserved(2) + type(2) + count(2)
    buf += struct.pack('<HHH', 0, 1, len(entries))
    # 每个图标对应 14 字节的 GRPICONDIRENTRY
    for i, (w, h, bpp, d) in enumerate(entries):
        bw = w if w < 256 else 0
        bh = h if h < 256 else 0
        # GRPICONDIRENTRY 结构 (14 bytes):
        # BYTE   bWidth;
        # BYTE   bHeight;
        # BYTE   bColorCount;
        # BYTE   bReserved;
        # WORD   wPlanes;
        # WORD   wBitCount;
        # DWORD  dwBytesInRes;  (对应 RT_ICON 资源的大小)
        # WORD   nID;           (对应 RT_ICON 资源的 ID)
        buf += struct.pack(
            '<BBBBHHIH',
            bw,            # width  (0 表示 256)
            bh,            # height (0 表示 256)
            0,              # colorCount (0 = 使用调色板)
            0,              # reserved
            1,              # planes
            32,             # bitCount
            len(d),        # bytesInRes (RT_ICON 资源的大小)
            i + 1          # nID (RT_ICON 资源的 ID)
        )
    return bytes(buf)

def inject_icon(exe_path, ico_path):
    """向 EXE 文件写入图标资源"""
    entries = read_ico(ico_path)
    print(f'Read {len(entries)} icon entries from {ico_path}')
    for i, (w, h, bpp, d) in enumerate(entries):
        fmt = 'PNG' if d[:4] == b'\x89PNG' else 'DIB'
        print(f'  [{i}] {w}x{h} bpp={bpp} size={len(d)} fmt={fmt}')

    # 1. 开始更新资源
    hUpdate = k32.BeginUpdateResourceW(exe_path, False)
    if not hUpdate:  # NULL = 失败
        raise Exception(f'BeginUpdateResource failed: {ctypes.GetLastError()}')
    print(f'BeginUpdateResource OK, hUpdate={hUpdate}')

    try:
        # 2. 删除现有的 RT_GROUP_ICON (ID=1) 和 RT_ICON (ID=1..N)
        # 删除 RT_GROUP_ICON
        ret = k32.UpdateResourceW(
            hUpdate,
            MAKEINTRESOURCE(RT_GROUP_ICON),
            MAKEINTRESOURCE(1),
            0,
            None,
            0
        )
        if not ret:
            err = ctypes.GetLastError()
            if err != 1812:  # ERROR_NOT_FOUND - 资源不存在也算正常
                print(f'Warning: could not delete RT_GROUP_ICON: {err}')

        # 删除可能的 RT_ICON resources
        for i in range(1, 50):
            ret = k32.UpdateResourceW(
                hUpdate,
                MAKEINTRESOURCE(RT_ICON),
                MAKEINTRESOURCE(i),
                0,
                None,
                0
            )
            if not ret:
                if ctypes.GetLastError() == 1812:  # not found, skip
                    pass

        # 3. 写入新的 RT_ICON 资源（每个尺寸一个）
        for i, (w, h, bpp, d) in enumerate(entries):
            icon_id = i + 1
            # 用 create_string_buffer 创建数据缓冲区
            buf = ctypes.create_string_buffer(d)
            # 获取指向缓冲区的指针
            data_ptr = ctypes.cast(buf, ctypes.c_void_p)
            ok = k32.UpdateResourceW(
                hUpdate,
                MAKEINTRESOURCE(RT_ICON),
                MAKEINTRESOURCE(icon_id),
                0,
                data_ptr,
                len(d)
            )
            if not ok:
                raise Exception(f'UpdateResource RT_ICON {icon_id} failed: {ctypes.GetLastError()}')
            print(f'  Written RT_ICON ID={icon_id} ({w}x{h})')

        # 4. 构建并写入 RT_GROUP_ICON 资源
        group_data = build_group_icon(entries)
        group_buf = ctypes.create_string_buffer(group_data)
        group_ptr = ctypes.cast(group_buf, ctypes.c_void_p)
        ok = k32.UpdateResourceW(
            hUpdate,
            MAKEINTRESOURCE(RT_GROUP_ICON),
            MAKEINTRESOURCE(1),
            0,
            group_ptr,
            len(group_data)
        )
        if not ok:
            raise Exception(f'UpdateResource RT_GROUP_ICON failed: {ctypes.GetLastError()}')
        print(f'  Written RT_GROUP_ICON ({len(entries)} icons)')

        # 5. 提交资源更新
        ok = k32.EndUpdateResourceW(hUpdate, False)
        if not ok:
            raise Exception(f'EndUpdateResource failed: {ctypes.GetLastError()}')
        hUpdate = None
        print(f'Icon injected successfully!')

    finally:
        if hUpdate:
            # 放弃更新
            k32.EndUpdateResourceW(hUpdate, True)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python inject_icon.py <exe_path> <ico_path>')
        sys.exit(1)

    exe_path = sys.argv[1]
    ico_path = sys.argv[2]

    if not os.path.exists(exe_path):
        print(f'EXE not found: {exe_path}')
        sys.exit(1)
    if not os.path.exists(ico_path):
        print(f'ICO not found: {ico_path}')
        sys.exit(1)

    inject_icon(exe_path, ico_path)
    print('Done!')
