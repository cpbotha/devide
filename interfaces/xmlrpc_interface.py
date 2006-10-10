from logging_mixin import LoggingMixin
from SimpleXMLRPCServer import SimpleXMLRPCServer
import time

class ServerProxy:
    def test_function(self):
        return "Hello World!"

class XMLRPCInterface(LoggingMixin):

    def __init__(self, devide_app):
        self._devide_app = devide_app

        # initialise logging mixin
        LoggingMixin.__init__(self)

        print "Initialising XMLRPC..."
        # without real IP number, this is only available via localhost
        self.server = SimpleXMLRPCServer(('localhost', 8000))
        self.server.register_instance(ServerProxy())
        #server.register_function()
        
    def handler_post_app_init(self):
        """DeVIDE-required method for interfaces."""

        pass

    def quit(self):
        self.server.server_close()

#     def log_error_list(self, msgs):
#         """Log a list of strings as error.

#         This method must be supplied by all interfaces.
#         """

#         for msg in msgs:
#             print 'ERROR: %s' % (msg,)

#     def log_error(self, message):
#         """Log a single string as error.

#         This method must be supplied by all interfaces.
#         """
        
#         self.log_error_list([message])

#     def log_info(self, message, timeStamp=True):
#         """Log information.

#         This will simply go into the log window.
#         """
        
#         if timeStamp:
#             msg = "%s: %s" % (
#                 time.strftime("%X", time.localtime(time.time())),
#                 message)
#         else:
#             msg = message

#         print 'INFO: %s' % (msg,)

#     def log_message(self, message, timeStamp=True):
#         """Use this to log a message that has to be shown to the user in
#         for example a message box.
#         """

#         print 'MESSAGE: %s' % (message,)

#     def log_warning(self, message, timeStamp=True):

#         print 'WARNING: %s' % (message,)

#     def set_progress(self, progress, message, noTime=False):
#         # we also output an informative message to standard out
#         # in cases where DeVIDE is very busy, this is quite
#         # handy.
#         print "PROGRESS: %s: %.2f" % (message, progress)

    def start_main_loop(self):
        self.log_message('DeVIDE available at %s' % ('localhost:8000',))
        self.log_message('Starting XMLRPC request loop.')
        try:
            self.server.serve_forever()
            
        except KeyboardInterrupt:
            self.log_message('Got keyboard interrupt.')
            
        self.log_message('Shutting down.')
        self.quit()

    
