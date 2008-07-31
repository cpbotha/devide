# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

from typeModules.imageStackClass import imageStackClass
import fixitk as itk
from module_base import ModuleBase
from module_mixins import FileOpenDialogModuleMixin
import module_utils
import wx

class imageStackRDR(ModuleBase, FileOpenDialogModuleMixin):
    """Loads a list of images as ITK Images.

    This list can e.g. be used as input to the 2D registration module.
    """

    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        # list of ACTUAL itk images
        self._imageStack = imageStackClass(self)

        self._viewFrame = None
        self._createViewFrame()

        # list of names that are to be loaded
        self._config._imageFileNames = []
        # we'll use this variable to check when we need to reload
        # filenames.
        self._imageFileNamesChanged = True
        #

        self.config_to_logic()
        self.logic_to_config()
        self.config_to_view()

    def close(self):

        # we took out explicit ITK references, let them go!
        for img in self._imageStack:
            img.UnRegister()
            
        # take care of other refs to all the loaded images            
        self._imageStack.close()
        self._imageStack = []
        # destroy GUI
        self._viewFrame.Destroy()
        # base classes taken care of
        ModuleBase.close(self)

    def get_input_descriptions(self):
        return ()

    def set_input(self, idx, inputStream):
        raise Exception

    def get_output_descriptions(self):
        return ('ITK Image Stack',)

    def get_output(self, idx):
        return self._imageStack

    def logic_to_config(self):
        pass

    def config_to_logic(self):
        pass

    def view_to_config(self):
        count = self._viewFrame.fileNamesListBox.GetCount()
        tempList = []
        for n in range(count):
            tempList.append(self._viewFrame.fileNamesListBox.GetString(n))

        
        if tempList != self._config._imageFileNames:
            # this is a new list
            self._imageFileNamesChanged = True
            # copy...
            self._config._imageFileNames = tempList
            
    def config_to_view(self):
        # clear wxListBox
        self._viewFrame.fileNamesListBox.Clear()
        for fileName in self._config._imageFileNames:
            self._viewFrame.fileNamesListBox.Append(fileName)

    def execute_module(self):
        if self._imageFileNamesChanged:
            # only if things have changed do we do our thing
            # first take care of old refs
            del self._imageStack[:]

            # setup for progress counter
            currentProgress = 0.0
            if len(self._config._imageFileNames) > 0:
                progressStep = 100.0 / len(self._config._imageFileNames)
            else:
                progressStep = 100.0
                
            for imageFileName in self._config._imageFileNames:
                self._module_manager.setProgress(
                    currentProgress, "Loading %s" % (imageFileName,))
                currentProgress += progressStep
                
                reader = itk.itkImageFileReaderF2_New()
                reader.SetFileName(imageFileName)
                reader.Update()
                self._imageStack.append(reader.GetOutput())
                # velly important; with ITK wrappings, ref count doesn't
                # increase if there's a coincidental python binding
                # it does if there was an explicit New()
                self._imageStack[-1].Register()

            self._module_manager.setProgress(100.0, "Done loading images.")
            # make sure all observers know about the changes
            self._imageStack.notify()
            # indicate that we're in sync now
            self._imageFileNamesChanged = False

    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()

    def _bindEvents(self):
        wx.EVT_BUTTON(self._viewFrame, self._viewFrame.addButtonId,
                      self._handlerAddButton)

    def _createViewFrame(self):
        self._module_manager.import_reload(
            'modules.Insight.resources.python.imageStackRDRViewFrame')
        import modules.Insight.resources.python.imageStackRDRViewFrame

        self._viewFrame = module_utils.instantiate_module_view_frame(
            self, self._module_manager,
            modules.Insight.resources.python.imageStackRDRViewFrame.\
            imageStackRDRViewFrame)

        module_utils.create_eoca_buttons(self, self._viewFrame,
                                      self._viewFrame.viewFramePanel)

        self._bindEvents()

    def _handlerAddButton(self, event):
        fres = self.filenameBrowse(self._viewFrame,
                                   "Select files to add to stack",
                                   "*", wx.OPEN | wx.MULTIPLE)
        if fres:
            for fileName in fres:
                self._viewFrame.fileNamesListBox.Append(fileName)
                
            
