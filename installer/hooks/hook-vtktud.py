# so vtktud.py uses a list of names to construct the various imports
# at runtime, installer doesn't see this. :(

import os

if os.name == 'posix':
    hiddenimports = ['libvtktudCommonPython',
            'libvtktudImagingPython', 'libvtktudGraphicsPython',
            'libvtktudWidgetsPython']
else:
    hiddenimports = ['vtktudCommonPython',
            'vtktudImagingPython', 'vtktudGraphicsPython',
            'vtktudWidgetsPython']

print "[*] hook-vtktud.py - HIDDENIMPORTS"
print hiddenimports
