# TODO: simplify module!!  all this muck was necessary due to the old
# demand-driven model.  Keep the code around, it could be used as
# illustrative case.

import gen_utils
from module_base import ModuleBase
from module_mixins import NoConfigModuleMixin
import module_utils
import vtk
import vtkdevide

class modifyHomotopy(NoConfigModuleMixin, ModuleBase):
    """IMPORTANT: this module needs to be updated to the new
    event-driven execution scheme.  It should still work, but it may also
    blow up your computer.

    Modifies homotopy of input image I so that the only minima will
    be at the user-specified seed-points or marker image, all other
    minima will be suppressed and ridge lines separating minima will
    be preserved.

    Either the seed-points or the marker image (or both) can be used.
    The marker image has to be >1 at the minima that are to be enforced
    and 0 otherwise.

    This module is often used as a pre-processing step to ensure that
    the watershed doesn't over-segment.

    This module uses a DeVIDE-specific implementation of Luc Vincent's
    fast greyscale reconstruction algorithm, extended for 3D.
    
    """


    def __init__(self, module_manager):
        # initialise our base class
        ModuleBase.__init__(self, module_manager)

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

        # we'll use this to change the markerImage into something we can use
        self._imageThreshold = vtk.vtkImageThreshold()
        # everything equal to or above 1.0 will be "on"
        self._imageThreshold.ThresholdByUpper(1.0)
        self._imageThresholdObserverID = self._imageThreshold.AddObserver(
            'EndEvent', self._observerImageThreshold)
        
        module_utils.setup_vtk_object_progress(
            self, self._dualGreyReconstruct,
            'Performing dual greyscale reconstruction')

        NoConfigModuleMixin.__init__(
            self,
            {'Module (self)' : self,
             'vtkImageGreyscaleReconstruct3D' : self._dualGreyReconstruct})

                                           
        self.sync_module_logic_with_config()
        
    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for input_idx in range(len(self.get_input_descriptions())):
            self.set_input(input_idx, None)

        # this will take care of all display thingies
        NoConfigModuleMixin.close(self)

        ModuleBase.close(self)

        #
        self._imageThreshold.RemoveObserver(self._imageThresholdObserverID)
        
        # get rid of our reference
        del self._dualGreyReconstruct
        del self._markerSource
        del self._maskSource
        del self._imageThreshold

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
                self._dualGreyReconstruct.Modified()

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
                self._dualGreyReconstruct.Modified()

        else:
            if inputStream != self._imageThreshold.GetInput():
                self._imageThreshold.SetInput(inputStream)
                # we have a different inputMarkerImage... have to recalc
                self._markerSource.Modified()
                self._maskSource.Modified()
                self._dualGreyReconstruct.Modified()


    def get_output_descriptions(self):
        return ('Modified VTK Image Data', 'I input', 'J input')

    def get_output(self, idx):
        if idx == 0:
            return self._dualGreyReconstruct.GetOutput()
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
        self._dualGreyReconstruct.Modified()

    def _observerInputImage(self, obj, eventName):
        # the inputImage has changed, so the marker will have to change too
        self._markerSource.Modified()
        # logical, input image has changed
        self._maskSource.Modified()
        self._dualGreyReconstruct.Modified()

    def _observerImageThreshold(self, obj, eventName):
        # if anything in the threshold has changed, (e.g. the input) we
        # have to invalidate everything else after it
        self._markerSource.Modified()
        self._maskSource.Modified()
        self._dualGreyReconstruct.Modified()
