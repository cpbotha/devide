# Linux #

  1. Make sure you've followed the instructions on how to upgrade your DeVIDE installation to development: [UpdateDeVIDE12\_2ToDEV](UpdateDeVIDE12_2ToDEV.md) -- you're going to need the PIP fix.
  1. Install or have someone install the following packages on your machine: libatlas-dev (for blas), liblapack-dev and gfortran (gnu fortran 95 compiler).
  1. Do the following magic incantation at the shell prompt:
```
dre shell
pip install scipy
```
  1. Your system will now download and compile scipy.

You should now be able to do
```
import scipy
print scipy.version.version
```

# Windows #

  1. Download numpy-MKL-1.6.2rc1.win32-py2.7.‌exe and scipy-0.10.1.win32-py2.7.‌exe from http://www.lfd.uci.edu/~gohlke/pythonlibs/
  1. Use 7-zip or a similar tool to unpack these exe files (there are secret ZIP files embedded in them! probably by spies!)
  1. In both of the unpacked directories, locate the PLATLIB directory, and within that a directory called scipy or numpy, depending on the relevant downloaded archive.
  1. Copy both of these (numpy and scipy) directories to DeVIDE-RE\python\Lib\site-packages\ (you should find the default numpy already there).
  1. After having startup up DeVIDE, you should be able to import scipy at any of the python prompts.

You might be wondering why we don't package these with DeVIDE to begin with. Well, it's a long story starting with the lack of free fortran compilers on Windows 64, and ending with the fact that Gohlke's numpy and scipy binaries that are required to get this working can't be redistributed due to the Intel Math Kernel Libraries that they were built with.