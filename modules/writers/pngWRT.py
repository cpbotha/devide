# $Id$

from module_base import ModuleBase
from moduleMixins import scriptedConfigModuleMixin
import module_utils
import vtk
import wx # needs this for wx.OPEN, we need to make this constant available
          # elsewhere


class pngWRT(scriptedConfigModuleMixin, ModuleBase):

    def __init__(self, module_manager):

        # call parent constructor
        ModuleBase.__init__(self, module_manager)
        # ctor for this specific mixin
        # filenameViewModuleMixin.__init__(self)
	
	self._shiftScale = vtk.vtkImageShiftScale()
        self._shiftScale.SetOutputScalarTypeToUnsignedShort()

        module_utils.setupVTKObjectProgress(
            self, self._shiftScale,
            'Converting input to unsigned short.')

        
	
	self._writer = vtk.vtkPNGWriter()
	self._writer.SetFileDimensionality(3)
        self._writer.SetInput(self._shiftScale.GetOutput())
        
	module_utils.setupVTKObjectProgress(
            self, self._writer, 'Writing PNG file(s)')

        
       
        self._config.filePattern = '%d.png'

        configList = [
            ('File pattern:', 'filePattern', 'base:str', 'filebrowser',
             'Filenames will be built with this.  See module help.',
             {'fileMode' : wx.OPEN,
              'fileMask' :
              'PNG files (*.png)|*.png|All files (*.*)|*.*'})]

        scriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self,
             'vtkPNGWriter' : self._writer})
            
        self.sync_module_logic_with_config()
        
    def close(self):
	# we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)

        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)

        ModuleBase.close(self)
        
        # get rid of our reference
        del self._writer


    def get_input_descriptions(self):
	return ('vtkImageData',)
    
    def set_input(self, idx, input_stream):
        self._shiftScale.SetInput(input_stream)
    
    def get_output_descriptions(self):
	return ()
    
    def get_output(self, idx):
       	raise Exception

    def logic_to_config(self):
        self._config.filePattern = self._writer.GetFilePattern()

    def config_to_logic(self):
        self._writer.SetFilePattern(self._config.filePattern)
    
    def execute_module(self):
        if len(self._writer.GetFilePattern()) and self._shiftScale.GetInput():
            inp = self._shiftScale.GetInput()
            inp.Update()
            minv,maxv = inp.GetScalarRange()
            self._shiftScale.SetShift(-minv)
            self._shiftScale.SetScale(65535 / (maxv - minv))
            self._shiftScale.Update()
            
            
	    self._writer.Write()
            
            self._module_manager.setProgress(
                100.0, "vtkPNGWriter: Writing PNG file(s). [DONE]")

