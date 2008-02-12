# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

import vtk
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor
import external.PyAUI as PyAUI
import wx
from wx.html import HtmlWindow

class SimpleHTMLListBox(wx.HtmlListBox):
    """Simple class to emulate normal wx.ListBox (Append, Clear, GetClientData
    and GetString methods) with the super-powers of the wx.HtmlListBox.

    @author Charl P. Botha <http://cpbotha.net/>
    """

    def __init__(self, *args, **kwargs):
        wx.HtmlListBox.__init__(self, *args, **kwargs)
        self.items = []
        self.Clear()

    def Append(self, text, data=None, refresh=True):
        """Emulates wx.ListBox Append method, except for refresh bit.

        Set refresh to False if you're going to be appending bunches of
        items.  When you're done, call the DoRefresh() method explicitly.
        """
        
        self.items.append((text, data))
        if refresh:
            self.SetItemCount(len(self.items))
            self.Refresh()

    def DoRefresh(self):
        """To be used after adding large amounts of items with Append and
        refresh=False.
        """
        
        self.SetItemCount(len(self.items))
        self.Refresh()

    def Clear(self):
        del self.items[:]
        self.SetSelection(-1)
        self.SetItemCount(0)

    def GetClientData(self, n):
        if n >= 0 and n < len(self.items):
            return self.items[n][1]
        else:
            return None

    def GetCount(self):
        return len(self.items)

    def GetString(self, n):
        if n >= 0 and n < len(self.items):
            return self.items[n][0]
        else:
            return None
        
    def OnGetItem(self, n):
        try:
            return self.items[n][0]
        except IndexError:
            return ''


