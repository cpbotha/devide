# graph_editor.py copyright 2002 by Charl P. Botha http://cpbotha.net/
# $Id: graph_editor.py,v 1.35 2003/01/29 12:09:22 cpbotha Exp $
# the graph-editor thingy where one gets to connect modules together

from wxPython.wx import *
from wxPython.ogl import *
import gen_utils
import string
import traceback

# we have to call this to do some global OGL init
wxOGLInitialize()

# wxGTK 2.3.2.1 bugs with mouse capture (BADLY), so we disable this
try:
    WX_USE_X_CAPTURE
except NameError:
    if wxPlatform == '__WXMSW__':
        WX_USE_X_CAPTURE = 1
    else:
        WX_USE_X_CAPTURE = 0

# ----------------------------------------------------------------------------
class wxFRectangleShape(wxRectangleShape):
    """This adds one method to the wxRectangleShape which can be used
    to fix a stupid wx bug.

    inout_shape is derived from this, and the main rectangle shape of a
    glyph is an instance of this.
    """
    def dont_move(self):
        """This fixes the stupid bug where Show()d shapes have to be moved to
        their own position to appear on the canvas.
        """
        if self.GetCanvas():
            dc = wxClientDC(self.GetCanvas())
            self.GetCanvas().PrepareDC(dc)
            self.Move(dc, self.GetX(), self.GetY())

# ----------------------------------------------------------------------------
class inout_shape(wxFRectangleShape):
    """Special shape for connection points on glyphs.

    This point has the drag events overridden so that wxLineShapes
    can be drawn.  During a drag, an arrow will be drawn; when the drag is
    done, the line with arrow will be removed and the main glyph shape will
    be notified.  The main glyph shape will then notify its owning glyph,
    I think.
    """
    def __init__(self, width, height, inout, parent_glyph):
        """Special init for inout shape that stores parent glyph as well as
        a flag indicating whether this is an in shape or an out shape.

        If inout is 1, this is an in shape.
        """
        self._inout = inout
        self._parent_glyph = parent_glyph
        wxFRectangleShape.__init__(self, width, height)

    def OnLeftClick(self, x, y, keys, attachment):
        ge = self.GetCanvas().get_graph_editor()
        ge.inout_leftclick_cb(self._parent_glyph, self,
                              x, y, keys, attachment)
        
    def OnDragLeft(self, draw, x, y, keys, attachment):
        ge = self.GetCanvas().get_graph_editor()
        ge.inout_dragleft_cb(self._parent_glyph, self,
                             x, y, keys, attachment)
    
    def OnBeginDragLeft(self, x, y, keys, attachment):
        ge = self.GetCanvas().get_graph_editor()
        ge.inout_begindragleft_cb(self._parent_glyph, self,
                                  x, y, keys, attachment)

    def OnEndDragLeft(self, x, y, keys, attachment):
        ge = self.GetCanvas().get_graph_editor()
        ge.inout_enddragleft_cb(self._parent_glyph, self,
                                x, y, keys, attachment)

    def get_inout(self):
        return self._inout

    def get_parent_glyph(self):
        return self._parent_glyph

