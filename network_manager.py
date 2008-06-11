# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

import cPickle
import time

class NetworkManager:
    """Contains all logic to do with network handling.

    This is still work in progress: code has to be refactored out of the
    ModuleManager and the GraphEditor.
    """

    def __init__(self, devide_app):
        self._devide_app = devide_app

    def execute_network(self, meta_modules):
        """Execute network represented by all modules in the list
        meta_modules.

        """

        # convert all metaModules to schedulerModules
        sms = self._devide_app.scheduler.meta_modules_to_scheduler_modules(
            meta_modules)

        print "STARTING network execute ----------------------------"
        print time.ctime()

        self._devide_app.scheduler.execute_modules(sms)
        
        self._devide_app.set_progress(100.0, 'Network execution complete.')

        print "ENDING network execute ------------------------------"        


    def load_network(self, filename):
        """Given a filename, read it as a DVN file and return a tuple with
        (pmsDict, connectionList, glyphPosDict) if successful.  If not
        successful, an exception will be raised.
        """
        
        f = None
        try:
            # load the fileData
            f = open(filename, 'rb')
            fileData = f.read()
        except Exception, e:
            if f:
                f.close()

            raise RuntimeError, 'Could not load network from %s:\n%s' % \
                  (filename,str(e))

        f.close()

        try:
            (headerTuple, dataTuple) = cPickle.loads(fileData)
            magic, major, minor, patch = headerTuple
            pmsDict, connectionList, glyphPosDict = dataTuple
            
        except Exception, e:
            raise RuntimeError, 'Could not interpret network from %s:\n%s' % \
                  (filename,str(e))
            

        if magic != 'DVN' and magic != 'D3N' or (major,minor,patch) != (1,0,0):
            raise RuntimeError, '%s is not a valid DeVIDE network file.' % \
                  (filename,)

        return (pmsDict, connectionList, glyphPosDict)

    def realise_network(self, pms_dict, connection_list):
        """Given pms_dict and connection_list as returned by load_network,
        realise the given network and return the realised new_modules_dict and
        new_connections.

        @TODO: move network-related code from mm.deserialiseModuleInstances
        here.
        """
        
        mm = self._devide_app.get_module_manager()
        
        new_modules_dict, new_connections = mm.deserialiseModuleInstances(
            pms_dict, connection_list)

        return new_modules_dict, new_connections

    def clear_network(self):
        """Remove/close complete network.

        This method is only called during the non-view mode of operation by
        the scripting interface for example.
        """
        
        mm = self._devide_app.get_module_manager()
        mm.delete_all_modules()

