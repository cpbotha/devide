from wxPython.wx import *
import string
import traceback

def log_error(msg):
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

