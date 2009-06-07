# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

class CodeRunner:
    kits = ['wx_kit', 'vtk_kit']
    cats = ['Viewers']
    help = \
    """CodeRunner facilitates the direct integration of Python code into a
    DeVIDE network.

    The top part contains three editor interfaces: scratch, setup and
    execute.  The first is for experimentation and does not take part in
    network scheduling.  The second, 'setup', will be executed once per
    modification that you make, at network execution time.  The third,
    'execute', will be executed everytime the module is ran during network
    execution.  You have to apply changes before they will be integrated in
    the network execution.  If you seen an asterisk (*) on the editor tab, it
    means your latest changes have not been applied.

    You can execute any editor window during editing by hitting Ctrl-Enter.
    This will execute the code currently visible, i.e. it doesn't have to be
    applied yet.  The three editor windows and the shell window below share
    the same interpreter, i.e. things that you define in one window will be
    available in all others.

    Applied code will also be saved and loaded along with the rest of the
    network.  You can also save code from the currently selected editor window
    to a separate .py file by selecting File|Save from the main menu.

    VTK and matplotlib support are included.

    To make a new matplotlib figure, do 'h1 = mpl_new_figure()'.  To close it,
    use 'mpl_close_figure(h1)'.  A list of all figures is available in
    obj.mpl_figure_handles.

    You can retrieve the VTK renderer, render window and render window
    interactor of any slice3dVWR by using vtk_get_render_info(name) where name
    has been set by right-clicking on a module in the graph editor and
    choosing 'Rename Module'.
    
    """

class CoMedI:
    kits = ['vtk_kit', 'itk_kit', 'wx_kit']
    cats = ['Viewers']
    keywords = ['compare', 'comparative visualisation',
            'comparative', 'comparative visualization']
    help = \
            """CoMedI: Compare Medical Images

            Viewer module for the comparison of arbitrary 2-D and 3-D
            medical images.
            """

class DICOMBrowser:
    kits = ['vtk_kit', 'gdcm_kit']
    cats = ['Viewers', 'Readers', 'DICOM', 'Medical']
    help = \
    """DICOMBrowser.  Does for DICOM reading what slice3dVWR does for
    3-D viewing.

    See the main DeVIDE help file (Special Modules | DICOMBrowser) for
    more information.  
    """

class histogram1D:
    kits = ['vtk_kit', 'numpy_kit']
    cats = ['Viewers', 'Statistics']

class histogram2D:
    kits = ['vtk_kit']
    cats = ['Viewers']

class histogramSegment:
    kits = ['wx_kit', 'vtk_kit']
    cats = ['Viewers']

class LarynxMeasurement:
    kits = ['wx_kit', 'vtk_kit', 'gdcm_kit']
    cats = ['Viewers']
    help = """Module for performing 2D measurements on photos of the
    larynx.

    Click the 'start' button to select a JPEG image.  On this image,
    shift click to select the apex of the larynx, then shift click
    again to select the bottom half-point.  You can now shift-click to
    select border points in a clock-wise fashion.  The POGO distance
    and area will be updated with the addition of each new point.

    You can move all points after having placed them.  Adjust the
    brightness and contrast by dragging the left mouse button, zoom
    by dragging the right button or using the mouse wheel, pan with
    the middle mouse button.

    When you click on the 'next' button, all information about the
    current image will be saved and the next image in the directory
    will be loaded.  If the next image has already been measured by
    you previously, the measurements will be loaded and shown.  This
    means that you can interrupt a measurement session at any time, as
    long as you've pressed the 'next' button after the LAST image.

    When you have measured all images (check the progress message
    box), you can click on the 'Save CSV' button to write all
    measurements to disk.  You can also do this even if you haven't
    done all measurements yet, as long as you have measured a multiple
    of three images.  The measurements will be written to disk in the
    same directory as the measured images and will be called
    'measurements.csv'.  
    """

 

class Measure2D:
    kits = ['wx_kit', 'vtk_kit', 'geometry_kit']
    cats = ['Viewers']
    help = """Module for performing 2D measurements on image slices.

    This is a viewer module and can not be used in an offline batch
    processing setting.
    """

class QuickInfo:
    kits = []
    cats = ['Viewers']
    help = """Gives more information about any module's output port.

    Use this to help identify any type of data.
    """

class SkeletonAUIViewer:
    kits = ['vtk_kit', 'wx_kit']
    cats = ['Viewers']
    help = """Skeleton module to using AUI for the interface and
    integrating a VTK renderer panel.

    Copy and adapt for your own use.  Remember to modify the relevant
    module_index.py.
    """

class slice3dVWR:
    kits = ['wx_kit', 'vtk_kit']
    cats = ['Viewers']
    help = """The all-singing, all-dancing slice3dVWR module.

    You can view almost anything with this module.  Most of its documentation
    is part of the application-central help.  Press F1 (or select Help from
    the main application menu) to see it.
    """

class Slicinator:
    kits = ['wx_kit', 'vtk_kit']
    cats = ['Viewers']
    keywords = ['segmentation', 'contour']
    help = """The Slicinator.  It will be back!
    """

class TransferFunctionEditor:
    kits = ['wx_kit', 'numpy_kit']
    cats = ['Viewers']
    help = """Transfer function editor.

    Module under heavy development.
    """

