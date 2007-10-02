# genMixins copyright 2003 by Charl P. Botha <http://cpbotha.net/>
# $Id$

class SubjectMixin(object):

    def __init__(self):
        # dictionary mapping from event name to list of observer
        # callables
        self._observers = {}

    def add_observer(self, event_name, observer):
        """Add an observer to this subject.

        observer is a function that takes the subject instance as parameter.
        """

        try:
            if not observer in self._observers[event_name]:
                self._observers[event_name].append(observer)
        except KeyError:
            self._observers[event_name] = [observer]

    def close(self):
        del self._observers

    def notify(self, event_name):
        try:
            for observer in self._observers[event_name]:
                if callable(observer):
                    # call observer with the observed subject as param
                    observer(self)
        except KeyError:
            # it could be that there are no observers for this event,
            # in which case we just shut up
            pass

    def remove_observer(self, event_name, observer):
        self._observers[event_name].remove(observer)


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



