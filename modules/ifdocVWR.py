# ifdocVWR copyright (c) 2003 by Charl P. Botha cpbotha@ieee.org
# $Id: ifdocVWR.py,v 1.5 2003/09/02 15:37:01 cpbotha Exp $
# module to interact with the ifdoc shoulder model

# TODO:
# * connect observer to self._mFileMatrices, update INTERNAL matrix forms
#   when it notifies... that way, doTimeStep doesn't have to parse the whole
#   frikking matrix everytime.
# * think about: ifdocRDR could do more of this parsing, that's what it's for
#   isn't it?

from moduleBase import moduleBase
import moduleUtils
import time
import vtk
from wxPython.wx import *

class ifdocVWR(moduleBase):

    _numInputs = 1

    def __init__(self, moduleManager):
        # base constructor
        moduleBase.__init__(self, moduleManager)

        self._mFileMatrices = None

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
        del self._mFileMatrices

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
        return ('ifdoc m-file matrices',)

    def setInput(self, idx, inputStream):
        # don't forget to register as an observer
        self._mFileMatrices = inputStream

        if self._mFileMatrices != None:
            self._mFileMatrices.Update()
            ppos = self._mFileMatrices['ppos']
            self.doTimeStep(ppos, 0)
            self.updateRender()
            self._threedRenderer.ResetCamera()

            # setup the slider
            # number of timeSteps == columns
            timeSteps = len(ppos[0])

            # setup UI
            self.controlFrame.timeStepSlider.SetRange(0, timeSteps - 1)
            self.controlFrame.timeStepSlider.SetValue(0)
            self.controlFrame.timeStepSpinCtrl.SetRange(0, timeSteps - 1)
            self.controlFrame.timeStepSpinCtrl.SetValue(0)

    def getOutputDescriptions(self):
        return ()

    def getOutput(self, idx):
        raise Exception

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
        self._mFileMatrices.Update()
        if self._mFileMatrices:
            ppos =  self._mFileMatrices['ppos']

            # timesteps are columns of ppos
            timeSteps = len(ppos[0])

            for timeStep in range(timeSteps):
                self.updateRender()
                wxSafeYield()
                self.doTimeStep(ppos, timeStep)
                time.sleep(0.2)

            time.sleep(0.5)
            self.doTimeStep(ppos, 0)
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

        parentWindow = self._moduleManager.get_module_view_parent_window()        
        # create the viewerFrame
        import modules.resources.python.ifdocVWRFrames
        reload(modules.resources.python.ifdocVWRFrames)

        viewerFrame = modules.resources.python.ifdocVWRFrames.viewerFrame
        self.viewerFrame = viewerFrame(parentWindow, id=-1, title='dummy')

        # attach close handler
        EVT_CLOSE(self.viewerFrame,
                  lambda e, s=self: s.viewerFrame.Show(false))

        self.viewerFrame.SetIcon(moduleUtils.getModuleIcon())

        # add the renderer
        self._threedRenderer = vtk.vtkRenderer()
        self._threedRenderer.SetBackground(0.5, 0.5, 0.5)
        self.viewerFrame.threedRWI.GetRenderWindow().AddRenderer(
            self._threedRenderer)
        
        # controlFrame creation and basic setup -------------------
        controlFrame = modules.resources.python.ifdocVWRFrames.\
                       controlFrame
        self.controlFrame = controlFrame(parentWindow, id=-1,
                                         title='dummy')
        EVT_CLOSE(self.controlFrame,
                  lambda e: self.controlFrame.Show(false))
        self.controlFrame.SetIcon(moduleUtils.getModuleIcon())

        # display the window
        self.viewerFrame.Show(True)
        self.controlFrame.Show(True)

    def _buildPipeline(self):
        # this is temporary
        self._appendPolyData = vtk.vtkAppendPolyData()

        self._lineSourceDict = {}
        for lineName in ['acts', 'acai', 'tsai', 'ghe', 'ew', 'tline']:
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
        
    def doTimeStep(self, ppos, timeStep):
        """timeStep is 0-based.
        """

        # rather modify this to break out the WHOLE ppos matrix in one
        # go... return a list of dicts, where first index is timeStep
        # and each timeStep has a dictionary with the points
        rowIdx = 0
        coordDict = {}
        for pointName in ['ac', 'ts', 'ai', 'gh', 'e', 'em', 'el', 'w']:
            rows = ppos[rowIdx:rowIdx+3]
            coordDict[pointName] = [row[timeStep] for row in rows]
            rowIdx += 3

        # now use the coordinates to set up the geometry
        self._lineSourceDict['acts'].SetPoint1(coordDict['ac'])
        self._lineSourceDict['acts'].SetPoint2(coordDict['ts'])

        self._lineSourceDict['acai'].SetPoint1(coordDict['ac'])
        self._lineSourceDict['acai'].SetPoint2(coordDict['ai'])

        self._lineSourceDict['tsai'].SetPoint1(coordDict['ts'])
        self._lineSourceDict['tsai'].SetPoint2(coordDict['ai'])

        self._lineSourceDict['ghe'].SetPoint1(coordDict['gh'])
        self._lineSourceDict['ghe'].SetPoint2(coordDict['e'])

        self._lineSourceDict['ew'].SetPoint1(coordDict['e'])
        self._lineSourceDict['ew'].SetPoint2(coordDict['w'])
        
        # make sure everything is up to date
        self._appendPolyData.Update()

    def _handlerAutoAnimate(self, event):
        self._autoAnimate()

    def _handlerShowControls(self, event):
        if not self.controlFrame.Show(True):
            self.controlFrame.Raise()

    def _handlerTimeStepSlider(self, event):
        timeStep = self.controlFrame.timeStepSlider.GetValue()
        ppos = self._mFileMatrices['ppos']
        self.doTimeStep(ppos, timeStep)
        self.updateRender()

    def updateRender(self):
        self.viewerFrame.threedRWI.GetRenderWindow().Render()
        
