# EmphysemaViewerFrame by Corine Slagboom & Noeska Smit
# Description
#
# Based on SkeletonAUIViewerFrame:
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
class EmphysemaViewerFrame(wx.Frame):
    """wx.Frame child class used by Emphysemaviewer for its
    interface.

    This is an AUI-managed window, so we create the top-level frame,
    and then populate it with AUI panes.
    """

    def __init__(self, parent, id=-1, title="", name=""):
        """Populates the menu and adds all required panels
        """
        wx.Frame.__init__(self, parent, id=id, title=title, 
                pos=wx.DefaultPosition, size=(1000,875), name=name)


        self.menubar = wx.MenuBar()
        self.SetMenuBar(self.menubar)

        file_menu = wx.Menu()
        self.id_file_open = wx.NewId()
        self.id_mask_open = wx.NewId()
        file_menu.Append(self.id_file_open, "&Open Volume\tCtrl-O",
                "Open a volume", wx.ITEM_NORMAL)
        file_menu.Append(self.id_mask_open, "&Open Mask\tCtrl-M",
                "Open a mask", wx.ITEM_NORMAL)
        self.id_mask_save = wx.NewId()
        file_menu.Append(self.id_mask_save, "&Save\tCtrl-S",
                "Save file", wx.ITEM_NORMAL)

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

        self._mgr.AddPane(self._create_rwi_pane(), wx.aui.AuiPaneInfo().
                          Name("rwi").Caption("3D Renderer").
                          Center().
                          BestSize(wx.Size(600,800)).
                          CloseButton(False).MaximizeButton(True))

        self._mgr.AddPane(self._create_controls_pane(), wx.aui.AuiPaneInfo().
                          Name("controls").Caption("Controls").
                          Top().
                          BestSize(wx.Size(1000,75)).
                          CloseButton(False).MaximizeButton(True))

        self._mgr.AddPane(self._create_overlay_slices_pane(), wx.aui.AuiPaneInfo().
                          Name("overlay").Caption("Emphysema Overlay").
                          Right().
                          BestSize(wx.Size(400,400)).
                          CloseButton(False).MaximizeButton(True))

        self._mgr.AddPane(self._create_original_slices_pane(), wx.aui.AuiPaneInfo().
                          Name("original").Caption("Original Scan").
                          Right().
                          BestSize(wx.Size(400,400)).
                          CloseButton(False).MaximizeButton(True))

        self.SetMinSize(wx.Size(400, 300))

        # first we save this default perspective with all panes
        # visible
        self._perspectives = {} 
        self._perspectives['default'] = self._mgr.SavePerspective()

        # then we hide all of the panes except the renderer
        self._mgr.GetPane("controls").Hide()
        self._mgr.GetPane("overlay").Hide()
        self._mgr.GetPane("original").Hide()
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
                
        self.CreateStatusBar()
        self.SetStatusText("This is the statusbar ^^")




    def close(self):
        """Selfdestruct :)
        """
        self.Destroy()

    def _create_rwi_pane(self):
        """Create a RenderWindowInteractor panel
        """
        panel = wx.Panel(self, -1)

        self.rwi = wxVTKRenderWindowInteractor(panel, -1, (600,800))
        self.button1 = wx.Button(panel, -1, "Reset Camera")
        self.button2 = wx.Button(panel, -1, "Reset All")
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

    def _create_controls_pane(self):
        """Create a pane for the controls (containing the threshold sliders and buttons for 
        setting default or calculated values)
        """
        panel = wx.Panel(self, -1)

        self.upper_slider = wx.Slider(panel, -1, -950, -1100, -900, (0, 0), (300, 50),wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
        self.label = wx.StaticText(panel, -1, "Emfysema Threshold (HU)" , wx.Point(0, 0))
        self.label.SetForegroundColour(wx.Colour(127,0,255))
        self.lower_slider = wx.Slider(panel, -1, -970, -1100, -900, (0, 0), (300, 50),wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
        self.label2 = wx.StaticText(panel, -1, "Severe Emfysema Threshold (HU)" , wx.Point(0, 0))
        self.label2.SetForegroundColour(wx.Colour(255,0,0))
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.upper_slider)
        sizer.Add(self.label)

        sizer2 = wx.BoxSizer(wx.VERTICAL)
        sizer2.Add(self.lower_slider)
        sizer2.Add(self.label2)

        self.button5 = wx.Button(panel, -1, "-950 / -970 HU",pos=(8, 8), size=(175, 28))
        self.button6 = wx.Button(panel, -1, "12% / 10% Lowest HU",pos=(8, 8), size=(175, 28))
        button_sizer = wx.BoxSizer(wx.VERTICAL)
        button_sizer.Add(self.button5)
        button_sizer.Add(self.button6)


        slider_sizer = wx.BoxSizer(wx.HORIZONTAL)
        slider_sizer.Add(sizer)
        slider_sizer.Add(sizer2)
        slider_sizer.Add(button_sizer)

        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer1.Add(slider_sizer)

        tl_sizer = wx.BoxSizer(wx.VERTICAL)
        tl_sizer.Add(sizer1, 1, wx.ALL|wx.EXPAND, 7)

        panel.SetSizer(tl_sizer)
        tl_sizer.Fit(panel)

        return panel

    def _create_overlay_slices_pane(self):
        """Create a RenderWindowInteractor for the original data and added emphysema overlay
        """
        panel = wx.Panel(self, -1)

        self.overlay = wxVTKRenderWindowInteractor(panel, -1, (400,400))

        self.button3 = wx.Button(panel, -1, "Reset Camera")
        self.button4 = wx.Button(panel, -1, "Reset All")
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(self.button3)
        button_sizer.Add(self.button4)

        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer1.Add(self.overlay, 1, wx.EXPAND|wx.BOTTOM, 7)
        sizer1.Add(button_sizer)

        tl_sizer = wx.BoxSizer(wx.VERTICAL)
        tl_sizer.Add(sizer1, 1, wx.ALL|wx.EXPAND, 7)

        panel.SetSizer(tl_sizer)
        tl_sizer.Fit(panel)

        return panel

    def _create_original_slices_pane(self):
        """Create a RenderWindowInteractor for the original data and added emphysema overlay
        """
        panel = wx.Panel(self, -1)

        self.original = wxVTKRenderWindowInteractor(panel, -1, (400,400))

        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer1.Add(self.original, 1, wx.EXPAND|wx.BOTTOM, 7)


        tl_sizer = wx.BoxSizer(wx.VERTICAL)
        tl_sizer.Add(sizer1, 1, wx.ALL|wx.EXPAND, 7)

        panel.SetSizer(tl_sizer)
        tl_sizer.Fit(panel)

        return panel

    def render(self):
        """Update embedded RWI, i.e. update the image.
        """
        self.rwi.Render()
        self.overlay.Render()
        self.original.Render()
      
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




