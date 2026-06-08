# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = ['openpyxl', 'openpyxl.styles', 'openpyxl.utils', 'openpyxl.drawing.image',
              'PIL', 'PIL.Image', 'PIL.ImageTk', 'PIL.ImageDraw',
              'pystray', 'pystray._win32']

# 打包所有图片资源（图标 + Logo + 侧边栏图标 + 模板）
datas += [
    ('assets/同仁堂企业LOGO2.ico', 'assets'),
    ('assets/icon_collapse.png', 'assets'),
    ('assets/icon_expand.png', 'assets'),
    ('assets/logo_40x40.png', 'assets'),
    ('assets/产品包装报价单_模板.xlsx', 'assets'),
    # 导航栏图标
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
]

# customtkinter 及其依赖
tmp_ret = collect_all('customtkinter')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('darkdetect')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='采购助手',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/同仁堂企业LOGO2.ico',
)
