# so vtktudoss.py uses a list of names to construct the various imports
# at runtime, installer doesn't see this. :(

import os

if os.name == 'posix':
    hiddenimports = ['libvtktudossGraphicsPython',
            'libvtktudossWidgetsPython']
else:
    hiddenimports = ['vtktudGraphicsPython',
            'vtktudWidgetsPython']

print "[*] hook-vtktudoss.py - HIDDENIMPORTS"
print hiddenimports
