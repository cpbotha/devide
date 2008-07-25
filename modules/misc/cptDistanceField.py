import gen_utils
from module_base import ModuleBase
import module_utils
import module_mixins
from module_mixins import ScriptedConfigModuleMixin
import os
import vtk

class cptDistanceField(ScriptedConfigModuleMixin, ModuleBase):

    def __init__(self, module_manager):

        # call parent constructor
        ModuleBase.__init__(self, module_manager)
        

        self._imageInput = None
        self._meshInput = None

        
        self._flipper = vtk.vtkImageFlip()
        self._flipper.SetFilteredAxis(1)
        module_utils.setupVTKObjectProgress(
            self, self._flipper, 'Flipping Y axis.')

        self._config.cpt_driver_path = \
                'd:\\misc\\stuff\\driver.bat'
            #'/home/cpbotha/build/cpt/3d/driver/driver.exe'
        self._config.max_distance = 5

        config_list = [
                ('CPT driver path', 'cpt_driver_path',
                'base:str', 'filebrowser', 
                'Path to CPT driver executable',
                {'fileMode' : module_mixins.wx.OPEN,
                 'fileMask' : 'All files (*.*)|*.*'}), 
                ('Maximum distance', 'max_distance', 
                'base:float', 'text', 
                'The maximum (absolute) distance up to which the field is computed.')]

        ScriptedConfigModuleMixin.__init__(
            self, config_list,
            {'Module (self)' : self})
            
        self.sync_module_logic_with_config()
        
    def close(self):
        # we should disconnect all inputs
        self.set_input(0, None)
        self.set_input(1, None)
        ScriptedConfigModuleMixin.close(self)

    def get_input_descriptions(self):
        return ('VTK Image', 'VTK Polydata')
    
    def set_input(self, idx, inputStream):
        if idx == 0:
            try:
                if inputStream == None or inputStream.IsA('vtkImageData'):
                    self._imageInput = inputStream
                else:
                    raise TypeError
                
            except (TypeError, AttributeError):
                raise TypeError, 'This input requires a vtkImageData.'
                
        else:
            try:
                if inputStream == None or inputStream.IsA('vtkPolyData'):
                    self._meshInput = inputStream
                else:
                    raise TypeError
                
            except (TypeError, AttributeError):
                raise TypeError, 'This input requires a vtkPolyData.'
            
        
    def get_output_descriptions(self):
        return ('Distance field (VTK Image)',)
    
    def get_output(self, idx):
        return self._flipper.GetOutput()
    
    def logic_to_config(self):
        pass

    def config_to_logic(self):
        pass

    def execute_module(self):
        if self._imageInput and self._meshInput:

            # basename for all CPT files
            cptBaseName = os.tempnam()

            # first convert mesh data to brep
            cbw = self._module_manager.createModule(
                'modules.writers.cptBrepWRT')
            cbw.set_input(0, self._meshInput)
            cfg = cbw.get_config()
            brepFilename = '%s.brep' % (cptBaseName,)
            cfg.filename = brepFilename
            cbw.set_config(cfg)
            # we're calling it directly... propagations will propagate
            # upwards to our caller (the ModuleManager) - execution
            # will be interrupted if cbw flags an error
            cbw.execute_module()

            # now let's write the geom file
            self._imageInput.UpdateInformation()
            b = self._imageInput.GetBounds()
            d = self._imageInput.GetDimensions()

            geomFile = file('%s.geom' % (cptBaseName,), 'w')
            # bounds
            geomFile.write('%f %f %f %f %f %f\n' % (b[0], b[2], b[4],
                                                    b[1], b[3], b[5]))
            # dimensions
            geomFile.write('%d %d %d\n' % (d[0], d[1], d[2]))
            # maximum distance
            geomFile.write('%d\n' % (self._config.max_distance,))
            # must be signed
            geomFile.write('1\n')
            geomFile.close()

            # now we can call the driver
            os.system('%s -b -o %s %s.geom %s.brep' % \
                      (self._config.cpt_driver_path,
                       cptBaseName, cptBaseName, cptBaseName))

            # we should have cptBaseName.dist waiting...
            reader = vtk.vtkImageReader()
            reader.SetFileName('%s.dist' % (cptBaseName,))
            reader.SetFileDimensionality(3)
            reader.SetDataScalarType(vtk.VTK_DOUBLE)
            # 3 doubles in header
            reader.SetHeaderSize(24)
            reader.SetDataExtent(self._imageInput.GetWholeExtent())
            reader.SetDataSpacing(self._imageInput.GetSpacing())
            module_utils.setupVTKObjectProgress(
                self, reader, 'Reading CPT distance field output.')

            self._flipper.SetInput(reader.GetOutput())
            self._flipper.GetOutput().UpdateInformation()
            self._flipper.GetOutput().SetUpdateExtentToWholeExtent()
            self._flipper.Update()

            self._module_manager.deleteModule(cbw)

            print "CPT Basename == %s" % (cptBaseName,)

