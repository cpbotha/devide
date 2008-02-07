#!/usr/bin/env python

# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

import re

# the current main release version
SVN_REVISION_TEXT = "$Revision$"

try:
    SVN_REVISION = re.match("\$Revision: ([0-9]+) \$", 
            SVN_REVISION_TEXT).group(1)
except Exception, e:
    SVN_REVISION = 'xXx'

DEVIDE_VERSION = '%s.0000' % (SVN_REVISION,)


# standard Python imports
import getopt
import mutex
import os
import re
import stat
import string
import sys
import time
import traceback
import ConfigParser

# we need to import this explicitly, else the installer builder
# forgets it and the binary has e.g. no help() support.
import site


############################################################################
class MainConfigClass(object):

    def __init__(self, appdir):

        # first need to parse command-line to get possible --config-profile
        pcl_data = self._parseCommandLine()

        config_defaults = {
                'nokits': '', 
                'interface' : 'wx',
                'streaming_pieces' : 5,
                'streaming_memory' : 100000}

        cp = ConfigParser.ConfigParser(config_defaults)
        cp.read(os.path.join(appdir, 'devide.cfg'))
        CSEC = pcl_data.config_profile

        # then apply configuration file and defaults #################
        self.nokits = [i.strip() for i in cp.get(CSEC, \
                'nokits').split(',')]
        self.streaming_pieces = cp.get(CSEC, 'streaming_pieces')
        self.streaming_memory = cp.get(CSEC, 'streaming_memory')

        self.interface = cp.get(CSEC, 'interface') 
        self.stereo = False
        self.test = False
        self.script = None
        self.script_params = None

        # finally apply command line switches ############################
        try:
            self.nokits = pcl_data.nokits
        except AttributeError:
            pass

        # now sanitise some options
        if type(self.nokits) != type([]):
            self.nokits = []

    def dispUsage(self):
        print "-h or --help          : Display this message."
        print "--config-profile name : Use config profile with name."
        print "--no-kits kit1,kit2   : Don't load the specified kits."
        print "--kits kit1,kit2      : Load the specified kits."
        print "--interface wx|pyro|xmlrpc|script"
        print "                      : Load 'wx', 'rpc' or 'script' interface."
        print "--stereo              : Allocate stereo visuals."
        print "--test                : Perform built-in unit testing."
        print "--script              : Run specified .py in script mode."

    def _parseCommandLine(self):
        """Parse command-line, return all parsed parameters in
        PCLData class.
        """

        class PCLData:
            def __init__(self):
                self.config_profile = 'DEFAULT'

        pcl_data = PCLData()

        try:
            # 'p:' means -p with something after
            optlist, args = getopt.getopt(
                sys.argv[1:], 'h',
                ['help', 'no-kits=', 'kits=', 'stereo', 'interface=', 'test',
                 'script=', 'script-params=', 'config-profile='])
            
        except getopt.GetoptError,e:
            self.dispUsage()
            sys.exit(1)

        for o, a in optlist:
            if o in ('-h', '--help'):
                self.dispUsage()
                sys.exit(1)

            elif o in ('--config-profile',):
                pcl_data.config_profile = a

            elif o in ('--no-kits',):
                pcl_data.nokits = [i.strip() for i in a.split(',')]

            elif o in ('--kits',):
                # this actually removes the listed kits from the nokits list
                kits = [i.strip() for i in a.split(',')]
                for kit in kits:
                    try:
                        del pcl_data.nokits[pcl_data.nokits.index(kit)]
                    except ValueError:
                        pass

            elif o in ('--interface',):
                if a == 'pyro':
                    pcl_data.interface = 'pyro'
                elif a == 'xmlrpc':
                    pcl_data.interface = 'xmlrpc'
                elif a == 'script':
                    pcl_data.interface = 'script'
                else:
                    pcl_data.interface = 'wx'

            elif o in ('--stereo',):
                pcl_data.stereo = True

            elif o in ('--test',):
                pcl_data.test = True

            elif o in ('--script',):
                pcl_data.script = a

            elif o in ('--script-params',):
                pcl_data.script_params = a

        return pcl_data

