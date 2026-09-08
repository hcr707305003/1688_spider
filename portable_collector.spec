# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


project_root = Path(SPECPATH)
app_icon = project_root / 'assets' / 'app-icon.ico'
common = dict(
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        (str(project_root / 'version.json'), '.'),
        (str(project_root / 'assets' / 'app-icon.ico'), 'assets'),
    ],
    hiddenimports=[
        'selenium.webdriver.chrome.webdriver',
        'selenium.webdriver.chrome.options',
        'selenium.webdriver.chrome.service',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['cv2', 'moviepy', 'tkinterweb', 'markdown', 'matplotlib'],
    noarchive=False,
    optimize=0,
)

gui_analysis = Analysis([str(project_root / 'collector_gui.pyw')], **common)
worker_analysis = Analysis([str(project_root / 'collector_worker.py')], **common)

gui_pyz = PYZ(gui_analysis.pure)
worker_pyz = PYZ(worker_analysis.pure)

gui_exe = EXE(
    gui_pyz,
    gui_analysis.scripts,
    [],
    exclude_binaries=True,
    name='1688商品采集工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    contents_directory='runtime',
    icon=str(app_icon),
)

worker_exe = EXE(
    worker_pyz,
    worker_analysis.scripts,
    [],
    exclude_binaries=True,
    name='_collector_worker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    contents_directory='runtime',
)

coll = COLLECT(
    gui_exe,
    worker_exe,
    gui_analysis.binaries,
    gui_analysis.datas,
    worker_analysis.binaries,
    worker_analysis.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='1688商品采集工具便携版',
)
