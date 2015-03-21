# Introduction #

This shows how to add teem and vtkTeem to a binary installation of DeVIDE.  teem is great software that is used by both SciRun and slicer for diffusion tensor imaging (DTI), and now you can add it to the DeVIDE kool-aid for even more fun.

First read [AddingVTKLibsToBinaryDeVIDE](AddingVTKLibsToBinaryDeVIDE.md) for some background on building external VTK-based libaries for binary DeVIDE installations.

# Building #

## Teem ##
Download the source to teem 1.10 from [here](http://prdownloads.sourceforge.net/teem/teem-1.10.0-src.tar.gz?download).  Unpack and do an out of source build with cmake according to [these instructions](http://teem.sourceforge.net/build.html).  CMAKE\_BUILD\_TYPE should be RelWithDebInfo and BUILD\_SHARED\_LIBS should be set to on.

Use the DRE ccmake, which you can find in devide-re/cmake/bin/ccmake

## vtkTeem ##
Get a vtkTeem checkout by doing the following:
```
svn co http://svn.slicer.org/Slicer3/trunk/Libs/vtkTeem -r 8877
```

vtkTeem builds by default with TCL wrappings, but we want Python. If you decide to build vtkTeem using [Johannes](http://code.google.com/p/devide/source/browse/README.txt?repo=johannes), then the necessary changes are automatically made so that vtkTeem build with Pynthon wrappings.

Otherwise (if you're not using Johannes) you can make the required changes to the CMake config yourself:
Modify the vtkTeem CMakeLists.txt file by changing all occurrences of TCL to Python (and for example tcl to python), taking care to match capitalisation.  vtkImagingPython, vtkIOPython and vtkGraphicsPython should further get a 'D' appended, for example vtkImagingPython becomes vtkImagingPythonD.

Also add the following line to just before the vtk\_wrap\_tcl3 -> vtk\_wrap\_python3 line:
```
INCLUDE_DIRECTORIES("${VTK_PYTHON_INCLUDE_DIR}")
```

Do an out-of-source build of vtkTeem with cmake, using the DeVIDE VTK binaries as explained in [AddingVTKLibsToBinaryDeVIDE](AddingVTKLibsToBinaryDeVIDE.md) as well as the teem you just built. **Very important: As stated in the mentioned page, do all of this in a shell / command window in which you've executed "dre shell"**

You should set the VTK\_DIR, the Teem\_DIR and the CMAKE\_BUILD\_TYPE to RelWithDebInfo.

### Caveat with Windows + Python2.7 ###
If you're wrapping vtkTeem under Windows, you'll notice that the build step outputs a .dll but no .pyd file. To enable DeVIDE to load your wrapped vtkTeem you'll have to rename the .dll to .pyd !

Python2.7 works fine under Linux without any similar intervention required (outputting a .so file).

# Starting up DeVIDE #

If your vtkTeem out-of-source build was done in /some/dir/vtkTeem-build, start up DeVIDE as follows:
```
devide --extra-module-paths /some/dir/vtkTeem-build
```

It is also sufficient to copy only the .pyd (Windows) or .so (Linux) file and start devide with --extra-module-paths pointing to its containing directory.

You should now be able to do the following in the DeVIDE Window | Python Shell to test:
```
import libvtkTeem as vtkteem
r = vtkteem.vtkNRRDReader()
```