# ----------------------------------------------------------------------------
class ge_glyph_shape(wxFRectangleShape):
    """This is our own little composite shape.

    It is used by the ge_glyph for displaying and catching events.  It's
    derived from the wxFRectangleShape, but it also contains a number
    of wxFRectangleShapes which it uses for the little connection points.
    """
    def __init__(self, canvas, glyph, x, y, num_inputs, num_outputs):
        self._glyph = glyph
        self._width = 80
        self._height = 40
        # call the parent constructor
        wxRectangleShape.__init__(self, self._width, self._height)
        # add the label
        self.AddText(self._glyph.get_name())
        # we want to be a drag
        self.SetDraggable(true)
        # position
        self.SetX(x)
        self.SetY(y)
        # add ourselves to the canvas
        canvas.AddShape(self)
        # then make ourselves display
        self.Show(true)
        self.dont_move()

        # draw all the input shapes
        self._input_shapes = []
        self._input_incr = 7
        tl_x = self.GetX() - self._width / 2
        tl_y = self.GetY() - self._height / 2
        for i in range(num_inputs):
            ishape = inout_shape(5, 5, 1, self._glyph)
            ishape.SetX(tl_x)
            ishape.SetY(tl_y + self._input_incr * len(self._input_shapes))
            canvas.AddShape(ishape)
            ishape.Show(true)
            ishape.dont_move()
            self._input_shapes.append(ishape)
            
            
        # and the output shapes
        self._output_shapes = []
        tr_x = self.GetX() + self._width / 2
        tr_y = self.GetY() - self._height / 2
        for i in range(num_outputs):
            oshape = inout_shape(5, 5, 0, self._glyph)
            oshape.SetX(tr_x)
            oshape.SetY(tr_y + self._input_incr * len(self._output_shapes))
            canvas.AddShape(oshape)
            oshape.Show(true)
            oshape.dont_move()
            self._output_shapes.append(oshape)

    def close(self):
        dc = wxClientDC(self.GetCanvas())
        self.GetCanvas().PrepareDC(dc)
        
        for shape in self._input_shapes + self._output_shapes + [self]:
            shape.Erase(dc)
            self.GetCanvas().RemoveShape(shape)

    def get_input_shapes(self):
        return self._input_shapes

    def get_output_shapes(self):
        return self._output_shapes

    def find_input_idx(self, io_shape):
        try:
            return self._input_shapes.index(io_shape)
        except:
            return None
        

    def find_output_idx(self, io_shape):
        try:
            return self._output_shapes.index(io_shape)
        except:
            return None

    def OnEndDragLeft(self, x, y, keys, attachment):
        """Overridden event handler so that we can move the input and outputs
        along once the user has placed the glyph.
        """
        # make sure our main rectangle moves
        wxFRectangleShape.base_OnEndDragLeft(self, x, y, keys, attachment)

        # prepare a dc for the canvas
        dc = wxClientDC(self.GetCanvas())
        self.GetCanvas().PrepareDC(dc)
        
        # move all the inputs
        tl_x = self.GetX() - self._width / 2
        tl_y = self.GetY() - self._height / 2
        i = 0
        for ishape in self._input_shapes:
            # nuke the old shape
            ishape.Erase(dc)
            # draw in new position
            ishape.Move(dc, tl_x, tl_y + self._input_incr * i)
            i += 1

        # move all the outputs
        tr_x = self.GetX() + self._width / 2
        tr_y = self.GetY() - self._height / 2
        i = 0
        for oshape in self._output_shapes:
            # nuke old shape
            oshape.Erase(dc)
            # draw new position
            oshape.Move(dc, tr_x, tr_y + self._input_incr * i)
            i += 1
            
        # this fixes some drawing problems (we'll have to optimise!)
        self.GetCanvas().Redraw(dc)

    def OnRightClick(self, x, y, keys, attachment):
        # see studio/shapes.cpp: csEvtHandler::OnRightClick
        ge = self.GetCanvas().get_graph_editor()
        ge.mshape_rightclick_cb(x, y, keys, attachment, self._glyph)
        
        
        
# ----------------------------------------------------------------------------
class ge_glyph:
    def __init__(self, shape_canvas, name, module_instance, x, y):
        # some instance variables
        self._name = name
        self._module_instance = module_instance
        input_descrs = self._module_instance.getInputDescriptions()
        output_descrs = self._module_instance.getOutputDescriptions()
        self._shape = ge_glyph_shape(shape_canvas, self, x, y,
                                     len(input_descrs), len(output_descrs))

    def close(self):
        """This method will remove all traces of the glyph from existence.

        Important note: we did not create the module instance, so we will
        NOT destroy it.  Also, we're not responsible for the links.  So,
        destroy the module instance, disconnect all links to and from it,
        then call this close method.  Okay?
        """
        self._shape.close()
        

    def get_name(self):
        return self._name

    def get_main_shape(self):
        return self._shape

    def get_module_instance(self):
        return self._module_instance

