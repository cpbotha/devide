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
                           'buttonUp' : []}

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

    def hitTest(self, x, y):
        return x >= self._position[0] and \
               x <= self._position[0] + self._size[0] and \
               y >= self._position[1] and \
               y <= self._position[1] + self._size[1]

#############################################################################

class coLine(canvasObject):

    def __init__(self, linePoints):
        """A line object for the canvas.

        linePoints is just a list of python tuples, each representing a
        coordinate of a node in the line.  The position is assumed to be
        the first point.
        """
        
        canvasObject.__init__(self, linePoints[0])
        self._linePoints = linePoints

    def draw(self, dc):
        dc.DrawLines(self._linePoints)

    def getBounds(self):
        # totally hokey: for now we just return the bounding box surrounding
        # the first two points - ideally we should iterate through the lines,
        # find extents and pick a position and bounds accordingly
        return (self._linePoints[-1][0] - self._linePoints[0][0],
                self._linePoints[-1][1] - self._linePoints[0][1])

    def hitTest(self, x, y):
        # maybe one day we will make the hitTest work, not tonight
        # I don't need it
        return False

#############################################################################
class coGlyph(coRectangle):

    _horizBorder = 5
    _vertBorder = 15
    _pWidth = 10
    _pHeight = 10
    

    def __init__(self, position, numInputs, numOutputs, label):
        # parent constructor
        canvasObject.__init__(self, position)
        # we'll fill this out later
        self._size = (0,0)
        self._numInputs = numInputs
        self._inputConnected = [False for i in range(self._numInputs)]
        self._numOutputs = numOutputs
        self._outputConnected = [False for i in range(self._numOutputs)]
        self._label = label

    def draw(self, dc):
        # default pen and font
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
            brush = [disconnBrush, connBrush][self._inputConnected[i]]
            self.drawPort(dc, brush,
                          (horizOffset + i * horizStep,
                           self._position[1]))

        lx = self._position[1] + self._size[1] - coGlyph._pHeight
        for i in range(self._numOutputs):
            brush = [disconnBrush, connBrush][self._outputConnected[i]]
            self.drawPort(dc, brush,
                          (horizOffset + i * horizStep,
                           lx))

    def drawPort(self, dc, brush, pos):
        dc.SetBrush(brush)
        dc.DrawRectangle(pos[0], pos[1], coGlyph._pWidth, coGlyph._pHeight)

    def drawSinglePort(self, dc, idx, inputPort=True):
        """Use to redraw a SINGLE port.

        Do NOT use as part of a full redraw, as it can be done faster.  This
        is for use during a mouseOver and whatnot.
        """

        if inputPort:
            connected = self._inputConnected[idx]
        else:
            connected = self._outputConnected[idx]
        
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
        
    def setPortConnected(self, idx, inputPort=True, connected=True):
        if inputPort:
            self._inputConnected[idx] = connected
        else:
            self._outputConnected[idx] = connected

        

        
    
