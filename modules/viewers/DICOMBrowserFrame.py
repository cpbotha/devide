# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

import wx
import wx.aui
# need listmix.ColumnSorterMixin
import wx.lib.mixins.listctrl as listmix

from resources.python import DICOMBrowserPanels
reload(DICOMBrowserPanels)

class SortedListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin, listmix.ColumnSorterMixin):

    def __init__(self, parent, ID, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        
        # for the ColumnSorterMixin: this should be a dict mapping
        # from item data values to sequence of values for the columns.
        # These values will be used for sorting
        self.itemDataMap = {}

        listmix.ColumnSorterMixin.__init__(self, 5)

    def GetListCtrl(self):
        """Method required by ColumnSorterMixin.
        """
        return self

class DICOMBrowserFrame(wx.Frame):
    def __init__(self, parent, id=-1, title="", name=""):
        wx.Frame.__init__(self, parent, id=id, title=title, 
                pos=wx.DefaultPosition, size=(800,600), name=name)

        # tell FrameManager to manage this frame        
        self._mgr = wx.aui.AuiManager()
        self._mgr.SetManagedWindow(self)
        
        self._mgr.AddPane(self._create_files_pane(), wx.aui.AuiPaneInfo().
                          Name("files").
                          Caption("Files and Directories").Top().
                          Row(1).
                          CloseButton(False).MaximizeButton(True))

        self._mgr.AddPane(self._create_studies_pane(), wx.aui.AuiPaneInfo().
                          Name("studies").Caption("Studies").Top().Row(2).
                          CloseButton(False).MaximizeButton(True))

        self._mgr.AddPane(self._create_series_pane(), wx.aui.AuiPaneInfo().
                          Name("series").Caption("Series").Top().Row(3).
                          CloseButton(False).MaximizeButton(True))


        self._perspectives = []

        self.SetMinSize(wx.Size(400, 300))

        self._mgr.Update()

    def close(self):
        self.Destroy()

    def _create_files_pane(self):
        # instantiate the wxGlade-created frame
        fpf = DICOMBrowserPanels.FilesPanelFrame(self, id=-1)
        # reparent the panel to us
        panel = fpf.files_panel
        panel.Reparent(self)

        # still need fpf.* to bind everything
        # but we can destroy fpf (everything has been reparented)
        fpf.Destroy()

        panel.ad_button = fpf.ad_button
        panel.scan_button = fpf.scan_button
        panel.dirs_files_lb = fpf.dirs_files_lb
        self.files_pane = panel

        return panel

    def _create_studies_pane(self):
        sl = SortedListCtrl(self, -1, style=wx.LC_REPORT)
        sl.InsertColumn(0, "Patient")
        sl.InsertColumn(1, "Description") # study description
        sl.InsertColumn(2, "Date") # study date
        sl.InsertColumn(3, "Images") # total number of images
        sl.InsertColumn(4, "Series") # number of series

        return sl

    def _create_series_pane(self):
        sl = SortedListCtrl(self, -1, style=wx.LC_REPORT)
        sl.InsertColumn(0, "Description")
        sl.InsertColumn(1, "Modality")
        sl.InsertColumn(2, "Images")

        return sl
       


