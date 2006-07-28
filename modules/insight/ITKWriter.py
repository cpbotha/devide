# $Id$

import itk
import module_kits.itk_kit as itk_kit
from moduleBase import moduleBase
from moduleMixins import filenameViewModuleMixin
import re

class ITKWriter(moduleBase, filenameViewModuleMixin):
    def __init__(self, moduleManager):

        # call parent constructor
        moduleBase.__init__(self, moduleManager)
        # ctor for this specific mixin
        filenameViewModuleMixin.__init__(self)

        self._input = None
        self._writer = None
        self._writer_type = None

        wildCardString = 'Meta Image all-in-one (*.mha)|*.mha|' \
                         'Meta Image separate header/data (*.mhd)|*.mhd|' \
                         'Analyze separate header/data (*.hdr)|*.hdr|' \
                         'All files (*)|*'
        # we now have a viewFrame in self._viewFrame
        self._createViewFrame('Select a filename',
                              wildCardString,
                              {'Module (self)': self},
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
	return ('ITK Image',)
    
    def setInput(self, idx, inputStream):
        # should we take an explicit ref?
        if inputStream == None:
            # this is a disconnect
            self._input = inputStream

        else:
            try:
                if inputStream.GetNameOfClass() != 'Image':
                    raise AttributeError
            except AttributeError, e:
                raise TypeError, \
                      'This module requires an ITK Image Type (%s).' \
                      % (str(e),)
            else:
                self._input = inputStream
    
    def getOutputDescriptions(self):
	return ()
    
    def getOutput(self, idx):
        raise Exception
    
    def logicToConfig(self):
        return False

    def configToLogic(self):
        # if the user has Applied, we assume that things have changed
        # we could check for a change in the filename... (it's only that)
        return True

    def viewToConfig(self):
        self._config.filename = self._getViewFrameFilename()

    def configToView(self):
        self._setViewFrameFilename(self._config.filename)

    def executeModule(self):
        
        if len(self._config.filename) and self._input:

            shortstring = itk_kit.utils.get_img_type_and_dim_shortstring(
                self._input)

            if shortstring != self._writer_type:
                print "ITKWriter: creating new writer instance."
                witk_template = getattr(itk, 'ImageFileWriter')
                witk_type = getattr(itk.Image, shortstring)

                try:
                    self._writer = witk_template[witk_type].New()
                except Exception, e:
                    if vectorString == 'V':
                        vType = 'vector'
                    else:
                        vType = ''
                         
                        raise RuntimeError, \
                              'Unable to instantiate ITK writer with' \
                              'type %s.' % (shortstring,)

                else:
                    itk_kit.utils.setupITKObjectProgress(
                        self, self._writer,
                        'itkImageFileWriter',
                        'Writing ITK image to disc.')                    
                    
                    self._writer_type = shortstring

            self._input.UpdateOutputInformation()
            self._input.SetBufferedRegion(
                self._input.GetLargestPossibleRegion())
            self._input.Update()
                
            self._writer.SetInput(self._input)
            self._writer.SetFileName(self._config.filename)
            # activating this crashes DeVIDE *BOOM*
            #self._writer.GetImageIO().SetUseCompression(True)
            self._writer.Write()

    def view(self, parent_window=None):
        self._viewFrame.Show(True)
        self._viewFrame.Raise()
