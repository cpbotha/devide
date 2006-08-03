class cptBrepWRT:
    kits = ['vtk_kit']
    cats = ['Writers']
    help = """Writes polydata to disc in the format required by the Closest
    Point Transform (CPT) driver software.  Input data is put through
    a triangle filter first, as that is what the CPT requires.

    See the
    <a href="http://www.acm.caltech.edu/~seanm/projects/cpt/cpt.html">CPT
    home page</a> for more information about the algorithm and the
    software.
    """


class ivWRT:
    kits = ['vtk_kit']
    cats = ['Writers']
    help = """ivWRT is an Inventor Viewer polygonal data writer devide module.
    """


class metaImageWRT:
    kits = ['vtk_kit']
    cats = ['Writers']
    help = """Writes VTK image data or structured points in MetaImage format.
    """

class pngWRT:
    kits = ['vtk_kit']
    cats = ['Writers']
    help = """Writes a volume as a series of PNG images.

    Set the file pattern by making use of the file browsing dialog.  Replace
    the increasing index by a %d format specifier.  %3d can be used for
    example, in which case %d will be replaced by an integer zero padded to 3
    digits, i.e. 000, 001, 002 etc.  %d starts from 0.

    Module by Joris van Zwieten.
    """


class stlWRT:
    kits = ['vtk_kit']
    cats = ['Writers']
    help = """Writes STL format data.
    """

class vtiWRT:
    kits = ['vtk_kit']
    cats = ['Writers']
    help = """Writes VTK image data or structured points in the VTK XML
    format. The data attribute is compressed.

    This is the preferred way of saving image data in DeVIDE.
    """

class vtkPolyDataWRT:
    kits = ['vtk_kit']
    cats = ['Writers']
    help = """Module for writing legacy VTK polydata.  vtpWRT should be
    preferred for all VTK-compatible polydata storage.
    """

class vtkStructPtsWRT:
    kits = ['vtk_kit']
    cats = ['Writers']
    help = """Module for writing legacy VTK structured points data.  vtiWRT
    should be preferred for all VTK-compatible image data storage.
    """

class vtpWRT:
    kits = ['vtk_kit']
    cats = ['Writers']
    help = """Writes VTK PolyData in the VTK XML format.  The data attribute
    is compressed.

    This is the preferred way of saving PolyData in DeVIDE.
    """



