from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
from wxPython.wx import *
import vtk

class testModule(moduleBase, noConfigModuleMixin):

    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)
        # initialise any mixins we might have
        noConfigModuleMixin.__init__(self)


        # we'll be playing around with some vtk objects, this could
        # be anything
        self._testObject0 = vtk.vtkTriangleFilter()
        self._testObject0b = vtk.vtkWindowedSincPolyDataFilter()
        self._testObject0b.SetInput(self._testObject0.GetOutput())
        self._testObject1 = vtk.vtkCurvatures()
        self._testObject1.SetCurvatureTypeToMean()
        self._testObject1.SetInput(self._testObject0.GetOutput())

        # following is the standard way of connecting up the dscas3 progress
        # callback to a VTK object; you should do this for all objects in
        # your module
        self._testObject1.SetProgressText('doing stuff...')
        mm = self._moduleManager
        self._testObject1.SetProgressMethod(lambda s=self, mm=mm:
                                            mm.vtk_progress_cb(
            s._testObject1))

        self._createViewFrame('Test Module View',
                              {'testObject1' :
                               self._testObject1})

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)
        # don't forget to call the close() method of the vtkPipeline mixin
        noConfigModuleMixin.close(self)
        # get rid of our reference
        del self._testObject1

    def getInputDescriptions(self):
	return ('vtkPolyData',)

    def setInput(self, idx, inputStream):
        self._testObject0.SetInput(inputStream)

    def getOutputDescriptions(self):
        return (self._testObject1.GetOutput().GetClassName(),)

    def getOutput(self, idx):
        return self._testObject1.GetOutput()

    def logicToConfig(self):
        pass

    def configToLogic(self):
        pass
    

    def viewToConfig(self):
        pass

    def configToView(self):
        pass
    

    def executeModule(self):
        self._testObject1.Update()


    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()
    
    
        
        
        
