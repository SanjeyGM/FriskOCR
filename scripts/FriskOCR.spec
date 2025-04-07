# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\SanjeyGM\\Desktop\\trying_build_app_1\\ocr_tool\\launcher.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\SanjeyGM\\Desktop\\trying_build_app_1\\ocr_tool\\main.py', '.')],
    hiddenimports=[],
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
    name='FriskOCR',
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
    uac_admin=True,
    icon=['C:\\Users\\SanjeyGM\\Desktop\\trying_build_app_1\\ocr_tool\\assets\\icon.ico'],
    manifest='C:\\Users\\SanjeyGM\\Desktop\\trying_build_app_1\\ocr_tool\\uac_manifest.manifest',
)
