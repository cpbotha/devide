# assistants.py copyright 2002 by Charl P. Botha http://cpbotha.net/
# $Id: assistants.py,v 1.3 2004/01/15 10:46:21 cpbotha Exp $
# code for keeping track of the big buttoned simple interface

import os
import sys
from wxPython.wx import *
from wxPython.xrc import *

class load_data_assistant:
    def __init__(self, assistants):
        self._assistants = assistants
        self._dlg1 = None

    def close(self):
        if self._dlg1 != None:
            self._dlg1.Destroy()
        del self._dlg1

    def assist(self):
        if self._dlg1 == None:
            res = self._assistants.get_res()
            main_window = self._assistants.get_app().get_main_window()
            self._dlg1 = res.LoadDialog(main_window,
                                        'DLG_LOAD_DATA_A1')
            # the event is triggered by dlg, not by us!
            EVT_BUTTON(self._dlg1, XMLID('LDA_ID_FN_BROWSE'), self.browse_cb)

        self._dlg1.ShowModal()

    def browse_cb(self, event):
        dlg = wxFileDialog(self._dlg1, "Choose a file", ".", "", "*.*",
                           wxOPEN|wxMULTIPLE)
        if dlg.ShowModal() == wxID_OK:
            print dlg.GetPaths()
        dlg.Destroy()
    
class assistants:
    """Class for keeping track of all data pertinent to the assistants.

    When devide is started, the user is faced with the super-easy assistants
    interface.  These are big friendly buttons with which the user can do her
    thing.
    """
    
    def __init__(self, app):
        """Opens resource file and intialises instance variables.

        This creates variables for all the available assistants but initialises
        them to None.  As soon as an assistant is called, it's created but
        from then on the same instance will be re-used.
        """
        self._app = app
        res_path = os.path.join(sys.path[0], 'resources/xml/assistants.xrc')
        self._res = wxXmlResource(res_path)
        self._load_data_assistant = None

    def close(self):
        """We use explicit calls to close().

        As Guido says, try to avoid using finalizers, i.e. *_del__.  This makes
        it difficult for the garbage collector.
        """
        self._load_data_assistant.close()

    def load_data(self):
        """Activates the load data assistant.
        """
        if self._load_data_assistant == None:
            self._load_data_assistant = load_data_assistant(self)
        self._load_data_assistant.assist()

    def get_app(self):
        return self._app

    def get_res(self):
        return self._res

