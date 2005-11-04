# ifdocRDR copyright (c) 2003 by Charl P. Botha cpbotha@ieee.org
# $Id: ifdocRDR.py,v 1.5 2005/11/04 10:35:03 cpbotha Exp $
# module to read and interpret data from ifdoc output

from genMixins import subjectMixin, updateCallsExecuteModuleMixin
import md5
from moduleBase import moduleBase, genericObject
from moduleMixins import filenameViewModuleMixin
import re
import time
import vtk

# -------------------------------------------------------------------------
class mData(subjectMixin, updateCallsExecuteModuleMixin):
    """Class for holding the parsed m-file.  An instance of this class is
    available at the output of the ifdocRDR.
    """
    
    def __init__(self, d3Module):
        # mixin constructor
        subjectMixin.__init__(self)
        # mixin constructor
        updateCallsExecuteModuleMixin.__init__(self, d3Module)
        
        # important variables

        # ppos is a list of dictionaries, each dictionary encapsulating
        # one complete timestep... the keys are the various point names
        # and their values are the tuples containing the point positions
        self.ppos = []
        # phin is a list of dictionaries, each dictionary encapsulating
        # one complete timestep.  The dictionary has the names of the
        # rotating bones as keys and tuples of euler angles as values
        self.phin = []

    def close(self):
        # this will get rid of all bindings to observers
        subjectMixin.close(self)
        # and this of bindings to the generating d3module
        updateCallsExecuteModuleMixin.close(self)

# -------------------------------------------------------------------------
class ifdocRDR(moduleBase, filenameViewModuleMixin):
    """Module that reads and parses ifdoc output.

    This module will read the ifdoc .m file output after an ifdoc or
    ifdoc forward simulation.  Its output is an mData object that can
    be used by e.g. the ifdocVWR module.
    """
    
    def __init__(self, moduleManager):
        # do the base class
        moduleBase.__init__(self, moduleManager)

        # do the mixin
        filenameViewModuleMixin.__init__(self)
        
        # setup our output
        self._mData = mData(self)

        # setup the md5sum variable so that we know when the file has changed
        self._md5HexDigest = ''

        # now initialise some config stuff
        self._config.dspFilename = ''
        self._config.mFilename = ''

        self._createViewFrame('Select a filename',
                              'IFDOC m file (*.m)|*.m|All files (*)|*',
                              None)

        self.configToLogic()
        self.logicToConfig()
        self.configToView()
        
    def close(self):
        filenameViewModuleMixin.close(self)
        self._mData.close()
        del self._mData

    def getInputDescriptions(self):
        return ()

    def setInput(self, idx, inputStream):
        raise Exception, 'This module does not accept any input.'

    def getOutputDescriptions(self):
        return ('ifdoc m-Data',)

    def getOutput(self, idx):
        return self._mData

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

    def parseMDict(self, mDict, mData):
        """After a file has been parsed by a suitable call to parseMFile,
        this method will perform higher level parsing.  Relevant data
        structures in mDict (the result of parseMFile) will be interpreted
        and inserted into mData.
        """

        # PPOS ---------------------------------------------------------
        # column is time, rows are coordinates of various points
        # matrix is row, column ordered
        pposMatrix = mDict['ppos']

        # let's clear out our ppos
        mData.ppos = [{} for i in xrange(len(pposMatrix[0]))]
        
        rowIdx = 0
        for pointName in ['ac', 'ts', 'ai', 'ghr', 'er', 'em', 'el', 'wr',
                          'hcog',
                          'ij', 'sc', 'aa', 'su', 'sr']: # newly added
            rows = pposMatrix[rowIdx:rowIdx+3]
            # go through all timesteps, storing the currently active point
            for timeStep in xrange(len(mData.ppos)):
                mData.ppos[timeStep][pointName] = (rows[0][timeStep],
                                                   rows[1][timeStep],
                                                   rows[2][timeStep])
            
            rowIdx += 3

        # PPOS ---------------------------------------------------------
        phinMatrix = mDict['phin']
        mData.phin = [{} for i in xrange(len(phinMatrix[0]))]

        rowIdx = 0
        for jointName in ['thorax', 'clavicula', 'scapula', 'humerus',
                          'ulna', 'radius', 'hand']:
            rows = phinMatrix[rowIdx:rowIdx+3]
            for timeStep in xrange(len(mData.phin)):
                mData.phin[timeStep][jointName] = (rows[0][timeStep],
                                                   rows[1][timeStep],
                                                   rows[2][timeStep])

    def parseMFile(self, fileBuffer, variableNameList):
        """This will parse fileBuffer for any variable = [ lines and
        return these as lists of lists in a dictionary with
        matlab variable name as key.

        Use this as a raw parser for matlab files, i.e. it just returns
        the raw matrices.
        """
        
        # build regular expressions that'll catch any of the variables
        # var1|var2|var3
        vnlre = '|'.join(variableNameList)
        vre = r'(%s)\s*=\s*\[([^\]]*)\];' % (vnlre)
        poVariable = re.compile(vre, re.DOTALL)

        # groupList is a list of occurrences of the regexp above
        # each occurrence is a tuple containing all found groups
        groupList = poVariable.findall(fileBuffer)

        variableDict = {}

        for groupTuple in groupList:
            stripped = groupTuple[1].strip()
            floatStringLines = stripped.split('\n')
            floats = []
            for floatString in floatStringLines:
                floatStringList = floatString.strip().split()
                lineFloats = []
                for floatString in floatStringList:
                    try:
                        lineFloats.append(float(floatString))
                    except ValueError:
                        # couldn't cast, just continue...
                        pass

                floats.append(lineFloats)

            # before we assign, make sure it's a valid matrix (constant number
            # of columns over all lines)
            cDict = {}
            for rowIdx in range(len(floats)):
                cDict[len(floats[rowIdx])] = rowIdx

            if len(cDict) > 1:
                raise ValueError, \
                      'Non-constant number of columns in in matrix %s' % \
                      (groupTuple[0],)

            variableDict[groupTuple[0]] = floats

        return variableDict
            
        
    def parseMFileOld(self, fileLines, variableNameList):
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

        numberOfProgressSteps = 20.0
        progressStepSize = 100.0 / numberOfProgressSteps
        linesPerStep = len(fileLines) / numberOfProgressSteps
        progress = 0.0

        print linesPerStep
        print len(fileLines)
        
        for lineIdx in xrange(len(fileLines)):
            if lineIdx % linesPerStep == 0:
                progress += progressStepSize
                self._moduleManager.setProgress(
                    progress, "Parsing ifdoc m-file")
                                                
            line = fileLines[lineIdx]

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

        self._moduleManager.setProgress(
            100.0, "Parsing ifdoc m-file [DONE]")


        # return our payload as a dict
        return variableDict

    def executeModule(self):
        mFile = open(self._config.mFilename)
        mBuffer = mFile.read()
        mFile.close()        

        # now check with md5 if the file has changed!
        m = md5.new()
        m.update(mBuffer)

        newHexDigest = m.hexdigest()
        if newHexDigest != self._md5HexDigest:
            # this will throw an exception if it can't parse the file
            # this exception will trigger the handler in moduleManager
            mDict = self.parseMFile(mBuffer, ['ppos', 'phin'])

            # this will clear necessary structures in self._mData and
            # re-init them with new data
            self.parseMDict(mDict, self._mData)

            # now indicate that we've changed stuff
            self._mData.notify()

            # and update our digest
            self._md5HexDigest = newHexDigest

    def view(self, parent_window=None):
        # if the window is already visible, raise it
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()


