# slice3d_vwr.py copyright (c) 2002 Charl P. Botha <cpbotha@ieee.org>
# $Id$
# next-generation of the slicing and dicing devide module

# TODO: 'refresh' handlers in set_input()
# TODO: front-end / back-end module split (someday)

import cPickle
import genUtils

from module_base import ModuleBase
from module_mixins import IntrospectModuleMixin, ColourDialogMixin
import module_utils

# the following four lines are only needed during prototyping of the modules
# that they import
import modules.viewers.slice3dVWRmodules.sliceDirections
reload(modules.viewers.slice3dVWRmodules.sliceDirections)
import modules.viewers.slice3dVWRmodules.selectedPoints
reload(modules.viewers.slice3dVWRmodules.selectedPoints)
import modules.viewers.slice3dVWRmodules.tdObjects
reload(modules.viewers.slice3dVWRmodules.tdObjects)
import modules.viewers.slice3dVWRmodules.implicits
reload(modules.viewers.slice3dVWRmodules.implicits)


from modules.viewers.slice3dVWRmodules.sliceDirections import sliceDirections
from modules.viewers.slice3dVWRmodules.selectedPoints import selectedPoints
from modules.viewers.slice3dVWRmodules.tdObjects import tdObjects
from modules.viewers.slice3dVWRmodules.implicits import implicits

import os
import time
import vtk
import vtkdevide

import wx
import weakref
    
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor
import operator


