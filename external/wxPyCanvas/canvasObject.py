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
        dc.SetBrush(wx.wxBrush('BLUE', wx.wxSOLID))
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
