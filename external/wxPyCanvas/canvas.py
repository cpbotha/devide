from wxPython import wx

class canvas(wx.wxScrolledWindow):
    def __init__(self, parent, id = -1, size = wx.wxDefaultSize):
        wx.wxScrolledWindow.__init__(self, parent, id, wx.wxPoint(0, 0), size,
                                     wx.wxSUNKEN_BORDER)

        self._cobjects = []
        self._previousRealCoords = None

        self.SetBackgroundColour("WHITE")

        wx.EVT_MOUSE_EVENTS(self, self.OnMouseEvent)
        wx.EVT_PAINT(self, self.OnPaint)

    def OnMouseEvent(self, event):
        # these coordinates are relative to the visible part of the canvas
        ex, ey = event.GetX(), event.GetY()

        # get canvas parameters
        vsx, vsy = self.GetViewStart()
        dx, dy = self.GetScrollPixelsPerUnit()

        # calculate REAL coords
        rx = ex + vsx * dx
        ry = ey + vsy * dy

        mouseOnObject = False
        
        for cobject in self._cobjects:
            if cobject.hitTest(rx, ry):
                mouseOnObject = True

                # we modify what's in the event structure to REAL coords
                event.m_x = rx
                event.m_y = ry
                
                if not cobject.__hasMouse:
                    cobject.__hasMouse = True
                    cobject.notifyObservers('enter', event)

                if event.Dragging():
                    cobject.notifyObservers('drag', event)

                elif event.ButtonUp():
                    cobject.notifyObservers('buttonUp', event)

                elif event.ButtonDown():
                    cobject.notifyObservers('buttonDown', event)

            # ends if cobject.hitTest(ex, ey)
            else:
                if cobject.__hasMouse:
                    if not event.Dragging():
                        cobject.__hasMouse = False
                        cobject.notifyObservers('exit', event)

        self._previousRealCoords = (rx, ry)
                    

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

    def getPreviousRealCoords(self):
        return self._previousRealCoords

    def moveObject(self, cobj, delta):
        cpos = cobj.getPosition()
        npos = (cpos[0] + delta[0], cpos[1] + delta[1])
        cobj.setPosition(npos)
        self.Refresh()
        
def main():

    from canvasObject import coRectangle

    class App(wx.wxApp):
        def OnInit(self):
            frame = wx.wxFrame(None, -1, 'wxPyCanvasTest')
            pc = canvas(frame, -1)
            pc.SetVirtualSize((1024, 1024))
            pc.SetScrollRate(20,20)

            for i in range(7):
                r1 = coRectangle((i * 60, 20), (50, 20))
                r1.addObserver('enter', enterObserver)
                r1.addObserver('drag', dragObserver)
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

    def enterObserver(cobject, eventName, event, userData):
        print eventName

    def dragObserver(cobject, eventName, event, userData):
        pr = cobject.getCanvas().getPreviousRealCoords()
        if pr:
            cobject.getCanvas().moveObject(cobject,
                                           (event.GetX() - pr[0],
                                            event.GetY() - pr[1]))
            
    # the 0 will make it use the existing stdout
    app = App(0)
    app.MainLoop()
    
if __name__ == '__main__':
    main()

