# Introduction #
This is probably the module you'll use most often.  It's also the first thing you should try whenever you have any data you'd like to visualise.  Simply connect the output of any data- generating or filtering module to any input of the slice3dVWR and execute the network.  The slice3dVWR picks a suitable default visualisation based on the input data you supply.

# Slices #
When a volume has been connected to an input of the slice3dVWR, the volume can be examined by "slicing'' through it. By default, an axial slice is created automatically, but any number of additional slices can be activated.

Move the slice by dragging with your middle mouse button, or with Ctrl-MouseWheel.

# Overlay modes #
The slice3dVWR has several overlay modes. These modes make it possible to visualise the correspondence between multiple inputs, for e.g. original CT data and a segmentation. If a second volume input is connected, the slice3dVWR checks if the dimensions of the already connected volume. If this is the case, the connection is allowed and the second volume is overlayed (superimposed) on the first.

There are several ways to perform this overlay. This setting is user-configurable and its user interface can be found on the "Main'' tab of the slice3dVWR "Controls'' window, in the "Slices'' section. The user interface consists of an Overlay Mode choice box and an Alpha slider. The alpha slider determines the alpha parameter used for the fusion-based overlay modes.
  * Green Fusion: The overlay is composited with the user-defined alpha parameter. The value (i.e. brightness) is directly related to the image intensity of the overlay, so we see shades of green (reflecting the overlay intensity) alpha blended with the primary input.
  * Red Fusion: Same as above, except with shades of red.
  * Blue Fusion: Same as above, except with shades of blue.
  * Hue Fusion: The value is kept constant, but the hue is directly related to the overlay image intensity. The overlay is alpha blended with the user-supplied alpha parameter.
  * Hue/Value Fusion: Hue and brightness are directly related to the overlay image intensity. The overlay is alpha-blended with the user-supplied alpha parameter.
  * Green Opacity Range: The opacity of the overlay is directly related to its image intensity. The hue is constant green and the brightness is constant unity.
  * Blue Opacity Range: The same as above, except the hue is constant red.
  * Blue Opacity Range: The same as above, except the hue is constant blue.
  * Hue Opacity Range: The hue and the opacity of the overlay are directly related to the overlay image intensity.

Adjusting the alpha slider whilst one of the "fusion'' overlay modes is active will result in real- time changes. The idea is to adjust it up and down its complete range in order to get a better idea of the amount of the image correspondence.