class MainWXFrame(wx.Frame):
    """Class for building main user interface frame.

    All event handling and other intelligence should be elsewhere.
    """

    def __init__(self, parent, id=-1, title="", pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE |
                                            wx.SUNKEN_BORDER |
                                            wx.CLIP_CHILDREN):

        wx.Frame.__init__(self, parent, id, title, pos, size, style)
        
        # tell FrameManager to manage this frame        
        self._mgr = PyAUI.FrameManager()
        self._mgr.SetFrame(self)

        self._make_menu()

        # statusbar
        self.statusbar = self.CreateStatusBar(2, wx.ST_SIZEGRIP)
        self.statusbar.SetStatusWidths([-2, -3])
        self.statusbar.SetStatusText("Ready", 0)
        self.statusbar.SetStatusText("Welcome To DeVIDE!", 1)

        self.SetMinSize(wx.Size(400, 300))

        # could make toolbars here

        # now we need to add panes

        # minsize is quite important here; progress-panel can never be
        # obscured by moving one of the splitters
        pp = self._create_progress_panel() 
        self._mgr.AddPane(
            pp,
            PyAUI.PaneInfo().Name('progress_panel').
            Caption('Progress').CenterPane().Top().MinSize(pp.GetSize()))

       
        self._rwi = wxVTKRenderWindowInteractor(self, -1,
                size=(400,400))

        # we have to call this, else moving a modal dialogue over the
        # graph editor will result in trails.  Usually, a wxVTKRWI
        # refuses to render if its top-level parent is disabled.  This
        # is to stop VTK pipeline updates whilst wx.SafeYield() is
        # being called.  In _this_ case, the VTK pipeline is safe, so
        # we can disable this check.
        self._rwi.SetRenderWhenDisabled(True)
        self._ren = vtk.vtkRenderer()
        self._rwi.GetRenderWindow().AddRenderer(self._ren)

        rw = self._rwi.GetRenderWindow()
        rw.SetLineSmoothing(1)
        rw.SetPointSmoothing(1)

        # PolygonSmoothing is not really necessary for the GraphEditor
        # (yet), and on a GeForce 4600 Ti on Linux with driver version
        # 1.0-9639, you can see triangle lines bisecting quads.  Not
        # a nice artifact, so I've disabled this for now.
        #rw.SetPolygonSmoothing(1)

        self._mgr.AddPane(
            self._rwi,
            PyAUI.PaneInfo().Name('graph_canvas').
            Caption('Graph Canvas').Center().CloseButton(False))

        sp = self._create_module_search_panel()
        self._mgr.AddPane(
            sp,
            PyAUI.PaneInfo().Name('module_search').
            Caption('Module Search').Left().MinSize(sp.GetSize()).
            CloseButton(False))

        # a little trick I found in the PyAUI source code.  This will make
        # sure that the pane is as low (small y) as it can be
        p = self._mgr.GetPane('module_search')
        p.dock_proportion = 0
        
        self.module_cats = self._create_module_cats()
        self._mgr.AddPane(
            self.module_cats,
            PyAUI.PaneInfo().Name('module_cats').Caption('Module Categories').
            Left().CloseButton(False))

        self.module_list = self._create_module_list()
        self._mgr.AddPane(
            self.module_list,
            PyAUI.PaneInfo().Name('module_list').Caption('Module List').
            CloseButton(False))


        self._mgr.AddPane(
            self._create_documentation_window(),
            PyAUI.PaneInfo().Name('doc_window').
            Caption('Documentation Window').Bottom().CloseButton(False))

        self._mgr.AddPane(
            self._create_log_window(),
            PyAUI.PaneInfo().Name('log_window').
            Caption('Log Messages').Bottom().CloseButton(False))
        
        self._mgr.Update()

        self.perspective_default = self._mgr.SavePerspective()

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
        self._ren.RemoveAllViewProps()
        del self._ren
        self._rwi.GetRenderWindow().Finalize()
        self._rwi.SetRenderWindow(None)
        del self._rwi
        self.Destroy()

    def _create_documentation_window(self):
        self.doc_window = HtmlWindow(self, -1, size=(200,80))
        return self.doc_window

    def _create_log_window(self):
        tc = wx.TextCtrl(
            self, -1, "", size=(200, 80),
            style=wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL)
        tc.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.message_log_text_ctrl = tc
        return tc

    def _create_module_cats(self):
        self.module_cats_list_box = wx.ListBox(
            self, -1, choices=[],
            style=wx.LB_EXTENDED|wx.LB_NEEDED_SB)
        return self.module_cats_list_box 

    def _create_module_list(self):
        self.module_list_box = SimpleHTMLListBox(
            self, -1,
            style=wx.LB_SINGLE|wx.LB_NEEDED_SB)
        return self.module_list_box

    def _create_module_search_panel(self):
        search_panel = wx.Panel(self, -1)

        self.search_text = wx.TextCtrl(search_panel, -1, "", 
                style=wx.TE_PROCESS_ENTER)
        self.search_x_button = wx.Button(search_panel, -1, "X",
                                    style=wx.BU_EXACTFIT)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        #sizer.Add(search_label, 0,
        #          wx.RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 3)
        sizer.Add(self.search_text, 1,
                  wx.RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 3)
        sizer.Add(self.search_x_button, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        tl_sizer = wx.BoxSizer(wx.VERTICAL)
        # in this case the wx.EXPAND makes it stretch horizontally
        # the option=1 makes it stretch vertically
        tl_sizer.Add(sizer, 1, wx.EXPAND | wx.ALL, 4)
        
        search_panel.SetAutoLayout(True)
        search_panel.SetSizer(tl_sizer)
        search_panel.GetSizer().Fit(search_panel)
        search_panel.GetSizer().SetSizeHints(search_panel)

        return search_panel

    def _create_progress_panel(self):
        progress_panel = wx.Panel(self, -1)#, size=wx.Size(100, 50))
        self.progress_text = wx.StaticText(progress_panel, -1, "...")
        self.progress_text.SetFont(
           wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.progress_gauge = wx.Gauge(progress_panel, -1, 100)
        self.progress_gauge.SetValue(50)
        #self.progress_gauge.SetBackgroundColour(wx.Colour(50, 50, 204))

        tl_sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # these are in a vertical sizer, so expand will make them draw
        # out horizontally as well
        sizer.Add(self.progress_text, 0, wx.EXPAND | wx.BOTTOM, 4)
        sizer.Add(self.progress_gauge, 0, wx.EXPAND)

        tl_sizer.Add(sizer, 1, wx.EXPAND | wx.ALL, 7)
        
        #sizer.SetMinSize((100, 50))
        progress_panel.SetAutoLayout(True)
        progress_panel.SetSizer(tl_sizer)
        progress_panel.GetSizer().Fit(progress_panel)
        progress_panel.GetSizer().SetSizeHints(progress_panel)

        return progress_panel

    def _make_menu(self):
        # Menu Bar
        self.menubar = wx.MenuBar()
        self.SetMenuBar(self.menubar)
        self.fileNewId = wx.NewId()
        self.fileOpenId = wx.NewId()
        self.fileOpenSegmentId = wx.NewId()
        self.fileSaveId = wx.NewId()
        self.fileSaveSelectedId = wx.NewId()
        self.fileExportAsDOTId = wx.NewId()
        self.fileExportSelectedAsDOTId = wx.NewId()
        self.fileExitId = wx.NewId()
        self.window_python_shell_id = wx.NewId()
        self.helpShowHelpId = wx.NewId()
        self.helpAboutId = wx.NewId()

        
        file_menu = wx.Menu()
        file_menu.Append(self.fileNewId, "&New\tCtrl-N",
                         "Create new network.", wx.ITEM_NORMAL)
        file_menu.Append(self.fileOpenId, "&Open\tCtrl-O",
                         "Open and load existing network.", wx.ITEM_NORMAL)
        file_menu.Append(
            self.fileOpenSegmentId, "Open as Se&gment\tCtrl-G",
            "Open a DeVIDE network as a segment in the copy buffer.",
            wx.ITEM_NORMAL)
        file_menu.Append(self.fileSaveId, "&Save\tCtrl-S",
                         "Save the current network.", wx.ITEM_NORMAL)
        file_menu.Append(self.fileSaveSelectedId,
                         "Save se&lected Glyphs\tCtrl-L",
                         "Save the selected glyphs as a network.",
                         wx.ITEM_NORMAL)
        file_menu.AppendSeparator()
        file_menu.Append(
            self.fileExportAsDOTId, "&Export as DOT file\tCtrl-E",
            "Export the current network as a GraphViz DOT file.",
            wx.ITEM_NORMAL)
        file_menu.Append(self.fileExportSelectedAsDOTId,
                         "Export selection as DOT file",
                         "Export the selected glyphs as a GraphViz DOT file.",
                         wx.ITEM_NORMAL)
        file_menu.AppendSeparator()
        file_menu.Append(self.fileExitId, "E&xit\tCtrl-Q",
                         "Exit DeVIDE!", wx.ITEM_NORMAL)
        self.menubar.Append(file_menu, "&File")

        self.edit_menu = wx.Menu()
        self.menubar.Append(self.edit_menu, "&Edit")

        modules_menu = wx.Menu()

        self.id_modules_search = wx.NewId()
        modules_menu.Append(
            self.id_modules_search, "Search for modules\tCtrl-F",
            "Change input "
            "focus to module search box.", wx.ITEM_NORMAL)
        
        self.id_rescan_modules = wx.NewId()
        modules_menu.Append(
            self.id_rescan_modules, "Rescan modules", "Recheck all module "
            "directories for new modules and metadata.", wx.ITEM_NORMAL)

        self.id_refresh_module_kits = wx.NewId()
        modules_menu.Append(
            self.id_refresh_module_kits, "Refresh module kits",
            "Attempt to refresh / reload all module_kits.", wx.ITEM_NORMAL)
        
        self.menubar.Append(modules_menu, "&Modules")

        self.network_menu = wx.Menu()
        self.menubar.Append(self.network_menu, "&Network")

        window_menu = wx.Menu()

        self.window_default_view_id = wx.NewId()
        window_menu.Append(
            self.window_default_view_id, "Restore &default view",
            "Restore default perspective / window configuration.",
            wx.ITEM_NORMAL)
        
        window_menu.Append(self.window_python_shell_id, "&Python Shell",
                                "Show the Python Shell interface.",
                                wx.ITEM_NORMAL)
        self.menubar.Append(window_menu, "&Window")

        help_menu = wx.Menu()
        help_menu.Append(self.helpShowHelpId, "Show &Help\tF1", "",
                         wx.ITEM_NORMAL)
        help_menu.Append(self.helpAboutId, "About", "",
                                wx.ITEM_NORMAL)
        
        self.menubar.Append(help_menu, "&Help")
        # Menu Bar end
        
    def OnEraseBackground(self, event):
        # from PyAUI demo
        event.Skip()

    def OnPaneButton(self, event):
        event.GetPane().Hide()

    def OnSize(self, event):
        # from PyAUI demo
        event.Skip()
