# decimateFLT.py copyright (c) 2003 by Charl P. Botha http://cpbotha.net/
# $Id$
# module that triangulates and decimates polygonal input

import genUtils
from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtk
from module_kits.vtk_kit.mixins import VTKErrorFuncMixin

class decimate(scriptedConfigModuleMixin, moduleBase, VTKErrorFuncMixin):

    def __init__(self, moduleManager):

        # call parent constructor
        moduleBase.__init__(self, moduleManager)

        # the decimator only works on triangle data, so we make sure
        # that it only gets triangle data
        self._triFilter = vtk.vtkTriangleFilter()
        self._decimate = vtk.vtkDecimatePro()
        self._decimate.PreserveTopologyOn()
        self._decimate.SetInput(self._triFilter.GetOutput())

        moduleUtils.setupVTKObjectProgress(self, self._triFilter,
                                           'Converting to triangles')
        self.add_vtk_error_handler(self._triFilter)
        moduleUtils.setupVTKObjectProgress(self, self._decimate,
                                           'Decimating mesh')
        self.add_vtk_error_handler(self._decimate)
                                           
        # now setup some defaults before our sync
        self._config.target_reduction = self._decimate.GetTargetReduction() \
                                        * 100.0

        config_list = [
            ('Target reduction (%):', 'target_reduction', 'base:float', 'text',
             'Decimate algorithm will attempt to reduce by this much.')]
        scriptedConfigModuleMixin.__init__(self, config_list)

        self._viewFrame = self._createWindow(
            {'Module (self)' : self,
             'vtkDecimatePro' : self._decimate,
             'vtkTriangleFilter' : self._triFilter})

        # pass the data down to the underlying logic
        self.configToLogic()
        # and all the way up from logic -> config -> view to make sure
        self.logicToConfig()
        self.configToView()
        
    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        self.setInput(0, None)

        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)

        moduleBase.close(self)

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
        self._config.target_reduction = self._decimate.GetTargetReduction() \
                                        * 100.0

    def configToLogic(self):
        self._decimate.SetTargetReduction(
            self._config.target_reduction / 100.0)

    def executeModule(self):
        # get the filter doing its thing
        self._triFilter.Update()
        self.check_vtk_error()
        self._decimate.Update()
        self.check_vtk_error()

