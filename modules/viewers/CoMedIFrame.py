# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

import cStringIO
import vtk
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

# using Andrea Gavana's latest Python AUI:
#from external import aui
#wx.aui = aui
# this works fine on Windows.  Have not been able to test on Linux
# whilst in Magdeburg.

import resources.python.comedi_frames
reload(resources.python.comedi_frames)

class CMIPane:
    """Class for anything that would like to populate the interface.
    Each _create* method returns an instance of this class, populated
    with the various required ivars.
    """
    def __init__(self):
        self.window = None

class CoMedIFrame(wx.Frame):
    """wx.Frame child class used by SkeletonAUIViewer for its
    interface.

    This is an AUI-managed window, so we create the top-level frame,
    and then populate it with AUI panes.
    """

    def __init__(self, parent, id=-1, title="", name=""):
        wx.Frame.__init__(self, parent, id=id, title=title, 
                pos=wx.DefaultPosition, size=(1000,600), name=name)


        self.menubar = wx.MenuBar()
        self.SetMenuBar(self.menubar)

        file_menu = wx.Menu()
        self.id_file_open = wx.NewId()
        file_menu.Append(self.id_file_open, "&Open\tCtrl-O",
                "Open a file", wx.ITEM_NORMAL)

        self.menubar.Append(file_menu, "&File")
       




        ###################################################################
        camera_menu = wx.Menu()

        self.id_camera_perspective = wx.NewId()
        camera_menu.Append(self.id_camera_perspective, "&Perspective",
                "Perspective projection mode", wx.ITEM_RADIO)

        self.id_camera_parallel = wx.NewId()
        camera_menu.Append(self.id_camera_parallel, "Pa&rallel",
                "Parallel projection mode", wx.ITEM_RADIO)

        camera_menu.AppendSeparator()

        self.id_camera_xyzp = wx.NewId()
        camera_menu.Append(self.id_camera_xyzp, "View XY from Z+",
                "View XY plane face-on from Z+", wx.ITEM_NORMAL)

        self.menubar.Append(camera_menu, "&Camera")

        ###################################################################
        views_menu = wx.Menu()

        self.id_views_synchronised = wx.NewId()
        mi = views_menu.Append(self.id_views_synchronised, "&Synchronised",
                "Toggle view synchronisation", wx.ITEM_CHECK)
        mi.Check(True)

        views_menu.AppendSeparator()

        self.id_views_slice2 = wx.NewId()
        mi = views_menu.Append(self.id_views_slice2, "Slice &2",
                "Toggle slice 2", wx.ITEM_CHECK)
        mi.Check(False)

        self.id_views_slice3 = wx.NewId()
        mi = views_menu.Append(self.id_views_slice3, "Slice &3",
                "Toggle slice 3", wx.ITEM_CHECK)
        mi.Check(False)

        views_menu.AppendSeparator()

        views_default_id = wx.NewId()
        views_menu.Append(views_default_id, "&Default\tCtrl-0",
                         "Activate default view layout.", wx.ITEM_NORMAL)
                

        views_max_image_id = wx.NewId()
        views_menu.Append(views_max_image_id, "&Maximum image size\tCtrl-1",
                         "Activate maximum image view size layout.", 
                         wx.ITEM_NORMAL)

        self.menubar.Append(views_menu, "&Views")

        adv_menu = wx.Menu()
        self.id_adv_introspect = wx.NewId()
        adv_menu.Append(self.id_adv_introspect, '&Introspect\tAlt-I',
                'Introspect this CoMedI instance.', wx.ITEM_NORMAL)
        self.menubar.Append(adv_menu, '&Advanced')



        # tell FrameManager to manage this frame        
        self._mgr = wx.aui.AuiManager()
        self._mgr.SetManagedWindow(self)

      
        self.pane_controls = self._create_controls_pane()
        self._mgr.AddPane(self.pane_controls.window, wx.aui.AuiPaneInfo().
                          Name("controls").Caption("Controls").
                          Left().Layer(2).
                          BestSize(wx.Size(400,400)).
                          CloseButton(False).MaximizeButton(True))

        self.rwi_pane_data1 = self._create_rwi_pane()
        self._mgr.AddPane(self.rwi_pane_data1.window, wx.aui.AuiPaneInfo().
                          Name("data1 rwi").Caption("Data 1").
                          Left().Position(0).Layer(1).
                          BestSize(wx.Size(400,400)).
                          CloseButton(False).MaximizeButton(True))

        self.rwi_pane_data2 = self._create_rwi_pane()
        self._mgr.AddPane(self.rwi_pane_data2.window, wx.aui.AuiPaneInfo().
                          Name("data2 rwi").Caption("Data 2").
                          Left().Position(1).Layer(1).
                          BestSize(wx.Size(400,400)).
                          CloseButton(False).MaximizeButton(True))

        self.rwi_pane_compvis = self._create_rwi_pane()
        self._mgr.AddPane(self.rwi_pane_compvis.window, wx.aui.AuiPaneInfo().
                          Name("compvis1 rwi").Caption("Main CompVis").
                          Center().
                          BestSize(wx.Size(800,800)).
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
        for rwi_pane in self.get_rwi_panes():
            self._close_rwi_pane(rwi_pane)

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

    def _create_controls_pane(self):

        f = resources.python.comedi_frames.CoMedIControlsFrame(self)

        # reparent the panel to us
        panel = f.main_panel
        panel.Reparent(self)

        # still need fpf.* to bind everything
        # but we can destroy fpf (everything has been reparented)
        f.Destroy()

        panel.cursor_text = f.cursor_text
        panel.data1_landmarks_olv = f.data1_landmarks_olv
        panel.data2_landmarks_olv = f.data2_landmarks_olv
        panel.lm_add_button = f.lm_add_button
        panel.compare_button = f.compare_button
        panel.update_compvis_button = f.update_compvis_button
        panel.match_mode_notebook = f.match_mode_notebook
        panel.comparison_mode_notebook = f.comparison_mode_notebook

        panel.cm_checkerboard_divx = f.cm_checkerboard_divx
        panel.cm_checkerboard_divy = f.cm_checkerboard_divy
        panel.cm_checkerboard_divz = f.cm_checkerboard_divz

        cmi_pane = CMIPane()
        cmi_pane.window = panel
        return cmi_pane

    def _create_rwi_pane(self):
        """Return pane with renderer and buttons.
        """

        panel = wx.Panel(self, -1)

        rwi = wxVTKRenderWindowInteractor(panel, -1, (300,300))

        if False:
            self.button1 = wx.Button(panel, -1, "Add Superquadric")
            self.button2 = wx.Button(panel, -1, "Reset Camera")
            button_sizer = wx.BoxSizer(wx.HORIZONTAL)
            button_sizer.Add(self.button1)
            button_sizer.Add(self.button2)

            sizer1 = wx.BoxSizer(wx.VERTICAL)
            sizer1.Add(rwi, 1, wx.EXPAND|wx.BOTTOM, 7)
            sizer1.Add(button_sizer)

        tl_sizer = wx.BoxSizer(wx.VERTICAL)
        tl_sizer.Add(rwi, 1, wx.ALL|wx.EXPAND, 7)

        panel.SetSizer(tl_sizer)
        tl_sizer.Fit(panel)

        ren = vtk.vtkRenderer()
        ren.SetBackground(0.5,0.5,0.5)
        rwi.GetRenderWindow().AddRenderer(ren)

        cmi_pane = CMIPane()
        cmi_pane.window = panel
        cmi_pane.renderer = ren
        cmi_pane.rwi = rwi

        return cmi_pane

    def _close_rwi_pane(self, cmi_pane):
        cmi_pane.renderer.RemoveAllViewProps()
        cmi_pane.rwi.GetRenderWindow().Finalize()
        cmi_pane.rwi.SetRenderWindow(None)
        del cmi_pane.rwi
        del cmi_pane.renderer # perhaps not...
        
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
    
    def get_rwi_panes(self):
        return [self.rwi_pane_data1, 
                self.rwi_pane_data2, 
                self.rwi_pane_compvis]

    def get_rwis(self):
        return [rwi_pane.rwi for rwi_pane in self.get_rwi_panes()]

    def render_all(self):
        """Update embedded RWI, i.e. update the image.
        """

        for rwi in self.get_rwis():
            rwi.Render()

    def set_cam_parallel(self):
        """Set check next to "parallel" menu item.
        """
        mi = self.menubar.FindItemById(self.id_camera_parallel)
        mi.Check(True)

    def set_cam_perspective(self):
        """Set check next to "perspective" menu item.
        """
        mi = self.menubar.FindItemById(self.id_camera_perspective)
        mi.Check(True)
       
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




