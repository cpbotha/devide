# sliceDirections.py copyright (c) 2003 Charl P. Botha <cpbotha@ieee.org>
# $Id: sliceDirections.py,v 1.1 2003/09/20 21:23:51 cpbotha Exp $
# class encapsulating all instances of the sliceDirection class

import genUtils

# the following two lines are only needed during prototyping of the modules
# that they import
import modules.slice3dVWRmodules.sliceDirection
reload(modules.slice3dVWRmodules.sliceDirection)

from modules.slice3dVWRmodules.sliceDirection import sliceDirection
from modules.slice3dVWRmodules.shared import s3dcGridMixin

import vtk
import wx
import wx.grid

class sliceDirections(object, s3dcGridMixin):

    _gridCols = [('Slice Name', 0), ('Enabled', 0), ('Interaction', 0)]

    _gridNameCol = 0
    _gridEnabledCol = 1
    _gridInteractionCol = 2

    def __init__(self, slice3dVWRThingy, sliceGrid):
        self.slice3dVWR = slice3dVWRThingy
        self._grid = sliceGrid
        self._sliceDirectionsDict = {}

        # this same picker is used on all new IPWS of all sliceDirections
        self.ipwPicker = vtk.vtkCellPicker()

        self.currentCursor = None

        # configure the grid from scratch
        self._initialiseGrid()

        # bind all events
        self._bindEvents()

        # fill out our drop-down menu
        self._disableMenuItems = self._appendGridCommandsToMenu(
            self.slice3dVWR.controlFrame.slicesMenu,
            self.slice3dVWR.controlFrame, disable=True)

        # create the first slice
        self._createSlice('Axial')

    def addData(self, theData):
        try:
            # add this input to all available sliceDirections
            for sliceName, sliceDirection in self._sliceDirectionsDict.items():
                sliceDirection.addData(theData)
                    
        except Exception, msg:
            # if an exception was thrown, clean up and raise again
            for sliceName, sliceDirection in self._sliceDirectionsDict.items():
                sliceDirection.removeData(theData)
                
            raise Exception, msg

    def addContourObject(self, tdObject, prop3D):
        """Activate contouring for tdObject on all sliceDirections.  prop3D
        is the actor/prop representing the tdObject (which is most often a
        vtkPolyData) in the 3d scene.
        """
        for sliceName, sliceDirection in self._sliceDirectionsDict.items():
            sliceDirection.addContourObject(tdObject, prop3D)

    def _appendGridCommandsToMenu(self, menu, eventWidget, disable=True):
        """Appends the slice grid commands to a menu.  This can be used
        to build up the context menu or the drop-down one.
        """

        commandsTuple = [
            ('C&reate Slice', 'Create a new slice',
             self._handlerCreateSlice, False),
            ('---',),
            ('Select &All', 'Select all slices',
             self._handlerSliceSelectAll, False),
            ('D&Eselect All', 'Deselect all slices',
             self._handlerSliceDeselectAll, False),
            ('---',),
            ('&Show', 'Show selected slices',
             self._handlerSliceShow, True),
            ('&Hide', 'Hide selected slices',
             self._handlerSliceHide, True),
            ('&Interaction ON', 'Activate Interaction for all selected slices',
             self._handlerSliceInteractionOn, True),
            ('I&nteraction OFF',
             'Deactivate Interaction for all selected slices',
             self._handlerSliceInteractionOff, True),
            ('---',),
            ('&Lock to Points', 'Move the selected slices to selected points',
             self._handlerSliceLockToPoints, True),
            ('---',),
            ('Reset to A&xial', 'Reset the selected slices to Axial',
            self._handlerSliceResetToAxial, True),
            ('Reset to &Coronal', 'Reset the selected slices to Coronal',
            self._handlerSliceResetToCoronal, True),
            ('Reset to Sa&gittal', 'Reset the selected slices to Sagittal',
            self._handlerSliceResetToSagittal, True),
            ('---',), # important!  one-element tuple...
            ('&Delete', 'Delete selected slices',
             self._handlerSliceDelete, True)]

        disableList = self._appendGridCommandsTupleToMenu(
            menu, eventWidget, commandsTuple, disable)
        
        return disableList
        
    def _bindEvents(self):
        controlFrame = self.slice3dVWR.controlFrame

        wx.EVT_BUTTON(controlFrame, controlFrame.createSliceButtonId,
                      self._handlerCreateSlice)

        # for ortho view use sliceDirection.createOrthoView()

        wx.grid.EVT_GRID_CELL_RIGHT_CLICK(
            self._grid, self._handlerGridRightClick)
        wx.grid.EVT_GRID_LABEL_RIGHT_CLICK(
            self._grid, self._handlerGridRightClick)

        wx.grid.EVT_GRID_RANGE_SELECT(
            self._grid, self._handlerGridRangeSelect)
        

    def close(self):
        for sliceName, sd in self._sliceDirectionsDict.items():
            self._destroySlice(sliceName)

    def _createSlice(self, sliceName):
        if sliceName:
            if sliceName in self._sliceDirectionsDict:
                wx.LogError("A slice with that name already exists.")
                return None
            
            else:
                newSD = sliceDirection(sliceName, self)
                self._sliceDirectionsDict[sliceName] = newSD

                # now attach all inputs to it
                for i in self.slice3dVWR._inputs:
                    if i['Connected'] == 'vtkImageDataPrimary' or \
                           i['Connected'] == 'vtkImageDataOverlay':
                        newSD.addData(i['inputData'])

                # add it to our grid
                nrGridRows = self._grid.GetNumberRows()
                self._grid.AppendRows()
                self._grid.SetCellValue(nrGridRows, self._gridNameCol,
                                        sliceName)

                # set the relevant cells up for Boolean
                for col in [self._gridEnabledCol, self._gridInteractionCol]:
                    # instead of SetCellRenderer, you could have used
                    # wxGrid.SetColFormatBool()
                    self._grid.SetCellRenderer(
                        nrGridRows, col, wx.grid.GridCellBoolRenderer())
                    self._grid.SetCellAlignment(
                        nrGridRows, col, wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)
                

                # set initial boolean values
                self._setSliceEnabled(sliceName, True)
                self._setSliceInteraction(sliceName, True)

                return newSD

    def _destroySlice(self, sliceName):
        """Destroy the named slice."""

        if sliceName in self._sliceDirectionsDict:
            sliceDirection = self._sliceDirectionsDict[sliceName]
            # this will disconnect all inputs
            sliceDirection.close()

            # remove from the grid
            row = self._findGridRowByName(sliceName)
            if row >= 0:
                self._grid.DeleteRows(row)

            # and remove it from our dict
            del self._sliceDirectionsDict[sliceName]

    def _findGridRowByName(self, sliceName):
        nrGridRows = self._grid.GetNumberRows()
        rowFound = False
        row = 0

        while not rowFound and row < nrGridRows:
            value = self._grid.GetCellValue(row, self._gridNameCol)
            rowFound = (value == sliceName)
            row += 1

        if rowFound:
            # prepare and return the row
            row -= 1
            return row
        
        else:
            return -1

    def getSelectedSliceDirections(self):
        """Returns list with bindings to user-selected sliceDirections.
        """
        selectedSliceNames  = self._getSelectedSliceNames()
        selectedSliceDirections = [self._sliceDirectionsDict[sliceName]
                                   for sliceName in selectedSliceNames]
        return selectedSliceDirections

    def _getSelectedSliceNames(self):
        """
        """
        sliceNames = []
        selectedRows = self._grid.GetSelectedRows()
        for row in selectedRows:
            sliceNames.append(
                self._grid.GetCellValue(row, self._gridNameCol))

        return sliceNames

    def _handlerCreateSlice(self, event):
        sliceName = self.slice3dVWR.controlFrame.createSliceComboBox.GetValue()

        newSD = self._createSlice(sliceName)

        if newSD:
            if sliceName == 'Coronal':
                newSD.resetToACS(1)
            elif sliceName == 'Sagittal':
                newSD.resetToACS(2)

            # a new slice was added, re-render!
            self.slice3dVWR.render3D()

    def _handlerGridRightClick(self, gridEvent):
        """This will popup a context menu when the user right-clicks on the
        grid.
        """

        pmenu = wx.Menu('Slices Context Menu')

        self._appendGridCommandsToMenu(pmenu, self._grid)
        self._grid.PopupMenu(pmenu, gridEvent.GetPosition())

    def _handlerSliceSelectAll(self, event):
        for row in range(self._grid.GetNumberRows()):
            self._grid.SelectRow(row, True)        

    def _handlerSliceDeselectAll(self, event):
        self._grid.ClearSelection()

    def _handlerSliceLockToPoints(self, event):
        worldPoints = self.slice3dVWR.selectedPoints.getSelectedWorldPoints()
        if len(worldPoints) >= 3:
            selectedSliceDirections = self.getSelectedSliceDirections()

            for sliceDirection in selectedSliceDirections:
                sliceDirection.lockToPoints(
                    worldPoints[0], worldPoints[1], worldPoints[2])
                
            if selectedSliceDirections:
                self.slice3dVWR.render3D()
                
        else:
            wx.LogMessage("You have to select at least three points.")

    def _handlerSliceHide(self, event):
        names = self._getSelectedSliceNames()
        for name in names:
            self._setSliceEnabled(name, False)

        self.slice3dVWR.render3D()

    def _handlerSliceShow(self, event):
        names = self._getSelectedSliceNames()
        for name in names:
            self._setSliceEnabled(name, True)

        self.slice3dVWR.render3D()
        
    def _handlerSliceShowHide(self, event):
        names = self._getSelectedSliceNames()
        for name in names:
            self._setSliceEnabled(
                name, not self._sliceDirectionsDict[name].getEnabled())

        self.slice3dVWR.render3D()

    def _handlerSliceInteraction(self, event):
        names = self._getSelectedSliceNames()
        for name in names:
            self._setSliceInteraction(
                name,
                not self._sliceDirectionsDict[name].getInteractionEnabled())

    def _handlerSliceInteractionOn(self, event):
        names = self._getSelectedSliceNames()
        for name in names:
            self._setSliceInteraction(
                name,
                True)

    def _handlerSliceInteractionOff(self, event):
        names = self._getSelectedSliceNames()
        for name in names:
            self._setSliceInteraction(
                name,
                False)

    def _handlerSliceDelete(self, event):
        names = self._getSelectedSliceNames()
        for name in names:
            self._destroySlice(name)

        if names:
            self.slice3dVWR.render3D()

    def _handlerSliceACS(self, event):
        selection = self.slice3dVWR.controlFrame.acsChoice.GetSelection()
        names = self._getSelectedSliceNames()
        for name in names:
            sd = self._sliceDirectionsDict[name]
            sd.resetToACS(selection)

        if names:
            self.slice3dVWR.render3D()
        

    def _handlerSliceResetToAxial(self, event):
        names = self._getSelectedSliceNames()
        for name in names:
            sd = self._sliceDirectionsDict[name]
            sd.resetToACS(0)

        if names:
            self.slice3dVWR.render3D()

    def _handlerSliceResetToCoronal(self, event):
        names = self._getSelectedSliceNames()
        for name in names:
            sd = self._sliceDirectionsDict[name]
            sd.resetToACS(1)

        if names:
            self.slice3dVWR.render3D()

    def _handlerSliceResetToSagittal(self, event):
        names = self._getSelectedSliceNames()
        for name in names:
            sd = self._sliceDirectionsDict[name]
            sd.resetToACS(2)

        if names:
            self.slice3dVWR.render3D()

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

    def removeData(self, theData):
        for sliceName, sliceDirection in self._sliceDirectionsDict.items():
            sliceDirection.removeData(theData)

    def removeContourObject(self, tdObject):
        for sliceName, sliceDirection in self._sliceDirectionsDict.items():
            sliceDirection.removeContourObject(tdObject)
            

    def resetAll(self):
        for sliceName, sliceDirection in self._sliceDirectionsDict.items():
            sliceDirection._resetPrimary()
            sliceDirection._resetOverlays()
            sliceDirection._syncContours()
        
    def setCurrentCursor(self, cursor):
        self.currentCursor = cursor
        cstring = str(self.currentCursor[0:3]) + " = " + \
                  str(self.currentCursor[3])
        
        self.slice3dVWR.controlFrame.sliceCursorText.SetValue(cstring)

    def setCurrentSliceDirection(self, sliceDirection):
        # find this sliceDirection
        sdFound = False

        for sliceName, sd in self._sliceDirectionsDict.items():
            if sd == sliceDirection:
                sdFound = True
                break

        if sdFound:
            row = self._findGridRowByName(sliceName)
            if row >= 0:
                self._grid.SelectRow(row, False)
        
    def _setSliceEnabled(self, sliceName, enabled):
        if sliceName in self._sliceDirectionsDict:
            sd = self._sliceDirectionsDict[sliceName]
            if enabled:
                sd.enable()
            else:
                sd.disable()
                
            row = self._findGridRowByName(sliceName)
            if row >= 0:
                genUtils.setGridCellYesNo(
                    self._grid, row, self._gridEnabledCol, enabled)

    def _setSliceInteraction(self, sliceName, interaction):
        if sliceName in self._sliceDirectionsDict:
            sd = self._sliceDirectionsDict[sliceName]
            if interaction:
                sd.enableInteraction()
            else:
                sd.disableInteraction()
                
            row = self._findGridRowByName(sliceName)
            if row >= 0:
                genUtils.setGridCellYesNo(
                    self._grid, row, self._gridInteractionCol, interaction)

    def syncContoursToObject(self, tdObject):
        for sliceName, sliceDirection in self._sliceDirectionsDict.items():
            sliceDirection.syncContourToObject(tdObject)

    def syncContoursToObjectViaProp(self, prop):
        for sliceName, sliceDirection in self._sliceDirectionsDict.items():
            sliceDirection.syncContourToObjectViaProp(prop)
                
