# $Id: ifdocRDR.py,v 1.5 2003/09/01 16:39:54 cpbotha Exp $

from genMixins import subjectMixin, updateCallsExecuteModuleMixin
import md5
from moduleBase import moduleBase
from moduleMixins import filenameViewModuleMixin
import re
import time
import vtk
from wxPython.wx import *

class mFileMatrices(dict, subjectMixin, updateCallsExecuteModuleMixin):
    """Class for holding the matrices of the ifdoc m-file as output.
    """
    
    def __init__(self, d3Module, *argv):
        # base constructor (passing parameters along)
        dict.__init__(self, *argv)
        # mixin constructor
        subjectMixin.__init__(self)
        # mixin constructor
        updateCallsExecuteModuleMixin.__init__(self, d3Module)

    def close(self):
        # this will get rid of all bindings to observers
        subjectMixin.close(self)
        # and this of bindings to the generating d3module
        updateCallsExecuteModuleMixin.close(self)

        
class ifdocRDR(moduleBase, filenameViewModuleMixin):

    def __init__(self, moduleManager):
        # do the base class
        moduleBase.__init__(self, moduleManager)

        # do the mixin
        filenameViewModuleMixin.__init__(self)
        
        # setup our output
        self._mFileMatrices = mFileMatrices()

        # now initialise some config stuff
        self._config.dspFilename = ''
        self._config.mFilename = ''

        self._createViewFrame('Select a filename',
                              'IFDOC m file (*.m)|*.m|All files (*)|*',
                              None)

        self.configToLogic()
        self.syncViewWithLogic()
        
    def close(self):
        filenameViewModuleMixin.close(self)
        self._mFileMatrices.close()
        del self._mFileMatrices

    def getInputDescriptions(self):
        return ()

    def setInput(self, idx, inputStream):
        raise Exception, 'This module does not accept any input.'

    def getOutputDescriptions(self):
        return ('ifdoc m-file matrices',)

    def getOutput(self, idx):
        return self._mFileMatrices

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


        # now check with md5 if the file has changed!
        mDict = self.parseMFile(mLines, ['ppos'])

        # we have to do it this way as we're using a special class
        self._mFileMatrices.clear()
        self._mFileMatrices.update(mDict)

        # now indicate that we've changed stuff
        self._mFileMatrices.notify()

    def view(self, parent_window=None):
        # if the window is already visible, raise it
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()


