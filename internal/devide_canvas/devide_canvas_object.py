# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

from module_kits.misc_kit.mixins import SubjectMixin
import vtk

# z-coord of RBB box
RBBOX_HEIGHT = 1 

class UnfilledBlock:
    """Create block outline.
    """
    def __init__(self):

        self.polydata = lp = vtk.vtkPolyData()

        pts = vtk.vtkPoints()
        pts.InsertPoint(0, 0, 0, 0)
        pts.InsertPoint(1, 1, 0, 0)
        pts.InsertPoint(2, 1, 1, 0)
        pts.InsertPoint(3, 0, 1, 0)
        lp.SetPoints(pts)

        cells = vtk.vtkCellArray()
        cells.InsertNextCell(5)
        cells.InsertCellPoint(0)
        cells.InsertCellPoint(1)
        cells.InsertCellPoint(2)
        cells.InsertCellPoint(3)
        cells.InsertCellPoint(0)
        lp.SetLines(cells)

    def update_geometry(self, width, height, z):
        lp = self.polydata
        pts = lp.GetPoints()
        pts.SetPoint(0, 0,0,z)
        pts.SetPoint(1, width, 0, z)
        pts.SetPoint(2, width, height, z)
        pts.SetPoint(3, 0, height, c)
        # FIXME: is there no cleaner way of explaining to the polydata
        # that it has been updated?
        lp.SetPoints(None)
        lp.SetPoints(pts)

class FilledBlock:
    """Create filled block.
    """
    def __init__(self):

        self.polydata = lp = vtk.vtkPolyData()

        pts = vtk.vtkPoints()
        pts.InsertPoint(0, 0, 0, 0)
        pts.InsertPoint(1, 1, 0, 0)
        pts.InsertPoint(2, 1, 1, 0)
        pts.InsertPoint(3, 0, 1, 0)
        lp.SetPoints(pts)

        cells = vtk.vtkCellArray()
        cells.InsertNextCell(5)
        cells.InsertCellPoint(0)
        cells.InsertCellPoint(1)
        cells.InsertCellPoint(2)
        cells.InsertCellPoint(3)
        lp.SetPolys(cells)

    def update_geometry(self, width, height, z):
        lp = self.polydata
        pts = lp.GetPoints()
        pts.SetPoint(0, 0,0,z)
        pts.SetPoint(1, width, 0, z)
        pts.SetPoint(2, width, height, z)
        pts.SetPoint(3, 0, height, z)
        # FIXME: is there no cleaner way of explaining to the polydata
        # that it has been updated?
        lp.SetPoints(None)
        lp.SetPoints(pts)



