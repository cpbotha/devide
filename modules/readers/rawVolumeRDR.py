import genUtils
from moduleBase import moduleBase
from moduleMixins import vtkPipelineConfigModuleMixin
from moduleMixins import fileOpenDialogModuleMixin
import moduleUtils
import vtk
import wx

class rawVolumeRDR(moduleBase,
                   vtkPipelineConfigModuleMixin,
                   fileOpenDialogModuleMixin):

    def __init__(self, moduleManager):

        # call parent constructor
        moduleBase.__init__(self, moduleManager)

	self._reader = vtk.vtkImageReader()
        self._reader.SetFileDimensionality(3)
        # FIXME: make configurable (or disable)
        #self._reader.SetFileLowerLeft(1)        

        moduleUtils.setupVTKObjectProgress(self, self._reader,
                                           'Reading raw volume data')

        
        
        self._dataTypes = {'Double': vtk.VTK_DOUBLE,
                           'Float' : vtk.VTK_FLOAT,
                           'Long'  : vtk.VTK_LONG,
                           'Unsigned Long' : vtk.VTK_UNSIGNED_LONG,
                           'Integer' : vtk.VTK_INT,
                           'Unsigned Integer' : vtk.VTK_UNSIGNED_INT,
                           'Short' : vtk.VTK_SHORT,
                           'Unsigned Short' : vtk.VTK_UNSIGNED_SHORT,
                           'Char' : vtk.VTK_CHAR,
                           'Unsigned Char' : vtk.VTK_UNSIGNED_CHAR}

        self._viewFrame = None

        # now setup some defaults before our sync
        self._config.filename = ''
        self._config.dataType = self._reader.GetDataScalarType()
        # 1 is little endian
        self._config.endianness = 1
        self._config.headerSize = 0
        self._config.extent = (0, 128, 0, 128, 0, 128)
        self._config.spacing = (1.0, 1.0, 1.0)

        self.sync_module_logic_with_config()

    def close(self):
        # close down the vtkPipeline stuff
        vtkPipelineConfigModuleMixin.close(self)
        # take out our view interface
        if self._viewFrame is not None:
            self._viewFrame.Destroy()
            
        # get rid of our reference
        del self._reader

    def get_input_descriptions(self):
        return ()

    def set_input(self, idx, inputStream):
        raise Exception, 'rawVolumeRDR has no input!'

    def get_output_descriptions(self):
	return (self._reader.GetOutput().GetClassName(),)

    def get_output(self, idx):
        return self._reader.GetOutput()

    def logic_to_config(self):
        # now setup some defaults before our sync
        self._config.filename = self._reader.GetFileName()
        self._config.dataType = self._reader.GetDataScalarType()
        self._config.endianness = self._reader.GetDataByteOrder()
        # it's going to try and calculate this... do we want this behaviour?
        self._config.headerSize = self._reader.GetHeaderSize()
        self._config.extent = self._reader.GetDataExtent()
        self._config.spacing = self._reader.GetDataSpacing()

    def config_to_logic(self):
        self._reader.SetFileName(self._config.filename)
        self._reader.SetDataScalarType(self._config.dataType)
        self._reader.SetDataByteOrder(self._config.endianness)
        self._reader.SetHeaderSize(self._config.headerSize)
        self._reader.SetDataExtent(self._config.extent)
        self._reader.SetDataSpacing(self._config.spacing)
        
    def view_to_config(self):
        if self._viewFrame is None:
            self._createViewFrame()
        
        self._config.filename = self._viewFrame.filenameText.GetValue()

        # first get the selected string
        dtcString = self._viewFrame.dataTypeChoice.GetStringSelection()
        # this string MUST be in our dataTypes dictionary, get its value
        self._config.dataType = self._dataTypes[dtcString]

        # we have little endian first, but in VTK world it has to be 1
        ebs = self._viewFrame.endiannessRadioBox.GetSelection()
        self._config.endianness = not ebs

        # try and convert headerSize control to int, if it doesn't work,
        # use old value
        try:
            headerSize = int(self._viewFrame.headerSizeText.GetValue())
        except:
            headerSize = self._config.headerSize

        self._config.headerSize = headerSize
        
        # try and convert the string to a tuple
        # yes, this is a valid away! see:
        # http://mail.python.org/pipermail/python-list/1999-April/000546.html
        try:
            extent = eval(self._viewFrame.extentText.GetValue())

            # now check that extent is a 6-element tuple
            if type(extent) != tuple or len(extent) != 6:
                raise Exception

            # make sure that each element is an int
            extent = tuple([int(i) for i in extent])
            
        except:
            # if this couldn't be converted to a 6-element int tuple, default
            # to what's in config
            extent = self._config.extent

        self._config.extent = extent

        try:
            spacing = eval(self._viewFrame.spacingText.GetValue())

            # now check that spacing is a 3-element tuple
            if type(spacing) != tuple or len(spacing) != 3:
                raise Exception

            # make sure that each element is an FLOAT
            spacing = tuple([float(i) for i in spacing])
            
        except:
            # if this couldn't be converted to a 6-element int tuple, default
            # to what's in config
            spacing = self._config.spacing

        self._config.spacing = spacing

    def config_to_view(self):

        self._viewFrame.filenameText.SetValue(self._config.filename)

        # now we have to find self._config.dataType in self._dataTypes
        # I believe that I can assume .values() and .keys() to be consistent
        # with each other (if I don't mutate the dictionary)
        idx = self._dataTypes.values().index(self._config.dataType)
        self._viewFrame.dataTypeChoice.SetStringSelection(
            self._dataTypes.keys()[idx])

        self._viewFrame.endiannessRadioBox.SetSelection(
            not self._config.endianness)
        self._viewFrame.headerSizeText.SetValue(str(self._config.headerSize))
        self._viewFrame.extentText.SetValue(str(self._config.extent))
        spacingText = "(%.3f, %.3f, %.3f)" % tuple(self._config.spacing)
        self._viewFrame.spacingText.SetValue(spacingText)

    def execute_module(self):
        # get the reader to read :)
        self._reader.Update()
        

    def view(self, parent_window=None):
        if self._viewFrame is None:
            self._createViewFrame()
            self.sync_module_view_with_logic()
        
        # if the window was visible already. just raise it
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()

    def _createViewFrame(self):

        # import the viewFrame (created with wxGlade)
        import modules.readers.resources.python.rawVolumeRDRViewFrame
        reload(modules.readers.resources.python.rawVolumeRDRViewFrame)

        self._viewFrame = moduleUtils.instantiateModuleViewFrame(
            self, self._moduleManager,
            modules.readers.resources.python.rawVolumeRDRViewFrame.\
            rawVolumeRDRViewFrame)

        # bind the file browse button
        wx.EVT_BUTTON(self._viewFrame,
                      self._viewFrame.browseButtonId,
                      self._browseButtonCallback)
                   
        # setup object introspection
        objectDict = {'vtkImageReader' : self._reader}
        moduleUtils.createStandardObjectAndPipelineIntrospection(
            self, self._viewFrame, self._viewFrame.viewFramePanel,
            objectDict, None)

        # standard module buttons + events
        moduleUtils.createECASButtons(self, self._viewFrame,
                                      self._viewFrame.viewFramePanel)

        # finish setting up the output datatype choice
        self._viewFrame.dataTypeChoice.Clear()
        for aType in self._dataTypes.keys():
            self._viewFrame.dataTypeChoice.Append(aType)

    def _browseButtonCallback(self, event): 
        path = self.filenameBrowse(self._viewFrame,
                                   "Select a raw volume filename",
                                   "All files (*)|*")

        if path != None:
            self._viewFrame.filenameText.SetValue(path)

