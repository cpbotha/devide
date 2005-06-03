import genUtils
from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
import moduleUtils
import vtk
import vtkdevide

class imageBacktracker(noConfigModuleMixin, moduleBase):
    """JORIK'S STUFF.

    """

    def __init__(self, moduleManager):

        # call parent constructor
        moduleBase.__init__(self, moduleManager)
	noConfigModuleMixin.__init__(self)

	self._imageBacktracker = vtkdevide.vtkImageBacktracker()

        moduleUtils.setupVTKObjectProgress(self, self._imageBacktracker,
                                           'Backtracking...')
        
        # we'll use this to keep a binding (reference) to the passed object
        self._inputPoints = None
        # inputPoints observer ID
        self._inputPointsOID = None
        # this will be our internal list of points
        self._seedPoints = []

        self._viewFrame = None
        self._createViewFrame({'Module (self)' : self, 'vtkImageBacktracker' : self._imageBacktracker})

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        self.setInput(0, None)
        self.setInput(1, None)
        # don't forget to call the close() method of the vtkPipeline mixin
        noConfigModuleMixin.close(self)
        # take out our view interface
        del self._imageBacktracker
	moduleBase.close(self)


    def getInputDescriptions(self):
        return ('vtkImageData', 'Seed points')
    
    def setInput(self, idx, inputStream):
        if idx == 0:
            # will work for None and not-None
            self._imageBacktracker.SetInput(inputStream)
        else:
            if inputStream is not self._inputPoints:
                if self._inputPoints:
                    self._inputPoints.removeObserver(self._inputPointsObserver)

                if inputStream:
                    inputStream.addObserver(self._inputPointsObserver)

                self._inputPoints = inputStream

                # initial update
                self._inputPointsObserver(None)
            
    
    def getOutputDescriptions(self):
        return ('Backtracked polylines (vtkPolyData)',)
    
    def getOutput(self, idx):
        return self._imageBacktracker.GetOutput()


    def executeModule(self):
        self._imageBacktracker.Update()

    def _inputPointsObserver(self, obj):
        # extract a list from the input points
        tempList = []
        if self._inputPoints:
            for i in self._inputPoints:
                tempList.append(i['discrete'])
            
        if tempList != self._seedPoints:
            self._seedPoints = tempList
            self._imageBacktracker.RemoveAllSeeds()
            for seedPoint in self._seedPoints:
                self._imageBacktracker.AddSeed(seedPoint[0], seedPoint[1],
		                               seedPoint[2])
                print "adding %s" % (str(seedPoint))



