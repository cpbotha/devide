from wxPython.py.wxd import wx_

hiddenimports = ['wxPython.py.wxd.%s' % (modName,) for
                 modName in wx_._topics.keys()]

print "[*] hook-startupImports.py - HIDDENIMPORTS"
print hiddenimports

