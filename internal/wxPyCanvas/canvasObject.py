from wxPython import wx
from canvasSubject import canvasSubject

#############################################################################
class canvasObject(canvasSubject):
    
    def __init__(self, position):
        # call parent ctor
        canvasSubject.__init__(self)
        
        self._position = position
        self._canvas = None
        self._observers = {'enter' : [],
                           'exit' : [],
                           'drag' : [],
                           'buttonDown' : [],
                           'buttonUp' : [],
                           'buttonDClick' : [],
                           'motion' : []}
    def close(self):
        """Take care of any cleanup here.
        """
        pass

    def draw(self, dc):
        pass

    def getBounds(self):
        raise NotImplementedError

    def getPosition(self):
        return self._position

    def setPosition(self, destination):
        self._position = destination

    def getCanvas(self):
        return self._canvas

    def hitTest(self, x, y):
        return False
    def isInsideRect(self, x, y, width, height):
        return False

    def setCanvas(self, canvas):
        self._canvas = canvas


#############################################################################
class coRectangle(canvasObject):

    def __init__(self, position, size):
        canvasObject.__init__(self, position)
        self._size = size

    def draw(self, dc):
        # drawing rectangle!
        dc.SetBrush(wx.wxBrush(wx.wxColour(192,192,192), wx.wxSOLID))
        dc.DrawRectangle(self._position[0], self._position[1],
                         self._size[0], self._size[1])

    def getBounds(self):
        return (self._size)

    def getTopLeftBottomRight(self):
        return ((self._position[0], self._position[1]),
                (self._position[0] + self._size[0] - 1,
                 self._position[1] + self._size[1] - 1))

    def hitTest(self, x, y):
        # think carefully about the size of the rectangle...
        # e.g. from 0 to 2 is size 2 (spaces between vertices)
        return x >= self._position[0] and \
               x <= self._position[0] + self._size[0] and \
               y >= self._position[1] and \
               y <= self._position[1] + self._size[1]

    def isInsideRect(self, x, y, width, height):
        x0 = (self._position[0] - x)
        y0 = (self._position[1] - y)
        return x0 >= 0 and x0 <= width and \
               y0 >= 0 and y0 <= height and \
               x0 + self._size[0] <= width and \
               y0 + self._size[1] <= height
               

#############################################################################

class coLine(canvasObject):

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

        canvasObject.__init__(self, self._linePoints[0])        


    def close(self):
        # delete things that shouldn't be left hanging around
        del self.fromGlyph
        del self.toGlyph

    def draw(self, dc):
        # lines are 2 pixels thick
        dc.SetPen(wx.wxPen(self.lineColourName, 2, wx.wxSOLID))

        # simple mode: just the lines thanks.
        #dc.DrawLines(self._linePoints)

        # spline mode for N points:
        # 1. Only 4 points: drawlines.  DONE
        # 2. Draw line from 0 to 1
        # 3. Draw line from N-2 to N-1 (second last to last)
        # 4. Draw spline from 1 to N-2 (second to second last)
#         if len(self._linePoints) > 4:
#             dc.DrawLines(self._linePoints[0:2]) # 0 - 1
#             dc.DrawLines(self._linePoints[-2:]) # second last to last
#             dc.DrawSpline(self._linePoints[1:-1])
#         else:
#             dc.DrawLines(self._linePoints)

        dc.SetPen(wx.wxPen('BLACK', 4, wx.wxSOLID))
        dc.DrawSpline(self._linePoints)
        dc.SetPen(wx.wxPen(self.lineColourName, 2, wx.wxSOLID))
        dc.DrawSpline(self._linePoints)
                          
    def getBounds(self):
        # totally hokey: for now we just return the bounding box surrounding
        # the first two points - ideally we should iterate through the lines,
        # find extents and pick a position and bounds accordingly
        return (self._linePoints[-1][0] - self._linePoints[0][0],
                self._linePoints[-1][1] - self._linePoints[0][1])

    def getUpperLeftWidthHeight(self):
        """This returns the upperLeft coordinate and the width and height of
        the bounding box enclosing the third-last and second-last points.
        This is used for fast intersection checking with rectangles.
        """

        p3 = self._linePoints[-3]
        p2 = self._linePoints[-2]

        upperLeftX = [p3[0], p2[0]][bool(p2[0] < p3[0])]
        upperLeftY = [p3[1], p2[1]][bool(p2[1] < p3[1])]
        width = abs(p2[0] - p3[0])
        height = abs(p2[1] - p3[1])
                                    
        return ((upperLeftX, upperLeftY), (width,  height))

    def getThirdLastSecondLast(self):
        return (self._linePoints[-3], self._linePoints[-2])
            

    def hitTest(self, x, y):
        # maybe one day we will make the hitTest work, not tonight
        # I don't need it
        return False

    def insertRoutingPoint(self, x, y):
        """Insert new point x,y before second-last point, i.e. the new point
        becomes the third-last point.
        """
        if (x,y) not in self._linePoints:
            self._linePoints.insert(len(self._linePoints) - 2, (x, y))
            return True
        else:
            return False

    def updateEndPoints(self):
        # first get us just out of the port, then create margin between
        # us and glyph
        boostFromPort = coGlyph._pHeight / 2 + coLine.routingOvershoot
        
        self._linePoints = [(), (), (), ()]
        
        self._linePoints[0] = self.fromGlyph.getCenterOfPort(
            1, self.fromOutputIdx)
        self._linePoints[1] = (self._linePoints[0][0],
                               self._linePoints[0][1] + boostFromPort)

        
        self._linePoints[-1] = self.toGlyph.getCenterOfPort(
            0, self.toInputIdx)
        self._linePoints[-2] = (self._linePoints[-1][0],
                                self._linePoints[-1][1] - boostFromPort)

