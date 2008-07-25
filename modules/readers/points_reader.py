# $Id: vtpWRT.py 2401 2006-12-20 20:29:15Z cpbotha $

from module_base import ModuleBase
from moduleMixins import filenameViewModuleMixin
import moduleUtils
import types
from modules.viewers.slice3dVWRmodules.selectedPoints import outputSelectedPoints

class points_reader(filenameViewModuleMixin, ModuleBase):
    def __init__(self, moduleManager):

        # call parent constructor
        ModuleBase.__init__(self, moduleManager)

        # ctor for this specific mixin
        filenameViewModuleMixin.__init__(
            self,
            'Select a filename',
            'DeVIDE points (*.dvp)|*.dvp|All files (*)|*',
            {'Module (self)': self},
            fileOpen=True)
            
        # set up some defaults
        self._config.filename = ''

        self._output_points = None

        self.sync_module_logic_with_config()

    def close(self):
        filenameViewModuleMixin.close(self)

    def get_input_descriptions(self):
	return ()
    
    def set_input(self, idx, input_stream):
        raise NotImplementedError
    
    def get_output_descriptions(self):
	return ('DeVIDE points',)
    
    def get_output(self, idx):
        return self._output_points
    
    def logic_to_config(self):
        pass

    def config_to_logic(self):
        pass

    def view_to_config(self):
        self._config.filename = self._getViewFrameFilename()

    def config_to_view(self):
        self._setViewFrameFilename(self._config.filename)

    def execute_module(self):
        if self._config.filename:
            fh = file(self._config.filename)
            ltext = fh.read()
            fh.close()
            points_list = eval(ltext)
            self._output_points = outputSelectedPoints()
            self._output_points.extend(points_list)

            
