# graph_editor.py copyright 2002 by Charl P. Botha http://cpbotha.net/
# $Id: graphEditor.py,v 1.6 2003/05/07 23:34:13 cpbotha Exp $
# the graph-editor thingy where one gets to connect modules together

from wxPython.wx import *
from external.wxPyCanvas import wxpc
import genUtils
import string
import traceback


# ----------------------------------------------------------------------------
class graphEditor:
    def __init__(self, dscas3_app):
        # initialise vars
        self._dscas3_app = dscas3_app

        import resources.python.graphEditorFrame
        self._graphFrame = resources.python.graphEditorFrame.graphEditorFrame(
            self._dscas3_app.get_main_window(),
            -1, title='dummy', wxpcCanvas=wxpc.canvas)

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

        self._graphFrame.canvas.addObserver('buttonUp',
                                            self._canvasButtonUp)
        
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


    def _disconnect(self, glyph, inputIdx):
        """Disconnect inputIdx'th input of glyph.
        """

        try:
            # first disconnect the actual modules
            mm = self._dscas3_app.getModuleManager()
            mm.disconnectModules(glyph.moduleInstance, inputIdx)

            deadLine = glyph.inputLines[inputIdx]
            if deadLine:
                # remove the line from the destination module input lines
                glyph.inputLines[inputIdx] = None
                # and for the source module output lines
                outlines = deadLine.fromGlyph.outputLines[
                    deadLine.fromOutputIdx]
                del outlines[outlines.index(deadLine)]

                # and from the canvas
                self._graphFrame.canvas.removeObject(deadLine)
                deadLine.close()
            
        except Exception, e:
            genUtils.logError('Could not disconnect modules: %s' \
                              % (str(e)))
                
    def _canvasLeftClick(self, canvas, eventName, event, userData):
        if event.LeftDown():
            # we are in "create/edit" mode, so let's create some glyph
            # first get the currently selected tree node
            sel_item = self._graphFrame.treeCtrl.GetSelection()
            # then the root node
            root_item = self._graphFrame.treeCtrl.GetRootItem()
            if root_item != sel_item and \
                   self._graphFrame.treeCtrl.GetItemText(sel_item) and \
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

    def _canvasButtonUp(self, canvas, eventName, event, userData):
        if event.LeftUp():
            if canvas.getDraggedObject() and \
                   canvas.getDraggedObject().draggedPort and \
                   canvas.getDraggedObject().draggedPort != (-1,-1):

                if canvas.getDraggedObject().draggedPort[0] == 0:
                    # the user was dragging an input port and dropped it
                    # on the canvas, so she probably wants us to disconnect
                    inputIdx = canvas.getDraggedObject().draggedPort[1]
                    self._disconnect(canvas.getDraggedObject(),
                                     inputIdx)
            

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

            oldLine = draggedObject.inputLines[draggedPort[1]]
            fromGlyph = oldLine.fromGlyph
            fromOutputIdx = oldLine.fromOutputIdx
            toGlyph = oldLine.toGlyph
            toInputIdx = oldLine.toInputIdx

            # delete the old one
            self._disconnect(toGlyph, toInputIdx)

            # connect up the new one
            self._connect(fromGlyph, fromOutputIdx,
                          droppedObject, droppedInputPort)

            self._graphFrame.canvas.Refresh()
            

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

                cop = glyph.getCenterOfPort(glyph.draggedPort[0],
                                            glyph.draggedPort[1])
                self._drawPreviewLine(cop,
                                      canvas._previousRealCoords,
                                      (event.realX, event.realY))

            elif glyph.inputLines and glyph.inputLines[glyph.draggedPort[1]]:
                # the user is attempting to relocate or disconnect an input
                inputLine = glyph.inputLines[glyph.draggedPort[1]]
                cop = inputLine.fromGlyph.getCenterOfPort(
                    1, inputLine.fromOutputIdx)

                self._drawPreviewLine(cop,
                                      canvas._previousRealCoords,
                                      (event.realX, event.realY))
        
        if not canvas.getDraggedObject():
            # this means that this drag has JUST been cancelled
            if glyph.draggedPort == (-1, -1):
                # and we were busy dragging a glyph around, so we probably
                # want to reroute all lines!
                for lines in glyph.outputLines:
                    for line in lines:
                        line.updateEndPoints()

                for line in glyph.inputLines:
                    if line:
                        line.updateEndPoints()

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
                        inputIdx = canvas.getDraggedObject().draggedPort[1]
                        self._disconnect(canvas.getDraggedObject(),
                                         inputIdx)

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
            # first we disconnect all consumers
            consumerList = []
            for lines in glyph.outputLines:
                for line in lines:
                    consumerList.append((line.toGlyph, line.toInputIdx))

            for consumer in consumerList:
                self._disconnect(consumer[0], consumer[1])

            # then far simpler all suppliers
            for inputIdx in range(len(glyph.inputLines)):
                self._disconnect(glyph, inputIdx)
            
            
            # then get the module manager to NUKE the module itself
            mm = self._dscas3_app.getModuleManager()
            # this thing can also remove all links between supplying and
            # consuming objects (we hope) :)
            mm.deleteModule(module)

            canvas = glyph.getCanvas()
            # remove it from the canvas
            canvas.removeObject(glyph)
            # take care of possible lyings around
            glyph.close()
            
            # after all that work, we deserve a redraw
            canvas.Refresh()

        except Exception, e:
            genUtils.logError('Could not delete module: %s' % (str(e)))
        
                         
            
            

        
