# genMixins copyright 2003 by Charl P. Botha <http://cpbotha.net/>
# $Id$

class subjectMixin(object):

    def __init__(self):
        self._observers = []

    def addObserver(self, observer):
        """Add an observer to this subject.

        observer is a function that takes the subject instance as parameter.
        """
        if not observer in self._observers:
            self._observers.append(observer)
            return True

        else:
            return False

    def close(self):
        del self._observers[:]

    def notify(self):
        for observer in self._observers:
            if callable(observer):
                observer(self)

    def removeObserver(self, observer):
        if not callable(observer):
            print "WARNING: subjectMixin.removeObserver() invoked with " \
                  "non-callable."
            
        if observer in self._observers:
            self._observers.remove(observer)
            return True
        
        print "WARNING: observer %s not removed in " \
              "subjectMixin.removeObserver()." % (observer,)

        return False

class updateCallsExecuteModuleMixin(object):
    """The DeVIDE API requires that calling Update on outputData should
    ensure that that data is current.  This mixin does that by calling
    execute_module on the generating module when Update is invoked.
    """

    def __init__(self, d3Module):
        self._d3Module = d3Module

    def close(self):
        # get rid of our reference
        del self._d3Module

    def Update(self):
        """Part of our API.  If Update is called, we somehow have to make
        sure that we are current.
        """
        if self._d3Module:
            self._d3Module._moduleManager.execute_module(self._d3Module)



