# tdObjects.py copyright (c) 2003 by Charl P. Botha <cpbotha@ieee.org>
# $Id: tdObjects.py,v 1.1 2003/06/28 15:29:14 cpbotha Exp $
# class that controls the 3-D objects list

class tdObjects:

    _objectColours = ['LIMEGREEN', 'SKYBLUE', 'PERU', 'CYAN', 
                      'GOLD',  'MAGENTA', 'GREY80',
                      'PURPLE']

    _gridCols = [('Object Name', 0), ('Colour', 150), ('Visible', 0),
                 ('Contour', 0), ('3D Motion', 0)]
    
    _gridNameCol = 0
    _gridColourCol = 1
    _gridVisibleCol = 2
    _gridContourCol = 3
    _gridTDMotionCol = 4

    def __init__(self, slice3dVWRThingy, grid):
        self._tdObjectsDict = {}
        self._objectId = 0
        
        self._slice3dVWR = slice3dVWRThingy
        self._grid = grid
        self._initialiseGrid()
        self._bindEvents()

        # this will fix up wxTheColourDatabase
        colourdb.updateColourDB()

    def close(self):
        self._tdObjectsDict.clear()
        self._slice3dVWR = None
        self._grid.ClearGrid()
        self._grid = None

    def _bindEvents(self):
        svViewFrame = self._slice3dVWR.getViewFrame()

        EVT_BUTTON(svViewFrame, svViewFrame.objectSelectAllButtonId,
                   self._handlerObjectSelectAll)

        EVT_BUTTON(svViewFrame, svViewFrame.objectDeselectAllButtonId,
                   self._handlerObjectDeselectAll)
        
        EVT_BUTTON(svViewFrame, svViewFrame.objectSetColourButtonId,
                   self._handlerObjectSetColour)
        
        EVT_BUTTON(svViewFrame, svViewFrame.objectShowHideButtonId,
                   self._handlerObjectShowHide)

        EVT_BUTTON(svViewFrame, svViewFrame.objectContourButtonId,
                   self._handlerObjectContour)

    def _getSelectedObjects(self):
        objectNames = []        
        selectedRows = self._grid.GetSelectedRows()
        for sRow in selectedRows:
            objectNames.append(
                self._grid.GetCellValue(sRow, self._gridNameCol)
                )

        objs = self.findObjectsByNames(objectNames)
        return objs

    def getContourObjects(self):
        """Returns a list of objects that have contouring activated.
        """
        return [o['tdObject'] for o in self._tdObjectsDict.values()
                if o['contour']]

    def getObjectColour(self, tdObject):
        """Given tdObject, this will return that object's current colour
        in the scene.  If the tdObject doesn't exist in our list, it gets
        green by default.
        """
        
        try:
            return self._tdObjectsDict[tdObject]['colour']
        except:
            return (0.0, 1.0, 0.0)

    def _handlerObjectSelectAll(self, event):
        for row in range(self._grid.GetNumberRows()):
            self._grid.SelectRow(row, True)

    def _handlerObjectDeselectAll(self, event):
        self._grid.ClearSelection()

    def _handlerObjectContour(self, event):
        objs = self._getSelectedObjects()

        for obj in objs:
            contour = self._tdObjectsDict[obj]['contour']
            self._setObjectContouring(obj, not contour)

        if objs:
            self._slice3dVWR.render3D()

    def _handlerObjectSetColour(self, event):
        objs = self._getSelectedObjects()
        
        if objs:
            self._slice3dVWR.setColourDialogColour(
                self._tdObjectsDict[objs[0]]['colour'])
                
            dColour = self._slice3dVWR.getColourDialogColour()
            if dColour:
                for obj in objs:
                    self._setObjectColour(obj, dColour)

        if objs:
            self._slice3dVWR.render3D()
                    

    def _handlerObjectShowHide(self, event):
        objs = self._getSelectedObjects()

        for obj in objs:
            visible = self._tdObjectsDict[obj]['visible']
            self._setObjectVisibility(obj, not visible)

        if objs:
            self._slice3dVWR.render3D()
            
    def _initialiseGrid(self):
        """Setup the object listCtrl from scratch, mmmkay?
        """

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
        
    def addObject(self, tdObject):
        """Takes care of all the administration of adding a new 3-d object
        to the list and updating it in the list control.
        """

        if not self._tdObjectsDict.has_key(tdObject):

            # we get to pick a colour and a name
            colourName = self._objectColours[
                self._objectId % len(self._objectColours)]
            # objectName HAS TO BE unique!
            objectName = "%s%d" % ('obj', self._objectId)
            self._objectId += 1

            # create a colour as well
            colour = wxTheColourDatabase.FindColour(colourName).asTuple()
            # normalise
            nColour = tuple([c / 255.0 for c in colour])

            # now actually create the necessary thingies and add the object
            # to the scene
            if hasattr(tdObject, 'GetClassName') and \
               callable(tdObject.GetClassName):

                if tdObject.GetClassName() == 'vtkVolume':
                    self._slice3dVWR._threedRenderer.AddVolume(tdObject)
                    self._tdObjectsDict[tdObject] = {'tdObject' : tdObject,
                                                     'type' : 'vtkVolume',
                                                     'observerId' : None}

                elif tdObject.GetClassName() == 'vtkPolyData':
                    mapper = vtk.vtkPolyDataMapper()
                    mapper.SetInput(tdObject)
                    actor = vtk.vtkActor()
                    actor.SetMapper(mapper)
                    self._slice3dVWR._threedRenderer.AddActor(actor)
                    self._tdObjectsDict[tdObject] = {'tdObject' : tdObject,
                                                     'type' : 'vtkPolyData',
                                                     'vtkActor' : actor,
                                                     'observerId' : None}

                    # to get the name of the scalars we need to do this.
                    tdObject.Update()
                
                    # now some special case handling
                    if tdObject.GetPointData().GetScalars():
                        sname = tdObject.GetPointData().GetScalars().GetName()
                    else:
                        sname = None
                
                    if sname and sname.lower().find("curvature") >= 0:
                        # if the active scalars have "curvature" somewhere in
                        # their name, activate flat shading and scalar vis
                        property = actor.GetProperty()
                        property.SetInterpolationToFlat()
                        mapper.ScalarVisibilityOn()
                    
                    else:
                        # the user can switch this back on if she really
                        # wants it
                        # we switch it off as we mostly work with isosurfaces
                        mapper.ScalarVisibilityOff()
                
                    # connect an event handler to the data
                    source = tdObject.GetSource()
                    if source:
                        oid = source.AddObserver(
                            'EndEvent',
                            self._tdObjectModifiedCallback)
                        self._tdObjectsDict[tdObject]['observerId'] = oid

                else:
                    raise Exception, 'Non-handled tdObject type'

            else:
                # the object has no GetClassName that's callable
                raise Exception, 'tdObject has no GetClassName()'

            nrGridRows = self._grid.GetNumberRows()
            self._grid.AppendRows()
            self._grid.SetCellValue(nrGridRows, 0, objectName)
            self._grid.SetCellValue(nrGridRows, 1, colourName)
            self._grid.SetCellValue(nrGridRows, 2, 'Yes')
            
            # store the name
            self._tdObjectsDict[tdObject]['objectName'] = objectName
            # and store the colour
            self._setObjectColour(tdObject, nColour)
            # and the visibility
            self._setObjectVisibility(tdObject, True)
            # and the contouring
            self._setObjectContouring(tdObject, False)

            self._slice3dVWR._threedRenderer.ResetCamera()
            self._slice3dVWR.render3D()
            
        # ends 
        else:
            raise Exception, 'Attempt to add same object twice.'

    def findGridRowByName(self, objectName):
        nrGridRows = self._grid.GetNumberRows()
        rowFound = False
        row = 0

        while not rowFound and row < nrGridRows:
            value = self._grid.GetCellValue(row, self._gridNameCol)
            rowFound = (value == objectName)
            row += 1

        if rowFound:
            # prepare and return the row
            row -= 1
            return row
        
        else:
            return -1

    def findObjectsByNames(self, objectNames):
        """Given an objectName, return an object binding.
        """
        
        dictItems = self._tdObjectsDict.items()
        dictLen = len(dictItems)

        objectFound = False
        itemsIdx = 0

        while not objectFound and itemsIdx < dictLen:
            objectFound = objectName == dictItems[itemsIdx][1]['objectName']
            itemsIdx += 1

        if objectFound:
            itemsIdx -= 1
            return dictItems[itemsIdx][0]
        else:
            return None

    def findObjectsByNames(self, objectNames):
        """Given a sequence of object names, return a sequence with bindings
        to all the found objects.  There could be less objects than names.
        """

        dictItems = self._tdObjectsDict.items()
        dictLen = len(dictItems)

        itemsIdx = 0
        foundObjects = []

        while itemsIdx < dictLen:
            if dictItems[itemsIdx][1]['objectName'] in objectNames:
                foundObjects.append(dictItems[itemsIdx][0])

            itemsIdx += 1

        return foundObjects
            

    def removeObject(self, tdObject):
        if not self._tdObjectsDict.has_key(tdObject):
            raise Exception, 'Attempt to remove non-existent tdObject'

        oType = self._tdObjectsDict[tdObject]['type']
        if oType == 'vtkVolume':
            self._slice3dVWR._threedRenderer.RemoveVolume(tdObject)
            self._slice3dVWR.render3D()

        elif oType == 'vtkPolyData':
            # remove all contours due to this object
            self._setObjectContouring(tdObject, False)
            
            actor = self._tdObjectsDict[tdObject]['vtkActor']
            self._slice3dVWR._threedRenderer.RemoveActor(actor)
            if self._tdObjectsDict[tdObject]['observerId']:
                source = actor.GetMapper().GetInput().GetSource()
                if source:
                    source.RemoveObserver(
                        self._tdObjectsDict[tdObject]['observerId'])
                    
                # whether we had a source or not, zero this
                self._tdObjectsDict[tdObject]['observerId'] = None

            self._slice3dVWR.render3D()
            
        else:
            raise Exception,\
                  'Unhandled object type in tdObjects.removeObject()'

        # whatever the case may be, we need to remove it from the wxGrid
        # first search for the correct objectName
        nrGridRows = self._grid.GetNumberRows()
        rowFound = False
        row = 0
        objectName = self._tdObjectsDict[tdObject]['objectName']

        while not rowFound and row < nrGridRows:
            value = self._grid.GetCellValue(row, self._gridNameCol)
            rowFound = value == objectName
            row += 1

        if rowFound:
            # and then delete just that row
            row -= 1
            self._grid.DeleteRows(row)
            
        # and from the dict
        del self._tdObjectsDict[tdObject]

    def _setObjectColour(self, tdObject, dColour):
        if self._tdObjectsDict.has_key(tdObject):
            if self._tdObjectsDict[tdObject]['type'] == 'vtkPolyData':
                objectDict = self._tdObjectsDict[tdObject]
                
                # in our metadata
                objectDict['colour'] = dColour
                
                # change its colour in the scene                
                actor = objectDict['vtkActor']
                actor.GetProperty().SetDiffuseColor(dColour)

                # and change its colour in the grid
                row = self.findGridRowByName(objectDict['objectName'])
                if row >= 0:
                    r,g,b = [c * 255.0 for c in dColour]
                    colour = wxColour(r,g,b)
                    self._grid.SetCellBackgroundColour(
                        row, self._gridColourCol, colour)
                    
                    # also search for the name
                    cName = wxTheColourDatabase.FindName(colour)
                    if not cName:
                        cName = 'USER DEFINED'

                    self._grid.SetCellValue(row, self._gridColourCol, cName)

    def _setObjectVisibility(self, tdObject, visible):
        if self._tdObjectsDict.has_key(tdObject):
            objectDict = self._tdObjectsDict[tdObject]

            # in our own dict
            objectDict['visible'] = bool(visible)
            
            # in the scene
            if objectDict['type'] == 'vtkVolume':
                tdObject.SetVisibility(bool(visible))
            elif objectDict['type'] == 'vtkPolyData':
                objectDict['vtkActor'].SetVisibility(bool(visible))
            else:
                pass

            # finally in the grid
            gridRow = self.findGridRowByName(objectDict['objectName'])
            if gridRow >= 0:
                self._grid.SetCellValue(gridRow, self._gridVisibleCol,
                                        ['No', 'Yes'][bool(visible)])

    def _setObjectContouring(self, tdObject, contour):
        if self._tdObjectsDict.has_key(tdObject):
            objectDict = self._tdObjectsDict[tdObject]

            # in our own dict
            objectDict['contour'] = bool(contour)

            # in the scene
            for sd in self._slice3dVWR._sliceDirections:
                if contour:
                    sd.addContourObject(tdObject)
                else:
                    sd.removeContourObject(tdObject)

            # in the grid
            gridRow = self.findGridRowByName(objectDict['objectName'])
            if gridRow >= 0:
                self._grid.SetCellValue(gridRow, self._gridContourCol,
                                        ['No', 'Yes'][bool(contour)])
                    

    def _tdObjectModifiedCallback(self, o, e):
        self._slice3dVWR.render3D()

