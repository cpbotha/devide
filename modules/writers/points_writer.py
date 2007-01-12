# $Id: vtpWRT.py 2401 2006-12-20 20:29:15Z cpbotha $

from moduleBase import moduleBase
from moduleMixins import filenameViewModuleMixin
import moduleUtils
import types

class points_writer(filenameViewModuleMixin, moduleBase):
    def __init__(self, moduleManager):

        # call parent constructor
        moduleBase.__init__(self, moduleManager)

        # ctor for this specific mixin
        filenameViewModuleMixin.__init__(
            self,
            'Select a filename',
            'DeVIDE points (*.dvp)|*.dvp|All files (*)|*',
            {'Module (self)': self},
            fileOpen=False)
            
        # set up some defaults
        self._config.filename = ''

        self._input_points = None

        self.sync_module_logic_with_config()

    def close(self):
        # we should disconnect all inputs
        self.set_input(0, None)
        filenameViewModuleMixin.close(self)

    def get_input_descriptions(self):
	return ('DeVIDE points',)
    
    def set_input(self, idx, input_stream):
        self._input_points = input_stream
    
    def get_output_descriptions(self):
	return ()
    
    def get_output(self, idx):
        raise Exception
    
    def logic_to_config(self):
        pass

    def config_to_logic(self):
        pass

    def view_to_config(self):
        self._config.filename = self._getViewFrameFilename()

    def config_to_view(self):
        self._setViewFrameFilename(self._config.filename)

    def execute_module(self):
        print self._input_points
        print type(self._input_points)
        if self._input_points and hasattr(self._input_points, 'devideType') and \
           self._input_points.devideType == 'namedPoints' \
           and self._config.filename:
            fh = file(self._config.filename, 'w')
            fh.write(str(self._input_points))
            fh.close()
            
