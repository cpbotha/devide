
# graph_editor.py copyright 2002 by Charl P. Botha http://cpbotha.net/
# $Id: graphEditor.py,v 1.4 2003/05/07 21:24:45 cpbotha Exp $
# the graph-editor thingy where one gets to connect modules together

from wxPython.wx import *
#from wxPython.ogl import *
from external.wxPyCanvas import wxpc
import genUtils
import string
import traceback

# wxGTK 2.3.2.1 bugs with mouse capture (BADLY), so we disable this
try:
    WX_USE_X_CAPTURE
except NameError:
    if wxPlatform == '__WXMSW__':
        WX_USE_X_CAPTURE = 1
    else:
        WX_USE_X_CAPTURE = 0


# ----------------------------------------------------------------------------
class graphEditor:
    def __init__(self, dscas3_app):
        # initialise vars
        self._dscas3_app = dscas3_app

        import resources.python.graphEditorFrame
        self._graphFrame = resources.python.graphEditorFrame.graphEditorFrame(
            self._dscas3_app.get_main_window(),
            -1, title='dummy', wxpcCanvas=wxpc.canvas)
        #self._graphFrame.canvas.setGraphEditor(self)

        EVT_CLOSE(self._graphFrame, self.close_graph_frame_cb)        

        EVT_BUTTON(self._graphFrame, self._graphFrame.rescanButtonId,
                   lambda e, s=self: s.fill_module_tree())

        self.fill_module_tree()

        # setup the canvas...
        self._graphFrame.canvas.SetVirtualSize((1024, 1024))
        self._graphFrame.canvas.SetScrollRate(20,20)
        # bind events on the canvas
        self._graphFrame.canvas.addObserver('buttonDown',
                                            self._canvasLeftClick)

        
        # now display the shebang
        self.show()

    def fill_module_tree(self):
        self._graphFrame.treeCtrl.DeleteAllItems()

        tree_root = self._graphFrame.treeCtrl.AddRoot('Modules')
        rdrn = self._graphFrame.treeCtrl.AppendItem(tree_root, 'Readers')
        wrtn = self._graphFrame.treeCtrl.AppendItem(tree_root, 'Writers')
        vwrn = self._graphFrame.treeCtrl.AppendItem(tree_root, 'Viewers')
        fltn = self._graphFrame.treeCtrl.AppendItem(tree_root, 'Filters')
        miscn = self._graphFrame.treeCtrl.AppendItem(tree_root, 'Misc')

        mm = self._dscas3_app.getModuleManager()
        mm.scanModules()
        for cur_mod in mm.getAvailableModuleList():
            mtype = cur_mod[-3:].lower()
            if mtype == 'rdr':
                self._graphFrame.treeCtrl.AppendItem(rdrn, cur_mod)
            elif mtype == 'wrt':
                self._graphFrame.treeCtrl.AppendItem(wrtn, cur_mod)
            elif mtype == 'vwr':
                self._graphFrame.treeCtrl.AppendItem(vwrn, cur_mod)
            elif mtype == 'flt':
                self._graphFrame.treeCtrl.AppendItem(fltn, cur_mod)
            else:
                self._graphFrame.treeCtrl.AppendItem(miscn, cur_mod)

        # only do stuff if !ItemHasChildren()

    def close_graph_frame_cb(self, event):
        self.hide()

    def show(self):
        self._graphFrame.Show(True)

    def hide(self):
        self._graphFrame.Show(False)

    def _drawPreviewLine(self, beginp, endp0, endp1):

        # make a DC to draw on
        dc = wxClientDC(self._graphFrame.canvas)
        self._graphFrame.canvas.PrepareDC(dc)

        dc.BeginDrawing()
        
        # dotted line
        dc.SetBrush(wxBrush('WHITE', wx.wxTRANSPARENT))
        dc.SetPen(wxPen('BLACK', 1, wxDOT))
        dc.SetLogicalFunction(wxINVERT) # NOT dst

        # nuke the previous line, draw the new one
        dc.DrawLine(beginp[0], beginp[1], endp0[0], endp0[1])
        dc.DrawLine(beginp[0], beginp[1], endp1[0], endp1[1])
        
        dc.EndDrawing()

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
                mm = self._dscas3_app.getModuleManager()
                mm.connectModules(from_glyph.get_module_instance(), out_idx,
                                   to_glyph.get_module_instance(), in_idx)
                # create a connecting line
                conn = wxLineShape()
                conn.MakeLineControlPoints(2)
                conn.AddArrow(ARROW_ARROW, ARROW_POSITION_END)
                self._graphFrame.canvas.AddShape(conn)
                from_io_shape.AddLine(conn, to_io_shape)
                conn.Show(True)
                # fix the fuxors
                from_io_shape.dont_move()
                to_io_shape.dont_move()
            except Exception, e:
                genUtils.logError('Could not connect modules: %s' % (str(e)))

    def _disconnect(self, glyph, inputIdx):
        """Disconnect inputIdx'th input of glyph.
        """

        try:
            mm = self._dscas3_app.getModuleManager()
            mm.disconnectModules(glyph.moduleInstance, inputIdx)
        except Exception, e:
            genUtils.logError('Could not disconnect modules: %s' \
                              % (str(e)))
                
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
                mm = self._dscas3_app.getModuleManager()
                # disconnect that shape
                mm.disconnectModules(to_glyph.get_module_instance(), in_idx)
                
                # now perform the surgery on the canvas
                # disconnect the line
                the_line.Unlink()
                # erase it
                dc =  wxClientDC(self._graphFrame.canvas)
                self._graphFrame.canvas.PrepareDC(dc)
                the_line.Erase(dc)
                # remove it from the canvas (actually the diagram)
                self._graphFrame.canvas.RemoveShape(the_line)
            except Exception, e:
                genUtils.logError('Could not disconnect modules: %s' \
                                    % (str(e)))

    def disconnect_glyphs_by_oshape(self, oshape):
        # iterate through all the lines emanating from oshape
        for line in oshape.GetLines():
            self.disconnect_glyphs_by_ishape(line.GetTo())

    def redraw_canvas(self):
        dc = wxClientDC(self._graphFrame.canvas)
        self._graphFrame.canvas.PrepareDC(dc)
        self._graphFrame.canvas.Redraw(dc)

    def _canvasLeftClick(self, canvas, eventName, event, userData):
        # first see what mode we are in
        # blah blah

        # we are in "create/edit" mode, so let's create some glyph
        # first get the currently selected tree node
        sel_item = self._graphFrame.treeCtrl.GetSelection()
        # then the root node
        root_item = self._graphFrame.treeCtrl.GetRootItem()
        if root_item != sel_item and \
           self._graphFrame.treeCtrl.GetItemParent(sel_item) != root_item:
            # we have a valid module, we should try and instantiate
            mod_name = self._graphFrame.treeCtrl.GetItemText(sel_item)
            mm = self._dscas3_app.getModuleManager()
            temp_module = mm.createModule(mod_name)
            # if the module_manager did its trick, we can make a glyph
            if temp_module:
                co = wxpc.coGlyph((event.realX, event.realY),
                                  len(temp_module.getInputDescriptions()),
                                  len(temp_module.getOutputDescriptions()),
                                  mod_name, temp_module)
                canvas.addObject(co)

                co.addObserver('buttonDown',
                               self._glyphRightClick, temp_module)
                co.addObserver('buttonUp',
                               self._glyphButtonUp, temp_module)
                co.addObserver('drag',
                               self._glyphDrag, temp_module)
                
                canvas.Refresh()
                #ge_glyph(self._graphFrame.canvas, mod_name, temp_module, x, y)

    def _checkAndConnect(self, draggedObject, draggedPort,
                         droppedObject, droppedInputPort):

        if droppedObject.inputLines[droppedInputPort]:
            # the user dropped us on a connected input, we can just bail
            return
            
        if draggedPort[0] == 1:
            # this is a good old "I'm connecting an output to an input"
            self._connect(draggedObject, draggedPort[1],
                          droppedObject, droppedInputPort)
            
            self._graphFrame.canvas.Refresh()

        else:
            # this means the user was dragging an input port and has now
            # dropped it on another input port... (we've already eliminated
            # the case of a drop on an occupied input port, and thus also
            # a drop on the dragged port)
            # what's left: the user drops us on an unoccupied port, this means
            # we have to delete the old connection and create a new one

            FIXME CONTINUE HERE
            

    def _connect(self, fromObject, fromOutputIdx,
                 toObject, toInputIdx):

        try:
            # connect the actual modules
            mm = self._dscas3_app.getModuleManager()
            mm.connectModules(fromObject.moduleInstance, fromOutputIdx,
                              toObject.moduleInstance, toInputIdx)

            # if that worked, we can make a linypoo
            l1 = wxpc.coLine(fromObject, fromOutputIdx,
                             toObject, toInputIdx)
            self._graphFrame.canvas.addObject(l1)

            # also record the line in the glyphs
            toObject.inputLines[toInputIdx] = l1
            fromObject.outputLines[fromOutputIdx].append(l1)

        except Exception, e:
            genUtils.logError('Could not connect modules: %s' % (str(e)))
                                         

    def updatePortInfoStatusbar(self, from_io_shape, to_io_shape=None):

        msgs = ['N/A', 'N/A']
        i = 0
        for i in range(2):
            io_shape = (from_io_shape, to_io_shape)[i]
            if not io_shape is None:
                glyph = io_shape.get_parent_glyph()
                if io_shape.get_inout():
                    idx = glyph.get_main_shape().find_input_idx(io_shape)
                    msgs[i] = glyph.get_module_instance().\
                              getInputDescriptions()[idx]
                else:
                    idx = glyph.get_main_shape().find_output_idx(io_shape)
                    msgs[i] = glyph.get_module_instance().\
                              getOutputDescriptions()[idx]


        if to_io_shape is None:
            stxt = msgs[0]
        else:
            stxt = 'From %s to %s' % tuple(msgs)
            
        self._graphFrame.GetStatusBar().SetStatusText(stxt)
        
    def inout_leftclick_cb(self, parent_glyph, io_shape,
                           x, y, keys, attachment):
        # single click, just display the shape type
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
                self.updatePortInfoStatusbar(io_shape)

        # after doing our setup, we capture the mouse so things don't
        # get confused when the user waves his wand outside the canvas
        if WX_USE_X_CAPTURE:
            self._graphFrame.canvas.CaptureMouse()        

    def inout_enddragleft_cb(self, parent_glyph, io_shape,
                             x, y, keys, attachment):
        # give the mouse back ASAP, else people get angry, he he
        if WX_USE_X_CAPTURE:
            self._graphFrame.canvas.ReleaseMouse()

        # find shape that we're close to (we will need this in both cases)
        f_ret = self._graphFrame.canvas.FindShape(x, y, None)

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
        f_ret = self._graphFrame.canvas.FindShape(x, y, None)

        if f_ret and hasattr(f_ret[0], 'get_inout'):
            self.updatePortInfoStatusbar(io_shape, f_ret[0])

    def _glyphDrag(self, glyph, eventName, event, module):

        canvas = glyph.getCanvas()        

        # this clause will execute once at the beginning of a drag...
        if not glyph.draggedPort:
            # we're dragging, but we don't know if we're dragging a port yet
            port = glyph.findPortContainingMouse(event.realX, event.realY)
            if port:
                # 
                glyph.draggedPort = port
            else:
                # this indicates that the glyph is being dragged, but that
                # we don't have to check for a port during this drag
                glyph.draggedPort = (-1, -1)

        # when we get here, glyph.draggedPort CAN't BE None
        if glyph.draggedPort == (-1, -1):
            # this means that there's no port involved, so the glyph itself
            # gets dragged
            canvas.dragObject(glyph, canvas.getMouseDelta())
        else:
            if glyph.draggedPort[0] == 1:
                # the user is attempting a new connection starting with
                # an output port 

                cop = glyph.getCenterOfPort(glyph.draggedPort)
                self._drawPreviewLine(cop,
                                      canvas._previousRealCoords,
                                      (event.realX, event.realY))

            elif glyph.inputLines and glyph.inputLines[glyph.draggedPort[1]]:
                # the user is attempting to relocate or disconnect an input
                gap = glyph.inputLines[glyph.draggedPort[1]].fromGlyphAndPort
                cop = gap[0].GetCenterOfPort(gap[1])
        
        if not canvas.getDraggedObject():
            # this means that this drag has JUST been cancelled
            # switch off the draggedPort
            glyph.draggedPort = None
            # redraw everything
            canvas.Refresh()

    def _glyphRightClick(self, glyph, eventName, event, module):
        if event.RightDown():

            pmenu = wxMenu(glyph.getLabel())

            vc_id = wxNewId()
            pmenu.AppendItem(wxMenuItem(pmenu, vc_id, "View-Configure"))
            EVT_MENU(self._graphFrame.canvas, vc_id,
                     lambda e: self._viewConfModule(module))

            del_id = wxNewId()
            pmenu.AppendItem(wxMenuItem(pmenu, del_id, 'Delete'))
            EVT_MENU(self._graphFrame.canvas, del_id,
                     lambda e: self._deleteModule(module, glyph))

            mcs_id = wxNewId()
            pmenu.AppendItem(wxMenuItem(pmenu, mcs_id,
                                        'Make current'))
            EVT_MENU(self._graphFrame.canvas, mcs_id,
                     lambda e, s=self, glyph=glyph:
                     s._dscas3_app.getModuleManager().set_current_module(
                glyph.get_module_instance()))

            # popup that menu!
            self._graphFrame.canvas.PopupMenu(pmenu, wxPoint(event.GetX(),
                                                             event.GetY()))

    def _glyphButtonUp(self, glyph, eventName, event, module):
        if event.LeftUp():
            canvas = glyph.getCanvas()

            # when we receive the ButtonUp that ends the drag event, 
            # canvas.getDraggedObject is still set!
            
            if canvas.getDraggedObject() and \
                   canvas.getDraggedObject().draggedPort and \
                   canvas.getDraggedObject().draggedPort != (-1,-1):
                # this means the user was dragging a port... so we're
                # interested
                pcm = glyph.findPortContainingMouse(event.realX, event.realY)
                if not pcm:
                    # the user dropped us inside of the glyph, NOT above a port
                    # if the user was dragging an input port, we have to
                    # manually disconnect
                    if canvas.getDraggedObject().draggedPort[0] == 0:
                        self._disconnect(canvas.getDraggedObject(),
                                         canvas.getDraggedObject().draggedPort)

                    else:
                        # the user was dragging a port and dropped us
                        # inside a glyph... we do nothing
                        pass

                else:
                    # this means the drag is ended above a port!
                    if pcm[0] == 0:
                        # ended above an INPUT port
                        self._checkAndConnect(
                            canvas.getDraggedObject(),
                            canvas.getDraggedObject().draggedPort,
                            glyph, pcm[1])

                    else:
                        # ended above an output port... we can't do anything
                        # (I think)
                        pass

    def _viewConfModule(self, module):
        mm =self._dscas3_app.getModuleManager()
        mm.viewModule(module)

    def _deleteModule(self, module, glyph):
        try:
            # it is important that we first delete all dependants and
            # then suppliers of the glyph

            
            
#             # delete all outgoing connections
#             for oshape in glyph.get_main_shape().get_output_shapes():
#                 self.disconnect_glyphs_by_oshape(oshape)
#             # delete all incoming connections
#             for ishape in glyph.get_main_shape().get_input_shapes():
#                 self.disconnect_glyphs_by_ishape(ishape)
#             # we're going to destroy the glyph, make sure we keep tabs
#             module_instance = glyph.get_module_instance()
#             glyph.close()

            
            mm = self._dscas3_app.getModuleManager()
            # this will also perform ALL necessary disconnections
            mm.deleteModule(module)

            canvas = glyph.getCanvas()
            canvas.removeObject(glyph)
            # take care of possible lyings around
            glyph.close()
            
            canvas.Refresh()

        except Exception, e:
            genUtils.logError('Could not delete module: %s' % (str(e)))
        
                         
            
            

        
