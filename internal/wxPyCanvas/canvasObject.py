from wxPython import wx
from canvasSubject import canvasSubject

#############################################################################
class canvasObject(wx.wxObject, canvasSubject):
    
    def __init__(self, position):
        # call parent ctor
        wx.wxObject(self)

        self._position = position
        self._canvas = None
        self._observers = {'enter' : [],
                           'exit' : [],
                           'drag' : [],
                           'buttonDown' : [],
                           'buttonUp' : [],
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
        return x >= self._position[0] and \
               x <= self._position[0] + self._size[0] and \
               y >= self._position[1] and \
               y <= self._position[1] + self._size[1]

#############################################################################

class coLine(canvasObject):

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

        # any line begins with 4 (four) points

        self.updateEndPoints()

        canvasObject.__init__(self, self._linePoints[0])        


    def close(self):
        # delete things that shouldn't be left hanging around
        del self.fromGlyph
        del self.toGlyph

    def draw(self, dc):
        # lines are 2 pixels thick
        dc.SetPen(wx.wxPen('BLACK', 2, wx.wxSOLID))
        dc.DrawLines(self._linePoints)

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
        self._linePoints = [() for i in range(4)]
        
        self._linePoints[0] = self.fromGlyph.getCenterOfPort(
            1, self.fromOutputIdx)
        self._linePoints[1] = (self._linePoints[0][0],
                               self._linePoints[0][1] + coGlyph._pHeight)
        
        self._linePoints[-1] = self.toGlyph.getCenterOfPort(
            0, self.toInputIdx)
        self._linePoints[-2] = (self._linePoints[-1][0],
                                self._linePoints[-1][1] - coGlyph._pHeight)
        

#############################################################################
class coGlyph(coRectangle):

    _horizBorder = 5
    _vertBorder = 15
    _pWidth = 10
    _pHeight = 10
    

    def __init__(self, position, numInputs, numOutputs, label, moduleInstance):
        # parent constructor
        canvasObject.__init__(self, position)
        # we'll fill this out later
        self._size = (0,0)
        self._numInputs = numInputs
        self.inputLines = [None for i in range(self._numInputs)]
        self._numOutputs = numOutputs
        self.outputLines = [[] for i in range(self._numOutputs)]
        self._label = label
        self.moduleInstance = moduleInstance
        self.draggedPort = None
        self.enteredPort = None

    def close(self):
        del self.moduleInstance
        del self.inputLines
        del self.outputLines

    def draw(self, dc):
        # default pen and font
        dc.SetBrush(wx.wxBrush(wx.wxColour(192, 192, 192), wx.wxSOLID))
        dc.SetPen(wx.wxPen('BLACK', 1, wx.wxSOLID))
        dc.SetFont(wx.wxNORMAL_FONT)
        
        # calculate our size
        tex, tey = dc.GetTextExtent(self._label)
        self._size = (tex + 2 * coGlyph._horizBorder,
                      tey + 2 * coGlyph._vertBorder)

        # draw the main rectangle
        dc.DrawRectangle(self._position[0], self._position[1],
                         self._size[0], self._size[1])
        
        dc.DrawText(self._label,
                    self._position[0] + coGlyph._horizBorder,
                    self._position[1] + coGlyph._vertBorder)

        # then the inputs
        horizOffset = self._position[0] + coGlyph._horizBorder
        horizStep = coGlyph._pWidth + coGlyph._horizBorder
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

    def drawSinglePort(self, dc, port):
        """Use to redraw a SINGLE port.

        Do NOT use as part of a full redraw, as it can be done faster.  This
        is for use during a mouseOver and whatnot.
        """

        if port[0] == 0:
            connected = bool(self.inputLines[idx])
        else:
            connected = bool(self.outputLines[idx])
        
        if connected:
            brush = wx.wxBrush("GREEN")
        else:
            brush = wx.wxBrush("RED")

        px = self._position[0] + coGlyph._horizBorder + \
             idx * (coGlyph._pWidth + coGlyph._horizBorder)
        py = self._position[1]

        if not inputPort:
            py += self._size[1] - coGlyph._pHeight

        self.drawPort(dc, brush, (px, py))

    def findPortContainingMouse(self, x, y):
        """Find port that contains the mouse pointer.  Returns tuple
        containing inOut and port index.
        """

        horizOffset = self._position[0] + coGlyph._horizBorder
        horizStep = coGlyph._pWidth + coGlyph._horizBorder
        
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
        horizStep = coGlyph._pWidth + coGlyph._horizBorder
        cy = self._position[1] + coGlyph._pHeight / 2

        if inOrOut:
            cy += self._size[1] - coGlyph._pHeight 

        cx = horizOffset + idx * horizStep + coGlyph._pWidth / 2

        return (cx, cy)

    def getLabel(self):
        return self._label
        


        

        
    
