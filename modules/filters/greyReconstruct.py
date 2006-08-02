import genUtils
from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
import moduleUtils
import wx
import vtk
import vtkdevide


class greyReconstruct(noConfigModuleMixin, moduleBase):
    """
    Performs grey value reconstruction of mask I from marker J.

    Theoretically, marker J is dilated and the infimum with mask I is
    determined.  This infimum now takes the place of J.  This process is
    repeated until stability.

    This module uses a DeVIDE specific implementation of Luc Vincent's fast
    hybrid algorithm for greyscale reconstruction.

    $Revision: 1.2 $
    """

    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)
        noConfigModuleMixin.__init__(self)

        self._greyReconstruct = vtkdevide.vtkImageGreyscaleReconstruct3D()
        
        moduleUtils.setupVTKObjectProgress(
            self, self._greyReconstruct,
            'Performing greyscale reconstruction')
        

        self._viewFrame = self._createViewFrame(
            {'Module (self)' : self,
             'vtkImageGreyscaleReconstruct3D' : self._greyReconstruct})

        # pass the data down to the underlying logic
        self.configToLogic()
        # and all the way up from logic -> config -> view to make sure
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
        
        # get rid of our reference
        del self._greyReconstruct

    def getInputDescriptions(self):
        return ('Mask image I (VTK)', 'Marker image J (VTK)')

    def setInput(self, idx, inputStream):
        if idx == 0:
            self._greyReconstruct.SetInput1(inputStream)
        else:
            self._greyReconstruct.SetInput2(inputStream)

    def getOutputDescriptions(self):
        return ('Reconstructed image (VTK)', )

    def getOutput(self, idx):
        return self._greyReconstruct.GetOutput()

    def logicToConfig(self):
        pass
    
    def configToLogic(self):
        pass
    
    def viewToConfig(self):
        pass

    def configToView(self):
        pass
    
    def executeModule(self):
        self._greyReconstruct.Update()
        
    
