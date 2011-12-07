from module_base import ModuleBase
from module_mixins import NoConfigModuleMixin
import module_utils
import vtk

class transformImageToTarget(NoConfigModuleMixin, ModuleBase):
    def __init__(self, module_manager):
        # initialise our base class
        ModuleBase.__init__(self, module_manager)

        self._reslicer = vtk.vtkImageReslice()        
        self._probefilter = vtk.vtkProbeFilter()
        
        #This is retarded - we (sometimes, see below) need the padder 
        #to get the image extent big enough to satisfy the probe filter. 
        #No apparent logical reason, but it throws an exception if we don't.
        self._padder = vtk.vtkImageConstantPad()
        
        # initialise any mixins we might have
        NoConfigModuleMixin.__init__(
            self,
            {'Module (self)' : self,
             'vtkImageReslice' : self._reslicer})

        module_utils.setup_vtk_object_progress(self, self._reslicer,
                                           'Transforming image (Image Reslice)')
        module_utils.setup_vtk_object_progress(self, self._probefilter,
                                           'Performing remapping (Probe Filter)')

        self.sync_module_logic_with_config()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # Rdisconnected us by now)
        for input_idx in range(len(self.get_input_descriptions())):
            self.set_input(input_idx, None)
        # don't forget to call the close() method of the vtkPipeline mixin
        NoConfigModuleMixin.close(self)
        # get rid of our reference
        del self._reslicer
        del self._probefilter
        del self._padder

    def get_input_descriptions(self):
        return ('Source VTK Image Data', 'VTK Transform', 'Target VTK Image (supplies extent and spacing)')

    def set_input(self, idx, inputStream):
        if idx == 0:
            self._imagedata = inputStream
            self._reslicer.SetInput(self._imagedata)
        elif idx == 1:
            if inputStream == None:
                # disconnect
                self._transform = vtk.vtkMatrix4x4()
            else:
                # resliceTransform transforms the resampling grid, which
                # is equivalent to transforming the volume with its inverse
                self._transform = inputStream.GetMatrix()
                self._transform.Invert()  #This is required
        else:
            if inputStream != None:
                self._outputVolumeExample = inputStream
            else:
                # define output extent same as input
                self._outputVolumeExample = self._imagedata

    def _convert_input(self):
        self._reslicer.SetInput(self._imagedata)
        self._reslicer.SetResliceAxes(self._transform)        
        self._reslicer.SetAutoCropOutput(1)        
        self._reslicer.SetInterpolationModeToCubic()
        spacing_i = self._imagedata.GetSpacing()
        isotropic_sp = min(min(spacing_i[0],spacing_i[1]),spacing_i[2])
        self._reslicer.SetOutputSpacing(isotropic_sp, isotropic_sp, isotropic_sp)
        self._reslicer.Update()
        
        source = self._reslicer.GetOutput()
        source_extent = source.GetExtent()
        output_extent = self._outputVolumeExample.GetExtent()
        
        if (output_extent[0] < source_extent[0]) or (output_extent[2] < source_extent[2]) or (output_extent[4] < source_extent[4]):
            raise Exception('Output extent starts at lower index than source extent. Assumed that both should be zero?')
        elif (output_extent[1] > source_extent[1]) or (output_extent[3] > source_extent[3]) or (output_extent[5] > source_extent[5]):
            extX = max(output_extent[1], source_extent[1])
            extY = max(output_extent[3], source_extent[3])
            extZ = max(output_extent[5], source_extent[5])            
            padX = extX - source_extent[1]
            padY = extY - source_extent[3]
            padZ = extZ - source_extent[5]            
            print 'Zero-padding source by (%d, %d, %d) voxels to force extent to match/exceed input''s extent. Lame, eh?' % (padX, padY, padZ)            
            self._padder.SetInput(source)
            self._padder.SetConstant(0.0)
            self._padder.SetOutputWholeExtent(source_extent[0],extX,source_extent[2],extY,source_extent[4],extZ)
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
        pass

    def config_to_logic(self):
        pass
    

    def view_to_config(self):
        pass

    def config_to_view(self):
        pass
    
    def execute_module(self):
        self._convert_input()