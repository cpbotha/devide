import vtk
from gen_mixins import SubjectMixin
from devide_canvas_object import DeVIDECanvasGlyph

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

        # this x,y is in VTK display coords
        # (bottom left of thingy is 0,0)
        self.disp_pos = (0,0)
        # we also need to convert the y to wx coordinates (top-left is
        # 0,0)

        self.world_pos = (0,0,0)

        # state information #################
        self.left_button = False
        self.middle_button = False
        self.right_button = False

        self.clicked_object = None

        # which cobject has the mouse
        self.has_mouse = None
        self.has_mouse_sub_prop = None



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
        self.prop_to_glyph = {}
        self._previousRealCoords = None
        self._mouseDelta = (0,0)
        self._potentiallyDraggedObject = None
        self._draggedObject = None

        
        self._ren.SetBackground(1.0,1.0,1.0)

        istyle = vtk.vtkInteractorStyleImage()
        self._rwi.SetInteractorStyle(istyle)

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

    # nuke this function, replace with display_to_world.
    # events are in display, everything else in world.
    # go back to graph_editor
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

    def display_to_world(self, dpt):
        """Takes 2-D display point as input, returns 3-D world point.
        """
        self._ren.SetDisplayPoint(dpt + (0.0,))
        self._ren.DisplayToWorld()
        return self._ren.GetWorldPoint()[0:3]

    def _helper_glyph_button_down(self, o, event_name):
        ex, ey = o.GetEventPosition()
        ret = self._pick_glyph(ex,ey)
        if ret:
            pc, psp = ret
            self.event.clicked_object = pc
            self.event.name = event_name
            pc.notify(event_name)
        else:
            self.event.clicked_object = None

        self.event.name = event_name
        self.notify(event_name)
            
    def _helper_glyph_button_up(self, o, event_name):
        ex, ey = o.GetEventPosition()
        ret = self._pick_glyph(ex,ey)
        if ret:
            pc, psp = ret
            self.event.name = event_name
            pc.notify(event_name)

        self.event.clicked_object = None
        self.event.name = event_name
        self.notify(event_name)

    def _observer_lbpe(self, o, e):
        self.event.left_button = True
        self._helper_glyph_button_down(o, 'left_button_down')

    def _observer_lbre(self, o, e):
        self.event.left_button = False
        self._helper_glyph_button_up(o, 'left_button_up')

    def _observer_mbpe(self, o, e):
        self.event.middle_button = True
        self._helper_glyph_button_down(o, 'middle_button_down')

    def _observer_mbre(self, o, e):
        self.event.middle_button = False
        self._helper_glyph_button_up(o, 'middle_button_up')

    def _observer_rbpe(self, o, e):
        self.event.right_button = True
        self._helper_glyph_button_down(o, 'right_button_down')


    def _observer_rbre(self, o, e):
        self.event.right_button = False
        self._helper_glyph_button_up(o, 'right_button_up')

    def _pick_glyph(self, ex, ey):
        """Give current event coordinate (as returned by
        rwi.GetEventPosition()) return picked cobject and the picked
        sub-prop.
        """
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
                picked_cobject = self.prop_to_glyph[prop]
            except KeyError:
                return None
            else:
                # need to find out WHICH sub-actor was picked.
                if p.GetPath().GetNumberOfItems() == 2:
                    sub_prop = p.GetPath().GetItemAsObject(1)

                else:
                    sub_prop = None

                #print p.GetPath().GetNumberOfItems()
                #print p.GetPath().GetItemAsObject(0)
                #print p.GetPath().GetItemAsObject(1)
                # our assembly is one level deep, so 1 is the one we
                # want (actor at leaf node)

                #p.GetPath().InitTraversal()
                #print p.GetPath().GetNextItemAsObject().GetViewProp()
                #print p.GetPath().GetNextItemAsObject().GetViewProp()

                return (picked_cobject, sub_prop)

        return None


    def _observer_mme(self, o, e):
        """MouseMoveEvent observer for RWI.

        o contains a binding to the RWI.
        """

        # event position is viewport relative (i.e. in pixels,
        # bottom-left is 0,0)
        ex, ey = o.GetEventPosition()
        self.event.disp_pos = ex, ey

        # we need to flip the y for wx-relative coords
        self.event.disp_posf = ex, o.GetSize()[1] - ey - 1

        lex, ley = o.GetLastEventPosition()

        wex, wey, wez = self.display_to_world((ex,ey))
        self.world_pos = wex, wey, wez
        lwex, lwey, lwez = self.display_to_world((lex,ley))

        # add the "real" coords to the event structure
        self.event.realX = wex 
        self.event.realY = wey
        self.event.realZ = wez 

        # also build into event
        self._mouseDelta = (wex -lwex, wey - lwey, wez - lwez)


        self.event.has_mouse = None # this will be set during this handler
        self.event.has_mouse_sub_prop = None


        # we need to generate the following events for cobjects:
        # motion, enter
        pg_ret = self._pick_glyph(ex, ey)
        if pg_ret:
            picked_cobject, picked_sub_prop = pg_ret

            if not picked_cobject is self.event.has_mouse:
                self.event.has_mouse = picked_cobject
                self.event.has_mouse_sub_prop = picked_sub_prop
                self.event.name = 'enter'
                picked_cobject.notify('enter')

            if self.event.left_button and \
            self.event.clicked_object is picked_cobject:
                self.event.name = 'dragging'
                picked_cobject.notify('dragging')

            else:
                self.event.name = 'motion'
                picked_cobject.notify('motion')

        else:
            # nothing under the mouse...
            if self.event.has_mouse:
                self.event.name = 'exit'
                self.event.has_mouse.notify('exit')
                self.event.has_mouse = None

    def add_object(self, cobj):
        if cobj and cobj not in self._cobjects:
            cobj.canvas = self
            self._cobjects.append(cobj)
            self._ren.AddViewProp(cobj.prop)
            # we only add prop to cobject if it's a glyph
            if isinstance(cobj, DeVIDECanvasGlyph):
                self.prop_to_glyph[cobj.prop] = cobj

            cobj.__hasMouse = False

    def redraw(self):
        """Redraw the whole scene.
        """

        self._rwi.Render()

    def remove_object(self, cobj):
        if cobj and cobj in self._cobjects:
            self._ren.RemoveViewProp(cobj.prop)
            del self.prop_to_glyph[cobj.prop]
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



