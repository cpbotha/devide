# Introduction #

Stef Busking has added a VTK and Python layer to his NQVTK library, meaning that this can now also be used in DeVIDE.

The mentioned libraries will be available as open source soon.  At the moment, they are only available to members of the TUD Vis group.

# Instructions #

  1. Get and build NQVTK from https://graphics.tudelft.nl/svn/mfmv/stef/Source/NQVTK
  1. Follow the instructions on [AddingVTKLibsToBinaryDeVIDE](AddingVTKLibsToBinaryDeVIDE.md) for adding VTK libraries to the DRE to get the latest vtktud integrated.
  1. Try this example network: [nqvtktest.dvn](http://code.google.com/p/devide/source/browse/trunk/devide/examples/nqvtktest.dvn) and use your own VTP files
  1. If all went according to plan, you should see something like the image at the bottom of this post.
  1. You can now either use NQVTK from the DeVIDE user interface, or from any application that you start with the DRE.

<img src='http://devide.googlecode.com/svn-history/r3829/wiki/help_images/devide-nqvtk.png' width='600'>