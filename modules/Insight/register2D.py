# $Id: register2D.py,v 1.14 2004/12/05 00:42:42 cpbotha Exp $

# TODO:
# * if the input imageStackRDR is reconfigured to read a different stack
#   by the user, then things will break.  We probably have to add an observer
#   and adapt to the new situation.
# * ditto for the input transformStackRDR
# * an observer which internally disconnects in the case of a screwup would
#   be good enough; the user can be warned that he should reconnect

import genUtils
from typeModules.imageStackClass import imageStackClass
from typeModules.transformStackClass import transformStackClass
from moduleBase import moduleBase
import moduleUtils
import operator
import fixitk as itk
import ConnectVTKITKPython as CVIPy
import vtk
import wx

class register2D(moduleBase):
    """Registers a stack of 2D images and generates a list of transforms.

    This is BAD-ASSED CODE(tm) and can crash the whole of DeVIDE without
    even saying sorry afterwards.  You have been warned.
    """

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        self._createLogic()
        self._createViewFrames()
        self._bindEvents()

        # FIXME: add current transforms to config stuff

    def close(self):
        # we do this just in case...
        self.setInput(0, None)
        self.setInput(1, None)
        
        moduleBase.close(self)

        # take care of the IPWs
        self._destroyIPWs()

        # take care of pipeline thingies
        del self._rescaler1
        del self._itkExporter1
        del self._vtkImporter1

        del self._resampler2
        del self._rescaler2
        del self._itkExporter2
        del self._vtkImporter2

        # also take care of our output!
        del self._transformStack

        # nasty trick to take care of RenderWindow
        self._threedRenderer.RemoveAllProps()
        del self._threedRenderer
        self.viewerFrame.threedRWI.GetRenderWindow().WindowRemap()
        self.viewerFrame.Destroy()
        del self.viewerFrame
        
        # then do the controlFrame
        self.controlFrame.Destroy()
        del self.controlFrame

    def getInputDescriptions(self):
        return ('ITK Image Stack', '2D Transform Stack')

    def setInput(self, idx, inputStream):
        if idx == 0:
            if inputStream != self._imageStack:
                # if it's None, we have to take it
                if inputStream == None:
                    # disconnect
                    del self._transformStack[:]
                    self._destroyIPWs()
                    self._imageStack = None
                    self._pairNumber = -1
                    return

                # let's setup for a new stack!
                try:
                    assert(inputStream.__class__.__name__ == 'imageStackClass')
                    inputStream.Update()
                    assert(len(inputStream) >= 2)
                except Exception:
                    # if the Update call doesn't work or
                    # if the input list is not long enough (or unsizable),
                    # we don't do anything
                    raise TypeError, \
                          "register2D requires an ITK Image Stack of minimum length 2 as input."

                # now check that the imageStack is the same size as the
                # transformStack
                if self._inputTransformStack and \
                   len(inputStream) != len(self._inputTransformStack):
                    raise TypeError, \
                          "The Image Stack you are trying to connect has a\n" \
                          "different length than the connected Transform\n" \
                          "Stack."

                self._imageStack = inputStream

                if self._inputTransformStack:
                    self._copyInputTransformStack()
                else:
                    # create a new transformStack
                    del self._transformStack[:]
                    # the first transform is always identity
                    for dummy in self._imageStack:
                        self._transformStack.append(
                            itk.itkEuler2DTransform_New())
                        self._transformStack[-1].SetIdentity()

                self._showImagePair(1)

        else: # closes if idx == 0 block
            if inputStream != self._inputTransformStack:
                if inputStream == None:
                    # we disconnect, but we keep the transforms we have
                    self._inputTransformStack = None
                    return

                try:
                    assert(inputStream.__class__.__name__ == \
                           'transformStackClass')
                except Exception:
                    raise TypeError, \
                          "register2D requires an ITK Transform Stack on " \
                          "this port."

                inputStream.Update()

                if len(inputStream) < 2:
                    raise TypeError, \
                          "The input transform stack should be of minimum " \
                          "length 2."
                    
                if self._imageStack and \
                   len(inputStream) != len(self._imageStack):
                    raise TypeError, \
                          "The Transform Stack you are trying to connect\n" \
                          "has a different length than the connected\n" \
                          "Transform Stack"

                self._inputTransformStack = inputStream

                if self._imageStack:
                    self._copyInputTransformStack()
                    self._showImagePair(self._pairNumber)
                          
        
    def getOutputDescriptions(self):
        return ('2D Transform Stack',)

    def getOutput(self, idx):
        return self._transformStack

    def executeModule(self):
        pass

    def view(self, parent_window=None):
        # if the window is already visible, raise it
        if not self.viewerFrame.Show(True):
            self.viewerFrame.Raise()

        if not self.controlFrame.Show(True):
            self.controlFrame.Raise()

    # ----------------------------------------------------------------------
    # non-API methods start here -------------------------------------------
    # ----------------------------------------------------------------------

    def _bindEvents(self):
        wx.EVT_BUTTON(self.viewerFrame, self.viewerFrame.showControlsButtonId,
                      self._handlerShowControls)
        wx.EVT_BUTTON(self.viewerFrame, self.viewerFrame.resetCameraButtonId,
                      lambda e: self._resetCamera())

        wx.EVT_SPINCTRL(self.controlFrame,
                        self.controlFrame.pairNumberSpinCtrlId,
                        self._handlerPairNumberSpinCtrl)
        wx.EVT_BUTTON(self.controlFrame, self.controlFrame.transformButtonId,
                      self._handlerTransformButton)
        wx.EVT_BUTTON(self.controlFrame, self.controlFrame.registerButtonId,
                      self._handlerRegisterButton)

    def _copyInputTransformStack(self):
        """Copy the contents of the inputTransformStack to the internal
        transform stack.
        """

        # take care of the current ones
        del self._transformStack[:]
        # then copy
        for trfm in self._inputTransformStack:
            # FIXME: do we need to take out a ref?
            self._transformStack.append(trfm)

    def _createLogic(self):
        # input
        self._imageStack = None
        # optional input
        self._inputTransformStack = None
        # output is a transform stack
        self._transformStack = transformStackClass(self)

        self._ipw1 = None
        self._ipw2 = None

        # some control variables
        self._pairNumber = -1
        
        # we need to have two converters from itk::Image to vtkImageData,
        # hmmmm kay?
        self._transform1 = itk.itkEuler2DTransform_New()
        self._transform1.SetIdentity()
        print self._transform1.GetParameters()


        self._rescaler1 = itk.itkRescaleIntensityImageFilterF2F2_New()
        self._rescaler1.SetOutputMinimum(0)
        self._rescaler1.SetOutputMaximum(255)
        self._itkExporter1 = itk.itkVTKImageExportF2_New()
        self._itkExporter1.SetInput(self._rescaler1.GetOutput())
        self._vtkImporter1 = vtk.vtkImageImport()
        CVIPy.ConnectITKF2ToVTK(self._itkExporter1.GetPointer(),
                                self._vtkImporter1)

        self._resampler2 = None

        self._rescaler2 = itk.itkRescaleIntensityImageFilterF2F2_New()
        self._rescaler2.SetOutputMinimum(0)
        self._rescaler2.SetOutputMaximum(255)
        self._itkExporter2 = itk.itkVTKImageExportF2_New()
        self._itkExporter2.SetInput(self._rescaler2.GetOutput())
        self._vtkImporter2 = vtk.vtkImageImport()
        CVIPy.ConnectITKF2ToVTK(self._itkExporter2.GetPointer(),
                                self._vtkImporter2)
        
    
    def _createViewFrames(self):
        import modules.Insight.resources.python.register2DViewFrames
        reload(modules.Insight.resources.python.register2DViewFrames)

        viewerFrame = modules.Insight.resources.python.register2DViewFrames.\
                      viewerFrame
        self.viewerFrame = moduleUtils.instantiateModuleViewFrame(
            self, self._moduleManager, viewerFrame)

        self._threedRenderer = vtk.vtkRenderer()
        self._threedRenderer.SetBackground(0.5, 0.5, 0.5)
        self.viewerFrame.threedRWI.GetRenderWindow().AddRenderer(
            self._threedRenderer)

        istyle = vtk.vtkInteractorStyleImage()
        self.viewerFrame.threedRWI.SetInteractorStyle(istyle)
        

        

        # controlFrame creation
        controlFrame = modules.Insight.resources.python.\
                       register2DViewFrames.controlFrame
        self.controlFrame = moduleUtils.instantiateModuleViewFrame(
            self, self._moduleManager, controlFrame)

        # display
        self.viewerFrame.Show(True)
        self.controlFrame.Show(True)

    def _createIPWs(self):
        self._ipw1 = vtk.vtkImagePlaneWidget()
        self._ipw2 = vtk.vtkImagePlaneWidget()
        
        for ipw, vtkImporter in ((self._ipw1, self._vtkImporter1),
                                 (self._ipw2, self._vtkImporter2)):
            vtkImporter.Update()
            ipw.SetInput(vtkImporter.GetOutput())
            ipw.SetPlaneOrientation(2)        
            ipw.SetInteractor(self.viewerFrame.threedRWI)
            ipw.On()
            ipw.InteractionOff()            

        self._setModeRedGreen()
            
    def _destroyIPWs(self):
        """If the two IPWs exist, remove them completely and remove all
        bindings that we have.
        """

        for ipw in (self._ipw1, self._ipw2):
            if ipw:
                # switch off
                ipw.Off()
                # disconnect from interactor
                ipw.SetInteractor(None)
                # disconnect from its input
                ipw.SetInput(None)

        self._ipw1 = None
        self._ipw2 = None

    def _handlerPairNumberSpinCtrl(self, event):
        self._showImagePair(self.controlFrame.pairNumberSpinCtrl.GetValue())

    def _handlerRegisterButton(self, event):
        maxIterations = genUtils.textToFloat(
            self.controlFrame.maxIterationsTextCtrl.GetValue(), 50)
        if not maxIterations > 0:
            maxIterations = 50
            
        self._registerCurrentPair(maxIterations)
        
        self.controlFrame.maxIterationsTextCtrl.SetValue(str(maxIterations))

    def _handlerShowControls(self, event):
        # make sure the window is visible and raised
        self.controlFrame.Show(True)
        self.controlFrame.Raise()

    def _handlerTransformButton(self, event):
        # take xtranslate, ytranslate, rotate and work it into the current
        # transform (if that exists)
        if self._pairNumber > 0:
            pda = self._transformStack[self._pairNumber].GetParameters()
            
            rot = genUtils.textToFloat(
                self.controlFrame.rotationTextCtrl.GetValue(),
                pda.GetElement(0))
            xt = genUtils.textToFloat(
                self.controlFrame.xTranslationTextCtrl.GetValue(),
                pda.GetElement(1))
            yt = genUtils.textToFloat(
                self.controlFrame.yTranslationTextCtrl.GetValue(),
                pda.GetElement(2))

            pda.SetElement(0, rot)
            pda.SetElement(1, xt)
            pda.SetElement(2, yt)

            self._transformStack[self._pairNumber].SetParameters(pda)
            # we have to do this manually
            self._transformStack[self._pairNumber].Modified()

            self._rescaler2.Update() # give ITK a chance to complain
            self.viewerFrame.threedRWI.GetRenderWindow().Render()

    def _registerCurrentPair(self, maxIterations):
        if not self._pairNumber > 0:
            # no data, return
            return
        
        currentTransform = self._transformStack[self._pairNumber]
        fixedImage = self._imageStack[self._pairNumber - 1]
        movingImage = self._imageStack[self._pairNumber]
        
        registration = itk.itkImageRegistrationMethodF2F2_New()
        # sum of squared differences
        imageMetric = itk.itkMeanSquaresImageToImageMetricF2F2_New()
        #imageMetric = itk.itkNormalizedCorrelationImageToImageMetricF2F2_New()
        optimizer = itk.itkRegularStepGradientDescentOptimizer_New()
        #optimizer = itk.itkConjugateGradientOptimizer_New()
        interpolator = itk.itkLinearInterpolateImageFunctionF2D_New()

        registration.SetOptimizer(optimizer.GetPointer())
        registration.SetTransform(currentTransform.GetPointer()    )
        registration.SetInterpolator(interpolator.GetPointer())
        registration.SetMetric(imageMetric.GetPointer())
        registration.SetFixedImage(fixedImage)
        registration.SetMovingImage(movingImage)

        registration.SetFixedImageRegion(fixedImage.GetBufferedRegion())

        initialParameters = currentTransform.GetParameters()
        registration.SetInitialTransformParameters( initialParameters )

        #
        #  Define optimizer parameters
        #
        optimizer.SetMaximumStepLength(  1 )
        optimizer.SetMinimumStepLength(  0.01 )
        optimizer.SetNumberOfIterations( maxIterations  )

        # velly impoltant: the scales
        # the larger a scale, the smaller the impact of that parameter on
        # the calculated gradient
        scalesDA = itk.itkArrayD(3)
        scalesDA.SetElement(0, 1e-01)
        scalesDA.SetElement(1, 1e-05)
        scalesDA.SetElement(2, 1e-05)
        optimizer.SetScales(scalesDA)

        #
        #  Start the registration process
        #

        def iterationEvent():
            pm = "register2D optimizer value: %f stepsize: %f" % \
                 (optimizer.GetValue(),
                  optimizer.GetCurrentStepLength())

            p = (optimizer.GetCurrentIteration() + 1) / maxIterations * 100.0
            self._moduleManager.setProgress(p, pm)

        pc2 = itk.itkPyCommand_New()
        pc2.SetCommandCallable(iterationEvent)
        optimizer.AddObserver(itk.itkIterationEvent(),
                              pc2.GetPointer())

        # FIXME: if this throws an exception, reset  transform!
        registration.StartRegistration()

        fpm = 'register2D registration done (final value: %0.2f).' % \
              optimizer.GetValue()
        self._moduleManager.setProgress(100.0, fpm)

        print registration.GetLastTransformParameters().GetElement(0)
        print registration.GetLastTransformParameters().GetElement(1)
        print registration.GetLastTransformParameters().GetElement(2)        
        
        self._syncGUIToCurrentPair()
        
        currentTransform.Modified()
        self._rescaler2.Update() # give ITK a chance to complain
        self.viewerFrame.threedRWI.GetRenderWindow().Render()
        

    def _resetCamera(self):
        """If an IPW is available (i.e. there's some data), this method
        will setup the camera to be nice and orthogonal to the IPW.
        """
        if self._ipw1:
            planeSource = self._ipw1.GetPolyDataSource()
            cam = self._threedRenderer.GetActiveCamera()
            cam.SetPosition(planeSource.GetCenter()[0],
                            planeSource.GetCenter()[1], 10)
            cam.SetFocalPoint(planeSource.GetCenter())
            cam.OrthogonalizeViewUp()
            cam.SetViewUp(0,1,0)
            cam.SetClippingRange(1, 11)
            v2 = map(operator.sub, planeSource.GetPoint2(),
                     planeSource.GetOrigin())
            n2 = vtk.vtkMath.Normalize(v2)
            cam.SetParallelScale(n2 / 2.0)
            cam.ParallelProjectionOn()

            self.viewerFrame.threedRWI.GetRenderWindow().Render()

    def _setModeCheckerboard(self):
        pass
        
    def _setModeRedGreen(self):
        """Set visualisation mode to RedGreen.

        The second image is always green.
        """

        #for ipw, col in ((self._ipw1, 0.0), (self._ipw2, 0.3)):
        for ipw, col in ((self._ipw2, 0.3),):        
            inputData = ipw.GetInput()
            inputData.Update() # make sure the metadata is up to date
            minv, maxv = inputData.GetScalarRange()
            lut = vtk.vtkLookupTable()
            lut.SetTableRange((minv, maxv))
            lut.SetHueRange((col, col)) # keep it green!
            lut.SetSaturationRange((1.0, 1.0))
            lut.SetValueRange((0.0, 1.0))
            lut.SetAlphaRange((0.5, 0.5))
            lut.Build()
            ipw.SetLookupTable(lut)
        
    def _showImagePair(self, pairNumber):
        """Set everything up to have the user interact with image pair
        pairNumber.

        pairNumber is 1 based, i.e. pairNumber 1 implies the registration
        between image 1 and image 0.
        """

        # FIXME: do sanity checking on pairNumber
        self._pairNumber = pairNumber

        # connect up ITK pipelines with the correct images and transforms
        fixedImage = self._imageStack[pairNumber - 1]
        self._rescaler1.SetInput(fixedImage)
        self._rescaler1.Update() # give ITK a chance to complain...

        self._resampler2 = itk.itkResampleImageFilterF2F2_New()

        self._resampler2.SetTransform(
            self._transformStack[pairNumber].GetPointer())
        self._resampler2.SetInput(self._imageStack[pairNumber])
        region = fixedImage.GetLargestPossibleRegion()
        self._resampler2.SetSize(region.GetSize())
        self._resampler2.SetOutputSpacing(fixedImage.GetSpacing())
        self._resampler2.SetOutputOrigin(fixedImage.GetOrigin())
        self._resampler2.SetDefaultPixelValue(0)
        
        self._rescaler2.SetInput(self._resampler2.GetOutput())
        self._rescaler2.Update() # give ITK a chance to complain...


        self._syncGUIToCurrentPair()
        
        # we're going to create new ones, so take care of the old ones
        self._destroyIPWs()
        
        self._createIPWs()

        self._resetCamera()

    def _syncGUIToCurrentPair(self):
        # update GUI #####################################################
        self.controlFrame.pairNumberSpinCtrl.SetRange(1,
                                                      len(self._imageStack)-1)
        self.controlFrame.pairNumberSpinCtrl.SetValue(self._pairNumber)

        pda = self._transformStack[self._pairNumber].GetParameters()
        self.controlFrame.rotationTextCtrl.SetValue(
            '%.8f' % (pda.GetElement(0),))
        self.controlFrame.xTranslationTextCtrl.SetValue(
            '%.8f' % (pda.GetElement(1),))
        self.controlFrame.yTranslationTextCtrl.SetValue(
            '%.8f' % (pda.GetElement(2),))

        # default
        self.controlFrame.maxIterationsTextCtrl.SetValue('50')
        
