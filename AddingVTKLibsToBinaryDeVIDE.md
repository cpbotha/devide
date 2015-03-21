# Introduction #

You have a binary DeVIDE-RE installation, but you've written some of your own VTK C++ code and would like to use that with your DeVIDE-RE without having to rebuild the WHOLE beast.  Now you can, and this page explains how.

# Linux #

  1. Start up a DRE capable shell and use this to follow the instructions below:
```
dre ipython
>>> import os
>>> os.system('bash')
```
  1. Use the cmake 2.8.x included in the DRE to build your code.
    * An out-of source build is recommended.  Let's call that directory "vtkmy-build" for now, and its full path "/fulldir/vtkmy-build".
```
mkdir /fulldir/vtkmy-build
cd /fulldir/vtkmy-build
/full/path/to/devide-re/cmake/bin/ccmake /fulldir/vtkmy-source/
```
    * You're going to have to point cmake variable VTK\_DIR at the DRE VTK directory.  This should be devide-re/inst/VTK/lib/vtk-5.8
    * Use CMAKE\_BUILD\_TYPE `RelWithDebInfo`.
  1. Do the build:
```
cd /fulldir/vtkmy-build
make
```

## Problems ##

  * It could be that you run into something like this:
```
-- Configuring done
-- Generating done
-- Build files have been written to: /home/cbotha/vtk4307-build
make[2]: *** No rule to make target `/usr/lib/libXt.so', needed by `bin/libvtk4307Graphics.so'.  Stop.
make[1]: *** [Graphics/CMakeFiles/vtk4307Graphics.dir/all] Error 2
make: *** [all] Error 2
```
> In that case, first make sure that you have libXt.so (or whichever library it is complaining about) installed.  It could be that it's hiding in /usr/lib64 (or somewhere else), in which case you should edit the VTK/lib/vtk-5.2/VTKLibraryDepends.cmake file to reflect this.

## Starting up DeVIDE ##
  * Edit your dre.cfg to add the necessary paths to the env:ld\_library\_path (location of the relevant .py file) and env:pythonpath (location of the relevant .py file AS WELL AS the location of the .so files, separated with a colon) sections.
  * **OR** startup DeVIDE with a comma-separated extra-module-paths parameter. When including multiple paths remember to enclose the whole comma-separated path-list in quotation marks, e.g.:
```
# [dre] devide --extra-module-paths "/path/to/so-files,/path/to/py-files"
# in other words:
devide --extra-module-paths "/fulldir/vtk4307/bin,/fulldir/vtk4307/Wrapping/Python"
```

# Windows #

You'll probably need to use the same compiler version for your library as the one used to build the DRE. For the binary distributions of DeVIDE, this is Visual Studio 2008.
  * BEFORE version 12.2.7, there was an [issue](http://code.google.com/p/devide/issues/detail?id=157) where the VTK configuration contains invalid paths. Edit **both** `VTKConfig.cmake` and `VTKLibraryDepends.cmake` in `\DeVIDE-RE\VTK\lib\vtk-5.4`, and replace all instances of `C:/build/jwd/inst/` with `${VTK_INSTALL_PREFIX}/../`.
  * IN version 12.2.7, there is a new issue where the VTK configuration contains invalid paths. Edit 'VTKTargets-relwithdebinfo.cmake' in `\DeVIDE-RE\VTK\lib\vtk5-8`, and replace the one instance of `C:/build/jwd/inst/` with `${VTK_INSTALL_PREFIX}/../`. This has been [fixed in source](http://code.google.com/p/devide/source/detail?r=b38c6914e7b829cf802c5a09d30591c4bbf603eb&repo=johannes), releases after 12.2.7 will not have this problem.
  * To help CMake find the correct libraries, first get the environment setup properly. Start a Visual Studio command prompt and get a DRE shell by doing the following:
```
dre ipython
>>> import os
>>> os.system('cmd')
```
  * Using this command prompt, navigate to the build directory for your project and start cmake:
```
> cd c:\MyProject\MyBuildDir
> "c:\Program Files\CMake 2.6\bin\cmake-gui.exe"
```
  * Using the cmake GUI, set the source path and press configure. When this is done, check if the VTK\_DIR path discovered by cmake points to your DRE installation. On a typical installation the path will be something like `C:\Program Files\DeVIDE-RE\VTK\lib\vtk-5.4`.
  * Press configure again, generate the project files and build the resulting solution (`MyProject.sln`) using Visual Studio. Make sure you build at least the `RelWithDebInfo` configuration of the solution.
  * Edit `dre.cfg` in the DRE directory and add the appropriate paths to your library (`RelWithDebInfo` version) to the `[env:path]` and `[env:pythonpath]` sections.
  * **OR** startup DeVIDE with a comma-separated extra-module-paths parameter. When including multiple paths remember to enclose the whole comma-separated path-list in quotation marks, e.g.:
```
# [dre] devide --extra-module-paths "/path/to/so-files,/path/to/py-files"
# in other words:
devide --extra-module-paths "/fulldir/vtk4307/bin,/fulldir/vtk4307/Wrapping/Python"
```


# Notes #

If you don't have your own VTK library to play with, you could start with vtk4307 at http://in4307.googlecode.com/

Here is a very quick step-by-step on how you would do this, assuming that you've downloaded and unpacked VTK and cmake as explained above.  Also, you will have to have all development libraries and compilers installed.  On Debian / Ubuntu systems, this should do the trick:
```
sudo apt-get install cvs subversion chrpath g++ gcc\
libsqlite3-dev libncurses-dev libgtk2.0-dev\
libxt-dev libfreetype6-dev libpng12-dev libz-dev libbz2-dev\
libgl1-mesa-dev libglu1-mesa-dev
```

Now for that step-by-step:
```
# NB: note that we're checking out the vtk4307 subdir !!
# it should contain a file called CMakeLists.txt
/tmp$ svn checkout http://in4307.googlecode.com/svn/trunk/vtk4307
/tmp$ mkdir vtk4307-build
/tmp$ cd vtk4307-build
/tmp/vtk4307-build$ /where/you/installed/cmake/bin/ccmake ../vtk4307
# when ccmake starts up, press 'c', then fill in 
# the build type and the VTK dir as explained above
# then keep on pressing 'c' until you can press 'g'
# EXIT from ccmake
/tmp/vtk4307-build$ make
# now we choose to startup devide with extra-module-paths instead of editing dre.cfg
devide --extra-module-paths /tmp/vtk4307-build/bin,/tmp/vtk4307-build/Wrapping/Python
```