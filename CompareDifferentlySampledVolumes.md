# Introduction #

This howto shows you how you could go about combining differently sampled and positioned volumes using the vtkImageReslice filter. This problem came up when trying to do voxel-wise math between two distance fields derived from two different meshes living in the same space with FastSurfaceToDistance. The distance fields were obviously correctly positioned, but only overlapped in a small region. For voxel-wise math you need full voxel-to-voxel correspondence.

You can use this generally to resample any volume onto the same grid as another volume.

# The example network #

![http://devide.googlecode.com/svn/wiki/help_images/combine_differently_sampled_fields.png](http://devide.googlecode.com/svn/wiki/help_images/combine_differently_sampled_fields.png)

We combine both meshes with an appendPolyData, then turn that into a distance field too so that we can give it to the image reslicers as an example of the output extent, origin and spacing that we want. We could have been less lazy, and just calculated this based on the bounds of the two separate distance fields.

# The CodeRunner code #

## Setup tab ##

```
irs0 = vtk.vtkImageReslice()
irs0.SetInterpolationModeToLinear()

irs1 = vtk.vtkImageReslice()
irs1.SetInterpolationModeToLinear()
```

## Execute tab ##

```
# this is just to do all of these calls on both irs0 and irs1
# and to connect their in/outputs to the correct module in/outputs
for idx, irs in enumerate([irs0, irs1]):
    irs.SetInformationInput(obj.inputs[2])
    irs.SetInput(obj.inputs[idx])
    irs.Update()
    obj.outputs[idx] = irs.GetOutput()
```