from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
from wxPython.wx import *
import vtk

class testModule3(moduleBase, noConfigModuleMixin):

    """Module to prototype modification of homotopy and subsequent
    watershedding of curvature-on-surface image.
    """

    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)
        # initialise any mixins we might have
        noConfigModuleMixin.__init__(self)

        self._tf = vtk.vtkTriangleFilter()
        self._curvatures = vtk.vtkCurvatures()
        self._curvatures.SetCurvatureTypeToMean()        
        self._curvatures.SetInput(self._tf.GetOutput())

        mm = self._moduleManager
        self._tf.SetProgressText('triangulating')
        self._tf.SetProgressMethod(lambda s=self, mm=mm:
                                   mm.vtk_progress_cb(s._tf))

        self._curvatures.SetProgressText('calculating curvatures')
        self._curvatures.SetProgressMethod(lambda s=self, mm=mm:
                                           mm.vtk_progress_cb(s._curvatures))
        

        self._createViewFrame('Test Module View',
                              {'vtkTriangleFilter' : self._tf,
                               'vtkCurvatures' : self._curvatures})

        self._viewFrame.Show(True)

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)
        # don't forget to call the close() method of the vtkPipeline mixin
        noConfigModuleMixin.close(self)
        # get rid of our reference
        del self._curvatures
        del self._tf

    def getInputDescriptions(self):
	return ('vtkPolyData',)

    def setInput(self, idx, inputStream):
        self._tf.SetInput(inputStream)

    def getOutputDescriptions(self):
        return ()

    def getOutput(self, idx):
        return None

    def logicToConfig(self):
        pass

    def configToLogic(self):
        pass

    def viewToConfig(self):
        pass

    def configToView(self):
        pass
    

    def executeModule(self):
        if self._tf.GetInput():
            self._curvatures.Update()

            #


    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()
    
    
        
        
        
