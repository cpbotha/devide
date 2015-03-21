# Introduction #

One day, the slice3dVWR will have easy to use measurement tools.  Until then, you can use work-arounds like this one, with which you can interactively place and fit ellipsoids in a 3D scene and then read out their centres and dimensions.

# Details #

First connect up the network:
  * connect second output of superQuadric to slice3dVWR
  * set superQuadric as follows:
    * toroidal off
    * size: 1
    * scale: pick some good initial scaling, for example 10,10,20

Then manually fit the ellipsoid:
  * move ellipsoid by right-clicking on the object, selecting "motion on" then dragging with middle button
  * resize ellipsoid by dragging with right mouse button
  * you can constrain motion to a plane by selecting the plane, then right clicking the object in the controls window and selecting "constrain motion"; unconstrain by selecting NO planes, then selecting "constrain motion" again.

Finally read out its size (on all three axes) and centre:
  * NB switch off motion (this will apply all transforms)
  * select "configure the object" in the objects part of the slice3dVWR controls window
  * left click on the ellipsoid in the scene
  * double click on the Actor in the dialog that appears
  * in the bottom part, type:
    * obj.GetPosition() to get the centre of the ellipsoid
    * obj.GetScale() to get the scale factor, should be 3 times the same.  Multiply this with the superQuadric scale factors you chose to calculate the true size.

# Thanks #

Thanks to Ali Nikooyan for suggesting this application!