# $Id$

import itk
from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
import vtk

class ITKUL3toVTK(noConfigModuleMixin, moduleBase):
    """Convert ITK 3D unsigned long data to VTK.

    $Revision: 1.3 $
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
        # due to event-driven vs. demand-driven issues, we have to make
        # sure in this converter that ALL data goes through.  if we don't
        # segfault fun ensues.
        #o = self._vtkImporter.GetOutput()
        #o.UpdateInformation()
        #o.SetUpdateExtentToWholeExtent()
        #o.Update()

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


        
            
