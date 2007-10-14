import vtk
from gen_mixins import SubjectMixin
from devide_canvas_object import DeVIDECanvasGlyph
import operator

import wx # we're going to use this for event handling

# think about turning this into a singleton.
class DeVIDECanvasEvent:
    def __init__(self):
        # last event information ############
        self.wx_event = None

        self.name = None
        #self.left_button_down = False
        #self.left_button_up = False
        #self.middle_button_down = False
        #self.middle_button_up = False
        #self.right_button_down = False
        #self.right_button_up = False

        self.pos = (0,0)
        self.last_pos = (0,0)
        self.pos_delta = (0,0)

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
        self._potentiallyDraggedObject = None
        self._draggedObject = None

        
        self._ren.SetBackground(1.0,1.0,1.0)

        istyle = vtk.vtkInteractorStyleUser()
        #istyle = vtk.vtkInteractorStyleImage()
        self._rwi.SetInteractorStyle(istyle)

        self._rwi.Bind(wx.EVT_RIGHT_DOWN, self._handler_rd)
        self._rwi.Bind(wx.EVT_RIGHT_UP, self._handler_ru)
        self._rwi.Bind(wx.EVT_LEFT_DOWN, self._handler_ld)
        self._rwi.Bind(wx.EVT_LEFT_UP, self._handler_lu)
        self._rwi.Bind(wx.EVT_MIDDLE_DOWN, self._handler_md)
        self._rwi.Bind(wx.EVT_MIDDLE_UP, self._handler_mu)
        self._rwi.Bind(wx.EVT_MOUSEWHEEL, self._handler_wheel)
        self._rwi.Bind(wx.EVT_MOTION, self._handler_motion)
        #self._rwi.Bind(wx.EVT_ENTER_WINDOW, self.OnEnter)
        #self._rwi.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeave)

        # If we use EVT_KEY_DOWN instead of EVT_CHAR, capital versions
        # of all characters are always returned.  EVT_CHAR also performs
        # other necessary keyboard-dependent translations.
        #self._rwi.Bind(wx.EVT_CHAR, self.OnKeyDown)
        #self._rwi.Bind(wx.EVT_KEY_UP, self.OnKeyUp)



        self._observer_ids = []

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
        """Takes 3-D display point as input, returns 3-D world point.
        """

        # make sure we have 3 elements 
        if len(dpt) < 3:
            dpt = tuple(dpt) + (0.0,)
        elif len(dpt) > 3:
            dpt = tuple(dpt[0:3])

        self._ren.SetDisplayPoint(dpt)
        self._ren.DisplayToWorld()
        return self._ren.GetWorldPoint()[0:3]

    def world_to_display(self, wpt):
        """Takes 3-D world point as input, returns 3-D display point.
        """
        self._ren.SetWorldPoint(tuple(wpt) + (0.0,)) # this takes 4-vec
        self._ren.WorldToDisplay()
        return self._ren.GetDisplayPoint()

    def _helper_handler_preamble(self, e):
        e.Skip(False) 
        # Skip(False) won't search for other event
        # handlers
        self.event.wx_event = e
        # we need to take focus... else some other subwindow keeps it
        # once we've been there to select a module for example
        self._rwi.SetFocus()

    def _helper_glyph_button_down(self, event_name):
        ex, ey = self.event.disp_pos 
        ret = self._pick_glyph(ex,ey)
        if ret:
            pc, psp = ret
            self.event.clicked_object = pc
            self.event.name = event_name
            pc.notify(event_name)
        else:
            self.event.clicked_object = None

            # we only give the canvas the event if the glyph didn't
            # take it
            self.event.name = event_name
            self.notify(event_name)
            
    def _helper_glyph_button_up(self, event_name):
        ex, ey = self.event.disp_pos
        ret = self._pick_glyph(ex,ey)
        if ret:
            pc, psp = ret
            self.event.name = event_name
            pc.notify(event_name)
        else:
            self.event.clicked_object = None
            self.event.name = event_name
            self.notify(event_name)

    def _handler_ld(self, e):
        self._helper_handler_preamble(e)
        
        #ctrl, shift = event.ControlDown(), event.ShiftDown()
        #self._Iren.SetEventInformationFlipY(event.GetX(), event.GetY(),
        #                                    ctrl, shift, chr(0), 0, None)

        self.event.left_button = True
        self._helper_glyph_button_down('left_button_down')

    def _handler_lu(self, e):
        self._helper_handler_preamble(e)
        self.event.left_button = False
        self._helper_glyph_button_up('left_button_up')

    def _handler_md(self, e):
        self._helper_handler_preamble(e)
        self.event.middle_button = True
        self._helper_glyph_button_down('middle_button_down')

    def _handler_mu(self, e):
        self._helper_handler_preamble(e)
        self.event.middle_button = False
        self._helper_glyph_button_up('middle_button_up')

    def _handler_rd(self, e):
        self._helper_handler_preamble(e)
        self.event.right_button = True
        self._helper_glyph_button_down('right_button_down')


    def _handler_ru(self, e):
        self._helper_handler_preamble(e)
        self.event.right_button = False
        self._helper_glyph_button_up('right_button_up')

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


    def _handler_wheel(self, event):
        # also see vtkInteractorStyleTrackballCamera::Dolly() for
        # how to do this with parallel projection
        
        factor = [2.0, -2.0][event.GetWheelRotation() > 0.0] 
        self._ren.GetActiveCamera().Dolly(1.1 ** factor)
        self._ren.ResetCameraClippingRange()
        self._ren.UpdateLightsGeometryToFollowCamera()
        self.redraw()
        #event.GetWheelDelta()

    def _flip_y(self, y):
        return self._rwi.GetSize()[1] - y - 1

    def _handler_motion(self, event):
        """MouseMoveEvent observer for RWI.

        o contains a binding to the RWI.
        """

        #self._helper_handler_preamble(event)
        self.event.wx_event = event

        # event position is viewport relative (i.e. in pixels,
        # bottom-left is 0,0)
        ex, ey = event.GetX(), event.GetY() 
       
        # we need to flip Y to get VTK display coords
        self.event.disp_pos = ex, self._rwi.GetSize()[1] - ey - 1
       
        # before setting the new pos, record the delta
        self.event.pos_delta = (ex - self.event.pos[0], 
                ey - self.event.pos[1])
        self.event.last_pos = self.event.pos
        self.event.pos = ex, ey


        wex, wey, wez = self.display_to_world(self.event.disp_pos)
        self.event.world_pos = wex, wey, wez

        # add the "real" coords to the event structure
        self.event.realX = wex 
        self.event.realY = wey
        self.event.realZ = wez 


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

        if event.Dragging() and event.MiddleIsDown():
            # move camera, according to self.event.pos_delta
            c = self._ren.GetActiveCamera()
            cfp = list(c.GetFocalPoint())
            cp = list(c.GetPosition())
            
            focal_depth = self.world_to_display(cfp)[2]

            new_pick_pt = self.display_to_world(self.event.disp_pos +
                    (focal_depth,))

            fy = self._flip_y(self.event.last_pos[1])
            old_pick_pt = self.display_to_world((self.event.last_pos[0], fy,
                    focal_depth))

            # old_pick_pt - new_pick_pt (reverse of camera!)
            motion_vector = map(operator.sub, old_pick_pt,
                    new_pick_pt)
            print motion_vector

            new_cfp = map(operator.add, cfp, motion_vector)
            new_cp = map(operator.add, cp, motion_vector)
            
            c.SetFocalPoint(new_cfp)
            c.SetPosition(new_cp)
            self.redraw()

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



