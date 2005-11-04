# $Id: distanceMap.py,v 1.2 2005/11/04 10:34:55 cpbotha Exp $

import fixitk as itk
from moduleBase import moduleBase
import moduleUtilsITK
from moduleMixins import scriptedConfigModuleMixin

class distanceMap(scriptedConfigModuleMixin, moduleBase):

    """
    $Revision: 1.2 $
    """

    def __init__(self, moduleManager):

        moduleBase.__init__(self, moduleManager)
        
        # setup defaults
        self._config.useImageSpacing = False
        self._config.squaredDistance = False
        
        configList = [
            ('Use image spacing:', 'useImageSpacing', 'base:bool',
             'checkbox', 'Use image spacing in distance calculation.'),
            ('Calculate squared distance:', 'squaredDistance', 'base:bool',
             'checkbox', 'Calculate squared distance instead of distance.')
            ]
        
        scriptedConfigModuleMixin.__init__(self, configList)

        # create all pipeline thingies
        self._ddmif = itk.itkDanielssonDistanceMapImageFilterF3F3_New()
        moduleUtilsITK.setupITKObjectProgress(
            self, self._ddmif,
            'itkDanielssonDistanceMapImageFilter',
            'Calculating distance map.')

        # call into scriptedConfigModuleMixin method
        self._createWindow(
            {'Module (self)' : self,
             'itkDanielssonDistanceMapImageFilter' : self._ddmif})


        # send config down to logic and then all the way up to the view
        self.configToLogic()
        self.logicToConfig()
        self.configToView()

    def close(self):
        del self._ddmif
        scriptedConfigModuleMixin.close(self)
        moduleBase.close(self)

    def executeModule(self):
        self.getOutput(0).Update()

    def getInputDescriptions(self):
        return ('Input image (ITK)', )

    def setInput(self, idx, inputStream):
        self._ddmif.SetInput(inputStream)

    def getOutputDescriptions(self):
        return ('Distance field (ITK Float 3D)',)

    def getOutput(self, idx):
        return self._ddmif.GetOutput()

    def configToLogic(self):
        self._ddmif.SetSquaredDistance(self._config.squaredDistance)
        self._ddmif.SetUseImageSpacing(self._config.useImageSpacing)

    def logicToConfig(self):
        self._config.squaredDistance = bool(self._ddmif.GetSquaredDistance())
        self._config.useImageSpacing = bool(self._ddmif.GetUseImageSpacing())

