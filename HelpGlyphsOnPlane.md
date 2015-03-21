If a vector dataset is available, such as a deformation field, the vector field can be visualised by making use of the Filters|glyphs module. However, this module visualises the complete vector field.

One can also visualise only the vectors on the current slices in the slice3dVWR. To do this, build a network as shown below:

![http://devide.googlecode.com/svn/wiki/help_images/glyphs_on_plane_dvn.png](http://devide.googlecode.com/svn/wiki/help_images/glyphs_on_plane_dvn.png)

The slice3dVWR outputs a poly data representing the geometry of all current slice planes. In this case, we use it as a probe input so that we can visualise arrow glyphs located on the plane.  If the slice is moved, the glyphs will update automatically.

Remember that the opacity of slices can be adjusted (Slices menu: "Set Opacity'') so that visualising a background slice along with the deformation vectors on it is easier.