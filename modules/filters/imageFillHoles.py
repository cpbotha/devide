from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtk
import vtkdevide


class imageFillHoles(scriptedConfigModuleMixin, moduleBase):
    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        self._imageBorderMask = vtkdevide.vtkImageBorderMask()
        # input image value for border
        self._imageBorderMask.SetBorderMode(1)
        # maximum of output for interior
        self._imageBorderMask.SetInteriorMode(3)
        
        self._imageGreyReconstruct = vtkdevide.vtkImageGreyscaleReconstruct3D()
        # we're going to use the dual, instead of inverting mask and image,
        # performing greyscale reconstruction, and then inverting the result
        # again.  (we should compare results though)
        self._imageGreyReconstruct.SetDual(1)

        # marker J is second input
        self._imageGreyReconstruct.SetInput(
            1, self._imageBorderMask.GetOutput())

        moduleUtils.setupVTKObjectProgress(self, self._imageBorderMask,
                                           'Creating image mask.')
        
        
        moduleUtils.setupVTKObjectProgress(self, self._imageGreyReconstruct,
                                           'Performing reconstruction.')
        

        self._config.holesTouchEdges = (0,0,0,0,0,0)

        configList = [
            ('Allow holes to touch edges:', 'holesTouchEdges',
             'tuple:int,6', 'text',
             'Indicate which edges (minX, maxX, minY, maxY, minZ, maxZ) may\n'
             'be touched by holes.  In other words, a hole touching such an\n'
             'edge will not be considered background and will be filled.')
            ]

        scriptedConfigModuleMixin.__init__(self, configList)        

        self._viewFrame = self._createViewFrame(
            {'Module (self)' : self,
             'vtkImageBorderMask' : self._imageBorderMask,
             'vtkImageGreyReconstruct' : self._imageGreyReconstruct})

        self.configToLogic()
        self.logicToConfig()
        self.configToView()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)

        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)

        moduleBase.close(self)
        
        # get rid of our reference
        del self._imageBorderMask
        del self._imageGreyReconstruct

    def getInputDescriptions(self):
        return ('VTK Image Data to be filled',)

    def setInput(self, idx, inputStream):
        self._imageBorderMask.SetInput(inputStream)
        # first input of the reconstruction is the image
        self._imageGreyReconstruct.SetInput(0, inputStream)

    def getOutputDescriptions(self):
        return ('Filled VTK Image Data', 'Marker')

    def getOutput(self, idx):
        if idx == 0:
            return self._imageGreyReconstruct.GetOutput()
        else:
            return self._imageBorderMask.GetOutput()

    def logicToConfig(self):
        borders = self._imageBorderMask.GetBorders()
        # if there is a border, a hole touching that edge is no hole
        self._config.holesTouchEdges = [int(not i) for i in borders]

    def configToLogic(self):
        borders = [int(not i) for i in self._config.holesTouchEdges]
        self._imageBorderMask.SetBorders(borders)

    def executeModule(self):
        self._imageGreyReconstruct.Update()
        



    
        

    
        
                            
