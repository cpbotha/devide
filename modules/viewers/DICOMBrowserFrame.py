import wx

class DICOMBrowserFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, id=-1, title="", 
                pos=wx.DefaultPosition, size=wx.DefaultSize)

        # tell FrameManager to manage this frame        
        self._mgr = wx.aui.AuiManager()
        self._mgr.SetManagedWindow(self)
        
        self._perspectives = []

        self.SetMinSize(wx.Size(400, 300))

    def close(self):
        self.Destroy()

    def create_studies_pane(self):
        pass


