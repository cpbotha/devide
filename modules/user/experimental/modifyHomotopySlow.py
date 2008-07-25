import genUtils
from module_base import ModuleBase
from moduleMixins import noConfigModuleMixin
import moduleUtils
import wx
import vtk
import vtkdevide

class modifyHomotopySlow(noConfigModuleMixin, ModuleBase):

    """
    WARNING, WARNING, DANGER WILL ROBINSON: this filter exists purely
    for experimental purposes.  If you really want to use
    modifyHomotopy, use the module in modules.Filters (also part of
    'Morphology').  This filter implements the modification according
    to very basic math and is dog-slow.  In addition, it's throw-away
    code.

    Modifies homotopy of input image I so that the only minima will
    be at the user-specified seed-points or marker image, all other
    minima will be suppressed and ridge lines separating minima will
    be preserved.

    Either the seed-points or the marker image (or both) can be used.
    The marker image has to be >1 at the minima that are to be enforced
    and 0 otherwise.

    This module is often used as a pre-processing step to ensure that
    the watershed doesn't over-segment.

    
    $Revision: 1.1 $
    """
    
    def __init__(self, moduleManager):
        # initialise our base class
        ModuleBase.__init__(self, moduleManager)
        noConfigModuleMixin.__init__(self)

        # these will be our markers
        self._inputPoints = None

        # we can't connect the image input directly to the masksource,
        # so we have to keep track of it separately.
        self._inputImage = None
        self._inputImageObserverID = None

        # we need to modify the mask (I) as well.  The problem with a
        # ProgrammableFilter is that you can't request GetOutput() before
        # the input has been set... 
        self._maskSource = vtk.vtkProgrammableSource()
        self._maskSource.SetExecuteMethod(self._maskSourceExecute)
        
        # we'll use this to synthesise a volume according to the seed points
        self._markerSource = vtk.vtkProgrammableSource()
        self._markerSource.SetExecuteMethod(self._markerSourceExecute)
        # second input is J (the marker)

        # we'll use this to change the markerImage into something we can use
        self._imageThreshold = vtk.vtkImageThreshold()
        # everything equal to or above 1.0 will be "on"
        self._imageThreshold.ThresholdByUpper(1.0)
        self._imageThresholdObserverID = self._imageThreshold.AddObserver(
            'EndEvent', self._observerImageThreshold)
        
        self._viewFrame = self._createViewFrame(
            {'Module (self)' : self})

        # we're not going to give imageErode any input... that's going to
        # to happen manually in the execute_module function :)
        self._imageErode = vtk.vtkImageContinuousErode3D()
        self._imageErode.SetKernelSize(3,3,3)

        moduleUtils.setupVTKObjectProgress(self, self._imageErode,
                                           'Performing greyscale 3D erosion')
        

        self._sup = vtk.vtkImageMathematics()
        self._sup.SetOperationToMax()
        self._sup.SetInput1(self._imageErode.GetOutput())
        self._sup.SetInput2(self._maskSource.GetStructuredPointsOutput())

        # pass the data down to the underlying logic
        self.config_to_logic()
        # and all the way up from logic -> config -> view to make sure
        self.syncViewWithLogic()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)

        # this will take care of all display thingies
        noConfigModuleMixin.close(self)

        ModuleBase.close(self)

        #
        self._imageThreshold.RemoveObserver(self._imageThresholdObserverID)
        
        # get rid of our reference
        del self._markerSource
        del self._maskSource
        del self._imageThreshold
        del self._sup
        del self._imageErode

    def get_input_descriptions(self):
        return ('VTK Image Data', 'Minima points', 'Minima image')

    def set_input(self, idx, inputStream):
        if idx == 0:
            if inputStream != self._inputImage:
                # if we have a different image input, the seeds will have to
                # be rebuilt!
                self._markerSource.Modified()
                # and obviously the masksource has to know that its "input"
                # has changed
                self._maskSource.Modified()

                if inputStream:
                    # we have to add an observer
                    s = inputStream.GetSource()
                    if s:
                        self._inputImageObserverID = s.AddObserver(
                            'EndEvent', self._observerInputImage)

                else:
                    # if we had an observer, remove it
                    if self._inputImage:
                        s = self._inputImage.GetSource()
                        if s and self._inputImageObserverID:
                            s.RemoveObserver(
                                self._inputImageObserverID)
                            
                        self._inputImageObserverID = None

                # finally store the new data
                self._inputImage = inputStream
                
        elif idx == 1:
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
                        self._observerInputPoints)

                self._inputPoints = inputStream
                
                if self._inputPoints:
                    self._inputPoints.addObserver(self._observerInputPoints)

                # the input points situation has changed, make sure
                # the marker source knows this...
                self._markerSource.Modified()
                # as well as the mask source of course
                self._maskSource.Modified()


        else:
            if inputStream != self._imageThreshold.GetInput():
                self._imageThreshold.SetInput(inputStream)
                # we have a different inputMarkerImage... have to recalc
                self._markerSource.Modified()
                self._maskSource.Modified()


    def get_output_descriptions(self):
        return ('Modified VTK Image Data', 'I input', 'J input')

    def get_output(self, idx):
        if idx == 0:
            return self._sup.GetOutput()
        elif idx == 1:
            return self._maskSource.GetStructuredPointsOutput()
        else:
            return self._markerSource.GetStructuredPointsOutput()

    def logic_to_config(self):
        pass
    
    def config_to_logic(self):
        pass

    def view_to_config(self):
        pass

    def config_to_view(self):
        pass
    
    def execute_module(self):
        # FIXME: if this module ever becomes anything other than an experiment, build
        # this logic into yet another ProgrammableSource
        
        # make sure marker is up to date
        self._markerSource.GetStructuredPointsOutput().Update()
        self._maskSource.GetStructuredPointsOutput().Update()

        tempJ = vtk.vtkStructuredPoints()
        tempJ.DeepCopy(self._markerSource.GetStructuredPointsOutput())

        self._imageErode.SetInput(tempJ)

        self._diff = vtk.vtkImageMathematics()
        self._diff.SetOperationToSubtract()

        self._accum = vtk.vtkImageAccumulate()
        self._accum.SetInput(self._diff.GetOutput())

        # now begin our loop
        stable = False
        while not stable:
            # do erosion, get supremum of erosion and mask I
            self._sup.GetOutput().Update()
            # compare this result with tempJ
            self._diff.SetInput1(tempJ)
            self._diff.SetInput2(self._sup.GetOutput())
            self._accum.Update()

            print "%f == %f ?" % (self._accum.GetMin()[0], self._accum.GetMax()[0])
            if abs(self._accum.GetMin()[0] - self._accum.GetMax()[0]) < 0.0001:
                stable = True
            else:
                # not stable yet...
                print "Trying again..."
                tempJ.DeepCopy(self._sup.GetOutput())
                
            
            
            
        

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

            mi = self._imageThreshold.GetInput()
            if mi:
                if mi.GetOrigin() == outputJ.GetOrigin() and \
                   mi.GetExtent() == outputJ.GetExtent():
                    self._imageThreshold.SetInValue(minI)
                    self._imageThreshold.SetOutValue(maxI)
                    self._imageThreshold.SetOutputScalarType(imageI.GetScalarType())
                    self._imageThreshold.GetOutput().SetUpdateExtentToWholeExtent()
                    self._imageThreshold.Update()
                    outputJ.DeepCopy(self._imageThreshold.GetOutput())
                    
                else:
                    vtk.vtkOutputWindow.GetInstance().DisplayErrorText(
                        'modifyHomotopy: marker input should be same dimensions as image input!')
                    # we can continue as if we only had seeds
                    scalars = outputJ.GetPointData().GetScalars()
                    scalars.FillComponent(0, maxI)
                    
            else:
                # initialise all scalars to maxI
                scalars = outputJ.GetPointData().GetScalars()
                scalars.FillComponent(0, maxI)

            # now go through all seed points and set those positions in
            # the scalars to minI
            if self._inputPoints:
                for ip in self._inputPoints:
                    x,y,z = ip['discrete']
                    outputJ.SetScalarComponentFromDouble(x, y, z, 0, minI)

    def _maskSourceExecute(self):
        inputI = self._inputImage
        if inputI:
            inputI.Update()
                
            self._markerSource.Update()
            outputJ = self._markerSource.GetStructuredPointsOutput()
            # we now have an outputJ

            if not inputI.GetScalarPointer() or \
               not outputJ.GetScalarPointer() or \
               not inputI.GetDimensions() > (0,0,0):
                vtk.vtkOutputWindow.GetInstance().DisplayErrorText(
                    'modifyHomotopy: Input is empty.')
                return

            iMath = vtk.vtkImageMathematics()
            iMath.SetOperationToMin()
            iMath.SetInput1(outputJ)
            iMath.SetInput2(inputI)
            iMath.GetOutput().SetUpdateExtentToWholeExtent()
            iMath.Update()

            outputI = self._maskSource.GetStructuredPointsOutput()
            outputI.DeepCopy(iMath.GetOutput())

    def _observerInputPoints(self, obj):
        # this will be called if anything happens to the points
        # simply make sure our markerSource knows that it's now invalid
        self._markerSource.Modified()
        self._maskSource.Modified()        

    def _observerInputImage(self, obj, eventName):
        # the inputImage has changed, so the marker will have to change too
        self._markerSource.Modified()
        # logical, input image has changed
        self._maskSource.Modified()

    def _observerImageThreshold(self, obj, eventName):
        # if anything in the threshold has changed, (e.g. the input) we
        # have to invalidate everything else after it
        self._markerSource.Modified()
        self._maskSource.Modified()
