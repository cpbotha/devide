# $Id: fixWxImports.py,v 1.1 2003/12/15 10:29:04 cpbotha Exp $

# This has to be imported BEFORE you do "import wx", else the McMillan
# installer won't know what to do with us.

# NB: also see installer/hooks/hook-startupImports.py !

# we also pre-import as much as possible of wxPython to make sure that the
# weird-assed wx renamer doesn't get to us.  The hook for this module also
# goes to some trouble to prevent the wx-renamer from biting our ass later.
from wxPython.wx import *
from wxPython.html import *
from wxPython.lib import *
from wxPython.py import *

# we're safe now due to all that crazy importing.  I hope.
import wx

