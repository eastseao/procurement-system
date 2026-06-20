"""
verify_icon.py - 验证 EXE 文件中的图标资源
读取 EXE 的 RT_GROUP_ICON 和 RT_ICON 资源，检查是否包含多尺寸图标。
用法: python verify_icon.py <exe_path>
"""
import sys
import os
import ctypes
import ctypes.wintypes
import struct

k32 = ctypes.WinDLL('kernel32', use_last_error=True)

# 常量
RT_ICON = 3
RT_GROUP_ICON = 14

# 函数原型
k32.LoadLibraryExW.argtypes = [ctypes.c_wchar_p, ctypes.c_void_p, ctypes.c_ulong]
k32.LoadLibraryExW.restype = ctypes.c_void_p

k32.FindResourceW.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
k32.FindResourceW.restype = ctypes.c_void_p

k32.SizeofResource.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
k32.SizeofResource.restype = ctypes.c_ulong

k32.LoadResource.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
k32.LoadResource.restype = ctypes.c_void_p

k32.LockResource.argtypes = [ctypes.c_void_p]
k32.LockResource.restype = ctypes.c_void_p

k32.FreeLibrary.argtypes = [ctypes.c_void_p]
k32.FreeLibrary.restype = ctypes.c_int

def MAKEINTRESOURCE(id):
    return ctypes.c_void_p(id)

def verify_icon(exe_path):
    # 以 LOAD_LIBRARY_AS_DATAFILE 方式加载 EXE
    LOAD_LIBRARY_AS_DATAFILE = 0x00000002
    hMod = k32.LoadLibraryExW(exe_path, None, LOAD_LIBRARY_AS_DATAFILE)
    if not hMod:
        raise Exception(f'LoadLibraryEx failed: {ctypes.GetLastError()}')
    
    try:
        # 查找 RT_GROUP_ICON 资源 (ID=1)
        hRes = k32.FindResourceW(hMod, MAKEINTRESOURCE(1), MAKEINTRESOURCE(RT_GROUP_ICON))
        if not hRes:
            print(f'ERROR: RT_GROUP_ICON (ID=1) 未找到！GetLastError={ctypes.GetLastError()}')
            return False
        
        size = k32.SizeofResource(hMod, hRes)
        print(f'RT_GROUP_ICON (ID=1): size={size} bytes')
        
        # 加载资源数据
        hData = k32.LoadResource(hMod, hRes)
        pData = k32.LockResource(hData)
        
        # 解析 GROUP_ICON 头
        header = ctypes.string_at(pData, 6)
        reserved, type_, count = struct.unpack('<HHH', header)
        print(f'  reserved={reserved}, type={type_}, count={count}')
        
        # 解析每个 ICON 条目 (GRPICONDIRENTRY = 14 bytes)
        # BYTE bWidth; BYTE bHeight; BYTE bColorCount; BYTE bReserved;
        # WORD wPlanes; WORD wBitCount; DWORD dwBytesInRes; WORD nID;
        fmt = '<BBBBHHIH'  # 1+1+1+1+2+2+4+2 = 14 bytes
        for i in range(count):
            offset = 6 + i * 14
            entry = ctypes.string_at(pData + offset, 14)
            bw, bh, color_count, reserved, planes, bit_count, bytes_in_res, nid = struct.unpack(fmt, entry)
            w = bw if bw != 0 else 256
            h = bh if bh != 0 else 256
            print(f'  [{i}] {w}x{h}  bytesInRes={bytes_in_res}  nID={nid}')
        
        # 检查 RT_ICON 资源
        print(f'\nRT_ICON 资源:')
        for i in range(1, count + 1):
            hRes = k32.FindResourceW(hMod, MAKEINTRESOURCE(i), MAKEINTRESOURCE(RT_ICON))
            if not hRes:
                print(f'  ID={i}: NOT FOUND (GetLastError={ctypes.GetLastError()})')
            else:
                size = k32.SizeofResource(hMod, hRes)
                print(f'  ID={i}: size={size} bytes ✓')
        
        return True
        
    finally:
        k32.FreeLibrary(hMod)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python verify_icon.py <exe_path>')
        sys.exit(1)
    
    exe_path = sys.argv[1]
    if not os.path.exists(exe_path):
        print(f'EXE not found: {exe_path}')
        sys.exit(1)
    
    print(f'Verifying: {exe_path}\n')
    success = verify_icon(exe_path)
    print(f'\nVerified: {"PASS" if success else "FAIL"}')
