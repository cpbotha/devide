from genMixins import subjectMixin, updateCallsExecuteModuleMixin
from moduleBase import moduleBase
import moduleUtils
import InsightToolkit as itk
import ConnectVTKITKPython as CVIPy
import vtk
import wx

class transformStackClass(list,
                          subjectMixin,
                          updateCallsExecuteModuleMixin):
    
    def __init__(self, d3Module):
        # call base ctors
        subjectMixin.__init__(self)
        updateCallsExecuteModuleMixin.__init__(self, d3Module)

    def close(self):
        subjectMixin.close(self)
        updateCallsExecuteModuleMixin.close(self)

class register2D(moduleBase):
    """Registers a stack of 2D images and generates a list of transforms.

    This is BAD-ASSED CODE(tm) and can crash the whole of DSCAS3 without
    even saying sorry afterwards.  You have been warned.
    """

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        # input
        self._imageStack = None
        # output is a transform stack
        self._transformStack = transformStackClass(self)

        self._createViewFrames()
        self._bindEvents()

        # FIXME: add current transforms to config stuff

    def close(self):
        moduleBase.close(self)

        # take care of pipeline thingies
        del self._itkExporter1
        del self._vtkImporter1

        del self._itkExporter2
        del self._vtkImporter2

        del self._imageViewer
        # nasty trick to take care of RenderWindow        
        self.viewerFrame.threedRWI.GetRenderWindow().WindowRemap()
        self.viewerFrame.Destroy()
        del self.viewerFrame

        self.controlFrame.Destroy()
        del self.controlFrame

    def getInputDescriptions(self):
        return ('ITK Image Stack',)

    def setInput(self, idx, inputStream):
        # FIXME: also check for correct type!
        if inputStream != self._imageStack:
            # let's setup for a new stack!
            self._imageStack = inputStream
            self._showImagePair(1)
        
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
        pass
    
    def _createViewFrames(self):
        import modules.Insight.resources.python.register2DViewFrames
        reload(modules.Insight.resources.python.register2DViewFrames)

        viewerFrame = modules.Insight.resources.python.register2DViewFrames.\
                      viewerFrame
        self.viewerFrame = moduleUtils.instantiateModuleViewFrame(
            self, self._moduleManager, viewerFrame)

        # we need to have two converters from itk::Image to vtkImageData,
        # hmmmm kay?

        self._itkExporter1 = itk.itkVTKImageExportF2_New()
        self._vtkImporter1 = vtk.vtkImageImport()
        CVIPy.ConnectITKF2ToVTK(self._itkExporter1.GetPointer(),
                                self._vtkImporter1)
        
        self._itkExporter2 = itk.itkVTKImageExportF2_New()
        self._vtkImporter2 = vtk.vtkImageImport()
        CVIPy.ConnectITKF2ToVTK(self._itkExporter2.GetPointer(),
                                self._vtkImporter2)
        

        self._imageViewer = vtk.vtkImageViewer()
        self._imageViewer.SetupInteractor(self.viewerFrame.threedRWI)

        # controlFrame creation
        controlFrame = modules.Insight.resources.python.\
                       register2DViewFrames.controlFrame
        self.controlFrame = moduleUtils.instantiateModuleViewFrame(
            self, self._moduleManager, controlFrame)

        # display
        self.viewerFrame.Show(True)
        self.controlFrame.Show(True)
        
    def _showImagePair(self, pairNumber):
        """Set everything up to have the user interact with image pair
        pairNumber.

        pairNumber is 1 based, i.e. pairNumber 1 implies the registration
        between image 1 and image 0.
        """


        try:
            self._imageStack.Update()
            assert(len(self._imageStack) >= 2)
        except Exception:
            # if the Update call doesn't work or
            # if the input list is not long enough (or unsizable),
            # we don't do anything
            return
        

        print "e1 setinput"
        print self._imageStack[0]
        self._itkExporter1.SetInput(self._imageStack[0])
        print "e1 update"
        self._itkExporter1.Update() # give ITK a chance to complain...
        print "e2 setinput"
        self._itkExporter2.SetInput(self._imageStack[1])
        print "e2 update"
        self._itkExporter2.Update() # give ITK a chance to complain...        

        checker = vtk.vtkImageCheckerboard()
        checker.SetNumberOfDivisions(10, 10, 1)
        checker.SetInput1(self._vtkImporter1.GetOutput())
        checker.SetInput2(self._vtkImporter2.GetOutput())

        self._imageViewer.SetInput(self._vtkImporter1.GetOutput())

        self._imageViewer.GetRenderWindow().Render()
