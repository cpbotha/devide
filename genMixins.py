# genMixins copyright 2003 by Charl P. Botha <http://cpbotha.net/>
# $Id: genMixins.py,v 1.1 2003/02/25 10:36:03 cpbotha Exp $

class subjectMixin:

    def __init__(self):
        self._observers = []

    def addObserver(self, observer):
        """Add an observer to this subject.

        observer is a function that takes the subject instance as parameter.
        """
        if not observer in self._observers:
            self._observers.append(observer)
            return self._observers.index(observer)

        else:
            return -1

    def close(self):
        del self._observers[:]

    def notify(self):
        for observer in self._observers:
            if callable(observer):
                observer(self)

    def removeObserver(self, observer):
        if observer in self._observers:
            self._observers.remove(observer)


