# Introduction #

The most recent stable release of DeVIDE is version 12.2.7.  See [the 12.2 series release notes](ReleaseNotes12_2.md) for more information on this series.

There are two ways of getting DeVIDE: in easy-to-install and compact binary form (**the DRE**), or the slightly more complex build-it-yourself way.

**If you're not sure what you need, go for the binaries.**  With these you can build networks and even program new modules in Python or in C++, making use of all the included libraries (VTK, ITK, numpy, matplotlib, stats, geometry).

If you're on a platform that there are no binaries for, or you would like a complete DeVIDE build tree (including builds of ITK, VTK and a bunch of other useful things), you're going to have to build your own using our superbly ugly but terribly useful automatic build system, johannes.  It can take care of building all dependencies all by itself.

# Binaries #

Binaries are available for Windows and Linux, 64 and 32 bit. We highly recommend using the 64 bit binaries if that is at all possible.

| Windows x86 (32bit) |[devide-re-v12.2.7-win32-setup.exe](http://graphics.tudelft.nl/~cpbotha/files/devide/win32/devide-re-v12.2.7-win32-setup.exe)|196M|
|:--------------------|:----------------------------------------------------------------------------------------------------------------------------|:---|
| Windows x64 (64bit) installer **recommended on Windows** |[devide-re-v12.2.7-win64-setup.exe](http://graphics.tudelft.nl/~cpbotha/files/devide/win64/devide-re-v12.2.7-win64-setup.exe)|222M|
| Windows x64 (64bit) portable ZIP |[devide-re-v12.2.7-win64-portable-zip](http://graphics.tudelft.nl/~cpbotha/files/devide/win64/devide-re-v12.2.7-win64-portable.zip)|215M|
| Linux x86 (32bit) | [devide-re-v12.2.7-lin32.tar.bz2](http://graphics.tudelft.nl/~cpbotha/files/devide/lin32/devide-re-v12.2.7-lin32.tar.bz2)|176M|
| Linux x86\_64 (64bit) **recommended on Linux** | [devide-re-v12.2.7-lin64.tar.bz2](http://graphics.tudelft.nl/~cpbotha/files/devide/lin64/devide-re-v12.2.7-lin64.tar.bz2)|186M|

**NB: While you're downloading, please read the [DeVIDEQuickStart](DeVIDEQuickStart.md) guide!**

**NB: If you're not able download the binaries due to bandwidth constraints, let me know (for example via the [mailing list](http://groups.google.com/group/devide-users)) so I can send you a CD-R with all four binaries.**

If you're planning on any kind of serious processing, for example on DICOM datasets of a few hundred megabytes, you should really try to get your hands on some 64 bit hardware.

# Building your own from source #

You should only be here if you are planning to compile your own source code.  For most other end-user purposes, the binaries above should be sufficient.

So, you've decided that you're brave enough for johannes.  Clone johannes:
```
hg clone https://code.google.com/p/devide.johannes/ 
```

Read the included http://code.google.com/p/devide/source/browse/README.txt?repo=johannes file to get started.