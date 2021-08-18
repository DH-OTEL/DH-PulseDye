# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['SerialPlotting.py'],
             pathex=['C:\\Users\\scott\\OneDrive\\Documents\\Python_Scripts\\Dye_Densitometer_GUI\\v1_2_0'],
             binaries=[],
             datas=[('AIF_Processing\\hemoglobin.dat', '.'), ('AIF_Processing\\icg.dat', '.'), ('AIF_Processing\\newwater.dat', '.')],
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,  
          [],
          name='SerialPlotting',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None , icon='Icons\\program_icon.ico')
