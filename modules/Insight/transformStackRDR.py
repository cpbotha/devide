# $Id: transformStackRDR.py,v 1.4 2003/12/18 14:27:46 cpbotha Exp $
from typeModules.transformStackClass import transformStackClass
import cPickle
import fixitk as itk
import md5
from moduleBase import moduleBase
from moduleMixins import filenameViewModuleMixin
import moduleUtils
import wx
import vtk

class transformStackRDR(moduleBase, filenameViewModuleMixin):

    """Reads 2D Transform Stack from disc.

    This module can be used to feed a register2D or a transform2D module.
    It reads the files that are written by transformStackWRT, but you knew
    that.
    """

    def __init__(self, moduleManager):

        # call parent constructor
        moduleBase.__init__(self, moduleManager)
        # ctor for this specific mixin
        filenameViewModuleMixin.__init__(self)

        # this is the output
        self._transformStack = transformStackClass(self)

        # we're going to use this to know when to actually read the data
        self._md5HexDigest = ''

        # we now have a viewFrame in self._viewFrame
        self._createViewFrame(
            'Select a filename to load',
            '2D Transform Stack file (*.2ts)|*.2ts|All files (*)|*',
            objectDict=None)

        # set up some defaults
        self._config.filename = ''
        self.configToLogic()
        # make sure these filter through from the bottom up
        self.syncViewWithLogic()
        
    def close(self):
        del self._transformStack
        filenameViewModuleMixin.close(self)

    def getInputDescriptions(self):
	return ()
    
    def setInput(self, idx, inputStream):
        raise Exception
    
    def getOutputDescriptions(self):
	return ('2D Transform Stack',)    
    
    def getOutput(self, idx):
        return self._transformStack
    
    def logicToConfig(self):
        pass

    def configToLogic(self):
        pass

    def viewToConfig(self):
        self._config.filename = self._getViewFrameFilename()

    def configToView(self):
        self._setViewFrameFilename(self._config.filename)

    def executeModule(self):
        if len(self._config.filename):
            
            self._readTransformStack(self._config.filename)

    def view(self, parent_window=None):
        # if the frame is already visible, bring it to the top; this makes
        # it easier for the user to associate a frame with a glyph
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()

    def _readTransformStack(self, filename):
        try:
            # binary mode
            transformFile = file(filename, 'rb')
        except IOError, ioemsg:
            raise IOError, 'Could not open %s for reading:\n%s' % \
                  (filename, ioemsg)

        tBuffer = transformFile.read()
        m = md5.new()
        m.update(tBuffer)
        newHexDigest = m.hexdigest()

        if newHexDigest != self._md5HexDigest:
            # this means the file has changed and we should update
            # first take care of the current one
            del self._transformStack[:]
            # we have to rewind to the beginning of the file, else
            # the load will break
            transformFile.seek(0)
            pickleList = cPickle.load(transformFile)
            for name, paramsTup in pickleList:
                # instantiate transform
                trfm = eval('itk.itk%s_New()' % (name,))
                # set the correct parameters
                pda = trfm.GetParameters()
                i = 0
                for p in paramsTup:
                    # FIXME: make sure i is within range with GetNOParameters
                    pda.SetElement(i, p)
                    i+=1

                trfm.SetParameters(pda)
                self._transformStack.append(trfm)
            
            self._md5HexDigest = newHexDigest
        
            
