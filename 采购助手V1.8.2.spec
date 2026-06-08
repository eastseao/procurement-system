# -*- mode: python ; coding: utf-8 -*-
# 采购助手 V1.8.2 - PyInstaller打包配置
import sys
from pathlib import Path

block_cipher = None

# 需要打包的资源文件
added_files = [
    ('assets/logo_40x40.png', 'assets'),
    ('assets/同仁堂企业LOGO.png', 'assets'),
    ('assets/icon_collapse.png', 'assets'),
    ('assets/icon_expand.png', 'assets'),
    ('assets/同仁堂集团组织架构3.0.html', 'assets'),
    ('assets/产品包装报价单_模板.xlsx', 'assets'),
    ('assets/avatar.png', 'assets'),
    ('assets/wx.png', 'assets'),
    ('assets/nav_dashboard.png', 'assets'),
    ('assets/nav_packaging.png', 'assets'),
    ('assets/nav_quotation.png', 'assets'),
    ('assets/nav_query.png', 'assets'),
    ('assets/nav_supplier.png', 'assets'),
    ('assets/nav_collection.png', 'assets'),
    ('assets/nav_purchase.png', 'assets'),
    ('assets/nav_travel.png', 'assets'),
    ('assets/nav_memo.png', 'assets'),
    ('assets/nav_settings.png', 'assets'),
    ('pages', 'pages'),
    ('version.py', '.'),
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'pystray', 'PIL', 'PIL._tkinter_finder',
        'customtkinter', 'tkinter', 'tkinter.messagebox',
        'ctypes', 'ssl', 'json', 'urllib', 'os', 're',
        'threading', 'webbrowser', 'datetime',
        'openpyxl', 'sqlite3',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ProcurementAssistant-V1.8.2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/同仁堂企业LOGO.ico',
)
