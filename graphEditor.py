# graph_editor.py copyright 2002 by Charl P. Botha http://cpbotha.net/
# $Id: graphEditor.py,v 1.59 2004/02/20 23:19:55 cpbotha Exp $
# the graph-editor thingy where one gets to connect modules together

import cPickle
from wxPython.wx import *
from internal.wxPyCanvas import wxpc
import genUtils
import moduleUtils # for getModuleIcon
import os
import re
import string
import sys

# ----------------------------------------------------------------------------
class geCanvasDropTarget(wxTextDropTarget):
    
    def __init__(self, graphEditor):
        wxTextDropTarget.__init__(self)        
        self._graphEditor = graphEditor

    def OnDropText(self, x, y, text):
        self._graphEditor.canvasDropText(x, y, text)

# ----------------------------------------------------------------------------
class glyphSelection:
    def __init__(self, canvas):
        self._canvas = canvas
        self._selectedGlyphs = []

    def close(self):
        # take care of all references
        self.removeAllGlyphs()

    def addGlyph(self, glyph):
        """Add a glyph to the selection.
        """

        if glyph in self._selectedGlyphs:
            # it's already selected, ignore
            return

        # add it to our structures
        self._selectedGlyphs.append(glyph)
        # tell it that it's the chosen one (ha ha)
        glyph.selected = True
        # redraw it
        self._canvas.drawObject(glyph)

    def getSelectedGlyphs(self):
        """Returns a list with the selected glyphs.  Do not modify externally.
        """
        return self._selectedGlyphs

    def removeGlyph(self, glyph):
        """Remove a glyph from the selection.
        """
        if not glyph in self._selectedGlyphs:
            # it's not in the selection, do nothing.
            return

        del self._selectedGlyphs[self._selectedGlyphs.index(glyph)]
        glyph.selected = False
        self._canvas.drawObject(glyph)

    def removeAllGlyphs(self):
        """Remove all glyphs from selection.
        """
        for glyph in self._selectedGlyphs:
            glyph.selected = False
            self._canvas.drawObject(glyph)

        self._selectedGlyphs = []
        
    def selectGlyph(self, glyph):
        """Set the selection on one single glyph.  All others must be
        unselected.
        """

        self.removeAllGlyphs()
        self.addGlyph(glyph)

# ----------------------------------------------------------------------------

