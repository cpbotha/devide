# The problem #

Font rendering as of 2008-05-24:

[![](http://lh5.ggpht.com/cpbotha/SDfllW_8XgI/AAAAAAAAC1k/CJmuuF5Nb4c/s400/ge_shitty_fonts1.png)](http://picasaweb.google.com/cpbotha/Screenshots/photo#5203880324441595394)

Font scaling is not consistent for the whole network, mostly due to the way the vtkTextActor scaling mode works (specify a box into which the text must fit) and the fact that its vertical justification is broken.

# Solution #

Fixed the whole vtkTextActor3D (my changes are checked into main VTK CVS), and this is the slightly less ugly but miles more consistent result:

[![](http://lh6.ggpht.com/cpbotha/SFKBW2IMkZI/AAAAAAAAC5Q/ksFddFxb5n8/s400/devide-85-newstyle-graph-editor.png)](http://picasaweb.google.com/cpbotha/Screenshots/photo#5211369948308083090)