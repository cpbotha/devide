# Introduction #

Major new direction: DeVIDE will be getting visual analysis and information visualisation functionality, through better integration of matplotlib and [VTK Titan](http://titan.sandia.gov/).

# Miscellaneous #

  * Upgrading to:
    * VTK 5.6
    * matplotlib 1.0.0
  * johannes (the build system) will get simple versioned packages, e.g. vtk-5.4 or vtk-5.6. This means if you use johannes to build your own VTK / ITK / matplotlib environment, you'll be able to specify versions for everything.

# Build notes #

  * Will try python 2.7.
  * Will try to build numpy 1.5.0 on Windows 64 (this was missing from previous win64 builds) OR:
  * Christoph Gohlke has built **everything**! http://www.lfd.uci.edu/~gohlke/pythonlibs/