#########################################################################
class slice3dVWR(IntrospectModuleMixin, ColourDialogMixin, ModuleBase):
    
    """Slicing, dicing slice viewing class.

    Please see the main DeVIDE help/user manual by pressing F1.  This module,
    being so absolutely great, has its own section.

    $Revision: 1.52 $
    """

    NUM_INPUTS = 16

    # part 0 is "normal", parts 1,2,3 are the input-independent output parts
    PARTS_TO_INPUTS = {0 : tuple(range(NUM_INPUTS))}
    #PARTS_TO_OUTPUTS = {0 : (3,), 1 : (0, 1, 2)}
    PARTS_TO_OUTPUTS = {0 : (3,4), 1 : (0,4), 2 : (1,4), 3 : (2,4)}
    # part 1 does the points, part 2 does the implicit function,
    # part 2 does the implicits
    # part 3 does the slices polydata
    # this makes it possible for various parts of the slice3dVWR to trigger
    # only bits of the network that are necessary
    # all parts trigger output 4, as that's the 'self' output

    gridSelectionBackground = (11, 137, 239)

    def __init__(self, module_manager):
        # call base constructor
        ModuleBase.__init__(self, module_manager)
        ColourDialogMixin.__init__(
            self, module_manager.get_module_view_parent_window())
        self._numDataInputs = self.NUM_INPUTS
        # use list comprehension to create list keeping track of inputs
        self._inputs = [{'Connected' : None, 'inputData' : None,
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
        self._cube_axes_actor2d.SetFlyModeToOuterEdges()
        #self._cube_axes_actor2d.SetFlyModeToClosestTriad()


        # use box widget for VOI selection
        self._voi_widget = vtk.vtkBoxWidget()
        # we want to keep it aligned with the cubic volume, thanks
        self._voi_widget.SetRotationEnabled(0)
        self._voi_widget.AddObserver('InteractionEvent',
                                     self.voiWidgetInteractionCallback)
        self._voi_widget.AddObserver('EndInteractionEvent',
                                     self.voiWidgetEndInteractionCallback)
        self._voi_widget.NeedsPlacement = True

        # also create the VTK construct for actually extracting VOI from data
        #self._extractVOI = vtk.vtkExtractVOI()
        self._currentVOI = 6 * [0]

        # set the whole UI up!
        self._create_window()

        # our interactor styles (we could add joystick or something too)
        self._cInteractorStyle = vtk.vtkInteractorStyleTrackballCamera()


        # set the default
        self.threedFrame.threedRWI.SetInteractorStyle(self._cInteractorStyle)

        # initialise our sliceDirections, this will also setup the grid and
        # bind all slice UI events
        self.sliceDirections = sliceDirections(
            self, self.controlFrame.sliceGrid)

        self.selectedPoints = selectedPoints(
            self, self.controlFrame.pointsGrid)

        # we now have a wx.ListCtrl, let's abuse it
        self._tdObjects = tdObjects(self,
                                    self.controlFrame.objectsListGrid)

        self._implicits = implicits(self,
                                    self.controlFrame.implicitsGrid)


        # setup orientation widget stuff
        self._orientation_widget = vtk.vtkOrientationMarkerWidget()
        
        self._annotated_cube_actor = aca = vtk.vtkAnnotatedCubeActor()
        #aca.TextEdgesOff()

        aca.GetXMinusFaceProperty().SetColor(1,0,0)
        aca.GetXPlusFaceProperty().SetColor(1,0,0)
        aca.GetYMinusFaceProperty().SetColor(0,1,0)
        aca.GetYPlusFaceProperty().SetColor(0,1,0)
        aca.GetZMinusFaceProperty().SetColor(0,0,1)
        aca.GetZPlusFaceProperty().SetColor(0,0,1)
        
        self._axes_actor = vtk.vtkAxesActor()

        self._orientation_widget.SetInteractor(
            self.threedFrame.threedRWI)
        self._orientation_widget.SetOrientationMarker(
            self._axes_actor)
        self._orientation_widget.On()
        

    #################################################################
    # module API methods
    #################################################################

    def close(self):
        # shut down the orientationWidget/Actor stuff
        self._orientation_widget.Off()
        self._orientation_widget.SetInteractor(None)
        self._orientation_widget.SetOrientationMarker(None)
        del self._orientation_widget
        del self._annotated_cube_actor
        
        # take care of scalarbar
        self._showScalarBarForProp(None)
        
        # this is standard behaviour in the close method:
        # call set_input(idx, None) for all inputs
        for idx in range(self._numDataInputs):
            self.set_input(idx, None)

        # take care of the sliceDirections
        self.sliceDirections.close()
        del self.sliceDirections

        # the points
        self.selectedPoints.close()
        del self.selectedPoints

        # take care of the threeD objects
        self._tdObjects.close()
        del self._tdObjects

        # the implicits
        self._implicits.close()
        del self._implicits

        # don't forget to call the mixin close() methods
        IntrospectModuleMixin.close(self)
        ColourDialogMixin.close(self)
        
        # unbind everything that we bound in our __init__
        del self._outline_source
        del self._outline_actor
        del self._cube_axes_actor2d

        del self._voi_widget
        #del self._extractVOI

        del self._cInteractorStyle

        # make SURE there are no props in the Renderer
        self._threedRenderer.RemoveAllViewProps()
        # take care of all our bindings to renderers
        del self._threedRenderer

        # also do the background renderer
        self._background_renderer.RemoveAllViewProps()
        del self._background_renderer

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
        #self.threedFrame.threedRWI.GetRenderWindow().WindowRemap()

        # finalize should be available everywhere
        self.threedFrame.threedRWI.GetRenderWindow().Finalize()
        # zero the RenderWindow
        self.threedFrame.threedRWI.SetRenderWindow(None)
        # and get rid of the threedRWI interface
        del self.threedFrame.threedRWI
        
        # all the RenderWindow()s are now reparented, so we can destroy
        # the containing frame
        self.threedFrame.Destroy()
        # unbind the _view_frame binding
        del self.threedFrame

        # take care of the objectAnimationFrame
        self.objectAnimationFrame.Destroy()
        del self.objectAnimationFrame

        # take care of the controlFrame too
        self.controlFrame.Destroy()
        del self.controlFrame

        # if we don't give time up here, things go wrong (BadWindow error,
        # invalid glcontext, etc).  we'll have to integrate this with the
        # eventual module front-end / back-end split.  This time-slice
        # allows wx time to destroy all windows which somehow also leads
        # to VTK being able to deallocate everything that it has.
        wx.SafeYield()

    def execute_module(self, part=0):
        # part 0 is the "normal" part and part 1 is the input-independent part
        if part == 0:
            self.render3D()

        else:
            # and make sure outputs and things are up to date!
            self.get_output(2).Update()
            
    def get_config(self):
        # implant some stuff into the _config object and return it
        self._config.savedPoints = self.selectedPoints.getSavePoints()

        # also save the visible bounds (this will be used during unpickling
        # to calculate pointwidget and text sizes and the like)
        self._config.boundsForPoints = self._threedRenderer.\
                                       ComputeVisiblePropBounds()

        self._config.implicitsState = self._implicits.getImplicitsState()
        
        return self._config

    def set_config(self, aConfig):
        self._config = aConfig

        savedPoints = self._config.savedPoints

        self.selectedPoints.setSavePoints(
            savedPoints, self._config.boundsForPoints)

        # we remain downwards compatible
        if hasattr(self._config, 'implicitsState'):
            self._implicits.setImplicitsState(self._config.implicitsState)
        
    def get_input_descriptions(self):
        # concatenate it num_inputs times (but these are shallow copies!)
        return self._numDataInputs * \
               ('vtkStructuredPoints|vtkImageData|vtkPolyData',)

    def set_input(self, idx, inputStream):
        """Attach new input.

        This is the slice3dVWR specialisation of the module API set_input
        call.
        """

        def _handleNewImageDataInput():
            connecteds = [i['Connected'] for i in self._inputs]
            if 'vtkImageDataOverlay' in connecteds and \
                   'vtkImageDataPrimary' not in connecteds:
                # this means the user has disconnected his primary and
                # is trying to reconnect something in its place.  We
                # don't like that...
                raise Exception, \
                      "Please remove all overlays first " \
                      "before attempting to add primary data."

            # if we already have a primary, make sure the new inputStream
            # is added at a higher port number than all existing
            # primaries and overlays
            if 'vtkImageDataPrimary' in connecteds:
                highestPortIndex = connecteds.index('vtkImageDataPrimary')
                for i in range(highestPortIndex, len(connecteds)):
                    if connecteds[i] == 'vtkImageDataOverlay':
                        highestPortIndex = i

                if idx <= highestPortIndex:
                    raise Exception, \
                          "Please add overlay data at higher input " \
                          "port numbers " \
                          "than existing primary data and overlays."

            # tell all our sliceDirections about the new data
            self.sliceDirections.addData(inputStream)
                
            # find out whether this is  primary or an overlay, record it
            if 'vtkImageDataPrimary' in connecteds:
                # there's no way there can be only overlays in the list,
                # the check above makes sure of that
                self._inputs[idx]['Connected'] = 'vtkImageDataOverlay'
            else:
                # there are no primaries or overlays, this must be
                # a primary then
                self._inputs[idx]['Connected'] = 'vtkImageDataPrimary'

            # also store binding to the data itself
            self._inputs[idx]['inputData'] = inputStream

            if self._inputs[idx]['Connected'] == 'vtkImageDataPrimary':
                # things to setup when primary data is added
                #self._extractVOI.SetInput(inputStream)

                # add outline actor and cube axes actor to renderer
                self._threedRenderer.AddActor(self._outline_actor)
                self._outline_actor.PickableOff()
                self._threedRenderer.AddActor(self._cube_axes_actor2d)
                self._cube_axes_actor2d.PickableOff()
                # FIXME: make this toggle-able
                self._cube_axes_actor2d.VisibilityOn()

                # also fix up orientation actor thingy...
                ala = inputStream.GetFieldData().GetArray('axis_labels_array')
                if ala:
                    lut = list('LRPAFH')
                    labels = []
                    for i in range(6):
                        labels.append(lut[ala.GetValue(i)])
                        
                    self._set_annotated_cube_actor_labels(labels)
                    self._orientation_widget.Off()
                    self._orientation_widget.SetOrientationMarker(
                        self._annotated_cube_actor)
                    self._orientation_widget.On()
                    
                else:
                    self._orientation_widget.Off()
                    self._orientation_widget.SetOrientationMarker(
                        self._axes_actor)
                    self._orientation_widget.On()


                # reset everything, including ortho camera
                self._resetAll()

            # update our 3d renderer
            self.threedFrame.threedRWI.Render()

        # end of function _handleImageData()


        if inputStream == None:
            if self._inputs[idx]['Connected'] == 'tdObject':
                self._tdObjects.removeObject(self._inputs[idx]['tdObject'])
                self._inputs[idx]['Connected'] = None
                self._inputs[idx]['tdObject'] = None

            elif self._inputs[idx]['Connected'] == 'vtkImageDataPrimary' or \
                 self._inputs[idx]['Connected'] == 'vtkImageDataOverlay':
                # remove data from the sliceDirections
                self.sliceDirections.removeData(self._inputs[idx]['inputData'])

                if self._inputs[idx]['Connected'] == 'vtkImageDataPrimary':
                    self._threedRenderer.RemoveActor(self._outline_actor)
                    self._threedRenderer.RemoveActor(self._cube_axes_actor2d)

                    # deactivate VOI widget as far as possible
                    self._voi_widget.SetInput(None)
                    self._voi_widget.Off()
                    self._voi_widget.SetInteractor(None)

                self._inputs[idx]['Connected'] = None
                self._inputs[idx]['inputData'] = None

            elif self._inputs[idx]['Connected'] == 'namedWorldPoints':
                pass

            elif self._inputs[idx]['Connected'] == \
                    'vtkLookupTable':
                        # disconnect from sliceDirections
                        self.sliceDirections.set_lookup_table(
                                None)
                        self._inputs[idx]['Connected'] = None
                        self._inputs[idx]['inputData'] = None

        # END of if inputStream is None clause -----------------------------

        # check for VTK types
        elif hasattr(inputStream, 'GetClassName') and \
             callable(inputStream.GetClassName):

            if inputStream.GetClassName() == 'vtkVolume' or \
               inputStream.GetClassName() == 'vtkPolyData':

                # first check if this is a None -> Something or a
                # Something -> Something case.  In the former case, it's
                # a new input, in the latter, it's an existing connection
                # that wants to be updated.

                if self._inputs[idx]['Connected'] is None:
                    # our _tdObjects instance likes to do this
                    self._tdObjects.addObject(inputStream)

                    # if this worked, we have to make a note that it was
                    # connected as such
                    self._inputs[idx]['Connected'] = 'tdObject'
                    self._inputs[idx]['tdObject'] = inputStream

                else:
                    # todo: take necessary actions to 'refresh' input
                    self._tdObjects.updateObject(
                        self._inputs[idx]['tdObject'], inputStream)
                    # and record the new object in our input lists
                    self._inputs[idx]['Connected'] = 'tdObject'
                    self._inputs[idx]['tdObject'] = inputStream
                    
                
            elif inputStream.IsA('vtkImageData'):
                if self._inputs[idx]['Connected'] is None:
                    _handleNewImageDataInput()

                else:
                    # take necessary actions to refresh
                    prevData = self._inputs[idx]['inputData']
                    self.sliceDirections.updateData(prevData, inputStream)
                    # record it in our main structure
                    self._inputs[idx]['inputData'] = inputStream

            elif inputStream.IsA('vtkLookupTable'):
                self.sliceDirections.set_lookup_table(
                        inputStream)
                self._inputs[idx]['Connected'] = \
                        'vtkLookupTable'
                self._inputs[idx]['inputData'] = inputStream

            else:
                raise TypeError, "Wrong input type!"

        # ends: elif hasattr GetClassName
        elif hasattr(inputStream, 'devideType'):
            # todo: re-implement, this will now be called at EVERY
            # network execute!
            print "has d3type"
            if inputStream.devideType == 'namedPoints':
                print "d3type correct"
                # add these to our selected points!
                self._inputs[idx]['Connected'] = 'namedWorldPoints'
                for point in inputStream:
                    self.selectedPoints._storePoint(
                        (0,0,0), point['world'], 0.0,
                        point['name'])

        else:
            raise TypeError, "Input type not recognised!"

    def get_output_descriptions(self):
        return ('Selected points',
                'Implicit Function',
                'Slices polydata',
                'Slices unstructured grid',
                'self (slice3dVWR object)')
        

    def get_output(self, idx):
        if idx == 0:
            return self.selectedPoints.outputSelectedPoints
        elif idx == 1:
            return self._implicits.outputImplicitFunction
        elif idx == 2:
            return self.sliceDirections.ipwAppendPolyData.GetOutput()
        elif idx == 3:
            return self.sliceDirections.ipwAppendFilter.GetOutput()
        else:
            return self
        
#         else:
#             class RenderInfo:
#                 def __init__(self, renderer, render_window, interactor):
#                     self.renderer = renderer
#                     self.render_window = render_window
#                     self.interactor = interactor

#             render_info = RenderInfo(
#                 self._threedRenderer,
#                 self.threedFrame.threedRWI.GetRenderWindow(),
#                 self.threedFrame.threedRWI)
            
#             return render_info
                    
    def view(self):
        # when a view is requested, we only show the 3D window
        # the user can show the control panel by using the button
        # made for that purpose.
        self.threedFrame.Show(True)
        # make sure the view comes to the front
        self.threedFrame.Raise()

        # need to call this so that the window is actually refreshed
        wx.SafeYield()

        # and then make sure the 3D renderer is working (else we
        # get empty windows)
        self.render3D()

    #################################################################
    # miscellaneous public methods
    #################################################################

    def getIPWPicker(self):
        return self._ipwPicker

    def getViewFrame(self):
        return self.threedFrame

    def get_3d_renderer(self):
        """All external entities MUST use this method to get to the VTK
        renderer.
        """
        return weakref.proxy(self._threedRenderer)

    def get_3d_render_window(self):
        """All external entities MUST use this method to get to the VTK
        render window.
        """
        return weakref.proxy(self.threedFrame.threedRWI.GetRenderWindow())

    def get_3d_render_window_interactor(self):
        """All external entities MUST use this method to get to the VTK render
        window interactor.
        """
        return weakref.proxy(self.threedFrame.threedRWI)

    def render3D(self):
        """This will cause a render to be called on the encapsulated 3d
        RWI.
        """
        self.threedFrame.threedRWI.Render()

        

    #################################################################
    # internal utility methods
    #################################################################


    def _create_window(self):
        import modules.viewers.resources.python.slice3dVWRFrames
        reload(modules.viewers.resources.python.slice3dVWRFrames)

        stereo = self._module_manager.get_app_main_config().stereo
        #print "STEREO:", stereo
        modules.viewers.resources.python.slice3dVWRFrames.S3DV_STEREO = stereo

        # threedFrame creation and basic setup -------------------
        threedFrame = modules.viewers.resources.python.slice3dVWRFrames.\
                      threedFrame
        self.threedFrame = module_utils.instantiateModuleViewFrame(
            self, self._module_manager, threedFrame)
        self.threedFrame.SetTitle('slice3dVWR 3D view')
            
        # see about stereo
        #self.threedFrame.threedRWI.GetRenderWindow().SetStereoCapableWindow(1)

        # create foreground and background renderers 
        self._threedRenderer = vtk.vtkRenderer()
        self._background_renderer = vtk.vtkRenderer()

        renwin = self.threedFrame.threedRWI.GetRenderWindow()
   
        # use function to setup fg and bg renderers so we can have a
        # nice gradient background.
        import module_kits.vtk_kit
        module_kits.vtk_kit.utils.setup_renderers(renwin,
                self._threedRenderer, self._background_renderer)

        # controlFrame creation and basic setup -------------------
        controlFrame = modules.viewers.resources.python.slice3dVWRFrames.\
                       controlFrame
        self.controlFrame = module_utils.instantiateModuleViewFrame(
            self, self._module_manager, controlFrame)
        self.controlFrame.SetTitle('slice3dVWR Controls')

        # fix for the grid
        #self.controlFrame.spointsGrid.SetSelectionMode(wx.Grid.wxGridSelectRows)
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
        wx.EVT_BUTTON(self.threedFrame, self.threedFrame.showControlsButtonId,
                   self._handlerShowControls)
        
        wx.EVT_BUTTON(self.threedFrame, self.threedFrame.resetCameraButtonId,
                   self._handlerResetCamera)

        wx.EVT_BUTTON(self.threedFrame, self.threedFrame.resetAllButtonId,
                   lambda e: (self._resetAll(), self._resetAll()))

        wx.EVT_BUTTON(self.threedFrame, self.threedFrame.saveImageButton.GetId(),
                   self._handlerSaveImageButton)
        
        wx.EVT_CHOICE(self.threedFrame,
                   self.threedFrame.projectionChoiceId,
                   self._handlerProjectionChoice)

        wx.EVT_BUTTON(self.threedFrame,
                   self.threedFrame.introspectButton.GetId(),
                   self._handlerIntrospectButton)

        wx.EVT_BUTTON(self.threedFrame,
                   self.threedFrame.introspectPipelineButtonId,
                   lambda e, pw=self.threedFrame, s=self,
                   rw=self.threedFrame.threedRWI.GetRenderWindow():
                   s.vtkPipelineConfigure(pw, rw))

#         wx.EVT_BUTTON(self.threedFrame, self.threedFrame.resetButtonId,
#                    lambda e, s=self: s._resetAll())


        # event logic for the voi panel

        wx.EVT_CHECKBOX(self.controlFrame,
                     self.controlFrame.voiEnabledCheckBoxId,
                     self._handlerWidgetEnabledCheckBox)

        wx.EVT_CHOICE(self.controlFrame,
                   self.controlFrame.voiAutoSizeChoice.GetId(),
                   self._handlerVoiAutoSizeChoice)

        wx.EVT_BUTTON(self.controlFrame,
                   self.controlFrame.voiFilenameBrowseButton.GetId(),
                   self._handlerVoiFilenameBrowseButton)

        wx.EVT_BUTTON(self.controlFrame,
                   self.controlFrame.voiSaveButton.GetId(),
                   self._handlerVoiSaveButton)

        def _ps_cb():
            # FIXME: update to new factoring
            sliceDirection  = self.getCurrentSliceDirection()
            if sliceDirection:
                val = self.threedFrame.pushSliceSpinCtrl.GetValue()
                if val:
                    sliceDirection.pushSlice(val)
                    self.threedFrame.pushSliceSpinCtrl.SetValue(0)
                    self.threedFrame.threedRWI.Render()

        # clicks directly in the window for picking
        self.threedFrame.threedRWI.AddObserver('LeftButtonPressEvent',
                                               self._rwiLeftButtonCallback)


        # objectAnimationFrame creation and basic setup -------------------
        oaf = modules.viewers.resources.python.slice3dVWRFrames.\
              objectAnimationFrame
        self.objectAnimationFrame = module_utils.instantiateModuleViewFrame(
            self, self._module_manager, oaf)

        # display the windows (but we don't show the oaf yet)
        self.view()
        
        if os.name == 'posix':
            # yet another workaround for GTK1.2 on Linux (Debian 3.0)
            # if we don't do this, the renderer is far smaller than its
            # containing window and only corrects once the window is resized

            # also, this shouldn't really fix it, but it does:
            # then size that we set, is the "small" incorrect size
            # but somehow tickling GTK in this way makes everything better
            self.threedFrame.threedRWI.GetRenderWindow().SetSize(
                self.threedFrame.threedRWI.GetSize())
            self.threedFrame.threedRWI._Iren.ConfigureEvent()
            wx.SafeYield()

    def _set_annotated_cube_actor_labels(self, labels):
        aca = self._annotated_cube_actor
        aca.SetXMinusFaceText(labels[0])
        aca.SetXPlusFaceText(labels[1])
        aca.SetYMinusFaceText(labels[2])
        aca.SetYPlusFaceText(labels[3])
        aca.SetZMinusFaceText(labels[4])
        aca.SetZPlusFaceText(labels[5])

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

    def getWorldPositionInInputData(self, discretePos):
        if len(discretePos) < 3:
            return None
        
        inputData = self.getPrimaryInput()

        if inputData:
            ispacing = inputData.GetSpacing()
            iorigin = inputData.GetOrigin()
            # calculate real coords
            world = map(operator.add, iorigin,
                        map(operator.mul, ispacing, discretePos[0:3]))
            return world

        else:
            return None

    def getValuesAtDiscretePositionInInputData(self, discretePos):
        inputData = self.getPrimaryInput()

        if inputData == None:
            return

        # check that discretePos is in the input volume
        validPos = True
        extent = inputData.GetExtent()
        for d in range(3):
            if discretePos[d]< extent[d*2] or discretePos[d] > extent[d*2+1]:
                validPos = False
                break

        if validPos:
            nc = inputData.GetNumberOfScalarComponents()
            values = []
            for c in range(nc):
                values.append(inputData.GetScalarComponentAsDouble(
                    discretePos[0], discretePos[1], discretePos[2], c))
                
        else:
            values = None

        return values
            

    def getValueAtPositionInInputData(self, worldPosition):
        """Try and find out what the primary image data input value is at
        worldPosition.

        If there is no inputData, or the worldPosition is outside of the
        inputData, None is returned.
        """
        
        inputData = self.getPrimaryInput()

        if inputData:
            # then we have to update our internal record of this point
            ispacing = inputData.GetSpacing()
            iorigin = inputData.GetOrigin()
            discrete = map(
                round, map(
                operator.div,
                map(operator.sub, worldPosition, iorigin), ispacing))
                
            validPos = True
            extent = inputData.GetExtent()
            for d in range(3):
                if discrete[d]< extent[d*2] or discrete[d] > extent[d*2+1]:
                    validPos = False
                    break

            if validPos:
                # we rearch this else if the for loop completed normally
                val = inputData.GetScalarComponentAsDouble(discrete[0],
                                                           discrete[1],
                                                           discrete[2], 0)
            else:
                val = None

        else:
            discrete = (0,0,0)
            val = None

        return (val, discrete)
        

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

        # we only want to placewidget if this is the first time
        if self._voi_widget.NeedsPlacement:
            self._voi_widget.PlaceWidget()
            self._voi_widget.NeedsPlacement = False

        self._voi_widget.SetPriority(0.6)
        self._handlerWidgetEnabledCheckBox()

        self._threedRenderer.ResetCamera()

        # make sure the overlays follow  suit
        self.sliceDirections.resetAll()
        
        # whee, thaaaar she goes.
        self.render3D()

    def _save3DToImage(self, filename):
        self._module_manager.setProgress(0, "Writing PNG image...")
        w2i = vtk.vtkWindowToImageFilter()
        w2i.SetInput(self.threedFrame.threedRWI.GetRenderWindow())

        writer = vtk.vtkPNGWriter()
        writer.SetInput(w2i.GetOutput())
        writer.SetFileName(filename)
        writer.Write()
        self._module_manager.setProgress(100, "Writing PNG image... [DONE]")

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
                    self._threedRenderer.AddViewProp(self._pdScalarBarActor)

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
            self._threedRenderer.RemoveViewProp(self._pdScalarBarActor)
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

        val, discrete = self.getValueAtPositionInInputData(xyz)
        if val == None:
            discrete = (0,0,0)
            val = 0

        pointName = self.controlFrame.sliceCursorNameCombo.GetValue()
        self.selectedPoints._storePoint(
            discrete, xyz, val, pointName, True) # lock to surface

        
    #################################################################
    # callbacks
    #################################################################

    def _handlerVoiAutoSizeChoice(self, event):
        if self._voi_widget.GetEnabled():
            asc = self.controlFrame.voiAutoSizeChoice.GetSelection()

            if asc == 0: # bounding box of selected points
                swp = self.selectedPoints.getSelectedWorldPoints()

                if len(swp) > 0:
                    minxyz = list(swp[0])
                    maxxyz = list(swp[0])

                    # find max bounds of the selected points
                    for p in swp:
                        for i in range(3):
                            if p[i] < minxyz[i]:
                                minxyz[i] = p[i]

                            if p[i] > maxxyz[i]:
                                maxxyz[i] = p[i]

                    # now set bounds on VOI thingy
                    # first we zip up minxyz maxxyz to get minx, maxx, miny
                    # etc., then we use * to break this open into 6 args
                    self._voi_widget.SetPlaceFactor(1.0)
                    self._voi_widget.PlaceWidget(minxyz[0], maxxyz[0],
                                                 minxyz[1], maxxyz[1],
                                                 minxyz[2], maxxyz[2])

                    # make sure these changes are reflected in the VOI output
                    self.voiWidgetInteractionCallback(self._voi_widget, None)
                    self.voiWidgetEndInteractionCallback(self._voi_widget,
                                                         None)
                    
                    self.render3D()

                        
    def _handlerWidgetEnabledCheckBox(self, event=None):
        # event can be None
        if self._voi_widget.GetInput():
            if self.controlFrame.voiEnabledCheckBox.GetValue():
                self._voi_widget.On()
                self.voiWidgetInteractionCallback(self._voi_widget, None)
                self.voiWidgetEndInteractionCallback(self._voi_widget,
                                                         None)
                
            else:
                self._voi_widget.Off()

    def _handlerVoiFilenameBrowseButton(self, event):
        dlg = wx.FileDialog(self.controlFrame,
                           "Select VTI filename to write VOI to",
                           "", "", "*.vti", wx.SAVE)
        
        if dlg.ShowModal() == wx.ID_OK:
            self.controlFrame.voiFilenameText.SetValue(dlg.GetPath())
                     

    def _handlerVoiSaveButton(self, event):
        input_data = self.getPrimaryInput()
        filename = self.controlFrame.voiFilenameText.GetValue()
        if input_data and self._voi_widget.GetEnabled() and filename:
            # see if we need to reset to zero origin
            zor = self.controlFrame.voiResetToOriginCheck.GetValue()

            extractVOI = vtk.vtkExtractVOI()
            extractVOI.SetInput(input_data)
            extractVOI.SetVOI(self._currentVOI)

            writer = vtk.vtkXMLImageDataWriter()
            writer.SetDataModeToBinary()
            writer.SetFileName(filename)
            
            if zor:
                ici = vtk.vtkImageChangeInformation()
                ici.SetOutputExtentStart(0,0,0)
                ici.SetInput(extractVOI.GetOutput())
                writer.SetInput(ici.GetOutput())

            else:
                writer.SetInput(extractVOI.GetOutput())

            writer.Write()

    def _handlerIntrospectButton(self, event):
        """Open Python introspection window with this module as main object.
        """

        self.miscObjectConfigure(
            self.threedFrame, self,
            'slice3dVWR %s' % \
            (self._module_manager.get_instance_name(self),))
        

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

    def _handlerResetCamera(self, event):
        self._threedRenderer.ResetCamera()
        self.render3D()

    def _handlerSaveImageButton(self, event):
        # first get the filename
        # (if we don't specify the parent correctly, the DeVIDE main
        #  window pops up!)
        filename = wx.FileSelector(
            "Choose filename for PNG image",
            "", "", "png",
            "PNG files (*.png)|*.png|All files (*.*)|*.*",
            wx.SAVE,
            parent=self.threedFrame)
                    
        if filename:
            self._save3DToImage(filename)

    def _handlerShowControls(self, event):
        if not self.controlFrame.Show(True):
            self.controlFrame.Raise()


    def voiWidgetInteractionCallback(self, o, e):
        planes = vtk.vtkPlanes()
        o.GetPlanes(planes)
        bounds =  planes.GetPoints().GetBounds()

        # first set bounds
        self.controlFrame.voiBoundsText.SetValue(
            "(%.2f %.2f %.2f %.2f %.2f %.2f) mm" %
            bounds)

        input_data = self.getPrimaryInput()
        if input_data:
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
            self.controlFrame.voiExtentText.SetValue(
                "(%d %d %d %d %d %d)" % tuple(voi))

    def voiWidgetEndInteractionCallback(self, o, e):
        # adjust the vtkExtractVOI with the latest coords
        #self._extractVOI.SetVOI(self._currentVOI)
        pass

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
                    
                    

