# -*- mode: python ; coding: utf-8 -*-


added_files = [
    ('python', 'python'),
    ('.venv/Lib/site-packages/gradio', 'gradio'),
    ('.venv/Lib/site-packages/safehttpx', 'safehttpx'),
    ('.venv/Lib/site-packages/groovy', 'groovy')
]

a = Analysis(
    ['python\\app.py'],
    pathex=['python'],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'brain',
        'state_manager',
        'comfy_client',
        'memory_manager',
        'config',
        'encryption',
        'config_manager',
        'ui_components',
        'game_initializer',
        'ui_builder',
        'logic_engine',
    ],
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
    name='app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
