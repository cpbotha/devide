# Introduction #

This shows how to read vector-valued NRRD files using ITK, for example the GK's DTI datasets.

# Details #

Make sure that you have a correct "kind" field.  In Gordon's helix dataset, this is missing.  You should add:
```
kind: vector space space space
```
(I got segfaults without it.)

Because of "sizes: 7 38 39 40", you should get a 38x39x40 volume with 7-component vectors using the code below:

```
# if the "kind" field in your NRRD is correct, e.g. kind: vector space space space
# this should work.

# this is a variable length vector in a 3D image
vitf3 = itk.VectorImage[itk.F,3]
# then make the reader for it
fr2 = itk.ImageFileReader[vitf3].New()
fr2.SetFileName('c:/tmp/dti/dt-helix.nhdr')
fr2.Update()

# the output is a 3-D image of variable length vectors
o = fr2.GetOutput()

# now write out as multi-component metaimage file
fw = itk.ImageFileWriter.VIF3.New()
fw.SetInput(fr2.GetOutput())
fw.SetFileName('c:/tmp/dti/dt-helix.mha')
fw.Write()
```

# Notes #

  * This is not the best way to read and process these things in ITK+VTK, because VTK wants full 3x3 tensors (although they are symmetric!) and you'd have to code that up (in Python).  See [AddingVTKTeem](AddingVTKTeem.md) for details on how to use vtkTeem with DeVIDE, this has built-in support for reading NRRD tensor files into VTK tensor representation.
  * If the kind is 3D-masked-symmetric-matrix (instead of vector), the NRRD code gives you only the 6 unique components of the diffusion tensor, and not the confidence / mask (the first component).