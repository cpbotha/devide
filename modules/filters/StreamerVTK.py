from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
import moduleUtils
import vtk

IMAGE_DATA = 0
POLY_DATA = 1

class StreamerVTK(noConfigModuleMixin, moduleBase):
    def __init__(self, module_manager):
        moduleBase.__init__(self, module_manager)

        self._image_data_streamer = vtk.vtkImageDataStreamer()
        self._poly_data_streamer = vtk.vtkPolyDataStreamer()

        noConfigModuleMixin.__init__(self, 
                {'module (self)' : self,
                 'vtkImageDataStreamer' : self._image_data_streamer,
                 'vtkPolyDataStreamer' : self._poly_data_streamer})

        moduleUtils.setupVTKObjectProgress(self,
                self._image_data_streamer, 'Streaming image data')

        self._current_mode = None

        self.sync_module_logic_with_config()


    def close(self):
        noConfigModuleMixin.close(self)
        del self._image_data_streamer
        del self._poly_data_streamer

    def get_input_descriptions(self):
        return ('VTK image or poly data',)

    def set_input(self, idx, input_stream):
        if hasattr(input_stream, 'IsA'):
            if input_stream.IsA('vtkImageData'):
                self._image_data_streamer.SetInput(input_stream)
                self._current_mode = IMAGE_DATA
            elif input_stream.IsA('vtkPolyData'):
                self._poly_data_streamer.SetInput(input_stream)
                self._current_mode = POLY_DATA


    def get_output_descriptions(self):
        return('VTK image or poly data',)

    def get_output(self, idx):
        if self._current_mode == IMAGE_DATA:
            return self._image_data_streamer.GetOutput()

        elif self._current_mode == POLY_DATA:
            return self._poly_data_streamer.GetOutput()

        else:
            return None

    def execute_module(self):
        pass

    def streaming_execute_module(self):
        sp = self._moduleManager.get_app_main_config().streaming_pieces
        if self._current_mode == IMAGE_DATA:
            self._image_data_streamer.SetNumberOfStreamDivisions(sp)
            self._image_data_streamer.Update()
        elif self._current_mode == POLY_DATA:
            self._poly_data_streamer.SetNumberOfStreamDivisions(sp)
            self._poly_data_streamer.Update()

    

