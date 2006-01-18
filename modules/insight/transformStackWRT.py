# $Id$
from typeModules.transformStackClass import transformStackClass
import cPickle
from moduleBase import moduleBase
from moduleMixins import filenameViewModuleMixin
import moduleUtils
import wx
import vtk

class transformStackWRT(moduleBase, filenameViewModuleMixin):
    """Writes 2D Transform Stack to disc.

    Use this module to save the results of a register2D session.
    """

    def __init__(self, moduleManager):

        # call parent constructor
        moduleBase.__init__(self, moduleManager)
        # ctor for this specific mixin
        filenameViewModuleMixin.__init__(self)

        # this is the input
        self._transformStack = None

        # we now have a viewFrame in self._viewFrame
        self._createViewFrame(
            'Select a filename',
            '2D Transform Stack file (*.2ts)|*.2ts|All files (*)|*',
            objectDict=None)

        # set up some defaults
        self._config.filename = ''
        self.configToLogic()
        # make sure these filter through from the bottom up
        self.logicToConfig()
        self.configToView()
        
    def close(self):
        # we should disconnect all inputs
        self.setInput(0, None)
        del self._transformStack
        filenameViewModuleMixin.close(self)

    def getInputDescriptions(self):
	return ('2D Transform Stack',)
    
    def setInput(self, idx, inputStream):
        if inputStream != self._transformStack:
            if inputStream == None: # disconnect
                self._transformStack = None
                return

            if not inputStream.__class__.__name__ == 'transformStackClass':
                raise TypeError, \
                      'transformStackWRT requires a transformStack at input'
            
            self._transformStack = inputStream
    
    def getOutputDescriptions(self):
	return ()
    
    def getOutput(self, idx):
        raise Exception
    
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
            self._writeTransformStack(self._transformStack,
                                      self._config.filename)

    def view(self, parent_window=None):
        # if the frame is already visible, bring it to the top; this makes
        # it easier for the user to associate a frame with a glyph
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()

    def _writeTransformStack(self, transformStack, filename):
        if not transformStack:
            md = wx.MessageDialog(
                self._moduleManager.getModuleViewParentWindow(),
                'Input transform Stack is empty or not connected, not saving.',
                "Information",
                wx.OK | wx.ICON_INFORMATION)
            
            md.ShowModal()
            return

        # let's try and open the file
        try:
            # opened for binary writing
            transformFile = file(filename, 'wb')
        except IOError, ioemsg:
            raise IOError, 'Could not open %s for writing:\n%s' % \
                  (filename, ioemsg)

        # convert transformStack to list of tuples
        pickleList = []
        for transform in transformStack:
            name = transform.GetNameOfClass()
            nop = transform.GetNumberOfParameters()
            pda = transform.GetParameters()
            paramsTup = tuple([pda.GetElement(i) for i in range(nop)])
            pickleList.append((name, paramsTup))

        cPickle.dump(pickleList, transformFile, True)

        
            
