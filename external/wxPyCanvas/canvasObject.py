from wxPython import wx

#############################################################################
class canvasObject(wx.wxObject):
    
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

    def addObserver(self, eventName, observer, userData=None):
        """Add an observer for a particular event.

        eventName can be one of 'enter', 'exit', 'drag', 'buttonDown'
        or 'buttonUp'.  observer is a callable object that will be
        invoked at event time with parameters canvas object,
        eventName, event and userData.
        """
        
        self._observers[eventName].append((observer, userData))

    def notifyObservers(self, eventName, event):
        for observer in self._observers[eventName]:
            observer[0](self, eventName, event, observer[1])

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

        
