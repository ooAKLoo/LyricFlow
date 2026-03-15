# PyInstaller spec for LyricFlow sidecar
# Build: pyinstaller lyricflow-sidecar.spec

import os
import sys

block_cipher = None
backend_dir = os.path.join(os.path.dirname(os.path.abspath(SPECPATH)), 'backend')

a = Analysis(
    ['main.py'],
    pathex=[backend_dir],
    binaries=[],
    datas=[
        (os.path.join(backend_dir, 'data', 'slang_dict.json'), 'data'),
        (os.path.join(backend_dir, 'data', 'weak_forms.json'), 'data'),
    ],
    hiddenimports=[
        'pipeline.stage1_preprocess',
        'pipeline.stage2_lyrics',
        'pipeline.stage3_alignment',
        'pipeline.stage4_phonetics',
        'pipeline.stage5_detection',
        'pipeline.stage6_output',
        'engine.rules.linking',
        'engine.rules.weak_forms',
        'engine.rules.elision',
        'engine.rules.constants',
        'engine.audio_verify',
        'engine.lyrics_parser',
        'engine.rap_optimizer',
        'librosa',
        'soundfile',
        'noisereduce',
        'mutagen',
        'nltk',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['whisper', 'spleeter', 'torch', 'tensorflow'],
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
    name='lyricflow-sidecar',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    console=True,  # Must be console app for stdin/stdout
    target_arch=None,
)
