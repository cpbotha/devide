# slice3d_vwr.py copyright (c) 2002 Charl P. Botha <cpbotha@ieee.org>
# $Id: slice3dVWR.py,v 1.68 2003/08/27 15:09:11 cpbotha Exp $
# next-generation of the slicing and dicing dscas3 module

import cPickle
from external.SwitchColourDialog import ColourDialog
from genUtils import logError
from genMixins import subjectMixin
from moduleBase import moduleBase
from moduleMixins import vtkPipelineConfigModuleMixin, colourDialogMixin
import moduleUtils

# the following four lines are only needed during prototyping of the modules
# that they import
import modules.slice3dVWRmodules.sliceDirections
reload(modules.slice3dVWRmodules.sliceDirections)
import modules.slice3dVWRmodules.tdObjects
reload(modules.slice3dVWRmodules.tdObjects)

from modules.slice3dVWRmodules.sliceDirections import sliceDirections
from modules.slice3dVWRmodules.tdObjects import tdObjects

import time
import vtk
import vtkdscas
from wxPython.wx import *
from wxPython.grid import *
from wxPython.lib import colourdb
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor
import operator


# -------------------------------------------------------------------------

class outputSelectedPoints(list, subjectMixin):
    """class for passing selected points to an output port.

    Derived from list as base and the subject/observer mixin.
    """
    
    def __init__(self):
        list.__init__(self)
        subjectMixin.__init__(self)

    def close(self):
        subjectMixin.close(self)
        
