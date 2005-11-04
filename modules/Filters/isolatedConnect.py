import genUtils
from moduleBase import moduleBase
from moduleMixins import vtkPipelineConfigModuleMixin
import moduleUtils
import vtk
import InsightToolkit as itk
import ConnectVTKITKPython as CVIPy

class isolatedConnect(moduleBase):

    def __init__(self, moduleManager):

        # call parent constructor
        moduleBase.__init__(self, moduleManager)

        # this will be the input module for now
        # (we still have to make a vtk->itk and an itk->vtk module)
        self._imageCast = vtk.vtkImageCast()
        self._imageCast.SetOutputScalarTypeToFloat()

        self._vtkExporter = vtk.vtkImageExport()
        self._vtkExporter.SetInput(self._imageCast.GetOutput())

        self._itkImporter = itk.itkVTKImageImportF3_New()
        CVIPy.ConnectVTKToITKF3(
            self._vtkExporter, self._itkImporter.GetPointer())

        # we're finally in ITK land now
        self._isolatedConnect = itk.itkIsolatedConnectedImageFilterF3F3_New()
        self._isolatedConnect.SetInput(self._itkImporter.GetOutput())
        # lower threshold, not configurable right now
        self._isolatedConnect.SetLower(0.9)


        self._itkExporter = itk.itkVTKImageExportF3_New()
        self._itkExporter.SetInput(self._isolatedConnect.GetOutput())

        self._vtkImporter = vtk.vtkImageImport()
        CVIPy.ConnectITKF3ToVTK(
            self._itkExporter.GetPointer(), self._vtkImporter)
        
        #moduleUtils.setupVTKObjectProgress(self, self._seedConnect,
        #                                   'Performing region growing')
        #moduleUtils.setupVTKObjectProgress(self, self._imageCast,
        #                                   'Casting data to unsigned char')
        
        # we'll use this to keep a binding (reference) to the passed object
        self._inputPoints = None
        # inputPoints observer ID
        self._inputPointsOID = None
        # this will be our internal list of points
        self._seedPoints = []

        # now setup some defaults before our sync
        #self._config.inputConnectValue = 1
        #self._config.outputConnectedValue = 1
        #self._config.outputUnconnectedValue = 0

        self._viewFrame = None
        #self._createViewFrame()

        # transfer these defaults to the logic
        self.configToLogic()

        # then make sure they come all the way back up via self._config
        self.logicToConfig()
        self.configToView()
        
    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        self.setInput(0, None)
        self.setInput(1, None)
        # take out our view interface
        #self._viewFrame.Destroy()
        # get rid of our reference
        del self._imageCast
        del self._vtkExporter
        del self._itkImporter
        del self._isolatedConnect

    def getInputDescriptions(self):
	return ('3D vtkImageData', 'Seed points')
    
    def setInput(self, idx, inputStream):
        if idx == 0:
            # will work for None and not-None
            self._imageCast.SetInput(inputStream)
        else:
            if inputStream is not self._inputPoints:
                if self._inputPoints:
                    self._inputPoints.removeObserver(self._inputPointsOID)

                if inputStream:
                    self._inputPointsOID = inputStream.addObserver(
                        self._inputPointsObserver)

                self._inputPoints = inputStream

                # initial update
                self._inputPointsObserver(None)
            
    
    def getOutputDescriptions(self):
	return (self._vtkImporter.GetOutput().GetClassName(),)
    
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
        self._isolatedConnect.Update()

    def view(self, parent_window=None):
        pass
    
    def _createViewFrame(self):
        pass
    
    def _inputPointsObserver(self, obj):
        # extract a list from the input points
        tempList = []
        if self._inputPoints:
            for i in self._inputPoints:
                tempList.append(i['discrete'])
            
        if len(tempList) >= 2 and tempList != self._seedPoints:
            self._seedPoints = tempList
            #self._seedConnect.RemoveAllSeeds()

            idx1 = itk.itkIndex3()
            idx2 = itk.itkIndex3()
            
            for ei in range(3):
                idx1.SetElement(ei, self._seedPoints[0][ei])
                idx2.SetElement(ei, self._seedPoints[1][ei])

            self._isolatedConnect.SetSeed1(idx1)
            self._isolatedConnect.SetSeed2(idx2)



