from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
from wxPython.wx import *
import vtk

class testModule2(moduleBase, noConfigModuleMixin):

    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)
        # initialise any mixins we might have
        noConfigModuleMixin.__init__(self)


        # we'll be playing around with some vtk objects, this could
        # be anything
        self._testObject0 = vtk.vtkImageReslice()
        self._testObject0.SetInterpolationModeToCubic()
        self._testObject0.SetResliceAxesDirectionCosines(
            0.5, 0, 0,
            0, 0.5, 0,
            0, 0, 0.5)

        # following is the standard way of connecting up the dscas3 progress
        # callback to a VTK object; you should do this for all objects in
        # your module
        self._testObject0.SetProgressText('doing stuff...')
        mm = self._moduleManager
        self._testObject0.SetProgressMethod(lambda s=self, mm=mm:
                                            mm.vtk_progress_cb(
            s._testObject0))

        self._createViewFrame('Test Module View',
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
    
    
        
        
        
