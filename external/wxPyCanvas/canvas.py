from wxPython import wx
from canvasSubject import canvasSubject

class canvas(wx.wxScrolledWindow, canvasSubject):
    def __init__(self, parent, id = -1, size = wx.wxDefaultSize):
        wx.wxScrolledWindow.__init__(self, parent, id, wx.wxPoint(0, 0), size,
                                     wx.wxSUNKEN_BORDER)

        self._cobjects = []
        self._previousRealCoords = None
        self._mouseDelta = (0,0)
        self._draggedObject = None

        self._observers = {'drag' : [],
                           'buttonDown' : [],
                           'buttonUp' : []}

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

        # add the "real" coords to the event structure
        event.realX = rx
        event.realY = ry

        if self._previousRealCoords:
            self._mouseDelta = (rx - self._previousRealCoords[0],
                                ry - self._previousRealCoords[1])
        else:
            self._mouseDelta = (0,0)


        # FIXME: store binding to object which "has" the mouse
        # on subsequent tries, we DON'T have to check all objects, only the
        # one which had the mouse on the previous try... only if it "loses"
        # the mouse, do we enter the mean loop again.

        mouseOnObject = False
        
        for cobject in self._cobjects:
            if cobject.hitTest(rx, ry):
                mouseOnObject = True

                cobject.notifyObservers('motion', event)

                if not cobject.__hasMouse:
                    cobject.__hasMouse = True
                    cobject.notifyObservers('enter', event)

                if event.Dragging():
                    if not self._draggedObject:
                        self._draggedObject = cobject

                elif event.ButtonUp():
                    cobject.notifyObservers('buttonUp', event)

                elif event.ButtonDown():
                    cobject.notifyObservers('buttonDown', event)

            # ends if cobject.hitTest(ex, ey)
            else:
                if cobject.__hasMouse:
                    cobject.__hasMouse = False
                    cobject.notifyObservers('exit', event)

        if not mouseOnObject:
            # we only get here if the mouse is not inside any canvasObject
            # (but it could be dragging a canvasObject!)
            if event.Dragging():
                self.notifyObservers('drag', event)
            elif event.ButtonUp():
                self.notifyObservers('buttonUp', event)
            elif event.ButtonDown():
                self.notifyObservers('buttonDown', event)
                    
        if self._draggedObject:
            # dragging locks onto an object, even if the mouse pointer
            # is not inside that object - it will keep receiving drag
            # events!
            draggedObject = self._draggedObject
            if event.ButtonUp():
                # a button up anywhere cancels any drag
                self._draggedObject = None

            # so, the object can query canvas.getDraggedObject: if it's
            # none, it means the drag has ended; if not, the drag is
            # ongoing
            draggedObject.notifyObservers('drag', event)

            

        # store the previous real coordinates for mouse deltas
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

    def removeObject(self, cobj):
        if cobj and cobj in self._cobjects:
            cobj.setCanvas(None)
            del self._cobjects[self._cobjects.index(cobj)]

    def getMouseDelta(self):
        return self._mouseDelta

    def getDraggedObject(self):
        return self._draggedObject

    def dragObject(self, cobj, delta):
        if abs(delta[0]) > 0 or abs(delta[1]) > 0:
            # calculate new position
            cpos = cobj.getPosition()
            npos = (cpos[0] + delta[0], cpos[1] + delta[1])
            cobj.setPosition(npos)
            
            # setup DC
            dc = wx.wxClientDC(self)
            self.PrepareDC(dc)
            dc.BeginDrawing()

            # we're only going to draw a dotted outline
            dc.SetBrush(wx.wxBrush('WHITE', wx.wxTRANSPARENT))
            dc.SetPen(wx.wxPen('BLACK', 1, wx.wxDOT))
            dc.SetLogicalFunction(wx.wxINVERT)
            bounds = cobj.getBounds()

            # first delete the old triangle
            dc.DrawRectangle(cpos[0], cpos[1], bounds[0], bounds[1])
            # then draw the new one
            dc.DrawRectangle(npos[0], npos[1], bounds[0], bounds[1])

            # thar she goes
            dc.EndDrawing()


#############################################################################
def main():

    from canvasObject import coRectangle, coLine, coGlyph

    class App(wx.wxApp):
        def OnInit(self):
            frame = wx.wxFrame(None, -1, 'wxPyCanvasTest')
            pc = canvas(frame, -1, (400, 300))
            pc.SetVirtualSize((1024, 1024))
            pc.SetScrollRate(20,20)

            for i in range(7):
                r1 = coRectangle((i * 60, 20), (50, 20))
                r1.addObserver('enter', enterObserver)
                r1.addObserver('drag', dragObserver)
                pc.addObject(r1)

            l1 = coLine(((60, 50), (70, 60), (100, 50)))
            pc.addObject(l1)

            g1 = coGlyph((60, 100), 7, 3,
                         'shellSplatSimpleFLT')
            g1.addObserver('drag', dragObserver)
            g1.setPortConnected(1, True, True)
            g1.setPortConnected(0, False, True)
            pc.addObject(g1)
                        

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
        cobject.getCanvas().dragObject(cobject,
                                       cobject.getCanvas().getMouseDelta())
        
        if not cobject.getCanvas().getDraggedObject():
            # this means only one thing: the drag has just stopped!
            cobject.getCanvas().Refresh()
            
    # the 0 will make it use the existing stdout
    app = App(0)
    app.MainLoop()
    
if __name__ == '__main__':
    main()

