from genMixins import subjectMixin, updateCallsExecuteModuleMixin
from moduleBase import moduleBase
import moduleUtils
import vtk
import wx

class transformStackClass(list,
                          subjectMixin,
                          updateCallsExecuteModuleMixin):
    
    def __init__(self, d3Module):
        # call base ctors
        subjectMixin.__init__(self)
        updateCallsExecuteModuleMixin.__init__(self, d3Module)

    def close(self):
        subjectMixin.close(self)
        updateCallsExecuteModuleMixin.close(self)

class register2D(moduleBase):
    """Registers a stack of 2D images and generates a list of transforms.
    """

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        # input
        self._imageStack = None
        # output is a transform stack
        self._transformStack = transformStackClass(self)

        self._createViewFrames()
        self._bindEvents()

        # FIXME: add current transforms to config stuff

    def close(self):
        moduleBase.close(self)

        # nasty trick to take care of RenderWindow
        self._threedRenderer.RemoveAllProps()
        del self._threedRenderer
        self.viewerFrame.threedRWI.GetRenderWindow().WindowRemap()
        self.viewerFrame.Destroy()
        del self.viewerFrame

        self.controlFrame.Destroy()
        del self.controlFrame

    def getInputDescriptions(self):
        return ('ITK Image Stack',)

    def setInput(self, idx, inputStream):
        # FIXME: check for correct type
        self._imageStack = inputStream
        
    def getOutputDescriptions(self):
        return ('2D Transform Stack',)

    def getOutput(self, idx):
        return self._transformStack

    def executeModule(self):
        pass

    def view(self, parent_window=None):
        # if the window is already visible, raise it
        if not self.viewerFrame.Show(True):
            self.viewerFrame.Raise()

        if not self.controlFrame.Show(True):
            self.controlFrame.Raise()

    # ----------------------------------------------------------------------
    # non-API methods start here -------------------------------------------
    # ----------------------------------------------------------------------

    def _bindEvents(self):
        pass
    
    def _createViewFrames(self):
        import modules.Insight.resources.python.register2DViewFrames
        reload(modules.Insight.resources.python.register2DViewFrames)

        viewerFrame = modules.Insight.resources.python.register2DViewFrames.\
                      viewerFrame
        self.viewerFrame = moduleUtils.instantiateModuleViewFrame(
            self, self._moduleManager, viewerFrame)

        # add the renderer
        self._threedRenderer = vtk.vtkRenderer()
        self._threedRenderer.SetBackground(0.5, 0.5, 0.5)
        self.viewerFrame.threedRWI.GetRenderWindow().AddRenderer(
            self._threedRenderer)

        # controlFrame creation
        controlFrame = modules.Insight.resources.python.\
                       register2DViewFrames.controlFrame
        self.controlFrame = moduleUtils.instantiateModuleViewFrame(
            self, self._moduleManager, controlFrame)

        # display
        self.viewerFrame.Show(True)
        self.controlFrame.Show(True)
        