class BeveledEdgeBlock:
    """Create PolyData beveled edge block.
    """

    def __init__(self):
        """Create all required geometry according to default size.
        Call update_geometry to update this to new specifications.
        """

        self.polydata = vtk.vtkPolyData()

        # width of the edge
        self.edge = edge = 5 
        # how much higher is inside rectangle than the outside (this
        # is what creates the beveled effect)
        self.eps = eps = 1.0/100.0

        # dummy variable for now
        width = 1
        
        # create points defining the geometry
        pts = vtk.vtkPoints()
        # InsertPoint takes care of memory allocation
        pts.InsertPoint(0, 0, 0, 0)
        pts.InsertPoint(1, width, 0, 0)
        pts.InsertPoint(2, width, 1, 0)
        pts.InsertPoint(3, 0, 1, 0)


        pts.InsertPoint(4, 0+edge, 0+edge, eps)
        pts.InsertPoint(5, width-edge, 0+edge, eps)
        pts.InsertPoint(6, width-edge, 1-edge, eps)
        pts.InsertPoint(7, 0+edge, 1-edge, eps)
        self.polydata.SetPoints(pts) # assign to the polydata
        self.pts = pts

        # create cells connecting points to each other
        cells = vtk.vtkCellArray()
        cells.InsertNextCell(4)
        cells.InsertCellPoint(0)
        cells.InsertCellPoint(1)
        cells.InsertCellPoint(2)
        cells.InsertCellPoint(3)

        cells.InsertNextCell(4)
        cells.InsertCellPoint(4)
        cells.InsertCellPoint(5)
        cells.InsertCellPoint(6)
        cells.InsertCellPoint(7)
        self.polydata.SetPolys(cells) # assign to the polydata

        # create pointdata
        arr = vtk.vtkUnsignedCharArray()
        arr.SetNumberOfComponents(4)
        arr.SetNumberOfTuples(8)
        arr.SetTuple4(0, 92,92,92,255)
        arr.SetTuple4(1, 130,130,130,255)
        arr.SetTuple4(2, 92,92,92,255)
        arr.SetTuple4(3, 0,0,0,255)
        arr.SetTuple4(4, 92,92,92,255)
        arr.SetTuple4(5, 0,0,0,255)
        arr.SetTuple4(6, 92,92,92,255)
        arr.SetTuple4(7, 192,192,192,255)
        arr.SetName('my_array')
        # and assign it as "scalars"
        self.polydata.GetPointData().SetScalars(arr)

    def update_geometry(self, width, height, z):
        """Update the geometry to the given specs.  self.polydata will
        be modified so that any downstream logic knows to update.
        """

        pts = self.pts
        edge = self.edge
        eps = self.eps

        # outer rectangle
        pts.SetPoint(0, 0,0,z)
        pts.SetPoint(1, width, 0, z)
        pts.SetPoint(2, width, height, z)
        pts.SetPoint(3, 0, height, z)

        # inner rectangle
        pts.SetPoint(4, 0+edge, 0+edge, z+eps)
        pts.SetPoint(5, width-edge, 0+edge, z+eps)
        pts.SetPoint(6, width-edge, height-edge, z+eps)
        pts.SetPoint(7, 0+edge, height-edge, z+eps)

        self.polydata.SetPoints(None)
        self.polydata.SetPoints(pts)


#############################################################################
class DeVIDECanvasObject(SubjectMixin):
    
    def __init__(self, canvas, position):
        # call parent ctor
        SubjectMixin.__init__(self)
       
        self.canvas = canvas
        self._position = position
        self._observers = {'enter' : [],
                           'exit' : [],
                           'drag' : [],
                           'buttonDown' : [],
                           'buttonUp' : [],
                           'buttonDClick' : [],
                           'motion' : []}

        # all canvas objects have a vtk prop that can be added to a
        # vtk renderer.
        self.props = []

    def close(self):
        """Take care of any cleanup here.
        """

        SubjectMixin.close(self)

    def get_bounds(self):
        raise NotImplementedError

    def get_position(self):
        return self._position

    def set_position(self, destination):
        self._position = destination

    def hit_test(self, x, y):
        return False

    def is_inside_rect(self, x, y, width, height):
        return False

class DeVIDECanvasRBBox(DeVIDECanvasObject):
    """Rubber-band box that can be used to give feedback rubber-band
    selection interaction.  Thingy.
    """


    def __init__(self, canvas, corner_bl, (width, height)):
        """ctor.  corner_bl is the bottom-left corner and corner_tr
        the top-right corner of the rbbox in world coords.
        """

        self.corner_bl = corner_bl
        self.width, self.height = width, height

        DeVIDECanvasObject.__init__(self, canvas, corner_bl)

        self._create_geometry()
        self.update_geometry()

    def _create_geometry(self):
        self._plane_source = vtk.vtkPlaneSource()
        self._plane_source.SetNormal((0.0,0.0,1.0))
        self._plane_source.SetXResolution(1)
        self._plane_source.SetYResolution(1)
        m = vtk.vtkPolyDataMapper()
        m.SetInput(self._plane_source.GetOutput())
        a = vtk.vtkActor()
        a.SetMapper(m)
        a.GetProperty().SetOpacity(0.3)
        a.GetProperty().SetColor(0.0, 0.0, 0.7)
        self.props = [a]

    def update_geometry(self):
        # bring everything up to the correct height (it should be in
        # front of all other objects)
        corner_bl = tuple(self.corner_bl[0:2]) + (RBBOX_HEIGHT,) 
        self._plane_source.SetOrigin(corner_bl)

        if self.width == 0:
            self.width = 0.1
        if self.height == 0:
            self.height = 0.1

        pos1 = [i+j for i,j in zip(corner_bl, (0.0, self.height, 0.0))]
        pos2 = [i+j for i,j in zip(corner_bl, (self.width, 0.0, 0.0))]
        self._plane_source.SetPoint1(pos1)
        self._plane_source.SetPoint2(pos2)


