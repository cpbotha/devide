class canvasSubject:
    def __init__(self):
        self._observers = {}
        
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
    
