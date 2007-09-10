# moduleManager.py copyright (c) 2007 Charl P. Botha http://cpbotha.net/
# $Id: moduleManager.py 2520 2007-08-12 20:41:25Z cpbotha $

# I could have done this with just a module variable, but I found this
# Borg thingy too nice not to use.  See:
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66531

class CounterBorg:
    """Borg-pattern (similar to a Singleton) for maintaining a
    monotonically increasing counter.

    Instantiate this anywhere, and call get() to return and increment
    the increasing counter.  DeVIDE uses this to stamp modified and
    execute times of modules.
    """

    # we start with 1, so that client code can init to 0 and guarantee
    # an initial invalid state.
    __shared_state = {'counter' : 1}

    def __init__(self):
        self.__dict__ = self.__shared_state

    def get(self):
        c = self.counter
        self.counter += 1
        return c

def counter():
    return CounterBorg().get()

