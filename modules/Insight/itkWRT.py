# $Id: itkWRT.py,v 1.2 2004/05/13 16:23:13 cpbotha Exp $

from moduleBase import moduleBase
from moduleMixins import filenameViewModuleMixin
import moduleUtilsITK
import wx
import fixitk as itk
import re

class itkWRT(moduleBase, filenameViewModuleMixin):
    """Writes any of the image formats supported by the ITK
    itkImageIOFactory.

    At least the following file formats are available (a choice is made based
    on the filename extension that you choose):<br>
    <ul>
    <li>.mha: MetaImage all-in-one file</li>
    <li>.mhd: MetaImage .mhd header file and .raw data file</li>
    <li>.hdr or .img: Analyze .hdr header and .img data</li>
    </ul>

    $Revision: 1.2 $
    """


    def __init__(self, moduleManager):

        # call parent constructor
        moduleBase.__init__(self, moduleManager)
        # ctor for this specific mixin
        filenameViewModuleMixin.__init__(self)

        self._input = None
        self._writer = None

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
        self.syncViewWithLogic()

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
        pass
        #filename = self._writer.GetFileName()
        #if filename == None:
        #    filename = ''

        #self._config.filename = filename

    def configToLogic(self):
        pass
        #self._writer.SetFileName(self._config.filename)

    def viewToConfig(self):
        self._config.filename = self._getViewFrameFilename()

    def configToView(self):
        self._setViewFrameFilename(self._config.filename)

    def executeModule(self):
        
        if len(self._config.filename) and self._input:
            # g will be e.g. ('float', '3')
            g = re.search('.*itk__ImageT(.*)_([0-9]+)_t',
                          self._input.this).groups()
            # this turns 'unsigned_char' into 'UC' and 'float' into 'F'
            itkTypeC = ''.join([i.upper()[0] for i in g[0].split('_')])
            
            itkClassName = 'itkImageFileWriter%s%s_New' % (itkTypeC, g[1])
            print itkClassName
            itkWClass = getattr(itk, itkClassName)
            
            try:
                self._writer = itkWClass()
            except Exception, e:
                raise RuntimeError, 'Unable to instantiate ITK writer with ' \
                      'type %s and dimensions %s.' % (g[0], g[1])
            else:
                self._input.UpdateOutputInformation()
                self._input.SetBufferedRegion(
                    self._input.GetLargestPossibleRegion())
                self._input.Update()

                moduleUtilsITK.setupITKObjectProgress(
                    self, self._writer,
                    'itkImageFileWriter',
                    'Writing ITK image to disc.')
                
                self._writer.SetInput(self._input)
                self._writer.SetFileName(self._config.filename)
                self._writer.Write()

                self._writer.SetInput(None)
                self._writer = None
        
    def view(self, parent_window=None):
        self._viewFrame.Show(True)
        self._viewFrame.Raise()