class graphEditor:
    def __init__(self, devide_app):
        # initialise vars
        self._devide_app = devide_app

        import resources.python.graphEditorFrame
        self._graphFrame = resources.python.graphEditorFrame.graphEditorFrame(
            self._devide_app.get_main_window(),
            -1, title='dummy', wxpcCanvas=wxpc.canvas)

        self._graphFrame.SetIcon(self._devide_app.getApplicationIcon())

        self._appendEditCommands(self._graphFrame.editMenu, self._graphFrame,
                                 (0,0), False)

        EVT_CLOSE(self._graphFrame, self.close_graph_frame_cb)




        EVT_BUTTON(self._graphFrame, self._graphFrame.rescanButtonId,
                   lambda e, s=self: s.fillModuleLists())
        

        EVT_MENU(self._graphFrame, self._graphFrame.fileNewId,
                 self._fileNewCallback)

        EVT_MENU(self._graphFrame, self._graphFrame.fileExitId,
                 self._fileExitCallback)

        EVT_MENU(self._graphFrame, self._graphFrame.fileOpenId,
                 self._fileOpenCallback)

        EVT_MENU(self._graphFrame, self._graphFrame.fileOpenSegmentId,
                 self._handlerFileOpenSegment)

        EVT_MENU(self._graphFrame, self._graphFrame.fileSaveId,
                 self._fileSaveCallback)

        EVT_MENU(self._graphFrame, self._graphFrame.fileSaveSelectedId,
                 self._handlerFileSaveSelected)

        EVT_MENU(self._graphFrame, self._graphFrame.helpContextHelpId,
                 self._handlerHelpContextHelp)


        # finish with moduleLists config
        self._graphFrame.moduleCatsListCtrl.InsertColumn(0,
                                                         'Categories')
        self._graphFrame.modulesListCtrl.InsertColumn(0,
                                                      'Modules')

        # event handlers
        EVT_LIST_ITEM_SELECTED(self._graphFrame,
                               self._graphFrame.moduleCatsListCtrlId,
                               self._handlerModuleCatsListCtrlSelected)
        EVT_LIST_ITEM_SELECTED(self._graphFrame,
                               self._graphFrame.modulesListCtrlId,
                               self._handlerModulesListCtrlSelected)

        # this will be filled in by self.fill_module_tree; it's here for
        # completeness
        self._availableModuleList = None
        #self.fill_module_tree()
        self.fillModuleLists()

        EVT_LIST_BEGIN_DRAG(self._graphFrame,
                            self._graphFrame.modulesListCtrlId,
                            self.modulesListCtrlBeginDragHandler)

        # and also setup the module quick search
        self._quickSearchString = ''
        self._currentModuleListShort = []        
        EVT_CHAR(self._graphFrame.canvas, self._handlerCanvasChar)

        # setup the canvas...
        self._graphFrame.canvas.SetVirtualSize((2048, 2048))
        self._graphFrame.canvas.SetScrollRate(20,20)

        # the canvas is a drop target
        self._canvasDropTarget = geCanvasDropTarget(self)
        self._graphFrame.canvas.SetDropTarget(self._canvasDropTarget)
        
        # bind events on the canvas
        self._graphFrame.canvas.addObserver('buttonDown',
                                            self._canvasButtonDown)
        self._graphFrame.canvas.addObserver('buttonUp',
                                            self._canvasButtonUp)
        self._graphFrame.canvas.addObserver('drag',
                                            self._canvasDrag)

        # initialise selection
        self._glyphSelection = glyphSelection(self._graphFrame.canvas)

        self._rubberBandCoords = None

        # initialise cut/copy/paste buffer
        self._copyBuffer = None

        # we'll use this list to keep track of module help windows
        self._moduleHelpFrames = {}
        
        # now display the shebang
        self.show()

    def modulesListCtrlBeginDragHandler(self, event):
        mlc = self._graphFrame.modulesListCtrl        
        moduleName = self._currentModuleList[mlc.GetItemData(event.GetIndex())]

        if type(moduleName) != str:
            return
        
        dataObject = wxTextDataObject(moduleName)
        dropSource = wxDropSource(self._graphFrame)
        dropSource.SetData(dataObject)
        # we don't need the result of the DoDragDrop call (phew)
        dropSource.DoDragDrop(TRUE)

    def canvasDropText(self, x, y, itemText):
        """itemText is a complete module or segment spec, e.g.
        module:modules.Readers.dicomRDR or
        segment:/home/cpbotha/work/code/devide/networkSegments/blaat.dvn
        """

        modp = 'module:'
        segp = 'segment:'
        
        if itemText.startswith(modp):
            self.createModuleAndGlyph(x, y, itemText[len(modp):])
        elif itemText.startswith(segp):
            # we have to convert the event coords to real coords
            rx, ry = self._graphFrame.canvas.eventToRealCoords(x, y)
            self._loadAndRealiseNetwork(itemText[len(segp):], (rx,ry),
                                        reposition=True)


    def close(self):
        """This gracefull takes care of all graphEditor shutdown and is mostly
        called at application shutdown.
        """

        # clear away all moduleHelpFrames
        for helpFrame in self._moduleHelpFrames.values():
            helpFrame.Destroy()
        self._moduleHelpFrames.clear()
        
        # make sure no refs are stuck in the selection
        self._glyphSelection.close()
        # this should take care of just about everything!
        self.clearAllGlyphsFromCanvas()

    def _appendEditCommands(self, pmenu, eventWidget, origin, disable=True):
        """Append copy/cut/paste/delete commands and the default handlers
        to a given menu.  Origin is used by the paste command, and should be
        the REAL canvas coordinates, i.e. with scroll position taken into
        account.
        """
        
        copyId = wxNewId()
        ni = wxMenuItem(pmenu, copyId, '&Copy Selected\tCtrl-C',
                        'Copy the selected glyphs into the copy buffer.')
        pmenu.AppendItem(ni)
        EVT_MENU(eventWidget, copyId,
                 self._handlerCopySelected)
        if disable:
            if not self._glyphSelection.getSelectedGlyphs():
                ni.Enable(False)
            
        cutId = wxNewId()
        ni = wxMenuItem(pmenu, cutId, 'Cu&t Selected\tCtrl-X',
                        'Cut the selected glyphs into the copy buffer.')
        pmenu.AppendItem(ni)
        EVT_MENU(eventWidget, cutId,
                 self._handlerCutSelected)
        if disable:
            if not self._glyphSelection.getSelectedGlyphs():
                ni.Enable(False)
            
        pasteId = wxNewId()
        ni = wxMenuItem(
            pmenu, pasteId, '&Paste\tCtrl-V',
            'Paste the contents of the copy buffer onto the canvas.')
        pmenu.AppendItem(ni)
        EVT_MENU(eventWidget, pasteId,
                 lambda e: self._handlerPaste(e, origin))
        if disable:
            if not self._copyBuffer:
                ni.Enable(False)
        
        deleteId = wxNewId()
        ni = wxMenuItem(pmenu, deleteId, '&Delete Selected\tCtrl-D',
                        'Delete all selected glyphs.')
        pmenu.AppendItem(ni)
        EVT_MENU(eventWidget, deleteId,
                 lambda e: self._deleteSelectedGlyphs())
        if disable:
            if not self._glyphSelection.getSelectedGlyphs():
                ni.Enable(False)
        

    def createGlyph(self, rx, ry, moduleName, moduleInstance):
        """Create only a glyph on the canvas given an already created
        moduleInstance.
        """
        

        co = wxpc.coGlyph((rx, ry),
                          len(moduleInstance.getInputDescriptions()),
                          len(moduleInstance.getOutputDescriptions()),
                          moduleName, moduleInstance)
        
        canvas = self._graphFrame.canvas
        canvas.addObject(co)


        co.addObserver('motion', self._glyphMotion)
                    
        co.addObserver('buttonDown',
                       self._glyphButtonDown, moduleInstance)
        co.addObserver('buttonUp',
                       self._glyphButtonUp, moduleInstance)
        co.addObserver('drag',
                       self._glyphDrag, moduleInstance)

        # first have to draw the just-placed glyph so it has
        # time to update its (label-dependent) dimensions
        dc = self._graphFrame.canvas.getDC()
        co.draw(dc)

        # the network loading needs this
        return co
    
    def createModuleAndGlyph(self, x, y, moduleName):
        """Create a DeVIDE and a corresponding glyph at window event
        position x,y.  x, y will be converted to real (canvavs-absolute)
        coordinates internally.
        """
        
        # check that it's a valid module name
        if moduleName in self._availableModuleList:
            # we have a valid module, we should try and instantiate
            mm = self._devide_app.getModuleManager()
            temp_module = mm.createModule(moduleName)
            # if the module_manager did its trick, we can make a glyph
            if temp_module:
                # create and draw the actual glyph
                rx, ry = self._graphFrame.canvas.eventToRealCoords(x, y)
                self.createGlyph(rx,ry,moduleName.split('.')[-1],temp_module)

                # route all lines
                self._routeAllLines()

    def _executeModule(self, moduleInstance):
        """Ask the moduleManager to execute the devide module represented by
        the parameter moduleInstance.
        """
        
        mm = self._devide_app.getModuleManager()
        mm.executeModule(moduleInstance)
	
    def _helpModule(self, moduleInstance):
	"""
	"""

        if not moduleInstance.__doc__:
            md = wxMessageDialog(
                self._graphFrame,
                "This module has no help documentation yet.",
                "Information",
                wxOK | wxICON_INFORMATION)
            md.ShowModal()
            return

        fullModuleName = moduleInstance.__class__.__module__
        try:
            htmlWindowFrame = self._moduleHelpFrames[fullModuleName]
        except KeyError:
            import resources.python.htmlWindowFrame
            htmlWindowFrame = resources.python.htmlWindowFrame.htmlWindowFrame(
                self._devide_app._mainFrame, id=-1,
                title='dummy')

            # store it in the dict for later use
            self._moduleHelpFrames[fullModuleName] = htmlWindowFrame

            htmlWindowFrame.SetTitle(
                'Help documentation for %s' % (fullModuleName,))

            htmlWindowFrame.SetIcon(moduleUtils.getModuleIcon())

            def handlerModuleHelpDestroy(event):
                htmlWindowFrame.Destroy()
                del self._moduleHelpFrames[fullModuleName]
                
            EVT_BUTTON(htmlWindowFrame, htmlWindowFrame.closeButtonId,
                       handlerModuleHelpDestroy)
            EVT_CLOSE(htmlWindowFrame, handlerModuleHelpDestroy)

        # do rudimentary __doc__ -> html conversion
        docLines = string.split(moduleInstance.__doc__.strip(), '\n')
        for idx in range(len(docLines)):
            docLine = docLines[idx].strip()
            if docLine == '':
                docLines[idx] = '<br><br>'

        # add pretty heading
        htmlDoc = '<center><b>%s</b></center><br><br>' % (fullModuleName,) + \
                  string.join(docLines, '\n')

        # finally change the contents of the new/existing module help window
        htmlWindowFrame.htmlWindow.SetPage(
            '<html><body>%s</body></html>' % (htmlDoc,))

        # if it's already visible, just raise it
        if not htmlWindowFrame.Show(True):
            htmlWindowFrame.Raise()


    def fillModuleLists(self):
        """Build up the module tree from the list of available modules
        supplied by the moduleManager.  At the moment, things will look
        a bit strange if the module tree goes deeper than one level, but
        everything will still work.
        """

        mm = self._devide_app.getModuleManager()
        mm.scanModules()
        self._availableModuleList = mm.getAvailableModuleList()

        self._moduleCats = {}
        # let's build up new dictionary with categoryName as key and
        # list of complete moduleNames as value - check for 'Segments',
        # that's reserved
        for mn,catTuple in self._availableModuleList.items():
            for cat in catTuple:
                if cat in self._moduleCats:
                    self._moduleCats[cat].append(mn)
                else:
                    self._moduleCats[cat] = [mn]


        # list of DVN filenames
        if len(mm.availableSegmentsList) > 0:
            self._moduleCats['Segments'] = mm.availableSegmentsList
                    
        
        # setup all categories
        self._graphFrame.moduleCatsListCtrl.DeleteAllItems()
        idx = 0

        cats = self._moduleCats.keys()
        cats.sort()
        
        for cat in cats:
            self._graphFrame.moduleCatsListCtrl.InsertStringItem(idx, cat)
            idx += 1

        self._graphFrame.moduleCatsListCtrl.SetColumnWidth(0, wxLIST_AUTOSIZE)

        # no category is selected
        self._graphFrame.modulesListCtrl.DeleteAllItems()

    def close_graph_frame_cb(self, event):
        self.hide()

    def show(self):
        self._graphFrame.Show(True)

    def _handlerFileOpenSegment(self, event):
        filename = wxFileSelector(
            "Choose DeVIDE network to load into copy buffer",
            "", "", "dvn",
            "DeVIDE networks (*.dvn)|*.dvn|All files (*.*)|*.*",
            wxOPEN)
        
        if filename:
            self._loadNetworkIntoCopyBuffer(filename)

    def _handlerFileSaveSelected(self, event):
        glyphs = self._glyphSelection.getSelectedGlyphs()
        if glyphs:
            filename = wxFileSelector(
                "Choose filename for DeVIDE network",
                "", "", "dvn",
                "DeVIDE networks (*.dvn)|*.dvn|All files (*.*)|*.*",
                wxSAVE)
                    
            if filename:
                self._saveNetwork(glyphs, filename)

    def _handlerModuleCatsListCtrlSelected(self, event):
        self._graphFrame.modulesListCtrl.DeleteAllItems()

        selectedCats = []

        clc = self._graphFrame.moduleCatsListCtrl
        if clc.GetSelectedItemCount():
            for idx in range(clc.GetItemCount()):
                if clc.GetItemState(idx, wxLIST_STATE_SELECTED):
                    selectedCats.append(clc.GetItemText(idx))

        selectedModuleNames = {}
        for cat in selectedCats:
            for mn in self._moduleCats[cat]:
                # the dict eliminates duplicates
                # we set value to 'cat' so we can later check whether this
                # thing is a segment
                selectedModuleNames[mn] = cat

        # now populate the module list
        self._currentModuleList = []

        # the currentModuleListShort is a list of the names as they are
        # displayed!  the order should be exactly the same as the list
        # that is currently being displayed
        self._currentModuleListShort = []
        idx = 0
        mlc = self._graphFrame.modulesListCtrl

        smnItems = selectedModuleNames.items()
        smnItems.sort()
        
        for mn,cat in smnItems:
            if cat == 'Segments':
                basename = os.path.splitext(os.path.basename(mn))[0]
                mlc.InsertStringItem(idx, basename)
                self._currentModuleListShort.append(basename)
                self._currentModuleList.append('segment:%s' % (mn,))
                # we store this just in case (but it's the same as idx!)
                mlc.SetItemData(idx, len(self._currentModuleList) - 1)
                
            else:
                mParts = mn.split('.')
                mlc.InsertStringItem(idx, mParts[-1])
                self._currentModuleListShort.append(mParts[-1])
                self._currentModuleList.append('module:%s' % (mn,))
                mlc.SetItemData(idx, len(self._currentModuleList) - 1)

            idx += 1

        mlc.SetColumnWidth(0, wxLIST_AUTOSIZE)

    def _handlerModulesListCtrlSelected(self, event):
        mlc = self._graphFrame.modulesListCtrl
        idx = mlc.GetItemData(event.m_itemIndex)
        self._currentModuleList[idx]
        self._graphFrame.GetStatusBar().SetStatusText(
            self._currentModuleList[idx])

    def _handlerPaste(self, event, position):
        if self._copyBuffer:
            self._realiseNetwork(
                # when we paste, we want the thing to reposition!
                self._copyBuffer[0], self._copyBuffer[1], self._copyBuffer[2],
                position, True)

    def _handlerCanvasChar(self, event):

        def prefixSearch(prefix):
            # let's search for a module in the module list with this prefix
            mFound = False
            idx = 0
            for m in self._currentModuleListShort:
                if m.lower().startswith(prefix.lower()):
                    mFound = True
                    break
                
                idx += 1

            if mFound:
                return idx
            else:
                return -1
            
        key = event.GetKeyCode()
        qss = self._quickSearchString
        idx = -1
        
        updateSelectionAndStatusBar = False

        # 'A' - 'z'
        if key >= 65 and key <= 122:
            qss = qss + chr(key)

            idx = prefixSearch(qss)
            updateSelectionAndStatusBar = True
            

        elif key == WXK_BACK:   # backspace removes one character and backs up
            if len(qss) > 0:
                qss = qss[:-1]

            idx = prefixSearch(qss)
            updateSelectionAndStatusBar = True

        elif key == WXK_RETURN:
            # place currently selected module at current mouse pos
            # and zero current qss

            mlc = self._graphFrame.modulesListCtrl
            if mlc.GetSelectedItemCount():
                for idx in range(mlc.GetItemCount()):
                    if mlc.GetItemState(idx, wxLIST_STATE_SELECTED):
                        # place just this one
                        self.canvasDropText(event.GetX(), event.GetY(),
                                            self._currentModuleList[idx])
                        # break out of the for loop
                        break

        elif key == WXK_ESCAPE:
            idx = -1
            qss = ''
            updateSelectionAndStatusBar = True

        else:
            event.Skip()


        if updateSelectionAndStatusBar:
            if idx >= 0:
                # use idx to select that thing
                self._graphFrame.modulesListCtrl.SetItemState(
                    idx, wxLIST_STATE_SELECTED, wxLIST_STATE_SELECTED)
                self._graphFrame.modulesListCtrl.EnsureVisible(idx)

            else:
                # deselect everything
                for idx in range(
                    self._graphFrame.modulesListCtrl.GetItemCount()):
                    self._graphFrame.modulesListCtrl.SetItemState(
                        idx, 0, wxLIST_STATE_SELECTED)
                    

            self._quickSearchString = qss
            self._graphFrame.GetStatusBar().SetStatusText(
                self._quickSearchString)

            
    def _handlerHelpContextHelp(self, event):
        owm = self._graphFrame.canvas.getObjectWithMouse()
        if owm and hasattr(owm, 'moduleInstance'):
            self._helpModule(owm.moduleInstance)

        else:
            md = wxMessageDialog(
                self._graphFrame,
                "Hold the mouse cursor over an already placed module, then "
                "press F1 to see its help documentation.",
                "Information",
                wxOK | wxICON_INFORMATION)
            md.ShowModal()
            
    def _handlerCopySelected(self, event):
        if self._glyphSelection.getSelectedGlyphs():
            self._copyBuffer = self._serialiseNetwork(
                self._glyphSelection.getSelectedGlyphs())

    def _handlerCutSelected(self, event):
        if self._glyphSelection.getSelectedGlyphs():
            self._copyBuffer = self._serialiseNetwork(
                self._glyphSelection.getSelectedGlyphs())
        
            self._deleteSelectedGlyphs()

    def hide(self):
        self._graphFrame.Show(False)

    def _drawPreviewLine(self, beginp, endp0, endp1):

        # make a DC to draw on
        dc = self._graphFrame.canvas.getDC()        

        dc.BeginDrawing()
        
        # dotted line
        dc.SetBrush(wxBrush('WHITE', wx.wxTRANSPARENT))
        dc.SetPen(wxPen('BLACK', 1, wxDOT))
        dc.SetLogicalFunction(wxINVERT) # NOT dst

        # nuke the previous line, draw the new one
        dc.DrawLine(beginp[0], beginp[1], endp0[0], endp0[1])
        dc.DrawLine(beginp[0], beginp[1], endp1[0], endp1[1])
        
        dc.EndDrawing()

    def _drawRubberBand(self, event, endRubberBand=False):
        """Set endRubberBand to True if this is the terminating rubberBand,
        i.e. the last one that gets drawn to erase the previous one when the
        user is done playing with us.
        """
        
        # make a DC to draw on
        dc = self._graphFrame.canvas.getDC()

        dc.BeginDrawing()
        
        # dotted line
        dc.SetBrush(wxBrush('WHITE', wx.wxTRANSPARENT))
        dc.SetPen(wxPen('BLACK', 1, wxDOT))
        dc.SetLogicalFunction(wxINVERT) # NOT dst

        if not self._rubberBandCoords:
            # the user is just beginning to rubberBand
            self._rubberBandCoords = [event.realX, event.realY, 0, 0]
            dc.DrawRectangle(
                self._rubberBandCoords[0], self._rubberBandCoords[1],
                self._rubberBandCoords[2], self._rubberBandCoords[3])

        else:
            dc.DrawRectangle(
                self._rubberBandCoords[0], self._rubberBandCoords[1],
                self._rubberBandCoords[2], self._rubberBandCoords[3])

            if not endRubberBand:
                self._rubberBandCoords[2] = event.realX - \
                                            self._rubberBandCoords[0]
                self._rubberBandCoords[3] = event.realY - \
                                            self._rubberBandCoords[1]

                dc.DrawRectangle(
                    self._rubberBandCoords[0], self._rubberBandCoords[1],
                    self._rubberBandCoords[2], self._rubberBandCoords[3])

            dc.EndDrawing()

    def _disconnect(self, glyph, inputIdx):
        """Disconnect inputIdx'th input of glyph.
        """

        try:
            # first disconnect the actual modules
            mm = self._devide_app.getModuleManager()
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

    def _canvasButtonDown(self, canvas, eventName, event, userData):
        # we should only get this if there's no glyph involved
        if event.RightDown():
            pmenu = wxMenu('Canvas Menu')

            # fill it out with edit (copy, cut, paste, delete) commands
            self._appendEditCommands(pmenu, self._graphFrame.canvas,
                                     (event.realX, event.realY))

            self._graphFrame.canvas.PopupMenu(pmenu, wxPoint(event.GetX(),
                                                             event.GetY()))
            
        elif not event.ShiftDown() and not event.ControlDown():
            self._glyphSelection.removeAllGlyphs()

    def _canvasButtonUp(self, canvas, eventName, event, userData):
        if event.LeftUp():

            # whatever the case may be, stop rubber banding
            self._stopRubberBanding(event)
            
            # any dragged objects?
            if canvas.getDraggedObject() and \
                   canvas.getDraggedObject().draggedPort and \
                   canvas.getDraggedObject().draggedPort != (-1,-1):

                if canvas.getDraggedObject().draggedPort[0] == 0:
                    # the user was dragging an input port and dropped it
                    # on the canvas, so she probably wants us to disconnect
                    inputIdx = canvas.getDraggedObject().draggedPort[1]
                    self._disconnect(canvas.getDraggedObject(),
                                     inputIdx)

    def _canvasDrag(self, canvas, eventName, event, userData):
        if event.LeftIsDown() and not canvas.getDraggedObject():
            self._drawRubberBand(event)

    def _checkAndConnect(self, draggedObject, draggedPort,
                         droppedObject, droppedInputPort):

        if droppedObject.inputLines[droppedInputPort]:
            # the user dropped us on a connected input, we can just bail
            return
            
        if draggedPort[0] == 1:
            # this is a good old "I'm connecting an output to an input"
            self._connect(draggedObject, draggedPort[1],
                          droppedObject, droppedInputPort)
            
            self._graphFrame.canvas.redraw()

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

            self._graphFrame.canvas.redraw()

    def clearAllGlyphsFromCanvas(self):
        allGlyphs = self._graphFrame.canvas.getObjectsOfClass(wxpc.coGlyph)

        mm = self._devide_app.getModuleManager()

        # we take care of the "difficult" modules first
        safeGlyphs = []
        for glyph in allGlyphs:
            if glyph.moduleInstance.__class__.__name__ \
               in mm.dangerousConsumerModules:
                self._deleteModule(glyph)
            else:
                safeGlyphs.append(glyph)

        # and then the rest
        for glyph in safeGlyphs:
            # delete each module, do NOT refresh canvas
            self._deleteModule(glyph, False)

        # only here!
        self._graphFrame.canvas.redraw()

    def _createLine(self, fromObject, fromOutputIdx, toObject, toInputIdx):
        l1 = wxpc.coLine(fromObject, fromOutputIdx,
                         toObject, toInputIdx)
        self._graphFrame.canvas.addObject(l1)
            
        # also record the line in the glyphs
        toObject.inputLines[toInputIdx] = l1
        fromObject.outputLines[fromOutputIdx].append(l1)

        # REROUTE THIS LINE
        self._routeLine(l1)

    def _connect(self, fromObject, fromOutputIdx,
                 toObject, toInputIdx):

        try:
            # connect the actual modules
            mm = self._devide_app.getModuleManager()
            mm.connectModules(fromObject.moduleInstance, fromOutputIdx,
                              toObject.moduleInstance, toInputIdx)

            # if that worked, we can make a linypoo
            self._createLine(fromObject, fromOutputIdx, toObject, toInputIdx)

        except Exception, e:
            genUtils.logError('Could not connect modules: %s' % (str(e)))

    def _deleteSelectedGlyphs(self):
        """Delete all currently selected glyphs.
        """

        # we have to make a deep copy, as we're going to be deleting stuff
        # from this list
        deadGlyphs = [glyph for glyph in \
                      self._glyphSelection.getSelectedGlyphs()]
        
        for glyph in deadGlyphs:
            # delete the glyph, do not refresh the canvas
            self._deleteModule(glyph, False)

        # finally we can let the canvas redraw
        self._graphFrame.canvas.redraw()

    def _realiseNetwork(self, pmsDict, connectionList, glyphPosDict,
                        origin=(0,0), reposition=False):
        """Given a pmsDict, connectionList and glyphPosDict, recreate
        the network described by those structures.  The origin of the glyphs
        will be set.  If reposition is True, the uppermost and leftmost
        coordinates of all glyphs in glyphPosDict is subtracted from all
        stored glyph positions before adding the origin.
        """
        
        # get the module manager to deserialise
        mm = self._devide_app.getModuleManager()
        newModulesDict, newConnections = mm.deserialiseModuleInstances(
            pmsDict, connectionList)
            
        # newModulesDict and newConnections contain the modules and
        # connections which were _actually_ realised... let's draw
        # glyphs!

        if reposition:
            coords = glyphPosDict.values()
            minX = min([coord[0] for coord in coords])
            minY = min([coord[1] for coord in coords])
            reposCoords = [minX, minY]
            
        else:
            reposCoords = [0, 0]

        # store the new glyphs in a dictionary keyed on OLD pickled
        # instanceName so that we can connect them up in the next step
        newGlyphDict = {} 
        for newModulePickledName in newModulesDict.keys():
            position = glyphPosDict[newModulePickledName]
            moduleInstance = newModulesDict[newModulePickledName]
            newGlyph = self.createGlyph(
                position[0] - reposCoords[0] + origin[0],
                position[1] - reposCoords[1] + origin[1],
                moduleInstance.__class__.__name__,
                moduleInstance)
            newGlyphDict[newModulePickledName] = newGlyph

        # now make lines for all the existing connections
        for connection in connectionList:
            sGlyph = newGlyphDict[connection.sourceInstanceName]
            tGlyph = newGlyphDict[connection.targetInstanceName]
            self._createLine(sGlyph, connection.outputIdx,
                             tGlyph, connection.inputIdx)

        # finally we can let the canvas redraw
        self._graphFrame.canvas.redraw()


    def _loadAndRealiseNetwork(self, filename, position=(0,0),
                               reposition=False):
        """Attempt to load (i.e. unpickle) a DVN network file and recreate
        this network on the canvas.

        The position has to be real (i.e. canvas-absolute and NOT event)
        coordinates.
        """

        try:
            pmsDict, connectionList, glyphPosDict = self._loadNetwork(filename)
            self._realiseNetwork(pmsDict, connectionList, glyphPosDict,
                                 position, reposition)
        except Exception, e:
            genUtils.logError(str(e))

    def _loadNetworkIntoCopyBuffer(self, filename):
        """Attempt to load (i.e. unpickle) a DVN network and bind the
        tuple to self._copyBuffer.  When the user pastes, the network will
        be recreated.  DANG!
        """

        try:
            pmsDict, connectionList, glyphPosDict = self._loadNetwork(filename)
            self._copyBuffer = (pmsDict, connectionList, glyphPosDict)

        except Exception, e:
            genUtils.logError(str(e))

    def _loadNetwork(self, filename):
        """Given a filename, read it as a DVN file and return a tuple with
        (pmsDict, connectionList, glyphPosDict) if successful.  If not
        successful, an exception will be raised.
        """
        
        f = None
        try:
            # load the fileData
            f = open(filename, 'rb')
            fileData = f.read()
        except Exception, e:
            if f:
                f.close()

            raise RuntimeError, 'Could not load network from %s:\n%s' % \
                  (filename,str(e))

        f.close()

        try:
            (headerTuple, dataTuple) = cPickle.loads(fileData)
            magic, major, minor, patch = headerTuple
            pmsDict, connectionList, glyphPosDict = dataTuple
            
        except Exception, e:
            raise RuntimeError, 'Could not interpret network from %s:\n%s' % \
                  (filename,str(e))
            

        if magic != 'DVN' and magic != 'D3N' or (major,minor,patch) != (1,0,0):
            raise RuntimeError, '%s is not a valid DeVIDE network file.' % \
                  (filename,)

        return (pmsDict, connectionList, glyphPosDict)



    def _saveNetwork(self, glyphs, filename):
        (pmsDict, connectionList, glyphPosDict) = \
                  self._serialiseNetwork(glyphs)

        # change the serialised moduleInstances to a pickled stream
        headerAndData = (('DVN', 1, 0, 0), \
                        (pmsDict, connectionList, glyphPosDict))
        stream = cPickle.dumps(headerAndData, True)
            
        f = None
        try:
            f = open(filename, 'wb')
            f.write(stream)
        except Exception, e:
            genUtils.logError('Could not write network to %s: %s' % (filename,
                                                                     str(e)))
                                                                     
        if f:
            f.close()

    def _serialiseNetwork(self, glyphs):
        """Given a list of glyphs, return a tuple containing pmsDict,
        connectionList and glyphPosDict.  This can be used to reconstruct the
        whole network from scratch and is used for saving and
        cutting/copying.
        """

        moduleInstances = [glyph.moduleInstance for glyph in glyphs]
        mm = self._devide_app.getModuleManager()

        # let the moduleManager serialise what it can
        pmsDict, connectionList = mm.serialiseModuleInstances(
            moduleInstances)

        savedInstanceNames = [pms.instanceName for pms in pmsDict.values()]
                                  
        # now we also get to store the coordinates of the glyphs which
        # have been saved (keyed on instanceName)
        savedGlyphs = [glyph for glyph in glyphs
                       if mm.getInstanceName(glyph.moduleInstance)\
                       in savedInstanceNames]
            
        glyphPosDict = {}
        for savedGlyph in savedGlyphs:
            instanceName = mm.getInstanceName(savedGlyph.moduleInstance)
            glyphPosDict[instanceName] = savedGlyph.getPosition()

        return (pmsDict, connectionList, glyphPosDict)
        

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
        self._devide_app.quit()

    def _fileNewCallback(self, event):
        self.clearAllGlyphsFromCanvas()

    def _fileOpenCallback(self, event):
        filename = wxFileSelector(
            "Choose DeVIDE network to load",
            "", "", "dvn",
            "DeVIDE networks (*.dvn)|*.dvn|All files (*.*)|*.*",
            wxOPEN)
        
        if filename:
            self.clearAllGlyphsFromCanvas()
            self._loadAndRealiseNetwork(filename)

    def _fileSaveCallback(self, event):
        # make a list of all glyphs
        allGlyphs = self._graphFrame.canvas.getObjectsOfClass(wxpc.coGlyph)
        if allGlyphs:
            filename = wxFileSelector(
                "Choose filename for DeVIDE network",
                "", "", "dvn",
                "DeVIDE networks (*.dvn)|*.dvn|All files (*.*)|*.*",
                wxSAVE)
        
            if filename:
                self._saveNetwork(allGlyphs, filename)

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
            # this means that there's no port involved, so the glyph itself,
            # or the current selection of glyphs, gets dragged
            if glyph in self._glyphSelection.getSelectedGlyphs():
                # move the whole selection (MAN THIS IS CLEAN)
                # err, kick yerself in the nads: you CAN'T use glyph
                # as iteration variable, it'll overwrite the current glyph
                for sglyph in self._glyphSelection.getSelectedGlyphs():
                    canvas.dragObject(sglyph, canvas.getMouseDelta())
            else:
                # or just the glyph under the mouse
                # this clause should never happen, as the dragged glyph
                # always has the selection.
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
            canvas.redraw()

    def _glyphMotion(self, glyph, eventName, event, module):
        port = glyph.findPortContainingMouse(event.realX, event.realY)
        if port:
            self.updatePortInfoStatusBar(glyph, port)

    def _glyphButtonDown(self, glyph, eventName, event, module):
        if event.RightDown():

            pmenu = wxMenu(glyph.getLabel())

            vc_id = wxNewId()
            pmenu.AppendItem(wxMenuItem(pmenu, vc_id, "View-Configure"))
            EVT_MENU(self._graphFrame.canvas, vc_id,
                     lambda e: self._viewConfModule(module))

            help_id = wxNewId()
            pmenu.AppendItem(wxMenuItem(
                pmenu, help_id, "Help on Module"))
            EVT_MENU(self._graphFrame.canvas, help_id,
                     lambda e: self._helpModule(module))
            
            exe_id = wxNewId()
            pmenu.AppendItem(wxMenuItem(pmenu, exe_id, "Execute Module"))
            EVT_MENU(self._graphFrame.canvas, exe_id,
                     lambda e: self._executeModule(module))

            del_id = wxNewId()
            pmenu.AppendItem(wxMenuItem(pmenu, del_id, 'Delete Module'))
            EVT_MENU(self._graphFrame.canvas, del_id,
                     lambda e: self._deleteModule(glyph))

            self._appendEditCommands(pmenu, self._graphFrame.canvas,
                                     (event.GetX(), event.GetY()))

            # popup that menu!
            self._graphFrame.canvas.PopupMenu(pmenu, wxPoint(event.GetX(),
                                                             event.GetY()))
        elif event.LeftDown():
            if event.ControlDown() or event.ShiftDown():
                # with control or shift you can add or remove that glyph
                if glyph.selected:
                    self._glyphSelection.removeGlyph(glyph)
                else:
                    self._glyphSelection.addGlyph(glyph)
            else:
                # if the user already has a selection of which this is a part,
                # we're not going to muck around with that.
                if not glyph.selected:
                    self._glyphSelection.selectGlyph(glyph)
            
    def _glyphButtonUp(self, glyph, eventName, event, module):
        if event.LeftUp():
            # whatever the case may be, stop rubber banding.
            self._stopRubberBanding(event)

            canvas = glyph.getCanvas()

            # when we receive the ButtonUp that ends the drag event, 
            # canvas.getDraggedObject is still set! - it will be unset
            # right after (by the canvas) and then the final drag event
            # will be triggered
            
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
                mi = 1.0 / m
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
                
    def _routeAllLines(self):
        canvas = self._graphFrame.canvas
        # THEN reroute all lines
        allLines = canvas.getObjectsOfClass(wxpc.coLine)
                    
        for line in allLines:
            self._routeLine(line)
            
        # redraw all
        canvas.redraw()
        

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
        mm = self._devide_app.getModuleManager()
        mm.viewModule(module)

    def _deleteModule(self, glyph, refreshCanvas=True):
        try:
            # FIRST remove it from any selections; we have to do this
            # while everything is still more or less active
            self._glyphSelection.removeGlyph(glyph)
            
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
            mm = self._devide_app.getModuleManager()
            # this thing can also remove all links between supplying and
            # consuming objects (we hope) :)
            mm.deleteModule(glyph.moduleInstance)

            canvas = glyph.getCanvas()
            # remove it from the canvas
            canvas.removeObject(glyph)
            # take care of possible lyings around
            glyph.close()

            # after all that work, we deserve a redraw
            if refreshCanvas:
                canvas.redraw()

        except Exception, e:
            genUtils.logError('Could not delete module: %s' % (str(e)))
        
    def _stopRubberBanding(self, event):
        # whatever the case may be, rubberBanding stops
        if self._rubberBandCoords:
            # delete the rubberBand (rubberBandCoords should remain intact)
            self._drawRubberBand(event, endRubberBand=True)

            # now determine all glyphs inside of the rubberBand
            allGlyphs = self._graphFrame.canvas.getObjectsOfClass(
                wxpc.coGlyph)

            glyphsInRubberBand = []
            for glyph in allGlyphs:
                if glyph.isInsideRect(self._rubberBandCoords[0],
                                      self._rubberBandCoords[1],
                                      self._rubberBandCoords[2],
                                      self._rubberBandCoords[3]):
                    glyphsInRubberBand.append(glyph)

            if not event.ControlDown() and not event.ShiftDown():
                self._glyphSelection.removeAllGlyphs()

            # hmmm, can't we be a bit more efficient with this and
            # dc.BeginDrawing()?
            for glyph in glyphsInRubberBand:
                    self._glyphSelection.addGlyph(glyph)
                
            self._rubberBandCoords = None
        
            
            

        
