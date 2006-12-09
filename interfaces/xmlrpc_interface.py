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

    def start_main_loop(self):
        self.log_message('DeVIDE available at %s' % ('localhost:8000',))
        self.log_message('Starting XMLRPC request loop.')
        try:
            self.server.serve_forever()
            
        except KeyboardInterrupt:
            self.log_message('Got keyboard interrupt.')
            
        self.log_message('Shutting down.')
        self.quit()

    
