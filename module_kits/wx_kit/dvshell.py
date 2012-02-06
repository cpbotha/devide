import wx
from wx import py

class DVShell(py.shell.Shell):
    """DeVIDE shell.

    Once again, PyCrust makes some pretty bad calls here and there.  With this
    override we fix some of them.

    1. passing locals=None will result in shell.Shell setting locals to
    __main__.__dict__ (!!) in contrast to the default behaviour of the Python
    code.InteractiveInterpreter , which is what we do here.
    """

    def __init__(self, parent, id=-1, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.CLIP_CHILDREN,
                 introText='', locals=None, InterpClass=None,
                 startupScript=None, execStartupScript=False,
                 *args, **kwds):

        # default behaviour for InteractiveInterpreter
        if locals is None:
            locals = {"__name__": "__console__", "__doc__": None}

        py.shell.Shell.__init__(self, parent, id, pos,
                                size, style,
                                introText, locals, InterpClass,
                                startupScript, execStartupScript,
                                *args, **kwds)
