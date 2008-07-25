import itk
import module_kits.itk_kit as itk_kit
from module_base import ModuleBase
from moduleMixins import scriptedConfigModuleMixin

import math

class BSplineRegistration(scriptedConfigModuleMixin, ModuleBase):
    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        self._create_pipeline()

        self._view_frame = None


    def _create_pipeline(self):
        interpolator = itk.LinearInterpolateImageFunction\
                [itk.Image.F3, itk.D].New()
        metric = itk.MeanSquaresImageToImageMetric\
                [itk.Image.F3, itk.Image.F3].New()
        optimizer = itk.LBFGSOptimizer.New()
        transform = itk.BSplineDeformableTransform[itk.D, 3, 3].New()

        r = itk.ImageRegistrationMethod[itk.Image.F3, itk.Image.F3].\
                New(
                        Interpolator=interpolator.GetPointer(), 
                        Metric=metric.GetPointer(),
                        Optimizer=optimizer.GetPointer(),
                        Transform=transform.GetPointer())



        self._interpolator = interpolator
        self._metric = metric
        self._optimizer = optimizer
        self._transform = transform
        self._registration = r

        itk_kit.utils.setupITKObjectProgress(
            self, self._registration, 'BSpline Registration', 
            'Performing registration')

        itk_kit.utils.setupITKObjectProgress(
                self, self._optimizer, 
                'LBFGSOptimizer', 'Optimizing')

    def get_input_descriptions(self):
        return ('Fixed image', 'Moved image')

    def set_input(self, idx, input_stream):
        if idx == 0:
            self._fixed_image = input_stream
            self._registration.SetFixedImage(input_stream)
        else:
            self._moving_image = input_stream
            self._registration.SetMovingImage(input_stream)

    def get_output_descriptions(self):
        return ('BSpline Transform',)

    def get_output(self, idx):
        return self._registration.GetTransform()
                        
    def execute_module(self):
        # itk.Size[3]()
        # itk.ImageRegion[3]()

        # we want a 1 node border on low x,y,z and a 2 node border on
        # high x,y,z; so if we want a bspline grid of 5x5x5, we need a
        # bspline region of 8x8x8
        grid_size_on_image = [5,5,5]

        fi_region = self._fixed_image.GetBufferedRegion()

        self._registration.SetFixedImageRegion(fi_region)

        fi_size1 = fi_region.GetSize()
        fi_size = [fi_size1.GetElement(i) for i in range(3)]

        spacing = 3 * [0]
        origin = 3 * [0]
        for i in range(3):
            spacing[i] = self._fixed_image.GetSpacing().GetElement(i) * \
                math.floor(
                        (fi_size[i] - 1) / float(grid_size_on_image[i] - 1))

            origin[i] = self._fixed_image.GetOrigin().GetElement(i) \
                    - spacing[i]


        self._transform.SetGridSpacing(spacing)
        self._transform.SetGridOrigin(origin)

        bspline_region = itk.ImageRegion[3]()
        bspline_region.SetSize([i + 3 for i in grid_size_on_image])
        self._transform.SetGridRegion(bspline_region)

        num_params = self._transform.GetNumberOfParameters()
        params = itk.Array[itk.D](num_params)
        params.Fill(0.0)

        self._transform.SetParameters(params)
        self._registration.SetInitialTransformParameters(
                self._transform.GetParameters())
        
        self._optimizer.SetGradientConvergenceTolerance( 0.05 )
        self._optimizer.SetLineSearchAccuracy( 0.9 )
        self._optimizer.SetDefaultStepLength( 1.5 )
        self._optimizer.TraceOn()
        self._optimizer.SetMaximumNumberOfFunctionEvaluations( 1000 )

        self._registration.Update()

    def logic_to_config(self):
        pass

    def config_to_logic(self):
        pass


