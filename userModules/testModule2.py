from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
from wxPython.wx import *
import vtk

class testModule2(moduleBase, noConfigModuleMixin):
    """Incomplete super-sampler.

    This super-samples an input volume by making use of a
    vtkImageReslice class.  It's incomplete because the output spacing
    is not adapted whilst the extent is, thus resulting in a
    physically larger volume.
    """

    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)
        # initialise any mixins we might have
        noConfigModuleMixin.__init__(self)


        # we'll be playing around with some vtk objects, this could
        # be anything
        self._testObject0 = vtk.vtkImageResample()
        self._testObject0.SetInterpolationModeToCubic()
        self._testObject0.SetAxisMagnificationFactor(0, 2)
        self._testObject0.SetAxisMagnificationFactor(1, 2)
        self._testObject0.SetAxisMagnificationFactor(2, 2)
        # following is the standard way of connecting up the devide progress
        # callback to a VTK object; you should do this for all objects in
        # your module
        self._testObject0.SetProgressText('doing stuff...')
        mm = self._moduleManager
        self._testObject0.SetProgressMethod(lambda s=self, mm=mm:
                                            mm.vtk_progress_cb(
            s._testObject0))

        self._viewFrame = self._createViewFrame('Test Module View',
                                                {'testObject0' :
                                                 self._testObject0})

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)
        # don't forget to call the close() method of the vtkPipeline mixin
        noConfigModuleMixin.close(self)
        # get rid of our reference
        del self._testObject0

    def getInputDescriptions(self):
	return ('vtkImageData',)

    def setInput(self, idx, inputStream):
        self._testObject0.SetInput(inputStream)

    def getOutputDescriptions(self):
        return (self._testObject0.GetOutput().GetClassName(),)

    def getOutput(self, idx):
        return self._testObject0.GetOutput()

    def logicToConfig(self):
        pass

    def configToLogic(self):
        pass
    

    def viewToConfig(self):
        pass

    def configToView(self):
        pass
    

    def executeModule(self):
        self._testObject0.Update()


    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()
    
    
        
        
        
