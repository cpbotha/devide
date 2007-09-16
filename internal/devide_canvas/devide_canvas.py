import vtk
from gen_mixins import SubjectMixin

# think about turning this into a singleton.
class DeVIDECanvasEvent:
    def __init__(self):
        # last event information ############
        self.name = None
        #self.left_button_down = False
        #self.left_button_up = False
        #self.middle_button_down = False
        #self.middle_button_up = False
        #self.right_button_down = False
        #self.right_button_up = False

        # state information #################
        self.left_button = False
        self.middle_button = False
        self.right_button = False
        
        # which cobject has the mouse
        self.has_mouse = None



class DeVIDECanvas(SubjectMixin):
    """Give me a vtkRenderWindowInteractor with a Renderer, and I'll
    do the rest.  YEAH.
    """

    def __init__(self, renderwindowinteractor, renderer):

        self._rwi = renderwindowinteractor
        self._ren = renderer

        # parent 2 ctor
        SubjectMixin.__init__(self)

        self._cobjects = []
        # dict for mapping from prop back to cobject
        self._prop_to_cobject = {}
        self._previousRealCoords = None
        self._mouseDelta = (0,0)
        self._potentiallyDraggedObject = None
        self._draggedObject = None

        self._observers = {'drag' : [],
                           'buttonDown' : [],
                           'buttonUp' : []}

        
        #self.SetBackgroundColour("WHITE")

        self._observer_ids = []
        # priority is higher than the default 0.0, so should be called
        # first
        self._observer_ids.append(self._rwi.AddObserver(
                'MouseMoveEvent', self._observer_mme, 0.2))

        self._observer_ids.append(self._rwi.AddObserver(
            'LeftButtonPressEvent', self._observer_lbpe))
        self._observer_ids.append(self._rwi.AddObserver(
            'LeftButtonReleaseEvent', self._observer_lbre))

        self._observer_ids.append(self._rwi.AddObserver(
            'MiddleButtonPressEvent', self._observer_mbpe))
        self._observer_ids.append(self._rwi.AddObserver(
            'MiddleButtonReleaseEvent', self._observer_mbre))
       
        self._observer_ids.append(self._rwi.AddObserver(
            'RightButtonPressEvent', self._observer_rbpe))
        self._observer_ids.append(self._rwi.AddObserver(
            'RightButtonReleaseEvent', self._observer_rbre))
        
        self.virtualWidth = 2048
        self.virtualHeight = 2048

        self.event = DeVIDECanvasEvent()
        

        # do initial drawing here.

    def close(self):
        # first remove all objects
        # (we could do this more quickly, but we're opting for neatly)
        for i in range(len(self._cobjects)-1,-1,-1):
            cobj = self._cobjects[i]
            self.remove_object(cobj)

        for i in self._observer_ids:
            self._rwi.RemoveObserver(i)

        del self._rwi
        del self._ren

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

    def display_to_world(self, dpt):
        """Takes 2-D display point as input, returns 3-D world point.
        """
        self._ren.SetDisplayPoint(dpt + (0.0,))
        self._ren.DisplayToWorld()
        return self._ren.GetWorldPoint()[0:3]

    def _observer_lbpe(self, o, e):
        self.event.left_button = True
        self.event.name = 'left_button_down'
        self.notify()

    def _observer_lbre(self, o, e):
        self.event.left_button = False
        self.event.dragging = False
        self.event.name = 'left_button_up'
        self.notify()

    def _observer_mbpe(self, o, e):
        self.event.middle_button = True
        self.event.name = 'middle_button_down'
        self.notify()

    def _observer_mbre(self, o, e):
        self.event.middle_button = False
        self.event.dragging = False
        self.event.name = 'middle_button_up'
        self.notify()

    def _observer_rbpe(self, o, e):
        self.event.right_button = True
        self.event.name = 'right_button_down'
        self.notify()

    def _observer_rbre(self, o, e):
        self.event.right_button = False
        self.event.dragging = False
        self.event.name = 'right_button_up'
        self.notify()

    def _observer_mme(self, o, e):
        """MouseMoveEvent observer for RWI.

        o contains a binding to the RWI.
        """

        # event position is viewport relative (i.e. in pixels,
        # bottom-left is 0,0)
        ex, ey = o.GetEventPosition()
        lex, ley = o.GetLastEventPosition()

        wex, wey, wez = self.display_to_world((ex,ey))
        lwex, lwey, lwez = self.display_to_world((lex,ley))

        # add the "real" coords to the event structure
        self.event.realX = wex 
        self.event.realY = wey
        self.event.realZ = wez 

        # also build into event
        self._mouseDelta = (wex -lwex, wey - lwey, wez - lwez)


        self.event.has_mouse = None # this will be set during this handler


        # we need to generate the following events for cobjects:
        # motion, enter

        p = vtk.vtkPicker()
        p.SetTolerance(0.001) # this is perhaps still too large
        ret = p.Pick((ex, ey, 0), self._ren)
        
        # use these two lines to limit picking
        #picker.AddPickList(p)
        #picker.PickFromListOn()

        if ret:
            #pc = p.GetProp3Ds()
            #pc.InitTraversal()
            #prop = pc.GetNextItemAsObject()
            prop = p.GetAssembly() # for now we only want this.
            try:
                picked_cobject = self._prop_to_cobject[prop]
            except KeyError:
                pass
            else:
                # need to find out WHICH sub-actor was picked.
                print p.GetPath().GetNumberOfItems()
                print p.GetPath().GetItemAsObject(0)
                print p.GetPath().GetItemAsObject(1)
                # our assembly is one level deep, so 1 is the one we
                # want (actor at leaf node)

                #p.GetPath().InitTraversal()
                #print p.GetPath().GetNextItemAsObject().GetViewProp()
                #print p.GetPath().GetNextItemAsObject().GetViewProp()
                self.event.name = 'motion'
                picked_cobject.notify()
                if not picked_cobject is self.event.has_mouse:
                    self.event.has_mouse = picked_cobject
                    self.event.name = 'enter'
                    picked_cobject.notify()

                if self.event.left_button:
                    # through the picking, we can distinguish between
                    # dragging the glyph itself, or dragging from one
                    # of its ports...
                    self.event.name = 'dragging'
                    picked_cobject.notify()

        else:
            # nothing under the mouse...
            if self.event.has_mouse:
                self.event.name = 'exit'
                self.event.has_mouse.notify()
                self.event.has_mouse = None


        return

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
            cobj.canvas = self
            self._cobjects.append(cobj)
            self._ren.AddViewProp(cobj.prop)
            self._prop_to_cobject[cobj.prop] = cobj
            cobj.__hasMouse = False

    def redraw(self):
        """Redraw the whole scene.
        """

        self._rwi.Render()

    def remove_object(self, cobj):
        if cobj and cobj in self._cobjects:
            self._ren.RemoveViewProp(cobj.prop)
            del self._prop_to_cobject[cobj.prop]
            cobj.canvas = None
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