# ----------------------------------------------------------------------------
class geShapeCanvas(wxShapeCanvas):
    """Graph editor canvas.

    We have overridden the canvas to catch mouse events on the canvas itself.
    In addition, this is a sneaky way for shapes to pass their events to the
    main graph_editor class via their canvas.
    """
    def __init__(self, parent):
        wxShapeCanvas.__init__(self, parent)
        self.SetScrollbars(20, 20, 100, 100)
        self._graph_editor = None

    def OnLeftClick(self, x, y, keys):
        self._graph_editor.canvas_left_click_cb(x,y,keys)

    def get_graph_editor(self):
        return self._graph_editor

    def setGraphEditor(self, graphEditor):
        self._graph_editor = graphEditor

# ----------------------------------------------------------------------------
class graph_editor:
    def __init__(self, dscas3_app):
        # initialise vars
        self._dscas3_app = dscas3_app

        import resources.python.graphEditorFrame
        self._graph_frame = resources.python.graphEditorFrame.graphEditorFrame(
            self._dscas3_app.get_main_window(),
            -1, title='dummy', geShapeCanvas=geShapeCanvas)
        self._graph_frame.shapeCanvas.setGraphEditor(self)

        self._diagram = wxDiagram()
        self._graph_frame.shapeCanvas.SetDiagram(self._diagram)
        self._diagram.SetCanvas(self._graph_frame.shapeCanvas)
        

        EVT_CLOSE(self._graph_frame, self.close_graph_frame_cb)        

        EVT_BUTTON(self._graph_frame, self._graph_frame.rescanButtonId,
                   lambda e, s=self: s.fill_module_tree())

        self.fill_module_tree()
        
        # now display the shebang
        self.show()

    def fill_module_tree(self):
        self._graph_frame.treeCtrl.DeleteAllItems()

        tree_root = self._graph_frame.treeCtrl.AddRoot('Modules')
        rdrn = self._graph_frame.treeCtrl.AppendItem(tree_root, 'Readers')
        wrtn = self._graph_frame.treeCtrl.AppendItem(tree_root, 'Writers')
        vwrn = self._graph_frame.treeCtrl.AppendItem(tree_root, 'Viewers')
        fltn = self._graph_frame.treeCtrl.AppendItem(tree_root, 'Filters')
        miscn = self._graph_frame.treeCtrl.AppendItem(tree_root, 'Misc')

        self._dscas3_app.get_module_manager().scan_modules()
        for cur_mod in self._dscas3_app.get_module_manager().get_module_list():
            mtype = cur_mod[-3:].lower()
            if mtype == 'rdr':
                self._graph_frame.treeCtrl.AppendItem(rdrn, cur_mod)
            elif mtype == 'wrt':
                self._graph_frame.treeCtrl.AppendItem(wrtn, cur_mod)
            elif mtype == 'vwr':
                self._graph_frame.treeCtrl.AppendItem(vwrn, cur_mod)
            elif mtype == 'flt':
                self._graph_frame.treeCtrl.AppendItem(fltn, cur_mod)
            else:
                self._graph_frame.treeCtrl.AppendItem(miscn, cur_mod)

        # only do stuff if !ItemHasChildren()

    def close_graph_frame_cb(self, event):
        self.hide()

    def show(self):
        self._graph_frame.Show(true)

    def hide(self):
        self._graph_frame.Show(false)

    def draw_preview_line(self, io_shape, to_x, to_y):
        # dotted line
        dotted_pen = wxPen('#000000', 1, wxDOT)
        # make a DC to draw on
        dc = wxClientDC(self._graph_frame.shapeCanvas)
        self._graph_frame.shapeCanvas.PrepareDC(dc)
        dc.SetLogicalFunction(wxINVERT) # NOT dst
        dc.SetPen(dotted_pen)
        # draw the line (I honestly don't know what happens to the previous
        # one)
        dc.DrawLine(io_shape.GetX(), io_shape.GetY(), to_x, to_y)

    def connect_glyphs_by_shapes(self, from_io_shape, to_io_shape):
        # get the main shapes associated with the actual glyphs
        from_glyph = from_io_shape.get_parent_glyph()
        from_mn_shape = from_glyph.get_main_shape()
        to_glyph = to_io_shape.get_parent_glyph()
        to_mn_shape = to_glyph.get_main_shape()
        # also find the output and input indexes on the source
        # and destination glyphs
        out_idx = from_mn_shape.find_output_idx(from_io_shape)
        in_idx = to_mn_shape.find_input_idx(to_io_shape)
        # if these are valid
        if in_idx != None and out_idx != None:
            try:
                mm = self._dscas3_app.get_module_manager()
                mm.connect_modules(from_glyph.get_module_instance(), out_idx,
                                   to_glyph.get_module_instance(), in_idx)
                # create a connecting line
                conn = wxLineShape()
                conn.MakeLineControlPoints(2)
                conn.AddArrow(ARROW_ARROW, ARROW_POSITION_END)
                self._graph_frame.shapeCanvas.AddShape(conn)
                from_io_shape.AddLine(conn, to_io_shape)
                conn.Show(true)
                # fix the fuxors
                from_io_shape.dont_move()
                to_io_shape.dont_move()
            except Exception, e:
                gen_utils.log_error('Could not connect modules: %s' % (str(e)))
                
    def disconnect_glyphs_by_ishape(self, ishape):
        if len(ishape.GetLines()) > 0:
            try:
                # there can be only one
                the_line = ishape.GetLines()[0]
                # get the output (from) shape
                oshape = the_line.GetFrom()
                
                # we need to get the input idx
                to_glyph = ishape.get_parent_glyph()
                in_idx = to_glyph.get_main_shape().find_input_idx(ishape)
                # get the module manager
                mm = self._dscas3_app.get_module_manager()
                # disconnect that shape
                mm.disconnect_modules(to_glyph.get_module_instance(), in_idx)
                
                # now perform the surgery on the canvas
                # disconnect the line
                the_line.Unlink()
                # erase it
                dc =  wxClientDC(self._graph_frame.shapeCanvas)
                self._graph_frame.shapeCanvas.PrepareDC(dc)
                the_line.Erase(dc)
                # remove it from the canvas (actually the diagram)
                self._graph_frame.shapeCanvas.RemoveShape(the_line)
            except Exception, e:
                gen_utils.log_error('Could not disconnect modules: %s' \
                                    % (str(e)))

    def disconnect_glyphs_by_oshape(self, oshape):
        # iterate through all the lines emanating from oshape
        for line in oshape.GetLines():
            self.disconnect_glyphs_by_ishape(line.GetTo())

    def redraw_canvas(self):
        dc = wxClientDC(self._graph_frame.shapeCanvas)
        self._graph_frame.shapeCanvas.PrepareDC(dc)
        self._graph_frame.shapeCanvas.Redraw(dc)

    def canvas_left_click_cb(self, x, y, keys):
        # first see what mode we are in
        # blah blah

        # we are in "create/edit" mode, so let's create some glyph
        # first get the currently selected tree node
        sel_item = self._graph_frame.treeCtrl.GetSelection()
        # then the root node
        root_item = self._graph_frame.treeCtrl.GetRootItem()
        if root_item != sel_item and \
           self._graph_frame.treeCtrl.GetItemParent(sel_item) != root_item:
            # we have a valid module, we should try and instantiate
            mod_name = self._graph_frame.treeCtrl.GetItemText(sel_item)
            mm = self._dscas3_app.get_module_manager()
            temp_module = mm.create_module(mod_name)
            # if the module_manager did its trick, we can make a glyph
            if temp_module:
                ge_glyph(self._graph_frame.shapeCanvas, mod_name, temp_module, x, y)

    def updatePortInfoStatusbar(self, from_io_shape, to_io_shape):
        from_msg = 'N/A'
        to_msg = ''

        for io_shape in (from_io_shape, to_io_shape):
            glyph = io_shape.get_parent_glyph()
            if io_shape.get_inout():
                idx = glyph.get_main_shape().find_input_idx(io_shape)
                msg = glyph.get_module_instance().getInputDescriptions()[idx]
            else:
                idx = glyph.get_main_shape().find_output_idx(io_shape)
                msg = glyph.get_module_instance().getOutputDescriptions()[idx]

        self._graph_frame.GetStatusBar().SetStatusText(msg)
        
    def inout_leftclick_cb(self, parent_glyph, io_shape,
                           x, y, keys, attachment):
        self.updatePortInfoStatusbar(io_shape)
                
    def inout_begindragleft_cb(self, parent_glyph, io_shape,
                               x, y, keys, attachment):
        if io_shape.get_inout() == 0:
            # user is beginning a connection
            self.draw_preview_line(io_shape, x, y)
            self.updatePortInfoStatusbar(io_shape)
        else:
            # if there is a line connected to this input, the user
            # might be removing or repositioning
            if len(io_shape.GetLines()) > 0:
                # by definition, this can be only one line
                ltn = io_shape.GetLines()[0]
                self.draw_preview_line(ltn.GetFrom(), x, y)

        # make sure the user knows which ports we're dealing with
        self.updatePortInfoStatusbar(io_shape)

        # after doing our setup, we capture the mouse so things don't
        # get confused when the user waves his wand outside the canvas
        if WX_USE_X_CAPTURE:
            self._graph_frame.shapeCanvas.CaptureMouse()        

    def inout_enddragleft_cb(self, parent_glyph, io_shape,
                             x, y, keys, attachment):
        # give the mouse back ASAP, else people get angry, he he
        if WX_USE_X_CAPTURE:
            self._graph_frame.shapeCanvas.ReleaseMouse()

        # find shape that we're close to (we will need this in both cases)
        f_ret = self._graph_frame.shapeCanvas.FindShape(x, y, None)

        if io_shape.get_inout() == 0:
            # if it's not the originating io_shape but it is another io_shape,
            # and that other shape is an input shape, we can consider playing
            if f_ret and f_ret[0] != io_shape and \
               hasattr(f_ret[0], 'get_inout') and f_ret[0].get_inout() == 1:
                to_shape = f_ret[0]
                # make sure there's nothing else connected to this input
                if len(to_shape.GetLines()) == 0:
                    self.connect_glyphs_by_shapes(io_shape, to_shape)

        else:
            # this drag event had an input shape as origin
            if len(io_shape.GetLines()) > 0:
                # there is a line connected to this input io_shape
                # so the user was busy with a remove or relocate
                if f_ret and f_ret[0] != io_shape and \
                   hasattr(f_ret[0], 'get_inout') and \
                   f_ret[0].get_inout() == 1 and \
                   len(f_ret[0].GetLines()) == 0:
                    # the user has dropped us on a NEW (different)
                    # input shape that hasn't been connected to yet:
                    # this means that we must break the old connection
                    # and create a new one
                    from_shape = io_shape.GetLines()[0].GetFrom()
                    self.disconnect_glyphs_by_ishape(io_shape)
                    self.connect_glyphs_by_shapes(from_shape, f_ret[0])
                elif f_ret and f_ret[0] == io_shape:
                    # this means the user dropped us back where we started,
                    # i.e. she DOESN't want to change anything, so we do
                    # nothing
                    pass
                else:
                    # the user has let the drag go NOT on an new or the
                    # original destination io_shape,
                    # which probably means that she wanted to disconnect
                    self.disconnect_glyphs_by_ishape(io_shape)
                

    def inout_dragleft_cb(self, parent_glyph, io_shape,
                          x, y, keys, attachment):
        # if the originating shape is an output shape, we can make
        # the line
        if io_shape.get_inout() == 0:
            self.draw_preview_line(io_shape, x, y)
        else:
            # if there is a line connected to this input, the user
            # might be removing or repositioning
            if len(io_shape.GetLines()) > 0:
                # by definition, this can be only one line
                ltn = io_shape.GetLines()[0]
                self.draw_preview_line(ltn.GetFrom(), x, y)

        # find shape that we're close to (we will need this in both cases)
        f_ret = self._graph_frame.shapeCanvas.FindShape(x, y, None)

        # if it's not the originating io_shape but it is another io_shape,
        # and that other shape is an input shape, we can consider playing
        if f_ret and hasattr(f_ret[0], 'get_inout'):
            self.updatePortInfoStatusbar(f_ret[0])

    def mshape_rightclick_cb(self, x, y, keys, attachment, glyph):
        pmenu = wxMenu(glyph.get_name())

        vc_id = wxNewId()
        pmenu.AppendItem(wxMenuItem(pmenu, vc_id, "View-Configure"))
        EVT_MENU(self._graph_frame.shapeCanvas, vc_id,
                 lambda e, s=self, glyph=glyph: s.vc_shape_cb(glyph))
        
        del_id = wxNewId()
        pmenu.AppendItem(wxMenuItem(pmenu, del_id, 'Delete'))
        EVT_MENU(self._graph_frame.shapeCanvas, del_id,
                 lambda e, s=self, glyph=glyph: s.del_shape_cb(glyph))

        mcs_id = wxNewId()
        pmenu.AppendItem(wxMenuItem(pmenu, mcs_id,
                                    'Make current'))
        EVT_MENU(self._graph_frame.shapeCanvas, mcs_id,
                 lambda e, s=self, glyph=glyph:
                 s._dscas3_app.get_module_manager().set_current_module(
            glyph.get_module_instance()))

        # where have we scrolled the canvas to
        view_start = self._graph_frame.shapeCanvas.GetViewStart()
        # to go from canvas units to pixels
        sppu = self._graph_frame.shapeCanvas.GetScrollPixelsPerUnit()
        # event coords to pixels
        x1 = x * self._graph_frame.shapeCanvas.GetScaleX()
        y1 = y * self._graph_frame.shapeCanvas.GetScaleY()
        # subtract scrolled offset
        mnx = x1 - view_start[0] * sppu[0]
        mny = y1 - view_start[1] * sppu[1]
        # popup that menu!
        self._graph_frame.shapeCanvas.PopupMenu(pmenu, wxPoint(mnx, mny))

    def vc_shape_cb(self, glyph):
        mm =self._dscas3_app.get_module_manager()
        mm.view_module(glyph.get_module_instance())

    def del_shape_cb(self, glyph):
        try:
            # delete all incoming connections
            for ishape in glyph.get_main_shape().get_input_shapes():
                self.disconnect_glyphs_by_ishape(ishape)
            # delete all outgoing connections
            for oshape in glyph.get_main_shape().get_output_shapes():
                self.disconnect_glyphs_by_oshape(oshape)
            # we're going to destroy the glyph, make sure we keep tabs
            module_instance = glyph.get_module_instance()
            glyph.close()
            # if all that worked, we can nuke the module
            mm = self._dscas3_app.get_module_manager()
            mm.delete_module(module_instance)

        except Exception, e:
            gen_utils.log_error('Could not delete module: %s' % (str(e)))
        
                         
            
            

        
