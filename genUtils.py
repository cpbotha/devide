import wx
import string
import sys
import traceback

# todo: remove all VTK dependencies from this file!!

def clampVariable(v, min, max):
    """Make sure variable is on the range [min,max].  Return clamped variable.
    """
    if v < min:
        v = min
    elif v > max:
        v = max

    return v

def exceptionToMsgs():
    # create nice formatted string with tracebacks and all
    ei = sys.exc_info()
    #dmsg = \
    #     string.join(traceback.format_exception(ei[0],
    #                                            ei[1],
    #                                            ei[2]))

    dmsgs = traceback.format_exception(ei[0], ei[1], ei[2])

    return dmsgs
    

def logError(msg):
    # create nice formatted string with tracebacks and all
    ei = sys.exc_info()
    #dmsg = \
    #     string.join(traceback.format_exception(ei[0],
    #                                            ei[1],
    #                                            ei[2]))

    dmsgs = traceback.format_exception(ei[0], ei[1], ei[2])
    
    # we can't disable the timestamp yet
    # wxLog_SetTimestamp()
    # set the detail message
    for dmsg in dmsgs:
        wx.LogError(dmsg)

    # then the most recent
    wx.LogError(msg)
    print msg
    # and flush... the last message will be the actual error
    # message, what we did before will add to it to become the
    # detail message
    wx.Log_FlushActive()

def logWarning(msg):
    # create nice formatted string with tracebacks and all
    ei = sys.exc_info()
    #dmsg = \
    #     string.join(traceback.format_exception(ei[0],
    #                                            ei[1],
    #                                            ei[2]))

    dmsgs = traceback.format_exception(ei[0], ei[1], ei[2])
    
    # we can't disable the timestamp yet
    # wxLog_SetTimestamp()
    # set the detail message
    for dmsg in dmsgs:
        wx.LogWarning(dmsg)
    # then the most recent
    wx.LogWarning(msg)
    # and flush... the last message will be the actual error
    # message, what we did before will add to it to become the
    # detail message
    wx.Log_FlushActive()
    


def setGridCellYesNo(grid, row, col, yes=True):
    if yes:
        colour = wx.Colour(0,255,0)
        text = '1'
    else:
        colour = wx.Colour(255,0,0)
        text = '0'
        
    grid.SetCellValue(row, col, text)
    grid.SetCellBackgroundColour(row, col, colour)

def textToFloat(text, defaultFloat):
    """Converts text to a float by using an eval and returns the float.
    If something goes wrong, returns defaultFloat.
    """

    try:
        returnFloat = float(text)
    except Exception:
        returnFloat = defaultFloat

    return returnFloat

def textToInt(text, defaultInt):
    """Converts text to an integer by using an eval and returns the integer.
    If something goes wrong, returns default Int.
    """

    try:
        returnInt = int(text)
    except Exception:
        returnInt = defaultInt

    return returnInt

def textToTuple(text, defaultTuple):
    """This will convert the text representation of a tuple into a real
    tuple.  No checking for type or number of elements is done.  See
    textToTypeTuple for that.
    """

    # first make sure that the text starts and ends with brackets
    text = text.strip()
    
    if text[0] != '(':
        text = '(%s' % (text,)

    if text[-1] != ')':
        text = '%s)' % (text,)

    try:
        returnTuple = eval('tuple(%s)' % (text,))
    except Exception:
        returnTuple = defaultTuple

    return returnTuple

def textToTypeTuple(text, defaultTuple, numberOfElements, aType):
    """This will convert the text representation of a tuple into a real
    tuple with numberOfElements elements, all of type aType.  If the required
    number of elements isn't available, or they can't all be casted to the
    correct type, the defaultTuple will be returned.
    """
    
    aTuple = textToTuple(text, defaultTuple)

    if len(aTuple) != numberOfElements:
        returnTuple = defaultTuple

    else:
        try:
            returnTuple = tuple([aType(e) for e in aTuple])
        except ValueError:
            returnTuple = defaultTuple

    return returnTuple

