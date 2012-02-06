class canvasSubject:
    def __init__(self):
        self._observers = {}
        
    def addObserver(self, eventName, observer):
        """Add an observer for a particular event.

        eventName can be one of 'enter', 'exit', 'drag', 'buttonDown'
        or 'buttonUp'.  observer is a callable object that will be
        invoked at event time with parameters canvas object,
        eventName, and event.
        """
        
        self._observers[eventName].append(observer)

    def notifyObservers(self, eventName, event):
        for observer in self._observers[eventName]:
            observer(self, eventName, event)
    
