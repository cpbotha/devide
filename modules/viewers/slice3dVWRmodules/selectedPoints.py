# selectedPoints.py  copyright (c) 2003 Charl P. Botha <cpbotha@ieee.org>
# $Id$
#

from genMixins import subjectMixin
from modules.viewers.slice3dVWRmodules.shared import s3dcGridMixin
import operator
import vtk
import wx

# -------------------------------------------------------------------------

class outputSelectedPoints(list, subjectMixin):
    """class for passing selected points to an output port.

    Derived from list as base and the subject/observer mixin.
    """

    devideType = 'namedPoints'
    
    def __init__(self):
        list.__init__(self)
        subjectMixin.__init__(self)

    def close(self):
        subjectMixin.close(self)
        
# -------------------------------------------------------------------------

class selectedPoints(s3dcGridMixin):
    _gridCols = [('Point Name', 0), ('World', 150), ('Discrete', 100),
                 ('Value', 0)]
    _gridNameCol = 0
    _gridWorldCol = 1
    _gridDiscreteCol = 2
    _gridValueCol = 3

    def __init__(self, slice3dVWRThingy, pointsGrid):
        self.slice3dVWR = slice3dVWRThingy
        self._grid = pointsGrid

        self._pointsList = []

        self._initialiseGrid()

        # this will be passed on as input to the next component
        self.outputSelectedPoints = outputSelectedPoints()

        self._bindEvents()

        # fill out our drop-down menu
        self._disableMenuItems = self._appendGridCommandsToMenu(
            self.slice3dVWR.controlFrame.pointsMenu,
            self.slice3dVWR.controlFrame, disable=True)

    def close(self):
        self.removePoints(range(len(self._pointsList)))

    def _appendGridCommandsToMenu(self, menu, eventWidget, disable=True):
        """Appends the points grid commands to a menu.  This can be used
        to build up the context menu or the drop-down one.
        """

        commandsTuple = [
            ('&Store Point', 'Store the current cursor as point',
             self._handlerStoreCursorAsPoint, False),
            ('---',),
            ('Select &All', 'Select all slices',
             self._handlerPointsSelectAll, False),
            ('D&Eselect All', 'Deselect all slices',
             self._handlerPointsDeselectAll, False),
            ('---',),
            ('&Interaction ON +',
             'Activate interaction for the selected points',
             self._handlerPointsInteractionOn, True),
            ('I&nteraction OFF',
             'Deactivate interaction for the selected points',
             self._handlerPointsInteractionOff, True),
            ('---',), # important!  one-element tuple...
            ('&Rename',
             'Rename selected points',
             self._handlerPointsRename, True),
            ('---',), # important!  one-element tuple...
            ('&Delete', 'Delete selected points',
             self._handlerPointsDelete, True)]

        disableList = self._appendGridCommandsTupleToMenu(
            menu, eventWidget, commandsTuple, disable)
        
        return disableList

    def _bindEvents(self):
        controlFrame = self.slice3dVWR.controlFrame
        
        # the store button
        wx.EVT_BUTTON(controlFrame, controlFrame.sliceStoreButtonId,
                      self._handlerStoreCursorAsPoint)


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

        pmenu = wx.Menu('Points Context Menu')

        self._appendGridCommandsToMenu(pmenu, self._grid)
        self._grid.PopupMenu(pmenu, gridEvent.GetPosition())

    def _handlerPointsRename(self, event):
        rslt = wx.GetTextFromUser(
            'Please enter a new name for the selected points '
            '("none" = no name).',
            'Points Rename', '')

        if rslt:
            if rslt.lower() == 'none':
                rslt = ''
                
            selRows = self._grid.GetSelectedRows()
            self._renamePoints(selRows, rslt)

    def _handlerPointsSelectAll(self, event):
        # calling SelectAll and then GetSelectedRows() returns nothing
        # so, we select row by row, and that does seem to work!
        for row in range(self._grid.GetNumberRows()):
            self._grid.SelectRow(row, True)

    def _handlerPointsDeselectAll(self, event):
        self._grid.ClearSelection()
        
    def _handlerPointsDelete(self, event):
        selRows = self._grid.GetSelectedRows()
        if len(selRows):
            self.removePoints(selRows)
            self.slice3dVWR.render3D()

    def _handlerPointsInteractionOn(self, event):
        for idx in self._grid.GetSelectedRows():
            self._pointsList[idx]['pointWidget'].On()

    def _handlerPointsInteractionOff(self, event):
        for idx in self._grid.GetSelectedRows():
            self._pointsList[idx]['pointWidget'].Off()
        
    def _handlerStoreCursorAsPoint(self, event):
        """Call back for the store cursor button.

        Calls store cursor method on [x,y,z,v].
        """
        self._storeCursor(self.slice3dVWR.sliceDirections.currentCursor)



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
            self._pointsList[idx]['sphereActor'].SetAttachmentPoint(pos)

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

    def _renamePoint(self, pointIdx, newName):
        """Given a point index and a new name, this will take care of all
        the actions required to rename a point.  This is often called for
        a series of points, so this function does not refresh the display
        or resync the output list.  You're responsible for that. :)
        """

        if newName != self._pointsList[pointIdx]['name']:
            # we only do something if this has really changed and if the name
            # is not blank

            # first make sure the 3d renderer knows about this
            ca =  self._pointsList[pointIdx]['sphereActor']
            ca.SetCaption(newName)

            # now record the change in our internal list
            self._pointsList[pointIdx]['name'] = newName

            # now in the grid (the rows and pointIdxs correlate)
            self._syncGridRowToSelPoints(pointIdx)

    def _renamePoints(self, pointIdxs, newName):
        for pointIdx in pointIdxs:
            self._renamePoint(pointIdx, newName)

        # now resync the output points
        self._syncOutputSelectedPoints()
        # and redraw stuff
        self.slice3dVWR.render3D()

    def setSavePoints(self, savedPoints, boundsForPoints):
        """Re-install the saved points that were returned with getPoints.
        """

        for sp in savedPoints:
            self._storePoint(sp['discrete'], sp['world'], sp['value'],
                             sp['name'], sp['lockToSurface'],
                             boundsForPoints)

    def _storeCursor(self, cursor):
        """Store the point represented by the cursor parameter.

        cursor is a 4-tuple with the discrete (data-relative) xyz coords and
        the value at that point.
        """

        # we first have to check that we don't have this pos already
        discretes = [i['discrete'] for i in self._pointsList]
        if tuple(cursor[0:3]) in discretes:
            return
        
        worldPos = self.slice3dVWR.getWorldPositionInInputData(cursor[0:3])
        if worldPos == None:
            return

        pointName = self.slice3dVWR.controlFrame.sliceCursorNameCombo.\
                    GetValue()
        self._storePoint(tuple(cursor[0:3]), tuple(worldPos), cursor[3],
                         pointName)

    def _storePoint(self, discrete, world, value, pointName,
                    lockToSurface=False, boundsForPoints=None):

        tdren = self.slice3dVWR._threedRenderer
        tdrwi = self.slice3dVWR.threedFrame.threedRWI

        if not boundsForPoints:
            bounds = tdren.ComputeVisiblePropBounds()
        else:
            bounds = boundsForPoints

        if bounds[1] - bounds[0] <= 0 or \
           bounds[3] - bounds[2] <= 0 or \
           bounds[5] - bounds[4] <= 0:
            bounds = (-1,1,-1,1,-1,1)
        

        # we use a pointwidget
        pw = vtk.vtkPointWidget()
        #pw.SetInput(inputData)
        pw.PlaceWidget(bounds[0], bounds[1], bounds[2], bounds[3], bounds[4],
                       bounds[5])
        pw.SetPosition(world)
        # make priority higher than the default of vtk3DWidget so
        # that imageplanes behind us don't get selected the whole time
        pw.SetPriority(0.6)
        pw.SetInteractor(tdrwi)
        pw.AllOff()
        pw.On()

        #ss.SetRadius((bounds[1] - bounds[0]) / 100.0)
        
        ca = vtk.vtkCaptionActor2D()
        ca.GetProperty().SetColor(1,0,0)
        ca.GetCaptionTextProperty().SetColor(1,0,0)
        ca.SetPickable(0)
        ca.SetAttachmentPoint(world)
        ca.SetPosition(25,10)
        ca.BorderOff()
        ca.SetWidth(0.3)
        ca.SetHeight(0.04)
        # I used to have the problem on my ATI X1600 that interaction
        # was extremely slow of 3D was on... problem seems to have
        # gone away by itself, or it rather has to do with the slow-
        # glcontext-things
        ca.ThreeDimensionalLeaderOn()
        ca.SetMaximumLeaderGlyphSize(10)

        coneSource = vtk.vtkConeSource()
        coneSource.SetResolution(6)
        # we want the cone's very tip to by at 0,0,0
        coneSource.SetCenter(- coneSource.GetHeight() / 2.0, 0, 0)

        ca.SetLeaderGlyph(coneSource.GetOutput())

        if len(pointName) > 0:
            ca.SetCaption(pointName)
            
        else:
            ca.SetCaption("")

        tdren.AddActor(ca)


        def pw_ei_cb(pw, evt_name):
            # make sure our output is good
            self._syncOutputSelectedPoints()

        pw.AddObserver('StartInteractionEvent', lambda pw, evt_name,
                       s=self:
                       s._observerPointWidgetInteraction(pw, evt_name))
        pw.AddObserver('InteractionEvent', lambda pw, evt_name,
                       s=self:
                       s._observerPointWidgetInteraction(pw, evt_name))
        pw.AddObserver('EndInteractionEvent', pw_ei_cb)

        # we start with it disabled
        pw.Off()

        # store the cursor (discrete coords) the coords and the actor
        self._pointsList.append({'discrete' : tuple(discrete),
                                 'world' : tuple(world),
                                 'value' : value,
                                 'name' : pointName,
                                 'pointWidget' : pw,
                                 'lockToSurface' : lockToSurface,
                                 'sphereActor' : ca})

        self._grid.AppendRows()
        #self._grid.AdjustScrollBars()
        row = self._grid.GetNumberRows() - 1
        self._syncGridRowToSelPoints(row)
        
        # make sure self._outputSelectedPoints is up to date
        self._syncOutputSelectedPoints()

        self.slice3dVWR.render3D()

    def _syncGridRowToSelPoints(self, row):
        # this just formats the real point
        name = self._pointsList[row]['name']
        discrete = self._pointsList[row]['discrete']
        world = self._pointsList[row]['world']
        value = self._pointsList[row]['value']
        discreteStr = "%.0f, %.0f, %.0f" % discrete
        worldStr = "%.2f, %.2f, %.2f" % world

        self._grid.SetCellValue(row, self._gridNameCol, name)
        self._grid.SetCellValue(row, self._gridWorldCol, worldStr)
        self._grid.SetCellValue(row, self._gridDiscreteCol, discreteStr)
        self._grid.SetCellValue(row, self._gridValueCol, str(value))

    def _syncOutputSelectedPoints(self):
        """Sync up the output vtkPoints and names to _sel_points.
        
        We play it safe, as the number of points in this list is usually
        VERY low.
        """

        
        temp_output_selected_points = []
        
        # then transfer everything
        for i in self._pointsList:
            temp_output_selected_points.append({'name' : i['name'],
                                                'discrete' : i['discrete'],
                                                'world' : i['world'],
                                                'value' : i['value']})

        if temp_output_selected_points != self.outputSelectedPoints:
            # only if the points have changed do we send them out
            # we have to copy like this so that outputSelectedPoints
            # keeps its type.
            self.outputSelectedPoints[:] = temp_output_selected_points[:]
            

            # make sure that the input-independent part of this module knows
            # that it has been modified
            mm = self.slice3dVWR._moduleManager
            mm.modifyModule(self.slice3dVWR, 1)
            mm.requestAutoExecuteNetwork(self.slice3dVWR)

    


