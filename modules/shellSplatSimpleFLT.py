from external.SwitchColourDialog import ColourDialog
import operator
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

        # setup the whole VTK pipeline that we're going to use
        self._createPipeline()

        # this is a list of all the objects in the pipeline and will
        # be used by the object and pipeline introspection
        self._objectDict = {'splatMapper' : self._splatMapper,
                            'opacity TF' : self._otf,
                            'colour TF' : self._ctf,
                            'volumeProp' : self._volumeProperty,
                            'volume' : self._volume}


        # setup some config defaults
        # for segmetented data
        self._config.threshold = 1.0
        # bony kind of colour
        self._config.colour = (1.0, 0.937, 0.859)
        # high quality, doh
        self._config.renderMode = 0

        # create the gui
        self._viewFrame = None
        self._createViewFrame()

        # some more UI elements that we'll need
        ccd = wxColourData()
        ccd.SetCustomColour(0,wxColour(255, 239, 219))
        # under windows, we want the complete thing
        ccd.SetChooseFull(True)
        # and create the bugger
        self._colourDialog = ColourDialog(self._viewFrame, ccd)

        # pass the data down to the underlying logic
        self.configToLogic()
        # and all the way up from logic -> config -> view to make sure
        self.syncViewWithLogic()

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

        del self._objectDict

        if self._colourDialog:
            self._colourDialog.Destroy()
            
        del self._colourDialog

        # we have to call this mixin close so that all inspection windows
        # can be taken care of.  They should be taken care of in anycase
        # when the viewFrame is destroyed, but we like better safe than
        # sorry
        vtkPipelineConfigModuleMixin.close(self)

        # take care of our own window
        self._viewFrame.Destroy()
        del self._viewFrame

    def getInputDescriptions(self):
	return ('input image data', 'optional gradient image data')

    def setInput(self, idx, inputStream):
        if idx == 0:
            self._splatMapper.SetInput(inputStream)
        else:
            self._splatMapper.SetGradientImageData(inputStream)

    def getOutputDescriptions(self):
        return (self._volume.GetClassName(),)

    def getOutput(self, idx):
        return self._volume

    def logicToConfig(self):
        # we CAN'T derive the threshold and colour from the opacity and colour
        # transfer functions (or we could, but it'd be terribly dirty)
        # but fortunately we don't really have to - logiToConfig is only really
        # for cases where the logic could return config information different
        # from that we programmed it with

        # this we can get
        self._config.renderMode = self._splatMapper.GetRenderMode()
        

    def configToLogic(self):

        # only modify the transfer functions if they've actually changed
        if self._otf.GetSize() != 2 or \
           self._otf.GetValue(self._config.threshold - 0.1) != 0.0 or \
           self._otf.GetValue(self._config.threshold) != 1.0:
            # make a step in the opacity transfer function
            self._otf.RemoveAllPoints()
            self._otf.AddPoint(self._config.threshold - 0.1, 0.0)
            self._otf.AddPoint(self._config.threshold, 1.0)

        # sample the two points and check that they haven't changed too much
        tfCol1 = self._ctf.GetColor(self._config.threshold)
        colDif1 = [i for i in
                  map(abs, map(operator.sub, self._config.colour, tfCol1))
                  if i > 0.001]

        tfCol2 = self._ctf.GetColor(self._config.threshold - 0.1)
        colDif2 = [i for i in
                  map(abs, map(operator.sub, (0,0,0), tfCol2))
                  if i > 0.001]
        
        if self._ctf.GetSize() != 2 or colDif1 or colDif2:
            # make a step in the colour transfer
            self._ctf.RemoveAllPoints()
            r,g,b = self._config.colour
            # setting two points is not necessary, but we play it safe
            self._ctf.AddRGBPoint(self._config.threshold - 0.1, 0, 0, 0)
            self._ctf.AddRGBPoint(self._config.threshold, r, g, b)

        # set the rendering mode
        self._splatMapper.SetRenderMode(self._config.renderMode)

    def viewToConfig(self):
        # get the threshold
        try:
            threshold = float(self._viewFrame.thresholdText.GetValue())
        except:
            # this means the user did something stupid, so we revert
            # to what's in the config - this will also turn up back
            # in the input box, as the DSCAS3 arch automatically syncs
            # view with logic after having applied changes
            threshold = self._config.threshold

        # store it in the config
        self._config.threshold = threshold
        
        # convert the colour in the input box to something we can use
        colour = self._colourDialog.GetColourData().GetColour()
        defaultColourTuple = (colour.Red() / 255.0,
                              colour.Green() / 255.0,
                              colour.Blue() / 255.0)
        colourTuple = self._convertStringToColour(
            self._viewFrame.colourText.GetValue(),
            defaultColourTuple)

        # and put it in the right place
        self._config.colour = colourTuple
        
        self._config.renderMode = self._viewFrame.\
                                  renderingModeChoice.GetSelection()

    def configToView(self):
        self._viewFrame.thresholdText.SetValue("%.2f" %
                                               (self._config.threshold))
        self._viewFrame.colourText.SetValue(
            "(%.3f, %.3f, %.3f)" % self._config.colour)
        self._viewFrame.renderingModeChoice.SetSelection(
            self._config.renderMode)

    def executeModule(self):
        self._splatMapper.Update()


    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()

    def _colourButtonCallback(self, evt):
        # first we have to translate the colour which is in the textentry
        # and set it in the colourDialog

        colour = self._colourDialog.GetColourData().GetColour()
        defaultColourTuple = (colour.Red() / 255.0,
                              colour.Green() / 255.0,
                              colour.Blue() / 255.0)
        colourTuple = self._convertStringToColour(
            self._viewFrame.colourText.GetValue(),
            defaultColourTuple)

        colourTuple = tuple([i * 255.0 for i in colourTuple])        

        self._colourDialog.GetColourData().SetColour(colourTuple)
        
        if self._colourDialog.ShowModal() == wxID_OK:
            col = self._colourDialog.GetColourData().GetColour()
            self._viewFrame.colourText.SetValue(
                "(%.2f, %.2f, %.2f)" %  (col.Red() / 255.0,
                                         col.Green() / 255.0,
                                         col.Blue() / 255.0))

    def _convertStringToColour(self, colourString, defaultColourTuple):
        """Attempt to convert colourString into tuple representation.

        Returns colour tuple.  No scaling is done, i.e. 3 elements in the str
        tuple are converted to floats and returned as a 3-tuple.
        """

        try:
            colourTuple = eval(colourString)
            if type(colourTuple) != tuple or len(colourTuple) != 3:
                raise Exception

            colourTuple = tuple([float(i) for i in colourTuple])
            
        except:
            # if we can't convert, we just let the colour chooser use
            # its previous default
            colourTuple = defaultColourTuple

        return colourTuple

    def _createPipeline(self):
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
        
    
    def _createViewFrame(self):

        mm = self._moduleManager
        # import/reload the viewFrame (created with wxGlade)
        mm.importReload(
            'modules.resources.python.shellSplatSimpleFLTViewFrame')
        # this line is harmless due to Python's import caching, but we NEED
        # to do it so that the Installer knows that this dscas3 module
        # requires it and so that it's available in this namespace.
        import modules.resources.python.shellSplatSimpleFLTViewFrame

        self._viewFrame = moduleUtils.instantiateModuleViewFrame(
            self, mm, modules.resources.python.shellSplatSimpleFLTViewFrame.\
            shellSplatSimpleFLTViewFrame)

        # setup introspection with default everythings
        moduleUtils.createStandardObjectAndPipelineIntrospection(
            self, self._viewFrame, self._viewFrame.viewFramePanel,
            self._objectDict, None)

        # create and configure the standard ECAS buttons
        moduleUtils.createECASButtons(self, self._viewFrame,
                                      self._viewFrame.viewFramePanel)

        
        # now we can finally do our own stuff to
        EVT_BUTTON(self._viewFrame, self._viewFrame.colourButtonId,
                   self._colourButtonCallback)
