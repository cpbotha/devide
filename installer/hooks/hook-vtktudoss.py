# so vtktudoss.py uses a list of names to construct the various imports
# at runtime, installer doesn't see this. :(

import os

if os.name == 'posix':
    hiddenimports = [
            'libvtktudossGraphicsPython',
            'libvtktudossWidgetsPython',
            'libvtktudossSTLibPython']
else:
    hiddenimports = [
            'vtktudossGraphicsPython',
            'vtktudossWidgetsPython',
            'vtktudossSTLibPython']

print "[*] hook-vtktudoss.py - HIDDENIMPORTS"
print hiddenimports
