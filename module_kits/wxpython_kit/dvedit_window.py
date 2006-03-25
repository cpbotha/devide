import wx
from wx import py

class DVEditWindow(py.editwindow.EditWindow):

    """DeVIDE EditWindow.

    This fixes all of the otherwise useful py screwups with providing a
    re-usable Python EditWindow component.
    """

    def __init__(self, editor, parent, id=-1, pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 style=wx.CLIP_CHILDREN | wx.SUNKEN_BORDER):

        py.editwindow.EditWindow(self, parent, id, pos, size, style)
