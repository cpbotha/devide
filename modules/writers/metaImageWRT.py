# $Id$

from moduleBase import moduleBase
from moduleMixins import filenameViewModuleMixin
import moduleUtils
import vtk
from module_kits.vtk_kit.mixins import VTKErrorFuncMixin

class metaImageWRT(moduleBase, filenameViewModuleMixin, VTKErrorFuncMixin):
    """Writes VTK image data or structured points in MetaImage format.

    """

    def __init__(self, moduleManager):

        # call parent constructor
        moduleBase.__init__(self, moduleManager)
        # ctor for this specific mixin
        filenameViewModuleMixin.__init__(self)

        self._writer = vtk.vtkMetaImageWriter()

        moduleUtils.setupVTKObjectProgress(
            self, self._writer,
            'Writing VTK ImageData')

        self.add_vtk_error_handler(self._writer)

        # we now have a viewFrame in self._viewFrame
        self._createViewFrame('Select a filename',
                              'MetaImage file (*.mha)|*.mha|All files (*)|*',
                              {'vtkMetaImageWriter': self._writer},
                              fileOpen=False)

        # set up some defaults
        self._config.filename = ''
        self.configToLogic()
        # make sure these filter through from the bottom up
        self.logicToConfig()
        self.configToView()

    def close(self):
        # we should disconnect all inputs
        self.setInput(0, None)
        del self._writer
        filenameViewModuleMixin.close(self)

    def getInputDescriptions(self):
	return ('vtkImageData',)
    
    def setInput(self, idx, input_stream):
        self._writer.SetInput(input_stream)
    
    def getOutputDescriptions(self):
	return ()
    
    def getOutput(self, idx):
        raise Exception
    
    def logicToConfig(self):
        filename = self._writer.GetFileName()
        if filename == None:
            filename = ''

        self._config.filename = filename

    def configToLogic(self):
        self._writer.SetFileName(self._config.filename)

    def viewToConfig(self):
        self._config.filename = self._getViewFrameFilename()

    def configToView(self):
        self._setViewFrameFilename(self._config.filename)

    def executeModule(self):
        if len(self._writer.GetFileName()) and self._writer.GetInput():
            self._writer.GetInput().UpdateInformation()
            self._writer.GetInput().SetUpdateExtentToWholeExtent()
            self._writer.GetInput().Update()
            self._writer.Write()

            self.check_vtk_error()

    def view(self, parent_window=None):
        self._viewFrame.Show(True)
        self._viewFrame.Raise()
