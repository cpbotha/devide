# sliceDirections.py copyright (c) 2003 Charl P. Botha <cpbotha@ieee.org>
# $Id: sliceDirections.py,v 1.5 2003/08/07 22:50:03 cpbotha Exp $
# class encapsulating all instances of the sliceDirection class

import genUtils

# the following two lines are only needed during prototyping of the modules
# that they import
import modules.slice3dVWRmodules.sliceDirection
reload(modules.slice3dVWRmodules.sliceDirection)

from modules.slice3dVWRmodules.sliceDirection import sliceDirection

import vtk
import wx

class sliceDirections(object):

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
        for sliceName, sliceDirection in self._sliceDirectionsDict.items():
            sliceDirection.addContourObject(tdObject, prop3D)

    def _bindEvents(self):
        controlFrame = self.slice3dVWR.controlFrame

        wx.EVT_BUTTON(controlFrame, controlFrame.createSliceButtonId,
                      self._handlerCreateSlice)
        wx.EVT_BUTTON(controlFrame, controlFrame.sliceSelectAllButtonId,
                      self._handlerSliceSelectAll)
        wx.EVT_BUTTON(controlFrame, controlFrame.sliceDeselectAllButtonId,
                      self._handlerSliceDeselectAll)
        wx.EVT_BUTTON(controlFrame, controlFrame.sliceShowHideButtonId,
                      self._handlerSliceShowHide)
        wx.EVT_BUTTON(controlFrame, controlFrame.sliceInteractionButtonId,
                      self._handlerSliceInteraction)
        wx.EVT_BUTTON(controlFrame, controlFrame.sliceDeleteButtonId,
                      self._handlerSliceDelete)
        wx.EVT_BUTTON(controlFrame,
                      controlFrame.sliceLockToPointsButtonId,
                      self._handlerSliceLockToPoints)
        

        wx.EVT_CHOICE(controlFrame, controlFrame.acsChoiceId,
                      self._handlerSliceACS)

        # for ortho view use sliceDirection.createOrthoView()

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

    def _handlerSliceSelectAll(self, event):
        for row in range(self._grid.GetNumberRows()):
            self._grid.SelectRow(row, True)        

    def _handlerSliceDeselectAll(self, event):
        self._grid.ClearSelection()

    def _handlerSliceLockToPoints(self, event):
        selRows = self.slice3dVWR.controlFrame.spointsGrid.GetSelectedRows()
        if len(selRows) >= 3:
            tp = [self.slice3dVWR._selectedPoints[idx]['world']
                  for idx in selRows]
            
            selectedSliceDirections = self.getSelectedSliceDirections()

            for sliceDirection in selectedSliceDirections:
                sliceDirection.lockToPoints(tp[0], tp[1], tp[2])
                
            if selectedSliceDirections:
                self.slice3dVWR.render3D()
                
        else:
            wx.LogMessage("You have to select at least three points.")

    def _handlerSliceShowHide(self, event):
        names = self._getSelectedSliceNames()
        for name in names:
            self._setSliceEnabled(
                name, not self._sliceDirectionsDict[name].getEnabled())

    def _handlerSliceInteraction(self, event):
        names = self._getSelectedSliceNames()
        for name in names:
            self._setSliceInteraction(
                name,
                not self._sliceDirectionsDict[name].getInteractionEnabled())

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

    def _initialiseGrid(self):
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

    def syncContoursToObjectViaProp(self, prop):
        for sliceName, sliceDirection in self._sliceDirectionsDict.items():
            sliceDirection.syncContourToObjectViaProp(prop)
                
