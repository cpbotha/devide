import genUtils
from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
import moduleUtils
import wx
import vtk
import vtkdevide

class modifyHomotopy(noConfigModuleMixin, moduleBase):
    """Modifies homotopy of input image I so that the only minima will
    be at the use-specified seed-points, all other minima will be
    suppressed and ridge lines separating minima will be preserved.

    This is often used as a pre-processing step to ensure that the
    watershed doesn't over-segment.

    This module uses a DeVIDE-specific implementation of Luc Vincent's
    fast greyscale reconstruction algorithm, extended for 3D.
    
    $Revision: 1.4 $
    """
    
    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)
        noConfigModuleMixin.__init__(self)

        # these will be our markers
        self._inputPoints = None
        # we keep track of our observer ID so we can remove it
        self._inputPointsObserverID = None

        # we can't connect the image input directly to the masksource,
        # so we have to keep track of it separately.
        self._inputImage = None

        # we need to modify the mask (I) as well.  The problem with a
        # ProgrammableFilter is that you can't request GetOutput() before
        # the input has been set... 
        self._maskSource = vtk.vtkProgrammableSource()
        self._maskSource.SetExecuteMethod(self._maskSourceExecute)

        self._dualGreyReconstruct = vtkdevide.vtkImageGreyscaleReconstruct3D()
        # first input is I (the modified mask)
        self._dualGreyReconstruct.SetDual(1)
        self._dualGreyReconstruct.SetInput1(self._maskSource.GetStructuredPointsOutput())
        
        # we'll use this to synthesise a volume according to the seed points
        self._markerSource = vtk.vtkProgrammableSource()
        self._markerSource.SetExecuteMethod(self._markerSourceExecute)
        # second input is J (the marker)
        self._dualGreyReconstruct.SetInput2(
            self._markerSource.GetStructuredPointsOutput())
        
        moduleUtils.setupVTKObjectProgress(
            self, self._dualGreyReconstruct,
            'Performing dual greyscale reconstruction')
                                           
        self._viewFrame = self._createViewFrame(
            {'Module (self)' : self,
             'vtkImageGreyscaleReconstruct3D' : self._dualGreyReconstruct})

        # pass the data down to the underlying logic
        self.configToLogic()
        # and all the way up from logic -> config -> view to make sure
        self.syncViewWithLogic()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)

        # this will take care of all display thingies
        noConfigModuleMixin.close(self)

        moduleBase.close(self)
        
        # get rid of our reference
        del self._dualGreyReconstruct
        del self._markerSource
        del self._maskSource

    def getInputDescriptions(self):
        return ('VTK Image Data', 'Minima points')

    def setInput(self, idx, inputStream):
        if idx == 0:
            if inputStream != self._inputImage:
                self._inputImage = inputStream
                # if we have a different image input, the seeds will have to
                # be rebuilt!
                self._markerSource.Modified()
                # and obviously the masksource has to know that it has to work
                self._maskSource.Modified()
                
        else:
            if inputStream != self._inputPoints:
                # check that the inputStream is either None (meaning
                # disconnect) or a valid type

                try:
                    if inputStream != None and \
                       inputStream.devideType != 'namedPoints':
                        raise TypeError

                except (AttributeError, TypeError):
                    raise TypeError, 'This input requires a points-type'
                    
                
                if self._inputPoints:
                    self._inputPoints.removeObserver(
                        self._inputPointsObserverID)
                    self._inputPointsObserverID = None

                self._inputPoints = inputStream
                
                if self._inputPoints:
                    self._inputPointsObserverID = self._inputPoints.\
                                                  addObserver(
                        self._observerInputPoints)

                # the input points situation has changed, make sure
                # the marker source knows this...
                self._markerSource.Modified()
                # as well as the mask source of course
                self._maskSource.Modified()


    def getOutputDescriptions(self):
        return ('VTK Image Data', )

    def getOutput(self, idx):
        return self._dualGreyReconstruct.GetOutput()

    def logicToConfig(self):
        pass
    
    def configToLogic(self):
        pass

    def viewToConfig(self):
        pass

    def configToView(self):
        pass
    
    def executeModule(self):
        self._dualGreyReconstruct.Update()

    def _markerSourceExecute(self):
        imageI = self._inputImage
        if imageI:
            imageI.Update()
            
            # setup and allocate J output
            outputJ = self._markerSource.GetStructuredPointsOutput()
            # _dualGreyReconstruct wants inputs the same with regards to
            # dimensions, origin and type, so this is okay.
            outputJ.CopyStructure(imageI)
            outputJ.AllocateScalars()

            # we need this to build up J
            minI, maxI = imageI.GetScalarRange()

            # initialise all scalars to maxI
            scalars = outputJ.GetPointData().GetScalars()
            scalars.FillComponent(0, maxI)

            # now go through all seed points and set those positions in
            # the scalars to minI
            if len(self._inputPoints) > 0:
                for ip in self._inputPoints:
                    x,y,z = ip['discrete']
                    outputJ.SetScalarComponentFromDouble(x, y, z, 0, minI)

    def _maskSourceExecute(self):
        inputI = self._inputImage

        if inputI:
            inputI.Update()
            outputI = self._maskSource.GetStructuredPointsOutput()
            outputI.DeepCopy(inputI)

            # we need this to modify our outputI (at least minI)
            minI, maxI = inputI.GetScalarRange()

            # now go through all seed points and set those positions in
            # the scalars to minI
            if len(self._inputPoints) > 0:
                for ip in self._inputPoints:
                    x,y,z = ip['discrete']
                    outputI.SetScalarComponentFromDouble(x, y, z, 0, minI)
            

    def _observerInputPoints(self, obj):
        # this will be called if anything happens to the points
        # simply make sure our markerSource knows that it's now invalid
        self._maskSource.Modified()
        self._markerSource.Modified()
