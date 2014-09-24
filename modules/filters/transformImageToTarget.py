# transformImageToTarget by Francois Malan, Aug 2011
# fmalan@medvis.org

from module_base import ModuleBase
from module_mixins import ScriptedConfigModuleMixin
import module_utils
import vtk


class transformImageToTarget(ScriptedConfigModuleMixin, ModuleBase):
    def __init__(self, module_manager):
        # initialise our base class
        ModuleBase.__init__(self, module_manager)

        self._reslicer = vtk.vtkImageReslice()
        self._probefilter = vtk.vtkProbeFilter()

        self._config.paddingValue = 0.0
        
        #This is retarded - we (sometimes, see below) need the padder 
        #to get the image extent big enough to satisfy the probe filter. 
        #No apparent logical reason, but it throws an exception if we don't.
        self._padder = vtk.vtkImageConstantPad()

        configList = [
            ('Padding value:', 'paddingValue', 'base:float', 'text',
             'The value used to pad regions that are outside the supplied volume.')]        
        
        # initialise any mixins we might have
        ScriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)': self,
             'vtkImageReslice': self._reslicer,
             'vtkProbeFilter': self._probefilter,
             'vtkImageConstantPad': self._padder})

        module_utils.setup_vtk_object_progress(self, self._reslicer,
                                               'Transforming image (Image Reslice)')
        module_utils.setup_vtk_object_progress(self, self._probefilter,
                                               'Performing remapping (Probe Filter)')

        self.sync_module_logic_with_config()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have disconnected us by now)
        for input_idx in range(len(self.get_input_descriptions())):
            self.set_input(input_idx, None)
            # don't forget to call the close() method of the vtkPipeline mixin
        ScriptedConfigModuleMixin.close(self)
        # get rid of our reference
        del self._reslicer
        del self._probefilter
        del self._padder

    def get_input_descriptions(self):
        return ('Image volume that will be transformed (vtkImageData)', 'Reference that supplies extent and spacing (vtkImageData)',
                '(optional) Transform to apply to the target (vtkTransform)')

    def set_input(self, idx, inputStream):
        if idx == 0:
            self._imagedata = inputStream
            self._reslicer.SetInput(self._imagedata)
        elif idx == 1:
            if inputStream != None:
                self._outputVolumeExample = inputStream
            else:
                # define output extent same as input
                self._outputVolumeExample = self._imagedata
        else:
            if inputStream == None:
                # disconnect
                self._transform = vtk.vtkMatrix4x4()
            else:
                # resliceTransform transforms the resampling grid, which
                # is equivalent to transforming the volume with its inverse
                self._transform = inputStream.GetMatrix()
                self._transform.Invert()  #This is required

    def _convert_input(self):
        self._reslicer.SetInput(self._imagedata)
        self._reslicer.SetResliceAxes(self._transform)
        self._reslicer.SetAutoCropOutput(1)
        self._reslicer.SetInterpolationModeToCubic()
        spacing_i = self._imagedata.GetSpacing()
        isotropic_sp = min(min(spacing_i[0], spacing_i[1]), spacing_i[2])
        self._reslicer.SetOutputSpacing(isotropic_sp, isotropic_sp, isotropic_sp)
        self._reslicer.Update()

        source = self._reslicer.GetOutput()
        source_extent = source.GetExtent()
        output_extent = self._outputVolumeExample.GetExtent()

        pad_start = (0, 0, 0)
        pad_end = (0, 0, 0)
        ext_X_min = source_extent[0]
        ext_X_max = source_extent[1]
        ext_Y_min = source_extent[2]
        ext_Y_max = source_extent[3]
        ext_Z_min = source_extent[4]
        ext_Z_max = source_extent[5]

        if (output_extent[0] < source_extent[0]) or (output_extent[2] < source_extent[2]) or (
                output_extent[4] < source_extent[4]):
            ext_X_min = min(output_extent[0], source_extent[0])
            ext_Y_min = min(output_extent[2], source_extent[2])
            ext_Z_min = min(output_extent[4], source_extent[4])
            pad_start = (source_extent[0] - ext_X_min, source_extent[2] - ext_Y_min, source_extent[4] - ext_Z_min)
        if (output_extent[1] > source_extent[1]) or (output_extent[3] > source_extent[3]) or (
                output_extent[5] > source_extent[5]):
            ext_X_max = max(output_extent[1], source_extent[1])
            ext_Y_max = max(output_extent[3], source_extent[3])
            ext_Z_max = max(output_extent[5], source_extent[5])
            pad_end = (ext_X_max - source_extent[1], ext_Y_max - source_extent[3], ext_Z_max - source_extent[5])

        if (max(pad_start) > 0) or (max(pad_end) > 0):
            print 'Zero-padding source by %s voxels at start and  %s voxels at end to force extent to match/exceed ' \
                  'input''s extent. Lame, eh?' % (str(pad_start), str(pad_end))
            self._padder.SetInput(source)
            self._padder.SetConstant(0.0)
            self._padder.SetOutputWholeExtent(ext_X_min, ext_X_max, ext_Y_min, ext_Y_max, ext_Z_min, ext_Z_max)
            self._padder.Update()
            source = self._padder.GetOutput()

        #dataType = self._outputVolumeExample.GetScalarType()
        #if dataType == 2 | dataType == 4:

        output = vtk.vtkImageData()
        output.DeepCopy(self._outputVolumeExample)
        self._probefilter.SetInput(output)
        self._probefilter.SetSource(source)
        self._probefilter.Update()
        self._output = self._probefilter.GetOutput()

    def get_output_descriptions(self):
        return ('vtkImageData',)

    def get_output(self, idx):
        return self._output

    def logic_to_config(self):
        self._config.paddingValue = self._reslicer.GetBackgroundLevel()
        assert self._padder.GetConstant() == self._config.paddingValue

    def config_to_logic(self):
        self._reslicer.SetBackgroundLevel(self._config.paddingValue)
        self._padder.SetConstant(self._config.paddingValue)

    def execute_module(self):
        self._convert_input()