#############################################################################

class DeVIDECanvasSimpleLine(DeVIDECanvasObject):
    def __init__(self, canvas, src, dst):
        """src and dst are 3D world space coordinates.
        """
        self.src = src
        self.dst = dst

        # call parent CTOR
        DeVIDECanvasObject.__init__(self, canvas, src)

        self._create_geometry()
        self.update_geometry()

    def _create_geometry(self):
        self._line_source = vtk.vtkLineSource()
        m = vtk.vtkPolyDataMapper()
        m.SetInput(self._line_source.GetOutput())
        a = vtk.vtkActor()
        a.SetMapper(m)
        a.GetProperty().SetColor(0.0, 0.0, 0.0)
        self.props = [a]

    def update_geometry(self):
        self._line_source.SetPoint1(self.src)
        self._line_source.SetPoint2(self.dst)
        self._line_source.Update() 



#############################################################################
class DeVIDECanvasLine(DeVIDECanvasObject):

    # this is used by the routing algorithm to route lines around glyphs
    # with a certain border; this is also used by updateEndPoints to bring
    # the connection out of the connection port initially
    routingOvershoot = 5
    _normal_width = 2
    _highlight_width = 2 

    def __init__(self, canvas, fromGlyph, fromOutputIdx, toGlyph, toInputIdx):

        """A line object for the canvas.

        linePoints is just a list of python tuples, each representing a
        coordinate of a node in the line.  The position is assumed to be
        the first point.
        """

        self.fromGlyph = fromGlyph
        self.fromOutputIdx = fromOutputIdx
        self.toGlyph = toGlyph
        self.toInputIdx = toInputIdx


        colours = [(0, 0, 255), # blue
                   (128, 64, 0), # brown
                   (0, 128, 0), # green
                   (255, 128, 64), # orange
                   (128, 0, 255), # purple
                   (128, 128, 64)] # mustard

        col = colours[self.toInputIdx % (len(colours))]
        self.line_colour = [i / 255.0 for i in col]
 
        # any line begins with 4 (four) points
        self.updateEndPoints()
        # now we call the parent ctor
        DeVIDECanvasObject.__init__(self, canvas, self._line_points[0])        
        
        self._create_geometry()
        self.update_geometry()

    def close(self):
        # delete things that shouldn't be left hanging around
        del self.fromGlyph
        del self.toGlyph

    def _create_geometry(self):
        self._spline_source = vtk.vtkParametricFunctionSource()

        s = vtk.vtkParametricSpline()

        if False:
            # these are quite ugly...
            # later: factor this out into method, so that we can
            # experiment live with different spline params.  For now
            # the vtkCardinal spline that is used is muuuch prettier.
            ksplines = []
            for i in range(3):
                ksplines.append(vtk.vtkKochanekSpline())
                ksplines[-1].SetDefaultTension(0)
                ksplines[-1].SetDefaultContinuity(0)
                ksplines[-1].SetDefaultBias(0)
            
            s.SetXSpline(ksplines[0])
            s.SetYSpline(ksplines[1])
            s.SetZSpline(ksplines[2])

        pts = vtk.vtkPoints()
        s.SetPoints(pts)
        self._spline_source.SetParametricFunction(s)
        
        m = vtk.vtkPolyDataMapper()
        m.SetInput(self._spline_source.GetOutput())

        a = vtk.vtkActor()
        a.SetMapper(m)

        a.GetProperty().SetColor(self.line_colour)
        a.GetProperty().SetLineWidth(self._normal_width)

        self.props = [a]

    def update_geometry(self):
        pts = vtk.vtkPoints()
        for p in self._line_points:
            pts.InsertNextPoint(p + (0.0,))

        self._spline_source.GetParametricFunction().SetPoints(pts)

        self._spline_source.Update()
                          
    def get_bounds(self):
        # totally hokey: for now we just return the bounding box surrounding
        # the first two points - ideally we should iterate through the lines,
        # find extents and pick a position and bounds accordingly
        return (self._line_points[-1][0] - self._line_points[0][0],
                self._line_points[-1][1] - self._line_points[0][1])

    def getUpperLeftWidthHeight(self):
        """This returns the upperLeft coordinate and the width and height of
        the bounding box enclosing the third-last and second-last points.
        This is used for fast intersection checking with rectangles.
        """

        p3 = self._line_points[-3]
        p2 = self._line_points[-2]

        upperLeftX = [p3[0], p2[0]][bool(p2[0] < p3[0])]
        upperLeftY = [p3[1], p2[1]][bool(p2[1] < p3[1])]
        width = abs(p2[0] - p3[0])
        height = abs(p2[1] - p3[1])
                                    
        return ((upperLeftX, upperLeftY), (width,  height))

    def getThirdLastSecondLast(self):
        return (self._line_points[-3], self._line_points[-2])
            

    def hitTest(self, x, y):
        # maybe one day we will make the hitTest work, not tonight
        # I don't need it
        return False

    def insertRoutingPoint(self, x, y):
        """Insert new point x,y before second-last point, i.e. the new point
        becomes the third-last point.
        """
        if (x,y) not in self._line_points:
            self._line_points.insert(len(self._line_points) - 2, (x, y))
            return True
        else:
            return False

    def set_highlight(self):
        prop = self.props[0].GetProperty()
        # for more stipple patterns, see:
        # http://fly.cc.fer.hr/~unreal/theredbook/chapter02.html
        prop.SetLineStipplePattern(0xAAAA)
        prop.SetLineStippleRepeatFactor(2)
        prop.SetLineWidth(self._highlight_width)

    def set_normal(self):
        prop = self.props[0].GetProperty()
        prop.SetLineStipplePattern(0xFFFF)
        prop.SetLineStippleRepeatFactor(1)
        prop.SetLineWidth(self._normal_width)

    def updateEndPoints(self):
        # first get us just out of the port, then create margin between
        # us and glyph
        dcg = DeVIDECanvasGlyph
        boostFromPort = dcg._pHeight / 2 + self.routingOvershoot
        
        self._line_points = [(), (), (), ()]
        
        self._line_points[0] = self.fromGlyph.get_centre_of_port(
                1, self.fromOutputIdx)[0:2]
        self._line_points[1] = (self._line_points[0][0],
                               self._line_points[0][1] - boostFromPort)

        
        self._line_points[-1] = self.toGlyph.get_centre_of_port(
                0, self.toInputIdx)[0:2]
        self._line_points[-2] = (self._line_points[-1][0],
                                self._line_points[-1][1] + boostFromPort)

