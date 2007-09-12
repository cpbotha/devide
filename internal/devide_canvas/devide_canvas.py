import vtk
from gen_mixins import SubjectMixin

class DeVIDECanvas(SubjectMixin):
    """Give me a vtkRenderWindowInteractor with a Renderer, and I'll
    do the rest.  YEAH.
    """

    def __init__(self, renderwindowinteractor):

        self._rwi = renderwindowinteractor

        # parent 2 ctor
        SubjectMixin.__init__(self)

        self._cobjects = []
        self._previousRealCoords = None
        self._mouseDelta = (0,0)
        self._potentiallyDraggedObject = None
        self._draggedObject = None

        self._observers = {'drag' : [],
                           'buttonDown' : [],
                           'buttonUp' : []}

        
        #self.SetBackgroundColour("WHITE")

        #wx.EVT_MOUSE_EVENTS(self, self.OnMouseEvent)
        #wx.EVT_PAINT(self, self.OnPaint)

        self.virtualWidth = 2048
        self.virtualHeight = 2048
        

        # do initial drawing here.

    def eventToRealCoords(self, ex, ey):
        """Convert window event coordinates to canvas relative coordinates.
        """
        
        # get canvas parameters
        vsx, vsy = self.GetViewStart()
        dx, dy = self.GetScrollPixelsPerUnit()

        # calculate REAL coords
        rx = ex + vsx * dx
        ry = ey + vsy * dy

        return (rx, ry)

    def getDC(self):
        """Returns DC which can be used by the outside to draw to our buffer.

        As soon as dc dies (and it will at the end of the calling function)
        the contents of self._buffer will be blitted to the screen.
        """

        cdc = wx.wxClientDC(self)
        # set device origin according to scroll position                
        self.PrepareDC(cdc)
        dc = wx.wxBufferedDC(cdc, self._buffer)
        return dc

    def get_glyph_on_coords(self, rx, ry):
        """If rx,ry falls on a glyph, return that glyph, else return
        None.
        """

        for cobject in self._cobjects:
            if cobject.hitTest(rx, ry) and isinstance(cobject,
                    coGlyph):
                return cobject

        return None

    def OnMouseEvent(self, event):

        # this seems to work fine under windows.  If we don't do this, and the
        # mouse leaves the canvas, the rubber band remains and no selection
        # is made.
        if event.ButtonDown():
            if not self.HasCapture():
                self.CaptureMouse()
                
        elif event.ButtonUp():
            if self.HasCapture():
                self.ReleaseMouse()
        
        # these coordinates are relative to the visible part of the canvas
        ex, ey = event.GetX(), event.GetY()

        rx, ry = self.eventToRealCoords(ex, ey)

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

        # the following three clauses, i.e. the hitTest, mouseOnObject and
        # draggedObject should be kept in this order, unless you know
        # EXACTLY what you're doing.  If you're going to change anything, test
        # that connects, disconnects (of all kinds) and rubber-banding still
        # work.
        
        # we need to do this expensive hit test every time, because the user
        # wants to know when he mouses over the input port of a destination
        # module
        for cobject in self._cobjects:
            if cobject.hitTest(rx, ry):
                mouseOnObject = True

                cobject.notifyObservers('motion', event)

                if not cobject.__hasMouse:
                    cobject.__hasMouse = True
                    cobject.notifyObservers('enter', event)
                        
                if event.Dragging():
                    if not self._draggedObject:
                        if self._potentiallyDraggedObject == cobject:
                            # the user is dragging inside an object inside
                            # of which he has previously clicked... this
                            # definitely means he's dragging the object
                            mouseOnObject = True
                            self._draggedObject = cobject
                            
                        else:
                            # this means the user has dragged the mouse
                            # over an object... which means mouseOnObject
                            # is technically true, but because we want the
                            # canvas to get this kind of dragEvent, we
                            # set it to false
                            mouseOnObject = False

                elif event.ButtonUp():
                    cobject.notifyObservers('buttonUp', event)

                elif event.ButtonDown():
                    if event.LeftDown():
                        # this means EVERY buttonDown in an object classifies
                        # as a potential drag.  if the user now drags, we
                        # have a winner
                        self._potentiallyDraggedObject = cobject
                            
                    cobject.notifyObservers('buttonDown', event)

                elif event.ButtonDClick():
                    cobject.notifyObservers('buttonDClick', event)

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

        if event.ButtonUp():
            # each and every ButtonUp cancels the current potential drag object
            self._potentiallyDraggedObject = None
                    

        # store the previous real coordinates for mouse deltas
        self._previousRealCoords = (rx, ry)
                    

    def add_object(self, cobj):
        if cobj and cobj not in self._cobjects:
            cobj.setCanvas(self)
            self._cobjects.append(cobj)
            cobj.__hasMouse = False

    def redraw(self):
        """Redraw the whole scene.
        """

        self._rwi.Render()

    def remove_object(self, cobj):
        if cobj and cobj in self._cobjects:
            cobj.setCanvas(None)
            if self._draggedObject == cobj:
                self._draggedObject = None
            del self._cobjects[self._cobjects.index(cobj)]

    def getMouseDelta(self):
        return self._mouseDelta

    def getDraggedObject(self):
        return self._draggedObject

    def getObjectsOfClass(self, classt):
        return [i for i in self._cobjects if isinstance(i, classt)]

    def getObjectWithMouse(self):
        """Return object currently containing mouse, None if no object has
        the mouse.
        """

        for cobject in self._cobjects:
            if cobject.__hasMouse:
                return cobject

        return None

    def dragObject(self, cobj, delta):
        if abs(delta[0]) > 0 or abs(delta[1]) > 0:
            # calculate new position
            cpos = cobj.getPosition()
            npos = (cpos[0] + delta[0], cpos[1] + delta[1])
            cobj.setPosition(npos)
            
            # setup DC
            dc = self.getDC()

            dc.BeginDrawing()

            # we're only going to draw a dotted outline
            dc.SetBrush(wx.wxBrush('WHITE', wx.wxTRANSPARENT))
            dc.SetPen(wx.wxPen('BLACK', 1, wx.wxDOT))
            dc.SetLogicalFunction(wx.wxINVERT)
            bounds = cobj.getBounds()

            # first delete the old rectangle
            dc.DrawRectangle(cpos[0], cpos[1], bounds[0], bounds[1])
            # then draw the new one
            dc.DrawRectangle(npos[0], npos[1], bounds[0], bounds[1])

            # thar she goes
            dc.EndDrawing()



