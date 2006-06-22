from internal.wxPyCanvas import wxpc
import external.PyAUI as PyAUI
import wx
from wx.html import HtmlWindow


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

        self.canvas = wxpc.canvas(self, -1)
        self._mgr.AddPane(
            self.canvas,
            PyAUI.PaneInfo().Name('graph_canvas').
            Caption('Graph Canvas').Center())

        sp = self._create_module_search_panel()
        self._mgr.AddPane(
            sp,
            PyAUI.PaneInfo().Name('module_search').
            Caption('Module Search').Left())
        
        self.module_cats = self._create_module_cats()
        self._mgr.AddPane(
            self.module_cats,
            PyAUI.PaneInfo().Name('module_cats').Caption('Module Categories').
            Left())

        self.module_list = self._create_module_list()
        self._mgr.AddPane(
            self.module_list,
            PyAUI.PaneInfo().Name('module_list').Caption('Module List'))


        self._mgr.AddPane(
            self._create_documentation_window(),
            PyAUI.PaneInfo().Name('doc_window').
            Caption('Documentation Window').Bottom())

        self._mgr.AddPane(
            self._create_log_window(),
            PyAUI.PaneInfo().Name('log_window').
            Caption('Log Messages').Bottom())
        
        self._mgr.Update()

        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        #self.Bind(wx.EVT_CLOSE, self.OnClose)

    def _create_documentation_window(self):
        return HtmlWindow(self, -1)

    def _create_log_window(self):
        tc = wx.TextCtrl(
            self, -1, "", style=wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL)
        tc.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.message_log_text_ctrl = tc
        return tc

    def _create_module_cats(self):
        self.module_cats_list_box = wx.ListBox(
            self, -1, choices=[],
            style=wx.LB_EXTENDED|wx.LB_NEEDED_SB)
        return self.module_cats_list_box 

    def _create_module_list(self):
        self.module_list_box = wx.ListBox(self, -1, choices=[],
                                          style=wx.LB_SINGLE|wx.LB_NEEDED_SB)
        return self.module_list_box

    def _create_module_search_panel(self):
        pass

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
        self.windowMainID = wx.NewId()
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

        self.execution_menu = wx.Menu()
        self.menubar.Append(self.execution_menu, "E&xecution")

        modules_menu = wx.Menu()
        self.id_rescan_modules = wx.NewId()
        modules_menu.Append(
            self.id_rescan_modules, "Rescan modules", "Recheck all module "
            "directories for new modules and metadata.", wx.ITEM_NORMAL)
        self.menubar.Append(modules_menu, "&Modules")

        window_menu = wx.Menu()
        window_menu.Append(
            self.windowMainID, "&Main window", "Show the DeVIDE main window.",
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

    def OnSize(self, event):
        # from PyAUI demo
        event.Skip()
