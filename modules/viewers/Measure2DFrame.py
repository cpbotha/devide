import vtk
import wx


from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor
import external.PyAUI as PyAUI

from resources.python import measure2d_panels
reload(measure2d_panels)

class Measure2DFrame(wx.Frame):
    def __init__(self, parent, id=-1, title="", pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE |
                                            wx.SUNKEN_BORDER |
                                            wx.CLIP_CHILDREN, name="frame"):

        wx.Frame.__init__(self, parent, id, title, pos, size, style, name)
        
        # tell FrameManager to manage this frame        
        self._mgr = PyAUI.FrameManager()
        self._mgr.SetFrame(self)

        self._make_menu()

        # statusbar
        self.statusbar = self.CreateStatusBar(2, wx.ST_SIZEGRIP)
        self.statusbar.SetStatusWidths([-2, -3])
        self.statusbar.SetStatusText("Ready", 0)
        self.statusbar.SetStatusText("DeVIDE Measure2D", 1)

        self.SetMinSize(wx.Size(400, 300))
        self.SetSize(wx.Size(400, 300))

        # could make toolbars here


        # now we need to add panes
        self._rwi_panel = self._create_rwi_panel()
        self._mgr.AddPane(self._rwi_panel,
                          PyAUI.PaneInfo().Name('rwi').
                          Caption('Image View').Center().
                          MinSize(self._rwi_panel.GetSize()))
        
        self._image_control_panel = self._create_image_control_panel()
        self._mgr.AddPane(self._image_control_panel,
                          PyAUI.PaneInfo().Name('image_control').
                          Caption('Controls').Bottom().
                          MinSize(self._image_control_panel.GetSize()))
        
        self._measurement_panel = self._create_measurement_panel()
        self._mgr.AddPane(self._measurement_panel,
                          PyAUI.PaneInfo().Name('measurement').
                          Caption('Measurements').Bottom().
                          MinSize(self._measurement_panel.GetSize()))
                          
        
        # post-pane setup
        self._mgr.Update()

        self.perspective_default = self._mgr.SavePerspective()

        # these come from the demo
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        
        #self.Bind(wx.EVT_CLOSE, self.OnClose)

        # even although we disable the close button, when a window floats
        # it gets a close button back, so we have to make sure that when
        # the user activates that the windows is merely hidden

        self.Bind(PyAUI.EVT_AUI_PANEBUTTON, self.OnPaneButton)

        wx.EVT_MENU(self, self.window_default_view_id,
                    lambda e: self._mgr.LoadPerspective(
            self.perspective_default) and self._mgr.Update())

    def close(self):
        # do the careful thing with the threedRWI and all
        self.Destroy()

    def _create_rwi_panel(self):
        #rwi_panel = wx.Panel(self, -1)
        self._rwi = wxVTKRenderWindowInteractor(self, -1, size=(300,100))
        
        #sizer = wx.BoxSizer(wx.VERTICAL)
        #sizer.Add(self._rwi, 1, wx.EXPAND | wx.ALL, 4)

        #rwi_panel.SetAutoLayout(True)
        #rwi_panel.SetSizer(sizer)
        #rwi_panel.GetSizer().Fit(rwi_panel)
        #rwi_panel.GetSizer().SetSizeHints(rwi_panel)

        #return rwi_panel
        return self._rwi
    
    def _create_image_control_panel(self):
        panel = wx.Panel(self, -1)
        #wx.Label(panel, -1, "")
        panel.slider = wx.Slider(panel, -1, 0, 0, 64, style=wx.SL_LABELS)
        slider_box = wx.BoxSizer(wx.HORIZONTAL)
        slider_box.Add(panel.slider, 1, wx.ALL)
        
        tl_sizer = wx.BoxSizer(wx.VERTICAL)
        tl_sizer.Add(slider_box, 0, wx.EXPAND, 4)
        
        panel.SetAutoLayout(True)
        panel.SetSizer(tl_sizer)
        panel.GetSizer().Fit(panel)
        panel.GetSizer().SetSizeHints(panel)
        
        return panel

    def _handler_grid_range_select(self, event):

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
        g = event.GetEventObject()

        # both of these are lists of (row, column) tuples
        tl = g.GetSelectionBlockTopLeft()
        br = g.GetSelectionBlockBottomRight()

        # this means that the user has most probably clicked on the little
        # block at the top-left corner of the grid... in this case,
        # SelectRow has no frikking effect (up to wxPython 2.4.2.4) so we
        # detect this situation and clear the selection (we're going to be
        # selecting the whole grid in anycase.
        if tl == [(0,0)] and br == [(g.GetNumberRows() - 1,
                                     g.GetNumberCols() - 1)]:
            g.ClearSelection()

        for (tlrow, tlcolumn), (brrow, brcolumn) in zip(tl, br):
            for row in range(tlrow,brrow + 1):
                g.SelectRow(row, True)


    
    def _create_measurement_panel(self):
        # drop-down box with type, name, create button
        # grid / list with names and measured data
        # also delete button to get rid of things we don't want

        # start nasty trick: load wxGlade created frame
        mpf = measure2d_panels.MeasurementPanelFrame
        self.dummy_measurement_frame = mpf(self, id=-1)

        # take and reparent the panel we want
        dmf = self.dummy_measurement_frame
        panel = dmf.panel
        panel.Reparent(self)
        panel.create_button = dmf.create_button
        panel.measurement_grid = dmf.measurement_grid
        panel.name_cb = dmf.name_cb
        panel.rename_button = dmf.rename_button
        panel.delete_button = dmf.delete_button
        panel.enable_button = dmf.enable_button
        panel.disable_button = dmf.disable_button

        # need this handler to fix brain-dead selection handling
        panel.measurement_grid.Bind(wx.grid.EVT_GRID_RANGE_SELECT,
                self._handler_grid_range_select)

        # destroy wxGlade created frame
        dmf.Destroy()

        return panel
                       
                    
    def _make_menu(self):
        # Menu Bar
        self.menubar = wx.MenuBar()
        self.SetMenuBar(self.menubar)
        self.fileNewId = wx.NewId()
        self.fileOpenId = wx.NewId()
        
        file_menu = wx.Menu()
        file_menu.Append(self.fileNewId, "&New\tCtrl-N",
                         "Create new network.", wx.ITEM_NORMAL)
        file_menu.Append(self.fileOpenId, "&Open\tCtrl-O",
                         "Open and load existing network.", wx.ITEM_NORMAL)
        self.menubar.Append(file_menu, "&File")

        window_menu = wx.Menu()
        self.window_default_view_id = wx.NewId()
        window_menu.Append(
            self.window_default_view_id, "Restore &default view",
            "Restore default perspective / window configuration.",
            wx.ITEM_NORMAL)
        self.menubar.Append(window_menu, "&Window")        
        
    def OnEraseBackground(self, event):
        # from PyAUI demo
        event.Skip()

    def OnPaneButton(self, event):
        event.GetPane().Hide()

    def OnSize(self, event):
        # from PyAUI demo
        event.Skip()
    