############################################################################
class DeVIDEApp:
    """Main devide application class.

    This instantiates the necessary main loop class (wx or headless pyro) and
    acts as communications hub for the rest of DeVIDE.  It also instantiates
    and owns the major components: Scheduler, ModuleManager, etc.
    """
    
    def __init__(self):
        """Construct DeVIDEApp.

        Parse command-line arguments, read configuration.  Instantiate and
        configure relevant main-loop / interface class.
        """
        
        
        self._inProgress = mutex.mutex()
        self._previousProgressTime = 0
        self._currentProgress = -1
        self._currentProgressMsg = ''
        
        #self._appdir, exe = os.path.split(sys.executable)
        if hasattr(sys, 'frozen') and sys.frozen:
            self._appdir, exe = os.path.split(sys.executable)
        else:
            dirname = os.path.dirname(sys.argv[0])
            if dirname and dirname != os.curdir:
                self._appdir = dirname
            else:
                self._appdir = os.getcwd()

        sys.path.insert(0, self._appdir) # for cx_Freeze

        # before this is instantiated, we need to have the paths
        self.main_config = MainConfigClass(self._appdir)

        ####
        # startup relevant interface instance
        if self.main_config.interface == 'pyro':
            from interfaces.pyro_interface import PyroInterface
            self._interface = PyroInterface(self)
            # this is a GUI-less interface, so wx_kit has to go
            self.main_config.nokits.append('wx_kit')

        elif self.main_config.interface == 'xmlrpc':
            from interfaces.xmlrpc_interface import XMLRPCInterface
            self._interface = XMLRPCInterface(self)
            # this is a GUI-less interface, so wx_kit has to go
            self.main_config.nokits.append('wx_kit')

        elif self.main_config.interface == 'script':
            from interfaces.script_interface import ScriptInterface
            self._interface = ScriptInterface(self)
            self.main_config.nokits.append('wx_kit')
            
        else:
            from interfaces.wx_interface import WXInterface
            self._interface = WXInterface(self)

        if 'wx_kit' in self.main_config.nokits:
            self.view_mode = False
        else:
            self.view_mode = True
                             

        ####
        # now startup module manager

        try:
            # load up the moduleManager; we do that here as the moduleManager
            # needs to give feedback via the GUI (when it's available)
            global moduleManager
            import moduleManager
            self.moduleManager = moduleManager.moduleManager(self)

        except Exception, e:
            es = 'Unable to startup the moduleManager: %s.  Terminating.' % \
                 (str(e),)
            self.log_error_with_exception(es)

            # this is a critical error: if the moduleManager raised an
            # exception during construction, we have no moduleManager
            # return False, thus terminating the application
            return False

        ####
        # start network manager
        import network_manager
        self.network_manager = network_manager.NetworkManager(self)

        ####
        # start scheduler
        import scheduler
        self.scheduler = scheduler.SchedulerProxy(self)
        self.scheduler.mode = scheduler.SchedulerProxy.HYBRID_MODE

        ####
        # call post-module manager interface hook

        self._interface.handler_post_app_init()

        self.setProgress(100, 'Started up')

    def close(self):
        """Quit application.
        """

        self._interface.close()
        self.moduleManager.close()

        # and make 100% we're done
        sys.exit()

    def get_devide_version(self):
        return DEVIDE_VERSION

    def get_module_manager(self):
        return self.moduleManager

    def getModuleManager(self):
        return self.get_module_manager()
    
    def log_error(self, msg):
        """Report error.

        In general this will be brought to the user's attention immediately.
        """
        self._interface.log_error(msg)

    def log_error_list(self, msgs):
        self._interface.log_error_list(msgs)

    def log_error_with_exception(self, msg):
        """Can be used by DeVIDE components to log an error message along
        with all information about current exception.

        """
        
        import genUtils
        emsgs = genUtils.exceptionToMsgs()
        self.log_error_list(emsgs + [msg])

    def log_info(self, message, timeStamp=True):
        """Log informative message to the log file or log window.
        """
        
        self._interface.log_info(message, timeStamp)

    def log_message(self, message, timeStamp=True):
        """Log a message that will also be brought to the user's attention,
        for example in a dialog box.
        """
        
        self._interface.log_message(message, timeStamp)

    def log_warning(self, message, timeStamp=True):
        """Log warning message.

        This is not as serious as an error condition, but it should also be
        brought to the user's attention.
        """
        
        self._interface.log_warning(message, timeStamp)

    def set_progress(self, progress, message, noTime=False):
        # 1. we shouldn't call setProgress whilst busy with setProgress
        # 2. only do something if the message or the progress has changed
        # 3. we only perform an update if a second or more has passed
        #    since the previous update, unless this is the final
        #    (i.e. 100% update) or noTime is True

        # the testandset() method of mutex.mutex is atomic... this will grab
        # the lock and set it if it isn't locked alread and then return true.
        # returns false otherwise
        if self._inProgress.testandset():
            if message != self._currentProgressMsg or \
                   progress != self._currentProgress:
                if abs(progress - 100.0) < 0.01 or noTime or \
                       time.time() - self._previousProgressTime >= 1:
                    self._previousProgressTime = time.time()
                    self._currentProgressMsg = message
                    self._currentProgress = progress

                    self._interface.set_progress(progress, message, noTime)

            # unset the mutex thingy
            self._inProgress.unlock()

    setProgress = set_progress
        
    def start_main_loop(self):
        """Start the main execution loop.

        This will thunk through to the contained interface object.
        """

        self._interface.start_main_loop()

    def get_appdir(self):
        """Return directory from which DeVIDE has been invoked.
        """
        
        return self._appdir

    def get_interface(self):
        """Return binding to the current interface.
        """
        
        return self._interface
    

############################################################################
def main():
    devide_app = DeVIDEApp()
    devide_app.start_main_loop()
    

if __name__ == '__main__':
    main()
    