# -------------------------------------------------------------------------
class selectedPoints(object):
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

    def close(self):
        self.removePoints(range(len(self._pointsList)))

    def _bindEvents(self):
        controlFrame = self.slice3dVWR.controlFrame
        
        # the store button
        EVT_BUTTON(controlFrame, controlFrame.sliceStoreButtonId,
                   lambda e: self._handlerStoreCursorAsPoint())

        def pointsSelectAllCallback(event):
            # calling SelectAll and then GetSelectedRows() returns nothing
            #self.threedFrame.spointsGrid.SelectAll()
            # so, we select row by row, and that does seem to work!
            for row in range(self._grid.GetNumberRows()):
                self._grid.SelectRow(row, True)

        def pointsDeselectAllCallback(event):
            self._grid.ClearSelection()

        def pointsRemoveCallback(event):
            selRows = self._grid.GetSelectedRows()
            if len(selRows):
                self.removePoints(selRows)

        EVT_BUTTON(controlFrame,
                   controlFrame.pointsSelectAllButtonId,
                   pointsSelectAllCallback)
        
        EVT_BUTTON(controlFrame,
                   controlFrame.pointsDeselectAllButtonId,
                   pointsDeselectAllCallback)
        
        EVT_BUTTON(controlFrame,
                   controlFrame.pointsRemoveButtonId,
                   pointsRemoveCallback)

        def pointInteractionCheckBoxCallback(event):
            val = controlFrame.pointInteractionCheckBox.GetValue()
            self.enablePointsInteraction(val)
            
        EVT_CHECKBOX(controlFrame,
                     controlFrame.pointInteractionCheckBoxId,
                     pointInteractionCheckBoxCallback)


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

    def _handlerStoreCursorAsPoint(self):
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
            self._pointsList[idx]['sphereActor'].SetPosition(pos)

            # also update the text_actor (if appropriate)
            ta = self._pointsList[idx]['textActor']
            if ta:
                ta.SetPosition(pos)

            inputData = self.slice3dVWR.getPrimaryInput()

            if inputData:
                # then we have to update our internal record of this point
                ispacing = inputData.GetSpacing()
                iorigin = inputData.GetOrigin()
                discrete = map(round,
                               map(operator.div,
                                   map(operator.sub, pos, iorigin), ispacing))
                val = inputData.GetScalarComponentAsFloat(discrete[0],
                                                          discrete[1],
                                                          discrete[2], 0)
            else:
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

        inputs = [i for i in self.slice3dVWR._inputs if i['Connected'] ==
                  'vtkImageDataPrimary']

        if not inputs or not cursor:
            return

        # we first have to check that we don't have this pos already
        discretes = [i['discrete'] for i in self._pointsList]
        if tuple(cursor[0:3]) in discretes:
            return
        
        input_data = inputs[0]['inputData']
        ispacing = input_data.GetSpacing()
        iorigin = input_data.GetOrigin()
        # calculate real coords
        world = map(operator.add, iorigin,
                    map(operator.mul, ispacing, cursor[0:3]))

        pointName = self.slice3dVWR.controlFrame.sliceCursorNameCombo.\
                    GetValue()
        self._storePoint(tuple(cursor[0:3]), tuple(world), cursor[3],
                         pointName)

    def _storePoint(self, discrete, world, value, pointName,
                    lockToSurface=False, boundsForPoints=None):

        tdren = self.slice3dVWR._threedRenderer
        tdrwi = self.slice3dVWR.threedFrame.threedRWI

        if not boundsForPoints:
            bounds = tdren.ComputeVisiblePropBounds()
        else:
            bounds = boundsForPoints
        
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

        ss = vtk.vtkSphereSource()
        #bounds = inputData.GetBounds()

        ss.SetRadius((bounds[1] - bounds[0]) / 100.0)
        sm = vtk.vtkPolyDataMapper()
        sm.SetInput(ss.GetOutput())
        sa = vtk.vtkActor()
        sa.SetMapper(sm)
        sa.SetPosition(world)
        sa.GetProperty().SetColor(1.0,0.0,0.0)
        tdren.AddActor(sa)
        sa.SetPickable(0)

        if len(pointName) > 0:
            name_text = vtk.vtkVectorText()
            name_text.SetText(pointName)
            name_mapper = vtk.vtkPolyDataMapper()
            name_mapper.SetInput(name_text.GetOutput())
            ta = vtk.vtkFollower()
            ta.SetMapper(name_mapper)
            ta.GetProperty().SetColor(1.0, 1.0, 0.0)
            ta.SetPosition(world)
            ta_bounds = ta.GetBounds()
            ta.SetScale((bounds[1] - bounds[0]) / 7.0 /
                        (ta_bounds[1] - ta_bounds[0]))
            tdren.AddActor(ta)
            ta.SetPickable(0)
            ta.SetCamera(tdren.GetActiveCamera())
        else:
            ta = None


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


        # after we've added observers, we get to switch the widget on or
        # off; but it HAS to be on when the observers are added
        if self.slice3dVWR.controlFrame.pointInteractionCheckBox.GetValue():
            pw.On()
        else:
            pw.Off()

        # store the cursor (discrete coords) the coords and the actor
        self._pointsList.append({'discrete' : tuple(discrete),
                                 'world' : tuple(world),
                                 'value' : value,
                                 'name' : pointName,
                                 'pointWidget' : pw,
                                 'lockToSurface' : lockToSurface,
                                 'sphereActor' : sa,
                                 'textActor' : ta})


        self._grid.AppendRows()
        #self._grid.AdjustScrollBars()
        row = self._grid.GetNumberRows() - 1
        self._syncGridRowToSelPoints(row)
        
        # make sure self._outputSelectedPoints is up to date
        self._syncOutputSelectedPoints()

        self.slice3dVWR.render3D()

    def _syncGridRowToSelPoints(self, row):
        # *sniff* *sob* It's unreadable, but why's it so pretty?
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

        del self.outputSelectedPoints[:]

        # then transfer everything
        for i in self._pointsList:
            self.outputSelectedPoints.append({'name' : i['name'],
                                              'discrete' : i['discrete'],
                                              'world' : i['world'],
                                              'value' : i['value']})

        # then make sure this structure knows that it has been modified
        self.outputSelectedPoints.notify()
            


# -------------------------------------------------------------------------

