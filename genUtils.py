from wxPython.wx import *
import string
import traceback

def logError(msg):
    # create nice formatted string with tracebacks and all
    dmsg = \
         string.join(traceback.format_exception(sys.exc_type,
                                                sys.exc_value,
                                                sys.exc_traceback))
    # we can't disable the timestamp yet
    # wxLog_SetTimestamp()
    # set the detail message
    wxLogError(dmsg)
    # then the most recent
    wxLogError(msg)
    # and flush... the last message will be the actual error
    # message, what we did before will add to it to become the
    # detail message
    wxLog_FlushActive()

def textToFloat(text, defaultFloat):
    """Converts text to a float by using an eval and returns the float.
    If something goes wrong, returns defaultFloat.
    """

    try:
        returnFloat = float(eval(text))
    except Exception:
        returnFloat = defaultFloat

    return returnFloat

def textToInt(text, defaultInt):
    """Converts text to an integer by using an eval and returns the integer.
    If something goes wrong, returns default Int.
    """

    try:
        returnInt = int(eval(text))
    except Exception:
        returnInt = defaultInt

    return returnInt

