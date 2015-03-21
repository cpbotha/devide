# Introduction #

The Slicinator is to be a DeVIDE viewer module for the slice-by-slice contouring of datasets.

An important difference with other solutions is that all contours are internally handled as distance fields (where possible) and masks otherwise.  This greatly facilitates contour arithmetic: Adding / subtracting contours, interpolating between slices, etc.

A very basic skeleton has been started: http://code.google.com/p/devide/source/browse/trunk/devide/modules/viewers/Slicinator.py

# General requirements #

  * Input dataset (supplied by other DeVIDE modules) is shown in a combined sliceviewer (use [CMSliceViewer](http://code.google.com/p/devide/source/browse/trunk/devide/modules/viewers/comedi_utils.py) for this).
  * Besides the sliceviewer, there is an orthogonal slice view (vtkImageColorViewer should help you here, see [LarynxMeasurement.py](http://code.google.com/p/devide/source/browse/trunk/devide/modules/viewers/LarynxMeasurement.py) for an example).
  * One can draw contours on the slice view.  All drawn contours belong to the current default object.
  * At any time, a new object can be created, or one can switch to an old object.  The selected object is the current context, and all new contours belong to the current object.
  * There are a number of per-slice tools available: draw, livewire, erase within newly drawn contour (done with subtraction), add newly drawn contour, region grow, smooth, etc.  All of these internally operate on the pixel mask / distance field.  Easy peasy.
  * There are a number of per-object tools available: interpolate, save, load, etc.
  * Drawn contours are also shown in the 3D combined sliceviewer view.
  * Also see the comments at the start of the current [Slicinator](http://code.google.com/p/devide/source/browse/trunk/devide/modules/viewers/Slicinator.py) for links to examples (for implementing line-drawing on slices in VTK etc) and also more hints as to the development.

## Nice-to-have requirements ##

# Other examples to study #

  * The MITK slice-by-slice segmentation app: http://www.mitk.org/wiki/Interactive_segmentation (NB see the movie)
  * MIPAV: http://mipav.cit.nih.gov/
  * Amira - not open source, no license available, but slice-by-slice tool is highly regarded.
  * VTK livewire example: http://markmail.org/message/f6keato2ovhmc23i#query:vtk%20livewire+page:1+mid:rahnxhvszlyb64kg+state:results