class slice3dVWR(moduleBase, vtkPipelineConfigModuleMixin, colourDialogMixin):
    
    """Slicing, dicing slice viewing class.

    This class is used as a dscas3 module.  Given vtkImageData-like input data,
    it will show 3 slices and 3 planes in a 3d scene.  PolyData objects can
    also be added.  One can interact with the 3d slices to change the slice
    orientation and position.
    """

    gridSelectionBackground = (11, 137, 239)

    def __init__(self, moduleManager):
        # call base constructor
        moduleBase.__init__(self, moduleManager)
        colourDialogMixin.__init__(
            self, moduleManager.get_module_view_parent_window())
        self._numDataInputs = 5
        # use list comprehension to create list keeping track of inputs
        self._inputs = [{'Connected' : None, 'inputData' : None,
                         'observerID' : -1,
                         'vtkActor' : None, 'ipw' : None}
                       for i in range(self._numDataInputs)]
        # then the window containing the renderwindows
        self.threedFrame = None

        # the renderers corresponding to the render windows
        self._threedRenderer = None

        self._outline_source = vtk.vtkOutlineSource()
        om = vtk.vtkPolyDataMapper()
        om.SetInput(self._outline_source.GetOutput())
        self._outline_actor = vtk.vtkActor()
        self._outline_actor.SetMapper(om)
        self._cube_axes_actor2d = vtk.vtkCubeAxesActor2D()

        # use box widget for VOI selection
        self._voi_widget = vtk.vtkBoxWidget()
        # we want to keep it aligned with the cubic volume, thanks
        self._voi_widget.SetRotationEnabled(0)
        self._voi_widget.AddObserver('InteractionEvent',
                                     self.voiWidgetInteractionCallback)
        self._voi_widget.AddObserver('EndInteractionEvent',
                                     self.voiWidgetEndInteractionCallback)

        # also create the VTK construct for actually extracting VOI from data
        self._extractVOI = vtk.vtkExtractVOI()
        self._currentVOI = 6 * [0]

        # set the whole UI up!
        self._create_window()

        # our interactor styles
        self._cInteractorStyle = vtk.vtkInteractorStyleTrackballCamera()
        self._aInteractorStyle = vtkdscas.\
                                 vtkInteractorStyleTrackballActorConstrained()

        # connect up an observer to the actor interactor style so that we
        # get a hook to update things that need to be updated when an actor
        # is moved around
        self._aInteractorStyle.AddObserver(
            'EndInteractionEvent',
            self._observerAIstyleEndInteraction)

        # set the default
        self.threedFrame.threedRWI.SetInteractorStyle(self._cInteractorStyle)

        # initialise our sliceDirections, this will also setup the grid and
        # bind all slice UI events
        self.sliceDirections = sliceDirections(
            self, self.controlFrame.sliceGrid)

        self.selectedPoints = selectedPoints(
            self, self.controlFrame.pointsGrid)

        # we now have a wxListCtrl, let's abuse it
        self._tdObjects = tdObjects(self,
                                    self.controlFrame.objectsListGrid)

    #################################################################
    # module API methods
    #################################################################

    def close(self):
        print "starting close"

        # take care of scalarbar
        self._showScalarBarForProp(None)
        
        # this is standard behaviour in the close method:
        # call set_input(idx, None) for all inputs
        for idx in range(self._numDataInputs):
            self.setInput(idx, None)

        # take care of the sliceDirections
        self.sliceDirections.close()
        del self.sliceDirections

        # the points
        self.selectedPoints.close()
        del self.selectedPoints

        # take care of the threeD objects
        self._tdObjects.close()
        del self._tdObjects

        # don't forget to call the mixin close() methods
        vtkPipelineConfigModuleMixin.close(self)
        colourDialogMixin.close(self)
        
        # unbind everything that we bound in our __init__
        del self._outline_source
        del self._outline_actor
        del self._cube_axes_actor2d
        del self._voi_widget
        del self._extractVOI

        del self._cInteractorStyle
        del self._aInteractorStyle
        
        # take care of all our bindings to renderers
        del self._threedRenderer

        # the remaining bit of logic is quite crucial:
        # we can't explicitly Destroy() the frame, as the RWI that it contains
        # will only disappear when it's reference count reaches 0, and we
        # can't really force that to happen either.  If you DO Destroy() the
        # frame before the RW destructs, it will cause the application to
        # crash because the RW assumes a valid WindowId in its dtor
        #
        # we have two solutions:
        # 1. call a WindowRemap on the RenderWindows so that they reparent
        #    themselves to newly created windowids
        # 2. attach event handlers to the RenderWindow DeleteEvent and
        #    destroy the containing frame from there
        #
        # method 2 doesn't alway work, so we use WindowRemap

        # hide it so long
        #self.threedFrame.Show(0)

        #self.threedFrame.threedRWI.GetRenderWindow().SetSize(10,10)
        self.threedFrame.threedRWI.GetRenderWindow().WindowRemap()
        
        # all the RenderWindow()s are now reparented, so we can destroy
        # the containing frame
        self.threedFrame.Destroy()
        # unbind the _view_frame binding
        del self.threedFrame

        # take care of the controlFrame too
        self.controlFrame.Destroy()
        del self.controlFrame

    def getConfig(self):
        # implant some stuff into the _config object and return it

        self._config.savedPoints = self.selectedPoints.getSavePoints()

        # also save the visible bounds (this will be used during unpickling
        # to calculate pointwidget and text sizes and the like)
        self._config.boundsForPoints = self._threedRenderer.\
                                       ComputeVisiblePropBounds()        

        
        return self._config

    def setConfig(self, aConfig):
        self._config = aConfig

        savedPoints = self._config.savedPoints

        self.selectedPoints.setSavePoints(
            savedPoints, self._config.boundsForPoints)
        
    def getInputDescriptions(self):
        # concatenate it num_inputs times (but these are shallow copies!)
        return self._numDataInputs * \
               ('vtkStructuredPoints|vtkImageData|vtkPolyData',)

    def setInput(self, idx, input_stream):
        if input_stream == None:
            if self._inputs[idx]['Connected'] == 'tdObject':
                self._tdObjects.removeObject(self._inputs[idx]['tdObject'])
                self._inputs[idx]['Connected'] = None
                self._inputs[idx]['tdObject'] = None

            elif self._inputs[idx]['Connected'] == 'vtkImageDataPrimary' or \
                 self._inputs[idx]['Connected'] == 'vtkImageDataOverlay':

                # remove data from the sliceDirections
                self.sliceDirections.removeData(self._inputs[idx]['inputData'])

                # remove our observer
                if self._inputs[idx]['observerID'] >= 0:
                    source = self._inputs[idx]['inputData'].GetSource()
                    if source:
                        source.RemoveObserver(
                            self._inputs[idx]['observerID'])
                    # whether we had a source or not, make sure to zero this
                    self._inputs[idx]['observerID'] = -1

                if self._inputs[idx]['Connected'] == 'vtkImageDataPrimary':
                    self._threedRenderer.RemoveActor(self._outline_actor)
                    self._threedRenderer.RemoveActor(self._cube_axes_actor2d)

                    # deactivate VOI widget as far as possible
                    self._voi_widget.SetInput(None)
                    self._voi_widget.Off()
                    self._voi_widget.SetInteractor(None)

                    # and stop vtkExtractVOI from extracting more VOIs
                    # we have to disconnect this, else the input data will
                    # live on...
                    self._extractVOI.SetInput(None)

                self._inputs[idx]['Connected'] = None
                self._inputs[idx]['inputData'] = None

        # END of if input_stream is None clause -----------------------------

        elif hasattr(input_stream, 'GetClassName') and \
             callable(input_stream.GetClassName):

            if input_stream.GetClassName() == 'vtkVolume' or \
               input_stream.GetClassName() == 'vtkPolyData':
                # our _tdObjects instance likes to do this
                self._tdObjects.addObject(input_stream)
                # if this worked, we have to make a note that it was
                # connected as such
                self._inputs[idx]['Connected'] = 'tdObject'
                self._inputs[idx]['tdObject'] = input_stream
                
            elif input_stream.IsA('vtkImageData'):
                # tell all our sliceDirections about the new data
                self.sliceDirections.addData(input_stream)
                
                # find out whether this is  primary or an overlay, record it
                connecteds = [i['Connected'] for i in self._inputs]
                if 'vtkImageDataPrimary' in connecteds or \
                       'vtkImageDataOverlay' in connecteds:
                    # this must be an overlay
                    self._inputs[idx]['Connected'] = 'vtkImageDataOverlay'
                else:
                    # there are no primaries or overlays, this must be
                    # a primary then
                    self._inputs[idx]['Connected'] = 'vtkImageDataPrimary'

                # also store binding to the data itself
                self._inputs[idx]['inputData'] = input_stream

                # add an observer to this data and store the id
                source = input_stream.GetSource()
                if source:
                    oid = source.AddObserver(
                        'EndEvent',
                        self.inputModifiedCallback)
                    self._inputs[idx]['observerID'] = oid
                
                if self._inputs[idx]['Connected'] == 'vtkImageDataPrimary':
                    # things to setup when primary data is added
                    self._extractVOI.SetInput(input_stream)

                    # add outline actor and cube axes actor to renderer
                    self._threedRenderer.AddActor(self._outline_actor)
                    self._outline_actor.PickableOff()
                    self._threedRenderer.AddActor(self._cube_axes_actor2d)
                    self._cube_axes_actor2d.PickableOff()
                    # FIXME: make this toggle-able
                    self._cube_axes_actor2d.VisibilityOff()

                    # reset everything, including ortho camera
                    self._resetAll()

                # update our 3d renderer
                self.threedFrame.threedRWI.Render()

            else:
                raise TypeError, "Wrong input type!"

        
        # make sure we catch any errors!
        self._moduleManager.vtk_poll_error()

        

    def getOutputDescriptions(self):
        return ('Selected points',
                'Volume of Interest (vtkStructuredPoints)')
        

    def getOutput(self, idx):
        if idx == 0:
            return self.selectedPoints.outputSelectedPoints
        else:
            return self._extractVOI.GetOutput()

    def view(self):
        if not self.threedFrame.Show(True):
            self.threedFrame.Raise()

        if not self.controlFrame.Show(True):
            self.controlFrame.Raise()

    #################################################################
    # miscellaneous public methods
    #################################################################

    def setPropMotion(self, prop, motion=True):
        if motion:
            self._aInteractorStyle.AddActiveProp(prop)
        else:
            self._aInteractorStyle.RemoveActiveProp(prop)

    def getIPWPicker(self):
        return self._ipwPicker

    def getViewFrame(self):
        return self.threedFrame

    def render3D(self):
        """This will cause a render to be called on the encapsulated 3d
        RWI.
        """
        self.threedFrame.threedRWI.Render()

        

    #################################################################
    # internal utility methods
    #################################################################


    def _create_window(self):
        import modules.resources.python.slice3dVWRFrames
        reload(modules.resources.python.slice3dVWRFrames)

        parent_window = self._moduleManager.get_module_view_parent_window()

        # threedFrame creation and basic setup -------------------
        threedFrame = modules.resources.python.slice3dVWRFrames.\
                      threedFrame
        self.threedFrame = threedFrame(parent_window, id=-1,
                                      title='dummy')

        # attach close handler
        EVT_CLOSE(self.threedFrame,
                  lambda e, s=self: s.threedFrame.Show(false))

        self.threedFrame.SetIcon(moduleUtils.getModuleIcon())

        # add the renderer
        self._threedRenderer = vtk.vtkRenderer()
        self._threedRenderer.SetBackground(0.5, 0.5, 0.5)
        self.threedFrame.threedRWI.GetRenderWindow().AddRenderer(self.
                                                               _threedRenderer)
        
        # controlFrame creation and basic setup -------------------
        controlFrame = modules.resources.python.slice3dVWRFrames.\
                       controlFrame
        self.controlFrame = controlFrame(parent_window, id=-1,
                                         title='dummy')
        EVT_CLOSE(self.controlFrame,
                  lambda e: self.controlFrame.Show(false))
        self.controlFrame.SetIcon(moduleUtils.getModuleIcon())


        # fix for the grid
        #self.controlFrame.spointsGrid.SetSelectionMode(wxGrid.wxGridSelectRows)
        #self.controlFrame.spointsGrid.DeleteRows(
        #   0, self.controlFrame.spointsGrid.GetNumberRows())


        # add possible point names
        self.controlFrame.sliceCursorNameCombo.Clear()
        self.controlFrame.sliceCursorNameCombo.Append('Point 1')
        self.controlFrame.sliceCursorNameCombo.Append('GIA Glenoid')
        self.controlFrame.sliceCursorNameCombo.Append('GIA Humerus')
        self.controlFrame.sliceCursorNameCombo.Append('FBZ Superior')
        self.controlFrame.sliceCursorNameCombo.Append('FBZ Inferior')
        
        # event handlers for the global control buttons
        EVT_BUTTON(self.threedFrame, self.threedFrame.showControlsButtonId,
                   self._handlerShowControls)
        
        EVT_BUTTON(self.threedFrame, self.threedFrame.resetCameraButtonId,
                   self._handlerResetCamera)

        EVT_BUTTON(self.threedFrame, self.threedFrame.resetAllButtonId,
                   lambda e, s=self: s._resetAll())
        
        EVT_CHOICE(self.threedFrame,
                   self.threedFrame.projectionChoiceId,
                   self._handlerProjectionChoice)

        EVT_CHOICE(self.threedFrame,
                   self.threedFrame.mouseMovesChoiceId,
                   self._handlerMouseMovesChoice)
        
