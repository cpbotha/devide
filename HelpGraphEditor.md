# Introduction #
The DeVIDE Graph Editor is a visual programming interface where glyphs representing the underlying DeVIDE modules can be connected together to form new programs.

It's the most flexible way of working with DeVIDE, short of directly interfacing with the underlying code.

This chapter will give a brief overview of graph editor usage.

# A small sample network #

## Constructing the network ##

Start by building the network shown in the figure below. First select the "Sources'' category on the top left of the Graph Editor. Drag and drop the "superQuadric'' module from the modules list on the bottom left to the canvas. You should see the "superQuadric'' glyph being created.

![http://devide.googlecode.com/svn/wiki/help_images/ge_samplenetworkb1.png](http://devide.googlecode.com/svn/wiki/help_images/ge_samplenetworkb1.png)

Now do the same for the "slice3dVWR'' module in the "Viewers'' category. Note that you can select multiple categories by holding the Shift key and clicking a category (this will select all categories between the previous selected category and your current click) or holding the control key and clicking (this will select the currently clicked module along with any previously selected modules). The module list will contain all modules in all selected categories. The modules are always alphabetically sorted.

Connect the second output of the "superQuadric'' glyph to any input of the "slice3dVWR'' glyph by dragging the mouse, with the left button depressed, from the output port to the input port. Note that hovering the mouse pointer over any port shows more information about that port in the status bar of the Graph Editor.

## Admiring your results ##
Now press F5 or select Network | Execute from the main menubar to execute the network.

Right-click on the slice3dVWR module and select "View-Configure'' to see the 3D surface representing the 0-surface of the generated Super Quadric. Note that this is how one activates the graphical interface of any glyph on the canvas. You can rotate your viewpoint around the generated 3D object by dragging with your left mouse button. Dragging with the right button will zoom. Dragging with the middle button will pan the viewpoint.

The network can be saved by selecting "Save'' from the "File'' menu. The default extension for a DeVIDE network is .dvn.

## Warping the Super Quadric ##
The slice3dVWR is a very special DeVIDE module. Because of this, its View/Config interface is non-standard. Right click on the "superQuadric'' glyph and select "View-Config'' to see a more standard user interface (you can also just double-click on the glyph, many users find this to be quicker). This interface is shown in the figure below:

![http://devide.googlecode.com/svn/wiki/help_images/ge_samplenetworkb2.png](http://devide.googlecode.com/svn/wiki/help_images/ge_samplenetworkb2.png)

Most module View/Config windows have the set of buttons at the bottom. If you make any changes to any of the module parameters, you have to click on the "Apply'' button (in which case the parameters will be transferred to the underlying logic) or the "Execute'' button, (in which case the new parameters will be transferred to the underlying logic and the module will be asked to re-perform its execution with the modified parameters). Clicking on the "Cancel'' button will undo any changes you've made without applying and close the window.  Clicking on "OK" will apply all changes and close the window.

Change the "Phi Roundness'' parameter to 3.0 and click on "Execute'' or simply press F5 or Alt-X. Pressing one of these key-combinations is effectively the same as clicking on "Execute''. See the results of your changes in the slice3dVWR window.