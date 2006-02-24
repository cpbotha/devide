# $Id$

import itk
import genUtils
from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
import vtk
import ConnectVTKITKPython as CVIPy

class ITKUS3toVTK(noConfigModuleMixin, moduleBase):
    """Convert ITK 3D unsigned short data to VTK.

    $Revision: 1.2 $
    """

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)
        noConfigModuleMixin.__init__(self)

        self._itkExporter = itk.itkVTKImageExportUS3_New()

        # setup the pipeline
        self._vtkImporter = vtk.vtkImageImport()

        CVIPy.ConnectITKUS3ToVTK(
            self._itkExporter.GetPointer(), self._vtkImporter)

        self._viewFrame = self._createViewFrame(
            {'Module (self)' : self,
             'itkVTKImageExportUS3' : self._itkExporter,
             'vtkImageImport' : self._vtkImporter})

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

        del self._itkExporter
        del self._vtkImporter

    def executeModule(self):
        o = self._vtkImporter.GetOutput()
        o.UpdateInformation()
        o.SetUpdateExtentToWholeExtent()
        o.Update()

    def getInputDescriptions(self):
        return ('ITK Image (3D, float)',)        

    def setInput(self, idx, inputStream):
        self._itkExporter.SetInput(inputStream)
        if not inputStream:
            # if the inputStream is NULL, we make sure that the output is empty
            self._vtkImporter.GetOutput().SetWholeExtent((0,0,0,0,0,0))
            self._vtkImporter.GetOutput().SetExtent((0,0,0,0,0,0))
            self._vtkImporter.GetOutput().SetUpdateExtent((0,0,0,0,0,0))            

    def getOutputDescriptions(self):
        return ('VTK Image Data',)

    def getOutput(self, idx):
        return self._vtkImporter.GetOutput()

    def logicToConfig(self):
        pass
    
    def configToLogic(self):
        pass
    
    def viewToConfig(self):
        pass

    def configToView(self):
        pass
    
    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        self._viewFrame.Show(True)
        self._viewFrame.Raise()

        
            
