# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

import cStringIO
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor
import wx

# wxPython 2.8.8.1 wx.aui bugs severely on GTK. See:
# http://trac.wxwidgets.org/ticket/9716
# Until this is fixed, use this PyAUI to which I've added a
# wx.aui compatibility layer.
if wx.Platform == "__WXGTK__":
    from external import PyAUI
    wx.aui = PyAUI
else:
    import wx.aui

# one could have loaded a wxGlade created resource like this:
#from resources.python import DICOMBrowserPanels
#reload(DICOMBrowserPanels)

class SkeletonAUIViewerFrame(wx.Frame):
    """wx.Frame child class used by SkeletonAUIViewer for its
    interface.

    This is an AUI-managed window, so we create the top-level frame,
    and then populate it with AUI panes.
    """

    def __init__(self, parent, id=-1, title="", name=""):
        wx.Frame.__init__(self, parent, id=id, title=title, 
                pos=wx.DefaultPosition, size=(800,800), name=name)


        self.menubar = wx.MenuBar()
        self.SetMenuBar(self.menubar)

        file_menu = wx.Menu()
        self.id_file_open = wx.NewId()
        file_menu.Append(self.id_file_open, "&Open\tCtrl-O",
                "Open a file", wx.ITEM_NORMAL)

        self.menubar.Append(file_menu, "&File")
       

        views_menu = wx.Menu()
        views_default_id = wx.NewId()
        views_menu.Append(views_default_id, "&Default\tCtrl-0",
                         "Activate default view layout.", wx.ITEM_NORMAL)
                

        views_max_image_id = wx.NewId()
        views_menu.Append(views_max_image_id, "&Maximum image size\tCtrl-1",
                         "Activate maximum image view size layout.", 
                         wx.ITEM_NORMAL)

        self.menubar.Append(views_menu, "&Views")



        # tell FrameManager to manage this frame        
        self._mgr = wx.aui.AuiManager()
        self._mgr.SetManagedWindow(self)

        self._mgr.AddPane(self._create_series_pane(), wx.aui.AuiPaneInfo().
                          Name("series").Caption("Series").Top().
                          BestSize(wx.Size(600, 100)).
                          CloseButton(False).MaximizeButton(True))

        self._mgr.AddPane(self._create_files_pane(), wx.aui.AuiPaneInfo().
                          Name("files").Caption("Image Files").
                          Left().
                          BestSize(wx.Size(200,400)).
                          CloseButton(False).MaximizeButton(True))

        self._mgr.AddPane(self._create_meta_pane(), wx.aui.AuiPaneInfo().
                          Name("meta").Caption("Image Metadata").
                          Left().
                          BestSize(wx.Size(200,400)).
                          CloseButton(False).MaximizeButton(True))

        self._mgr.AddPane(self._create_rwi_pane(), wx.aui.AuiPaneInfo().
                          Name("rwi").Caption("3D Renderer").
                          Center().
                          BestSize(wx.Size(400,400)).
                          CloseButton(False).MaximizeButton(True))



        self.SetMinSize(wx.Size(400, 300))

        # first we save this default perspective with all panes
        # visible
        self._perspectives = {} 
        self._perspectives['default'] = self._mgr.SavePerspective()

        # then we hide all of the panes except the renderer
        self._mgr.GetPane("series").Hide()
        self._mgr.GetPane("files").Hide()
        self._mgr.GetPane("meta").Hide()
        # save the perspective again
        self._perspectives['max_image'] = self._mgr.SavePerspective()

        # and put back the default perspective / view
        self._mgr.LoadPerspective(self._perspectives['default'])

        # finally tell the AUI manager to do everything that we've
        # asked
        self._mgr.Update()

        # we bind the views events here, because the functionality is
        # completely encapsulated in the frame and does not need to
        # round-trip to the DICOMBrowser main module.
        self.Bind(wx.EVT_MENU, self._handler_default_view, 
                id=views_default_id)

        self.Bind(wx.EVT_MENU, self._handler_max_image_view, 
                id=views_max_image_id)


    def close(self):
       self.Destroy()

    def _create_files_pane(self):
        sl = wx.ListCtrl(self, -1, 
                style=wx.LC_REPORT)
        sl.InsertColumn(0, "Full name")
        # we'll autosize this column later
        sl.SetColumnWidth(0, 300)

        #sl.InsertColumn(SeriesColumns.modality, "Modality")

        self.files_lc = sl

        return sl

    def _create_rwi_pane(self):

        panel = wx.Panel(self, -1)

        self.rwi = wxVTKRenderWindowInteractor(panel, -1, (400,400))
        self.button1 = wx.Button(panel, -1, "Add Superquadric")
        self.button2 = wx.Button(panel, -1, "Reset Camera")
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(self.button1)
        button_sizer.Add(self.button2)

        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer1.Add(self.rwi, 1, wx.EXPAND|wx.BOTTOM, 7)
        sizer1.Add(button_sizer)

        tl_sizer = wx.BoxSizer(wx.VERTICAL)
        tl_sizer.Add(sizer1, 1, wx.ALL|wx.EXPAND, 7)

        panel.SetSizer(tl_sizer)
        tl_sizer.Fit(panel)

        return panel

    def _create_meta_pane(self):
        ml = wx.ListCtrl(self, -1, 
                style=wx.LC_REPORT | 
                wx.LC_HRULES | wx.LC_VRULES |
                wx.LC_SINGLE_SEL)

        ml.InsertColumn(0, "Key")
        ml.SetColumnWidth(0, 70)

        ml.InsertColumn(1, "Value")
        ml.SetColumnWidth(1, 70)

        self.meta_lc = ml

        return ml

    def _create_series_pane(self):
        sl = wx.ListCtrl(self, -1, 
                style=wx.LC_REPORT | wx.LC_HRULES | wx.LC_SINGLE_SEL,
                size=(600,120))
        sl.InsertColumn(0, "Description")
        sl.SetColumnWidth(1, 170)

        sl.InsertColumn(2, "Modality")
        sl.InsertColumn(3, "# Images")
        sl.InsertColumn(4, "Size")

        self.series_lc = sl

        return sl

    def render(self):
        """Update embedded RWI, i.e. update the image.
        """
        self.rwi.Render()
       
    def _handler_default_view(self, event):
        """Event handler for when the user selects View | Default from
        the main menu.
        """
        self._mgr.LoadPerspective(
                self._perspectives['default'])

    def _handler_max_image_view(self, event):
        """Event handler for when the user selects View | Max Image
        from the main menu.
        """
        self._mgr.LoadPerspective(
            self._perspectives['max_image'])




