# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

import wx

def get_system_font_size():
    ft = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT)
    return ft.GetPointSize()

def create_html_font_size_array():
    """Based on the system font size, return a 7-element font-size
    array that can be used to SetFont() on a wxHtml.

    For system font size 8, this should be:
    [4,6,8,10,12,14,16]
    corresponding with HTML sizes -2 to +4
    """

    sfs = get_system_font_size()

    fsa = [0,0,0,0,0,0,0]
    for i in range(7):
        fsa[i] = sfs - (i-2)*2

    return fsa

