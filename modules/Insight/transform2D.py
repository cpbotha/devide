# $Id: transform2D.py,v 1.8 2005/11/04 10:34:55 cpbotha Exp $

# TODO:
# * this module is not sensitive to changes in its inputs... it should
#   register observers and run _createPipelines if/when they change.

from imageStackRDR import imageStackClass
from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
import fixitk as itk
from typeModules.transformStackClass import transformStackClass
from typeModules.imageStackClass import imageStackClass
import  vtk
import ConnectVTKITKPython as CVIPy

class transform2D(noConfigModuleMixin, moduleBase):

    """This apply a stack of transforms to a stack of images in an
    accumulative fashion, i.e. imageN is transformed:
    Tn(Tn-1(...(T1(imageN))).

    The result of this filter is a
    vtkImageData, ready for using in your friendly neighbourhood
    visualisation pipeline.

    NOTE: this module was currently kludged to transform 1:N images (and not
    0:N). 11/11/2004 (joris): kludge removed.
    """

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)
        noConfigModuleMixin.__init__(self)

        self._imageStack = None
        self._transformStack = None

        #
        self._itkExporterStack = []
        self._imageAppend = vtk.vtkImageAppend()
        # stack of images should become volume
        self._imageAppend.SetAppendAxis(2)

        self._viewFrame = self._createViewFrame(
            {'Module (self)' : self})
        self.configToLogic()
        self.logicToConfig()
        self.configToView()
             

    def close(self):
        # just in case
        self.setInput(0, None)
        self.setInput(1, None)

        # take care of our refs so that things can disappear
        self._destroyPipelines()
        del self._itkExporterStack
        del self._imageAppend

        noConfigModuleMixin.close(self)

        moduleBase.close(self)

    def getInputDescriptions(self):
        return ('ITK Image Stack', '2D Transform Stack')

    def setInput(self, idx, inputStream):
        if idx == 0:
            if inputStream != self._imageStack:
                # if it's None, we have to take it
                if inputStream == None:
                    # disconnect
                    self._imageStack = None
                    self._destroyPipelines()
                    return

                # let's setup for a new stack!
                try:
                    assert(inputStream.__class__.__name__ == 'imageStackClass')
                    inputStream.Update()
                    assert(len(inputStream) >= 2)
                except Exception:
                    # if the Update call doesn't work or
                    # if the input list is not long enough (or unsizable),
                    # we don't do anything
                    raise TypeError, \
                          "register2D requires an ITK Image Stack of minimum length 2 as input."

                # now check that the imageStack is the same size as the
                # transformStack
                if self._transformStack and \
                   len(inputStream) != len(self._transformStack):
                    raise TypeError, \
                          "The Image Stack you are trying to connect has a\n" \
                          "different length than the connected Transform\n" \
                          "Stack."

                self._imageStack = inputStream
                self._createPipelines()

        else: # closes if idx == 0 block
            if inputStream != self._transformStack:
                if inputStream == None:
                    self._transformStack = None
                    self._destroyPipelines()
                    return

                try:
                    assert(inputStream.__class__.__name__ == \
                           'transformStackClass')
                except Exception:
                    raise TypeError, \
                          "register2D requires an ITK Transform Stack on " \
                          "this port."

                inputStream.Update()

                if len(inputStream) < 2:
                    raise TypeError, \
                          "The input transform stack should be of minimum " \
                          "length 2."
                    
                if self._imageStack and \
                   len(inputStream) != len(self._imageStack):
                    raise TypeError, \
                          "The Transform Stack you are trying to connect\n" \
                          "has a different length than the connected\n" \
                          "Transform Stack"

                self._transformStack = inputStream
                self._createPipelines()

        # closes else

    def getOutputDescriptions(self):
        return ('vtkImageData',)

    def getOutput(self, idx):
        return self._imageAppend.GetOutput()

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

    # ----------------------------------------------------------------------
    # non-API methods start here -------------------------------------------
    # ----------------------------------------------------------------------

    def _createPipelines(self):
        """Setup all necessary logic to transform, combine and convert all
        input images.

        Call this ONLY if things have changed, i.e. when
        your change observer is called or if the transform2D input ports
        are changed.
        """

        if not self._imageStack or not self._transformStack:
            self._destroyPipelines()
            # in this case, we should break down the pipeline
            return

        # take care of all inputs
        self._imageAppend.RemoveAllInputs()

        #totalTrfm = itk.itkEuler2DTransform_New()
        totalTrfm = itk.itkCenteredRigid2DTransform_New()
        totalTrfm.SetIdentity()
        
        prevImage = self._imageStack[0]
        for trfm, img, i in zip(self._transformStack,
                                self._imageStack,
                                range(len(self._imageStack))):
            # accumulate with our totalTransform
            totalTrfm.Compose(trfm.GetPointer(), 0)
            # make a copy of the totalTransform that we can use on
            # THIS image

	    # copyTotalTrfm = itk.itkEuler2DTransform_New()
	    copyTotalTrfm = itk.itkCenteredRigid2DTransform_New()
	    
            # this is a really kludge way to copy the total transform,
            # as concatenation doesn't update the Parameters member, so
            # getting and setting parameters is not the way to go
            copyTotalTrfm.SetIdentity()
            copyTotalTrfm.Compose(totalTrfm.GetPointer(),0)

            # this SHOULD have worked
            #pda = totalTrfm.GetParameters()
            #copyTotalTrfm.SetParameters(pda)
            
            # this actually increases the ref count of the transform!
            # resampler
            resampler = itk.itkResampleImageFilterF2F2_New()
            resampler.SetTransform(copyTotalTrfm.GetPointer())
            resampler.SetInput(img)

            region = prevImage.GetLargestPossibleRegion()
            resampler.SetSize(region.GetSize())
            resampler.SetOutputSpacing(prevImage.GetSpacing())
            resampler.SetOutputOrigin(prevImage.GetOrigin())
            resampler.SetDefaultPixelValue(0)
            
            # set up all the 
            rescaler = itk.itkRescaleIntensityImageFilterF2US2_New()
            rescaler.SetOutputMinimum(0)
            rescaler.SetOutputMaximum(65535)
            rescaler.SetInput(resampler.GetOutput())
            print "Resampling image %d" % (i,)
            rescaler.Update() # give ITK a chance to complain

            itkExporter = itk.itkVTKImageExportUS2_New()
            itkExporter.SetInput(rescaler.GetOutput())
            # this is so the ref keeps hanging around
            self._itkExporterStack.append(itkExporter)

            vtkImporter = vtk.vtkImageImport()
            CVIPy.ConnectITKUS2ToVTK(itkExporter.GetPointer(),
                                     vtkImporter)

            # FIXME KLUDGE: we ignore image 0 (this is for joris)
            # if i > 0:
            #    self._imageAppend.AddInput(vtkImporter.GetOutput())

            # setup the previous Image for the next loop
            prevImage = img

        # things should now work *cough*
        
        
    def _destroyPipelines(self):
        if not self._imageStack or not self._transformStack:
            self._imageAppend.RemoveAllInputs()
            del self._itkExporterStack[:]
