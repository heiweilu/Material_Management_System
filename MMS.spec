# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包规格文件 — 物料管理系统
生成单目录发布包（one-folder）。
运行：pyinstaller MMS.spec
"""

from pathlib import Path

block_cipher = None
src_root = Path(SPECPATH)

# ── 隐式导入 ─────────────────────────────────────────────────────────
hidden_imports = [
    # PyQt6
    "PyQt6.QtWidgets",
    "PyQt6.QtCore",
    "PyQt6.QtGui",
    # SQLAlchemy
    "sqlalchemy.dialects.sqlite",
    "sqlalchemy.dialects.sqlite.pysqlite",
    # 第三方库
    "yaml",
    "openpyxl",
    "matplotlib",
    "matplotlib.backends.backend_qtagg",
    "matplotlib.backends.backend_agg",
    # 项目模块
    "src",
    "src.core",
    "src.db",
    "src.ui",
    "src.ui.pages",
    "src.ui.widgets",
    "src.ui.dialogs",
    "src.ui.theme",
]

# ── 数据文件 ─────────────────────────────────────────────────────────
datas = [
    (str(src_root / "src" / "ui" / "theme" / "style.qss"), "src/ui/theme"),
    (str(src_root / "src" / "ui" / "theme" / "dark.qss"),  "src/ui/theme"),
    (str(src_root / "config.example.yaml"), "."),
]

a = Analysis(
    [str(src_root / "main.py")],
    pathex=[str(src_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "pytest", "unittest", "_pytest",
        "nbformat", "notebook",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="物料管理系统",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon="assets/icon.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="物料管理系统",
)
