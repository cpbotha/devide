from moduleBase import moduleBase
import moduleUtils
import vtk

class histogramSegment(moduleBase):

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        self._createViewFrame()
        #self._bindEvents()

    def close(self):
        for i in range(len(self.getInputDescriptions())):
            self.setInput(i, None)

        # call close method of base class
        moduleBase.close(self)

        # we should be able to take care of our renderwindow now
        # we have to do this nasty trick until my Finalize changes are
        # implemented in all vtkRenderWindow types
        self._renderer.RemoveAllProps()
        del self._renderer
        self._viewFrame.rwi.GetRenderWindow().WindowRemap()
        self._viewFrame.Destroy()
        del self._viewFrame

    def getInputDescriptions(self):
        return ('Image Data 1', 'Imaga Data 2')

    def setInput(self, idx, inputStream):

        def checkTypeAndReturnInput(inputStream):
            """Check type of input.  None gets returned.  The input is
            returned if it has a valid type.  An exception is thrown if
            the input is invalid.
            """
            
            if inputStream == None:
                # disconnect
                return None
                
            else:
                # first check the type
                validType = False
                try:
                    if inputStream.IsA('vtkImageData'):
                        validType = True

                except AttributeError:
                    # validType is already False
                    pass

                if not validType:
                    raise TypeError, 'Input has to be of type vtkImageData.'
                else:
                    return inputStream
            
            
        if idx == 0:
            self._input0 = checkTypeAndReturnInput(inputStream)
            #self._histogram.SetInput1(self._input0)

        elif idx == 1:
            self._input1 = checkTypeAndReturnInput(inputStream)
            #self._histogram.SetInput2(self._input1)


    def getOutputDescriptions(self):
        return ('Segmented vtkImageData',)

    def getOutput(self, idx):
        return None

    def executeModule(self):
        pass

    def logicToConfig(self):
        pass
    
    def configToLogic(self):
        pass

    def viewToConfig(self):
        pass

    def configToView(self):
        pass

    def view(self):
        self._viewFrame.Show(True)
        

    # -------------------------------------------------------
    # END OF API METHODS
    # -------------------------------------------------------


    def _createViewFrame(self):
        # create the viewerFrame
        import modules.Viewers.resources.python.histogramSegmentFrames

        viewFrame = modules.Viewers.resources.python.histogramSegmentFrames.\
                    viewFrame

        self._viewFrame = moduleUtils.instantiateModuleViewFrame(
            self, self._moduleManager, viewFrame)
        
        # add the renderer
        self._renderer = vtk.vtkRenderer()
        self._renderer.SetBackground(0.5, 0.5, 0.5)
        self._viewFrame.rwi.GetRenderWindow().AddRenderer(
            self._renderer)
        
        # display the window
        self._viewFrame.Show(True)
        

