# shared.py copyright (c) 2003 Charl P. Botha <cpbotha@ieee.org>
# $Id: shared.py,v 1.1 2003/09/15 11:55:30 cpbotha Exp $
#

import wx

class s3dcGridMixin(object):
    """
    """
    
    def _handlerGridRangeSelect(self, event):
        """This event handler is a fix for the fact that the row
        selection in the wxGrid is deliberately broken.  It's also
        used to activate and deactivate relevant menubar items.
        
        Whenever a user clicks on a cell, the grid SHOWS its row
        to be selected, but GetSelectedRows() doesn't think so.
        This event handler will travel through the Selected Blocks
        and make sure the correct rows are actually selected.
        
        Strangely enough, this event always gets called, but the
        selection is empty when the user has EXPLICITLY selected
        rows.  This is not a problem, as then the GetSelectedRows()
        does return the correct information.
        """
            
        # both of these are lists of (row, column) tuples
        tl = self._grid.GetSelectionBlockTopLeft()
        br = self._grid.GetSelectionBlockBottomRight()
        for (tlrow, tlcolumn), (brrow, brcolumn) in zip(tl, br):
            for row in range(tlrow,brrow + 1):
                self._grid.SelectRow(row, True)

        if self._grid.GetSelectedRows():
            for mi in self._disableMenuItems:
                mi.Enable(True)
        else:
            for mi in self._disableMenuItems:
                mi.Enable(False)

    def _appendGridCommandsTupleToMenu(self, menu, eventWidget,
                                       commandsTuple, disable=True):
        """Appends the slice grid commands to a menu.  This can be used
        to build up the context menu or the drop-down one.
        """

        disableList = []
        for command in commandsTuple:
            if command[0] == '---':
                mi = wx.MenuItem(menu, wx.ID_SEPARATOR)
                menu.AppendItem(mi)
            else:
                id = wx.NewId()
                mi = wx.MenuItem(
                    menu, id, command[0], command[1])
                menu.AppendItem(mi)
                wx.EVT_MENU(
                    eventWidget, id, command[2])
                
                if disable and not self._grid.GetSelectedRows() and command[3]:
                    mi.Enable(False)

                if command[3]:
                    disableList.append(mi)

        # the disableList can be used later if the menu is created for use
        # in the frame menubar
        return disableList
        
