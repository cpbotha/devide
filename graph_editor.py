# graph_editor.py copyright 2002 by Charl P. Botha http://cpbotha.net/
# $Id: graph_editor.py,v 1.20 2002/04/25 14:32:21 cpbotha Exp $
# the graph-editor thingy where one gets to connect modules together

from wxPython.wx import *
from wxPython.ogl import *

# we have to call this to do some global OGL init
wxOGLInitialize()

# ----------------------------------------------------------------------------
class wxFRectangleShape(wxRectangleShape):
    """This adds one method to the wxRectangleShape which can be used
    to fix a stupid wx bug.
    """
    def dont_move(self):
        """This fixes the stupid bug where Show()d have to be moved to
        their own position to appear on the canvas.
        """
        if self.GetCanvas():
            dc = wxClientDC(self.GetCanvas())
            self.GetCanvas().PrepareDC(dc)
            self.Move(dc, self.GetX(), self.GetY())

class inout_shape(wxFRectangleShape):
    """Special shape for connection points on glyphs.

    This point has the drag events overridden so that wxLineShapes
    can be drawn.  During a drag, an arrow will be drawn; when the drag is
    done, the line with arrow will be removed and the main glyph shape will
    be notified.  The main glyph shape will then notify its owning glyph,
    I think.
    """
    def OnDragLeft(self, draw, x, y, keys, attachment):
        print "dragging..."
    
    def OnBeginDragLeft(self, x, y, keys, attachment):
        print "begin drag"

        self.GetCanvas().CaptureMouse()
    
    def OnEndDragLeft(self, x, y, keys, attachment):
        self.GetCanvas().ReleaseMouse()
        print "end drag"
        

# ----------------------------------------------------------------------------
class ge_glyph_shape(wxFRectangleShape):
    """This is our own little composite shape.

    It is used by the ge_glyph for displaying and catching events.  It's
    derived from the wxFRectangleShape, but it also contains a number
    of wxFRectangleShapes which it uses for the little connection points.
    """
    def __init__(self, canvas, name, x, y, num_inputs, num_outputs):
        self._width = 80
        self._height = 40
        # call the parent constructor
        wxRectangleShape.__init__(self, self._width, self._height)
        # add the label
        self.AddText(name)
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
            ishape = inout_shape(5, 5)
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
            oshape = inout_shape(5, 5)
            oshape.SetX(tr_x)
            oshape.SetY(tr_y + self._input_incr * len(self._output_shapes))
            canvas.AddShape(oshape)
            oshape.Show(true)
            oshape.dont_move()
            self._output_shapes.append(oshape)

    def Move(self, dc, to_x, to_y, display=true):
        print "Move!"
        wxFRectangleShape.Move(self, dc, to_x, to_y, display)

    def OnEndDragLeft(self, x, y, keys, attachment):
        print "OnEndDragLeft"
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
        
        

        
        
# ----------------------------------------------------------------------------
class ge_glyph:
    def __init__(self, shape_canvas, name, module_instance, x, y):
        # some instance variables
        self._module_instance = module_instance
        input_descrs = self._module_instance.get_input_descriptions()
        output_descrs = self._module_instance.get_output_descriptions()
        self._shape = ge_glyph_shape(shape_canvas, name, x, y,
                                     len(input_descrs), len(output_descrs))

# ----------------------------------------------------------------------------
class ge_shape_canvas(wxShapeCanvas):
    def __init__(self, parent, graph_editor):
        wxShapeCanvas.__init__(self, parent)
        self.SetScrollbars(20, 20, 100, 100)
        self._graph_editor = graph_editor

    def OnLeftClick(self, x, y, keys):
        self._graph_editor.canvas_left_click_cb(x,y,keys)

