import genUtils
from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
import moduleUtils
import vtk

class probeFilter(noConfigModuleMixin, moduleBase):
    """
    Maps source values onto input dataset.

    Input can be e.g. polydata and source a volume, in which case interpolated
    values from the volume will be mapped on the vertices of the polydata,
    i.e. the interpolated values will be associated as the attributes of the
    polydata points.

    $Revision: 1.4 $
    """

    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)
        noConfigModuleMixin.__init__(self)

        # what a lame-assed filter, we have to make dummy inputs!
        # if we don't have a dummy input (but instead a None input) it
        # bitterly complains when we do a GetOutput() (it needs the input
        # to know the type of the output) - and GetPolyDataOutput() also
        # doesn't work.
        # NB: this does mean that our probeFilter NEEDS a PolyData as
        # probe geometry!
        ss = vtk.vtkSphereSource()
        ss.SetRadius(0)
        self._dummyInput = ss.GetOutput()
        
        self._probeFilter = vtk.vtkProbeFilter()
        self._probeFilter.SetInput(self._dummyInput)

        moduleUtils.setupVTKObjectProgress(self, self._probeFilter,
                                           'Mapping source on input')

        self._viewFrame = self._createViewFrame(
            {'Module (self)' : self,
             'vtkProbeFilter' : self._probeFilter})

        # pass the data down to the underlying logic
        self.configToLogic()
        # and all the way up from logic -> config -> view to make sure
        self.logicToConfig()
        self.configToView()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)

        # this will take care of all display thingies
        noConfigModuleMixin.close(self)
        
        # get rid of our reference
        del self._probeFilter
        del self._dummyInput

    def getInputDescriptions(self):
        return ('Input', 'Source')

    def setInput(self, idx, inputStream):
        if idx == 0:
            if inputStream == None:
                # we don't really disconnect, we just reset the dummy
                # input...
                self._probeFilter.SetInput(self._dummyInput)
            else:
                self._probeFilter.SetInput(inputStream)

        else:
            self._probeFilter.SetSource(inputStream)

    def getOutputDescriptions(self):
        return ('Input with mapped source values',)

    def getOutput(self, idx):
        return self._probeFilter.GetOutput()

    def logicToConfig(self):
        pass
    
    def configToLogic(self):
        pass
    
    def viewToConfig(self):
        pass

    def configToView(self):
        pass
    
    def executeModule(self):
        self._probeFilter.Update()

        
