# $Id$

import itk
import genUtils
from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
import vtk

class ITKUS3toVTK(noConfigModuleMixin, moduleBase):
    """Convert ITK 3D unsigned short data to VTK.

    $Revision: 1.2 $
    """

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)
        noConfigModuleMixin.__init__(self)

        self._itk2vtk = itk.ImageToVTKImageFilter[itk.Image[itk.UL, 3]].New()

        self._viewFrame = self._createViewFrame(
            {'Module (self)' : self,
             'ImageToVTKImageFilter' : self._itk2vtk})

        self.configToLogic()
        self.logicToConfig()
        self.configToView()


    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)

        # this will take care of all display thingies
        noConfigModuleMixin.close(self)

        moduleBase.close(self)

        del self._itk2vtk

    def executeModule(self):
        self._itk2vtk.Update()

    def getInputDescriptions(self):
        return ('ITK Image (3D, float)',)        

    def setInput(self, idx, inputStream):
        self._itk2vtk.SetInput(inputStream)

    def getOutputDescriptions(self):
        return ('VTK Image Data',)

    def getOutput(self, idx):
        return self._itk2vtk.GetOutput()

    def logicToConfig(self):
        pass
    
    def configToLogic(self):
        pass
    
    def viewToConfig(self):
        pass

    def configToView(self):
        pass

        
            
