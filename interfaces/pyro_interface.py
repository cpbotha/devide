import Pyro.core
import time

# client example:
# import Pyro.core
# Pyro.core.initClient()
# URI = 'PYROLOC://localhost:7766/DeVIDE'
# p = Pyro.core.getProxyForURI(URI)
# p.test_func()

class ServerProxy(Pyro.core.ObjBase):
    def test_function(self):
        return "Hello world!"

class PyroInterface:

    def __init__(self, devide_app):
        self._devide_app = devide_app

        print "Initialising Pyro..."
        Pyro.core.initServer()
        self.daemon = Pyro.core.Daemon()

        self.server_proxy = ServerProxy()
        self.server_proxy_name = 'DeVIDE'
        self.uri = self.daemon.connect(
            self.server_proxy, self.server_proxy_name)
        self.easy_uri = 'PYROLOC://%s:%d/%s' % \
                        (self.daemon.hostname, self.daemon.port,
                         self.server_proxy_name)

    def handler_post_app_init(self):
        """DeVIDE-required method for interfaces."""

        pass

    def quit(self):
	self.daemon.disconnect(self.server_proxy)
	self.daemon.shutdown()

    def log_error_list(self, msgs):
        """Log a list of strings as error.

        This method must be supplied by all interfaces.
        """

        for msg in msgs:
            print 'ERROR: %s' % (msg,)

    def log_error(self, message):
        """Log a single string as error.

        This method must be supplied by all interfaces.
        """
        
        self.log_error_list([message])

    def log_info(self, message, timeStamp=True):
        """Log information.

        This will simply go into the log window.
        """
        
        if timeStamp:
            msg = "%s: %s" % (
                time.strftime("%X", time.localtime(time.time())),
                message)
        else:
            msg = message

        print 'INFO: %s' % (msg,)

    def log_message(self, message, timeStamp=True):
        """Use this to log a message that has to be shown to the user in
        for example a message box.
        """

        print 'MESSAGE: %s' % (message,)

    def log_warning(self, message, timeStamp=True):

        print 'WARNING: %s' % (message,)

    def set_progress(self, progress, message, noTime=False):
        # we also output an informative message to standard out
        # in cases where DeVIDE is very busy, this is quite
        # handy.
        print "PROGRESS: %s: %.2f" % (message, progress)

    def start_main_loop(self):
        self.log_message('DeVIDE available at %s' % (self.easy_uri,))
        self.log_message('Starting Pyro request loop.')
        try:
            self.daemon.requestLoop()
            
        except KeyboardInterrupt:
            self.log_message('Got keyboard interrupt.')
            
        self.log_message('Shutting down.')
        self.quit()

    
