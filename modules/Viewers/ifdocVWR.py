# ifdocVWR copyright (c) 2003 by Charl P. Botha cpbotha@ieee.org
# $Id: ifdocVWR.py,v 1.2 2003/09/20 22:22:34 cpbotha Exp $
# module to interact with the ifdoc shoulder model

# TODO:
# * connect observer to self._mData, update INTERNAL matrix forms
#   when it notifies... that way, doTimeStep doesn't have to parse the whole
#   frikking matrix everytime.

from genMixins import subjectMixin
from moduleBase import moduleBase
import moduleUtils
import os
import time
import vtk
from wxPython.wx import *

# named World points TEMPORARY
class outputPoints(dict, subjectMixin):
    """Class that we can use (temporarily) to let the sliceViewer visualise
    some of our points.
    """

    def __init__(self, *argv):
        dict.__init__(self, *argv)
        subjectMixin.__init__(self)
        # so the sliceVWR will know what to do with us (I hope)
        self.d3type = 'namedWorldPoints'

    def close(self):
        subjectMixin.close(self)
    

class ifdocVWR(moduleBase):

    _numInputs = 1

    def __init__(self, moduleManager):
        # base constructor
        moduleBase.__init__(self, moduleManager)

        # one of our input datas
        self._mData = None

        # temporary output
        self._outputPoints = outputPoints()

        self._createViewFrames()
        self._bindEvents()

        # temporary
        self._buildPipeline()

    def close(self):
        for i in range(self._numInputs):
            self.setInput(i, None)

        # call close method of base class
        moduleBase.close(self)

        # get rid of all the refs we carry
        del self._mData

        # we should be able to take care of our renderwindow now
        # we have to do this nasty trick until my Finalize changes are
        # implemented in all vtkRenderWindow types
        self._threedRenderer.RemoveAllProps()
        del self._threedRenderer
        self.viewerFrame.threedRWI.GetRenderWindow().WindowRemap()
        self.viewerFrame.Destroy()
        del self.viewerFrame
        # also take care of the controlFrame
        self.controlFrame.Destroy()
        del self.controlFrame

    def getInputDescriptions(self):
        return ('ifdoc m-Data',)

    def setInput(self, idx, inputStream):
        # don't forget to register as an observer
        self._mData = inputStream

        if self._mData != None:
            self._mData.Update()
            
            self.doTimeStep(0)
            self.updateRender()
            self._threedRenderer.ResetCamera()

            # setup the slider
            # number of timeSteps == columns
            timeSteps = len(self._mData.ppos)

            # setup UI
            self.controlFrame.timeStepSlider.SetRange(0, timeSteps - 1)
            self.controlFrame.timeStepSlider.SetValue(0)
            self.controlFrame.timeStepSpinCtrl.SetRange(0, timeSteps - 1)
            self.controlFrame.timeStepSpinCtrl.SetValue(0)

            # and setup our outputpoints (just the first timestep; temp)
            self._outputPoints.clear()
            timeStep = self._mData.ppos[0]
            for key in timeStep:
                self._outputPoints[key] = timeStep[key]

    def getOutputDescriptions(self):
        return ('namedWorldPoints',)

    def getOutput(self, idx):
        #raise Exception
        return self._outputPoints

    def logicToConfig(self):
        """Synchronise internal configuration information (usually
        self._config)with underlying system.
        """
        pass
    
    def configToLogic(self):
        """Apply internal configuration information (usually self._config) to
        the underlying logic.
        """
        pass

    def viewToConfig(self):
        """Synchronise internal configuration information with the view (GUI)
        of this module.

        """
        pass
        
    
    def configToView(self):
        """Make the view reflect the internal configuration information.

        """
        pass
    
    def executeModule(self):
        # we could call animate if the user does an execute
        pass
            
    def view(self, parent_window=None):
        # if the window is already visible, raise it
        if not self.viewerFrame.Show(True):
            self.viewerFrame.Raise()

        if not self.controlFrame.Show(True):
            self.controlFrame.Raise()

    # ----------------------------------------------------------------------
    # non-API methods start here -------------------------------------------
    # ----------------------------------------------------------------------

    def _autoAnimate(self):
        """Animate all time steps.
        """

        # make sure our data is up to date
        self._mData.Update()
        if self._mData:
            ppos =  self._mData.ppos

            # timesteps are columns of ppos
            timeSteps = len(ppos)

            for timeStep in range(timeSteps):
                self.updateRender()
                wxSafeYield()
                self.doTimeStep(timeStep)
                time.sleep(0.2)

            time.sleep(0.5)
            self.doTimeStep(0)
            wxSafeYield()
            self.updateRender()

    def _bindEvents(self):
        """Bind events to wxPython GUI elements.
        """

        EVT_BUTTON(self.viewerFrame, self.viewerFrame.showControlsButtonId,
                   self._handlerShowControls)

        EVT_BUTTON(self.controlFrame, self.controlFrame.autoAnimateButtonId,
                   self._handlerAutoAnimate)

        EVT_COMMAND_SCROLL(
            self.controlFrame, self.controlFrame.timeStepSliderId,
            self._handlerTimeStepSlider)
    
    def _createViewFrames(self):

        # create the viewerFrame
        import modules.Viewers.resources.python.ifdocVWRFrames
        reload(modules.Viewers.resources.python.ifdocVWRFrames)

        viewerFrame = \
                    modules.Viewers.resources.python.ifdocVWRFrames.viewerFrame

        self.viewerFrame = moduleUtils.instantiateModuleViewFrame(
            self, self._moduleManager, viewerFrame)
        
        # add the renderer
        self._threedRenderer = vtk.vtkRenderer()
        self._threedRenderer.SetBackground(0.5, 0.5, 0.5)
        self.viewerFrame.threedRWI.GetRenderWindow().AddRenderer(
            self._threedRenderer)
        
        # controlFrame creation and basic setup -------------------
        controlFrame = modules.Viewers.resources.python.ifdocVWRFrames.\
                       controlFrame

        self.controlFrame = moduleUtils.instantiateModuleViewFrame(
            self, self._moduleManager, controlFrame)
                
        # display the window
        self.viewerFrame.Show(True)
        self.controlFrame.Show(True)


    def _buildPipeline(self):
        # this is temporary
        self._appendPolyData = vtk.vtkAppendPolyData()

        self._lineSourceDict = {}
        for lineName in ['acts', 'acai', 'tsai', 'ghe', 'ew', 'tline',
                         'scac', 'susr', 'ijsc']:
            lineSource = vtk.vtkLineSource()
            tubeFilter = vtk.vtkTubeFilter()
            tubeFilter.SetInput(lineSource.GetOutput())
            self._appendPolyData.AddInput(tubeFilter.GetOutput())
            self._lineSourceDict[lineName] = lineSource

        self._lineSourceDict['tline'].SetPoint1(0,0,0)
        self._lineSourceDict['tline'].SetPoint2(0,10,0)

        # make actor and STUFF
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInput(self._appendPolyData.GetOutput())

        # eventually, we can keep this actor hanging around (or at least
        # cache the geometry so that we can switch to it)
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        self._threedRenderer.AddActor(actor)

        actor.GetProperty().SetColor(0,1.0,0)

        # test polydata
        #pdReader = vtk.vtkPolyDataReader()
        #pdReader.SetFileName('/home/cpbotha/
        
    def doTimeStep(self, timeStep):
        """timeStep is 0-based.
        """

        currentTimeStep = self._mData.ppos[timeStep]
        # now use the coordinates to set up the geometry
        self._lineSourceDict['acts'].SetPoint1(currentTimeStep['ac'])
        self._lineSourceDict['acts'].SetPoint2(currentTimeStep['ts'])

        self._lineSourceDict['acai'].SetPoint1(currentTimeStep['ac'])
        self._lineSourceDict['acai'].SetPoint2(currentTimeStep['ai'])

        self._lineSourceDict['tsai'].SetPoint1(currentTimeStep['ts'])
        self._lineSourceDict['tsai'].SetPoint2(currentTimeStep['ai'])

        self._lineSourceDict['ghe'].SetPoint1(currentTimeStep['ghr'])
        self._lineSourceDict['ghe'].SetPoint2(currentTimeStep['er'])

        self._lineSourceDict['ew'].SetPoint1(currentTimeStep['er'])
        self._lineSourceDict['ew'].SetPoint2(currentTimeStep['wr'])

        self._lineSourceDict['scac'].SetPoint1(currentTimeStep['sc'])
        self._lineSourceDict['scac'].SetPoint2(currentTimeStep['ac'])

        self._lineSourceDict['susr'].SetPoint1(currentTimeStep['su'])
        self._lineSourceDict['susr'].SetPoint2(currentTimeStep['sr'])

        self._lineSourceDict['ijsc'].SetPoint1(currentTimeStep['ij'])
        self._lineSourceDict['ijsc'].SetPoint2(currentTimeStep['sc'])
        
        # make sure everything is up to date
        self._appendPolyData.Update()

    def _handlerAutoAnimate(self, event):
        self._autoAnimate()

    def _handlerShowControls(self, event):
        if not self.controlFrame.Show(True):
            self.controlFrame.Raise()

    def _handlerTimeStepSlider(self, event):
        timeStep = self.controlFrame.timeStepSlider.GetValue()
        self.doTimeStep(timeStep)
        self.updateRender()

    def updateRender(self):
        self.viewerFrame.threedRWI.GetRenderWindow().Render()
        
