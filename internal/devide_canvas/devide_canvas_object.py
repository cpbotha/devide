from gen_mixins import SubjectMixin
import vtk


#############################################################################
class DeVIDECanvasObject(SubjectMixin):
    
    def __init__(self, position):
        # call parent ctor
        SubjectMixin.__init__(self)
        
        self._position = position
        self.canvas = None
        self._observers = {'enter' : [],
                           'exit' : [],
                           'drag' : [],
                           'buttonDown' : [],
                           'buttonUp' : [],
                           'buttonDClick' : [],
                           'motion' : []}

        # all canvas objects have a vtk prop that can be added to a
        # vtk renderer.
        self.prop = None

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

    def isInsideRect(self, x, y, width, height):
        return False

#############################################################################

class DeVIDECanvasSimpleLine(DeVIDECanvasObject):
    def __init__(self, src, dst):
        """src and dst are 3D world space coordinates.
        """
        self.src = src
        self.dst = dst

        # call parent CTOR
        DeVIDECanvasObject.__init__(self, src)

        self._create_geometry()
        self.update_geometry()

    def _create_geometry(self):
        self._line_source = vtk.vtkLineSource()
        m = vtk.vtkPolyDataMapper()
        m.SetInput(self._line_source.GetOutput())
        a = vtk.vtkActor()
        a.SetMapper(m)
        a.GetProperty().SetColor(0.0, 0.0, 0.0)
        self.prop = a

    def update_geometry(self):
        self._line_source.SetPoint1(self.src)
        self._line_source.SetPoint2(self.dst)
        self._line_source.Update() 