#############################################################################
class coGlyph(coRectangle):

    # at start and end of glyph
    _horizBorder = 5
    # between ports
    _horizSpacing = 5
    # at top and bottom of glyph
    _vertBorder = 15
    _pWidth = 10
    _pHeight = 10
    

    def __init__(self, position, numInputs, numOutputs, label, moduleInstance):
        # parent constructor
        coRectangle.__init__(self, position, (0,0))
        # we'll fill this out later
        self._size = (0,0)
        self._numInputs = numInputs
        self.inputLines = [None] * self._numInputs
        self._numOutputs = numOutputs
        # be careful with list concatenation!
        self.outputLines = [[] for i in range(self._numOutputs)]
        self._label = label
        self.moduleInstance = moduleInstance
        self.draggedPort = None
        self.enteredPort = None
        self.selected = False

    def close(self):
        del self.moduleInstance
        del self.inputLines
        del self.outputLines

    def draw(self, dc):
        # we're going to alpha blend a purplish sheen if this glyph is active
        if self.selected:
            # sheen: 255, 0, 246
            # alpha-blend with 192, 192, 192 with alpha 0.5 yields
            #  224, 96, 219
            blockFillColour = wx.wxColour(224, 96, 219)
        else:
            blockFillColour = wx.wxColour(192, 192, 192)
        
        # default pen and font
        dc.SetBrush(wx.wxBrush(blockFillColour, wx.wxSOLID))
        dc.SetPen(wx.wxPen('BLACK', 1, wx.wxSOLID))
        dc.SetFont(wx.wxNORMAL_FONT)
        
        # calculate our size
        # the width is the maximum(textWidth + twice the horizontal border,
        # all ports, horizontal borders and inter-port borders added up)
        maxPorts = max(self._numInputs, self._numOutputs)
        portsWidth = 2 * coGlyph._horizBorder + \
                     maxPorts * coGlyph._pWidth + \
                     (maxPorts - 1 ) * coGlyph._horizSpacing
        
        tex, tey = dc.GetTextExtent(self._label)
        textWidth = tex + 2 * coGlyph._horizBorder
        
        self._size = (max(textWidth, portsWidth),
                      tey + 2 * coGlyph._vertBorder)

        # draw the main rectangle
        dc.DrawRectangle(self._position[0], self._position[1],
                         self._size[0], self._size[1])

        #dc.DrawRoundedRectangle(self._position[0], self._position[1],
        #                        self._size[0], self._size[1], radius=5)
        
        
        dc.DrawText(self._label,
                    self._position[0] + coGlyph._horizSpacing,
                    self._position[1] + coGlyph._vertBorder)

        # then the inputs
        horizOffset = self._position[0] + coGlyph._horizBorder
        horizStep = coGlyph._pWidth + coGlyph._horizSpacing
        connBrush = wx.wxBrush("GREEN")
        disconnBrush = wx.wxBrush("RED")
        
        for i in range(self._numInputs):
            brush = [disconnBrush, connBrush][bool(self.inputLines[i])]
            self.drawPort(dc, brush,
                          (horizOffset + i * horizStep,
                           self._position[1]))

        lx = self._position[1] + self._size[1] - coGlyph._pHeight
        for i in range(self._numOutputs):
            brush = [disconnBrush, connBrush][bool(self.outputLines[i])]
            self.drawPort(dc, brush,
                          (horizOffset + i * horizStep,
                           lx))

    def drawPort(self, dc, brush, pos):
        dc.SetBrush(brush)
        dc.DrawRectangle(pos[0], pos[1], coGlyph._pWidth, coGlyph._pHeight)
        #dc.DrawEllipse(pos[0], pos[1], coGlyph._pWidth, coGlyph._pHeight)

    def findPortContainingMouse(self, x, y):
        """Find port that contains the mouse pointer.  Returns tuple
        containing inOut and port index.
        """

        horizOffset = self._position[0] + coGlyph._horizBorder
        horizStep = coGlyph._pWidth + coGlyph._horizSpacing
        
        bx = horizOffset
        by = self._position[1]
        
        for i in range(self._numInputs):
            if x >= bx and x <= bx + self._pWidth and \
               y >= by and y < by + self._pHeight:

                return (0, i)
            
            bx += horizStep

        bx = horizOffset
        by = self._position[1] + self._size[1] - coGlyph._pHeight
        
        for i in range(self._numOutputs):
            if x >= bx and x <= bx + self._pWidth and \
               y >= by and y < by + self._pHeight:

                return (1, i)
            
            bx += horizStep
            
        return None

    def getCenterOfPort(self, inOrOut, idx):

        horizOffset = self._position[0] + coGlyph._horizBorder
        horizStep = coGlyph._pWidth + coGlyph._horizSpacing
        cy = self._position[1] + coGlyph._pHeight / 2

        if inOrOut:
            cy += self._size[1] - coGlyph._pHeight 

        cx = horizOffset + idx * horizStep + coGlyph._pWidth / 2

        return (cx, cy)

    def getLabel(self):
        return self._label
        


        

        
    
