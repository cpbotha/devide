from moduleBase import moduleBase
from moduleMixins import vtkPipelineConfigModuleMixin
import moduleUtils
from wxPython.wx import *
import vtk
import vtkdscas

class shellSplatSimpleFLT(moduleBase, vtkPipelineConfigModuleMixin):

    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)

        # setup our pipeline
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

        self._viewFrame = None
        self._createViewFrame()


    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)

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
    
    def _createViewFrame(self):

        mm = self._moduleManager
        # import/reload the viewFrame (created with wxGlade)
        modules = mm.importReload(
            'modules.resources.python.shellSplatSimpleFLTViewFrame')

        # find our parent window and instantiate the frame
        pw = mm.get_module_view_parent_window()
        self._viewFrame = \
                        modules.resources.python.shellSplatSimpleFLTViewFrame.\
                        shellSplatSimpleFLTViewFrame(pw, -1, 'dummy')

        moduleUtils.createECASButtons(self, self._viewFrame,
                                      self._viewFrame.viewFramePanel)

        # make sure that a close of that window does the right thing
        EVT_CLOSE(self._viewFrame,
                  lambda e, s=self: s._viewFrame.Show(false))

        # default binding for the buttons at the bottom
        #moduleUtils.bindCSAEO(self, self._viewFrame)        

        # and now the standard examine object/pipeline stuff
        #EVT_CHOICE(self._viewFrame, self._viewFrame.objectChoiceId,
        #           self.vtkObjectChoiceCallback)
        #EVT_BUTTON(self._viewFrame, self._viewFrame.pipelineButtonId,
        #           self.vtkPipelineCallback)
        
