# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets'), ('version.py', '.'), ('ui_utils.py', '.')],
    hiddenimports=[
        'pages.third_party_page',
        'ui_utils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # AI/ML 框架（项目完全不使用）
        'torch',
        'torchvision',
        'torchaudio',
        'scipy',
        'sklearn',
        'sympy',
        'transformers',
        'sentence_transformers',
        'onnxruntime',
        'faiss',
        'chromadb',
        'huggingface_hub',
        'tokenizers',
        'datasets',
        'accelerate',
        'safetensors',
        # 数据处理/可视化（项目不使用）
        'pandas',
        'seaborn',
        'reportlab',
        'python_pptx',
        'xlsxwriter',
        # Web/网络（项目不使用）
        'requests',
        'urllib3',
        'rich',
        'uvicorn',
        'websockets',
        'watchfiles',
        'yt_dlp',
        # 浏览器自动化（项目不使用）
        'playwright',
        # 容器编排（项目不使用）
        'kubernetes',
    ],
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
    icon=['assets\\同仁堂logo\\同仁堂企业LOGO_×256.ico'],
)
