# graph_editor.py copyright 2002 by Charl P. Botha http://cpbotha.net/
# $Id: graph_editor.py,v 1.19 2002/04/24 16:09:58 cpbotha Exp $
# the graph-editor thingy where one gets to connect modules together

from wxPython.wx import *
from wxPython.ogl import *

# we have to call this to do some global OGL init
wxOGLInitialize()

class ge_shape_canvas(wxShapeCanvas):
    def __init__(self, parent, graph_editor):
        wxShapeCanvas.__init__(self, parent)
        self._graph_editor = graph_editor

    def OnLeftClick(self, x, y, keys):
        self._graph_editor.create_glyph_cb(x,y)

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
        self._tree_ctrl = wxTreeCtrl(parent=split_win)
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
        
        # now display the shebang
        self.show()

    def close_graph_frame_cb(self, event):
        self.hide()

    def show(self):
        self._graph_frame.Show(true)

    def hide(self):
        self._graph_frame.Show(false)

    def create_glyph_cb(self, x, y):
        # we will first check with the module manager if this can be created
        # if so, we will actually create the glyph
        
        # instantiate the new shape
        new_shape = wxRectangleShape(80, 40)
        # we want it to be able to move
        new_shape.SetDraggable(true, true)
        
        #new_shape.SetCanvas(self._shape_canvas)

        # set its coords
        new_shape.SetX(x)
        new_shape.SetY(y)

        # it needs to be added to the diagram (which contains the shapes)
        self._diagram.AddShape(new_shape)
        # and it needs to be visible
        new_shape.Show(true)

        # then, for some STUPID reason, it doesn't display if we don't
        # "move" it
        dc = wxClientDC(self._shape_canvas)
        self._shape_canvas.PrepareDC(dc)
        new_shape.Move(dc, new_shape.GetX(), new_shape.GetY())




