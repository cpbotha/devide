# $Id: ifdocRDR.py,v 1.4 2003/08/24 19:37:06 cpbotha Exp $

from moduleBase import moduleBase
from moduleMixins import filenameViewModuleMixin
import re
import time
import vtk
from wxPython.wx import *



class ifdocRDR(moduleBase, filenameViewModuleMixin):

    def __init__(self, moduleManager):
        # do the base class
        moduleBase.__init__(self, moduleManager)

        # do the mixin
        filenameViewModuleMixin.__init__(self)
        
        # setup our pipeline
        self._appendPolyData = None
        self._buildPipeline()

        # now initialise some config stuff
        self._config.dspFilename = ''
        self._config.mFilename = ''

        self._createViewFrame('Select a filename',
                              'IFDOC m file (*.m)|*.m|All files (*)|*',
                              {'vtkAppendPolyData': self._appendPolyData})

        self.configToLogic()
        self.syncViewWithLogic()
        

    def close(self):
        filenameViewModuleMixin.close(self)

    def getInputDescriptions(self):
        return ()

    def setInput(self, idx, inputStream):
        raise Exception, 'This module does not accept any input.'

    def getOutputDescriptions(self):
        return ('vtkPolyData',)

    def getOutput(self, idx):
        return self._appendPolyData.GetOutput()

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
        self._config.mFilename = self._getViewFrameFilename()
        
    
    def configToView(self):
        """Make the view reflect the internal configuration information.

        """
        self._setViewFrameFilename(self._config.mFilename)


    def parseMFile(self, fileLines, variableNameList):
        """This will parse fileLines for any variable = [ lines and
        return these as lists (or lists of lists) in a dictionary with
        matlab variable name as key.
        """

        # we use this to find the variable name (group 0)
        poStartMatrix = re.compile(r'([A-Za-z0-9_]+)\s*=\s*\[(.*)')
        # we'll use this to get the end of a matrix
        poEndMatrix = re.compile(r'(.*?)]')
        # whitespace pattern object (we'll use this to get rid of the
        # whitespace between elements)
        poWhiteSpace = re.compile('\s+')

        variableDict = {}
        currentName = None
        currentMatrix = None
        for line in fileLines:
            mo = poStartMatrix.search(line)
            if mo:
                if currentName:
                    # store the current variable
                    variableDict[currentName] = currentMatrix

                currentName = mo.groups()[0]
                if currentName in variableNameList:
                    currentMatrix = []
                    # the rest of the code will think that we're busy with
                    # a normal variable
                    line = mo.groups()[1]
                else:
                    currentName = None
                    currentMatrix = []
                    

            # we can only do stuff here if we actually have a variable
            if currentName:
                # check line for floats (] stops us)
                moEndMatrix = poEndMatrix.search(line)
                if moEndMatrix:
                    # we still have to get out the last data BEFORE the ]
                    line = moEndMatrix.groups()[0]

                # remove whitespace at start and end
                line = line.strip()
                # compress whitespace
                line = poWhiteSpace.sub(' ', line)
                # split into strings... now cast all to float
                if len(line) > 0:
                    splitLine = line.split(' ')
                    try:
                        floats = [float(e) for e in splitLine]
                    except ValueError:
                        # couldn't be converted
                        print "Couldn't convert splitLine to floats, skipping!"
                        print splitLine
                    else:
                        currentMatrix.append(floats)
                
                if moEndMatrix:
                    # store our payload
                    variableDict[currentName] = currentMatrix
                    # if this was the end, make sure everybody knows
                    currentName = None
                    currentMatrix = None

        # return our payload as a dict
        return variableDict

    def executeModule(self):
        mFile = open(self._config.mFilename)
        mLines = mFile.readlines()

        mDict = self.parseMFile(mLines, ['ppos'])
        ppos =  mDict['ppos']

        # timesteps are columns of ppos
        timeSteps = len(ppos[0])

        for timeStep in range(timeSteps):
            wxYield()
            self.doTimeStep(ppos, timeStep)
            time.sleep(0.2)

        time.sleep(0.5)
        self.doTimeStep(ppos, 0)
        
    def oldExecuteModule(self):
        # read in the dsp file
        dspFile = open(self._config.dspFilename)
        dspLines = dspFile.readlines()

        # build up patternObjects for the nodes that we want
        nodeNumberDict = {44 : 'SC', 45 : 'AC', 47 : 'TS', 48 : 'AI'}

        # build up global node pattern object (we'll check each line with
        # this first!)
        poX = re.compile(
            'X\s+([0-9]+)\s+([0-9\.\-]+)\s+([0-9\.\-]+)\s+([0-9\.\-]+)\s*')
        
        # go through the whole list, checking for the various patterns
        nodeCoords = {}
        for dspLine in dspLines:
            mo = poX.match(dspLine)
            if mo:
                try:
                    nodeNumber = int(mo.groups()[0])
                        
                    if nodeNumber in nodeNumberDict:
                        # convert the coords to floats
                        coords = tuple([float(e) for e in mo.groups()[1:4]])
                        nodeCoords[nodeNumber] = coords
                        
                except ValueError:
                    # could not cast nodeNumber to int
                    pass
                
        # now we have all the required node numbers in our thingy (tee hee)
        
                
            
        
            
    def view(self, parent_window=None):
        # if the window is already visible, raise it
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()


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

