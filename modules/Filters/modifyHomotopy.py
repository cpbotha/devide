import genUtils
from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
import moduleUtils
import wx
import vtk
import vtkdevide

class modifyHomotopy(noConfigModuleMixin, moduleBase):
    """Modifies homotopy of input image I so that the only minima will
    be at the use-specified seed-points, all other minima will be
    suppressed and ridge lines separating minima will be preserved.

    This is often used as a pre-processing step to ensure that the
    watershed doesn't over-segment.

    This module uses a DeVIDE-specific implementation of Luc Vincent's
    fast greyscale reconstruction algorithm, extended for 3D.
    
    $Revision: 1.1 $
    """
    
    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)
        noConfigModuleMixin.__init__(self)

        self._dualGreyReconstruct = vtkdevide.vtkImageGreyscaleReconstruct3D()
        # we'll use this to synthesise a volume according to the seed points
        self._markerSource = vtk.vtkProgrammableSource()
        # second input is J (the marker)
        self._dualGreyReconstruct.SetInput2(
            self._markerSource.GetStructuredPointsOutput())
        
        moduleUtils.setupVTKObjectProgress(
            self, self._dualGreyReconstruct,
            'Performing dual greyscale reconstruction')
                                           
        self._viewFrame = self._createViewFrame(
            {'Module (self)' : self,
             'vtkImageGreyscaleReconstruct3D' : self._dualGreyReconstruct})

        # pass the data down to the underlying logic
        self.configToLogic()
        # and all the way up from logic -> config -> view to make sure
        self.syncViewWithLogic()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)

        # this will take care of all display thingies
        noConfigModuleMixin.close(self)

        moduleBase.close(self)
        
        # get rid of our reference
        del self._dualGreyReconstruct
        del self._markerSource

    def getInputDescriptions(self):
        return ('VTK Image Data', 'Minima points')

    def setInput(self, idx, inputStream):
        if idx == 0:
            self._dualGreyReconstruct.SetInput1(inputStream)
        else:
            # store the points, take out observer
            pass

    def getOutputDescriptions(self):
        return ('VTK Image Data', )

    def getOutput(self, idx):
        return self._dualGreyReconstruct.GetOutput()

    def logicToConfig(self):
        pass
    
    def configToLogic(self):
        pass

    def viewToConfig(self):
        pass

    def configToView(self):
        pass
    
    def executeModule(self):
        self._dualGreyReconstruct.Update()

