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
            self._create_progress_panel(),
            PyAUI.PaneInfo().Name('progress_panel').
            Caption('Progress').Top())

        
        self._mgr.AddPane(
            wxpc.canvas(self, -1),
            PyAUI.PaneInfo().Name('graph_canvas').
            Caption('Graph Canvas').CenterPane())

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
        return tc

    def _create_module_cats(self):
        return wx.ListBox(self, -1, choices=[],
                          style=wx.LB_EXTENDED|wx.LB_NEEDED_SB)

    def _create_module_list(self):
        return wx.ListBox(self, -1, choices=[],
                          style=wx.LB_SINGLE|wx.LB_NEEDED_SB)

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
        sizer.Add(self.progress_text, 0, wx.EXPAND)
        sizer.Add(self.progress_gauge, 0, wx.EXPAND)

        tl_sizer.Add(sizer, 1, wx.EXPAND)
        
        #sizer.SetMinSize((100, 50))
        progress_panel.SetSizer(tl_sizer)
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
        self.helpShowHelpId = wx.NewId()
        wxglade_tmp_menu = wx.Menu()
        wxglade_tmp_menu.Append(self.fileNewId, "&New\tCtrl-N", "Create new network.", wx.ITEM_NORMAL)
        wxglade_tmp_menu.Append(self.fileOpenId, "&Open\tCtrl-O", "Open and load existing network.", wx.ITEM_NORMAL)
        wxglade_tmp_menu.Append(self.fileOpenSegmentId, "Open as Se&gment\tCtrl-G", "Open a DeVIDE network as a segment in the copy buffer.", wx.ITEM_NORMAL)
        wxglade_tmp_menu.Append(self.fileSaveId, "&Save\tCtrl-S", "Save the current network.", wx.ITEM_NORMAL)
        wxglade_tmp_menu.Append(self.fileSaveSelectedId, "Save se&lected Glyphs\tCtrl-L", "Save the selected glyphs as a network.", wx.ITEM_NORMAL)
        wxglade_tmp_menu.AppendSeparator()
        wxglade_tmp_menu.Append(self.fileExportAsDOTId, "&Export as DOT file\tCtrl-E", "Export the current network as a GraphViz DOT file.", wx.ITEM_NORMAL)
        wxglade_tmp_menu.Append(self.fileExportSelectedAsDOTId, "Export selection as DOT file", "Export the selected glyphs as a GraphViz DOT file.", wx.ITEM_NORMAL)
        wxglade_tmp_menu.AppendSeparator()
        wxglade_tmp_menu.Append(self.fileExitId, "E&xit\tCtrl-Q", "Exit DeVIDE!", wx.ITEM_NORMAL)
        self.menubar.Append(wxglade_tmp_menu, "&File")
        self.editMenu = wx.Menu()
        self.menubar.Append(self.editMenu, "&Edit")
        self.execution_menu = wx.Menu()
        self.menubar.Append(self.execution_menu, "E&xecution")
        wxglade_tmp_menu = wx.Menu()
        wxglade_tmp_menu.Append(self.windowMainID, "&Main window", "Show the DeVIDE main window.", wx.ITEM_NORMAL)
        self.menubar.Append(wxglade_tmp_menu, "&Window")
        wxglade_tmp_menu = wx.Menu()
        wxglade_tmp_menu.Append(self.helpShowHelpId, "Show &Help\tF1", "", wx.ITEM_NORMAL)
        self.menubar.Append(wxglade_tmp_menu, "&Help")
        # Menu Bar end
        
    def OnEraseBackground(self, event):

        event.Skip()


    def OnSize(self, event):

        event.Skip()
