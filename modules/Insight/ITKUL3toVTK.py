# $Id: ITKUL3toVTK.py,v 1.1 2004/03/10 17:56:19 cpbotha Exp $

import fixitk as itk
import genUtils
from moduleBase import moduleBase
import moduleUtils
import moduleUtilsITK
from moduleMixins import noConfigModuleMixin
import vtk
import ConnectVTKITKPython as CVIPy

class ITKUL3toVTK(noConfigModuleMixin, moduleBase):
    """Convert ITK 3D unsigned long data to VTK.

    $Revision: 1.1 $
    """

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)
        noConfigModuleMixin.__init__(self)

        self._itkExporter = itk.itkVTKImageExportUL3_New()

        # setup the pipeline
        self._vtkImporter = vtk.vtkImageImport()

        CVIPy.ConnectITKUL3ToVTK(
            self._itkExporter.GetPointer(), self._vtkImporter)

        self._viewFrame = self._createViewFrame(
            {'Module (self)' : self,
             'itkVTKImageExportUL3' : self._itkExporter,
             'vtkImageImport' : self._vtkImporter})

        self.configToLogic()
        self.syncViewWithLogic()


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
        self._vtkImporter.Update()

    def getInputDescriptions(self):
        return ('ITK Image (3D, float)',)        

    def setInput(self, idx, inputStream):
        self._itkExporter.SetInput(inputStream)

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
    
    def executeModule(self):
        self._vtkImporter.Update()

    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        self._viewFrame.Show(True)
        self._viewFrame.Raise()

        
            