# ----------------------------------------------------------------------------
class graph_editor:
    def __init__(self, dscas3_app):
        # initialise vars
        self._dscas3_app = dscas3_app

        # get a main frame going
        self._graph_frame = wxFrame(parent=self._dscas3_app.get_main_window(),
                                    id=-1, title="DSCAS3 Graph Editor")
        EVT_CLOSE(self._graph_frame, self.close_graph_frame_cb)

        # get the panel going
        panel = wxPanel(parent=self._graph_frame, id=-1)

        # put a splitter window in it
        split_win = wxSplitterWindow(parent=panel, id=-1,
                                     size=(640,480))
        # tree thingy on the one size
        self._tree_ctrl = wxTreeCtrl(parent=split_win,
                                     style=wxTR_HAS_BUTTONS|wxTR_HIDE_ROOT)
        # the shape canvas on the right side
        self._shape_canvas = ge_shape_canvas(split_win, self)
        self._diagram = wxDiagram()
        self._shape_canvas.SetDiagram(self._diagram)
        self._diagram.SetCanvas(self._shape_canvas)
        
        # then split the window, giving the tree thingy 120 pixels
        split_win.SplitVertically(self._tree_ctrl, self._shape_canvas, 120)

        # add a top level sizer and give it the splitter window to play with
        top_sizer = wxBoxSizer(wxVERTICAL)
        top_sizer.Add(split_win, option=1, flag=wxEXPAND)
        panel.SetAutoLayout(true)
        panel.SetSizer(top_sizer)
        top_sizer.Fit(self._graph_frame)
        top_sizer.SetSizeHints(self._graph_frame)

        self.fill_module_tree()
        
        # now display the shebang
        self.show()

    def fill_module_tree(self):
        self._tree_ctrl.DeleteAllItems()
        tree_root = self._tree_ctrl.AddRoot('Modules')
        rdrn = self._tree_ctrl.AppendItem(tree_root, 'Readers')
        wrtn = self._tree_ctrl.AppendItem(tree_root, 'Writers')
        vwrn = self._tree_ctrl.AppendItem(tree_root, 'Viewers')
        fltn = self._tree_ctrl.AppendItem(tree_root, 'Filters')
        miscn = self._tree_ctrl.AppendItem(tree_root, 'Misc')

        self._dscas3_app.get_module_manager().scan_modules()
        for cur_mod in self._dscas3_app.get_module_manager().get_module_list():
            mtype = cur_mod[-3:]
            if mtype == 'rdr':
                self._tree_ctrl.AppendItem(rdrn, cur_mod)
            elif mtype == 'wrt':
                self._tree_ctrl.AppendItem(wrtn, cur_mod)
            elif mtype == 'vwr':
                self._tree_ctrl.AppendItem(vwrn, cur_mod)
            elif mtype == 'flt':
                self._tree_ctrl.AppendItem(fltn, cur_mod)
            else:
                self._tree_ctrl.AppendItem(misc, cur_mod)

        # only do stuff if !ItemHasChildren()

    def close_graph_frame_cb(self, event):
        self.hide()

    def show(self):
        self._graph_frame.Show(true)

    def hide(self):
        self._graph_frame.Show(false)

    def canvas_left_click_cb(self, x, y, keys):
        # first see what mode we are in
        # blah blah

        # we are in "create/edit" mode, so let's create some glyph
        # first get the currently selected tree node
        sel_item = self._tree_ctrl.GetSelection()
        # then the root node
        root_item = self._tree_ctrl.GetRootItem()
        if root_item != sel_item and \
           self._tree_ctrl.GetItemParent(sel_item) != root_item:
            # we have a valid module, we should try and instantiate
            mod_name = self._tree_ctrl.GetItemText(sel_item)
            mm = self._dscas3_app.get_module_manager()
            temp_module = mm.create_module(mod_name)
            # if the module_manager did its trick, we can make a glyph
            if temp_module:
                ge_glyph(self._shape_canvas, mod_name, temp_module, x, y)
                
        
    def create_glyph_cb(self, x, y):
        # we will first check with the module manager if this can be created
        # if so, we will actually create the glyph
        
        # instantiate the new shape
        new_shape = ge_glyph(x, y, self._shape_canvas, None)
