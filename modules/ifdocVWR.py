# ifdocVWR copyright (c) 2003 by Charl P. Botha cpbotha@ieee.org
# $Id: ifdocVWR.py,v 1.3 2003/09/01 16:39:54 cpbotha Exp $
# module to interact with the ifdoc shoulder model

from moduleBase import moduleBase

class ifdocVWR(moduleBase):

    def __init__(self, moduleManager):
        # base constructor
        moduleBase.__init__(self, moduleManager)

    def close(self):
        pass

    def getInputDescriptions(self):
        return ('IFDOC M file',)

    def setInput(self, idx, inputStream):
        # don't forget to register as an observer
        self.mData = inputStream

    def getOutputDescriptions(self):
        return ()

    def getOutput(self, idx):
        raise Exception

    def logicToConfig(self):
        """Synchronise internal configuration information (usually
        self._config)with underlying system.
        """
        self._config.filename = self._reader.GetFileName()
        if self._config.filename is None:
            self._config.filename = ''

    def configToLogic(self):
        """Apply internal configuration information (usually self._config) to
        the underlying logic.
        """
        self._reader.SetFileName(self._config.filename)

    def viewToConfig(self):
        """Synchronise internal configuration information with the view (GUI)
        of this module.

        """
        self._config.filename = self._getViewFrameFilename()
        
    
    def configToView(self):
        """Make the view reflect the internal configuration information.

        """
        self._setViewFrameFilename(self._config.filename)
    
    def executeModule(self):
        self._reader.Update()
        # important call to make sure the app catches VTK error in the GUI
        self._moduleManager.vtk_poll_error()
            
    def view(self, parent_window=None):
        # if the window is already visible, raise it
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()
    
    
    def executeModuleRDR(self):
        ppos =  mDict['ppos']

        # timesteps are columns of ppos
        timeSteps = len(ppos[0])

        for timeStep in range(timeSteps):
            wxYield()
            self.doTimeStep(ppos, timeStep)
            time.sleep(0.2)

        time.sleep(0.5)
        self.doTimeStep(ppos, 0)

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

        
