# PyInstaller spec for Telegram Media Downloader (PyQt6)
import os, glob
from PyInstaller.utils.hooks import collect_submodules

# Add icons and fonts if present
_datas = []
for name in ["app.ico","icon.ico","app.png","icon.png","telegram.ico","telegram.png"]:
    if os.path.exists(name):
        _datas.append((name, "."))
for pat in ["Kantumruy*.ttf","Kantumruy*.otf","kantumruy*.ttf","kantumruy*.otf"]:
    for fn in glob.glob(pat):
        _datas.append((fn, "."))

hidden = []
try:
    hidden += collect_submodules('PyQt6')
except Exception:
    pass
try:
    hidden += collect_submodules('telethon')
except Exception:
    pass
try:
    hidden += collect_submodules('qrcode')
except Exception:
    pass

block_cipher = None

a = Analysis(
    ['app_pyqt6.py'],
    pathex=[os.getcwd()],
    binaries=[],
    datas=_datas,
    hiddenimports=hidden,
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
    name='Telegram Media Downloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    disable_windowed_traceback=True,
    console=False,
    icon='icon.ico' if os.path.exists('icon.ico') else ( 'app.ico' if os.path.exists('app.ico') else None ),
)

coll = COLLECT(exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Telegram Media Downloader'
)
