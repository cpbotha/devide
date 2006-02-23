#!/usr/bin/env python
# $Id$

# the current main release version
DEVIDE_VERSION = 'ng1phase1'

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

# we need these explicit imports for cx_Freeze
#import encodings
#import encodings.ascii
#import encodings.cp437
#import encodings.utf_8
#import encodings.idna

############################################################################
class mainConfigClass(object):

    def __init__(self):
        import defaults
        self.nokits = defaults.NOKITS
        self.stereo = False
        
        self._parseCommandLine()

        # now sanitise some options
        if type(self.nokits) != type([]):
            self.nokits = []

    def dispUsage(self):
        print "-h or --help               : Display this message."
        print "--no-kits kit1,kit2        : Don't load the specified kits."
        print "--stereo                   : Allocate stereo visuals."

    def _parseCommandLine(self):
        try:
            # 'p:' means -p with something after
            optlist, args = getopt.getopt(
                sys.argv[1:], 'h',
                ['help', 'no-kits=', 'stereo'])
            
        except getopt.GetoptError,e:
            self.dispUsage()
            sys.exit(1)

        for o, a in optlist:
            if o in ('-h', '--help'):
                self.dispUsage()
                sys.exit(1)

            elif o in ('--no-kits',):
                self.nokits = a.split(',')

            elif o in ('--stereo',):
                self.stereo = True

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
        
        self.mainConfig = mainConfigClass()
        
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

        ####
        # startup relevant interface instance
        from wx_interface import WXInterface
        self._interface = WXInterface(self)

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
            import genUtils
            msgs = genUtils.exceptionToMsgs()
            self.logError(msgs + [es])

            # this is a critical error: if the moduleManager raised an
            # exception during construction, we have no moduleManager
            # return False, thus terminating the application
            return False

        ####
        # start scheduler
        import scheduler
        self.scheduler = scheduler.Scheduler(self)

        ####
        # call post-module manager interface hook

        self._interface.handler_post_app_init()

        self.setProgress(100, 'Started up')

    def close(self):
        """Quit application.
        """

        self._interface.close()
        self.moduleManager.close()

    def get_devide_version(self):
        return DEVIDE_VERSION

    def get_module_manager(self):
        return self.moduleManager

    def getModuleManager(self):
        return self.get_module_manager()
    
    def log_error(self, msgs):
        self._interface.log_error(msgs)

    logError = log_error

    def log_message(self, message, timeStamp=True):
        self._interface.log_message(message, timeStamp)

    logMessage = log_message

    def setProgress(self, progress, message, noTime=False):
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
    
