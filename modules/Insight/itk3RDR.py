# $Id: itk3RDR.py,v 1.1 2004/05/13 16:23:13 cpbotha Exp $

from moduleBase import moduleBase
from moduleMixins import filenameViewModuleMixin
import moduleUtilsITK
import fixitk as itk

class itk3RDR(moduleBase, filenameViewModuleMixin):
    """Reads all the 3D formats that you can write with itkWRT.  Every output
    on this module represents a different type.  Keep in mind that DeVIDE
    mostly uses the float versions of ITK components.

    At least the following file formats are available (a choice is made based
    on the filename extension that you choose):<br>
    <ul>
    <li>.mha: MetaImage all-in-one file</li>
    <li>.mhd: MetaImage .mhd header file and .raw data file</li>
    <li>.hdr or .img: Analyze .hdr header and .img data</li>
    </ul>

    $Revision: 1.1 $
    """

    _outputTypes = ['Float 3D', 'Double 3D',
                     'Signed Integer 3D', 'Unsigned Integer 3D',
                     'Signed Short 3D', 'Unsigned Short 3D',
                     'Unsigned Char 3D',
                     'Unsigned Long 3D']

    # turns the above list into ['F3', 'D3', ...] - you have to love
    # nested list expresions
    _outputTypesShort = [''.join([j[0] for j in i.split(' ')])
                         for i in _outputTypes]

    def __init__(self, moduleManager):

        # call parent constructor
        moduleBase.__init__(self, moduleManager)
        # ctor for this specific mixin
        filenameViewModuleMixin.__init__(self)

        # allocate all readers
        self._readers = []
        for outputTypeShort, outputType in zip(self._outputTypesShort,
                                               self._outputTypes):
            self._readers.append(
                getattr(itk, 'itkImageFileReader%s_New' % outputTypeShort)())

            setattr(self, '_dummyReader%d' % (len(self._readers) - 1,),
                    self._readers[-1])

            moduleUtilsITK.setupITKObjectProgress(
                self, self._readers[-1],
                'itkImageFileReader',
                'Reading ITK %s image from disc.' % outputType)

        # we now have a viewFrame in self._viewFrame
        wildCardString = 'Meta Image all-in-one (*.mha)|*.mha|' \
                         'Meta Image separate header/data (*.mhd)|*.mhd|' \
                         'Analyze separate header/data (*.hdr)|*.hdr|' \
                         'All files (*)|*'
        
        self._createViewFrame('Select a filename to load',
                              wildCardString,
                              {'Module (self)': self})

        # set up some defaults
        self._config.filename = ''
        self.configToLogic()
        # make sure these filter through from the bottom up
        self.syncViewWithLogic()
        
    def close(self):
        for i in range(len(self._readers)):
            delattr(self, '_dummyReader%d' % (i,))
            
        del self._readers
        
        filenameViewModuleMixin.close(self)

    def getInputDescriptions(self):
        return ()
    
    def setInput(self, idx, input_stream):
        raise Exception
    
    def getOutputDescriptions(self):
        return tuple(['ITK Image (%s)' % outputType
                      for outputType in self._outputTypes])
    
    def getOutput(self, idx):
        return self._readers[idx].GetOutput()

    def logicToConfig(self):
        filename = self._readers[0].GetFileName()
        if filename == None:
            filename = ''

        self._config.filename = filename

    def configToLogic(self):
        for reader in self._readers:
            reader.SetFileName(self._config.filename)

    def viewToConfig(self):
        self._config.filename = self._getViewFrameFilename()

    def configToView(self):
        self._setViewFrameFilename(self._config.filename)
    
    def executeModule(self):
        # we can't do this... 
        pass

    def view(self, parent_window=None):
        self._viewFrame.Show(True)
        self._viewFrame.Raise()