class DeVIDECanvasLine(DeVIDECanvasObject):

    # this is used by the routing algorithm to route lines around glyphs
    # with a certain border; this is also used by updateEndPoints to bring
    # the connection out of the connection port initially
    routingOvershoot = 10

    def __init__(self, fromGlyph, fromOutputIdx, toGlyph, toInputIdx):

        """A line object for the canvas.

        linePoints is just a list of python tuples, each representing a
        coordinate of a node in the line.  The position is assumed to be
        the first point.
        """

        self.fromGlyph = fromGlyph
        self.fromOutputIdx = fromOutputIdx
        self.toGlyph = toGlyph
        self.toInputIdx = toInputIdx

        # 'BLACK' removed
        colourNames = ['BLUE', 'BROWN', 'MEDIUM FOREST GREEN',
                       'DARKORANGE1']
        self.lineColourName = colourNames[self.toInputIdx % (len(colourNames))]
 
        # any line begins with 4 (four) points
        self.updateEndPoints()
        # now we call the parent ctor
        DeVIDECanvasObject.__init__(self, self._line_points[0])        
        
        self._create_geometry()
        self.update_geometry()

    def close(self):
        # delete things that shouldn't be left hanging around
        del self.fromGlyph
        del self.toGlyph

    def _create_geometry(self):
        self._spline_source = vtk.vtkParametricFunctionSource()
        s = vtk.vtkParametricSpline()
        pts = vtk.vtkPoints()
        s.SetPoints(pts)
        self._spline_source.SetParametricFunction(s)
        
        m = vtk.vtkPolyDataMapper()
        m.SetInput(self._spline_source.GetOutput())

        a = vtk.vtkActor()
        a.SetMapper(m)

        a.GetProperty().SetColor(0.0,0.0,0.45)
        a.GetProperty().SetLineWidth(2.5)

        self.prop = a

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

    @ivar position: this is the position of the bottom left corner of
    the glyph in world space.  Remember that (0,0) is also bottom left
    of the canvas.
    """

    # at start and end of glyph
    _horizBorder = 5
    # between ports
    _horizSpacing = 5
    # at top and bottom of glyph
    _vertBorder = 15
    _pWidth = 10
    _pHeight = 10

    _label_height = 10


    t = vtk.vtkVectorText()
    t.SetText('M')
    t.Update()
    b = t.GetOutput().GetBounds()
    _label_scale = _label_height / (b[3] - b[2])

    def __init__(self, position, numInputs, numOutputs,
                 labelList, moduleInstance):
        # parent constructor
        #coRectangle.__init__(self, position, (0,0))
        DeVIDECanvasObject.__init__(self, position)

        # we'll fill this out later
        self._size = (0,0)
        self._numInputs = numInputs
        self.inputLines = [None] * self._numInputs
        self._numOutputs = numOutputs
        # be careful with list concatenation!
        self.outputLines = [[] for i in range(self._numOutputs)]
        self._labelList = labelList
        self.moduleInstance = moduleInstance
        self.draggedPort = None
        self.enteredPort = None
        self.selected = False
        self.blocked = False

        self.prop = vtk.vtkAssembly()
        self._rbs = vtk.vtkRectangularButtonSource()
        self._rbsa = vtk.vtkActor()
        self._ts = vtk.vtkVectorText()
        self._tsa = vtk.vtkActor()

        self._iportssa = \
            [(vtk.vtkRectangularButtonSource(),vtk.vtkActor()) for _ in
                range(self._numInputs)]

        self._oportssa = \
            [(vtk.vtkRectangularButtonSource(),vtk.vtkActor()) for _ in
                range(self._numOutputs)]

        self._create_geometry()
        self.update_geometry()

    def close(self):
        del self.moduleInstance
        del self.inputLines
        del self.outputLines

    def _create_geometry(self):
        normal_colour = (192, 192, 192)
        selected_colour = (255, 0, 246)
        blocked_colour = (16, 16, 16)

        colour = normal_colour

        if self.selected:
            colour = [selected_colour[i] * 0.5 + colour[i] * 0.5
                      for i in range(3)]

        if self.blocked:
            colour = [blocked_colour[i] * 0.5 + colour[i] * 0.5
                      for i in range(3)]

        colour = tuple([int(i) for i in colour])

        # TEXT LABEL ##############################################
        self._ts.SetText('\n'.join(self._labelList))
        self._ts.Update()
        m= vtk.vtkPolyDataMapper()
        m.SetInput(self._ts.GetOutput())
        self._tsa.SetMapper(m)

        self._tsa.SetScale(self._label_scale)
        inity = self._vertBorder + \
                self._label_height * (len(self._labelList) - 1)
        # still have to tune inity with the space between lines...
        initx = self._horizSpacing
        # y is the bottom left of the first character
        # 0.2 is 0.1 above the button (the button's depth is 0.1)
        self._tsa.SetPosition(initx, inity, 0.2)

        # we also need the text width for later
        b = self._ts.GetOutput().GetBounds()
        text_width = self._label_scale * (b[1] - b[2]) + \
            2 * self._horizBorder

        # text colour
        self._tsa.GetProperty().SetColor(0.0, 0.0, 0.0)

        self.prop.AddPart(self._tsa)
        
        # RECT BUTTON ##############################################
        # calculate our size
        # the width is the maximum(textWidth + twice the horizontal border,
        # all ports, horizontal borders and inter-port borders added up)
        maxPorts = max(self._numInputs, self._numOutputs)
        portsWidth = 2 * self._horizBorder + \
                     maxPorts * self._pWidth + \
                     (maxPorts - 1 ) * self._horizSpacing


        
        self._size = (max(text_width, portsWidth),
                      self._label_height * len(self._labelList) + \
                      2 * self._vertBorder)

        self._rbs.SetBoxRatio(1.0)
        self._rbs.SetTwoSided(1)
        self._rbs.SetHeight(self._size[1])
        self._rbs.SetWidth(self._size[0])
        # so bottom is wider than shoulder (beveled)
        self._rbs.SetBoxRatio(1.1)
        # remember this depth, others things have to be 'above' this
        # to be visible (such as the text!)
        self._rbs.SetDepth(0.1)

        m = vtk.vtkPolyDataMapper()
        m.SetInput(self._rbs.GetOutput())
        self._rbsa.SetMapper(m)
        # usually the position is the CENTRE of the button, so we
        # adjust so that the bottom left corner ends up at 0,0
        self._rbsa.SetPosition((self._size[0] / 2.0, 
            self._size[1] / 2.0, 0.0))

        p = self._rbsa.GetProperty()
        p.SetColor((0.0, 1.0, 0.0))

        # i prefer flat shading, okay?
        p.SetInterpolationToFlat()
        
        # Ka, background lighting coefficient
        p.SetAmbient(0.1)
        # light reflectance
        p.SetDiffuse(0.6)
        # the higher Ks, the more intense the highlights
        p.SetSpecular(0.4)
        # the higher the power, the more localised the
        # highlights
        p.SetSpecularPower(100)


        self.prop.AddPart(self._rbsa)

        # INPUTS #################################################### 
        horizOffset = self._horizBorder
        horizStep = self._pWidth + self._horizSpacing
        #connBrush = wx.wxBrush("GREEN")
        #disconnBrush = wx.wxBrush("RED")
        
        for i in range(self._numInputs):
            s,a = self._iportssa[i]
            s.SetHeight(self._pHeight)
            s.SetWidth(self._pWidth)
            m = vtk.vtkPolyDataMapper()
            m.SetInput(s.GetOutput())
            a.SetMapper(m)
            a.SetPosition((horizOffset + i * horizStep,
                self._size[1], 0.1))

            self.prop.AddPart(a)

        for i in range(self._numOutputs):
            s,a = self._oportssa[i]
            s.SetHeight(self._pHeight)
            s.SetWidth(self._pWidth)
            m = vtk.vtkPolyDataMapper()
            m.SetInput(s.GetOutput())
            a.SetMapper(m)
            a.SetPosition((horizOffset + i * horizStep, 0, 0.1))

            self.prop.AddPart(a)

        self.prop.SetPosition(self._position + (0.0,))

    def update_geometry(self):
        glyph_normal_col = (0.75, 0.75, 0.75)
        glyph_selected_col = (1.0, 0.0, 0.96)
        glyph_blocked_col = (0.06, 0.06, 0.06)
        port_conn_col = (0.0, 1.0, 0.0)
        port_disconn_col = (1.0, 0.0, 0.0)

        self.prop.SetPosition(self._position + (0.0,))

        if self.selected:
            gcol = glyph_selected_col
        elif self.blocked:
            gcol = glyph_blocked_col
        else:
            gcol = glyph_normal_col

        self._rbsa.GetProperty().SetColor(gcol)

        for i in range(self._numInputs):
            col = [port_conn_col,
                    port_disconn_col][bool(self.inputLines[i])]
            s,a = self._iportssa[i]
            a.GetProperty().SetColor(col)


        for i in range(self._numOutputs):
            col = [port_conn_col,
                    port_disconn_col][bool(self.outputLines[i])]
            s,a = self._oportssa[i]
            a.GetProperty().SetColor(col)

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
            cy += self._size[1] - self._pHeight 

        cx = horizOffset + idx * horizStep #+ self._pWidth / 2

        return (cx, cy, 0.0)

    def get_bottom_left_top_right(self):
         return ((self._position[0], 
                  self._position[1]),
                (self._position[0] + self._size[0] - 1,
                 self._position[1] + self._size[1] - 1))
       

    def getLabel(self):
        return ' '.join(self._labelList)
        
    def setLabelList(self,labelList):
        self._labelList = labelList
       
