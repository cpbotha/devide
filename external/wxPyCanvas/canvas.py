from wxPython import wx

class wxPyCanvasObject(wx.wxObject):
    
    def __init__(self, position):
        # call parent ctor
        wx.wxObject(self)

        self._position = position
        self._canvas = None

    def draw(self, dc):
        pass

    def hitTest(self, x, y):
        return False

    def setCanvas(self, canvas):
        self._canvas = canvas

    def OnEnter(self, event):
        pass

    def OnExit(self, event):
        pass

    def OnDrag(self, event):
        pass

    def OnButtonDown(self, event):
        pass

    def OnButtonUp(self, event):
        pass

class wxpcRectangle(wxPyCanvasObject):

    def __init__(self, position, size):
        wxPyCanvasObject.__init__(self, position)
        self._size = size

    def draw(self, dc):
        # drawing rectangle!
        dc.DrawRectangle(self._position[0], self._position[1],
                         self._size[0], self._size[1])

    def hitTest(self, x, y):
        return x >= self._position[0] and \
               x <= self._position[0] + self._size[0] and \
               y >= self._position[1] and \
               y <= self._position[1] + self._size[1]

    def OnEnter(self, event):
        print "entering!"

    def OnExit(self, event):
        print "exiting!"
    

class wxPyCanvas(wx.wxScrolledWindow):
    def __init__(self, parent, id = -1, size = wx.wxDefaultSize):
        wx.wxScrolledWindow.__init__(self, parent, id, wx.wxPoint(0, 0), size,
                                     wx.wxSUNKEN_BORDER)

        self._cobjects = []

        self.SetBackgroundColour("WHITE")

        wx.EVT_MOUSE_EVENTS(self, self.OnMouseEvent)
        wx.EVT_PAINT(self, self.OnPaint)

    def OnMouseEvent(self, event):
        # these coordinates are relative to the visible part of the canvas
        ex, ey = event.GetX(), event.GetY()
        
        for cobject in self._cobjects:
            if cobject.hitTest(ex, ey):
                if not cobject.__hasMouse:
                    cobject.__hasMouse = True
                    cobject.OnEnter(event)

                if event.Dragging():
                    cobject.OnDrag(event)

                elif event.ButtonUp():
                    cobject.OnButtonUp(event)

                elif event.ButtonDown():
                    cobject.OnButtonDown(event)

            else:
                if cobject.__hasMouse:
                    cobject.__hasMouse = False
                    cobject.OnExit(event)

    def OnPaint(self, event):
        # make a dc
        dc =  wx.wxPaintDC(self)
        # set device origin according to scroll position
        self.PrepareDC(dc)

        dc.BeginDrawing()
        # clear the whole shebang to background
        dc.SetBackground(wx.wxBrush(self.GetBackgroundColour(), wx.wxSOLID))
        dc.Clear()

        # draw all objects
        for cobj in self._cobjects:
            cobj.draw(dc)

        dc.EndDrawing()

    def addObject(self, cobj):
        if cobj and cobj not in self._cobjects:
            cobj.setCanvas(self)
            self._cobjects.append(cobj)
            cobj.__hasMouse = False
            #cobj.draw()
        


def main():

    class App(wx.wxApp):
        def OnInit(self):
            frame = wx.wxFrame(None, -1, 'wxPyCanvasTest')
            pc = wxPyCanvas(frame, -1)
            pc.SetVirtualSize((1024, 1024))
            pc.SetScrollRate(20,20)

            r1 = wxpcRectangle((20, 20), (50, 20))
            pc.addObject(r1)

            tlSizer = wx.wxBoxSizer(wx.wxVERTICAL)
            tlSizer.Add(pc, 1, wx.wxEXPAND)
            tlSizer.Add(wx.wxButton(frame, -1, "Quit"), 0, wx.wxEXPAND)

            frame.SetSizer(tlSizer)
            frame.SetAutoLayout(True)
            tlSizer.Fit(frame)
            tlSizer.SetSizeHints(frame)
            frame.Layout()
            
            frame.Show(True)
            self.SetTopWindow(frame)

            return True

            
    app = App()
    app.MainLoop()
    
if __name__ == '__main__':
    main()

