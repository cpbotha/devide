class EmphysemaViewer:
    kits = ['vtk_kit']
    cats = ['Viewers']
    help = """Module to visualize lungemphysema from a CT-thorax scan and a lung mask.

    EmphysemaViewer consists of a volume rendering and two linked slice-based views; one with the original data and one with an emphysema overlay. The volume rendering shows 3
    contours: the lungedges and 2 different contours of emphysema; a normal one and a severe one. 

    There are two ways of setting the emphysema values. 
    - The first way is choosing the 'default' values, which are literature-based. They are set on -950 HU (emphysema) and -970 HU (severe). 
    - The other way is a computational way: The lowest 11% values, that are present in the data are marked as emphysema, the lowest 8,5% values are marked as severe emphysema. The
    theory behind this is the hypothesis that the histograms of emphysema patients differ from healthy people in a way that in emphysema patients there are relatively more lower
    values present. 
    In both ways you can finetune the values, or completely change them (if you want to). 

    After loading your image data and mask data, you can inspect the data and examine the severity of the emphysema of the patient. 

    Controls:\n
    LMB: The left mouse button can be used to rotate objects in the 3D scene, or to poll Houndsfield Units in areas of interest (click and hold to see the values)\n
    RMB: For the slice viewers, you can set the window and level values by clicking and holding the right mouse button in a slice and moving your mouse. You can see the current
    window and level values in the bottom of the viewer. Outside of the slice, this zooms the camera in and out\n
    MMB: The middle mouse button enables stepping through the slices if clicked and held in the center of the slice. When clicking on de edges of a slice, this re-orients the
    entire slice. Outside of the slice, this pans the camera\n
    Scrollwheel: The scrollwheel can be used for zooming in and out of a scene, but also for sliceviewing if used with the CTRL- or SHIFT-key\n
    SHIFT: By holding the SHIFT-key, it is possible to use the mouse scrollwheel to scroll through the slices.\n
    CTRL: Holding the CTRL-key does the same, but enables stepping through the data in steps of 10 slices.\n
    """