#############################################################################
class DeVIDECanvasGlyph(DeVIDECanvasObject):
    """Object representing glyph on canvas.

    @ivar inputLines: list of self._numInputs DeVIDECanvasLine
    instances that connect to this glyph's inputs.
    @ivar outputLines: list of self._numOutputs lists of
    DeVIDECanvasLine instances that originate from this glyphs
    outputs.
    @ivar position: this is the position of the bottom left corner of
    the glyph in world space.  Remember that (0,0) is also bottom left
    of the canvas.
    """

    # at start and end of glyph
    # this has to take into account the bevel edge too
    _horizBorder = 12 
    # between ports
    _horizSpacing = 10 
    # at top and bottom of glyph
    _vertBorder = 20
    _pWidth = 20
    _pHeight = 20

    _glyph_bevel_edge = 7
    _glyph_z = 0.1
    _glyph_outline_z = 0.15
    _glyph_selection_z = 0.6  
    _glyph_blocked_z = 0.7 
    _port_z = 0.2
    _text_z = 0.4

    _glyph_normal_col = (0.75, 0.75, 0.75)
    _glyph_selected_col = (0.2, 0.367, 0.656)
    _glyph_blocked_col = (0.06, 0.06, 0.06)

    _text_normal_col = (0.0, 0.0, 0.0)
    # text_selected_col used to be white, but the vtkTextActor3D()
    # has broken aliasing that is more visible on a darker
    # background.
    #text_selected_col = (1.0, 1.0, 1.0)
    _text_selected_col = (0.0, 0.0, 0.0)

    # dark green to light green
    _port_conn_col = (0.0, 218 / 255.0, 25 / 255.0)
    _port_disconn_col = (0, 93 / 255.0, 11 / 255.0)


    def __init__(self, canvas, position, numInputs, numOutputs,
                 labelList, module_instance):
        # parent constructor
        DeVIDECanvasObject.__init__(self, canvas, position)

        # we'll fill this out later
        self._size = (0,0)
        self._numInputs = numInputs
        self.inputLines = [None] * self._numInputs
        self._numOutputs = numOutputs
        # be careful with list concatenation!
        self.outputLines = [[] for i in range(self._numOutputs)]
        self._labelList = labelList
        self.module_instance = module_instance
        self.draggedPort = None
        self.enteredPort = None
        self.selected = False
        self.blocked = False

        # we'll collect the glyph and its ports in this assembly
        self.prop1 = vtk.vtkAssembly()
        # the main body glyph
        self._beb = BeveledEdgeBlock()
        self._selection_block = FilledBlock()
        self._blocked_block = FilledBlock()

        self._rbsa = vtk.vtkActor()
        # and of course the label
        self._tsa = vtk.vtkTextActor3D()

        self._iportssa = \
            [(vtk.vtkCubeSource(),vtk.vtkActor()) for _ in
                range(self._numInputs)]

        self._oportssa = \
            [(vtk.vtkCubeSource(),vtk.vtkActor()) for _ in
                range(self._numOutputs)]

        self._create_geometry()
        self.update_geometry()

    def close(self):
        del self.module_instance
        del self.inputLines
        del self.outputLines

    def _create_geometry(self):

        # TEXT LABEL ##############################################
        tprop = self._tsa.GetTextProperty()
        tprop.SetFontFamilyToArial()
        tprop.SetFontSize(24)
        tprop.SetBold(0)
        tprop.SetItalic(0)
        tprop.SetShadow(0)
        tprop.SetColor((0,0,0))

        # GLYPH BLOCK ##############################################

        # remember this depth, others things have to be 'above' this
        # to be visible (such as the text!)
        m = vtk.vtkPolyDataMapper()
        m.SetInput(self._beb.polydata)
        self._rbsa.SetMapper(m)

        # we need Phong shading for the gradients
        p = self._rbsa.GetProperty()
        p.SetInterpolationToPhong()
        
        # Ka, background lighting coefficient
        p.SetAmbient(0.1)
        # light reflectance
        p.SetDiffuse(0.6)
        # the higher Ks, the more intense the highlights
        p.SetSpecular(0.4)
        # the higher the power, the more localised the
        # highlights
        p.SetSpecularPower(100)

        self.prop1.AddPart(self._rbsa)

        # GLYPH SELECTION OVERLAY #######################################

        m = vtk.vtkPolyDataMapper()
        m.SetInput(self._selection_block.polydata)
        a = vtk.vtkActor()
        a.SetMapper(m)
        a.GetProperty().SetOpacity(0.3)
        a.GetProperty().SetColor(self._glyph_selected_col)
        self.prop1.AddPart(a)
        self._selection_actor = a

        # GLYPH BLOCKED OVERLAY #######################################
        m = vtk.vtkPolyDataMapper()
        m.SetInput(self._blocked_block.polydata)
        a = vtk.vtkActor()
        a.SetMapper(m)
        a.GetProperty().SetOpacity(0.3)
        a.GetProperty().SetColor(self._glyph_blocked_col)
        self.prop1.AddPart(a)
        self._blocked_actor = a

        
        # you should really turn this into a class

        # let's make a line from scratch
        #m = vtk.vtkPolyDataMapper()
        #m.SetInput(lp)

        #a = vtk.vtkActor()
        #a.SetMapper(m)
        #self.prop1.AddPart(a)
        #prop = a.GetProperty()
        #prop.SetColor(0.1,0.1,0.1)
        #prop.SetLineWidth(1)

        #self._glyph_outline_polydata = lp


        # INPUTS #################################################### 
        
        for i in range(self._numInputs):
            s,a = self._iportssa[i]
            s.SetYLength(self._pHeight)
            s.SetXLength(self._pWidth)
            m = vtk.vtkPolyDataMapper()
            m.SetInput(s.GetOutput())
            a.SetMapper(m)

            self.prop1.AddPart(a)

        for i in range(self._numOutputs):
            s,a = self._oportssa[i]
            s.SetYLength(self._pHeight)
            s.SetXLength(self._pWidth)
            m = vtk.vtkPolyDataMapper()
            m.SetInput(s.GetOutput())
            a.SetMapper(m)

            self.prop1.AddPart(a)

        self.prop1.SetPosition(self._position + (0.0,))

        self.props = [self.prop1, self._tsa]

    def update_geometry(self):
        
        # update text label ###################################
       
        # update the text caption
        # experiments with inserting spaces in front of text were not
        # successful (sizing still screws up)
        #nll = [' %s' % (l,) for l in self._labelList]
        nll = self._labelList
        self._tsa.SetInput('\n'.join(nll))

        # self._position is the bottom left corner of the button face
        ap = self._position[0] + self._horizBorder, \
            self._position[1] + self._vertBorder, self._text_z

        self._tsa.SetPosition(ap)

        tprop = self._tsa.GetTextProperty()
        tcol = [self._text_normal_col, self._text_selected_col]\
                [self.selected]
        tprop.SetColor(tcol)

        # also get the text dimensions
        bb = [0,0,0,0]
        self._tsa.GetBoundingBox(bb)
        text_width, text_height = bb[1] - bb[0], bb[3] - bb[2]

        # update glyph position and size ######################
        self.props[0].SetPosition(self._position + (0.0,))

        # calculate our size
        # the width is the maximum(textWidth + twice the horizontal border,
        # all ports, horizontal borders and inter-port borders added up)
        maxPorts = max(self._numInputs, self._numOutputs)
        portsWidth = 2 * self._horizBorder + \
                     maxPorts * self._pWidth + \
                     (maxPorts - 1 ) * self._horizSpacing


       
        label_and_borders = text_width + 2 * self._horizBorder
        self._size = max(portsWidth, label_and_borders), \
                      text_height + \
                      2 * self._vertBorder

        # usually the position is the CENTRE of the button, so we
        # adjust so that the bottom left corner ends up at 0,0
        # (this is all relative to the Assembly)
        self._beb.update_geometry(
                self._size[0], self._size[1], self._glyph_z)
        self._selection_block.update_geometry(
                self._size[0], self._size[1], self._glyph_selection_z)
        self._blocked_block.update_geometry(
                self._size[0], self._size[1], self._glyph_blocked_z)
        

        # calc and update glyph colour ########################
        self._selection_actor.SetVisibility(self.selected)
        self._blocked_actor.SetVisibility(self.blocked)



        # position and colour all the inputs and outputs #####
        horizOffset = self._horizBorder
        horizStep = self._pWidth + self._horizSpacing

        for i in range(self._numInputs):
            col = [self._port_disconn_col,
                    self._port_conn_col][bool(self.inputLines[i])]
            s,a = self._iportssa[i]
            a.GetProperty().SetColor(col)
            a.SetPosition(
                    (horizOffset + i * horizStep + 0.5 * self._pWidth,
                self._size[1], self._port_z))

        for i in range(self._numOutputs):
            col = [self._port_disconn_col,
                    self._port_conn_col][bool(self.outputLines[i])]
            s,a = self._oportssa[i]
            a.GetProperty().SetColor(col)
            a.SetPosition(
                    (horizOffset + i * horizStep + 0.5 * self._pWidth, 
                        0, self._port_z))

    def get_port_containing_mouse(self):
        """Given the current has_mouse and has_mouse_sub_prop
        information in canvas.event, determine the port side (input,
        output) and index of the port represented by the sub_prop.
        gah.

        @returns: tuple (inout, idx), where inout is 0 for input (top)
        and 1 for output (bottom).  Returns (-1,-1) if nothing was
        found.
        """
        if not self.canvas.event.picked_cobject is self:
            return (-1, -1)

        sp = self.canvas.event.picked_sub_prop
        if not sp:
            return (-1, -1)

        for i in  range(len(self._iportssa)):
            s, a = self._iportssa[i]
            if sp is a:
                return (0,i) 


        for i in  range(len(self._oportssa)):
            s, a = self._oportssa[i]
            if sp is a:
                return (1,i) 

        return (-1, -1)


    def get_bounds(self):
        return self._size


    def get_centre_of_port(self, inOrOut, idx):
        """Given the side of the module and the index of the port,
        return the centre of the port in 3-D world coordinates.

        @param inOrOut: 0 is input side (top), 1 is output side
        (bottom).
        @param idx: zero-based index of the port.
        """

            

        horizOffset = self._position[0] + self._horizBorder
        horizStep = self._pWidth + self._horizSpacing
        cy = self._position[1] #+ self._pHeight / 2

        # remember, in world-space, y=0 is at the bottom!
        if inOrOut == 0:
            cy += self._size[1]

        cx = horizOffset + idx * horizStep + self._pWidth / 2

        return (cx, cy, 0.0)

    def get_bottom_left_top_right(self):
         return ((self._position[0], 
                  self._position[1]),
                (self._position[0] + self._size[0] - 1,
                 self._position[1] + self._size[1] - 1))
       

    def getLabel(self):
        return ' '.join(self._labelList)

    def is_inside_rect(self, bottom_left, w, h):
        """Given world coordinates for the bottom left corner and a
        width and a height, determine if the complete glyph is inside.  

        This method will ensure that bottom-left is bottom-left by
        swapping coordinates around
        """

        bl = list(bottom_left)
        tr = list((bl[0] + w, bl[1] + h))

        if bl[0] > tr[0]:
            # swap!
            bl[0],tr[0] = tr[0],bl[0]

        if bl[1] > tr[1]:
            bl[1],tr[1] = tr[1],bl[1]

        inside = True

        if self._position[0] < bl[0] or self._position[1] < bl[1]:
            inside = False

        elif (self._position[0] + self._size[0]) > tr[0] or \
                (self._position[1] + self._size[1]) > tr[1]:
                    inside = False

        return inside

    def is_origin_inside_rect(self, bottom_left, w, h):
        """Only check origin (bottom-left) of glyph for containtment
        in specified rectangle.
        """

        bl = list(bottom_left)
        tr = list((bl[0] + w, bl[1] + h))

        if bl[0] > tr[0]:
            # swap!
            bl[0],tr[0] = tr[0],bl[0]

        if bl[1] > tr[1]:
            bl[1],tr[1] = tr[1],bl[1]

        inside = True

        if self._position[0] < bl[0] or self._position[1] < bl[1]:
            inside = False

        return inside

        
    def setLabelList(self,labelList):
        self._labelList = labelList
       
