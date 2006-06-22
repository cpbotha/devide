# $Id$

import itk
from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
import vtk

class VTKtoITKF3(noConfigModuleMixin, moduleBase):

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)
        noConfigModuleMixin.__init__(self)

        # setup the pipeline
        self._imageCast = vtk.vtkImageCast()
        self._imageCast.SetOutputScalarTypeToFloat()

        self._vtk2itk = itk.VTKImageToImageFilter[itk.Image[itk.F, 3]].New()
        self._vtk2itk.SetInput(self._imageCast.GetOutput())

        self._viewFrame = self._createViewFrame(
            {'Module (self)' : self,
             'vtkImageCast' : self._imageCast,
             'VTKImageToImageFilter' : self._vtk2itk})

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

        del self._imageCast
        del self._vtk2itk

    def executeModule(self):
        # the whole connectvtkitk thingy is quite shaky and was really
        # designed for demand-driven use.  using it in an event-driven
        # environment, we have to make sure it does exactly what we want
        # it to do.  one day, we'll implement contracts and do this
        # differently.

        #o = self._itkImporter.GetOutput()
        #o.UpdateOutputInformation()
        #o.SetRequestedRegionToLargestPossibleRegion()
        #o.Update()

        self._vtk2itk.Update()

    def getInputDescriptions(self):
        return ('VTK Image Data',)

    def setInput(self, idx, inputStream):
        self._imageCast.SetInput(inputStream)

    def getOutputDescriptions(self):
        return ('ITK Image (3D, float)',)

    def getOutput(self, idx):
        return self._vtk2itk.GetOutput()

    def logicToConfig(self):
        pass
    
    def configToLogic(self):
        pass
    
    def viewToConfig(self):
        pass

    def configToView(self):
        pass
    

        
            
