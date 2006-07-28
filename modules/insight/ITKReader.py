# $Id: itk3RDR.py 1957 2006-03-05 22:49:30Z cpbotha $

import itk
import module_kits.itk_kit as itk_kit
from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import wx

class ITKReader(scriptedConfigModuleMixin, moduleBase):
    def __init__(self, moduleManager):
        # call parent constructor
        moduleBase.__init__(self, moduleManager)

        self._config.filename = ''
        self._config.autotype = True
        self._config.type = 'float'
        self._config.dimensionality = '3'

        wild_card_string = 'Meta Image all-in-one (*.mha)|*.mha|' \
                         'Meta Image separate header/data (*.mhd)|*.mhd|' \
                         'Analyze separate header/data (*.hdr)|*.hdr|' \
                         'All files (*)|*'
        config_list = [
            ('Filename:', 'filename', 'base:str', 'filebrowser',
             'Name of file that will be loaded.',
             {'fileMode' : wx.OPEN, 'fileMask' : wild_card_string}),
            ('AutoType:', 'autotype', 'base:bool', 'checkbox',
             'If activated, data type and dimensions will be determined '
             'automatically.'),
            ('Data type:', 'type', 'base:str', 'choice',
             'Data will be cast to this type if AutoType is not used.',
             ['float', 'unsigned char', 'unsigned long']),
            ('Data dimensionality:', 'dimensionality', 'base:str', 'choice',
             'Data will be read using this number of dimensions if AutoType '
             'is not used', ['2','3'])]


        scriptedConfigModuleMixin.__init__(self, config_list)

        # create ImageFileReader we'll be using for autotyping
        self._autotype_reader = itk.ImageFileReader[itk.Image.F3].New()

        itk_kit.utils.setupITKObjectProgress(
            self, self._autotype_reader, 'ImageFileReader',
            'Determining type and dimensionality of file.')

        # and create default ImageFileReader we'll use for the actual lifting
        self._reader = itk.ImageFileReader[itk.Image.F3].New()
        self._reader_type = 'F'
        self._reader_dim = 3

        itk_kit.utils.setupITKObjectProgress(
            self, self._reader, 'ImageFileReader',
            'Reading file.')

        self._createWindow(
            {'Module (self)' : self})

        self.configToLogic()
        self.logicToConfig()
        self.configToView()
        
        
    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)

        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)
        # and the baseclass close
        moduleBase.close(self)
            
        # and remove all bindings
        del self._autotype_reader
        del self._reader

    def getInputDescriptions(self):
        return ()
    
    def setInput(self, idx, input_stream):
        raise Exception
    
    def getOutputDescriptions(self):
        return ('ITK Image',)
    
    def getOutput(self, idx):
        return self._reader.GetOutput()

    def logicToConfig(self):
        # important to return False: logicToConfig can't change and
        # hasn't changed our config
        return False

    def configToLogic(self):
        # important to return False: logicToConfig can't change and
        # hasn't changed our internal state
        return False

    def executeModule(self):
        if self._config.autotype:
            self._autotype_reader.SetFileName(self._config.filename)
            self._autotype_reader.UpdateOutputInformation()
            iio = self._autotype_reader.GetImageIO()
            comp_type = iio.GetComponentTypeAsString(iio.GetComponentType())
            if comp_type == 'short':
                comp_type = 'signed_short'
            # lc will convert e.g. unsigned_char to UC
            short_type = ''.join([i[0].upper() for i in comp_type.split('_')])
            print comp_type, short_type
            dim = iio.GetNumberOfDimensions()

        else:
            # lc will convert e.g. unsigned char to UC
            comp_type = self._config.type
            short_type = ''.join([i[0].upper() for i in comp_type.split(' ')])
            dim = self._config.dimensionality

        # if things have changed, make a new reader, else re-use the old
        if short_type != self._reader_type or dim != self._reader_dim:
            # equivalent to e.g. itk.Image.UC3
            self._reader = itk.ImageFileReader[
                getattr(itk.Image, '%s%s' % (short_type, dim))].New()
            self._reader_type = short_type
            self._reader_dim = dim
                
            itk_kit.utils.setupITKObjectProgress(
                self, self._reader, 'ImageFileReader',
                'Reading file.')

        # now do the actual reading

        self._reader.SetFileName(self._config.filename)
        self._reader.Update()
