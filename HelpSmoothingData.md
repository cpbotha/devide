There are a number of filters in DeVIDE that can be used for smoothing volume data.

Filters.imageGaussianSmooth performs a straight-forward Gaussian smoothing (also known as "blurring'' in some image processing packages). The standard deviation (in pixels) can be set for all three dimensions. A truncation, or cut-off, can also be set for all three dimensions. Take into account the resolution of your image when selecting these parameters.

!curvatureFlowDenoising, !curvatureAnisotropicDiffusion and !gradientAnisotropicDiffusion, all in the "Insight'' module category, are more advanced smoothing algorithms that attempt to smooth homogeneous regions whilst retaining edge information. These are all compute- intensive ITK-based filters. Please read the tooltips available in the configuration windows: i.e. double click on the module and then let your mouse hover over any of the input boxes to get more information about the variable required for that input box. The defaults are naturally good values to start with.

When you use these with VTK data, for example the output of a vtiRDR, you have to use a VTKtoITK conversion module. To visualise the output, you need to convert back to VTK data by making use of an ITKtoVTK module. However, if you're planning to use the output in an ITK filter, for example the !demonsRegistration, you don't need an ITKtoVTK conversion module at the output. The figure below shows an example of this:

![http://devide.googlecode.com/svn/wiki/help_images/smoothing_ex_dvn.png](http://devide.googlecode.com/svn/wiki/help_images/smoothing_ex_dvn.png)