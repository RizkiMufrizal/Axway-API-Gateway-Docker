# -*- mode: python -*-
a = Analysis(['src/compose.py'],
             pathex=['/opt/axway-compose'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='axway-compose',
          debug=False,
          strip=True,
          upx=True,
          console=True )
