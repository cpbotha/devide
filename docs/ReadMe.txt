Introduction
------------

DeVIDE, or the Delft Visualisation and Image Processing Development
Environment, previously known as DSCAS3, was created as part of my Ph.D.
research in the Data Visualisation Group of the Delft University of
Technology.  DeVIDE is a software platform for the rapid prototyping,
testing and deployment of visualisation and image processing algorithms.

See http://cpbotha.net/DeVIDE for more info.

Platform-specific notes
-----------------------

Windows:
* DeVIDE is only supported on Windows 2000, XP and newer.
* Make sure you're up to date with the latest service packs and Microsoft
  hotfixes for your specific operating system.  http://www.windowsupdate.com/
  will do all of this automatically.

Build notes
-----------

Getting wxPython 2.6.1.0 to build on RHEL3 64 bits:
../configure --prefix=/home/cpbotha/opt/wx/2.6 --with-gtk --with-opengl \\
--enable-geometry --disable-display --enable-unicode \\
--x-libraries=/usr/X11R6/lib64

Architecture note
-----------------

As is the case with all things Python, this is not absolute, but try
never to call module methods directly: always work via the
moduleManager.

$Id$
