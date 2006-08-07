import genUtils
from moduleBase import moduleBase
import moduleUtils
from moduleMixins import noConfigModuleMixin
import os
import vtk

class cptDistanceField(noConfigModuleMixin, moduleBase):

    _cptDriverExe = '/home/cpbotha/build/cpt/3d/driver/driver.exe'

    def __init__(self, moduleManager):

        # call parent constructor
        moduleBase.__init__(self, moduleManager)
        noConfigModuleMixin.__init__(self)

        self._imageInput = None
        self._meshInput = None
        self._maxDistance = 5

        
        self._flipper = vtk.vtkImageFlip()
        self._flipper.SetFilteredAxis(1)
        moduleUtils.setupVTKObjectProgress(
            self, self._flipper, 'Flipping Y axis.')

        self._createViewFrame({'Module (self)' : self})
        
        self.configToLogic()
        # make sure these filter through from the bottom up
        self.logicToConfig()
        self.configToView()

    def close(self):
        # we should disconnect all inputs
        self.setInput(0, None)
        self.setInput(1, None)
        noConfigModuleMixin.close(self)

    def getInputDescriptions(self):
	return ('VTK Image', 'VTK Polydata')
    
    def setInput(self, idx, inputStream):
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
            
        
    def getOutputDescriptions(self):
	return ('Distance field (VTK Image)',)
    
    def getOutput(self, idx):
        return self._flipper.GetOutput()
    
    def logicToConfig(self):
        pass

    def configToLogic(self):
        pass

    def viewToConfig(self):
        pass

    def configToView(self):
        pass

    def executeModule(self):
        if self._imageInput and self._meshInput:

            # basename for all CPT files
            cptBaseName = os.tempnam()

            # first convert mesh data to brep
            cbw = self._moduleManager.createModule(
                'modules.Writers.cptBrepWRT')
            cbw.setInput(0, self._meshInput)
            cfg = cbw.getConfig()
            brepFilename = '%s.brep' % (cptBaseName,)
            cfg.filename = brepFilename
            cbw.setConfig(cfg)
            # we're calling it directly... propagations will propagate
            # upwards to our caller (the moduleManager) - execution
            # will be interrupted if cbw flags an error
            cbw.executeModule()

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
            geomFile.write('%d\n' % (self._maxDistance,))
            # must be signed
            geomFile.write('1\n')
            geomFile.close()

            # now we can call the driver
            os.system('%s -b -o %s %s.geom %s.brep' % \
                      (self._cptDriverExe,
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
            moduleUtils.setupVTKObjectProgress(
                self, reader, 'Reading CPT distance field output.')

            self._flipper.SetInput(reader.GetOutput())
            self._flipper.GetOutput().UpdateInformation()
            self._flipper.GetOutput().SetUpdateExtentToWholeExtent()
            self._flipper.Update()

            self._moduleManager.deleteModule(cbw)

            print "CPT Basename == %s" % (cptBaseName,)

