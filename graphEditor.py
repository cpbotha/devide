# graph_editor.py copyright 2002 by Charl P. Botha http://cpbotha.net/
# $Id: graphEditor.py,v 1.22 2003/06/05 15:59:41 cpbotha Exp $
# the graph-editor thingy where one gets to connect modules together

from wxPython.wx import *
from internal.wxPyCanvas import wxpc
import genUtils
import string
import sys
import traceback

# ----------------------------------------------------------------------------
class geCanvasDropTarget(wxTextDropTarget):
    
    def __init__(self, graphEditor):
        wxTextDropTarget.__init__(self)        
        self._graphEditor = graphEditor

    def OnDropText(self, x, y, text):
        self._graphEditor.canvasDropText(x, y, text)

# ----------------------------------------------------------------------------
class graphEditor:
    def __init__(self, dscas3_app):
        # initialise vars
        self._dscas3_app = dscas3_app

        import resources.python.graphEditorFrame
        self._graphFrame = resources.python.graphEditorFrame.graphEditorFrame(
            self._dscas3_app.get_main_window(),
            -1, title='dummy', wxpcCanvas=wxpc.canvas)

        self._graphFrame.SetIcon(self._dscas3_app.getApplicationIcon())

        EVT_CLOSE(self._graphFrame, self.close_graph_frame_cb)

        EVT_BUTTON(self._graphFrame, self._graphFrame.rescanButtonId,
                   lambda e, s=self: s.fill_module_tree())

        EVT_MENU(self._graphFrame, self._graphFrame.fileExitId,
                 self._fileExitCallback)

        EVT_MENU(self._graphFrame, self._graphFrame.fileSaveId,
                 self._fileSaveCallback)

        # this will be filled in by self.fill_module_tree; it's here for
        # completeness
        self._availableModuleList = None
        self.fill_module_tree()

        EVT_TREE_BEGIN_DRAG(self._graphFrame, self._graphFrame.treeCtrlId,
                            self.treeCtrlBeginDragHandler)

        # setup the canvas...
        self._graphFrame.canvas.SetVirtualSize((1024, 1024))
        self._graphFrame.canvas.SetScrollRate(20,20)

        # the canvas is a drop target
        self._canvasDropTarget = geCanvasDropTarget(self)
        self._graphFrame.canvas.SetDropTarget(self._canvasDropTarget)
        
        # bind events on the canvas
        self._graphFrame.canvas.addObserver('buttonUp',
                                            self._canvasButtonUp)
        
        # now display the shebang
        self.show()

    def treeCtrlBeginDragHandler(self, event):
        itemText = self._graphFrame.treeCtrl.GetItemText(event.GetItem())
        dataObject = wxTextDataObject(itemText)
        
        dropSource = wxDropSource(self._graphFrame)
        dropSource.SetData(dataObject)
        # we don't need the result of the DoDragDrop call (phew)
        dropSource.DoDragDrop(TRUE)

    def canvasDropText(self, x, y, text):
        self.createModule(x, y, text)
        # check if the text is in our module list (then we should create it)

    def close(self):
        """This gracefull takes care of all graphEditor shutdown and is mostly
        called at application shutdown.
        """
        # FIXME: clean the canvas!
        pass

    def createModule(self, x, y, moduleName):
        # check that it's a valid module name
        if moduleName in self._availableModuleList:
            # we have a valid module, we should try and instantiate
            mm = self._dscas3_app.getModuleManager()
            temp_module = mm.createModule(moduleName)
            # if the module_manager did its trick, we can make a glyph
            if temp_module:
                rx, ry = self._graphFrame.canvas.eventToRealCoords(x, y)
                co = wxpc.coGlyph((rx, ry),
                                  len(temp_module.getInputDescriptions()),
                                  len(temp_module.getOutputDescriptions()),
                                  moduleName, temp_module)
                canvas = self._graphFrame.canvas
                canvas.addObject(co)


                co.addObserver('motion', self._glyphMotion)
                    
                co.addObserver('buttonDown',
                               self._glyphRightClick, temp_module)
                co.addObserver('buttonUp',
                               self._glyphButtonUp, temp_module)
                co.addObserver('drag',
                               self._glyphDrag, temp_module)

                # first have to draw the just-placed glyph so it has
                # time to update its (label-dependent) dimensions
                dc = wxClientDC(self._graphFrame.canvas)
                self._graphFrame.canvas.PrepareDC(dc)
                co.draw(dc)

                # THEN reroute all lines
                allLines = self._graphFrame.canvas.getObjectsOfClass(
                    wxpc.coLine)
                    
                for line in allLines:
                    self._routeLine(line)

                # redraw all
                canvas.Refresh()

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
        self._availableModuleList = mm.getAvailableModuleList()
        for cur_mod in self._availableModuleList:
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

        self._graphFrame.treeCtrl.Expand(tree_root)

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

        elif draggedObject.inputLines[draggedPort[1]]:
            # this means the user was dragging a connected input port and has
            # now dropped it on another input port... (we've already eliminated
            # the case of a drop on an occupied input port, and thus also
            # a drop on the dragged port)

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

            # REROUTE THIS LINE
            self._routeLine(l1)

        except Exception, e:
            genUtils.logError('Could not connect modules: %s' % (str(e)))
                                         

    def updatePortInfoStatusBar(self, currentGlyph, currentPort):
        
        """You can only call this during motion IN a port of a glyph.
        """
        
        msg = ''
        canvas = currentGlyph.getCanvas()

        draggedObject = canvas.getDraggedObject()
        if draggedObject and draggedObject.draggedPort and \
               draggedObject.draggedPort != (-1, -1):

            if draggedObject.draggedPort[0] == 0:
                pstr = draggedObject.moduleInstance.getInputDescriptions()[
                    draggedObject.draggedPort[1]]
            else:
                pstr = draggedObject.moduleInstance.getOutputDescriptions()[
                    draggedObject.draggedPort[1]]

            msg = '|%s|-[%s] ===>> ' % (draggedObject.getLabel(), pstr)

        if currentPort[0] == 0:
            pstr = currentGlyph.moduleInstance.getInputDescriptions()[
                currentPort[1]]
        else:
            pstr = currentGlyph.moduleInstance.getOutputDescriptions()[
                currentPort[1]]
             
        msg += '|%s|-[%s]' % (currentGlyph.getLabel(), pstr)

        self._graphFrame.GetStatusBar().SetStatusText(msg)            
                                   
    def _fileExitCallback(self, event):
        self._dscas3_app.quit()

    def _fileSaveCallback(self, event):
        # make a list of all module instances
        allGlyphs = self._graphFrame.canvas.getObjectsOfClass(wxpc.coGlyph)
        moduleInstances = [glyph.moduleInstance for glyph in allGlyphs]
        mm = self._dscas3_app.getModuleManager()
        stream = mm.serialiseModuleInstances(moduleInstances)
        mm.deserialiseModuleInstances(stream)

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


                # reroute all lines
                allLines = self._graphFrame.canvas.getObjectsOfClass(
                    wxpc.coLine)

                for line in allLines:
                    self._routeLine(line)

            # switch off the draggedPort
            glyph.draggedPort = None
            # redraw everything
            canvas.Refresh()

    def _glyphMotion(self, glyph, eventName, event, module):
        port = glyph.findPortContainingMouse(event.realX, event.realY)
        if port:
            self.updatePortInfoStatusBar(glyph, port)

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

    def _cohenSutherLandClip(self,
                             x0, y0, x1, y1,
                             xmin, ymin, xmax, ymax):

        def outCode(x, y, xmin, ymin, xmax, ymax):


            a,b,c,d = (0,0,0,0)

            if y > ymax:
                a = 1
            if y < ymin:
                b = 1
                
            if x > xmax:
                c = 1
            elif x < xmin:
                d = 1

            return (a << 3) | (b << 2) | (c << 1) | d


        oc0 = outCode(x0, y0, xmin, ymin, xmax, ymax)
        oc1 = outCode(x1, y1, xmin, ymin, xmax, ymax)

        clipped = False
        accepted = False
        
        while not clipped:

            if oc0 == 0 and oc1 == 0:
                clipped = True
                accepted = True
                
            elif oc0 & oc1 != 0:
                # trivial reject, the line is nowhere near
                clipped = True
                
            else:
                m = float(y1 - y0 + 0.00000001) / float(x1 - x0 + 0.00000001)
                mi = 1 / m
                # this means there COULD be a clip

                # pick "outside" point
                oc = [oc1, oc0][bool(oc0)]

                if oc & 8: # y is above (numerically)
                    x = x0 + mi * (ymax - y0)
                    y = ymax
                elif oc & 4: # y is below (numerically)
                    x = x0 + mi * (ymin - y0)
                    y = ymin
                elif oc & 2: # x is right
                    x = xmax
                    y = y0 + m * (xmax - x0)
                else:
                    x = xmin
                    y = y0 + m * (xmin - x0)

                if oc == oc0:
                    # we're clipping off the line start
                    x0 = x
                    y0 = y
                    oc0 = outCode(x0, y0, xmin, ymin, xmax, ymax)
                else:
                    # we're clipping off the line end
                    x1 = x
                    y1 = y
                    oc1 = outCode(x1, y1, xmin, ymin, xmax, ymax)

        clipPoints = []
        if accepted:
            if x0 == xmin or x0 == xmax or y0 == ymin or y0 == ymax:
                clipPoints.append((x0, y0))
            if x1 == xmin or x1 == xmax or y1 == ymin or y1 == ymax:
                clipPoints.append((x1, y1))

        return clipPoints
                

    def _routeLine(self, line):
        
        # we have to get a list of all coGlyphs
        allGlyphs = self._graphFrame.canvas.getObjectsOfClass(wxpc.coGlyph)

        # make sure the line is back to 4 points
        line.updateEndPoints()

        #
        overshoot = 5

        successfulInsert = True
        while successfulInsert:
            
            (x0, y0), (x1, y1) = line.getThirdLastSecondLast()

            clips = {}
            for glyph in allGlyphs:
                (xmin, ymin), (xmax, ymax) = glyph.getTopLeftBottomRight()

                clipPoints = self._cohenSutherLandClip(x0, y0, x1, y1,
                                                       xmin, ymin, xmax, ymax)

                if clipPoints:
                    clips[glyph] = clipPoints

            # now look for the clip point closest to the start of the current
            # line segment!
            currentSd = sys.maxint
            nearestGlyph = None
            nearestClipPoint = None
            for clip in clips.items():
                for clipPoint in clip[1]:
                    xdif = clipPoint[0] - x0
                    ydif = clipPoint[1] - y0
                    sd = xdif * xdif + ydif * ydif
                    if sd < currentSd:
                        currentSd = sd
                        nearestGlyph = clip[0]
                        nearestClipPoint = clipPoint

            successfulInsert = False
            # we have the nearest clip point
            if nearestGlyph:
                (xmin, ymin), (xmax, ymax) = \
                       nearestGlyph.getTopLeftBottomRight()

                # does it clip the horizontal bar
                if nearestClipPoint[1] == ymin or nearestClipPoint[1] == ymax:
                    midPointX = xmin + (xmax - xmin) / 2.0
                    if x1 < midPointX:
                        newX = xmin - overshoot
                    else:
                        newX = xmax + overshoot
                    
                    newY = nearestClipPoint[1]
                    if newY == ymin:
                        newY -= overshoot

                    else:
                        newY += overshoot
                        
                    # if there are clips on the new segment, add an extra
                    # node to avoid those clips!
                    for glyph in allGlyphs:
                        (xmin2, ymin2), (xmax2, ymax2) = \
                                glyph.getTopLeftBottomRight()
                        cp2 = self._cohenSutherLandClip(x0,y0,newX,newY,
                                                        xmin2, ymin2,
                                                        xmax2, ymax2)
                        if cp2:
                            break
                     
                    if cp2:
                        line.insertRoutingPoint(nearestClipPoint[0], newY)
                        
                    successfulInsert = line.insertRoutingPoint(newX, newY)
                    
                # or does it clip the vertical bar
                elif nearestClipPoint[0] == xmin or \
                         nearestClipPoint[0] == xmax:
                    midPointY = ymin + (ymax - ymin) / 2.0
                    if y1 < midPointY:
                        newY = ymin - overshoot
                    else:
                        newY = ymax + overshoot

                    newX = nearestClipPoint[0]
                    if newX == xmin:
                        newX -= overshoot
                    else:
                        newX += overshoot

                    # if there are clips on the new segment, add an extra
                    # node to avoid those clips!
                    for glyph in allGlyphs:
                        (xmin2, ymin2), (xmax2, ymax2) = \
                                glyph.getTopLeftBottomRight()
                        cp2 = self._cohenSutherLandClip(x0,y0,newX,newY,
                                                        xmin2, ymin2,
                                                        xmax2, ymax2)
                        if cp2:
                            break
                     
                    if cp2:
                        line.insertRoutingPoint(newX, nearestClipPoint[1])
                        
                    successfulInsert = line.insertRoutingPoint(newX, newY)

                else:
                    print "HEEEEEEEEEEEEEEEEEEEELP!!  This shouldn't happen."
                    raise Exception



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
        
                         
            
            

        
