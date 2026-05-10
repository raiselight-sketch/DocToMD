# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[('/Users/raiselight/doctomd/.venv/lib/python3.14/site-packages/tkinterdnd2/tkdnd', 'tkinterdnd2/tkdnd')],
    hiddenimports=['markitdown', 'tkinterdnd2'],
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
    [],
    exclude_binaries=True,
    name='DocToMD',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['src/resources/icon.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DocToMD',
)
app = BUNDLE(
    coll,
    name='DocToMD.app',
    icon='src/resources/icon.icns',
    bundle_identifier='com.raiselight.doctomd',
    info_plist={
        'CFBundleShortVersionString': '1.0.1',
        'CFBundleVersion': '1.0.1',
        'NSAppleEventsUsageDescription': 'Pages 문서를 변환하기 위해 AppleScript 제어 권한이 필요합니다.',
    }
)
