# decimateFLT.py copyright (c) 2003 by Charl P. Botha http://cpbotha.net/
# $Id: decimate.py,v 1.2 2003/09/20 22:22:34 cpbotha Exp $
# module that triangulates and decimates polygonal input

import genUtils
from moduleBase import moduleBase
from moduleMixins import vtkPipelineConfigModuleMixin
import moduleUtils
from wxPython.wx import *
import vtk

class decimate(moduleBase, vtkPipelineConfigModuleMixin):

    def __init__(self, moduleManager):

        # call parent constructor
        moduleBase.__init__(self, moduleManager)

        # the decimator only works on triangle data, so we make sure
        # that it only gets triangle data
        self._triFilter = vtk.vtkTriangleFilter()
        self._decimate = vtk.vtkDecimate()
        self._decimate.PreserveTopologyOn()
        self._decimate.SetInput(self._triFilter.GetOutput())

        moduleUtils.setupVTKObjectProgress(self, self._triFilter,
                                           'Converting to triangles')
        moduleUtils.setupVTKObjectProgress(self, self._decimate,
                                           'Decimating mesh')
                                           
        # now setup some defaults before our sync
        self._config.targetReduction = self._decimate.GetTargetReduction()

        self._viewFrame = None
        self._createViewFrame()

        # transfer these defaults to the logic
        self.configToLogic()

        # then make sure they come all the way back up via self._config
        self.syncViewWithLogic()
        
    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        self.setInput(0, None)
        # don't forget to call the close() method of the vtkPipeline mixin
        vtkPipelineConfigModuleMixin.close(self)
        # take out our view interface
        self._viewFrame.Destroy()
        # get rid of our reference
        del self._decimate
        del self._triFilter

    def getInputDescriptions(self):
	return ('vtkPolyData',)
    
    def setInput(self, idx, inputStream):
        self._triFilter.SetInput(inputStream)
    
    def getOutputDescriptions(self):
	return (self._decimate.GetOutput().GetClassName(),)
    
    def getOutput(self, idx):
        return self._decimate.GetOutput()

    def logicToConfig(self):
        self._config.targetReduction = self._decimate.GetTargetReduction()

    def configToLogic(self):
        self._decimate.SetTargetReduction(self._config.targetReduction)

    def viewToConfig(self):
        f = genUtils.textToFloat(self._viewFrame.targetReductionText.\
                                 GetValue(), self._config.targetReduction)
        self._config.targetReduction = f / 100.0

    def configToView(self):
        self._viewFrame.targetReductionText.SetValue(
            '%.2f' % (self._config.targetReduction * 100.0,))

    def executeModule(self):
        # get the filter doing its thing
        self._decimate.Update()

    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()

    def _createViewFrame(self):

        # import the viewFrame (created with wxGlade)
        import modules.Filters.resources.python.decimateFLTViewFrame
        reload(modules.Filters.resources.python.decimateFLTViewFrame)

        self._viewFrame = moduleUtils.instantiateModuleViewFrame(
            self, self._moduleManager,
            modules.Filters.resources.python.decimateFLTViewFrame.\
            decimateFLTViewFrame)

        objectDict = {'triangle filter' : self._triFilter,
                      'decimator' : self._decimate}
        moduleUtils.createStandardObjectAndPipelineIntrospection(
            self, self._viewFrame, self._viewFrame.viewFramePanel,
            objectDict, None)

        moduleUtils.createECASButtons(self, self._viewFrame,
                                      self._viewFrame.viewFramePanel)
