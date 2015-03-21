# Introduction #

This shows how to implement the interactive advection balls mentioned in:

_[C. P. Botha, T. de Graaf, S. Schutte, R. Root, P. Wielopolski, F. C. van der Helm, H. J.  Simonsz, and F. H. Post, MRI-based visualisation of orbital fat deformation during eye motion, in Visualization in Medicine and Life Sciences, 2007.](http://visualisation.tudelft.nl/publications/botha2007.pdf)_

The illustration is slightly out of date, but the principle still holds and should work in the current DeVIDE release.

# Description #

The figure below shows how to perform interactive probing and warping (advection) with DeVIDE:

![http://devide.googlecode.com/svn/wiki/help_images/probing_and_warping_dvn.png](http://devide.googlecode.com/svn/wiki/help_images/probing_and_warping_dvn.png)

The volume data has been loaded with vtkRDR dvm11 and serves as context in the slice3dVWR. In this case, we are using two vector fields, loaded with respectively metaImageRDR dvm7 and dvm11fyi11. Points that have been selected and stored with the slice3dVWR (these can be changed at any time, the network updates interactively) are changed into spherical shells of points by the pointsToSpheres module dvm6ldz6. The output of this module can be connected to the slice3dVWR to view the initial sphere.

The first probeFilter dvm7fxg7 maps and interpolates the vectors from the first vector field onto the points of the spherical cloud. Connect the output of the probeFilter to the warpPoints module. After connecting the warpPoints input, make sure to "Execute'' and "Apply'' the warpPoints module once. The correct "Vectors selection'' can then be made from its View/Config window. "Default Active Vectors'' is very often NOT what you want. Experiment with this. After having made this selection, "Apply'' or "Execute'' the module again. Now you can connect its output to the slice3dVWR. The points are advected by the vectors that you have associated to them.

This output is also used in the next advection step, using the next vector field. Once again, make sure to select the correct vectors in the warpPoints module View/Config window. You could also simply copy and paste the first probeFilter and warpPoints module (AFTER you've performed the vector selection step), in which case the selection will already be correct.

Add as many of these steps as are necessary to complete the full advection with all your available vector fields. At each step, check that your sphere is being correctly advected before you continue.