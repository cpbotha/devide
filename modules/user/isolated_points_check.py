# $Id: pngWRT.py 2401 2006-12-20 20:29:15Z cpbotha $

from module_base import ModuleBase
from moduleMixins import ScriptedConfigModuleMixin
import module_utils
WX_OPEN = 1
WX_SAVE = 2


class isolated_points_check(ScriptedConfigModuleMixin, ModuleBase):

    def __init__(self, module_manager):

        # call parent constructor
        ModuleBase.__init__(self, module_manager)
        # ctor for this specific mixin
        # FilenameViewModuleMixin.__init__(self)

        self._input_image = None
        self._foreground_points = None
        self._background_points = None
       
        self._config.filename = ''

        configList = [
            ('Result file name:', 'filename', 'base:str', 'filebrowser',
             'Y/N result will be written to this file.',
             {'fileMode' : WX_SAVE,
              'fileMask' :
              'All files (*.*)|*.*'})]

        ScriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self})
            
        self.sync_module_logic_with_config()
        
    def close(self):
	# we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)

        # this will take care of all display thingies
        ScriptedConfigModuleMixin.close(self)

        ModuleBase.close(self)

    def get_input_descriptions(self):
	return ('Segmented image', 'Foreground points', 'Background points')
    
    def set_input(self, idx, input_stream):
        if idx == 0:
            self._input_image = input_stream
        elif idx == 1:
            self._foreground_points = input_stream
        else:
            self._background_points = input_stream
            
    def get_output_descriptions(self):
	return ()
    
    def get_output(self, idx):
       	raise Exception

    def logic_to_config(self):
        pass

    def config_to_logic(self):
        pass
    
    def execute_module(self):
        if not hasattr(self._input_image, 'GetClassName'):
            raise RuntimeError('Input image has wrong type')

        if not hasattr(self._foreground_points, 'devideType'):
            raise RuntimeError('Wrong type foreground points')

        if not hasattr(self._background_points, 'devideType'):
            raise RuntimeError('Wrong type background points')

        if not self._config.filename:
            raise RuntimeError('Result filename not specified')

        check = True

        for j in [i['discrete'] for i in self._foreground_points]:
            v = self._input_image.GetScalarComponentAsFloat(
                * list(j + (0,)))
            if v - 0.0 < 0.0000001:
                check = False
                break

        if check:
            for j in [i['discrete'] for i in self._background_points]:
                v = self._input_image.GetScalarComponentAsFloat(
                    * list(j + (0,)))
                if v - 0.0 > 0.0000001:
                    check = False
                    break

        
        check_string = ['n', 'y'][int(check)]
            
        rf = file(self._config.filename, 'w')
        rf.write('%s\n' % (check_string,))
        rf.close()

