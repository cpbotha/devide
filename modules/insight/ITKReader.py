# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

import copy
import itk
import module_kits.itk_kit as itk_kit
from module_base import ModuleBase
from moduleMixins import scriptedConfigModuleMixin
import wx

class ITKReader(scriptedConfigModuleMixin, ModuleBase):
    def __init__(self, moduleManager):
        # call parent constructor
        ModuleBase.__init__(self, moduleManager)

        self._config.filename = ''
        self._config.autotype = True
        self._config.type = 'float'
        self._config.dimensionality = '3'

        self._logic = copy.deepcopy(self._config)
        # we change this one ivar so that config_to_logic will return True
        # the first time
        self._logic.filename = None

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
             ['float', 'signed short', 'unsigned long']),
            ('Data dimensionality:', 'dimensionality', 'base:str', 'choice',
             'Data will be read using this number of dimensions if AutoType '
             'is not used', ['2','3'])]




        # create ImageFileReader we'll be using for autotyping
        self._autotype_reader = itk.ImageFileReader[itk.Image.F3].New()

        itk_kit.utils.setupITKObjectProgress(
            self, self._autotype_reader, 'ImageFileReader',
            'Determining type and dimensionality of file.')

        # and create default ImageFileReader we'll use for the actual lifting
        self._reader = itk.ImageFileReader[itk.Image.F3].New()
        self._reader_type_text = 'F3'

        itk_kit.utils.setupITKObjectProgress(
            self, self._reader, 'ImageFileReader',
            'Reading file.')

        scriptedConfigModuleMixin.__init__(self, config_list,
                                           {'Module (self)' : self})

        self.sync_module_logic_with_config()
        
    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)

        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)
        # and the baseclass close
        ModuleBase.close(self)
            
        # and remove all bindings
        del self._autotype_reader
        del self._reader

    def get_input_descriptions(self):
        return ()
    
    def set_input(self, idx, input_stream):
        raise Exception
    
    def get_output_descriptions(self):
        return ('ITK Image',)
    
    def get_output(self, idx):
        return self._reader.GetOutput()

    def logic_to_config(self):
        # important to return False: logic_to_config can't and
        # hasn't changed our config
        return False

    def config_to_logic(self):
        # if the user has performed an 'Apply', we want to invalidate
        return True

    def execute_module(self):
        if self._config.autotype:
            self._autotype_reader.SetFileName(self._config.filename)
            self._autotype_reader.UpdateOutputInformation()
            iio = self._autotype_reader.GetImageIO()
            comp_type = iio.GetComponentTypeAsString(iio.GetComponentType())
            if comp_type == 'short':
                comp_type = 'signed_short'
            # lc will convert e.g. unsigned_char to UC
            short_type = ''.join([i[0].upper() for i in comp_type.split('_')])
            dim = iio.GetNumberOfDimensions()
            num_comp = iio.GetNumberOfComponents()

        else:
            # lc will convert e.g. unsigned char to UC
            comp_type = self._config.type
            short_type = ''.join([i[0].upper() for i in comp_type.split(' ')])
            if short_type == 'S':
                short_type = 'SS'

            dim = self._config.dimensionality
            num_comp = 1

        # e.g. F3
        reader_type_text = '%s%d' % (short_type, dim)
        if num_comp > 1:
            # e.g. VF33
            reader_type_text = 'V%s%d' % (reader_type_text, num_comp)

        # if things have changed, make a new reader, else re-use the old
        if reader_type_text != self._reader_type_text:
            # equivalent to e.g. itk.Image.UC3
            self._reader = itk.ImageFileReader[
                getattr(itk.Image, reader_type_text)].New()
            self._reader_type_text = reader_type_text
            print reader_type_text
                
            itk_kit.utils.setupITKObjectProgress(
                self, self._reader, 'ImageFileReader',
                'Reading file.')

        # now do the actual reading

        self._reader.SetFileName(self._config.filename)
        self._reader.Update()