#         EVT_BUTTON(self.threedFrame, self.threedFrame.pipelineButtonId,
#                    lambda e, pw=self.threedFrame, s=self,
#                    rw=self.threedFrame.threedRWI.GetRenderWindow():
#                    s.vtkPipelineConfigure(pw, rw))

#         EVT_BUTTON(self.threedFrame, self.threedFrame.resetButtonId,
#                    lambda e, s=self: s._resetAll())


        # event logic for the voi panel

        def widgetEnabledCBoxCallback(event):
            if self._voi_widget.GetInput():
                if event.Checked():
                    self._voi_widget.On()
                    self.voiWidgetInteractionCallback(self._voi_widget, None)
                    self.voiWidgetEndInteractionCallback(self._voi_widget,
                                                         None)
                else:
                    self._voi_widget.Off()
            
        EVT_CHECKBOX(self.controlFrame,
                     self.controlFrame.voiEnabledCheckBoxId,
                     widgetEnabledCBoxCallback)

        def _ps_cb():
            # FIXME: update to new factoring
            sliceDirection  = self.getCurrentSliceDirection()
            if sliceDirection:
                val = self.threedFrame.pushSliceSpinCtrl.GetValue()
                if val:
                    sliceDirection.pushSlice(val)
                    self.threedFrame.pushSliceSpinCtrl.SetValue(0)
                    self.threedFrame.threedRWI.Render()

        EVT_SPINCTRL(self.controlFrame, self.controlFrame.pushSliceSpinCtrlId,
                     lambda e: _ps_cb())


        # clicks directly in the window for picking
        self.threedFrame.threedRWI.AddObserver('LeftButtonPressEvent',
                                               self._rwiLeftButtonCallback)
        

        # display the window
        self.threedFrame.Show(True)
        self.controlFrame.Show(True)

    def getPrimaryInput(self):
        """Get primary input data, i.e. bottom layer.

        If there is no primary input data, this will return None.
        """
        
        inputs = [i for i in self._inputs if i['Connected'] ==
                  'vtkImageDataPrimary']

        if inputs:
            inputData = inputs[0]['inputData']
        else:
            inputData = None

        return inputData

    def _resetAll(self):
        """Arrange everything for a single overlay in a single ortho view.

        This method is to be called AFTER the pertinent VTK pipeline has been
        setup.  This is here, because one often connects modules together
        before source modules have been configured, i.e. the success of this
        method is dependent on whether the source modules have been configged.
        HOWEVER: it won't die if it hasn't, just complain.

        It will configure all 3d widgets and textures and thingies, but it
        won't CREATE anything.
        """

        # we only do something here if we have data
        inputDataL = [i['inputData'] for i in self._inputs
                      if i['Connected'] == 'vtkImageDataPrimary']
        if inputDataL:
            inputData = inputDataL[0]
        else:
            return

        # we might have ipws, but no inputData, in which we can't do anything
        # either, so we bail
        if inputData is None:
            return

        # make sure this is all nicely up to date
        inputData.Update()

        # set up helper actors
        self._outline_source.SetBounds(inputData.GetBounds())
        self._cube_axes_actor2d.SetBounds(inputData.GetBounds())
        self._cube_axes_actor2d.SetCamera(
            self._threedRenderer.GetActiveCamera())

        # reset the VOI widget
        self._voi_widget.SetInteractor(self.threedFrame.threedRWI)
        self._voi_widget.SetInput(inputData)
        self._voi_widget.PlaceWidget()
        self._voi_widget.SetPriority(0.6)
        #self._voi_widget.On()

        self._threedRenderer.ResetCamera()

        # make sure the overlays follow  suit
        self.sliceDirections.resetAll()
        
        # whee, thaaaar she goes.
        self.render3D()

    def _showScalarBarForProp(self, prop):
        """Show scalar bar for the data represented by the passed prop.
        If prop is None, the scalar bar will be removed and destroyed if
        present.
        """

        destroyScalarBar = False

        if prop:
            # activate the scalarbar, connect to mapper of prop
            if prop.GetMapper() and prop.GetMapper().GetLookupTable():
                if not hasattr(self, '_pdScalarBarActor'):
                    self._pdScalarBarActor = vtk.vtkScalarBarActor()
                    self._threedRenderer.AddProp(self._pdScalarBarActor)

                sname = "Unknown"
                s = prop.GetMapper().GetInput().GetPointData().GetScalars()
                if s and s.GetName():
                    sname = s.GetName()

                self._pdScalarBarActor.SetTitle(sname)
                    
                self._pdScalarBarActor.SetLookupTable(
                    prop.GetMapper().GetLookupTable())

                self.threedFrame.threedRWI.Render()
                    
            else:
                # the prop doesn't have a mapper or the mapper doesn't
                # have a LUT, either way, we switch off the thingy...
                destroyScalarBar = True

        else:
            # the user has clicked "somewhere else", so remove!
            destroyScalarBar = True
                

        if destroyScalarBar and hasattr(self, '_pdScalarBarActor'):
            self._threedRenderer.RemoveProp(self._pdScalarBarActor)
            del self._pdScalarBarActor
        

    def _storeSurfacePoint(self, actor, pickPosition):
        polyData = actor.GetMapper().GetInput()
        if polyData:
            xyz = pickPosition
        else:
            # something really weird went wrong
            return

        if self.selectedPoints.hasWorldPoint(xyz):
            return

        inputData = self.getPrimaryInput()
            
        if inputData:
            # get the discrete coords of this point
            ispacing = inputData.GetSpacing()
            iorigin = inputData.GetOrigin()
            discrete = map(round,
                           map(operator.div,
                               map(operator.sub, xyz, iorigin), ispacing))
            val = inputData.GetScalarComponentAsFloat(discrete[0],discrete[1],
                                                      discrete[2], 0)
        else:
            discrete = (0, 0, 0)
            val = 0

        pointName = self.controlFrame.sliceCursorNameCombo.GetValue()
        self.selectedPoints._storePoint(
            discrete, xyz, val, pointName, True) # lock to surface

        
    #################################################################
    # callbacks
    #################################################################


    def _handlerProjectionChoice(self, event):
        """Handler for global projection type change.
        """
        
        cam = self._threedRenderer.GetActiveCamera()
        if not cam:
            return
        
        pcs = self.threedFrame.projectionChoice.GetSelection()
        if pcs == 0:
            # perspective
            cam.ParallelProjectionOff()
        else:
            cam.ParallelProjectionOn()

        self.render3D()

    def _handlerMouseMovesChoice(self, event):
        mmcs = self.threedFrame.mouseMovesChoice.GetSelection()

        if mmcs == 0:
            self.threedFrame.threedRWI.SetInteractorStyle(
                self._cInteractorStyle)
        else:
            self.threedFrame.threedRWI.SetInteractorStyle(
                self._aInteractorStyle)

    def _handlerResetCamera(self, event):
        self._threedRenderer.ResetCamera()
        self.render3D()

    def _handlerShowControls(self, event):
        if not self.controlFrame.Show(True):
            self.controlFrame.Raise()

    def _observerAIstyleEndInteraction(self, eventObject, eventType):
        iProp = self._aInteractorStyle.GetInteractionProp()
        if iProp:
            for sd in self._sliceDirections:
                sd.syncContourToObjectViaProp(iProp)


    # DEPRECATED CODE

    def _rw_ortho_pick_cb(self, wxvtkrwi):
        (cx,cy) = wxvtkrwi.GetEventPosition()
        r_idx = self._rwis.index(wxvtkrwi)

        # there has to be data in this pipeline before we can go on
        if len(self._ortho_pipes[r_idx - 1]):
        
            # instantiate WorldPointPicker and use it to get the World Point
            # that we've selected
            wpp = vtk.vtkWorldPointPicker()
            wpp.Pick(cx,cy,0,self._threedRenderers[r_idx])
            (ppx,ppy,ppz) = wpp.GetPickPosition()
            # ppz will be zero too

            # now check that it's within bounds of the sliced data
            reslice = self._ortho_pipes[r_idx - 1][0]['vtkImageReslice']
            rbounds = reslice.GetOutput().GetBounds()

            if ppx >= rbounds[0] and ppx <= rbounds[1] and \
               ppy >= rbounds[2] and ppy <= rbounds[3]:

                # this is just the way that the ResliceAxes are constructed
                # here we do: inpoint = ra * pp
                ra = reslice.GetResliceAxes()
                inpoint = ra.MultiplyPoint((ppx,ppy,ppz,1))

                input_bounds = reslice.GetInput().GetBounds()
                
                # now put this point in the applicable list
                # check that the point is in the volume
                # later we'll have a multi-point mode which is when this
                # "1" conditional will be used
                if 1 and \
                   inpoint[2] >= input_bounds[4] and \
                   inpoint[2] <= input_bounds[5]:

                    self._add_sel_point(inpoint[0:3], r_idx - 1)

                    #self._ortho_huds[r_idx - 1]['vtkAxes'].SetOrigin(ppx,ppy,
                    #                                                 0.5)
                    #self._ortho_huds[r_idx - 1]['axes_actor'].VisibilityOn()

                    self._rwis[r_idx].Render()
    
    # DEPRECATED CODE

    def _rw_slice_cb(self, wxvtkrwi):
        delta = wxvtkrwi.GetEventPosition()[1] - \
                wxvtkrwi.GetLastEventPosition()[1]

        r_idx = self._rwis.index(wxvtkrwi)

        if len(self._ortho_pipes[r_idx - 1]):
            # we make use of the spacing of the first layer, so there
            reslice = self._ortho_pipes[r_idx - 1][0]['vtkImageReslice']
            reslice.UpdateInformation()

            input_spacing = reslice.GetInput().GetSpacing()
            rai = vtk.vtkMatrix4x4()
            vtk.vtkMatrix4x4.Invert(reslice.GetResliceAxes(), rai)
            output_spacing = rai.MultiplyPoint(input_spacing + (0.0,))

            # modify the underlying polydatasource of the planewidget
            ps = self._pws[r_idx - 1].GetPolyDataSource()
            ps.Push(delta * output_spacing[2])
            self._pws[r_idx - 1].UpdatePlacement()

            # then call the pw callback (tee hee)
            self._pw_cb(self._pws[r_idx - 1], r_idx - 1)
            
            # render the 3d viewer
            self._rwis[0].Render()

    # DEPRECATED CODE

    def _rw_windowlevel_cb(self, wxvtkrwi):
        deltax = wxvtkrwi.GetEventPosition()[0] - \
                 wxvtkrwi.GetLastEventPosition()[0]     
        
        deltay = wxvtkrwi.GetEventPosition()[1] - \
                 wxvtkrwi.GetLastEventPosition()[1]

        ortho_idx = self._rwis.index(wxvtkrwi) - 1

        for layer_pl in self._ortho_pipes[ortho_idx]:
            lut = layer_pl['vtkLookupTable']
            lut.SetLevel(lut.GetLevel() + deltay * 5.0)
            lut.SetWindow(lut.GetWindow() + deltax * 5.0)
            lut.Build()

        wxvtkrwi.GetRenderWindow().Render()
        self._rwis[0].GetRenderWindow().Render()


    def voiWidgetInteractionCallback(self, o, e):
        planes = vtk.vtkPlanes()
        o.GetPlanes(planes)
        bounds =  planes.GetPoints().GetBounds()

        # first set bounds
        self.threedFrame.voiPanel.boundsText.SetValue(
            "(%.2f %.2f %.2f %.2f %.2f %.2f) mm" %
            bounds)

        # then set discrete extent (volume relative)
        input_data = self._extractVOI.GetInput()
        ispacing = input_data.GetSpacing()
        iorigin = input_data.GetOrigin()
        # calculate discrete coords
        bounds = planes.GetPoints().GetBounds()
        voi = 6 * [0]
        # excuse the for loop :)
        for i in range(6):
            voi[i] = round((bounds[i] - iorigin[i / 2]) / ispacing[i / 2])
        # store the VOI (this is a shallow copy)
        self._currentVOI = voi
        # display the discrete extent
        self.threedFrame.voiPanel.extentText.SetValue(
            "(%d %d %d %d %d %d)" % tuple(voi))

    def voiWidgetEndInteractionCallback(self, o, e):
        # adjust the vtkExtractVOI with the latest coords
        self._extractVOI.SetVOI(self._currentVOI)

    def inputModifiedCallback(self, o, e):
        # the data has changed, so re-render what's on the screen
        print "calling Render"
        self.threedFrame.threedRWI.Render()
        print "done calling Render"

    def _rwiLeftButtonCallback(self, obj, event):

        def findPickedProp(obj, onlyTdObjects=False):
            # we use a cell picker, because we don't want the point
            # to fall through the polygons, if you know what I mean
            picker = vtk.vtkCellPicker()
            # very important to set this, else we pick the weirdest things
            picker.SetTolerance(0.005)

            if onlyTdObjects:
                pp = self._tdObjects.getPickableProps()
                if not pp:
                    return (None, (0,0,0))
                
                else:
                    # tell the picker which props it's allowed to pick from
                    for p in pp:
                        picker.AddPickList(p)

                    picker.PickFromListOn()
                    
                
            (x,y) = obj.GetEventPosition()
            picker.Pick(x,y,0.0,self._threedRenderer)
            return (picker.GetActor(), picker.GetPickPosition())
            
        pickAction = self.controlFrame.surfacePickActionChoice.GetSelection()
        if pickAction == 1:
            # Place point on surface
            actor, pickPosition = findPickedProp(obj, True)
            if actor:
                self._storeSurfacePoint(actor, pickPosition)
                
        elif pickAction == 2:
            # configure picked object
            prop, unusedPickPosition = findPickedProp(obj)
            if prop:
                self.vtkPipelineConfigure(self.threedFrame,
                                          self.threedFrame.threedRWI, (prop,))

        elif pickAction == 3:
            # show scalarbar for picked object
            prop, unusedPickPosition = findPickedProp(obj)
            self._showScalarBarForProp(prop)

        elif pickAction == 4:
            # move the object -- for this we're going to use a special
            # vtkBoxWidget
            pass
                    
                    

