# $Id$

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

class histogram1D:
    kits = ['vtk_kit']
    cats = ['Viewers', 'Statistics']

class histogram2D:
    kits = ['vtk_kit']
    cats = ['Viewers']

class histogramSegment:
    kits = ['wx_kit', 'vtk_kit']
    cats = ['Viewers']

class Measure2D:
    kits = ['wx_kit', 'vtk_kit', 'geometry_kit']
    cats = ['Viewers']
    help = """Module for performing 2D measurements on image slices.

    This is a viewer module and can not be used in an offline batch
    processing setting.
    """

class slice3dVWR:
    kits = ['wx_kit', 'vtk_kit']
    cats = ['Viewers']
    help = """The all-singing, all-dancing slice3dVWR module.

    You can view almost anything with this module.  Most of its documentation
    is part of the application-central help.  Press F1 (or select Help from
    the main application menu) to see it.
    """

#class TFEditor:
#    # needs numpy for the wx FloatCanvas
#    kits = ['wx_kit', 'numpy_kit']
#    cats = ['Viewers']
#    help = """Transfer function editor.
#
#    Module under heavy development.
#    """

