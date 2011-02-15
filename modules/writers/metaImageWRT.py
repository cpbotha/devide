# $Id$

from module_base import ModuleBase
from module_mixins import ScriptedConfigModuleMixin
import module_utils
import vtk
import wx # need this for wx.SAVE


class metaImageWRT(ScriptedConfigModuleMixin, ModuleBase):
    def __init__(self, module_manager):

        # call parent constructor
        ModuleBase.__init__(self, module_manager)

        self._writer = vtk.vtkMetaImageWriter()

        module_utils.setup_vtk_object_progress(
            self, self._writer,
            'Writing VTK ImageData')

        # set up some defaults
        self._config.filename = ''
        self._config.compression = True

        config_list = [
                ('Filename:', 'filename', 'base:str', 'filebrowser',
                    'Output filename for MetaImage file.',
                    {'fileMode' : wx.SAVE,
                     'fileMask' : 'MetaImage single file (*.mha)|*.mha|MetaImage separate header/(z)raw files (*.mhd)|*.mhd|All files (*)|*',
                     'defaultExt' : '.mha'}
                    ),
                ('Compression:', 'compression', 'base:bool', 'checkbox',
                    'Compress the image / volume data')
                ]

        ScriptedConfigModuleMixin.__init__(self, config_list,
                {'Module (self)' : self})

       
    def close(self):
        # we should disconnect all inputs
        self.set_input(0, None)
        del self._writer
       
        # deinit our mixins
        ScriptedConfigModuleMixin.close(self)
        ModuleBase.close(self)

    def get_input_descriptions(self):
        return ('vtkImageData',)
    
    def set_input(self, idx, input_stream):
        self._writer.SetInput(input_stream)
    
    def get_output_descriptions(self):
        return ()
    
    def get_output(self, idx):
        raise Exception
    
    def logic_to_config(self):
        filename = self._writer.GetFileName()
        if filename == None:
            filename = ''

        self._config.filename = filename

        self._config.compression = self._writer.GetCompression()

    def config_to_logic(self):
        self._writer.SetFileName(self._config.filename)
        self._writer.SetCompression(self._config.compression)


    def execute_module(self):
        if self._writer.GetFileName() and self._writer.GetInput():
            self._writer.GetInput().UpdateInformation()
            self._writer.GetInput().SetUpdateExtentToWholeExtent()
            self._writer.GetInput().Update()
            self._writer.Write()

    def streaming_execute_module(self):
        if self._writer.GetFileName() and self._writer.GetInput():
            # if you use Update(), everything crashes (VTK 5.6.1, Ubuntu 10.04 x86_64)
            self._writer.Write()


