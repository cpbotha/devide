# $Id: VTKtoITKF3.py,v 1.2 2004/03/16 12:29:00 cpbotha Exp $

import fixitk as itk
import genUtils
from moduleBase import moduleBase
import moduleUtils
import moduleUtilsITK
from moduleMixins import noConfigModuleMixin
import vtk
import ConnectVTKITKPython as CVIPy

class VTKtoITKF3(noConfigModuleMixin, moduleBase):

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)
        noConfigModuleMixin.__init__(self)

        # setup the pipeline
        self._imageCast = vtk.vtkImageCast()
        self._imageCast.SetOutputScalarTypeToFloat()

        self._vtkExporter = vtk.vtkImageExport()
        #self._vtkExporter.SetInput(self._imageCast.GetOutput())

        # later we can build multiple pipelines with different types
        self._itkImporter = itk.itkVTKImageImportF3_New()
        CVIPy.ConnectVTKToITKF3(
            self._vtkExporter, self._itkImporter.GetPointer())

        self._viewFrame = self._createViewFrame(
            {'Module (self)' : self,
             'vtkImageCast' : self._imageCast,
             'vtkImageExport' : self._vtkExporter,
             'itkVTKImageImportF3' : self._itkImporter})

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

        del self._imageCast
        del self._vtkExporter
        del self._itkImporter

    def executeModule(self):
        self._itkImporter.Update()

    def getInputDescriptions(self):
        return ('VTK Image Data',)

    def setInput(self, idx, inputStream):
        self._imageCast.SetInput(inputStream)
        if inputStream and self._imageCast.GetInput() == inputStream:
            # a non-NULL input has been connected, so we connect up with
            # the vtkExporter
            self._vtkExporter.SetInput(self._imageCast.GetOutput())
        else:
            # the connect has been unsuccesful or the input is NULL
            self._vtkExporter.SetInput(None)

    def getOutputDescriptions(self):
        return ('ITK Image (3D, float)',)

    def getOutput(self, idx):
        return self._itkImporter.GetOutput()

    def logicToConfig(self):
        pass
    
    def configToLogic(self):
        pass
    
    def viewToConfig(self):
        pass

    def configToView(self):
        pass
    
    def executeModule(self):
        self._itkImporter.Update()

    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        self._viewFrame.Show(True)
        self._viewFrame.Raise()

        
            
