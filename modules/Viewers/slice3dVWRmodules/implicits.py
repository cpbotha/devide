# implicits.py  copyright (c) 2003 Charl P. Botha <cpbotha@ieee.org>
# $Id: implicits.py,v 1.5 2004/02/23 22:28:35 cpbotha Exp $
#

import genUtils
from modules.Viewers.slice3dVWRmodules.shared import s3dcGridMixin
import vtk
import wx

# -------------------------------------------------------------------------
class implicitInfo:
    def __init__(self):
        self.name = None
        self.type = None
        self.widget = None

class implicits(object, s3dcGridMixin):
    _gridCols = [('Name', 100), ('Type', 0), ('Enabled', 0)]
    _gridNameCol = 0
    _gridTypeCol = 1
    _gridEnabledCol = 2

    _implicitTypes = ['Plane']

    def __init__(self, slice3dVWRThingy, implicitsGrid):
        self.slice3dVWR = slice3dVWRThingy
        self._grid = implicitsGrid

        # dict with name as key, values are implicitInfo classes
        self._implicitsDict = {}

        self._initialiseGrid()

        self._bindEvents()

        # setup choice component
        # first clear
        cf = self.slice3dVWR.controlFrame
        cf.implicitTypeChoice.Clear()
        for implicitType in self._implicitTypes:
            cf.implicitTypeChoice.Append(implicitType)
            
        cf.implicitTypeChoice.SetSelection(0)
        cf.implicitNameText.SetValue("implicit 0")

        # fill out our drop-down menu
        self._disableMenuItems = self._appendGridCommandsToMenu(
            self.slice3dVWR.controlFrame.implicitsMenu,
            self.slice3dVWR.controlFrame, disable=True)

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

    def _createImplicit(self, implicitName, implicitType):
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
                
            
            implicitWidget = None
            rwi = self.slice3dVWR.threedFrame.threedRWI
            ren = self.slice3dVWR._threedRenderer

            # we're going to try to calculate some bounds
            # first see if we have some props
            bounds = self.slice3dVWR._threedRenderer.\
                     ComputeVisiblePropBounds()
            b0 = bounds[1] - bounds[0]
            b1 = bounds[3] - bounds[2]
            b2 = bounds[5] - bounds[4]

            if b0 <= 0 or b1 <= 0 or b2 <= 0:
                # not good enough...                    
                bounds = None

            pi = None
            if bounds != None:
                pi = self.slice3dVWR.getPrimaryInput()

            if implicitType == "Plane":
                implicitWidget = vtk.vtkImplicitPlaneWidget()

                #implicitWidget.SetIn
                if bounds != None:
                    implicitWidget.PlaceWidget(bounds)
                elif pi != None:
                    implicitWidget.SetInput(pi)
                    implicitWidget.PlaceWidget()
                else:
                    implicitWidget.PlaceWidget(-1.0, 1.0, -1.0, 1.0, -1.0, 1.0)

                implicitWidget.SetInteractor(rwi)
                implicitWidget.On()

            if implicitWidget:
                # first add to our internal thingy
                ii = implicitInfo()
                ii.name = implicitName
                ii.type = implicitType                
                ii.widget = implicitWidget
                
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

        # take care of the widget
        w = self._implicitsDict[name].widget
        w.Off()
        w.SetInteractor(None)

        # FIXME: take care of the function

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

    def getSavePoints(self):
        """Get special list of points that can be easily pickled.
        """
        savedPoints = []
        for sp in self._pointsList:
            savedPoints.append({'discrete' : sp['discrete'],
                                'world' : sp['world'],
                                'value' : sp['value'],
                                'name' : sp['name'],
                                'lockToSurface' : sp['lockToSurface']})

        return savedPoints

    def getSelectedWorldPoints(self):
        """Return list of world coordinates that correspond to selected
        points.
        """

        return [self._pointsList[i]['world']
                for i in self._grid.GetSelectedRows()]

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

        cf = self.slice3dVWR.controlFrame
        implicitType = cf.implicitTypeChoice.GetStringSelection()
        implicitName = cf.implicitNameText.GetValue()
        self._createImplicit(implicitName, implicitType)

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

    def _observerPointWidgetInteraction(self, pw, evt_name):
        # we have to find pw in our list
        pwidgets = map(lambda i: i['pointWidget'], self._pointsList)
        if pw in pwidgets:
            idx = pwidgets.index(pw)
            # toggle the selection for this point in our list
            self._grid.SelectRow(idx)

            # if this is lockToSurface, lock it! (and we can only lock
            # to something if there're some pickable objects as reported
            # by the tdObjects class)
            pp = self.slice3dVWR._tdObjects.getPickableProps()            
            if self._pointsList[idx]['lockToSurface'] and pp:
                tdren = self.slice3dVWR._threedRenderer
                # convert the actual pointwidget position back to
                # display coord
                tdren.SetWorldPoint(pw.GetPosition() + (1,))
                tdren.WorldToDisplay()
                ex,ey,ez = tdren.GetDisplayPoint()
                # we make use of a CellPicker (for the same reasons we
                # use it during the initial placement of a surface point)
                picker = vtk.vtkCellPicker()
                # this is quite important
                picker.SetTolerance(0.005)
                
                # tell the picker which props it's allowed to pick from
                for p in pp:
                    picker.AddPickList(p)

                picker.PickFromListOn()
                # and go!
                picker.Pick(ex, ey, 0.0, tdren)
                if picker.GetActor():
                    # correct the pointWidget's position so it sticks to
                    # the surface
                    pw.SetPosition(picker.GetPickPosition())

            # get its position and transfer it to the sphere actor that
            # we use
            pos = pw.GetPosition()
            self._pointsList[idx]['sphereActor'].SetPosition(pos)

            # also update the text_actor (if appropriate)
            ta = self._pointsList[idx]['textActor']
            if ta:
                ta.SetPosition(pos)

            val, discrete = self.slice3dVWR.getValueAtPositionInInputData(pos)
            if val == None:
                discrete = (0, 0, 0)
                val = 0
                
            # the cursor is a tuple with discrete position and value
            self._pointsList[idx]['discrete'] = tuple(discrete)
            # 'world' is the world coordinates
            self._pointsList[idx]['world'] = tuple(pos)
            # and the value
            self._pointsList[idx]['value'] = val

            self._syncGridRowToSelPoints(idx)


    def removePoints(self, idxs):
        """Remove all points at indexes in idxs list.
        """
        # we have to delete one by one from back to front
        idxs.sort()
        idxs.reverse()

        ren = self.slice3dVWR._threedRenderer
        for idx in idxs:
            # remove the sphere actor from the renderer
            ren.RemoveActor(self._pointsList[idx]['sphereActor'])
            # remove the text_actor (if any)
            if self._pointsList[idx]['textActor']:
                ren.RemoveActor(self._pointsList[idx]['textActor'])
            
            # then deactivate and disconnect the point widget
            pw = self._pointsList[idx]['pointWidget']
            pw.SetInput(None)
            pw.Off()
            pw.SetInteractor(None)

            # remove the entries from the wxGrid
            self._grid.DeleteRows(idx)

            # then remove it from our internal list
            del self._pointsList[idx]

            # rerender
            self.slice3dVWR.render3D()

            # and sync up output points
            self._syncOutputSelectedPoints()


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
                genUtils.setGridCellYesNo(
                    self._grid, gridRow, self._gridEnabledCol, ii.enabled)


            


