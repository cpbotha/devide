from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
from wxPython.wx import *
import vtk
import vtkdscas

class shellSplatSegmentedFLT(moduleBase, noConfigModuleMixin):

    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)
        # initialise any mixins we might have
        noConfigModuleMixin.__init__(self)

        # we'll be playing around with some vtk objects, this could
        # be anything
        self._splatMapper = vtkdscas.vtkOpenGLVolumeShellSplatMapper()
        self._splatMapper.SetOmegaL(0.9)
        self._splatMapper.SetOmegaH(0.9)
        # high-quality rendermode
        self._splatMapper.SetRenderMode(0)

        self._otf = vtk.vtkPiecewiseFunction()
        self._otf.AddPoint(0.0, 0.0)
        self._otf.AddPoint(0.9, 0.0)
        self._otf.AddPoint(1.0, 1.0)

        self._ctf = vtk.vtkColorTransferFunction()
        self._ctf.AddRGBPoint(0.0, 0.0, 0.0, 0.0)
        self._ctf.AddRGBPoint(0.9, 0.0, 0.0, 0.0)
        self._ctf.AddRGBPoint(1.0, 1.0, 0.937, 0.859)

        self._volumeProperty = vtk.vtkVolumeProperty()
        self._volumeProperty.SetScalarOpacity(self._otf)
        self._volumeProperty.SetColor(self._ctf)
        self._volumeProperty.ShadeOn()
        self._volumeProperty.SetAmbient(0.1)
        self._volumeProperty.SetDiffuse(0.7)
        self._volumeProperty.SetSpecular(0.2)
        self._volumeProperty.SetSpecularPower(10)

        self._volume = vtk.vtkVolume()
        self._volume.SetProperty(self._volumeProperty)
        self._volume.SetMapper(self._splatMapper)


        self._createViewFrame('Test Module View',
                              {'splatMapper' :
                               self._splatMapper})

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)
        # don't forget to call the close() method of the vtkPipeline mixin
        noConfigModuleMixin.close(self)
        # get rid of our reference
        del self._splatMapper
        del self._otf
        del self._ctf
        del self._volumeProperty
        del self._volume

    def getInputDescriptions(self):
	return ('vtkVolume',)

    def setInput(self, idx, inputStream):
        self._splatMapper.SetInput(inputStream)

    def getOutputDescriptions(self):
        return (self._volume.GetClassName(),)

    def getOutput(self, idx):
        return self._volume

    def logicToConfig(self):
        pass

    def configToLogic(self):
        pass
    

    def viewToConfig(self):
        pass

    def configToView(self):
        pass
    

    def executeModule(self):
        self._splatMapper.Update()


    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()
    
