# geodesicActiveContour.py
# $Id$

import itk
import module_kits.itk_kit as itk_kit
from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin

class tpgac(scriptedConfigModuleMixin, moduleBase):


    def __init__(self, moduleManager):

        moduleBase.__init__(self, moduleManager)
        
        # setup defaults
        self._config.propagationScaling = 1.0
        self._config.curvatureScaling = 1.0
        self._config.advectionScaling = 1.0
        self._config.numberOfIterations = 100
        
        configList = [
            ('Propagation scaling:', 'propagationScaling', 'base:float',
             'text', 'Propagation scaling parameter for the geodesic active '
             'contour, '
             'i.e. balloon force.  Positive for outwards, negative for '
             'inwards.'),
            ('Curvature scaling:', 'curvatureScaling', 'base:float',
             'text', 'Curvature scaling term weighting.'),
            ('Advection scaling:', 'advectionScaling', 'base:float',
             'text', 'Advection scaling term weighting.'),
            ('Number of iterations:', 'numberOfIterations', 'base:int',
             'text',
             'Number of iterations that the algorithm should be run for')]
        
        scriptedConfigModuleMixin.__init__(self, configList)

        # call into scriptedConfigModuleMixin method
        self._createWindow({'Module (self)' : self})

        # create all pipeline thingies
        self._createITKPipeline()

        # send config down to logic and then all the way up to the view
        self.configToLogic()
        self.logicToConfig()
        self.configToView()

    def close(self):
        self._destroyITKPipeline()
        scriptedConfigModuleMixin.close(self)
        moduleBase.close(self)

    def executeModule(self):
        self.getOutput(0).Update()
        self._moduleManager.setProgress(
            100, "Geodesic active contour complete.")

    def getInputDescriptions(self):
        return ('Feature image (ITK)', 'Initial level set (ITK)' )

    def setInput(self, idx, inputStream):
        if idx == 0:
            self._tpgac.SetFeatureImage(inputStream)
            
        else:
            self._tpgac.SetInput(inputStream)
            

    def getOutputDescriptions(self):
        return ('Final level set (ITK Float 3D)',)

    def getOutput(self, idx):
        return self._tpgac.GetOutput()

    def configToLogic(self):
        self._tpgac.SetPropagationScaling(
            self._config.propagationScaling)

        self._tpgac.SetCurvatureScaling(
            self._config.curvatureScaling)

        self._tpgac.SetAdvectionScaling(
            self._config.advectionScaling)

        self._tpgac.SetNumberOfIterations(
            self._config.numberOfIterations)

    def logicToConfig(self):
        self._config.propagationScaling = self._tpgac.\
                                          GetPropagationScaling()

        self._config.curvatureScaling = self._tpgac.\
                                        GetCurvatureScaling()

        self._config.advectionScaling = self._tpgac.\
                                        GetAdvectionScaling()

        self._config.numberOfIterations = self._tpgac.\
                                          GetNumberOfIterations()

    # --------------------------------------------------------------------
    # END OF API CALLS
    # --------------------------------------------------------------------

    def _createITKPipeline(self):
        # input: smoothing.SetInput()
        # output: thresholder.GetOutput()

        if3 = itk.Image.F3
        self._tpgac = itk.TPGACLevelSetImageFilter[if3, if3, itk.F].New()
        #geodesicActiveContour.SetMaximumRMSError( 0.1 );

        itk_kit.utils.setupITKObjectProgress(
            self, self._tpgac,
            'TPGACLevelSetImageFilter',
            'Growing active contour')
        
    def _destroyITKPipeline(self):
        """Delete all bindings to components of the ITK pipeline.
        """

        del self._tpgac
        
