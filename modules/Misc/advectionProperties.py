#
#
#

from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtk
import wx

class advectionProperties(scriptedConfigModuleMixin, moduleBase):
    """Given a series of prepared advection volumes (each input is a
    timestep), calculate a number of metrics.

    $Revision: 1.1 $
    """

    _numberOfInputs = 10

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        self._config.csvFilename = ''

        configList = [
            ('CSV Filename:', 'csvFilename', 'base:str', 'filebrowser',
             'Filename Comma-Separated-Values file that will be written.',
             {'fileMode' : wx.SAVE,
              'fileMask' : 'CSV files (*.csv)|*.csv|All files (*.*)|*.*'})]
        
        scriptedConfigModuleMixin.__init__(self, configList)

        self._inputs = [None] * self._numberOfInputs
        
        #moduleUtils.setupVTKObjectProgress(self, self._warpVector,
        #                                   'Warping points.')

        self._createWindow(
            {'Module (self)' : self})

        # pass the data down to the underlying logic
        self.configToLogic()
        # and all the way up from logic -> config -> view to make sure
        self.syncViewWithLogic()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)

        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)
        
        # get rid of any references
        

    def executeModule(self):
        # inputs are arranged according to timesteps (presumably)
        # things have been marked with a VolumeIndex array

        # find valid inputs with VolumeIndex scalars
        newInputs = [i for i in self._inputs if i != None and
                     i.GetPointData().GetScalars('VolumeIndex') != None]

        [i.GetPointData().SetActiveScalars('VolumeIndex') for i in newInputs]

        # this will contain a dictionary of each timestep
        # where each dictionary will contain a number of lists containing
        # points belonging to each VolumeIndex
        allPointsList = []

        # extract lists of points!
        for tipt in newInputs:
            tiptDict = {}
            
            vis = tipt.GetPointData().GetScalars('VolumeIndex')
            # go through all points in this tipt
            for ptid in xrange(tipt.GetNumberOfPoints()):
                pt = tipt.GetPoint(ptid)
                vidx = vis.GetTuple1(ptid)

                if vidx >= 0:
                    if vidx in tiptDict:
                        tiptDict[vidx].append(ptid)
                    else:
                        tiptDict[vidx] = [ptid]

            allPointsList.append(tiptDict)

        
                

    def getInputDescriptions(self):
        return ('vtkPolyData with VolumeIndex attribute',) * \
               self._numberOfInputs

    def setInput(self, idx, inputStream):
        validInput = False
        
        try:
            if inputStream.GetClassName() == 'vtkPolyData':
                validInput = True
        except:
            # we come here if GetClassName() is not callable (or doesn't
            # exist) - but things could still be None
            if inputStream == None:
                validInput = True

        if validInput:
            self._inputs[idx] = inputStream
        else:
            raise TypeError, 'This input requires a vtkPolyData.'

    def getOutputDescriptions(self):
        return ()

    def getOutput(self, idx):
        raise Exception

    def logicToConfig(self):
        pass
    
    def configToLogic(self):
        pass
