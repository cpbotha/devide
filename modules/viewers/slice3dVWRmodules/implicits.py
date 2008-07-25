# implicits.py  copyright (c) 2003 Charl P. Botha <cpbotha@ieee.org>
# $Id$

import gen_utils
from modules.viewers.slice3dVWRmodules.shared import s3dcGridMixin
import vtk
import wx

# -------------------------------------------------------------------------
class implicitInfo:
    def __init__(self):
        self.name = None
        self.type = None
        self.widget = None
        self.bounds = None
        self.function = None

class implicits(s3dcGridMixin):
    _gridCols = [('Name', 100), ('Type', 75), ('Enabled', 0)]
    _gridNameCol = 0
    _gridTypeCol = 1
    _gridEnabledCol = 2

    _implicitTypes = ['Plane', 'Sphere']

    _boundsTypes = ['Primary Input', 'Selected object', 'Visible objects',
                    'Manual']

    def __init__(self, slice3dVWRThingy, implicitsGrid):
        self.slice3dVWR = slice3dVWRThingy
        self._grid = implicitsGrid

        # dict with name as key, values are implicitInfo classes
        self._implicitsDict = {}

        # we have to update this function when:
        # * a new implicit is created
        # * an implicit is deleted
        # * the user has adjusted the representative widget
        self.outputImplicitFunction = vtk.vtkImplicitBoolean()
        self.outputImplicitFunction.SetOperationTypeToUnion()

        self._initialiseGrid()

        self._setupGUI()

        self._bindEvents()



    def close(self):
        # delete all implicits, the good way
        # this shouldn't cause problems, because the whole slice3dVWR module
        # has been disconnected by this time
        dNames = self._implicitsDict.keys()
        for dName in dNames:
            self._deleteImplicit(dName)
            
        # make sure we have no more bindings to any of the implicits data
        self._implicitsDict.clear()

        # various other thingies
        self.slice3dVWR = None
        self._grid.ClearGrid()
        self._grid = None

    def _createImplicitFromUI(self):
        cf = self.slice3dVWR.controlFrame
        implicitType = cf.implicitTypeChoice.GetStringSelection()
        implicitName = cf.implicitNameText.GetValue()
        
        if implicitType in self._implicitTypes:
            if implicitName in self._implicitsDict:
                md = wx.MessageDialog(
                    self.slice3dVWR.controlFrame,
                    "You have to enter a unique name for the new implicit. "
                    "Please try again.",
                    "Information",
                    wx.OK | wx.ICON_INFORMATION)
                md.ShowModal()

                return
                
            
            #implicitWidget = None
            
            ren = self.slice3dVWR._threedRenderer


            # let's find out which bounds the user wanted
            cf = self.slice3dVWR.controlFrame
            bt = cf.implicitBoundsChoice.GetStringSelection()

            pi = None
            bounds = None

            bti = self._boundsTypes.index(bt)

            if bti == 0:
                # primary input
                pi = self.slice3dVWR.getPrimaryInput()
                if pi == None:
                    md = wx.MessageDialog(
                        cf,
                        "There is no primary input. "
                        "Please try another bounds type.",
                        "Information",
                        wx.OK | wx.ICON_INFORMATION)
                    md.ShowModal()

                    return

            elif bti == 1:
                # selected object
                objs = self.slice3dVWR._tdObjects._getSelectedObjects()
                if not objs:
                    md = wx.MessageDialog(
                        cf,
                        "No object has been selected. "
                        "Please try another bounds type or select an object.",
                        "Information",
                        wx.OK | wx.ICON_INFORMATION)
                    md.ShowModal()

                    return

                try:
                    prop = self.slice3dVWR._tdObjects.findPropByObject(objs[0])
                    bounds = prop.GetBounds()
                except KeyError:
                    # this should never ever happen
                    return

            elif bti == 2:
                # visible objects
                bounds = self.slice3dVWR._threedRenderer.\
                         ComputeVisiblePropBounds()

            elif bti == 3:
                # manual
                v = cf.implicitManualBoundsText.GetValue()
                t = gen_utils.textToTypeTuple(v, (-1, 1, -1, 1, -1, 1),
                                             6, float)
                cf.implicitManualBoundsText.SetValue(str(t))
                        

            if bounds:
                b0 = bounds[1] - bounds[0]
                b1 = bounds[3] - bounds[2]
                b2 = bounds[5] - bounds[4]

                if b0 <= 0 or b1 <= 0 or b2 <= 0:
                    # not good enough...                    
                    bounds = None

                    md = wx.MessageDialog(
                        cf,
                        "Resultant bounds are invalid. "
                        "Please try again.",
                        "Information",
                        wx.OK | wx.ICON_INFORMATION)
                    md.ShowModal()

                    return
                    
            # at this stage, you MUST have pi or bounds!
            self._createImplicit(implicitType, implicitName, bounds, pi)

    def _createImplicit(self, implicitType, implicitName, bounds, primaryInput):
        if implicitType in self._implicitTypes and \
               implicitName not in self._implicitsDict:

            pi = primaryInput
            rwi = self.slice3dVWR.threedFrame.threedRWI
            implicitInfoBounds = None
            
            if implicitType == "Plane":
                implicitWidget = vtk.vtkImplicitPlaneWidget()
                implicitWidget.SetPlaceFactor(1.25)
                if pi != None:
                    implicitWidget.SetInput(pi)
                    implicitWidget.PlaceWidget()
                    b = pi.GetBounds()
                    implicitWidget.SetOrigin(b[0], b[2], b[4])
                    implicitInfoBounds = b
                elif bounds != None:
                    implicitWidget.PlaceWidget(bounds)
                    implicitWidget.SetOrigin(bounds[0], bounds[2], bounds[4])
                    implicitInfoBounds = bounds
                else:
                    # this can never happen
                    pass

                implicitWidget.SetInteractor(rwi)
                implicitWidget.On()

                # create the implicit function
                implicitFunction = vtk.vtkPlane()
                # sync it to the initial widget
                self._syncPlaneFunctionToWidget(implicitWidget)
                # add it to the output
                self.outputImplicitFunction.AddFunction(implicitFunction)

                # now add an observer to the widget
                def observerImplicitPlaneWidget(widget, eventName):
                    # sync it to the initial widget
                    ret = self._syncPlaneFunctionToWidget(widget)
                    # also select the correct grid row
                    if ret != None:
                        name, ii = ret
                        row = self.findGridRowByName(name)
                        if row >= 0:
                            self._grid.SelectRow(row)

                oId = implicitWidget.AddObserver('EndInteractionEvent',
                                                 observerImplicitPlaneWidget)
                    
            elif implicitType == "Sphere":
                implicitWidget = vtk.vtkSphereWidget()
                implicitWidget.SetPlaceFactor(1.25)
                implicitWidget.TranslationOn()
                implicitWidget.ScaleOn()
                #implicitWidget.HandleVisibilityOn()
                
                if pi != None:
                    implicitWidget.SetInput(pi)
                    implicitWidget.PlaceWidget()
                    b = pi.GetBounds()
                    implicitInfoBounds = b
                    #implicitWidget.SetOrigin(b[0], b[2], b[4])
                elif bounds != None:
                    implicitWidget.PlaceWidget(bounds)
                    implicitInfoBounds = bounds
                    #implicitWidget.SetOrigin(bounds[0], bounds[2], bounds[4])
                else:
                    # this can never happen
                    pass

                implicitWidget.SetInteractor(rwi)
                implicitWidget.On()

                # create the implicit function
                implicitFunction = vtk.vtkSphere()
                # sync it to the initial widget
                self._syncSphereFunctionToWidget(implicitWidget)
                # add it to the output
                self.outputImplicitFunction.AddFunction(implicitFunction)

                # now add an observer to the widget
                def observerImplicitSphereWidget(widget, eventName):
                    # sync it to the initial widget
                    ret = self._syncSphereFunctionToWidget(widget)
                    # also select the correct grid row
                    if ret != None:
                        name, ii = ret
                        row = self.findGridRowByName(name)
                        if row >= 0:
                            self._grid.SelectRow(row)

                oId = implicitWidget.AddObserver('EndInteractionEvent',
                                                 observerImplicitSphereWidget)



            if implicitWidget:
                # set the priority so it gets interaction before the
                # ImagePlaneWidget.  3D widgets have default priority 0.5,
                # so we assign our widgets just a tad higher. (voiwidget
                # has 0.6 for example)
                # NB: in a completely weird twist of events, only slices
                # added AFTER this widget will act like they have lower
                # priority.  The initial slice still takes events from us!
                implicitWidget.SetPriority(0.7)
                
                # add to our internal thingy
                ii = implicitInfo()
                ii.name = implicitName
                ii.type = implicitType
                ii.widget = implicitWidget
                ii.bounds = implicitInfoBounds
                ii.oId = oId
                ii.function = implicitFunction
                
                self._implicitsDict[implicitName] = ii

                # now add to the grid
                nrGridRows = self._grid.GetNumberRows()
                self._grid.AppendRows()
                self._grid.SetCellValue(nrGridRows, self._gridNameCol,
                                        implicitName)
                self._grid.SetCellValue(nrGridRows, self._gridTypeCol,
                                       implicitType)

                # set the relevant cells up for Boolean
                for col in [self._gridEnabledCol]:

                    self._grid.SetCellRenderer(nrGridRows, col,
                                               wx.grid.GridCellBoolRenderer())
                    self._grid.SetCellAlignment(nrGridRows, col,
                                                wx.ALIGN_CENTRE,
                                                wx.ALIGN_CENTRE)

                self._setImplicitEnabled(ii.name, True)

    def _deleteImplicit(self, name):
        dRow = self.findGridRowByName(name)
        if dRow >= 0:
            # delete that row
            self._grid.DeleteRows(dRow)

        ii = self._implicitsDict[name]

        # take care of the widget
        w = ii.widget
        w.RemoveObserver(ii.oId)
        w.Off()
        w.SetInteractor(None)

        self.outputImplicitFunction.RemoveFunction(ii.function)

        # finally remove our record of everything
        del self._implicitsDict[name]
                

    def _appendGridCommandsToMenu(self, menu, eventWidget, disable=True):
        """Appends the points grid commands to a menu.  This can be used
        to build up the context menu or the drop-down one.
        """

        commandsTuple = [
            ('&Create Implicit', 'Create a new implicit with the currently '
             'selected name and type',
             self._handlerCreateImplicit, False),
            ('---',),
            ('Select &All', 'Select all implicits',
             self._handlerSelectAllImplicits, False),
            ('D&Eselect All', 'Deselect all implicits',
             self._handlerDeselectAllImplicits, False),
            ('---',),
            ('&Show', 'Show selected implicits',
             self._handlerShowImplicits, True),
            ('&Hide', 'Hide selected implicits',
             self._handlerHideImplicits, True),
            ('---',), # important!  one-element tuple...
            ('&Rename',
             'Rename selected implicits',
             self._handlerRenameImplicits, True),
            ('&Flip',
             'Flip selected implicits if possible.',
             self._handlerFlipImplicits, True),
            ('---',), # important!  one-element tuple...
            ('&Delete', 'Delete selected implicits',
             self._handlerDeleteImplicits, True)]

        disableList = self._appendGridCommandsTupleToMenu(
            menu, eventWidget, commandsTuple, disable)
        
        return disableList

    def _bindEvents(self):
        controlFrame = self.slice3dVWR.controlFrame
        
        # the store button
        wx.EVT_BUTTON(controlFrame, controlFrame.createImplicitButtonId,
                      self._handlerCreateImplicit)


        wx.grid.EVT_GRID_CELL_RIGHT_CLICK(
            self._grid, self._handlerGridRightClick)
        wx.grid.EVT_GRID_LABEL_RIGHT_CLICK(
            self._grid, self._handlerGridRightClick)

        wx.grid.EVT_GRID_RANGE_SELECT(
            self._grid, self._handlerGridRangeSelect)
        


    def enablePointsInteraction(self, enable):
        """Enable/disable points interaction in the 3d scene.
        """

        if enable:
            for selectedPoint in self._pointsList:
                if selectedPoint['pointWidget']:
                    selectedPoint['pointWidget'].On()
                        
        else:
            for selectedPoint in self._pointsList:
                if selectedPoint['pointWidget']:
                    selectedPoint['pointWidget'].Off()


    def findNameImplicitInfoUsingWidget(self, widget):
        # let's find widget in our records
        found = False
        for name, ii in self._implicitsDict.items():
            if ii.widget == widget:
                found  = True
                break

        if found:
            return name, ii
        else:
            return None
        
        
    def findGridRowByName(self, name):
        nrGridRows = self._grid.GetNumberRows()
        rowFound = False
        row = 0

        while not rowFound and row < nrGridRows:
            value = self._grid.GetCellValue(row, self._gridNameCol)
            rowFound = (value == name)
            row += 1

        if rowFound:
            # prepare and return the row
            row -= 1
            return row
        
        else:
            return -1

    def getImplicitsState(self):
        """Get state of current implicits in a pickle-able data structure.
        """

        implicitsState = []
        for implicitName, implicitInfo in self._implicitsDict.items():
            functionState = None
            
            if implicitInfo.type == 'Plane':
                # we need to get origin and normal
                o = implicitInfo.widget.GetOrigin()
                n = implicitInfo.widget.GetNormal()
                functionState = (o, n)
                
                
            elif implicitInfo.type == 'Sphere':
                # we need to get center and radius
                c = implicitInfo.widget.GetCenter()
                r = implicitInfo.widget.GetRadius()
                functionState = (c, r)
                
            else:
                break
            
            implicitsState.append({'name'   : implicitName,
                                   'type'   : implicitInfo.type,
                                   'bounds' : implicitInfo.bounds,
                                   'fState' : functionState})

        return implicitsState
                                  
    def setImplicitsState(self, implicitsState):
        """Given an implicitsState data structure, create implicits exactly
        as they were when the implicitsState was generated.
        """

        # first delete all implicits
        for dname in self._implicitsDict.keys():
            self._deleteImplicit(dname)

        # now start creating new ones
        for state in implicitsState:
            self._createImplicit(state['type'], state['name'], state['bounds'], None)
            if state['name'] in self._implicitsDict:
                # succesful creation - now restore function state
                ii = self._implicitsDict[state['name']]
                
                if ii.type == 'Plane':
                    ii.widget.SetOrigin(state['fState'][0])
                    ii.widget.SetNormal(state['fState'][1])
                    self._syncPlaneFunctionToWidget(ii.widget)
                    
                elif ii.type == 'Sphere':
                    ii.widget.SetCenter(state['fState'][0])
                    ii.widget.SetRadius(state['fState'][1])
                    self._syncSphereFunctionToWidget(ii.widget)

                else:
                    pass
                    
                
        
    def _getSelectedImplicitNames(self):
        """Return a list of names representing the currently selected
        implicits.
        """
        selRows = self._grid.GetSelectedRows()
        sNames = []
        for sRow in selRows:
            sNames.append(self._grid.GetCellValue(sRow, self._gridNameCol))

        return sNames
        
    def _handlerFlipImplicits(self, event):
        """If any of the selected implicits are of 'Plane' type, flip it, i.e.
        change the direction of the normal.
        """
        
        sNames = self._getSelectedImplicitNames()

        for sName in sNames:
            ii = self._implicitsDict[sName]
            if ii.type == 'Plane':
                # flip both the function and the widget
                n = ii.function.GetNormal()
                fn = [-1.0 * e for e in n]
                ii.function.SetNormal(fn)
                ii.widget.SetNormal(fn)

        if sNames:
            # if we don't re-render, we don't see the flipped thingies
            self.slice3dVWR.render3D()
                                     

    def _handlerGridRightClick(self, gridEvent):
        """This will popup a context menu when the user right-clicks on the
        grid.
        """

        imenu = wx.Menu('Implicits Context Menu')

        self._appendGridCommandsToMenu(imenu, self._grid)
        self._grid.PopupMenu(imenu, gridEvent.GetPosition())

    def _handlerRenameImplicits(self, event):
        selRows = self._grid.GetSelectedRows()
        rNames = []
        for sRow in selRows:
            rNames.append(self._grid.GetCellValue(sRow, self._gridNameCol))

        for rName in rNames:
            self._renameImplicit(rName)

    def _renameImplicit(self, name):
        """Pop-up text box asking the user for a new name.
        """

        if name in self._implicitsDict:
            newName = wx.GetTextFromUser(
                'Please enter a new name for "%s".' % (name,),
                'Implicit Rename', name)

            if newName:
                if newName in self._implicitsDict:
                    md = wx.MessageDialog(
                        self.slice3dVWR.controlFrame,
                        "You have to enter a unique name. "
                        "Please try again.",
                        "Information",
                        wx.OK | wx.ICON_INFORMATION)
                    md.ShowModal()

                else:
                    # first the grid
                    row = self.findGridRowByName(name)
                    if row >= 0:
                        self._grid.SetCellValue(row, self._gridNameCol,
                                                newName)

                    # do the actual renaming
                    ii = self._implicitsDict[name]
                    ii.name = newName
                    del self._implicitsDict[name]
                    self._implicitsDict[newName] = ii

    def _handlerSelectAllImplicits(self, event):
        # calling SelectAll and then GetSelectedRows() returns nothing
        # so, we select row by row, and that does seem to work!
        for row in range(self._grid.GetNumberRows()):
            self._grid.SelectRow(row, True)

    def _handlerDeselectAllImplicits(self, event):
        self._grid.ClearSelection()
        
    def _handlerDeleteImplicits(self, event):
        selRows = self._grid.GetSelectedRows()
        # first get a list of names
        dNames = []
        for sRow in selRows:
            name = self._grid.GetCellValue(sRow, self._gridNameCol)
            dNames.append(name)

        for name in dNames:
            self._deleteImplicit(name)


    def _handlerHideImplicits(self, event):
        selectedRows = self._grid.GetSelectedRows()
        for sRow in selectedRows:
            name = self._grid.GetCellValue(sRow, self._gridNameCol)
            self._setImplicitEnabled(name, False)

    def _handlerShowImplicits(self, event):
        selectedRows = self._grid.GetSelectedRows()
        for sRow in selectedRows:
            name = self._grid.GetCellValue(sRow, self._gridNameCol)
            self._setImplicitEnabled(name, True)

    def _handlerImplicitsInteractionOn(self, event):
        for idx in self._grid.GetSelectedRows():
            self._pointsList[idx]['pointWidget'].On()

    def _handlerImplicitsInteractionOff(self, event):
        for idx in self._grid.GetSelectedRows():
            self._pointsList[idx]['pointWidget'].Off()
        
    def _handlerCreateImplicit(self, event):
        """Create 3d widget and the actual implicit function.
        """

        self._createImplicitFromUI()

    def hasWorldPoint(self, worldPoint):
        worldPoints = [i['world'] for i in self._pointsList]
        if worldPoint in worldPoints:
            return True
        else:
            return False
        

    def _initialiseGrid(self):
        # setup default selection background
        gsb = self.slice3dVWR.gridSelectionBackground
        self._grid.SetSelectionBackground(gsb)
        
        # delete all existing columns
        self._grid.DeleteCols(0, self._grid.GetNumberCols())

        # we need at least one row, else adding columns doesn't work (doh)
        self._grid.AppendRows()
        
        # setup columns
        self._grid.AppendCols(len(self._gridCols))
        for colIdx in range(len(self._gridCols)):
            # add labels
            self._grid.SetColLabelValue(colIdx, self._gridCols[colIdx][0])

        # set size according to labels
        self._grid.AutoSizeColumns()

        for colIdx in range(len(self._gridCols)):
            # now set size overrides
            size = self._gridCols[colIdx][1]
            if size > 0:
                self._grid.SetColSize(colIdx, size)

        # make sure we have no rows again...
        self._grid.DeleteRows(0, self._grid.GetNumberRows())

    def _renameImplicits(self, Idxs, newName):
        for idx in Idxs:
            self._renameImplicit(idx, newName)

    def _setImplicitEnabled(self, implicitName, enabled):
        if implicitName in self._implicitsDict:
            ii = self._implicitsDict[implicitName]

            # in our internal list
            ii.enabled = bool(enabled)
            # the widget
            if ii.widget:
                ii.widget.SetEnabled(ii.enabled)

            # in the grid
            gridRow = self.findGridRowByName(implicitName)
            if gridRow >= 0:
                gen_utils.setGridCellYesNo(
                    self._grid, gridRow, self._gridEnabledCol, ii.enabled)

    def _setupGUI(self):
        # fill out our drop-down menu
        self._disableMenuItems = self._appendGridCommandsToMenu(
            self.slice3dVWR.controlFrame.implicitsMenu,
            self.slice3dVWR.controlFrame, disable=True)
        
        # setup choice component
        # first clear
        cf = self.slice3dVWR.controlFrame
        cf.implicitTypeChoice.Clear()
        for implicitType in self._implicitTypes:
            cf.implicitTypeChoice.Append(implicitType)
            
        cf.implicitTypeChoice.SetSelection(0)
        cf.implicitNameText.SetValue("implicit 0")

        # setup bounds type thingies
        cf.implicitBoundsChoice.Clear()
        for t in self._boundsTypes:
            cf.implicitBoundsChoice.Append(t)

        cf.implicitBoundsChoice.SetSelection(0)

        # setup default value for the manual bounds thingy
        cf.implicitManualBoundsText.SetValue('(-1, 1, -1, 1, -1, 1)')


    def _syncPlaneFunctionToWidget(self, widget):

        # let's find widget in our records
        found = False
        for name, ii in self._implicitsDict.items():
            if ii.widget == widget:
                found  = True
                break

        if found:
            ii.function.SetOrigin(ii.widget.GetOrigin())
            # FIXME: incorporate "sense" setting
            ii.function.SetNormal(ii.widget.GetNormal())

            self._auto_execute()

            # as a convenience, we return the name and ii
            return name, ii
        
        else:
            return None
            

    def _syncSphereFunctionToWidget(self, widget):

        r = self.findNameImplicitInfoUsingWidget(widget)
        if r != None:
            name, ii = r
            
            ii.function.SetCenter(ii.widget.GetCenter())
            ii.function.SetRadius(ii.widget.GetRadius())

            self._auto_execute()

            # as a convenience, we return the name and ii
            return name, ii
        
        else:
            return None

    def _auto_execute(self):
        """Invalidate part 2 of the slice3dVWR module (the implicits part) and
        request an auto execution.

        This method should be called when any of the implicits is modified.
        """
        
        mm = self.slice3dVWR._module_manager
        # part 2 is responsible for the implicit output
        mm.modifyModule(self.slice3dVWR, 2)
        mm.requestAutoExecuteNetwork(self.slice3dVWR)
