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

        self._config.holesTouchX0 = False
        self._config.holesTouchX1 = False
        self._config.holesTouchY0 = False
        self._config.holesTouchY1 = False
        self._config.holesTouchZ0 = False
        self._config.holesTouchZ1 = False

        configList = [
            ('Allow holes to touch minimum X-edge:', 'holesTouchX0',
             'base:bool', 'checkbox',
             'A hole touching this X-edge will not be considered background, '
             'i.e. it will be filled.'),
            ('Allow holes to touch maximum X-edge:', 'holesTouchX1',
             'base:bool', 'checkbox',
             'A hole touching this X-edge will not be considered background, '
             'i.e. it will be filled.'),
            ('Allow holes to touch minimum Y-edge:', 'holesTouchY0',
             'base:bool', 'checkbox',
             'A hole touching this Y-edge will not be considered background, '
             'i.e. it will be filled.'),
            ('Allow holes to touch maximum Y-edge:', 'holesTouchY1',
             'base:bool', 'checkbox',
             'A hole touching this Y-edge will not be considered background, '
             'i.e. it will be filled.'),
            ('Allow holes to touch minimum Z-edge:', 'holesTouchZ0',
             'base:bool', 'checkbox',
             'A hole touching this Z-edge will not be considered background, '
             'i.e. it will be filled.'),
            ('Allow holes to touch maximum Z-edge:', 'holesTouchZ1',
             'base:bool', 'checkbox',
             'A hole touching this Z-edge will not be considered background, '
             'i.e. it will be filled.')
            ]

        scriptedConfigModuleMixin.__init__(self, configList)        

        self._viewFrame = self._createViewFrame(
            {'Module (self)' : self,
             'vtkImageBorderMask' : self._imageBorderMask,
             'vtkImageGreyReconstruct' : self._imageGreyReconstruct})

        self.configToLogic()
        self.syncViewWithLogic()

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
        return ('Filled VTK Image Data',)

    def getOutput(self, idx):
        return self._imageBorderMask.GetOutput()

    def logicToConfig(self):
        borders = self._imageBorderMask.GetBorders()
        self._config.holesTouchX0 = bool(borders[0])
        self._config.holesTouchX1 = bool(borders[1])        
        self._config.holesTouchY0 = bool(borders[2])
        self._config.holesTouchY1 = bool(borders[3])        
        self._config.holesTouchZ0 = bool(borders[4])
        self._config.holesTouchZ1 = bool(borders[5])

    def configToLogic(self):
        borders = [self._config.holesTouchX0,
                   self._config.holesTouchX1,
                   self._config.holesTouchY0,
                   self._config.holesTouchY1,
                   self._config.holesTouchZ0,
                   self._config.holesTouchZ1]
        self._imageBorderMask.SetBorders(borders)

    def executeModule(self):
        self._imageBorderMask.Update()



    
        

    
        
                            
