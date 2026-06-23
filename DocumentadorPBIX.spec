# -*- mode: python ; coding: utf-8 -*-
# Spec gerado para: Documentador de PBIX 1.0
# Build com: pyinstaller DocumentadorPBIX.spec

from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

# Coleta todos os dados e imports ocultos de reportlab e pbixray
datas_rl,    binaries_rl,    hiddenimports_rl    = collect_all('reportlab')
datas_pbix,  binaries_pbix,  hiddenimports_pbix  = collect_all('pbixray')
datas_pil,   binaries_pil,   hiddenimports_pil   = collect_all('PIL')
datas_gv,    binaries_gv,    hiddenimports_gv    = collect_all('graphviz')
datas_pd,    binaries_pd,    hiddenimports_pd    = collect_all('pandas')
datas_np,    binaries_np,    hiddenimports_np    = collect_all('numpy')

all_datas      = datas_rl + datas_pbix + datas_pil + datas_gv + datas_pd + datas_np
all_binaries   = binaries_rl + binaries_pbix + binaries_pil + binaries_gv + binaries_pd + binaries_np
all_hidden     = (
    hiddenimports_rl
    + hiddenimports_pbix
    + hiddenimports_pil
    + hiddenimports_gv
    + hiddenimports_pd
    + hiddenimports_np
    + [
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.colorchooser',
        'PIL._tkinter_finder',
        'PIL.ImageFont',
        'PIL.ImageDraw',
        'PIL.Image',
        'json',
        'threading',
        'tempfile',
        'zipfile',
        're',
        'math',
        'shutil',
    ]
)

a = Analysis(
    ['app.py'],
    pathex=['.'],
    binaries=all_binaries,
    datas=all_datas,
    hiddenimports=all_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'scipy', 'IPython', 'jupyter', 'PyQt5', 'PyQt6'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='DocumentadorPBIX',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # sem janela de terminal
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,              # coloque o caminho de um .ico aqui se quiser ícone personalizado
)
